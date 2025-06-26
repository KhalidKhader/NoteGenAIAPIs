"""
Medical API Models for NoteGen AI APIs - Production Ready.

Core models for the production medical SOAP note generation system.
Supports dynamic section generation, SNOMED validation, and comprehensive logging.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, ValidationInfo


# =============================================================================
# Core Production Models (Actually Used)
# =============================================================================

class RequestedSection(BaseModel):
    """
    Represents a section that needs to be generated, based on a template.
    This model is flexible to support multiple templates like SOAP, Visit Summaries, etc.
    """
    id: Union[int, str] = Field(..., description="Unique ID for the section definition.", example=1)
    templateId: Union[int, str] = Field(..., description="ID of the template this section belongs to.", example=1)
    name: str = Field(..., description="Name of the section, e.g., 'Subjective' or 'Visit Summary'.", example="Subjective")
    prompt: str = Field(..., description="The prompt to use for generating this section's content.")
    order: int = Field(..., description="The order of this section within its template.", example=1)


class SectionGenerationStatus(BaseModel):
    """Status tracking for section generation with retry logic."""
    status: str = Field(..., description="Generation status: 'success', 'failed', 'processing'")
    attempt_count: int = Field(default=0, description="Number of attempts made")
    max_attempts: int = Field(default=3, description="Maximum number of attempts allowed")
    error_message: Optional[str] = Field(None, description="Error message if generation failed")
    error_trace: Optional[str] = Field(None, description="Full error trace for debugging")
    last_attempt_time: Optional[datetime] = Field(None, description="Timestamp of last attempt")


class EncounterRequestModel(BaseModel):
    """
    Production request model for a complete encounter processing task.
    
    This model supports the entire workflow, including dynamic multi-template
    section generation, speaker-aware transcription, and doctor-specific preferences.
    """
    encounterId: str = Field(
        ..., 
        min_length=1,
        description="Unique encounter ID to isolate and track the conversation.", 
        example="encounter_12345"
    )
    encounterTranscript: List[Dict[str, str]] = Field(
        ..., 
        min_items=1,
        description="Speaker-aware transcription array. Each dict should contain one key-value pair "
                    "representing the speaker and their dialogue, e.g., `{'doctor': 'text'}` or "
                    "`{'patient': 'text'}`.",
        example=[
            {"doctor": "How are you feeling today?"},
            {"patient": "I've been having chest pain."}
        ]
    )
    systemPrompt: str = Field(
        ...,
        min_length=1,
        description="Base system prompt guiding the AI's persona and general instructions."
    )
    sections: List[RequestedSection] = Field(
        ...,
        min_items=1,
        description="A list of all sections to be generated across all requested templates."
    )
    doctorId: str = Field(
        ...,
        min_length=1,
        description="Identifier for the doctor to apply learned preferences."
    )
    doctor_preferences: Dict[str, str] = Field(
        default_factory=dict,
        description="Doctor-specific terminology preferences.",
        example={"Hypertension": "HTN"}
    )
    language: str = Field(
        default="en",
        pattern="^(en|fr)$",
        description="Language code for the encounter (en/fr)."
    )
    clinicId: str = Field(
        ...,
        min_length=1,
        description="Clinic ID required for NestJS integration."
    )
    patientInfo: bool = Field(
        default=False,
        description="Flag to extract and send patient demographic information."
    )

    @field_validator('encounterId', 'doctorId', 'clinicId')
    @classmethod
    def validate_not_empty(cls, v: str, info: ValidationInfo):
        if not v or not v.strip():
            raise ValueError(f'{info.field_name} cannot be empty')
        return v.strip()


class GeneratedSection(BaseModel):
    """
    Represents a single generated section of a medical note, complete with
    traceability and validation metadata. This is the primary output unit.
    """
    section_id: str = Field(..., description="Unique identifier for the generated section instance.")
    template_id: Union[str, int] = Field(..., description="Identifier of the template this section belongs to.")
    section_name: str = Field(..., description="Name of the section, e.g., 'Subjective'.")
    content: str = Field(..., description="The generated textual content for the section.")
    line_references: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="List of exact line numbers and substrings from the transcript used for generation."
    )
    snomed_mappings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of SNOMED-validated medical terms found in the content."
    )
    confidence_score: float = Field(
        ..., 
        description="Confidence score (0.0 to 1.0) indicating hallucination risk."
    )
    language: str = Field(..., description="Language of the generated content.")
    processing_metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Metadata from the generation process, like tokens used or model version."
    )
    generation_status: SectionGenerationStatus = Field(
        ..., 
        description="Status and error tracking for section generation."
    )


class SectionGenerationResult(BaseModel):
    """
    Result of section generation including success/failure status.
    Used internally for processing and API responses.
    """
    sectionId: Union[str, int] = Field(..., description="Section ID from the request")
    section_name: str = Field(..., description="Name of the section")
    status: str = Field(..., description="'SUCCESS' or 'FAILED'")
    content: Optional[str] = Field(None, description="Generated content if successful, empty if failed")
    errorMessage: Optional[str] = Field(None, description="Error message if failed, empty if successful")
    error_trace: Optional[str] = Field(None, description="Full error trace if failed")
    attempt_count: int = Field(default=0, description="Number of attempts made")
    processing_time: Optional[float] = Field(None, description="Time taken for generation in seconds")
    
    # Success-specific fields
    line_references: List[Dict[str, Any]] = Field(default_factory=list)
    snomed_mappings: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: Optional[float] = Field(None)
    language: Optional[str] = Field(None)
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)


class JobAcknowledgementResponse(BaseModel):
    """Response to acknowledge that a job has been started."""
    job_id: str = Field(..., description="Job ID for tracking")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    encounter_id: str = Field(..., description="Encounter ID being processed")


# =============================================================================
# Health Check Models
# =============================================================================

class ServiceStatus(BaseModel):
    """Model for reporting the status of a single service."""
    service_name: str = Field(..., description="Service name")
    status: str = Field(..., description="healthy/unhealthy/degraded")
    details: Optional[str] = Field(None, description="Additional details")


class MedicalComplianceStatus(BaseModel):
    """Medical compliance features status."""
    conversation_isolation: bool = Field(..., description="ID-based isolation working")
    snomed_validation: bool = Field(..., description="Neo4j SNOMED integration working")
    line_referencing: bool = Field(..., description="Line tracking working")
    doctor_preferences: bool = Field(..., description="Preferences system working")


class HealthCheckResponse(BaseModel):
    """Comprehensive health check response."""
    status: str = Field(..., description="overall/healthy/degraded/unhealthy")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    services: List[ServiceStatus] = Field(..., description="Individual service statuses")
    medical_compliance: MedicalComplianceStatus = Field(..., description="Medical compliance status")
    version: str = Field(default="1.0.0", description="API version")

class LineReference(BaseModel):
    """Line reference for medical traceability and hallucination prevention."""
    line_number: int = Field(..., description="Line number in original transcript")
    start_char: int = Field(..., description="Start character position in line")
    end_char: int = Field(..., description="End character position in line")
    text: str = Field(..., description="Referenced text from transcript")
    speaker: Optional[str] = Field(None, description="Speaker (Doctor/Patient)")
    confidence: float = Field(default=1.0, description="Reference accuracy confidence") 