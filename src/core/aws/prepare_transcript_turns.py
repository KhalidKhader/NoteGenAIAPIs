from datetime import datetime
from typing import Dict, List, Any
from opensearchpy import OpenSearch
from .setup_aws_auth import setup_aws_auth
from .opensearch_conversation_rag_service import ConversationRAGService
from src.core.settings.config import settings
from src.core.settings.logging import logger

def prepare_transcript_turns(transcript: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Transforms the raw transcript into a structured list of turns."""
    prepared_turns = []
    for i, item in enumerate(transcript):
        if not isinstance(item, dict):
            logger.warning(f"Skipping invalid transcript item (not a dict) at index {i}: {item}")
            continue

        turn_id = item.get("id")
        if not turn_id:
            logger.warning(f"Skipping transcript item without 'id' at index {i}: {item}")
            continue
        
        # Robustly find speaker and text
        speaker = next((key for key in item if key.lower() not in ["id", "line_number"]), None)
        
        if speaker and isinstance(item[speaker], str):
            prepared_turns.append({
                "id": turn_id,
                "line_number": i,
                "speaker": speaker.strip(),
                "text": item[speaker].strip()
            })
        else:
            logger.warning(f"Could not determine speaker/text for item at index {i}: {item}")
    return prepared_turns