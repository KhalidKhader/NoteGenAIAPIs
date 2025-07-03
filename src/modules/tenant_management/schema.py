from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, ValidationInfo

class TenantCollectionRequest(BaseModel):
    """Request model for tenant collection creation."""
    collection_name: str = Field(
        ...,
        min_length=3,
        max_length=28,
        description="Name of the collection to create. Must start with a lowercase letter and contain only lowercase letters, numbers, and hyphens."
    )
    clinic_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the clinic"
    )

    @field_validator('collection_name')
    @classmethod
    def validate_collection_name(cls, v: str) -> str:
        """Validate collection name according to AWS OpenSearch requirements."""
        # Convert to lowercase
        v = v.lower()
        
        # Must start with a letter
        if not v[0].isalpha():
            raise ValueError("Collection name must start with a lowercase letter")
            
        # Must contain only lowercase letters, numbers, and hyphens
        if not all(c.islower() or c.isdigit() or c == '-' for c in v):
            raise ValueError("Collection name must contain only lowercase letters, numbers, and hyphens")
            
        # Must not end with a hyphen
        if v.endswith('-'):
            raise ValueError("Collection name must not end with a hyphen")
            
        return v 