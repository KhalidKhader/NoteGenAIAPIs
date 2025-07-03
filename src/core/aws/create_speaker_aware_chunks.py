from datetime import datetime
from typing import Dict, List, Any
from urllib.parse import urlparse
from opensearchpy import OpenSearch
from .setup_aws_auth import setup_aws_auth
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .opensearch_conversation_rag_service import ConversationRAGService

def create_speaker_aware_chunks(
    turns: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Creates semantic chunks from conversation turns, ensuring no speaker's
    turn is split across chunks. Each element from the encounterTranscript array
    becomes a complete chunk to preserve speaker context and avoid mid-turn splits.
    
    New strategy: Each transcript element becomes its own chunk to preserve
    complete speaker turns and avoid splitting mid-conversation.
    """
    if not turns:
        return []

    chunks = []
    
    # Each turn becomes its own chunk to preserve speaker context completely
    for turn in turns:
        chunk_content = f"{turn['speaker']}: {turn['text']}"
        chunk_data = {
            "content": chunk_content,
            "line_numbers": [turn['line_number']],
            "speaker": turn['speaker'],
            "turn_preserved": True,
            "id": turn.get("id")
        }
        chunks.append(chunk_data)
    
        details={
                "total_turns": len(turns),
                "chunks_created": len(chunks),
                "strategy": "one_chunk_per_turn"
            }
        logger.info(f"Created {len(chunks)} speaker-aware chunks (1 per turn) to preserve complete speaker context. details={details}")
    return chunks