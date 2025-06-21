"""
Medical Observability Service with Langfuse Integration

Provides comprehensive tracing and monitoring for medical SOAP generation:
- LLM call tracing with medical context
- RAG system performance monitoring
- SOAP generation workflow tracking
- Medical accuracy metrics
- Compliance audit trails
"""

import asyncio
from typing import Any, Dict, Optional

from langfuse import Langfuse

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

class MedicalObservabilityService:
    """
    Medical-grade observability service with Langfuse integration.
    
    Features:
    - Medical SOAP generation tracing with rich metadata
    - RAG system performance monitoring
    - LLM call tracking with token and estimated cost metrics
    - Trace scoring for quality, relevance, and hallucination metrics
    - Compliance audit trails and structured event logging
    """
    
    def __init__(self):
        self.langfuse: Optional[Langfuse] = None
        self._initialized = False
        self._enabled = bool(settings.langfuse_secret_key and settings.langfuse_public_key)
        
        self.active_traces: Dict[str, Any] = {}  # conversation_id -> trace object
        self.metrics = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "llm_token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "estimated_cost_usd": 0.0,
        }
    
    async def initialize(self) -> None:
        """Initialize Langfuse for medical observability."""
        if self._initialized or not self._enabled:
            return
            
        try:
            logger.info("🔍 Initializing Medical Observability with Langfuse")
            self.langfuse = Langfuse(
                secret_key=settings.langfuse_secret_key,
                public_key=settings.langfuse_public_key,
                host=settings.langfuse_host,
                debug=False,
                flush_at=10, # Batching
                flush_interval=5 # Seconds
            )
            await self._test_connection()
            self._initialized = True
            logger.info("✅ Medical Observability initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Medical Observability: {str(e)}")
            self._enabled = False
    
    async def _test_connection(self) -> None:
        """Test Langfuse connection."""
        try:
            self.langfuse.trace(name="medical_system_test_trace").span(name="test_span", input={"status": "ok"})
            self.langfuse.flush()
            logger.info("✅ Langfuse connection verified")
        except Exception as e:
            logger.error(f"Langfuse connection test failed: {str(e)}")
            raise
    
    def start_medical_encounter_trace(
        self, 
        conversation_id: str,
        doctor_id: str,
        language: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Start tracing a medical encounter and returns the trace object."""
        if not self._enabled or not self._initialized:
            return None
            
        try:
            trace_metadata = {
                "conversation_id": conversation_id,
                "doctor_id": doctor_id,
                "language": language,
                "app_version": settings.app_version,
                "app_name": settings.app_name,
                **(metadata or {})
            }
            
            trace = self.langfuse.trace(
                name=f"medical_encounter_processing",
                user_id=doctor_id,
                session_id=conversation_id,
                metadata=trace_metadata,
                tags=["medical", "multi-template-generation", language]
            )
            
            self.active_traces[conversation_id] = trace
            self.metrics["total_runs"] += 1
            logger.info(f"🔍 Started medical encounter trace: {trace.id}")
            return trace
            
        except Exception as e:
            logger.error(f"Failed to start medical encounter trace: {str(e)}")
            return None

    def score_trace(self, trace_id: str, name: str, value: float, comment: Optional[str] = None):
        """
        Adds a score to a trace. Used for evaluations like hallucination checks,
        relevance, or clinical accuracy.
        """
        if not self._enabled or not self._initialized:
            return
        
        try:
            score = self.langfuse.score(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment
            )
            logger.debug(f"Logged score '{name}' with value {value} to trace {trace_id}")
            return score
        except Exception as e:
            logger.error(f"Failed to score trace {trace_id}: {str(e)}")

    def log_llm_usage(self, prompt_tokens: int, completion_tokens: int):
        """Logs token usage and estimated cost."""
        total_tokens = prompt_tokens + completion_tokens
        self.metrics["llm_token_usage"]["prompt_tokens"] += prompt_tokens
        self.metrics["llm_token_usage"]["completion_tokens"] += completion_tokens
        self.metrics["llm_token_usage"]["total_tokens"] += total_tokens
        
        # Estimate cost
        cost = (
            (prompt_tokens / 1000) * settings.azure_input_price_per_1k_tokens +
            (completion_tokens / 1000) * settings.azure_output_price_per_1k_tokens
        )
        self.metrics["estimated_cost_usd"] += cost
        logger.debug(f"Logged usage: {total_tokens} tokens, estimated cost: ${cost:.6f}")

    def finish_medical_encounter_trace(
        self,
        conversation_id: str,
        success: bool,
        final_status: str
    ) -> None:
        """Finish tracing a medical encounter with final metrics."""
        if not self._enabled or not self._initialized:
            return
            
        trace = self.active_traces.get(conversation_id)
        if not trace:
            return
            
        try:
            if success:
                self.metrics["successful_runs"] += 1
            else:
                self.metrics["failed_runs"] += 1

            # Update trace with final summary metadata
            trace.update(
                metadata={
                    **trace.metadata,
                    "final_status": final_status,
                    "final_metrics": self.get_run_metrics()
                },
                output={"status": final_status}
            )
            
            del self.active_traces[conversation_id]
            self.langfuse.flush()
            logger.info(f"✅ Finished medical encounter trace: {trace.id} with status: {final_status}")
            
        except Exception as e:
            logger.error(f"Failed to finish medical encounter trace: {str(e)}")
    
    def get_run_metrics(self) -> Dict[str, Any]:
        """Get metrics for the current run."""
        return self.metrics

    async def health_check(self) -> Dict[str, Any]:
        """Check observability service health."""
        return {
            "service": "medical_observability",
            "status": "healthy" if self._initialized else "disabled",
            "langfuse_enabled": self._enabled,
            "langfuse_initialized": self._initialized,
            "active_traces": len(self.active_traces)
        }
    
    async def close(self) -> None:
        """Close observability service and flush remaining data."""
        if self.langfuse:
            try:
                self.langfuse.shutdown()
                logger.info("🔍 Medical Observability service closed")
            except Exception as e:
                logger.error(f"Error shutting down observability service: {str(e)}")

# Global observability service instance
_observability_service: Optional[MedicalObservabilityService] = None

async def get_observability_service() -> MedicalObservabilityService:
    """Get the global observability service instance."""
    global _observability_service
    
    if _observability_service is None:
        _observability_service = MedicalObservabilityService()
        await _observability_service.initialize()
    
    return _observability_service