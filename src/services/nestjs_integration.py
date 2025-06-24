"""
NestJS Integration Service for NoteGen AI APIs.

This service handles communication with the NestJS backend to send generated
medical sections and manage the integration workflow.
"""

import asyncio
from typing import Dict, Any, Optional

import httpx
from src.core.logging import get_logger, MedicalProcessingLogger

logger = get_logger(__name__)


class NestJSIntegrationService:
    """
    Service for integrating with NestJS backend.
    
    Handles:
    - Sending generated sections to NestJS
    - Managing job status updates
    - Error handling and retry logic
    - Comprehensive logging for medical compliance
    """
    
    def __init__(self):
        self.base_url = "https://9134-196-159-22-237.ngrok-free.app"
        self.timeout = 30.0
        self.max_retries = 3
        self._client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self) -> None:
        """Initialize the NestJS integration service."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "NoteGen-AI-APIs/1.0"
            }
        )
        logger.info("NestJS Integration Service initialized")
    
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
        Send a generated section to NestJS backend.
        
        Args:
            encounter_id: The encounter ID
            section_id: The section ID from NestJS
            note_content: The generated content
            clinic_id: The clinic ID
            job_id: Our internal job ID for tracking
            medical_logger: Logger for medical compliance
        
        Returns:
            Response data from NestJS
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
                f"🚀 Sending section {section_id} to NestJS",
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
                        f"NestJS Response Status: {response.status_code}",
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
                            f"✅ Successfully sent section {section_id} to NestJS",
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
                    error_msg = f"NestJS returned status {response.status_code}"
                    try:
                        error_response = response.json()
                        error_msg += f": {error_response}"
                    except:
                        error_msg += f": {response.text}"
                    
                    if medical_logger:
                        medical_logger.log(
                            f"❌ NestJS error on attempt {attempt + 1}: {error_msg}",
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
                error_msg = f"Timeout sending to NestJS: {str(e)}"
                last_error = error_msg
                
                if medical_logger:
                    medical_logger.log(
                        f"⏰ Timeout on attempt {attempt + 1}: {error_msg}",
                        "WARNING",
                        details={"attempt": attempt + 1, "error": str(e)}
                    )
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                error_msg = f"Unexpected error sending to NestJS: {str(e)}"
                last_error = error_msg
                
                if medical_logger:
                    medical_logger.log(
                        f"💥 Unexpected error on attempt {attempt + 1}: {error_msg}",
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
                f"🔥 Failed to send section {section_id} to NestJS after {self.max_retries} attempts",
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
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if NestJS backend is reachable."""
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
_nestjs_service: Optional[NestJSIntegrationService] = None


async def get_nestjs_integration_service() -> NestJSIntegrationService:
    """Get the global NestJS integration service instance."""
    global _nestjs_service
    if _nestjs_service is None:
        _nestjs_service = NestJSIntegrationService()
        await _nestjs_service.initialize()
    return _nestjs_service 