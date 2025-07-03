"""
Section Generation Agent Tools

Utility functions for the section generation agent.
"""

import re
from typing import Dict, Any, Optional
from src.core.settings.logging import logger
from src.modules.ai_agents.utils.json import parse_json, clean_json_response, format_json_response


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON content from text that might contain explanatory content.
    
    Args:
        text: Text that might contain JSON
        
    Returns:
        Extracted JSON string or None if not found
    """
    # Try to find JSON object pattern (most common for section generation)
    json_object_pattern = r'\{.*?\}'
    matches = re.findall(json_object_pattern, text, re.DOTALL)
    
    if matches:
        # Return the first (and usually only) JSON object found
        return matches[0]
    
    # Try to find JSON array pattern as fallback
    json_array_pattern = r'\[.*?\]'
    matches = re.findall(json_array_pattern, text, re.DOTALL)
    
    if matches:
        return matches[0]
    
    return None


def validate_section_generation_data(data: Any) -> bool:
    """
    Validate that the parsed JSON has the expected structure for section generation.
    
    Args:
        data: Parsed JSON data
        
    Returns:
        True if structure is valid, False otherwise
    """
    if not isinstance(data, dict):
        return False
    
    # Check for required fields for section generation
    required_fields = ["noteContent"]
    for field in required_fields:
        if field not in data:
            return False
    
    # Validate noteContent is string
    note_content = data.get("noteContent")
    if not isinstance(note_content, str):
        return False
    
    return True


def parse_section_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON content specifically for section generation with validation.
    
    Args:
        text: The text content to parse as JSON
        
    Returns:
        Parsed JSON as dictionary, or None if parsing fails
    """
    try:
        # First, try to extract JSON from the text if it contains explanatory content
        json_content = extract_json_from_text(text)
        if json_content:
            text = json_content
            logger.debug(f"Extracted JSON content: {json_content[:100]}...")
        
        # Use the shared parse_json function
        repaired = parse_json(text)
        
        if not repaired:
            return None
            
        # Validate structure for section generation
        if not validate_section_generation_data(repaired):
            logger.warning(f"JSON structure validation failed for section generation data: {repaired}")
            return None
            
        if isinstance(repaired, dict):
            return repaired
        elif isinstance(repaired, list) and repaired:
            # If it's a list, take the last item (most recent response)
            last_item = repaired[-1]
            if isinstance(last_item, dict) and validate_section_generation_data(last_item):
                return last_item
            else:
                logger.warning(f"Last item in list is not valid section generation data: {last_item}")
            return None
        else:
            logger.warning(f"Parsed JSON is not dict or valid list: {repaired}")
            return None
    except Exception as e:
        logger.error(f"Failed to parse section JSON: {e}")
        return None


def create_section_generation_template(note_content: str, line_references: list = None) -> Dict[str, Any]:
    """
    Create a properly formatted section generation response template.
    
    Args:
        note_content: The generated note content
        line_references: List of line references
        
    Returns:
        Formatted section generation response dictionary
    """
    response = {
        "noteContent": note_content,
        "lineReferences": line_references or []
    }
    
    return response
