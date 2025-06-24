"""
Pattern Learning Service for NoteGen AI APIs.

This service learns doctor preferences from SOAP note modifications
and applies them to future generations.
"""

import json
from typing import Dict, Optional, Any
from pathlib import Path

from src.core.logging import get_logger

logger = get_logger(__name__)

class PatternLearningService:
    """
    Service for learning and applying doctor-specific preferences.
    
    Learns from doctor modifications to generated SOAP notes and
    applies these patterns to future generations.
    """
    
    def __init__(self):
        self.patterns_file = Path("doctor_patterns.json")
        self.doctor_patterns: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the pattern learning service."""
        try:
            logger.info("Initializing Pattern Learning Service...")
            
            # Load existing patterns from file
            self.doctor_patterns = self._load_patterns_from_file()
            
            self._initialized = True
            logger.info("Pattern Learning Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pattern Learning Service: {str(e)}")
            raise RuntimeError(f"Pattern Learning initialization failed: {str(e)}")
    
    def _load_patterns_from_file(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns from JSON file."""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    patterns = json.load(f)
                logger.info(f"Loaded {len(patterns)} doctor patterns from file")
                return patterns
            except Exception as e:
                logger.error(f"Failed to load patterns from file: {str(e)}")
        
        return {}
    
    async def get_doctor_preferences(
        self, 
        doctor_id: str
    ) -> Dict[str, str]:
        """Get doctor terminology preferences as simple dict mapping."""
        if not self._initialized or doctor_id not in self.doctor_patterns:
            return {}
        
        preferences = {}
        terminology_prefs = self.doctor_patterns[doctor_id].get("terminology_preferences", {})
        
        for pattern_key, pattern_data in terminology_prefs.items():
            original_term = pattern_data.get("original_term", "")
            preferred_term = pattern_data.get("preferred_term", "")
            confidence = pattern_data.get("confidence", 0.0)
            
            # Only include high-confidence preferences
            if confidence >= 0.7 and original_term and preferred_term:
                preferences[original_term] = preferred_term
        
        return preferences
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for medical system monitoring."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Test file system access
            file_system_ok = True
            try:
                test_file = Path("test_patterns.json")
                test_file.write_text("{}")
                test_file.unlink()
            except Exception:
                file_system_ok = False
            
            return {
                "service": "pattern_learning",
                "status": "healthy" if self._initialized and file_system_ok else "unhealthy",
                "initialized": self._initialized,
                "file_system_ok": file_system_ok,
                "total_doctors": len(self.doctor_patterns),
                "total_patterns": sum(
                    len(patterns.get("terminology_preferences", {}))
                    for patterns in self.doctor_patterns.values()
                )
            }
            
        except Exception as e:
            logger.error(f"Pattern Learning health check failed: {str(e)}")
            return {
                "service": "pattern_learning",
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def close(self) -> None:
        """Close the service and cleanup resources."""
        logger.info("Pattern Learning Service closed")


# Service Factory and Singleton Management
_pattern_learning_service: Optional[PatternLearningService] = None


async def get_pattern_learning_service() -> PatternLearningService:
    """Get or create pattern learning service instance."""
    global _pattern_learning_service
    
    if _pattern_learning_service is None:
        _pattern_learning_service = PatternLearningService()
        await _pattern_learning_service.initialize()
    
    return _pattern_learning_service
