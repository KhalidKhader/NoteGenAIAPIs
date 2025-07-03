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
from typing import Dict, Optional, Any
from urllib.parse import urlparse


from opensearchpy import OpenSearch, RequestsHttpConnection
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch

from .setup_aws_auth import setup_aws_auth

from src.core.settings.config import settings
from src.core.settings.logging import logger

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
            auth = await setup_aws_auth()

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