"""
Recording Consent Agent Tools

Utility functions for the recording consent agent.
"""

from src.modules.ai_agents.utils.json import parse_json, clean_json_response, format_json_response

# Re-export the functions for backward compatibility
__all__ = ["parse_json", "clean_json_response", "format_json_response"]
