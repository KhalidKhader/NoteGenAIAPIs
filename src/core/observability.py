"""
Simple, direct observability integration with Langfuse.
"""

from typing import Optional

from langfuse.callback import CallbackHandler
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

def get_langfuse_handler(conversation_id: str) -> Optional[CallbackHandler]:
    """
    Creates a Langfuse CallbackHandler for Langchain.

    The handler automatically picks up credentials (LANGFUSE_SECRET_KEY,
    LANGFUSE_PUBLIC_KEY, LANGFUSE_HOST) from the environment.

    Args:
        conversation_id: The unique ID for the conversation/session.

    Returns:
        An initialized CallbackHandler if Langfuse is configured, otherwise None.
    """
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        logger.warning("Langfuse keys not found in environment. Observability is disabled.")
        return None

    logger.info(f"Creating Langfuse handler for conversation_id: {conversation_id}")
    try:
        # Per Langfuse docs, CallbackHandler() reads credentials from the environment.
        # We provide a session_id to group all related traces for this encounter.
        handler = CallbackHandler(
            session_id=conversation_id,
        )
        return handler
    except Exception as e:
        logger.error(f"Failed to create Langfuse handler: {e}", exc_info=True)
        return None 