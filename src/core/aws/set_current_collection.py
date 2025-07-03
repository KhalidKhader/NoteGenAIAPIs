import boto3
from opensearchpy import RequestsHttpConnection
from langchain_community.vectorstores import OpenSearchVectorSearch
from .setup_aws_auth import setup_aws_auth
from .opensearch_conversation_rag_service import ConversationRAGService

from src.core.settings.config import settings
from src.core.settings.logging import logger

async def set_current_collection(rag_service: ConversationRAGService, collection_name: str) -> None:
    """Set the current collection for operations."""
    rag_service = ConversationRAGService()
    await rag_service.initialize()
    
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
        
        if collection_name != rag_service.current_collection:
            rag_service.current_collection = collection_name
            rag_service.vector_store = OpenSearchVectorSearch(
                opensearch_url=settings.opensearch_endpoint,
                index_name=collection_name,
                embedding_function=rag_service.embeddings,
                http_auth=await setup_aws_auth(),
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