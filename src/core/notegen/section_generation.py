"""
NoteGen API Service for NoteGen AI APIs.

This service handles communication with the NoteGen backend (formerly NestJS) 
to send generated medical sections and manage the integration workflow.
"""

import asyncio
from typing import Dict, Any, Optional

import httpx
from src.core.settings.config import settings
from src.core.settings.logging import logger

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
        payload: Dict[str, Any],
        clinic_id: str,
        job_id: str,
    ) -> Dict[str, Any]:
        """
        Send a generated section to NoteGen API backend.
        
        Args:
            encounter_id: The encounter ID
            section_id: The section ID from NoteGen API backend
            payload: The complete payload to send
            clinic_id: The clinic ID
            job_id: Our internal job ID for tracking
            logger: Logger for medical compliance
        
        Returns:
            Response data from NoteGen API backend
        """
        if not self._client:
            await self.initialize()
        
        url = f"{self.base_url}/{encounter_id}/notes"
        
        headers = {
            "x-clinic-id": str(clinic_id),
            "Content-Type": "application/json"
        }
        
        
        details={
                    "encounter_id": encounter_id,
                    "section_id": section_id,
                    "clinic_id": clinic_id,
                    "job_id": job_id,
                    "url": url,
                    "status": payload.get("status"),
                    "is_last_section": payload.get("lastSection", False)
                }
        logger.info(f"Sending section {section_id} to NoteGen API backend details={details}")
        
        # Retry logic for robust delivery
        last_error = None
        for attempt in range(self.max_retries):
            try:
                
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} to send section {section_id}")
                
                # Try POST first, fallback to PUT if needed
                try:
                    response = await self._client.post(
                        url,
                        json=payload,
                        headers=headers
                    )
                except Exception as post_error:
                    logger.warning(f"POST request failed, trying PUT: {str(post_error)}")
                    response = await self._client.put(
                        url,
                        json=payload,
                        headers=headers
                    )
                
                
                
                # Log the response
                
                details={
                            "status_code": response.status_code,
                            "response_headers": dict(response.headers),
                            "attempt": attempt + 1
                        }
                logger.info(f"NoteGen API Response Status: {response.status_code} details={details}")
                
                if response.status_code == 200 or response.status_code == 201:
                    response_data = response.json() if response.content else {}
                    
                    
                    details={
                                "response_data": response_data,
                                "attempt": attempt + 1,
                                "final_status": "SUCCESS"
                            }
                    logger.info(f"Successfully sent section {section_id} to NoteGen API backend")
                    
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
                    
                        details={
                                "status_code": response.status_code,
                                "response_text": response.text,
                                "attempt": attempt + 1
                            }
                        logger.warning(f"NoteGen API error on attempt {attempt + 1}: {error_msg} details={details}")
                    
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
                
                
                details={"attempt": attempt + 1, "error": str(e)}
                logger.warning(f"Timeout on attempt {attempt + 1}: {error_msg}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                error_msg = f"Unexpected error sending to NoteGen API backend: {str(e)}"
                last_error = error_msg
                
                
                details={
                            "attempt": attempt + 1,
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                logger.error(f"Unexpected error on attempt {attempt + 1}: {error_msg}, details={details}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        # All attempts failed
            details={
                    "final_error": last_error,
                    "total_attempts": self.max_retries,
                    "encounter_id": encounter_id,
                    "section_id": section_id
                }
            logger.error(
                f"Failed to send section {section_id} to NoteGen API backend after {self.max_retries} attempts, details={details}")
        
        return {
            "success": False,
            "error": last_error,
            "attempts": self.max_retries
        }
    
    async def send_section_result(
        self,
        encounter_id: str,
        section_id: int,
        section_result: str,
        clinic_id: str,
        job_id: str,
        is_last_section: bool = False,
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
            is_last_section: Indicates if this is the last section
            logger: Logger for medical compliance
        
        Returns:
            Response data from NoteGen API backend
        """
        if not self._client:
            await self.initialize()
            
        url = f"{self.base_url}/{encounter_id}/notes"
        
        # Prepare payload based on section result status
        if section_result.status == "SUCCESS":
            payload = {
                "sectionId": section_id,
                "content": section_result.content,
                "errorMessage": "",
                "status": "SUCCESS",
                "lastSection": is_last_section,
                "metadata": {
                    "attempt_count": section_result.attempt_count,
                    "processing_time": section_result.processing_time,
                    "line_references_count": len(section_result.line_references),
                    "snomed_mappings_count": len(section_result.snomed_mappings)
                }
            }
        else:
            payload = {
                "sectionId": section_id,
                "content": "",
                "errorMessage": section_result.errorMessage,
                "status": "FAILED",
                "lastSection": is_last_section,
                "error": {
                    "message": section_result.errorMessage,
                    "trace": section_result.error_trace,
                    "attempt_count": section_result.attempt_count,
                    "processing_time": section_result.processing_time
                }
            }
        
        headers = {
            "x-clinic-id": str(clinic_id),
            "Content-Type": "application/json"
        }
        
        
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
        logger.info(f"Sending section result {section_id} ({section_result.status}) to NoteGen API backend, details={details}")
        
        # Use the existing retry logic
        return await self.send_generated_section(
            encounter_id=encounter_id,
            section_id=section_id,
            payload=payload,
            clinic_id=clinic_id,
            job_id=job_id,
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