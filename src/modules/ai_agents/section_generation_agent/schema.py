from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class SectionGenerationStatus(BaseModel):
    """Status tracking for section generation with retry logic."""
    status: str = Field(..., description="Generation status: 'success', 'failed', 'processing'")
    attempt_count: int = Field(default=0, description="Number of attempts made")
    max_attempts: int = Field(default=3, description="Maximum number of attempts allowed")
    error_message: Optional[str] = Field(None, description="Error message if generation failed")
    error_trace: Optional[str] = Field(None, description="Full error trace for debugging")
    last_attempt_time: Optional[datetime] = Field(None, description="Timestamp of last attempt")

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
    language: Optional[str] = Field(None)
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)
    doctor_preferences: bool = Field(..., description="Whether doctor preferences were applied during generation")


class LineReference(BaseModel):
    """Line reference for medical traceability and hallucination prevention."""
    line_number: int = Field(..., description="Line number in original transcript")
    start_char: int = Field(..., description="Start character position in line")
    end_char: int = Field(..., description="End character position in line")
    text: str = Field(..., description="Referenced text from transcript")
    speaker: Optional[str] = Field(None, description="Speaker (Doctor/Patient)")
    confidence: float = Field(default=1.0, description="Reference accuracy confidence")

