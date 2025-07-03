"""
Tenant management endpoints for NoteGen AI APIs.

Simple router that delegates to handlers for tenant collection management.
"""

from fastapi import APIRouter
from .schema import TenantCollectionRequest
from .handlers import handle_create_tenant_collection

router = APIRouter()

@router.post("/tenant")
async def create_tenant_collection(request: TenantCollectionRequest):
    """Create a new tenant collection with all required security policies."""
    return await handle_create_tenant_collection(request)