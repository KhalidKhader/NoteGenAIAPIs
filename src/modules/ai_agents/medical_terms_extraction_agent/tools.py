"""
Medical Terms Extraction Agent Tools

Utility functions for the medical terms extraction agent.
"""

from src.modules.ai_agents.utils.json import parse_json, clean_json_response, extract_medical_terms_from_json

# Re-export the functions for backward compatibility
__all__ = ["parse_json", "clean_json_response", "extract_medical_terms_from_json"]