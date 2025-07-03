"""
Tenant management handlers for NoteGen AI APIs.

Handlers for creating and managing tenant collections with AWS OpenSearch.
"""

from fastapi import HTTPException
from .schema import TenantCollectionRequest
from src.core.aws.opensearch_conversation_rag_service import ConversationRAGService
from src.core.settings.config import get_settings
import logging
from src.core.aws.create_tenant_collection import create_tenant_collection

logger = logging.getLogger("notegenaiapis")
settings = get_settings()

async def handle_create_tenant_collection(request: TenantCollectionRequest):
    """Create a new tenant collection with all required security policies."""
    try:
        # Simple validation
        if not request.collection_name or len(request.collection_name.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="collection_name is required and cannot be empty"
            )
        
        if not request.clinic_id or len(request.clinic_id.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="clinic_id is required and cannot be empty"
            )
        
        # Validate collection name format (alphanumeric and hyphens only, 3-32 chars)
        import re
        if not re.match(r'^[a-z0-9-]{3,32}$', request.collection_name):
            raise HTTPException(
                status_code=400,
                detail="collection_name must be 3-32 characters, lowercase letters, numbers, and hyphens only"
            )
        
        # Get OpenSearch service
        rag_service = ConversationRAGService()
        await rag_service.initialize()
        
        # Create collection with all required policies
        result = await create_tenant_collection(
            collection_name=request.collection_name,
            clinic_id=request.clinic_id
        )
        
        return {
            "message": f"Successfully created tenant collection: {request.collection_name}",
            "collection_id": result['collection_id'],
            "status": result['status'],
            "endpoint": result['endpoint']
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Failed to create tenant collection: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create tenant collection: {str(e)}"
        )
