from src.core.settings.logging import logger
from .prompts import get_prompt
from .tools import clean_json_response, parse_json
from typing import List, Optional, Any
from .wrapper import _get_medical_generator

async def extract_medical_terms_with_llm(
    text: str,
    language: str = "en",
    medical_logger: Optional[Any] = None,
    langfuse_handler: Optional[Any] = None,
    conversation_id: Optional[str] = None,
) -> List[str]:
    """Extracts medical terms from a given text using an LLM."""
    # Get the medical generator service
    medical_generator = await _get_medical_generator()
    
    if not medical_generator._initialized or not medical_generator.llm:
        await medical_generator.initialize()

    if medical_logger:
        details={"text_length": len(text), "language": language}
        medical_logger.info(f"LLM_TERM_EXTRACTION_START Starting medical term extraction from text  details={details}")

    try:
        # Get the prompt template
        prompt = get_prompt()
        
        # Format the prompt with input variables
        formatted_messages = prompt.format_messages(
            language=language,
            text=text,
            agent_scratchpad=[]  # Initial empty scratchpad
        )
        
        # Invoke the LLM with the formatted messages
        response = await medical_generator.llm.ainvoke(
            formatted_messages,
            config={"callbacks": [langfuse_handler]} if langfuse_handler else None
        )
        content = response.content
        
        # Clean up the response content
        cleaned_content = clean_json_response(content)
        
        # Parse the JSON response using the robust parser
        parsed_data = parse_json(cleaned_content)
        
        if parsed_data is None:
            logger.warning(f"LLM returned non-JSON for term extraction: {cleaned_content}")
            return []
        
        if medical_logger:
            details={"terms_extracted": len(parsed_data), "sample_terms": parsed_data[:10]}
            medical_logger.info(f"LLM_TERM_EXTRACTION_COMPLETED Extracted {len(parsed_data)} medical terms using LLM. details={details}")
        
        return parsed_data
    
    except Exception as e:
        logger.error(f"Failed to extract medical terms with LLM: {str(e)}")
        if medical_logger:
            medical_logger.info(f"LLM_TERM_EXTRACTION_FAILED: Failed to extract medical terms with LLM: {str(e)}")
        return []