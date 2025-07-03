from src.core.preferences.pattern_learning import PatternLearningService
from typing import Optional

# Service Factory and Singleton Management
_pattern_learning_service: Optional[PatternLearningService] = None


async def get_pattern_learning_service() -> PatternLearningService:
    """Get or create pattern learning service instance."""
    global _pattern_learning_service
    
    if _pattern_learning_service is None:
        _pattern_learning_service = PatternLearningService()
        await _pattern_learning_service.initialize()
    
    return _pattern_learning_service