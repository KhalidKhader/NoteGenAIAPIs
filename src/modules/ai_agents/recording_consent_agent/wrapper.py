from src.services.azure_openai import get_section_generator_service
from src.core.azure_openai.azure_openai import MedicalSectionGenerator

async def _get_medical_generator() -> MedicalSectionGenerator:
    """Get or create the medical generator instance."""
    return await get_section_generator_service()

__all__ = ["_get_medical_generator"]