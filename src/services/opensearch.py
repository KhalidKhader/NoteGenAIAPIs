from src.core.aws.opensearch_conversation_rag_service import ConversationRAGService
from typing import Optional

_conversation_rag_service: Optional[ConversationRAGService] = None

async def get_conversation_rag_service() -> ConversationRAGService:
    """Get or create the conversation RAG service singleton."""
    global _conversation_rag_service
    if _conversation_rag_service is None:
        _conversation_rag_service = ConversationRAGService()
        await _conversation_rag_service.initialize()
    return _conversation_rag_service