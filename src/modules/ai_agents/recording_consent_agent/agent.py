"""
Recording Consent Agent - Finds consent statements in conversations using LLM with proper agent_scratchpad support.
"""
from src.core.settings.logging import logger
from .prompts import get_prompt
from typing import List, Optional, Any
from .wrapper import _get_medical_generator
from src.core.settings.config import settings

async def find_consent_chunk_id(
    conversation_id: str,
    language: str = 'en',
    langfuse_handler: Optional[Any] = None
) -> Optional[str]:
    """
    Finds the chunk_id of the turn where the patient gives consent to record, using an LLM for classification.
    Searches patient's text for consent keywords in either English or French.
    """
    # Get the medical generator service
    medical_generator = await _get_medical_generator()
    
    if not medical_generator._initialized or not medical_generator.llm:
        await medical_generator.initialize()

    # Get the prompt template
    prompt = get_prompt()
    
    try:
        search_query = {
            "size": 1000,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"metadata.conversation_id": conversation_id}},
                        {"term": {"metadata.speaker": "patient"}}
                    ]
                }
            },
            "_source": ["text", "content", "page_content", "metadata"]
        }
        # Get the conversation RAG service to access OpenSearch
        conversation_rag = medical_generator.conversation_rag
        if not conversation_rag or not conversation_rag.opensearch_client:
            logger.error("Conversation RAG service not properly initialized")
            return None
            
        response = conversation_rag.opensearch_client.search(
            index=settings.opensearch_index,
            body=search_query
        )

        for hit in response['hits']['hits']:
            source = hit['_source']
            content = (source.get('content') or 
                      source.get('text') or 
                      source.get('page_content', ''))
            
            # Format the prompt with input variables
            formatted_messages = prompt.format_messages(
                patient_text=content,
                agent_scratchpad=[]  # Initial empty scratchpad
            )
            
            # Call LLM with formatted messages
            try:
                llm_response = await medical_generator.llm.ainvoke(
                    formatted_messages,
                    config={"callbacks": [langfuse_handler]} if langfuse_handler else None
                )
                
                # Extract content from response
                llm_response = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
                logger.debug(f"LLM response for consent check: {llm_response[:100]}...")
            except Exception as e:
                logger.error(f"Failed to get LLM response for consent check: {str(e)}")
                return None
            
            if "CONSENT" in llm_response.upper():
                metadata = source.get('metadata', {})
                consent_chunk_id = metadata.get("chunk_id")
                if consent_chunk_id:
                    logger.info(f"Found consent in chunk {consent_chunk_id} for conversation {conversation_id} using LLM")
                    return consent_chunk_id
        
        logger.warning(f"Could not find a clear consent statement for conversation {conversation_id} using LLM.")
        return None

    except Exception as e:
        logger.error(f"Failed to find consent chunk for conversation {conversation_id} using LLM: {str(e)}")
        return None
