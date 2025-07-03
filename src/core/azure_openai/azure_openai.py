"""
Medical Section Generator Service for NoteGen AI APIs.

This service generates medical sections (SOAP notes and other templates) from conversations
using prompts provided by the NestJS backend. It integrates with RAG services for enhanced
medical accuracy and maintains line-number referencing for traceability.
"""
from typing import Dict, List, Optional, Any

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage

from src.core.settings.config import settings
from src.core.settings.logging import logger
from src.services.opensearch import get_conversation_rag_service
from src.services.neo4j import get_snomed_rag_service
from src.services.preferences import get_pattern_learning_service

class MedicalSectionGenerator:
    """
    Medical Section Generator for SOAP notes and other medical templates.
    """
    
    def __init__(self):
        self.llm: Optional[AzureChatOpenAI] = None
        self.conversation_rag = None
        self.snomed_rag = None
        self.pattern_learning = None
        self._initialized = False
        
        # Performance tracking
        self.generation_stats = {
            "total_generations": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "average_processing_time": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize the medical section generator service."""
        if self._initialized:
            return
            
        logger.info("Initializing Medical Section Generator")
        
        try:
            # Initialize Azure OpenAI with medical-optimized settings
            self.llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                deployment_name=settings.azure_openai_deployment_name,
                model=settings.azure_openai_model,
                temperature=0.1,  # Low temperature for medical accuracy
                max_tokens=4000,
                request_timeout=60,
                max_retries=3
            )
            
            # Initialize RAG services
            self.conversation_rag = await get_conversation_rag_service()
            self.snomed_rag = await get_snomed_rag_service()
            self.pattern_learning = await get_pattern_learning_service()
            
            # Verify all services
            await self._verify_services()
            
            self._initialized = True
            logger.info("Medical Section Generator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Medical Section Generator: {str(e)}")
            raise RuntimeError(f"Section generator initialization failed: {str(e)}")
    
    async def _verify_services(self) -> None:
        """Verify all medical services are operational."""
        try:
            # Test LLM connection
            test_response = await self.llm.agenerate(
                [[HumanMessage(content="Test medical system connectivity.")]]
            )
            if not test_response.generations[0][0].text:
                raise RuntimeError("LLM test failed")
            
            # Test RAG services
            await self.conversation_rag.health_check()
            await self.snomed_rag.health_check()
            await self.pattern_learning.health_check()
            
            logger.info("All medical services verified and operational")
            
        except Exception as e:
            logger.error(f"Service verification failed: {str(e)}")
            raise
    
    def _update_stats(self, duration: float, success: bool) -> None:
        """Update generation statistics."""
        if success:
            self.generation_stats["successful_generations"] += 1
        else:
            self.generation_stats["failed_generations"] += 1
        
        self.generation_stats["total_generations"] += 1
        
        # Update average processing time
        total_gens = self.generation_stats["total_generations"]
        current_avg = self.generation_stats["average_processing_time"]
        self.generation_stats["average_processing_time"] = (
            (current_avg * (total_gens - 1) + duration) / total_gens
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for medical system monitoring."""
        if not self._initialized:
            return {"status": "unhealthy", "error": "Service not initialized"}
        
        try:
            # Test LLM
            test_response = await self.llm.agenerate(
                [[HumanMessage(content="Test")]]
            )
            llm_healthy = bool(test_response.generations[0][0].text)
            
            # Test RAG services
            conv_health = await self.conversation_rag.health_check()
            snomed_health = await self.snomed_rag.health_check()
            pattern_health = await self.pattern_learning.health_check()
            
            return {
                "status": "healthy",
                "services": {
                    "llm": llm_healthy,
                    "conversation_rag": conv_health.get("status") == "healthy",
                    "snomed_rag": snomed_health.get("status") == "healthy",
                    "pattern_learning": pattern_health.get("status") == "healthy"
                },
                "statistics": self.generation_stats
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}