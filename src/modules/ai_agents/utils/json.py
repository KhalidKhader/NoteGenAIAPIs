"""
Shared JSON Utilities

Common JSON parsing and manipulation functions used across all AI agents.
"""

import json_repair
import json
from typing import Dict, Any, Optional, List, Union
from src.core.settings.logging import logger


def parse_json(text: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """
    Parse JSON content using json_repair for robust parsing.
    
    Args:
        text: The text content to parse as JSON
        
    Returns:
        Parsed JSON as dictionary or list, or None if parsing fails
    """
    try:
        repaired = json_repair.loads(text)
        if isinstance(repaired, (dict, list)):
            return repaired
        else:
            logger.warning(f"Parsed JSON is not a dict or list: {repaired}")
            return None
    except Exception as e:
        logger.error(f"Failed to parse JSON with json_repair: {e}")
        return None


def clean_json_response(content: str) -> str:
    """
    Clean up JSON response content by removing common formatting artifacts.
    
    Args:
        content: Raw response content from LLM
        
    Returns:
        Cleaned content string
    """
    return content.strip().strip("`").strip("json").strip()


def format_json_response(data: Union[List, Dict], indent: int = 2) -> str:
    """
    Format JSON data with proper indentation and error handling.
    
    Args:
        data: JSON data to format
        indent: Number of spaces for indentation
        
    Returns:
        Formatted JSON string
    """
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to format JSON: {e}")
        return str(data)


def extract_medical_terms_from_json(data: Union[Dict, List]) -> List[str]:
    """
    Extract medical terms from parsed JSON data, which is expected to be a list.
    
    Args:
        data: Parsed JSON data, expected to be a list of strings.
        
    Returns:
        List of medical terms as strings.
    """
    if not isinstance(data, list):
        logger.warning(f"Expected a list of medical terms, but got type {type(data)}. Data: {str(data)[:200]}")
        return []
    
    # Process the direct list of terms, ensuring they are strings and stripped of whitespace
    terms = [str(term).strip() for term in data if term and isinstance(term, (str, int, float))]
    
    # Remove duplicates while preserving order
    unique_terms = list(dict.fromkeys(terms))
    
    logger.debug(f"Extracted {len(unique_terms)} unique medical terms from JSON list.")
    return unique_terms 