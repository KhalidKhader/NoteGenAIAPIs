"""
Medical Section Generator Service for NoteGen AI APIs.

This service generates medical sections (SOAP notes and other templates) from conversations
using prompts provided by the NestJS backend. It integrates with RAG services for enhanced
medical accuracy and maintains line-number referencing for traceability.
"""

import time
import uuid
import json
from typing import Dict, List, Optional, Any, Union

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.core.config import settings
from src.core.logging import get_logger, MedicalProcessingLogger
from src.core.observability import get_observability_service
from src.models.api_models import LineReference
from src.models.api_models import GeneratedSection
from src.templates.prompts import (
    FACTUAL_CONSISTENCY_VALIDATION_PROMPT,
    MEDICAL_TERM_EXTRACTION_SYSTEM_PROMPT,
    MEDICAL_TERM_EXTRACTION_USER_PROMPT_TEMPLATE,
    SECTION_GENERATION_SYSTEM_PROMPT_TEMPLATE,
    SECTION_GENERATION_USER_PROMPT_TEMPLATE,
)
from src.services.conversation_rag import get_conversation_rag_service
from src.services.snomed_rag import get_snomed_rag_service
from src.services.pattern_learning import get_pattern_learning_service

logger = get_logger(__name__)


class MedicalSectionGenerator:
    """
    Medical Section Generator for SOAP notes and other medical templates.
    
    This service receives prompts from NestJS and generates medical sections with:
    - Medical term validation via SNOMED
    - Doctor preference application
    - Line-number referencing for traceability
    - RAG-enhanced context retrieval
    """
    
    def __init__(self):
        self.llm: Optional[AzureChatOpenAI] = None
        self.conversation_rag = None
        self.snomed_rag = None
        self.pattern_learning = None
        self._initialized = False
        
        # Performance tracking
        self.generation_stats = {
            "total_generations": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "average_processing_time": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize the medical section generator service."""
        if self._initialized:
            return
            
        logger.info("Initializing Medical Section Generator")
        
        try:
            # Initialize Azure OpenAI with medical-optimized settings
            self.llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                deployment_name=settings.azure_openai_deployment_name,
                model=settings.azure_openai_model,
                temperature=0.1,  # Low temperature for medical accuracy
                max_tokens=4000,
                request_timeout=60,
                max_retries=3
            )
            
            # Initialize RAG services
            self.conversation_rag = await get_conversation_rag_service()
            self.snomed_rag = await get_snomed_rag_service()
            self.pattern_learning = await get_pattern_learning_service()
            
            # Verify all services
            await self._verify_services()
            
            self._initialized = True
            logger.info("Medical Section Generator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Medical Section Generator: {str(e)}")
            raise RuntimeError(f"Section generator initialization failed: {str(e)}")
    
    async def _verify_services(self) -> None:
        """Verify all medical services are operational."""
        try:
            # Test LLM connection
            test_response = await self.llm.agenerate(
                [[HumanMessage(content="Test medical system connectivity.")]]
            )
            if not test_response.generations[0][0].text:
                raise RuntimeError("LLM test failed")
            
            # Test RAG services
            await self.conversation_rag.health_check()
            await self.snomed_rag.health_check()
            await self.pattern_learning.health_check()
            
            logger.info("All medical services verified and operational")
            
        except Exception as e:
            logger.error(f"Service verification failed: {str(e)}")
            raise
    
    def _update_stats(self, duration: float, success: bool) -> None:
        """Update generation statistics."""
        if success:
            self.generation_stats["successful_generations"] += 1
        else:
            self.generation_stats["failed_generations"] += 1
        
        self.generation_stats["total_generations"] += 1
        
        # Update average processing time
        total_gens = self.generation_stats["total_generations"]
        current_avg = self.generation_stats["average_processing_time"]
        self.generation_stats["average_processing_time"] = (
            (current_avg * (total_gens - 1) + duration) / total_gens
        )
    
    async def _get_factual_consistency_score(self, generated_text: str, context: str) -> (float, Dict[str, Any]):
        """Uses an LLM call to get a factual consistency score."""
        if not self.llm:
            return 0.5, {} # Default confidence, empty details

        prompt = FACTUAL_CONSISTENCY_VALIDATION_PROMPT.format(
            generated_content=generated_text,
            source_chunks=context
        )
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            cleaned_content = response.content.strip().strip("`").strip("json").strip()
            
            validation_data = json.loads(cleaned_content)
            score = validation_data.get("factualConsistencyScore", 5)
            normalized_score = min(max(score / 10.0, 0.0), 1.0)
            
            return normalized_score, validation_data

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.warning(f"Could not parse consistency score from LLM response: {e}")
        except Exception as e:
            logger.warning(f"Could not get consistency score due to an unexpected error: {e}")
        
        return 0.5, {"error": "Failed to get consistency score."} # Default confidence

    async def extract_medical_terms_with_llm(
        self,
        text: str,
        language: str = "en",
        medical_logger: Optional[MedicalProcessingLogger] = None
    ) -> List[str]:
        """Extracts medical terms from a given text using an LLM."""
        if not self._initialized or not self.llm:
            await self.initialize()

        if medical_logger:
            medical_logger.log_step(
                "LLM_TERM_EXTRACTION_START",
                f"Starting medical term extraction from text (length: {len(text)})",
                {"text_length": len(text), "language": language}
            )

        system_prompt = MEDICAL_TERM_EXTRACTION_SYSTEM_PROMPT
        
        prompt = MEDICAL_TERM_EXTRACTION_USER_PROMPT_TEMPLATE.format(
            text=text,
            language=language
        )
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt),
            ]
            
            response = await self.llm.ainvoke(messages)
            content = response.content
            
            # Clean up the response content
            cleaned_content = content.strip().strip("`").strip("json").strip()
            
            # The response should be a JSON string of a list.
            try:
                extracted_terms = json.loads(cleaned_content)
            except json.JSONDecodeError:
                logger.warning(f"LLM returned non-JSON for term extraction: {cleaned_content}")
                return []
            
            if not isinstance(extracted_terms, list):
                raise ValueError("LLM did not return a list.")

            # Validate that items are strings
            terms = [str(term) for term in extracted_terms]

            if medical_logger:
                medical_logger.log_step(
                    "LLM_TERM_EXTRACTION_COMPLETED",
                    f"Extracted {len(terms)} medical terms using LLM.",
                    {"terms_extracted": len(terms), "sample_terms": terms[:10]}
                )
            
            return terms
        
        except Exception as e:
            logger.error(f"Failed to extract medical terms with LLM: {str(e)}")
            if medical_logger:
                medical_logger.log_step(
                    "LLM_TERM_EXTRACTION_FAILED",
                    f"Failed to extract medical terms with LLM: {str(e)}",
                    {"error": str(e)}
                )
            return []

    async def generate_section_with_context(
        self,
        template_id: str,
        section_name: str,
        section_prompt: str,
        language: str,
        conversation_context_text: str,
        snomed_context: List[Dict[str, Any]],
        doctor_preferences: Dict[str, str],
        full_transcript: List[Dict[str, Any]],
        previous_sections_context: str = "",
        medical_logger: Optional[MedicalProcessingLogger] = None
    ) -> GeneratedSection:
        """
        DYNAMIC SECTION GENERATION - Handles ANY section type based on prompt.
        Returns a detailed GeneratedSection object with traceability.
        """
        if not self._initialized or not self.llm:
            await self.initialize()

        start_time = time.time()
        obs_service = await get_observability_service()
        
        parent_trace = obs_service.active_traces.get(medical_logger.encounter_id)
        generation_span = None

        if parent_trace:
            generation_span = parent_trace.generation(
                name=f"section-generation-{section_name.replace(' ', '-')}",
                metadata={
                    "section_name": section_name,
                    "template_id": template_id,
                    "language": language,
                    "total_context_chars": len(conversation_context_text)
                },
                tags=["section-generation", language]
            )

        # 1. Prepare context and prompts
        system_prompt = self._get_system_prompt(
            section_name,
            language,
            doctor_preferences,
            previous_sections_context,
            snomed_context
        )
        
        user_prompt = SECTION_GENERATION_USER_PROMPT_TEMPLATE.format(
            section_name=section_name,
            section_prompt=section_prompt,
            conversation_context_text=conversation_context_text
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        if generation_span:
            generation_span.update(input=[msg.model_dump() for msg in messages])

        # 2. Invoke LLM and process response
        note_content = ""
        validated_references = []
        llm_response = None
        
        try:
            llm_response = await self.llm.ainvoke(messages)
            content = llm_response.content
            
            # Clean and parse the JSON response
            cleaned_content = content.strip().strip("`").strip("json").strip()
            
            try:
                response_data = json.loads(cleaned_content)
                note_content = response_data.get("noteContent", "")
                
                raw_references = response_data.get("lineReferences", [])
                
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
                
                if generation_span:
                    generation_span.update(output=response_data)

            except (json.JSONDecodeError, TypeError, ValueError) as e:
                note_content = f"Error: Failed to parse LLM response. Raw output: {cleaned_content}"
                logger.error(f"Failed to parse LLM response for section '{section_name}': {e}. Raw output: {cleaned_content}")
                if generation_span:
                    generation_span.update(output={"error": str(e), "raw_output": cleaned_content}, level="ERROR")

        except Exception as e:
            note_content = f"Error: Failed to generate section. Raw output was not received from LLM."
            logger.error(f"Failed to generate section '{section_name}': {str(e)}")
            if generation_span:
                generation_span.update(output={"error": str(e)}, level="ERROR")

        # 3. Finalize section object and update stats
        duration = time.time() - start_time
        success = not note_content.startswith("Error:")
        self._update_stats(duration, success)
        
        # 4. Perform factual consistency check
        consistency_score, consistency_details = await self._get_factual_consistency_score(note_content, conversation_context_text)
        
        if generation_span:
            obs_service.score_trace(
                trace_id=parent_trace.id,
                name="factual-consistency",
                value=consistency_score,
                comment=json.dumps(consistency_details.get("justification", {}))
            )

        # 5. Log usage and end the generation span
        if generation_span and llm_response and llm_response.response_metadata and 'token_usage' in llm_response.response_metadata:
            usage = llm_response.response_metadata['token_usage']
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            obs_service.log_llm_usage(prompt_tokens, completion_tokens)
            generation_span.end(usage=usage, metadata={"parsed_successfully": success, "factual_consistency": consistency_details})
        elif generation_span:
            generation_span.end(metadata={"parsed_successfully": success, "factual_consistency": consistency_details})


        final_section = GeneratedSection(
            section_id=f"section_{uuid.uuid4().hex[:8]}",
            template_id=template_id,
            section_name=section_name,
            content=note_content,
            line_references=[ref.model_dump() for ref in validated_references],
            snomed_mappings=snomed_context or [],
            confidence_score=consistency_score,
            language=language,
            processing_metadata={
                "duration_seconds": duration,
                "model_name": self.llm.model_name if self.llm else "unknown",
                "context_chars_used": len(conversation_context_text),
                "factual_consistency_details": consistency_details
            }
        )

        if medical_logger:
            medical_logger.log_section_generation(final_section.section_id, section_name, final_section.dict())
            
        return final_section

    def _get_system_prompt(
        self,
        section_name: str,
        language: str,
        doctor_preferences: Dict[str, str],
        previous_sections: str,
        snomed_context: List[Dict[str, Any]]
    ) -> str:
        """Builds the dynamic system prompt for the LLM."""
        
        snomed_text = json.dumps(snomed_context, indent=2) if snomed_context else "No SNOMED terms provided."
        prefs_text = json.dumps(doctor_preferences, indent=2) if doctor_preferences else "No specific preferences."
        prev_sections_text = previous_sections if previous_sections else "This is the first section."

        return SECTION_GENERATION_SYSTEM_PROMPT_TEMPLATE.format(
            section_name=section_name,
            language=language,
            snomed_context=snomed_text,
            doctor_preferences=prefs_text,
            previous_sections=prev_sections_text
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for medical system monitoring."""
        if not self._initialized:
            return {"status": "unhealthy", "error": "Service not initialized"}
        
        try:
            # Test LLM
            test_response = await self.llm.agenerate(
                [[HumanMessage(content="Test")]]
            )
            llm_healthy = bool(test_response.generations[0][0].text)
            
            # Test RAG services
            conv_health = await self.conversation_rag.health_check()
            snomed_health = await self.snomed_rag.health_check()
            pattern_health = await self.pattern_learning.health_check()
            
            return {
                "status": "healthy",
                "services": {
                    "llm": llm_healthy,
                    "conversation_rag": conv_health.get("status") == "healthy",
                    "snomed_rag": snomed_health.get("status") == "healthy",
                    "pattern_learning": pattern_health.get("status") == "healthy"
                },
                "statistics": self.generation_stats
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# =============================================================================
# Service Instance Management
# =============================================================================

_section_generator_instance: Optional[MedicalSectionGenerator] = None

async def get_section_generator_service() -> MedicalSectionGenerator:
    """Get singleton instance of medical section generator service."""
    global _section_generator_instance
    
    if _section_generator_instance is None:
        _section_generator_instance = MedicalSectionGenerator()
        await _section_generator_instance.initialize()
    
    return _section_generator_instance

# Backward compatibility alias
async def get_soap_generator_service() -> MedicalSectionGenerator:
    """Backward compatibility alias for get_section_generator_service."""
    return await get_section_generator_service()
