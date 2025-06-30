"""
Services module for NoteGen AI APIs.

This module contains all business logic services for medical SOAP note generation,
RAG systems, and AI processing.
"""

from .opensearch.opensearch_rag import ConversationRAGService, get_conversation_rag_service
from .preferences.pattern_learning import PatternLearningService, get_pattern_learning_service
from .neo4j.service import get_snomed_rag_service, SNOMEDRAGService
from .openai.azure_openai import MedicalSectionGenerator, get_section_generator_service, get_soap_generator_service
from .notegen.patient_info import PatientInfoService, get_patient_info_service

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
