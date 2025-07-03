"""
Enhanced observability integration with Langfuse for medical AI applications.

This module provides comprehensive observability for medical SOAP generation including:
- Azure OpenAI + LangChain integration following Langfuse v2 best practices
- Medical-specific tracing and metrics
- Proper callback handler management
- Performance monitoring
- Error tracking and debugging
"""

from typing import Optional, Dict, Any

from langfuse.callback import CallbackHandler
from langfuse import Langfuse
from src.core.settings.config import settings
from src.core.settings.logging import logger

# Global Langfuse client instance
_langfuse_client: Optional[Langfuse] = None

def get_langfuse_client() -> Optional[Langfuse]:
    """
    Get or create the global Langfuse client instance.
    
    Returns:
        Initialized Langfuse client if configured, otherwise None.
    """
    global _langfuse_client
    
    if _langfuse_client is None:
        if not settings.langfuse_public_key or not settings.langfuse_secret_key:
            logger.warning("Langfuse keys not found in environment. Observability is disabled.")
            return None
        
        try:
            _langfuse_client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
                debug=settings.debug
            )
            
            # Test connection
            _langfuse_client.auth_check()
            logger.info("Langfuse client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse client: {e}", exc_info=True)
            _langfuse_client = None
    
    return _langfuse_client

def get_langfuse_handler(
    conversation_id: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[CallbackHandler]:
    """
    Creates a Langfuse CallbackHandler for LangChain with enhanced medical context.
    
    This follows the Langfuse v2 SDK pattern for LangChain integration.

    Args:
        conversation_id: The unique ID for the conversation/encounter
        user_id: Optional user/doctor ID
        session_id: Optional session ID (defaults to conversation_id)
        metadata: Additional metadata for the trace

    Returns:
        An initialized CallbackHandler if Langfuse is configured, otherwise None.
    """
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        logger.warning("Langfuse keys not found in environment. Observability is disabled.")
        return None

    logger.info(f"Creating Langfuse handler for conversation_id: {conversation_id}")
    
    try:
        # Enhanced metadata for medical context
        enhanced_metadata = {
            "conversation_id": conversation_id,
            "application": "notegen-ai-apis",
            "version": settings.app_version,
            "environment": "production" if not settings.debug else "development",
            "azure_model": settings.azure_openai_model,
            "azure_deployment": settings.azure_openai_deployment_name,
        }
        
        if metadata:
            enhanced_metadata.update(metadata)
        
        # Create handler using v2 pattern
        handler = CallbackHandler(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
            session_id=session_id or conversation_id,
            user_id=user_id,
            metadata=enhanced_metadata,
            debug=settings.debug
        )
        
        logger.info(f"Langfuse handler created successfully for conversation: {conversation_id}")
        return handler
        
    except Exception as e:
        logger.error(f"Failed to create Langfuse handler: {e}", exc_info=True)
        return None

def create_medical_trace_context(
    name: str,
    conversation_id: str,
    doctor_id: Optional[str] = None,
    section_type: Optional[str] = None,
    template_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Create a medical-specific trace using Langfuse v2 patterns.
    
    Args:
        name: Name of the trace
        conversation_id: Unique conversation/encounter ID
        doctor_id: Doctor/user ID
        section_type: Type of medical section (subjective, objective, etc.)
        template_type: Type of template (soap, visit_summary, etc.)
        metadata: Additional metadata
    
    Returns:
        Langfuse trace object or None if not configured
    """
    client = get_langfuse_client()
    if not client:
        return None
    
    try:
        trace_metadata = {
            "conversation_id": conversation_id,
            "application": "notegen-ai-apis",
            "version": settings.app_version,
            "azure_model": settings.azure_openai_model,
            "azure_deployment": settings.azure_openai_deployment_name,
        }
        
        if doctor_id:
            trace_metadata["doctor_id"] = doctor_id
        if section_type:
            trace_metadata["section_type"] = section_type
        if template_type:
            trace_metadata["template_type"] = template_type
        if metadata:
            trace_metadata.update(metadata)
        
        # Use the v2 SDK pattern for creating traces
        trace = client.trace(
            name=name,
            session_id=conversation_id,
            user_id=doctor_id,
            metadata=trace_metadata
        )
        
        logger.debug(f"Created medical trace: {name} for conversation: {conversation_id}")
        return trace
        
    except Exception as e:
        logger.error(f"Failed to create medical trace: {e}", exc_info=True)
        return None

def add_medical_score(
    trace_id: str,
    score_name: str,
    score_value: float,
    comment: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Add a medical-specific score to a trace.
    
    Args:
        trace_id: ID of the trace to score
        score_name: Name of the score (e.g., 'medical_accuracy', 'factual_consistency')
        score_value: Score value (0.0 to 1.0)
        comment: Optional comment about the score
        metadata: Additional metadata
    
    Returns:
        True if score was added successfully, False otherwise
    """
    client = get_langfuse_client()
    if not client:
        return False
    
    try:
        client.score(
            trace_id=trace_id,
            name=score_name,
            value=score_value,
            comment=comment,
            metadata=metadata or {}
        )
        
        logger.debug(f"Added medical score '{score_name}' to trace {trace_id}: {score_value}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add medical score: {e}", exc_info=True)
        return False

def track_medical_generation_metrics(
    conversation_id: str,
    section_type: str,
    generation_time: float,
    token_usage: Dict[str, int],
    success: bool,
    error_message: Optional[str] = None
) -> None:
    """
    Track medical generation metrics for monitoring and analysis.
    
    Args:
        conversation_id: Unique conversation/encounter ID
        section_type: Type of medical section generated
        generation_time: Time taken for generation in seconds
        token_usage: Token usage statistics
        success: Whether generation was successful
        error_message: Error message if generation failed
    """
    try:
        # Log metrics for monitoring
        logger.info(
            f"Medical generation metrics - "
            f"conversation_id: {conversation_id}, "
            f"section_type: {section_type}, "
            f"generation_time: {generation_time:.2f}s, "
            f"success: {success}, "
            f"tokens: {token_usage}"
        )
        
        # Could be extended to send to additional monitoring systems
        if not success and error_message:
            logger.error(f"Generation failed for {conversation_id}/{section_type}: {error_message}")
            
    except Exception as e:
        logger.error(f"Failed to track medical generation metrics: {e}", exc_info=True)

def flush_langfuse_data(handler: Optional[CallbackHandler] = None) -> None:
    """
    Flush Langfuse data to ensure all traces are sent.
    
    Args:
        handler: Optional specific handler to flush
    """
    try:
        if handler:
            handler.flush()
            logger.debug("Flushed specific Langfuse handler")
        
        # Also flush the global client
        client = get_langfuse_client()
        if client:
            client.flush()
            logger.debug("Flushed global Langfuse client")
            
    except Exception as e:
        logger.error(f"Failed to flush Langfuse data: {e}", exc_info=True)

# Backward compatibility functions
def create_medical_trace(*args, **kwargs):
    """Backward compatibility wrapper for create_medical_trace_context"""
    return create_medical_trace_context(*args, **kwargs) 