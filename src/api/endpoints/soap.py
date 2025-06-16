"""SOAP generation API endpoints for NoteGen AI APIs."""

import time
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse

from src.core.logging import get_logger, audit_logger
from src.core.security import jwt_bearer_optional, medical_data_validator
from src.models.soap_models import (
    SOAPGenerationRequest,
    SOAPGenerationResponse,
    SOAPValidationResult,
    ProcessingMetadata,
    SOAPSectionType
)
from src.models.api_models import ErrorResponse, SuccessResponse
from src.services.soap_generator import SOAPGeneratorService
from src.services.conversation_rag import ConversationRAGService
from src.services.snomed_rag import SNOMEDRAGService
from src.services.pattern_learning import PatternLearningService

logger = get_logger(__name__)
router = APIRouter()


# Dependency injection for services
async def get_soap_generator() -> SOAPGeneratorService:
    """Get SOAP generator service instance."""
    # This would normally be injected through a dependency container
    # For now, we'll create a simple factory
    return SOAPGeneratorService()


async def get_conversation_rag() -> ConversationRAGService:
    """Get conversation RAG service instance."""
    return ConversationRAGService()


async def get_snomed_rag() -> SNOMEDRAGService:
    """Get SNOMED RAG service instance."""
    return SNOMEDRAGService()


async def get_pattern_learning() -> PatternLearningService:
    """Get pattern learning service instance."""
    return PatternLearningService()


