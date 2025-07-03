from typing import Dict, List, Union
from pydantic import BaseModel, Field, field_validator, ValidationInfo

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


class JobAcknowledgementResponse(BaseModel):
    """Response to acknowledge that a job has been started."""
    job_id: str = Field(..., description="Job ID for tracking")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    encounter_id: str = Field(..., description="Encounter ID being processed")
    

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
    collection_name: str = Field(
        ...,
        min_length=1,
        max_length=28,
        description="Name of the OpenSearch collection to use for storing data. Must be provided to identify the clinic's collection."
    )

    @field_validator('encounterId', 'doctorId', 'clinicId', 'collection_name')
    @classmethod
    def validate_not_empty(cls, v: str, info: ValidationInfo):
        if not v or not v.strip():
            raise ValueError(f'{info.field_name} cannot be empty')
        return v.strip()
