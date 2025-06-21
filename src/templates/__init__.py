"""
Templates module for NoteGen AI APIs.

This module contains all prompt templates and generation functions for medical
SOAP note creation and other medical documentation templates.
"""

from .prompts import (
    PromptLanguage,
    SOAPSectionType,
    generate_soap_section_prompt,
    generate_multi_template_prompt,
    FACTUAL_CONSISTENCY_VALIDATION_PROMPT,
    SNOMED_VALIDATION_PROMPT
)

__all__ = [
    "PromptLanguage",
    "SOAPSectionType", 
    "generate_soap_section_prompt",
    "generate_multi_template_prompt",
    "FACTUAL_CONSISTENCY_VALIDATION_PROMPT",
    "SNOMED_VALIDATION_PROMPT"
] 