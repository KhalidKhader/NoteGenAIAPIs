from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field 

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

class HealthCheckResponse(BaseModel):
    """Comprehensive health check response."""
    status: str = Field(..., description="overall/healthy/degraded/unhealthy")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    services: List[ServiceStatus] = Field(..., description="Individual service statuses")
    medical_compliance: MedicalComplianceStatus = Field(..., description="Medical compliance status")
    version: str = Field(default="1.0.0", description="API version")
    

    
    
