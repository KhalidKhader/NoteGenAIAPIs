from src.core.neo4j.snomed_rag_service import SNOMEDRAGService
import asyncio
from typing import Optional

_snomed_rag_service: Optional[SNOMEDRAGService] = None
_current_loop = None

async def get_snomed_rag_service() -> SNOMEDRAGService:
    """Get or create the global SNOMED RAG service instance."""
    global _snomed_rag_service, _current_loop
    
    # Get current event loop
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None
    
    # Reset service if event loop changed (for tests)
    if _current_loop != current_loop:
        if _snomed_rag_service:
            try:
                await _snomed_rag_service.close()
            except:
                pass  # Ignore errors during cleanup
        _snomed_rag_service = None
        _current_loop = current_loop
    
    if _snomed_rag_service is None:
        _snomed_rag_service = SNOMEDRAGService()
        await _snomed_rag_service.initialize()
    
    return _snomed_rag_service


def return_snomed_rag_service() -> SNOMEDRAGService:
    """Return the global SNOMED RAG service instance."""
    return SNOMEDRAGService