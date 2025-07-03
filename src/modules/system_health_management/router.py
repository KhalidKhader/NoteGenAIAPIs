"""
Health check endpoints for NoteGen AI APIs.

Simple router that delegates to handlers for medical system health monitoring.
"""

from fastapi import APIRouter

from .schema import HealthCheckResponse
from .handlers import handle_detailed_health_check

router = APIRouter()

@router.get("/", response_model=HealthCheckResponse)
async def detailed_health_check() -> HealthCheckResponse:
    """
    Comprehensive health check for all medical system components.
    
    **Checks:**
    - AWS OpenSearch connection (conversation RAG)
    - Neo4j connection (SNOMED GraphRAG)
    - Azure OpenAI connection (note generation)
    - Pattern learning service
    - Medical compliance features
    """
    return await handle_detailed_health_check()