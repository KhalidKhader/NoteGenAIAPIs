"""
SNOMED RAG Service for Medical Term Validation using Neo4j GraphRAG.

Features:
- Neo4j GraphRAG integration with SNOMED Canadian edition
- Real-time medical term validation and mapping
- Multilingual support (language provided by NestJS API)
- Hierarchical concept relationships
- No hardcoded patterns or mock data
"""

import asyncio
from typing import Dict, List, Optional, Any

from neo4j import AsyncGraphDatabase, AsyncDriver

from src.core.config import settings
from src.core.logging import get_logger, MedicalProcessingLogger
from src.templates.queries import (
    SNOMED_TERM_SEARCH_FRENCH,
    SNOMED_TERM_SEARCH_ENGLISH,
    SNOMED_TERM_SEARCH_GENERIC,
    SNOMED_CONNECTION_TEST_QUERY,
    SNOMED_EXACT_MATCH_QUERY,
    SNOMED_SEMANTIC_SEARCH_QUERY
)

logger = get_logger(__name__)


class SNOMEDRAGService:
    """
    SNOMED RAG Service for medical term validation using Neo4j GraphRAG.
    
    Features:
    - Real Neo4j GraphRAG with SNOMED Canadian edition
    - Medical term validation and mapping
    - Language-agnostic (language provided by API)
    - Hierarchical concept relationships
    - No hardcoded patterns or mock data
    """

    def __init__(self):
        self.driver: Optional[AsyncDriver] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the SNOMED RAG service with Neo4j GraphRAG."""
        if self._initialized:
            return
            
        logger.info("Initializing SNOMED RAG Service with Neo4j GraphRAG")
        
        try:
            # Initialize Neo4j driver
            self.driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                max_connection_lifetime=settings.neo4j_max_connection_lifetime,
                max_connection_pool_size=settings.neo4j_max_connections,
                connection_acquisition_timeout=settings.neo4j_connection_timeout
            )
            
            # Test connection
            await self._test_connection()
            logger.info("Neo4j GraphRAG connection established")
            
            self._initialized = True
            logger.info("SNOMED RAG Service initialized successfully")
            
        except Exception as e:
            logger.error(f"SNOMED RAG initialization failed: {str(e)}")
            raise RuntimeError(f"SNOMED RAG initialization failed: {str(e)}")

    async def _test_connection(self) -> None:
        """Test Neo4j GraphRAG connection."""
        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(SNOMED_CONNECTION_TEST_QUERY)
            record = await result.single()
            if not record or record["test"] != 1:
                raise ConnectionError("Neo4j GraphRAG connection test failed")

    async def get_snomed_mappings_for_terms(
        self, 
        medical_terms: List[str], 
        language: str = "en",
        medical_logger: Optional[MedicalProcessingLogger] = None
    ) -> List[Dict[str, Any]]:
        """
        Get SNOMED mappings for medical terms using Neo4j GraphRAG.
        
        Args:
            medical_terms: List of medical terms to map
            language: Language code provided by NestJS API ("en" or "fr")
            medical_logger: Optional medical processing logger
        
        Returns:
            List of SNOMED mappings with concept IDs and preferred terms
        """
        if not self._initialized or not self.driver:
            logger.error("SNOMED RAG service not initialized")
            raise RuntimeError("SNOMED RAG service not initialized")
        
        if not medical_terms:
            return []
        
        logger.info(f"Getting SNOMED mappings for {len(medical_terms)} terms in language: {language}")
        
        if medical_logger:
            medical_logger.log_step(
                "NEO4J_SNOMED_MAPPING_START",
                f"Starting SNOMED mapping for {len(medical_terms)} medical terms",
                {
                    "medical_terms": medical_terms,
                    "language": language,
                    "database": "NEO4J_SNOMED_CANADIAN_EDITION",
                    "query_strategy": "EXACT_MATCH_THEN_CONTAINS_THEN_SEMANTIC"
                }
            )
        
        try:
            mappings = []
            
            async with self.driver.session(database=settings.neo4j_database) as session:
                for i, term in enumerate(medical_terms):
                    if medical_logger:
                        medical_logger.log_step(
                            "NEO4J_TERM_QUERY_START",
                            f"Querying Neo4j for term '{term}' ({i+1}/{len(medical_terms)})",
                            {
                                "term": term,
                                "term_index": i + 1,
                                "total_terms": len(medical_terms),
                                "language": language
                            }
                        )
                    
                    term_mappings = await self._search_snomed_term(session, term, language, medical_logger)
                    mappings.extend(term_mappings)
                    
                    if medical_logger:
                        for mapping in term_mappings:
                            medical_logger.log_neo4j_mapping(term, mapping)
            
            if medical_logger:
                medical_logger.log_step(
                    "NEO4J_SNOMED_MAPPING_COMPLETED",
                    f"SNOMED mapping completed: {len(mappings)} mappings found",
                    {
                        "total_mappings_found": len(mappings),
                        "terms_processed": len(medical_terms),
                        "success_rate": len(mappings) / len(medical_terms) if medical_terms else 0,
                        "database": "NEO4J_SNOMED_CANADIAN_EDITION"
                    }
                )
            
            logger.info(f"Found {len(mappings)} SNOMED mappings")
            return mappings
            
        except Exception as e:
            logger.error(f"Failed to get SNOMED mappings: {str(e)}")
            if medical_logger:
                medical_logger.log_step(
                    "NEO4J_SNOMED_MAPPING_FAILED",
                    f"SNOMED mapping failed: {str(e)}",
                    {"error": str(e), "terms": medical_terms}
                )
            raise RuntimeError(f"SNOMED mapping failed: {str(e)}")

    async def _search_snomed_term(
        self, 
        session, 
        term: str, 
        language: str,
        medical_logger: Optional[MedicalProcessingLogger] = None
    ) -> List[Dict[str, Any]]:
        """Search for a single term in SNOMED using appropriate language query."""
        
        # Select query based on language
        query = self._get_query_for_language(language)
        
        try:
            # Try exact match first
            if medical_logger:
                medical_logger.log_step(
                    "NEO4J_EXACT_MATCH_QUERY",
                    f"Trying exact match for term '{term}' in Neo4j SNOMED",
                    {"term": term, "query_type": "EXACT_MATCH"}
                )
            
            exact_result = await session.run(SNOMED_EXACT_MATCH_QUERY, term=term.lower())
            exact_records = await exact_result.data()
            
            if exact_records:
                if medical_logger:
                    medical_logger.log_step(
                        "NEO4J_EXACT_MATCH_SUCCESS",
                        f"Found {len(exact_records)} exact matches for '{term}'",
                        {"term": term, "matches_found": len(exact_records), "match_type": "EXACT"}
                    )
                return self._format_snomed_records(exact_records, term, "exact")
            
            # If no exact match, try contains search
            if medical_logger:
                medical_logger.log_step(
                    "NEO4J_CONTAINS_SEARCH_QUERY",
                    f"No exact match found, trying contains search for '{term}'",
                    {"term": term, "query_type": "CONTAINS", "language": language}
                )
            
            result = await session.run(query, term=term.lower())
            records = await result.data()
            
            if records:
                if medical_logger:
                    medical_logger.log_step(
                        "NEO4J_CONTAINS_SEARCH_SUCCESS",
                        f"Found {len(records)} contains matches for '{term}'",
                        {"term": term, "matches_found": len(records), "match_type": "CONTAINS"}
                    )
                return self._format_snomed_records(records, term, "contains")
            
            # If still no results, try semantic search
            if medical_logger:
                medical_logger.log_step(
                    "NEO4J_SEMANTIC_SEARCH_QUERY",
                    f"No contains match found, trying semantic search for '{term}'",
                    {"term": term, "query_type": "SEMANTIC"}
                )
            
            semantic_result = await session.run(SNOMED_SEMANTIC_SEARCH_QUERY, term=term.lower())
            semantic_records = await semantic_result.data()
            
            if semantic_records:
                if medical_logger:
                    medical_logger.log_step(
                        "NEO4J_SEMANTIC_SEARCH_SUCCESS",
                        f"Found {len(semantic_records)} semantic matches for '{term}'",
                        {"term": term, "matches_found": len(semantic_records), "match_type": "SEMANTIC"}
                    )
            else:
                if medical_logger:
                    medical_logger.log_step(
                        "NEO4J_NO_MATCHES_FOUND",
                        f"No SNOMED matches found for term '{term}' in any search type",
                        {"term": term, "searches_attempted": ["EXACT", "CONTAINS", "SEMANTIC"]}
                    )
            
            return self._format_snomed_records(semantic_records, term, "semantic")
            
        except Exception as e:
            logger.warning(f"Failed to search SNOMED for term '{term}': {str(e)}")
            if medical_logger:
                medical_logger.log_step(
                    "NEO4J_SEARCH_ERROR",
                    f"Neo4j search failed for term '{term}': {str(e)}",
                    {"term": term, "error": str(e)}
                )
            return []

    def _get_query_for_language(self, language: str) -> str:
        """Get appropriate SNOMED query based on language."""
        if language == "fr":
            return SNOMED_TERM_SEARCH_FRENCH
        elif language == "en":
            return SNOMED_TERM_SEARCH_ENGLISH
        else:
            return SNOMED_TERM_SEARCH_GENERIC

    def _format_snomed_records(
        self, 
        records: List[Dict], 
        original_term: str,
        match_type: str = "unknown"
    ) -> List[Dict[str, Any]]:
        """Format SNOMED database records into standardized mapping format."""
        mappings = []
        
        # Set confidence based on match type
        confidence_map = {
            "exact": 0.95,
            "contains": 0.80,
            "semantic": 0.65,
            "unknown": 0.50
        }
        
        for record in records:
            mappings.append({
                "concept_id": record.get("conceptId", ""),
                "preferred_term": record.get("preferredTerm", ""),
                "description": record.get("description", ""),
                "original_term": original_term,
                "confidence": confidence_map.get(match_type, 0.8),
                "match_type": match_type,
                "language": record.get("languageCode", "en")
            })
        
        return mappings

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the SNOMED RAG service."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Test Neo4j connection
            if self.driver:
                await self._test_connection()
                return {
                    "status": "healthy",
                    "neo4j_connected": True,
                    "initialized": self._initialized
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Neo4j driver not available",
                    "neo4j_connected": False,
                    "initialized": self._initialized
                }
                
        except Exception as e:
            logger.error(f"SNOMED RAG health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "neo4j_connected": False,
                "initialized": False
            }

    async def close(self) -> None:
        """Close Neo4j driver and cleanup resources."""
        try:
            if self.driver:
                await self.driver.close()
                self.driver = None
            self._initialized = False
            logger.info("SNOMED RAG Service closed")
        except Exception as e:
            logger.error(f"Error closing SNOMED RAG service: {str(e)}")


# =============================================================================
# Service Instance Management
# =============================================================================

_snomed_rag_service: Optional[SNOMEDRAGService] = None
_current_loop = None


async def get_snomed_rag_service() -> SNOMEDRAGService:
    """Get or create the global SNOMED RAG service instance."""
    global _snomed_rag_service, _current_loop
    
    # Get current event loop
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None
    
    # Reset service if event loop changed (for tests)
    if _current_loop != current_loop:
        if _snomed_rag_service:
            try:
                await _snomed_rag_service.close()
            except:
                pass  # Ignore errors during cleanup
        _snomed_rag_service = None
        _current_loop = current_loop
    
    if _snomed_rag_service is None:
        _snomed_rag_service = SNOMEDRAGService()
        await _snomed_rag_service.initialize()
    
    return _snomed_rag_service
