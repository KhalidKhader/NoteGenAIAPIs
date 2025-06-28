"""
Services module for NoteGen AI APIs.

This module contains all business logic services for medical SOAP note generation,
RAG systems, and AI processing.
"""

from .conversation_rag import ConversationRAGService, get_conversation_rag_service
from .pattern_learning import PatternLearningService, get_pattern_learning_service
from .snomed_rag import SNOMEDRAGService, get_snomed_rag_service
from .section_generator import MedicalSectionGenerator, get_section_generator_service, get_soap_generator_service
from .patient_info_service import PatientInfoService, get_patient_info_service

__all__ = [
    "ConversationRAGService",
    "get_conversation_rag_service",
    "PatternLearningService",
    "get_pattern_learning_service",
    "SNOMEDRAGService",
    "get_snomed_rag_service",
    "MedicalSectionGenerator",
    "get_section_generator_service",
    "get_soap_generator_service",  # Backward compatibility
    "PatientInfoService",
    "get_patient_info_service",
]
