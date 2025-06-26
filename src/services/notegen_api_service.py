"""
NoteGen API Service for NoteGen AI APIs.

This service handles communication with the NoteGen backend (formerly NestJS) 
to send generated medical sections and manage the integration workflow.
"""

import asyncio
from typing import Dict, Any, Optional

import httpx
from src.core.config import settings
from src.core.logging import get_logger, MedicalProcessingLogger

logger = get_logger(__name__)


class NotegenAPIService:
    """
    Service for integrating with NoteGen API backend.
    
    Handles:
    - Sending generated sections to NoteGen API backend
    - Managing job status updates
    - Error handling and retry logic
    - Comprehensive logging for medical compliance
    """
    
    def __init__(self):
        self.base_url = settings.notegen_api_base_url
        self.timeout = settings.notegen_api_timeout
        self.max_retries = settings.notegen_api_max_retries
        self._client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self) -> None:
        """Initialize the NoteGen API integration service."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "NoteGen-AI-APIs/1.0"
            }
        )
        logger.info("NoteGen API Integration Service initialized")
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
    
    async def send_generated_section(
        self,
        encounter_id: str,
        section_id: int,
        note_content: str,
        clinic_id: str,
        job_id: str,
        medical_logger: Optional[MedicalProcessingLogger] = None
    ) -> Dict[str, Any]:
        """
        Send a generated section to NoteGen API backend.
        
        Args:
            encounter_id: The encounter ID
            section_id: The section ID from NoteGen API backend
            note_content: The generated content
            clinic_id: The clinic ID
            job_id: Our internal job ID for tracking
            medical_logger: Logger for medical compliance
        
        Returns:
            Response data from NoteGen API backend
        """
        if not self._client:
            await self.initialize()
        
        url = f"{self.base_url}/internal/encounters/{encounter_id}/notes"
        
        payload = {
            "sectionId": section_id,
            "noteContent": note_content
        }
        
        headers = {
            "x-clinic-id": str(clinic_id),
            "Content-Type": "application/json"
        }
        
        if medical_logger:
            medical_logger.log(
                f"Sending section {section_id} to NoteGen API backend",
                "INFO",
                details={
                    "encounter_id": encounter_id,
                    "section_id": section_id,
                    "clinic_id": clinic_id,
                    "job_id": job_id,
                    "url": url,
                    "content_length": len(note_content)
                }
            )
        
        # Retry logic for robust delivery
        last_error = None
        for attempt in range(self.max_retries):
            try:
                if medical_logger:
                    medical_logger.log(
                        f"Attempt {attempt + 1}/{self.max_retries} to send section {section_id}",
                        "DEBUG"
                    )
                
                response = await self._client.post(
                    url,
                    json=payload,
                    headers=headers
                )
                
                # Log the response
                if medical_logger:
                    medical_logger.log(
                        f"NoteGen API Response Status: {response.status_code}",
                        "DEBUG",
                        details={
                            "status_code": response.status_code,
                            "response_headers": dict(response.headers),
                            "attempt": attempt + 1
                        }
                    )
                
                if response.status_code == 200 or response.status_code == 201:
                    response_data = response.json() if response.content else {}
                    
                    if medical_logger:
                        medical_logger.log(
                            f"Successfully sent section {section_id} to NoteGen API backend",
                            "INFO",
                            details={
                                "response_data": response_data,
                                "attempt": attempt + 1,
                                "final_status": "SUCCESS"
                            }
                        )
                    
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "response_data": response_data,
                        "attempt": attempt + 1
                    }
                else:
                    error_msg = f"NoteGen API backend returned status {response.status_code}"
                    try:
                        error_response = response.json()
                        error_msg += f": {error_response}"
                    except:
                        error_msg += f": {response.text}"
                    
                    if medical_logger:
                        medical_logger.log(
                            f"NoteGen API error on attempt {attempt + 1}: {error_msg}",
                            "WARNING",
                            details={
                                "status_code": response.status_code,
                                "response_text": response.text,
                                "attempt": attempt + 1
                            }
                        )
                    
                    last_error = error_msg
                    
                    # Don't retry on client errors (4xx)
                    if 400 <= response.status_code < 500:
                        break
                    
                    # Wait before retry for server errors
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            except httpx.TimeoutException as e:
                error_msg = f"Timeout sending to NoteGen API backend: {str(e)}"
                last_error = error_msg
                
                if medical_logger:
                    medical_logger.log(
                        f"Timeout on attempt {attempt + 1}: {error_msg}",
                        "WARNING",
                        details={"attempt": attempt + 1, "error": str(e)}
                    )
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                error_msg = f"Unexpected error sending to NoteGen API backend: {str(e)}"
                last_error = error_msg
                
                if medical_logger:
                    medical_logger.log(
                        f"Unexpected error on attempt {attempt + 1}: {error_msg}",
                        "ERROR",
                        details={
                            "attempt": attempt + 1,
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    )
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        # All attempts failed
        if medical_logger:
            medical_logger.log(
                f"Failed to send section {section_id} to NoteGen API backend after {self.max_retries} attempts",
                "ERROR",
                details={
                    "final_error": last_error,
                    "total_attempts": self.max_retries,
                    "encounter_id": encounter_id,
                    "section_id": section_id
                }
            )
        
        return {
            "success": False,
            "error": last_error,
            "attempts": self.max_retries
        }
    
    async def send_section_result(
        self,
        encounter_id: str,
        section_id: int,
        section_result: 'SectionGenerationResult',
        clinic_id: str,
        job_id: str,
        medical_logger: Optional[MedicalProcessingLogger] = None
    ) -> Dict[str, Any]:
        """
        Send a section generation result (success or failure) to NoteGen API backend.
        
        This method handles both successful and failed section generations,
        providing comprehensive status and error information to the backend.
        
        Args:
            encounter_id: The encounter ID
            section_id: The section ID from NoteGen API backend
            section_result: The SectionGenerationResult with status and content
            clinic_id: The clinic ID
            job_id: Our internal job ID for tracking
            medical_logger: Logger for medical compliance
        
        Returns:
            Response data from NoteGen API backend
        """
        if not self._client:
            await self.initialize()
        
        url = f"{self.base_url}/internal/encounters/{encounter_id}/notes"
        
        # Prepare payload based on section result status
        if section_result.status == "success":
            payload = {
                "sectionId": section_id,
                "noteContent": section_result.content,
                "status": "success",
                "metadata": {
                    "attempt_count": section_result.attempt_count,
                    "processing_time": section_result.processing_time,
                    "confidence_score": section_result.confidence_score,
                    "line_references_count": len(section_result.line_references),
                    "snomed_mappings_count": len(section_result.snomed_mappings)
                }
            }
        else:
            payload = {
                "sectionId": section_id,
                "noteContent": f"GENERATION_FAILED: {section_result.error_message}",
                "status": "failed",
                "error": {
                    "message": section_result.error_message,
                    "trace": section_result.error_trace,
                    "attempt_count": section_result.attempt_count,
                    "processing_time": section_result.processing_time
                }
            }
        
        headers = {
            "x-clinic-id": str(clinic_id),
            "Content-Type": "application/json"
        }
        
        if medical_logger:
            medical_logger.log(
                f"Sending section result {section_id} ({section_result.status}) to NoteGen API backend",
                "INFO",
                details={
                    "encounter_id": encounter_id,
                    "section_id": section_id,
                    "section_name": section_result.section_name,
                    "status": section_result.status,
                    "attempt_count": section_result.attempt_count,
                    "clinic_id": clinic_id,
                    "job_id": job_id,
                    "url": url
                }
            )
        
        # Use the existing retry logic
        return await self.send_generated_section(
            encounter_id=encounter_id,
            section_id=section_id,
            note_content=payload["noteContent"],
            clinic_id=clinic_id,
            job_id=job_id,
            medical_logger=medical_logger
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if NoteGen API backend is reachable."""
        if not self._client:
            await self.initialize()
        
        try:
            response = await self._client.get(f"{self.base_url}/health", timeout=5.0)
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global service instance
_notegen_api_service: Optional[NotegenAPIService] = None


async def get_notegen_api_service() -> NotegenAPIService:
    """Get the global NoteGen API service instance."""
    global _notegen_api_service
    if _notegen_api_service is None:
        _notegen_api_service = NotegenAPIService()
        await _notegen_api_service.initialize()
    return _notegen_api_service
