"""
Patient Information Extraction Service for NoteGen AI APIs.

This service orchestrates the extraction of patient demographic information
and sends the data to the NoteGen API backend.
"""

from typing import Dict, Any, Optional
from src.core.settings.logging import logger

from src.core.aws.opensearch_conversation_rag_service import ConversationRAGService
from src.core.azure_openai.azure_openai import MedicalSectionGenerator
from src.core.notegen.section_generation import NotegenAPIService
from src.modules.ai_agents.recording_consent_agent.agent import find_consent_chunk_id
from src.modules.ai_agents.patient_info_agent.agent import extract_patient_info_with_llm


class PatientInfoService:
    """
    Service for orchestrating patient demographic information extraction.
    It uses dedicated AI agents for the extraction logic.
    """

    def __init__(
        self,
        conversation_rag: ConversationRAGService,
        section_generator: MedicalSectionGenerator,
        notegen_api: NotegenAPIService,
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
        langfuse_handler: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Extract patient information using agents and send to NoteGen API backend.
        """
        try:
            logger.info(f"Starting patient information extraction for encounter {encounter_id}")

            # Convert transcript to a single text block for processing
            transcript_text = self._format_transcript_for_extraction(encounter_transcript)

            # Extract patient info using the dedicated agent
            patient_info = await extract_patient_info_with_llm(
                transcript_text, language, langfuse_handler, encounter_id
            )

            # Find the consent chunk ID using the specialized consent agent
            consent_chunk_id = await find_consent_chunk_id(
                conversation_id=encounter_id,
                language=language,
                langfuse_handler=langfuse_handler,
            )
            patient_info["recordingConsentChunkId"] = consent_chunk_id
            
            details = {"extracted_fields": list(patient_info.keys())}
            logger.info(f"Patient information extracted successfully, details={details}")

            # Send the complete payload to the NoteGen API backend
            api_response = await self._send_patient_info_to_api(
                encounter_id, patient_info, clinic_id
            )

            return {"success": True, "patient_info": patient_info, "api_response": api_response}

        except Exception as e:
            error_details = {
                "encounter_id": encounter_id,
                "language": language,
                "clinic_id": clinic_id,
                "transcript_length": len(encounter_transcript) if encounter_transcript else 0,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "has_conversation_rag": self.conversation_rag is not None,
                "has_section_generator": self.section_generator is not None,
                "has_notegen_api": self.notegen_api is not None
            }
            logger.error(f"Failed to extract patient information: {error_details}")
            return {"success": False, "error": str(e), "error_details": error_details}

    def _format_transcript_for_extraction(self, transcript: list) -> str:
        """Format transcript list into a single string for LLM processing."""
        formatted_lines = []
        for i, line_dict in enumerate(transcript):
            for speaker, text in line_dict.items():
                formatted_lines.append(f"Line {i+1} ({speaker}): {text}")
        return "\n".join(formatted_lines)

    async def _send_patient_info_to_api(
        self,
        encounter_id: str,
        patient_info: Dict[str, Any],
        clinic_id: str,
    ) -> Dict[str, Any]:
        """Send patient information to NoteGen API backend."""
        if not self.notegen_api._client:
            await self.notegen_api.initialize()
            
        url = f"{self.notegen_api.base_url}/{encounter_id}/patient-extracted"
        headers = {"x-clinic-id": str(clinic_id), "Content-Type": "application/json"}

        details = {
            "encounter_id": encounter_id, "clinic_id": clinic_id, "endpoint": url,
            "payload_fields": list(patient_info.keys()),
            "base_url": self.notegen_api.base_url,
            "full_url": url
        }
        logger.info(f"Sending patient info to NestJS backend, details={details}")

        try:
            # Try different HTTP methods if the endpoint doesn't support POST
            try:
                response = await self.notegen_api._client.post(url, json=patient_info, headers=headers)
                logger.debug(f"POST request successful for patient info: {response.status_code}")
            except Exception as post_error:
                logger.warning(f"POST request failed, trying PUT: {str(post_error)}")
                response = await self.notegen_api._client.put(url, json=patient_info, headers=headers)
                logger.debug(f"PUT request successful for patient info: {response.status_code}")
            
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            response_data = response.json() if response.content else {}
            logger.info(f"Successfully sent patient info for encounter {encounter_id}")
            return {"success": True, "status_code": response.status_code, "response_data": response_data}

        except Exception as e:
            error_details = {
                "encounter_id": encounter_id,
                "clinic_id": clinic_id,
                "endpoint": url,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "base_url": self.notegen_api.base_url,
                "payload_keys": list(patient_info.keys()) if patient_info else []
            }
            logger.error(f"Failed to send patient info to NestJS: {error_details}")
            return {"success": False, "error": str(e), "error_details": error_details}