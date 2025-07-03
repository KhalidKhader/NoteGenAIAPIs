"""
Section Generation Agent - Handles dynamic section generation with proper agent_scratchpad support.
"""
from src.core.settings.logging import logger
from .prompts import get_prompt
from .tools import parse_section_json, clean_json_response
from .wrapper import _get_medical_generator
from typing import Dict, Optional, Any, List, Union
import time
import uuid
from datetime import datetime
from .schema import LineReference, SectionGenerationStatus, GeneratedSection
import json

async def generate_section_with_context(
    template_id: str,
    section_name: str,
    section_prompt: str,
    language: str,
    conversation_context_text: str,
    snomed_context: List[Dict[str, Any]],
    doctor_preferences: Dict[str, str],
    full_transcript: List[Dict[str, Any]],
    previous_sections_context: str = "",
    langfuse_handler: Optional[Any] = None,
    conversation_id: Optional[str] = None,
    doctor_id: Optional[str] = None,
) -> GeneratedSection:
    """
    DYNAMIC SECTION GENERATION - Handles ANY section type based on prompt.
    Returns a detailed GeneratedSection object with traceability.
    """
    medical_generator = await _get_medical_generator()
    
    if not medical_generator._initialized or not medical_generator.llm:
        await medical_generator.initialize()

    start_time = time.time()

    # 1. Prepare context and prompts
    snomed_text = json.dumps(snomed_context, indent=2) if snomed_context else "No SNOMED terms provided."
    prefs_text = json.dumps(doctor_preferences, indent=2) if doctor_preferences else "No specific preferences."
    prev_sections_text = previous_sections_context if previous_sections_context else "This is the first section."

    # Get the prompt template
    prompt = get_prompt()
    
    # Format the prompt with input variables
    formatted_messages = prompt.format_messages(
        section_name=section_name,
        language=language,
        snomed_context=snomed_text,
        doctor_preferences=prefs_text,
        previous_sections=prev_sections_text,
        section_prompt=section_prompt,
        conversation_context_text=conversation_context_text,
        agent_scratchpad=[]  # Initial empty scratchpad
    )

    # 2. Invoke LLM and process response with enhanced tracing
    note_content = ""
    validated_references = []
    
    try:
        llm_response = await medical_generator.llm.ainvoke(
            formatted_messages,
            config={"callbacks": [langfuse_handler]} if langfuse_handler else None
        )
        content = llm_response.content
        logger.info(f"LLM response: {content}")
        
        # Clean and parse the JSON response using the enhanced tools
        cleaned_content = clean_json_response(content)
        logger.debug(f"Cleaned content: {cleaned_content[:200]}...")
        
        parsed_data = parse_section_json(cleaned_content)
        
        if parsed_data is None:
            note_content = f"Error: Failed to parse LLM response. Raw output: {cleaned_content}"
            logger.error(f"Failed to parse LLM response for section '{section_name}'. Raw output: {cleaned_content}")
        else:
            try:
                note_content = parsed_data.get("noteContent", "")
                raw_references = parsed_data.get("lineReferences", [])
            
                if raw_references:
                    if isinstance(raw_references[0], int):
                        # Handle old integer-only format
                        for line_num in raw_references:
                            line_text = "Referenced line not found in transcript."
                            adj_line_num = line_num - 1
                            if 0 <= adj_line_num < len(full_transcript):
                                line_item = full_transcript[adj_line_num]
                                line_text = next((v for k, v in line_item.items() if k.lower() != 'id'), "Text not found")
                            
                            validated_references.append(LineReference(
                                line_number=line_num, text=line_text, start_char=0, end_char=len(line_text)
                            ))
                    else:
                        # Handle new detailed object format
                        for ref_data in raw_references:
                            if isinstance(ref_data, dict) and all(k in ref_data for k in ["line_number", "start_char", "end_char", "text"]):
                                validated_references.append(LineReference(**ref_data))
                            else:
                                logger.warning(f"Discarding incomplete line reference from LLM: {ref_data}")
            
            except (TypeError, ValueError) as e:
                note_content = f"Error: Failed to parse LLM response. Raw output: {parsed_data}"
                logger.error(f"Failed to parse LLM response for section '{section_name}': {e}. Raw output: {parsed_data}")

    except Exception as e:
        note_content = f"Error: Failed to generate section. Raw output was not received from LLM."
        logger.error(f"Failed to generate section '{section_name}': {str(e)}")

    # 3. Finalize section object and update stats
    duration = time.time() - start_time
    success = not note_content.startswith("Error:")
    medical_generator._update_stats(duration, success)

    # Create generation status
    generation_status = SectionGenerationStatus(
        status="SUCCESS" if not note_content.startswith("Error:") else "FAILED",
        attempt_count=1,
        max_attempts=1,
        error_message=note_content if note_content.startswith("Error:") else None,
        error_trace=note_content if note_content.startswith("Error:") else None,
        last_attempt_time=datetime.now()
    )

    final_section = GeneratedSection(
        section_id=f"section_{uuid.uuid4().hex[:8]}",
        template_id=template_id,
        section_name=section_name,
        content=note_content,
        line_references=[ref.model_dump() for ref in validated_references],
        snomed_mappings=snomed_context or [],
        language=language,
        processing_metadata={
            "duration_seconds": duration,
            "model_name": medical_generator.llm.model_name if medical_generator.llm else "unknown",
            "context_chars_used": len(conversation_context_text),
        },
        generation_status=generation_status
    )

    logger.info(f'{final_section.section_id}, {section_name}, {final_section.dict()}')
        
    return final_section


