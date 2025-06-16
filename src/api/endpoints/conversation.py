"""Conversation management API endpoints for NoteGen AI APIs."""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends, status

from src.core.logging import get_logger, audit_logger
from src.core.security import jwt_bearer_optional, medical_data_validator
from src.models.conversation_models import (
    ConversationStoreRequest,
    ConversationStoreResponse
)
from src.models.api_models import SuccessResponse
from src.services.conversation_rag import ConversationRAGService

logger = get_logger(__name__)
router = APIRouter()


async def get_conversation_rag() -> ConversationRAGService:
    """Get conversation RAG service instance."""
    return ConversationRAGService()


@router.post(
    "/store",
    response_model=ConversationStoreResponse,
    summary="Store Conversation",
    description="Store a medical conversation in the RAG system for future SOAP generation"
)
async def store_conversation(
    request: ConversationStoreRequest,
    http_request: Request,
    conversation_rag: ConversationRAGService = Depends(get_conversation_rag),
    user_id: Optional[str] = Depends(jwt_bearer_optional)
) -> ConversationStoreResponse:
    """Store a conversation in the RAG system."""
    
    request_id = getattr(http_request.state, 'request_id', str(uuid.uuid4()))
    
    logger.set_context(
        request_id=request_id,
        conversation_id=request.conversation_data.conversation_id,
        user_id=user_id
    )
    
    try:
        # Validate conversation data
        conversation_dict = {
            "transcription_text": request.conversation_data.get_text_content(),
            "conversation_id": request.conversation_data.conversation_id
        }
        
        if not medical_data_validator.validate_conversation_data(conversation_dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation data"
            )
        
        # Log data access
        audit_logger.log_patient_data_access(
            user_id=user_id or "system",
            action="conversation_storage",
            conversation_id=request.conversation_data.conversation_id,
            metadata={"encrypted": request.encrypt_content}
        )
        
        # Store conversation
        storage_result = await conversation_rag.store_conversation(
            conversation_data=request.conversation_data,
            encrypt_content=request.encrypt_content,
            generate_embeddings=request.generate_embeddings
        )
        
        logger.info("Conversation stored successfully")
        
        return storage_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation storage failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage failed: {str(e)}"
        )
    finally:
        logger.clear_context()


@router.get(
    "/{conversation_id}",
    summary="Get Conversation",
    description="Retrieve a stored conversation by ID"
)
async def get_conversation(
    conversation_id: str,
    user_id: Optional[str] = Depends(jwt_bearer_optional)
) -> SuccessResponse:
    """Retrieve a conversation by ID."""
    
    logger.set_context(conversation_id=conversation_id, user_id=user_id)
    
    try:
        # Placeholder for actual retrieval
        logger.info("Conversation retrieval requested")
        
        return SuccessResponse(
            message="Conversation retrieval not yet implemented",
            data={"conversation_id": conversation_id}
        )
        
    except Exception as e:
        logger.error(f"Conversation retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval failed: {str(e)}"
        )
    finally:
        logger.clear_context() 