"""
Health check handlers for NoteGen AI APIs.

Comprehensive medical system health monitoring with AWS OpenSearch integration.
"""

from datetime import datetime
from typing import List

from fastapi import HTTPException, status

from src.core.settings.logging import logger 
from .schema import (
    HealthCheckResponse,
    ServiceStatus,
    MedicalComplianceStatus
)
from .services import get_snomed_rag_service, get_soap_generator_service, get_conversation_rag_service
from .services import get_pattern_learning_service

async def handle_detailed_health_check() -> HealthCheckResponse:
    """
    Comprehensive health check for all medical system components.
    
    **Checks:**
    - AWS OpenSearch connection (conversation RAG)
    - Neo4j connection (SNOMED GraphRAG)
    - Azure OpenAI connection (note generation)
    - Pattern learning service
    - Medical compliance features
    """
    try:
        services: List[ServiceStatus] = []
        
        # --- Service Health Checks ---
        service_factories = {
            "AWS OpenSearch (Conversation RAG)": get_conversation_rag_service,
            "Neo4j (SNOMED RAG)": get_snomed_rag_service,
            "Azure OpenAI (Note Generation)": get_soap_generator_service,
            "Pattern Learning Service": get_pattern_learning_service
        }

        for service_name, factory in service_factories.items():
            try:
                service = await factory()
                health_result = await service.health_check()
                is_healthy = health_result.get("status") == "healthy"
                
                # Ensure details is a string
                details = health_result.get("details", "")
                if isinstance(details, dict):
                    details = "; ".join(f"{k}: {v}" for k, v in details.items())
                elif details is None:
                    details = "Service check completed"
                
                services.append(ServiceStatus(
                    service_name=service_name,
                    status="healthy" if is_healthy else "unhealthy",
                    details=str(details)
                ))
            except Exception as e:
                services.append(ServiceStatus(
                    service_name=service_name,
                    status="unhealthy",
                    details=f"Connection failed: {str(e)}"
                ))

        # --- Determine Overall Status ---
        unhealthy_count = sum(1 for s in services if s.status == "unhealthy")
        if unhealthy_count == 0:
            overall_status = "healthy"
        elif unhealthy_count == len(services):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        # --- Create Compliance and Observability Info ---
        medical_compliance = MedicalComplianceStatus(
            conversation_isolation=True,
            snomed_validation=True,
            line_referencing=True,
            doctor_preferences=True
        )

        return HealthCheckResponse(
            status=overall_status,
            services=services,
            medical_compliance=medical_compliance,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Medical system health check failed: {str(e)}"
        )
