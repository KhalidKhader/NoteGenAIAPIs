"""
Patient Information Extraction Service for NoteGen AI APIs.

This service extracts patient demographic information from medical conversations
using LLM and conversation RAG, then sends the data to NoteGen API backend.
"""

import json
from typing import Dict, Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from src.core.logging import logger
from src.core.config import settings
from src.services.opensearch.opensearch_rag import ConversationRAGService
from src.services.openai.azure_openai import MedicalSectionGenerator
from src.services.notegen.notegen_api import NotegenAPIService
from src.templates.prompts import PATIENT_INFO_EXTRACTION_PROMPT, PATIENT_INFO_SYSTEM_PROMPT

class PatientInfoService:
    """
    Service for extracting patient demographic information from conversations.
    
    Extracts:
    - First name
    - Last name  
    - Date of birth
    - Gender
    - Recording consent status
    """
    
    def __init__(
        self,
        conversation_rag: ConversationRAGService,
        section_generator: MedicalSectionGenerator,
        notegen_api: NotegenAPIService
    ):
        self.conversation_rag = conversation_rag
        self.section_generator = section_generator
        self.notegen_api = notegen_api
    
    async def extract_and_send_patient_info(
        self,
        encounter_id: str,
        encounter_transcript: list,
        language: str,
        clinic_id: str,
        medical_logger: Optional[Any] = None,
        langfuse_handler: Optional[Any] = None,
        logger: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Extract patient information and send to NoteGen API backend.
        
        Args:
            encounter_id: Unique encounter identifier
            encounter_transcript: Full conversation transcript
            language: Language code (en/fr)
            clinic_id: Clinic identifier
            medical_logger: Medical compliance logger
            
        Returns:
            Result of extraction and API call
        """
        try:
            if medical_logger:
                medical_logger.info("Starting patient information extraction")
            
            # Convert transcript to text for LLM processing
            transcript_text = self._format_transcript_for_extraction(encounter_transcript)
            
            # Extract patient info using LLM with Langfuse tracing
            patient_info = await self._extract_patient_info_with_llm(
                transcript_text, language, medical_logger, langfuse_handler, encounter_id
            )
            
            # Find the consent chunk ID using the specialized RAG service method
            consent_chunk_id = await self.conversation_rag.find_consent_chunk_id(
                conversation_id=encounter_id,
                language=language,
                langfuse_handler=langfuse_handler
            )
            
            # Add the consent information to the patient_info payload
            patient_info["recordingConsentChunkId"] = consent_chunk_id
            
            if medical_logger:
                details={"extracted_fields": list(patient_info.keys())}
                medical_logger.info(f"Patient information extracted successfully, details={details}")
            
            # Send to NoteGen API backend
            api_response = await self._send_patient_info_to_api(
                encounter_id, patient_info, clinic_id, medical_logger
            )
            
            return {
                "success": True,
                "patient_info": patient_info,
                "api_response": api_response
            }
            
        except Exception as e:
            error_msg = f"Failed to extract patient information: {str(e)}"
            if medical_logger:
                medical_logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg
            }
    
    def _format_transcript_for_extraction(self, transcript: list) -> str:
        """Format transcript for LLM processing."""
        formatted_lines = []
        for i, line_dict in enumerate(transcript):
            for speaker, text in line_dict.items():
                formatted_lines.append(f"Line {i+1} ({speaker}): {text}")
        return "\n".join(formatted_lines)
    
    async def _extract_patient_info_with_llm(
        self,
        transcript_text: str,
        language: str,
        medical_logger: Optional[Any] = None,
        langfuse_handler: Optional[Any] = None,
        encounter_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract patient information using LLM."""
        
        # Get the appropriate prompt for the language
        prompt = PATIENT_INFO_EXTRACTION_PROMPT[language]
        
        system_prompt = PATIENT_INFO_SYSTEM_PROMPT
        
        # Ensure section generator is initialized
        if not self.section_generator._initialized:
            await self.section_generator.initialize()
        
        # Use the section generator's LLM with Langfuse tracing
        try:
            if medical_logger:
                details={
                        "language": language,
                        "transcript_length": len(transcript_text),
                        "encounter_id": encounter_id
                    }
                medical_logger.info(f"Starting LLM call for patient info extraction, details={details}")
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt.format(transcript=transcript_text)),
            ]
            
            # Create LLM call with Langfuse tracing
            if langfuse_handler:
                response = await self.section_generator.llm.ainvoke(
                    messages,
                    config={"callbacks": [langfuse_handler]}
                )
                # Extract text from response
                response_text = response.content.strip()
            else:
                response = await self.section_generator.llm.agenerate(
                    [messages]
                )
                # Extract text from response
                response_text = response.generations[0][0].text.strip()
            
            # Clean response if it contains markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            patient_info = json.loads(response_text)
            
            # The consent is now handled separately, so we ensure it's not in the base extraction
            patient_info.pop("recordingConsent", None)
            
            if medical_logger:
                details={
                        "response_length": len(response_text),
                        "extracted_fields": list(patient_info.keys()),
                        "encounter_id": encounter_id,
                        "language": language
                    }
                medical_logger.info(f"LLM extraction completed successfully, details={details}")
            
            return patient_info
            
        except json.JSONDecodeError as e:
            if medical_logger:
                medical_logger.error(f"JSON parsing error: {str(e)}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
        
        except Exception as e:
            if medical_logger:
                medical_logger.error(f"LLM extraction error: {str(e)}")
            raise
    
    async def _send_patient_info_to_api(
        self,
        encounter_id: str,
        patient_info: Dict[str, Any],
        clinic_id: str,
        medical_logger: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Send patient information to NoteGen API backend."""
        
        if not self.notegen_api._client:
            await self.notegen_api.initialize()
        
        url = f"{self.notegen_api.base_url}/{encounter_id}/patient-extracted"
        
        headers = {
            "x-clinic-id": str(clinic_id),
            "Content-Type": "application/json"
        }
        
        if medical_logger:
            details={
                    "encounter_id": encounter_id,
                    "clinic_id": clinic_id,
                    "endpoint": "internal/encounters/patient",
                    "full_url": url,
                    "method": "POST",
                    "headers": headers,
                    "payload_fields": list(patient_info.keys())
                }
            medical_logger.info(f"Sending patient info to NestJS backend endpoint, details={details}")
        
        try:
            response = await self.notegen_api._client.post(
                url,
                json=patient_info,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                response_data = response.json() if response.content else {}
                
                if medical_logger:
                    details={
                            "status_code": response.status_code,
                            "endpoint": "internal/encounters/patient-extracted",
                            "encounter_id": encounter_id,
                            "response_size": len(str(response_data)) if response_data else 0,
                            "clinic_id": clinic_id
                        }
                    medical_logger.info(f"Successfully sent patient info to NestJS backend details={details}")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_data": response_data
                }
            else:
                error_msg = f"NestJS API returned status {response.status_code}: {response.text}"
                if medical_logger:
                    details={
                            "status_code": response.status_code,
                            "endpoint": "internal/encounters/patient-extracted",
                            "encounter_id": encounter_id,
                            "clinic_id": clinic_id,
                            "response_text": response.text[:500]  # Limit response text length
                        }
                    medical_logger.error(f"NestJS API error: {error_msg}, details={details}")
                
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except Exception as e:
            error_msg = f"Failed to send patient info: {str(e)}"
            if medical_logger:
                medical_logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg
            }


# Global service instance
_patient_info_service: Optional[PatientInfoService] = None


async def get_patient_info_service() -> PatientInfoService:
    """Get the global patient info service instance."""
    global _patient_info_service
    if _patient_info_service is None:
        from src.services.opensearch.opensearch_rag import get_conversation_rag_service
        from src.services.openai.azure_openai import get_soap_generator_service
        from src.services.notegen.notegen_api import get_notegen_api_service
        
        conversation_rag = await get_conversation_rag_service()
        section_generator = await get_soap_generator_service()
        notegen_api = await get_notegen_api_service()
        
        _patient_info_service = PatientInfoService(
            conversation_rag=conversation_rag,
            section_generator=section_generator,
            notegen_api=notegen_api
        )
    
    return _patient_info_service 