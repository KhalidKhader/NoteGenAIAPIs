"""
Medical Conversation RAG Service for NoteGen AI APIs - AWS OpenSearch Implementation.

Features:
- AWS OpenSearch vector database integration for transcript storage
- Conversation isolation by ID (medical requirement)
- Line number preservation for traceability
- Full conversation storage with chunking for long encounters
- Medical compliance (HIPAA/PIPEDA)
- Canadian data residency with AWS OpenSearch
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import boto3
import json
import asyncio

from opensearchpy import OpenSearch, RequestsHttpConnection, NotFoundError
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.core.config import settings
from src.core.logging import logger
from src.templates.prompts import (
    RECORDING_CONSENT_SYSTEM_PROMPT,
    RECORDING_CONSENT_USER_PROMPT_TEMPLATE
)



class ConversationRAGService:
    """
    Medical Conversation RAG Service using AWS OpenSearch Serverless (AOSS).
    
    Features:
    - AWS OpenSearch Serverless (AOSS) vector database for medical transcript storage
    - Strict conversation isolation by conversation_id
    - Line number preservation for medical traceability
    - Semantic chunking for long encounters (2+ hours)
    - Encryption for sensitive medical data
    - Canadian data residency compliance
    - Only supports IAM authentication (no basic auth)
    """
    def __init__(self):
        self.opensearch_client: Optional[OpenSearch] = None
        self.vector_store: Optional[OpenSearchVectorSearch] = None
        self.llm: Optional[AzureChatOpenAI] = None
        self.embeddings: Optional[AzureOpenAIEmbeddings] = None
        self._initialized = False
        self.current_collection: Optional[str] = None
    
    async def initialize(self) -> None:
        """Initialize the medical conversation RAG service with AWS OpenSearch."""
        if self._initialized:
            return
        logger.info("Initializing Medical Conversation RAG Service with AWS OpenSearch")
        try:
            self.llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                deployment_name=settings.azure_openai_deployment_name,
                model=settings.azure_openai_model,
                temperature=0.0,
            )
            self.embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=settings.azure_openai_embedding_endpoint,
                api_key=settings.azure_openai_embedding_api_key,
                api_version=settings.azure_openai_api_version,
                deployment=settings.azure_openai_embedding_deployment_name,
                model=settings.azure_openai_embedding_model
            )
            auth = await self._setup_aws_auth()

            # Parse the OpenSearch endpoint URL
            parsed_url = urlparse(settings.opensearch_endpoint)
            host = parsed_url.hostname
            port = parsed_url.port or 443

            self.opensearch_client = OpenSearch(
                hosts=[{'host': host, 'port': port}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=settings.opensearch_timeout
            )
            self.vector_store = OpenSearchVectorSearch(
                opensearch_url=settings.opensearch_endpoint,
                index_name=settings.opensearch_index,
                embedding_function=self.embeddings,
                http_auth=auth,
                timeout=settings.opensearch_timeout,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
            )
            await self._create_index()
            self._initialized = True
            logger.info("Medical Conversation RAG Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Medical Conversation RAG: {str(e)}")
            raise RuntimeError(f"Medical RAG initialization failed: {str(e)}")
    
    async def _setup_aws_auth(self):
        """Setup authentication for OpenSearch Serverless (AOSS) only."""
        from opensearchpy import AWSV4SignerAuth
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            raise ValueError("No AWS credentials found - ensure IAM roles are configured or provide explicit credentials")
        # Always use 'aoss' for OpenSearch Serverless
        service = 'aoss'
        return AWSV4SignerAuth(credentials, settings.aws_region, service)
    
    async def create_tenant_collection(self, collection_name: str, clinic_id: str) -> Dict[str, Any]:
        """Create a new tenant collection with all required policies."""
        if not self._initialized:
            await self.initialize()

        try:
            aoss = boto3.client('opensearchserverless', region_name=settings.aws_region)
            
            # Generate short policy names (max 32 chars)
            policy_prefix = collection_name[:20]  # Leave room for suffixes
            
            # 1. Create encryption policy (if not exists)
            encryption_policy = {
                "Rules": [{
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"]
                }],
                "AWSOwnedKey": True
            }
            
            try:
                aoss.create_security_policy(
                    name=f"{policy_prefix}-enc",
                    policy=json.dumps(encryption_policy),
                    type='encryption',
                    description=f'Encryption policy for {collection_name}'
                )
                logger.info(f"Created encryption policy for {collection_name}")
            except aoss.exceptions.ConflictException:
                logger.info(f"Encryption policy already exists for {collection_name}")
            
            # 2. Create network policy (if not exists)
            network_policy = [{
                "Description": f"Network policy for {collection_name}",
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"]
                    }
                ],
                "AllowFromPublic": True
            }]
            
            try:
                aoss.create_security_policy(
                    name=f"{policy_prefix}-net",
                    policy=json.dumps(network_policy),
                    type='network',
                    description=f'Network policy for {collection_name}'
                )
                logger.info(f"Created network policy for {collection_name}")
            except aoss.exceptions.ConflictException:
                logger.info(f"Network policy already exists for {collection_name}")
            
            # 3. Create data access policy (if not exists)
            # Get caller identity for proper ARN
            sts = boto3.client('sts')
            account_id = sts.get_caller_identity()['Account']
            
            data_policy = [{
                "Rules": [
                    {
                        "Resource": [
                            f"index/{collection_name}/*"
                        ],
                        "Permission": [
                            "aoss:CreateIndex",
                            "aoss:DeleteIndex",
                            "aoss:UpdateIndex",
                            "aoss:DescribeIndex",
                            "aoss:ReadDocument",
                            "aoss:WriteDocument"
                        ],
                        "ResourceType": "index"
                    },
                    {
                        "Resource": [
                            f"collection/{collection_name}"
                        ],
                        "Permission": [
                            "aoss:CreateCollectionItems",
                            "aoss:DeleteCollectionItems",
                            "aoss:UpdateCollectionItems",
                            "aoss:DescribeCollectionItems"
                        ],
                        "ResourceType": "collection"
                    }
                ],
                "Principal": [
                    f"arn:aws:iam::{account_id}:root"  # Grant access to the entire AWS account
                ]
            }]
            
            try:
                aoss.create_access_policy(
                    name=f"te-{policy_prefix}",
                    policy=json.dumps(data_policy),
                    type='data',
                    description=f'Data access policy for {collection_name}'
                )
                logger.info(f"Created access policy for {collection_name}")
            except aoss.exceptions.ConflictException:
                logger.info(f"Access policy already exists for {collection_name}")
            
            # 4. Create collection
            try:
                response = aoss.create_collection(
                    name=collection_name,
                    type='VECTORSEARCH',
                    description=f'Tenant collection for clinic {clinic_id}'
                )
                
                collection_id = response['createCollectionDetail']['id']
                logger.info(f"Created collection {collection_name}")
                
                # 5. Wait for collection to be active
                max_attempts = 20  # Increased from 10
                delay_seconds = 30
                
                for attempt in range(max_attempts):
                    try:
                        status_response = aoss.batch_get_collection(ids=[collection_id])
                        collection_details = status_response['collectionDetails'][0]
                        status = collection_details['status']
                        
                        logger.info(f"Collection {collection_name} status: {status}. Attempt {attempt + 1}/{max_attempts}")
                        
                        if status == 'ACTIVE':
                            logger.info(f"Collection {collection_name} is now active")
                            
                            # Create OpenSearch client for the new collection
                            collection_endpoint = collection_details.get('collectionEndpoint')
                            if not collection_endpoint:
                                raise Exception("Collection endpoint not available")
                            
                            # Create index with vector mapping
                            index_name = collection_name
                            index_mapping = {
                                "mappings": {
                                    "properties": {
                                        "text": {"type": "text", "analyzer": "standard"},
                                        "vector_field": {
                                            "type": "knn_vector",
                                            "dimension": 1536,
                                            "method": {
                                                "name": "hnsw",
                                                "space_type": "cosinesimil",
                                                "parameters": {
                                                    "ef_construction": 512,
                                                    "m": 16
                                                }
                                            }
                                        },
                                        "metadata": {
                                            "type": "object",
                                            "properties": {
                                                "conversation_id": {"type": "keyword"},
                                                "chunk_id": {"type": "keyword"},
                                                "turn_ids": {"type": "keyword"},
                                                "chunk_index": {"type": "integer"},
                                                "line_numbers": {"type": "integer"},
                                                "speaker": {"type": "keyword"},
                                                "doctor_id": {"type": "keyword"},
                                                "language": {"type": "keyword"},
                                                "created_at": {"type": "date"},
                                                "is_complete_conversation": {"type": "boolean"},
                                                "speaker_turn_preserved": {"type": "boolean"}
                                            }
                                        }
                                    }
                                },
                                "settings": {
                                    "index": {
                                        "number_of_shards": 3,
                                        "number_of_replicas": 2,
                                        "refresh_interval": "10s"
                                    }
                                }
                            }
                            
                            try:
                                if not collection_endpoint:
                                    raise Exception("Collection endpoint not available")
                                client = OpenSearch(
                                    hosts=[{'host': collection_endpoint.replace('https://', ''), 'port': 443}],
                                    http_auth=self._get_aws_auth(),
                                    use_ssl=True,
                                    verify_certs=True,
                                    connection_class=RequestsHttpConnection,
                                    timeout=30
                                )
                                
                                if not client.indices.exists(index=index_name):
                                    client.indices.create(
                                        index=index_name,
                                        body=index_mapping
                                    )
                                    logger.info(f"Created vector index for collection {collection_name}")
                                else:
                                    logger.info(f"Vector index already exists for collection {collection_name}")
                            except Exception as e:
                                logger.error(f"Failed to create vector index: {str(e)}")
                            
                            return {
                                'collection_id': collection_id,
                                'status': 'ACTIVE',
                                'endpoint': collection_endpoint
                            }
                        
                        elif status == 'FAILED':
                            raise Exception(f"Collection creation failed with status: {status}")
                        elif status == 'DELETED':
                            raise Exception(f"Collection was deleted during creation")
                        
                        # If not active yet, wait and try again
                        logger.info(f"Waiting {delay_seconds} seconds before next check...")
                        await asyncio.sleep(delay_seconds)
                        
                    except Exception as e:
                        if "collection_id" not in str(e):  # If not a normal "not active yet" case
                            logger.error(f"Error checking collection status: {str(e)}")
                        await asyncio.sleep(delay_seconds)
                
                # If we get here, check one last time if the collection exists and is usable
                try:
                    final_check = aoss.batch_get_collection(ids=[collection_id])
                    if final_check['collectionDetails'][0]['status'] == 'ACTIVE':
                        collection_endpoint = final_check['collectionDetails'][0].get('collectionEndpoint')
                        return {
                            'collection_id': collection_id,
                            'status': 'ACTIVE',
                            'endpoint': collection_endpoint
                        }
                except Exception:
                    pass
                
                # If we get here, the collection exists but we timed out waiting for ACTIVE status
                return {
                    'collection_id': collection_id,
                    'status': 'CREATING',
                    'message': 'Collection created but not yet active. Please check AWS console for status.',
                    'endpoint': 'Not yet available'
                }
                
            except aoss.exceptions.ConflictException:
                logger.error(f"Collection {collection_name} already exists")
                raise Exception(f"Collection {collection_name} already exists")
            
        except Exception as e:
            error_msg = f"Failed to create tenant collection {collection_name}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def set_current_collection(self, collection_name: str) -> None:
        """Set the current collection for operations."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Create AWS OpenSearch Serverless client to check collection existence
            aoss = boto3.client('opensearchserverless', region_name=settings.aws_region)
            
            # List collections to check if the requested one exists
            collections = aoss.list_collections()
            collection_names = [c['name'] for c in collections.get('collectionSummaries', [])]
            
            if collection_name not in collection_names:
                error_msg = f"Collection '{collection_name}' does not exist. Please provide a valid clinic collection name."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if collection_name != self.current_collection:
                self.current_collection = collection_name
                self.vector_store = OpenSearchVectorSearch(
                    opensearch_url=settings.opensearch_endpoint,
                    index_name=collection_name,
                    embedding_function=self.embeddings,
                    http_auth=await self._setup_aws_auth(),
                    timeout=settings.opensearch_timeout,
                    use_ssl=True,
                    verify_certs=True,
                    connection_class=RequestsHttpConnection
                )
                logger.info(f"Switched to collection: {collection_name}")
        except Exception as e:
            error_msg = f"Failed to set collection: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def _create_index(self) -> None:
        """Create OpenSearch index for medical conversations."""
        try:
            index_name = settings.opensearch_index
            if self.opensearch_client.indices.exists(index=index_name):
                logger.info(f"OpenSearch index '{index_name}' already exists")
                return
            index_mapping = {
                "mappings": {
                    "properties": {
                        "text": {"type": "text", "analyzer": "standard"},
                        "vector_field": {
                            "type": "knn_vector",
                            "dimension": 1536,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil"
                            }
                        },
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "conversation_id": {"type": "keyword"},
                                "chunk_id": {"type": "keyword"},
                                "turn_ids": {"type": "keyword"},
                                "chunk_index": {"type": "integer"},
                                "line_numbers": {"type": "integer"},
                                "speaker": {"type": "keyword"},
                                "doctor_id": {"type": "keyword"},
                                "language": {"type": "keyword"},
                                "created_at": {"type": "date"},
                                "is_complete_conversation": {"type": "boolean"},
                                "speaker_turn_preserved": {"type": "boolean"}
                            }
                        }
                    }
                }
            }
            try:
                self.opensearch_client.indices.create(
                    index=index_name,
                    body=index_mapping
                )
                logger.info(f"Created OpenSearch index '{index_name}'")
            except Exception as create_error:
                logger.warning(f"Index creation failed: {create_error}. May be created automatically.")
        except Exception as e:
            logger.error(f"Failed to create OpenSearch index: {str(e)}")
    
    def _prepare_transcript_turns(self, transcript: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Transforms the raw transcript into a structured list of turns."""
        prepared_turns = []
        for i, item in enumerate(transcript):
            if not isinstance(item, dict):
                logger.warning(f"Skipping invalid transcript item (not a dict) at index {i}: {item}")
                continue

            turn_id = item.get("id")
            if not turn_id:
                logger.warning(f"Skipping transcript item without 'id' at index {i}: {item}")
                continue
            
            # Robustly find speaker and text
            speaker = next((key for key in item if key.lower() not in ["id", "line_number"]), None)
            
            if speaker and isinstance(item[speaker], str):
                prepared_turns.append({
                    "id": turn_id,
                    "line_number": i,
                    "speaker": speaker.strip(),
                    "text": item[speaker].strip()
                })
            else:
                logger.warning(f"Could not determine speaker/text for item at index {i}: {item}")
        return prepared_turns

    def _create_speaker_aware_chunks(
        self, 
        turns: List[Dict[str, Any]],
        max_chunk_size: int,
        logger: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Creates semantic chunks from conversation turns, ensuring no speaker's
        turn is split across chunks. Each element from the encounterTranscript array
        becomes a complete chunk to preserve speaker context and avoid mid-turn splits.
        
        New strategy: Each transcript element becomes its own chunk to preserve
        complete speaker turns and avoid splitting mid-conversation.
        """
        if not turns:
            return []

        chunks = []
        
        # Each turn becomes its own chunk to preserve speaker context completely
        for turn in turns:
            chunk_content = f"{turn['speaker']}: {turn['text']}"
            chunk_data = {
                "content": chunk_content,
                "line_numbers": [turn['line_number']],
                "speaker": turn['speaker'],
                "turn_preserved": True,
                "id": turn.get("id")
            }
            chunks.append(chunk_data)
        
            details={
                    "total_turns": len(turns),
                    "chunks_created": len(chunks),
                    "strategy": "one_chunk_per_turn"
                }
            logger.info(f"Created {len(chunks)} speaker-aware chunks (1 per turn) to preserve complete speaker context. details={details}")
        return chunks
    
    async def store_and_chunk_conversation(
        self,
        encounterTranscript: List[Dict[str, str]],
        conversation_id: str,
        doctor_id: str,
        language: str,
        metadata: Optional[Dict[str, Any]] = None,
        logger: Optional[Any] = None
    ) -> List[str]:
        """
        Stores and chunks a medical conversation using a speaker-aware strategy.
        This is the main entry point for processing and storing new encounters.
        """
        if not self._initialized:
            await self.initialize()
        
        details={"turn_count": len(encounterTranscript)}
        logger.info(f"Storing conversation {conversation_id} for doctor {doctor_id} in {language}. details={details}")
        
        # 1. Prepare structured turns from the raw transcript
        turns = self._prepare_transcript_turns(encounterTranscript)
        
        # 2. Create chunks without splitting speaker turns
        chunks = self._create_speaker_aware_chunks(turns, settings.chunk_size, logger=logger)
        
        # 3. Store each chunk in OpenSearch
        document_ids = []
        for i, chunk_data in enumerate(chunks):
            chunk_id = chunk_data.get("id")
            if not chunk_id:
                logger.warning(f"Chunk at index {i} for conversation {conversation_id} has no ID, generating a fallback.")
                chunk_id = f"{conversation_id}_chunk_{i}"

            chunk_metadata = {
                "conversation_id": conversation_id,
                "chunk_id": chunk_id,
                "chunk_index": i,
                "doctor_id": doctor_id,
                "language": language,
                "line_numbers": chunk_data["line_numbers"],
                "created_at": datetime.utcnow().isoformat(),
                "is_complete_conversation": False, # This is a chunk, not the full text
                "speaker_turn_preserved": True,
                "turn_ids": [chunk_id],
                **(metadata or {})
            }
            
            try:
                doc_id = await self._store_single_document(chunk_data['content'], chunk_metadata)
                document_ids.append(doc_id)
                logger.info(f"Stored chunk {i+1}/{len(chunks)} with doc_id {doc_id}")
            except Exception as e:
                error_message = f"Failed to store chunk {i} for conversation {conversation_id}: {str(e)}"
                logger.error(error_message)

        # 4. Optionally store the full conversation as a single document
        if settings.store_full_conversation:
            full_text = "\n".join([f"{t['speaker']}: {t['text']}" for t in turns])
            full_text_metadata = {
                "conversation_id": conversation_id,
                "chunk_id": f"{conversation_id}_full",
                "chunk_index": -1, # Indicates full conversation
                "doctor_id": doctor_id,
                "language": language,
                "created_at": datetime.utcnow().isoformat(),
                "is_complete_conversation": True,
                **(metadata or {})
            }
            # Avoid re-embedding the full text if not necessary by storing it without vectorization,
            # or ensure the vector store can handle this efficiently.
            # For now, we proceed with storing it as a standard document.
            await self._store_single_document(full_text, full_text_metadata)
            logger.info("Stored full conversation document.")

        return document_ids

    async def _store_single_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """Store a single document in OpenSearch."""
        try:
            return self.vector_store.add_texts(
                texts=[content],
                metadatas=[metadata]
            )[0]
        except Exception as e:
            logger.error(f"Failed to store document: {str(e)}")
            raise
    
    async def retrieve_relevant_chunks(
        self, 
        conversation_id: str, 
        query: str, 
        k: int = settings.retrieval_k_value
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant conversation chunks using semantic search."""
        try:
            logger.info(f"Retrieving {k} chunks for conversation {conversation_id}")
            search_query = {
                "size": k,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"metadata.conversation_id": conversation_id}},
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["text^2", "content^2", "page_content^2", "metadata.speaker"],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO"
                                }
                            }
                        ]
                    }
                },
                "_source": ["text", "content", "page_content", "metadata"]
            }
            response = self.opensearch_client.search(
                index=settings.opensearch_index,
                body=search_query
            )
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                metadata = source.get('metadata', {})
                content = (source.get('content') or 
                          source.get('text') or 
                          source.get('page_content', ''))
                if not content or 'chunk_id' not in metadata:
                    continue
                result = {
                    "content": content,
                    "chunk_id": metadata.get("chunk_id", "unknown"),
                    "line_numbers": metadata.get("line_numbers", []),
                    "speaker": metadata.get("speaker", "Unknown"),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "score": hit['_score'],
                    "conversation_id": conversation_id
                }
                results.append(result)
            logger.info(f"Retrieved {len(results)} relevant chunks")
            return results
        except Exception as e:
            logger.error(f"Failed to retrieve chunks: {str(e)}")
            raise RuntimeError(f"RAG retrieval failed: {str(e)}")
    
    async def find_consent_chunk_id(
        self,
        conversation_id: str,
        language: str = 'en',
        langfuse_handler: Optional[Any] = None
    ) -> Optional[str]:
        """
        Finds the chunk_id of the turn where the patient gives consent to record, using an LLM for classification.
        Searches patient's text for consent keywords in either English or French.
        """
        if not self._initialized or not self.llm:
            await self.initialize()

        consent_prompt = ChatPromptTemplate.from_messages([
            ("system", RECORDING_CONSENT_SYSTEM_PROMPT),
            ("human", RECORDING_CONSENT_USER_PROMPT_TEMPLATE)
        ])
        
        consent_chain = consent_prompt | self.llm | StrOutputParser()
        
        try:
            search_query = {
                "size": 1000,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"metadata.conversation_id": conversation_id}},
                            {"term": {"metadata.speaker": "patient"}}
                        ]
                    }
                },
                "_source": ["text", "content", "page_content", "metadata"]
            }
            response = self.opensearch_client.search(
                index=settings.opensearch_index,
                body=search_query
            )

            for hit in response['hits']['hits']:
                source = hit['_source']
                content = (source.get('content') or 
                          source.get('text') or 
                          source.get('page_content', ''))
                
                llm_response = await consent_chain.ainvoke(
                    {"patient_text": content},
                    config={"callbacks": [langfuse_handler]} if langfuse_handler else None
                )
                
                if "CONSENT" in llm_response.upper():
                    metadata = source.get('metadata', {})
                    consent_chunk_id = metadata.get("chunk_id")
                    if consent_chunk_id:
                        logger.info(f"Found consent in chunk {consent_chunk_id} for conversation {conversation_id} using LLM")
                        return consent_chunk_id
            
            logger.warning(f"Could not find a clear consent statement for conversation {conversation_id} using LLM.")
            return None

        except Exception as e:
            logger.error(f"Failed to find consent chunk for conversation {conversation_id} using LLM: {str(e)}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """Health check for medical system monitoring."""
        if not self._initialized:
            return {
                "service": "conversation_rag",
                "status": "unhealthy",
                "details": "Service not initialized"
            }
        
        try:
            # For AOSS, we check if we can access the index
            opensearch_connected = False
            opensearch_status = "unknown"
            
            # Check index existence for AOSS
            if self.opensearch_client and self.opensearch_client.indices.exists(index=settings.opensearch_index):
                opensearch_status = "aoss_connected"
                opensearch_connected = True
            else:
                opensearch_status = "aoss_index_not_found"
            
            # Check other components
            embeddings_initialized = self.embeddings is not None
            vector_store_initialized = self.vector_store is not None
            
            # Format the details string (keep the working format)
            details = f"OpenSearch Status: {opensearch_status}, OpenSearch Connected: {opensearch_connected}, Embeddings: {'initialized' if embeddings_initialized else 'not initialized'}, Vector Store: {'initialized' if vector_store_initialized else 'not initialized'}"
            
            return {
                "service": "conversation_rag",
                "status": "healthy" if opensearch_connected and embeddings_initialized and vector_store_initialized else "unhealthy",
                "details": details
            }
            
        except Exception as e:
            return {
                "service": "conversation_rag",
                "status": "unhealthy",
                "details": f"Health check failed: {str(e)}"
            }
    

_conversation_rag_service: Optional[ConversationRAGService] = None

async def get_conversation_rag_service() -> ConversationRAGService:
    """Get or create the conversation RAG service singleton."""
    global _conversation_rag_service
    if _conversation_rag_service is None:
        _conversation_rag_service = ConversationRAGService()
        await _conversation_rag_service.initialize()
    return _conversation_rag_service