"""
Recording Consent Agent

This module provides functionality to detect patient consent for recording
in medical conversations using LLM-based classification.
"""

from .agent import find_consent_chunk_id

__all__ = ["find_consent_chunk_id"] 