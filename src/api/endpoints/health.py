"""Health check API endpoints for NoteGen AI APIs."""

import time
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.logging import get_logger
from src.models.api_models import HealthCheckResponse

logger = get_logger(__name__)
router = APIRouter()

# Application start time for uptime calculation
app_start_time = time.time()


@router.get(
    "/detailed",
    response_model=HealthCheckResponse,
    summary="Detailed Health Check",
    description="Comprehensive health check including all service dependencies"
)
async def detailed_health_check() -> HealthCheckResponse:
    """Detailed health check with service dependency status."""
    
    try:
        # Check individual services
        services_status = await check_all_services()
        
        # Determine overall status
        overall_status = "healthy" if all(
            status == "healthy" for status in services_status.values()
        ) else "degraded"
        
        return HealthCheckResponse(
            status=overall_status,
            version=settings.app_version,
            services=services_status,
            uptime_seconds=time.time() - app_start_time
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Health check failed")


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Check if the service is ready to accept requests"
)
async def readiness_check() -> Dict[str, Any]:
    """Readiness probe for Kubernetes."""
    
    try:
        # Basic readiness checks
        critical_services = await check_critical_services()
        
        if all(status == "healthy" for status in critical_services.values()):
            return {"status": "ready", "services": critical_services}
        else:
            raise HTTPException(status_code=503, detail="Service not ready")
            
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get(
    "/live",
    summary="Liveness Check", 
    description="Check if the service is alive and responsive"
)
async def liveness_check() -> Dict[str, Any]:
    """Liveness probe for Kubernetes."""
    
    try:
        return {
            "status": "alive",
            "timestamp": time.time(),
            "uptime": time.time() - app_start_time
        }
        
    except Exception as e:
        logger.error(f"Liveness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service not alive")


async def check_all_services() -> Dict[str, str]:
    """Check status of all service dependencies."""
    
    services = {}
    
    # Check Azure OpenAI
    services["azure_openai"] = await check_azure_openai()
    
    # Check Neo4j
    services["neo4j"] = await check_neo4j()
    
    # Check Vector Database
    services["vector_db"] = await check_vector_db()
    
    # Check Redis (if enabled)
    if settings.redis_url:
        services["redis"] = await check_redis()
    
    return services


async def check_critical_services() -> Dict[str, str]:
    """Check only critical services needed for basic operation."""
    
    services = {}
    
    # Only check absolutely critical services for readiness
    services["application"] = "healthy"  # Basic app health
    
    # Add critical service checks here
    # services["azure_openai"] = await check_azure_openai()
    
    return services


async def check_azure_openai() -> str:
    """Check Azure OpenAI service connectivity."""
    
    try:
        # Placeholder for actual Azure OpenAI connectivity check
        # This would make a simple test request to verify the service is accessible
        
        # For now, just return healthy if configuration is present
        if settings.azure_openai_api_key and settings.azure_openai_endpoint:
            return "healthy"
        else:
            return "misconfigured"
            
    except Exception as e:
        logger.warning(f"Azure OpenAI health check failed: {str(e)}")
        return "unhealthy"


async def check_neo4j() -> str:
    """Check Neo4j database connectivity."""
    
    try:
        # Placeholder for actual Neo4j connectivity check
        # This would attempt to connect and run a simple query
        
        if settings.neo4j_uri and settings.neo4j_password:
            return "healthy"
        else:
            return "misconfigured"
            
    except Exception as e:
        logger.warning(f"Neo4j health check failed: {str(e)}")
        return "unhealthy"


async def check_vector_db() -> str:
    """Check vector database connectivity."""
    
    try:
        # Placeholder for actual vector DB connectivity check
        # This would verify ChromaDB or Weaviate is accessible
        
        if settings.vector_db_type in ["chroma", "weaviate"]:
            return "healthy"
        else:
            return "misconfigured"
            
    except Exception as e:
        logger.warning(f"Vector DB health check failed: {str(e)}")
        return "unhealthy"


async def check_redis() -> str:
    """Check Redis connectivity."""
    
    try:
        # Placeholder for actual Redis connectivity check
        # This would attempt to ping Redis
        
        if settings.redis_url:
            return "healthy"
        else:
            return "misconfigured"
            
    except Exception as e:
        logger.warning(f"Redis health check failed: {str(e)}")
 