from src.core.azure_openai.azure_openai import MedicalSectionGenerator
from typing import Optional 

_section_generator_instance: Optional[MedicalSectionGenerator] = None

async def get_section_generator_service() -> MedicalSectionGenerator:
    """Get singleton instance of medical section generator service."""
    global _section_generator_instance
    
    if _section_generator_instance is None:
        _section_generator_instance = MedicalSectionGenerator()
        await _section_generator_instance.initialize()
    
    return _section_generator_instance

# Backward compatibility alias
async def get_soap_generator_service() -> MedicalSectionGenerator:
    """Backward compatibility alias for get_section_generator_service."""
    return await get_section_generator_service()