@router.post(
    "/generate-section",
    response_model=SOAPGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate SOAP Section",
    description="Generate a specific SOAP section from medical conversation data using AI and RAG systems"
)
async def generate_soap_section(
    request: SOAPGenerationRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    soap_generator: SOAPGeneratorService = Depends(get_soap_generator),
    user_id: Optional[str] = Depends(jwt_bearer_optional)
) -> SOAPGenerationResponse:
    """Generate a SOAP section from conversation data."""
    
    start_time = time.time()
    request_id = getattr(http_request.state, 'request_id', str(uuid.uuid4()))
    
    # Set logging context
    logger.set_context(
        request_id=request_id,
        conversation_id=request.conversation_id,
        section_type=request.generator_section,
        doctor_id=request.doctor_id,
        user_id=user_id
    )
    
    logger.info("Starting SOAP section generation")
    
    try:
        # Validate conversation data
        conversation_data = {
            "transcription_text": request.transcription_text,
            "conversation_id": request.conversation_id
        }
        
        if not medical_data_validator.validate_conversation_data(conversation_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation data"
            )
        
        # Log patient data access for audit
        audit_logger.log_patient_data_access(
            user_id=user_id or "system",
            action="soap_generation_request",
            conversation_id=request.conversation_id,
            metadata={
                "section_type": request.generator_section,
                "request_id": request_id
            }
        )
        
        # Generate SOAP section
        generation_result = await soap_generator.generate_soap_section(
            section_type=request.generator_section,
            section_prompt=request.section_prompt,
            transcription_text=request.transcription_text,
            soap_template=request.soap_templates,
            custom_instructions=request.custom_instructions,
            doctor_id=request.doctor_id,
            previous_sections=request.previous_sections,
            language=request.language,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Create processing metadata
        processing_metadata = ProcessingMetadata(
            chunks_used=generation_result.get("chunks_used", 0),
            snomed_codes_referenced=generation_result.get("snomed_codes_referenced", 0),
            doctor_preferences_applied=generation_result.get("doctor_preferences_applied", False),
            processing_time_ms=processing_time_ms,
            token_usage=generation_result.get("token_usage", {}),
            confidence_score=generation_result.get("confidence_score"),
            validation_passed=generation_result.get("validation_passed", True),
            model_version=generation_result.get("model_version", "gpt-4o")
        )
        
        # Create response
        response = SOAPGenerationResponse(
            section_id=generation_result["section_id"],
            section_type=request.generator_section,
            section_content=generation_result["content"],
            conversation_id=request.conversation_id,
            doctor_id=request.doctor_id,
            processing_metadata=processing_metadata,
            medical_terms_used=generation_result.get("medical_terms", []),
            snomed_codes=generation_result.get("snomed_codes", []),
            confidence_score=generation_result.get("confidence_score", 0.9),
            completeness_score=generation_result.get("completeness_score"),
            success=True,
            warnings=generation_result.get("warnings", [])
        )
        
        # Log successful generation
        audit_logger.log_soap_generation(
            user_id=user_id or "system",
            conversation_id=request.conversation_id,
            section_type=request.generator_section,
            success=True,
            metadata={
                "section_id": response.section_id,
                "processing_time_ms": processing_time_ms,
                "confidence_score": response.confidence_score
            }
        )
        
        # Background task for pattern learning (if doctor made modifications)
        if request.doctor_id and request.previous_sections:
            background_tasks.add_task(
                learn_doctor_patterns,
                request.doctor_id,
                generation_result,
                request.generator_section
            )
        
        logger.info(
            f"SOAP section generated successfully",
            extra={
                "section_id": response.section_id,
                "processing_time_ms": processing_time_ms,
                "confidence_score": response.confidence_score
            }
        )
        
        # Sanitize response before returning
        sanitized_response = medical_data_validator.sanitize_soap_output(response.dict())
        
        return SOAPGenerationResponse(**sanitized_response)
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.error(
            f"SOAP generation failed: {str(e)}",
            extra={"processing_time_ms": processing_time_ms}
        )
        
        # Log failed generation
        audit_logger.log_soap_generation(
            user_id=user_id or "system",
            conversation_id=request.conversation_id,
            section_type=request.generator_section,
            success=False,
            metadata={
                "error": str(e),
                "processing_time_ms": processing_time_ms
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SOAP generation failed: {str(e)}"
        )
    finally:
        logger.clear_context()


@router.post(
    "/validate-section",
    response_model=SOAPValidationResult,
    summary="Validate SOAP Section",
    description="Validate a SOAP section for medical accuracy and completeness"
)
async def validate_soap_section(
    section_content: str,
    section_type: SOAPSectionType,
    conversation_id: str,
    http_request: Request,
    user_id: Optional[str] = Depends(jwt_bearer_optional)
) -> SOAPValidationResult:
    """Validate a SOAP section for medical accuracy."""
    
    request_id = getattr(http_request.state, 'request_id', str(uuid.uuid4()))
    section_id = f"{section_type}_{conversation_id}_{int(time.time())}"
    
    logger.set_context(
        request_id=request_id,
        section_id=section_id,
        section_type=section_type,
        user_id=user_id
    )
    
    try:
        # Placeholder for actual validation logic
        # This would integrate with medical validation services
        
        validation_result = SOAPValidationResult(
            section_id=section_id,
            is_valid=True,
            completeness_check=True,
            medical_accuracy_check=True,
            format_check=True,
            snomed_validation=True,
            validation_scores={
                "completeness": 0.95,
                "medical_accuracy": 0.92,
                "format": 1.0,
                "snomed_compliance": 0.88
            },
            validation_errors=[],
            validation_warnings=[],
            improvement_suggestions=[]
        )
        
        logger.info("SOAP section validation completed")
        return validation_result
        
    except Exception as e:
        logger.error(f"SOAP validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )
    finally:
        logger.clear_context()


@router.get(
    "/section/{section_id}",
    response_model=Dict[str, Any],
    summary="Get SOAP Section",
    description="Retrieve a previously generated SOAP section by ID"
)
async def get_soap_section(
    section_id: str,
    user_id: Optional[str] = Depends(jwt_bearer_optional)
) -> Dict[str, Any]:
    """Retrieve a SOAP section by ID."""
    
    logger.set_context(section_id=section_id, user_id=user_id)
    
    try:
        # Placeholder for actual retrieval logic
        # This would fetch from database/storage
        
        logger.info("SOAP section retrieved")
        return {
            "section_id": section_id,
            "message": "Section retrieval not yet implemented",
            "status": "pending_implementation"
        }
        
    except Exception as e:
        logger.error(f"SOAP section retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval failed: {str(e)}"
        )
    finally:
        logger.clear_context()


# Background task functions
async def learn_doctor_patterns(
    doctor_id: str,
    generation_result: Dict[str, Any],
    section_type: str
):
    """Background task to learn doctor patterns."""
    try:
        # This would implement pattern learning logic
        logger.info(f"Learning patterns for doctor {doctor_id}")
        
        # Placeholder for pattern learning implementation
        pass
        
    except Exception as e:
        logger.error(f"Pattern learning failed: {str(e)}")


# Error handlers specific to SOAP endpoints
@router.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors for SOAP endpoints."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="ValidationError",
            message=str(exc),
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    ) 