from typing import Dict, List, Any
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .opensearch_conversation_rag_service import ConversationRAGService
async def retrieve_relevant_chunks(
    conversation_id: str, 
    query: str, 
    k: int = settings.retrieval_k_value
) -> List[Dict[str, Any]]:
    """Retrieve relevant conversation chunks using semantic search."""
    rag_service = ConversationRAGService()
    if not rag_service._initialized:
        await rag_service.initialize()
    try:
        logger.info(f"Retrieving {k} chunks for conversation {conversation_id}")
        search_query = {
            "size": k,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"metadata.conversation_id": conversation_id}},
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["text^2", "content^2", "page_content^2", "metadata.speaker"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            },
            "_source": ["text", "content", "page_content", "metadata"]
        }
        response = rag_service.opensearch_client.search(
            index=settings.opensearch_index,
            body=search_query
        )
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            metadata = source.get('metadata', {})
            content = (source.get('content') or 
                        source.get('text') or 
                        source.get('page_content', ''))
            if not content or 'chunk_id' not in metadata:
                continue
            result = {
                "content": content,
                "chunk_id": metadata.get("chunk_id", "unknown"),
                "line_numbers": metadata.get("line_numbers", []),
                "speaker": metadata.get("speaker", "Unknown"),
                "chunk_index": metadata.get("chunk_index", 0),
                "score": hit['_score'],
                "conversation_id": conversation_id
            }
            results.append(result)
        logger.info(f"Retrieved {len(results)} relevant chunks")
        return results
    except Exception as e:
        logger.error(f"Failed to retrieve chunks: {str(e)}")
        raise RuntimeError(f"RAG retrieval failed: {str(e)}")