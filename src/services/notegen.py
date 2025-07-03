from src.core.notegen.section_generation import NotegenAPIService, NotegenAPIService
from src.core.notegen.patient_info import PatientInfoService
from typing import Optional
from .opensearch import get_conversation_rag_service
from .azure_openai import get_soap_generator_service

# Global service instance
_notegen_api_service: Optional[NotegenAPIService] = None


async def get_notegen_api_service() -> NotegenAPIService:
    """Get the global NoteGen API service instance."""
    global _notegen_api_service
    if _notegen_api_service is None:
        _notegen_api_service = NotegenAPIService()
        await _notegen_api_service.initialize()
    return _notegen_api_service

# Global service instance
_patient_info_service: Optional[PatientInfoService] = None

async def get_patient_info_service() -> PatientInfoService:
    """Get the global patient info service instance."""
    global _patient_info_service
    if _patient_info_service is None:
        
        conversation_rag = await get_conversation_rag_service()
        section_generator = await get_soap_generator_service()
        notegen_api = await get_notegen_api_service()
        
        _patient_info_service = PatientInfoService(
            conversation_rag=conversation_rag,
            section_generator=section_generator,
            notegen_api=notegen_api
        )
    
    return _patient_info_service 