from datetime import datetime
from typing import Dict, List, Optional, Any
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .opensearch_conversation_rag_service import ConversationRAGService
from .create_speaker_aware_chunks import create_speaker_aware_chunks
from .prepare_transcript_turns import prepare_transcript_turns

async def store_and_chunk_conversation(
    encounterTranscript: List[Dict[str, str]],
    conversation_id: str,
    doctor_id: str,
    language: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Stores and chunks a medical conversation using a speaker-aware strategy.
    This is the main entry point for processing and storing new encounters.
    """
    rag_service = ConversationRAGService()
    if not rag_service._initialized:
        await rag_service.initialize()
    
    details={"turn_count": len(encounterTranscript)}
    logger.info(f"Storing conversation {conversation_id} for doctor {doctor_id} in {language}. details={details}")
    
    # 1. Prepare structured turns from the raw transcript
    turns = prepare_transcript_turns(encounterTranscript)
    
    # 2. Create chunks without splitting speaker turns
    chunks = create_speaker_aware_chunks(turns)
    
    # 3. Store each chunk in OpenSearch
    document_ids = []
    for i, chunk_data in enumerate(chunks):
        chunk_id = chunk_data.get("id")
        if not chunk_id:
            logger.warning(f"Chunk at index {i} for conversation {conversation_id} has no ID, generating a fallback.")
            chunk_id = f"{conversation_id}_chunk_{i}"

        chunk_metadata = {
            "conversation_id": conversation_id,
            "chunk_id": chunk_id,
            "chunk_index": i,
            "doctor_id": doctor_id,
            "language": language,
            "line_numbers": chunk_data["line_numbers"],
            "created_at": datetime.utcnow().isoformat(),
            "is_complete_conversation": False, # This is a chunk, not the full text
            "speaker_turn_preserved": True,
            "turn_ids": [chunk_id],
            **(metadata or {})
        }
        
        try:
            doc_id = await _store_single_document(chunk_data['content'], chunk_metadata)
            document_ids.append(doc_id)
            logger.info(f"Stored chunk {i+1}/{len(chunks)} with doc_id {doc_id}")
        except Exception as e:
            error_message = f"Failed to store chunk {i} for conversation {conversation_id}: {str(e)}"
            logger.error(error_message)

    # 4. Optionally store the full conversation as a single document
    if settings.store_full_conversation:
        full_text = "\n".join([f"{t['speaker']}: {t['text']}" for t in turns])
        full_text_metadata = {
            "conversation_id": conversation_id,
            "chunk_id": f"{conversation_id}_full",
            "chunk_index": -1, # Indicates full conversation
            "doctor_id": doctor_id,
            "language": language,
            "created_at": datetime.utcnow().isoformat(),
            "is_complete_conversation": True,
            **(metadata or {})
        }
        await _store_single_document(full_text, full_text_metadata)
        logger.info("Stored full conversation document.")

    return document_ids

async def _store_single_document(content: str, metadata: Dict[str, Any]) -> str:
    """Store a single document in OpenSearch."""
    try:
        rag_service = ConversationRAGService()
        await rag_service.initialize()
        return rag_service.vector_store.add_texts(
            texts=[content],
            metadatas=[metadata]
        )[0]
    except Exception as e:
        logger.error(f"Failed to store document: {str(e)}")
        raise