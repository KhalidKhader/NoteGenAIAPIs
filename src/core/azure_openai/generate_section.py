"""
Section Generation Agent - Handles dynamic section generation with proper agent_scratchpad support.
"""
from src.core.settings.logging import logger
from typing import Dict, Optional, Any, List, Union
import time
import asyncio
import traceback
from datetime import datetime
from src.modules.ai_agents.section_generation_agent.schema import SectionGenerationResult
from src.modules.ai_agents.section_generation_agent.agent import generate_section_with_context


async def generate_section(
    section_id: Union[str, int],
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
    max_attempts: int = 3,
) -> SectionGenerationResult:
    """
    Generate a section with retry logic and comprehensive error handling.
    
    This method implements the 3-attempt retry pattern:
    - Attempt 1-3: Try to generate the section
    - On failure: Log error, wait briefly, retry
    - After max attempts: Return failure result with error details
    - On success: Return success result with generated content
    
    Returns SectionGenerationResult with status, content, and error details.
    """
    start_time = time.time()
    last_error = None
    last_error_trace = None
    

    details={
            "section_id": section_id,
            "section_name": section_name,
            "template_id": template_id,
            "max_attempts": max_attempts
        }
    logger.info(f"Starting section generation with retry logic for '{section_name}' (max {max_attempts} attempts), details={details}")

    for attempt in range(1, max_attempts + 1):
        try:

            details={"attempt": attempt, "section_id": section_id}
            logger.info(f"Attempt {attempt}/{max_attempts} for section {section_name}, details={details}")
            
            # Call the original generation method
            generated_section = await generate_section_with_context(
                template_id=template_id,
                section_name=section_name,
                section_prompt=section_prompt,
                language=language,
                conversation_context_text=conversation_context_text,
                snomed_context=snomed_context,
                doctor_preferences=doctor_preferences,
                full_transcript=full_transcript,
                previous_sections_context=previous_sections_context,
                langfuse_handler=langfuse_handler,
                conversation_id=conversation_id,
                doctor_id=doctor_id
            )
            
            # Check if generation was successful (not an error message)
            if not generated_section.content.startswith("Error:"):
                processing_time = time.time() - start_time
                

                details={
                        "section_id": section_id,
                        "attempt": attempt,
                        "processing_time": processing_time,
                        "content_length": len(generated_section.content),
                    }
                logger.info(f"Section {section_name} generated successfully on attempt {attempt}, details={details}")
                
                # Return success result
                return SectionGenerationResult(
                    sectionId=section_id,
                    section_name=section_name,
                    status="SUCCESS",
                    content=generated_section.content,
                    errorMessage="",  # Empty on success
                    attempt_count=attempt,
                    processing_time=processing_time,
                    line_references=generated_section.line_references,
                    snomed_mappings=generated_section.snomed_mappings,
                    language=generated_section.language,
                    processing_metadata=generated_section.processing_metadata,
                    doctor_preferences=bool(doctor_preferences)  # Indicate if preferences were applied
                )
            else:
                # Generation returned an error message
                error_msg = generated_section.content
                last_error = f"Generation failed on attempt {attempt}: {error_msg}"
                last_error_trace = error_msg
                
                
                details={
                            "section_id": section_id,
                            "attempt": attempt,
                            "error": error_msg
                        }
                logger.error(f"Section {section_name} generation failed on attempt {attempt}: {error_msg}, details={details}")
            
        except Exception as e:
            # Unexpected exception during generation
            error_msg = str(e)
            error_trace = traceback.format_exc()
            last_error = f"Exception on attempt {attempt}: {error_msg}"
            last_error_trace = error_trace
            
            
            details={
                        "section_id": section_id,
                        "attempt": attempt,
                        "error": error_msg,
                        "trace": error_trace
                    }
            logger.error(f"Exception during section '{section_name}' generation on attempt {attempt}, details={details}")
        
        # Wait before retry (except on last attempt)
        if attempt < max_attempts:
            wait_time = min(2 ** (attempt - 1), 10)  # Exponential backoff, max 10 seconds
            
            logger.warning(f"Waiting {wait_time} seconds before retry attempt {attempt + 1}")
            await asyncio.sleep(wait_time)
    
    # All attempts failed - return failure result
    processing_time = time.time() - start_time
    final_error = last_error or f"All {max_attempts} attempts failed for section '{section_name}'"
    final_trace = last_error_trace or "No detailed error trace available"
    
    
    details={
                "section_id": section_id,
                "total_attempts": max_attempts,
                "total_processing_time": processing_time,
                "final_error": final_error,
                "error_trace": final_trace
            }
    logger.error(f"Section '{section_name}' generation failed after {max_attempts} attempts, details={details}")
    
    return SectionGenerationResult(
        sectionId=section_id,
        section_name=section_name,
        status="FAILED",
        content="",  # Empty content on failure
        errorMessage=final_error,
        error_trace=final_trace,
        attempt_count=max_attempts,
        processing_time=processing_time,
        doctor_preferences=bool(doctor_preferences)  # Indicate if preferences were applied
    )