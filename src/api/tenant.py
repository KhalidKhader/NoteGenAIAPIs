from fastapi import APIRouter, HTTPException
from src.models.api_models import TenantCollectionRequest
from src.services.opensearch.opensearch_rag import ConversationRAGService
from src.core.config import get_settings
import logging

router = APIRouter()
logger = logging.getLogger("notegenaiapis")
settings = get_settings()

@router.post("/tenant")
async def create_tenant_collection(request: TenantCollectionRequest):
    """Create a new tenant collection with all required security policies."""
    try:
        # Get OpenSearch service
        rag_service = ConversationRAGService()
        await rag_service.initialize()
        
        # Create collection with all required policies
        result = await rag_service.create_tenant_collection(
            collection_name=request.collection_name,
            clinic_id=request.clinic_id
        )
        
        return {
            "message": f"Successfully created tenant collection: {request.collection_name}",
            "collection_id": result['collection_id'],
            "status": result['status'],
            "endpoint": result['endpoint']
        }
        
    except Exception as e:
        logger.error(f"Failed to create tenant collection: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create tenant collection: {str(e)}"
        )