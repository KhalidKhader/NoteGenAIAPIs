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

from opensearchpy import OpenSearch, RequestsHttpConnection, NotFoundError
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.core.config import settings
from src.core.logging import get_logger, MedicalProcessingLogger
from src.templates.prompts import (
    RECORDING_CONSENT_SYSTEM_PROMPT,
    RECORDING_CONSENT_USER_PROMPT_TEMPLATE
)

logger = get_logger(__name__)


class ConversationRAGService:
    """
    Medical Conversation RAG Service using AWS OpenSearch.
    
    Features:
    - AWS OpenSearch vector database for medical transcript storage
    - Strict conversation isolation by conversation_id
    - Line number preservation for medical traceability
    - Semantic chunking for long encounters (2+ hours)
    - Encryption for sensitive medical data
    - Canadian data residency compliance
    """
    def __init__(self):
        self.opensearch_client: Optional[OpenSearch] = None
        self.vector_store: Optional[OpenSearchVectorSearch] = None
        self.llm: Optional[AzureChatOpenAI] = None
        self.embeddings: Optional[AzureOpenAIEmbeddings] = None
        self._initialized = False
    
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
            print("XXXXXXXXXXXXXXXXX ",auth," XXXXXXXXYXXXXXXXXX")
            print("XXXXXXXXXXXXXXXXX ",settings.opensearch_endpoint," XXXXXXXXYXXXXXXXXX")
            self.opensearch_client = OpenSearch(
                hosts=[settings.opensearch_endpoint],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=settings.opensearch_timeout
            )
            await self._test_connection()
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
        """Setup authentication for OpenSearch."""
        
        # Check if OpenSearch username/password are provided (for Fine-Grained Access Control)
        if settings.opensearch_username and settings.opensearch_password:
            logger.info("Using OpenSearch basic authentication (username/password)")
            return (settings.opensearch_username, settings.opensearch_password)
        
        # Fallback to AWS IAM authentication
        import boto3
        from opensearchpy import AWSV4SignerAuth
        
        # Check if explicit credentials are provided in settings
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            logger.info("Using explicit AWS credentials from settings")
            session = boto3.Session(
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
        else:
            logger.info("Using default boto3 session (IAM roles or instance profile)")
            session = boto3.Session()
        
        credentials = session.get_credentials()
        if not credentials:
            raise ValueError("No AWS credentials found - ensure IAM roles are configured or provide explicit credentials")
        
        # Use appropriate service identifier based on OpenSearch type
        service = 'aoss' if settings.is_aoss else 'es'
        return AWSV4SignerAuth(credentials, settings.aws_region, service)
    
    async def _test_connection(self):
        """
        Test OpenSearch connection.
        This test is lenient for Serverless (AOSS) and will not raise an exception
        for auth errors during startup. This allows the service to start even if
        IAM data access policies are not yet correctly configured.
        """
        try:
            # This is the standard health check for OpenSearch domains.
            # It's expected to fail with a 404 for OpenSearch Serverless (AOSS).
            cluster_health = self.opensearch_client.cluster.health()
            if cluster_health['status'] not in ['green', 'yellow']:
                logger.warning(f"OpenSearch cluster status: {cluster_health['status']}")
            else:
                logger.info("OpenSearch connection verified via health check.")
        except NotFoundError:
            # This is the expected path for AOSS.
            logger.info("Health check endpoint not found, which is normal for AWS OpenSearch Serverless (AOSS).")
            # We will not perform a fallback check here to avoid startup failures due to IAM policies.
            # The connection will be tested implicitly by the first actual operation.
            logger.info("Skipping fallback connection test to allow startup with potentially pending IAM permissions.")
        except Exception as e:
            # Catch other potential exceptions during the health check.
            logger.warning(
                f"An unexpected error occurred during OpenSearch health check: {e}. "
                "The service will continue to start, but OpenSearch operations may fail.",
                exc_info=True
            )
    
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
                                "space_type": "cosinesimil",
                                "engine": "faiss"
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
        medical_logger: Optional[MedicalProcessingLogger] = None
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
        
            if medical_logger:
                    medical_logger.log(
                f"Created {len(chunks)} speaker-aware chunks (1 per turn) to preserve complete speaker context.",
                "INFO",
                details={
                    "total_turns": len(turns),
                    "chunks_created": len(chunks),
                    "strategy": "one_chunk_per_turn"
                }
            )
        
        return chunks
    
    async def store_and_chunk_conversation(
        self,
        encounterTranscript: List[Dict[str, str]],
        conversation_id: str,
        doctor_id: str,
        language: str,
        metadata: Optional[Dict[str, Any]] = None,
        medical_logger: Optional[MedicalProcessingLogger] = None
    ) -> List[str]:
        """
        Stores and chunks a medical conversation using a speaker-aware strategy.
        This is the main entry point for processing and storing new encounters.
        """
        if not self._initialized:
            await self.initialize()
        
        if medical_logger:
            medical_logger.log(
                message=f"Storing conversation {conversation_id} for doctor {doctor_id} in {language}.",
                level="INFO",
                details={"turn_count": len(encounterTranscript)}
            )
        
        # 1. Prepare structured turns from the raw transcript
        turns = self._prepare_transcript_turns(encounterTranscript)
        
        # 2. Create chunks without splitting speaker turns
        chunks = self._create_speaker_aware_chunks(turns, settings.chunk_size, medical_logger=medical_logger)
        
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
                if medical_logger:
                    medical_logger.log(f"Stored chunk {i+1}/{len(chunks)} with doc_id {doc_id}", "DEBUG")
            except Exception as e:
                error_message = f"Failed to store chunk {i} for conversation {conversation_id}: {str(e)}"
                logger.error(error_message)
                if medical_logger:
                    medical_logger.log(error_message, "ERROR")

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
            if medical_logger:
                medical_logger.log("Stored full conversation document.", "INFO")

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
                "reason": "Service not initialized"
            }
        
        try:
            opensearch_connected = False
            opensearch_status = "unknown"
            if self.opensearch_client and self.opensearch_client.ping():
                cluster_health = self.opensearch_client.cluster.health()
                opensearch_status = cluster_health.get('status', 'unknown')
                opensearch_connected = opensearch_status in ['green', 'yellow']
            elif self.opensearch_client:
                opensearch_status = "ping_failed"

            is_healthy = opensearch_connected and self.embeddings is not None
            
            return {
                "service": "conversation_rag",
                "status": "healthy" if is_healthy else "unhealthy",
                "details": {
                    "opensearch_connected": opensearch_connected,
                    "opensearch_status": opensearch_status,
                    "embeddings_initialized": self.embeddings is not None,
                    "vector_store_initialized": self.vector_store is not None
                }
            }
        except Exception as e:
            logger.error(f"Health check encountered an error: {str(e)}")
            return {
                "service": "conversation_rag",
                "status": "unhealthy",
                "reason": f"Health check exception: {str(e)}"
            }
    

_conversation_rag_service: Optional[ConversationRAGService] = None

async def get_conversation_rag_service() -> ConversationRAGService:
    """Get or create the conversation RAG service singleton."""
    global _conversation_rag_service
    if _conversation_rag_service is None:
        _conversation_rag_service = ConversationRAGService()
        await _conversation_rag_service.initialize()
    return _conversation_rag_service