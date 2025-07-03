"""
Patient Info Extraction Agent - Extracts patient information using LLM with proper agent_scratchpad support.
"""
from src.core.settings.logging import logger
from .prompts import get_prompt
from .tools import parse_json, clean_json_response
from .wrapper import _get_medical_generator
from typing import Dict, Optional, Any
import json

async def extract_patient_info_with_llm(
    transcript_text: str,
    language: str,
    langfuse_handler: Optional[Any] = None,
    encounter_id: Optional[str] = None
) -> Dict[str, Any]:
    """Extract patient information using an LLM as a standalone agent function."""
    
    # Get the medical generator service which contains the LLM
    medical_generator = await _get_medical_generator()
    if not medical_generator._initialized:
        await medical_generator.initialize()
    
    # Get the appropriate prompt template for the language
    prompt = get_prompt(language)
    
    try:
        details = {
            "language": language,
            "transcript_length": len(transcript_text),
            "encounter_id": encounter_id
        }
        logger.info(f"Starting LLM call for patient info extraction, details={details}")
        
        # Format the prompt with input variables
        formatted_messages = prompt.format_messages(
            transcript=transcript_text,
            agent_scratchpad=[]  # Initial empty scratchpad
        )
        
        # Invoke the LLM with formatted messages
        response = await medical_generator.llm.ainvoke(
            formatted_messages,
            config={"callbacks": [langfuse_handler] if langfuse_handler else None}
        )
        response_text = response.content
        
        # Clean and parse the response
        cleaned_response = clean_json_response(response_text)
        patient_info = parse_json(cleaned_response)
        
        if not patient_info:
            raise ValueError(f"Invalid JSON response from LLM: {cleaned_response}")
        
        # The consent is now handled separately, so we ensure it's not in the base extraction
        if isinstance(patient_info, dict):
            patient_info.pop("recordingConsent", None)
            
            details = {
                "response_length": len(response_text),
                "extracted_fields": list(patient_info.keys()) if isinstance(patient_info, dict) else [],
                "encounter_id": encounter_id,
                "language": language
            }
            logger.info(f"LLM extraction completed successfully, details={details}")
            
            return patient_info
    
    except Exception as e:
        logger.error(f"LLM extraction error for encounter {encounter_id}: {str(e)}")
        raise