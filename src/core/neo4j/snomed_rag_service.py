"""
SNOMED RAG Service for Medical Term Validation using Neo4j GraphRAG.

Features:
- Neo4j GraphRAG integration with SNOMED Canadian edition
- Real-time medical term validation and mapping
- Multilingual support (language provided by NestJS API)
- Hierarchical concept relationships
- No hardcoded patterns or mock data
"""

from typing import Dict, List, Optional, Any
from neo4j import AsyncGraphDatabase, AsyncDriver
from src.core.settings.config import settings
from src.core.settings.logging import logger
from src.core.neo4j.queries import (
    SNOMEDQueryParams,
    get_term_search_query,
    get_connection_test_query,
    get_exact_match_query,
    get_semantic_search_query,
    ConfidenceScores,
    MatchType,
    Language
)

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
            query = get_connection_test_query()
            result = await session.run(query["query"], query["params"])
            record = await result.single()
            if not record or record["test"] != 1:
                raise ConnectionError("Neo4j GraphRAG connection test failed")

    async def _search_snomed_term(
        self, 
        session, 
        term: str, 
        language: str,
    ) -> List[Dict[str, Any]]:
        """Search for a single term in SNOMED using appropriate language query."""
        
        try:
            # Try exact match first
            query_params = SNOMEDQueryParams(term=term, language=language)
            
            details = {"term": term, "query_type": MatchType.EXACT.value}
            logger.info(f"NEO4J_EXACT_MATCH_QUERY Trying exact match for term '{term}' in Neo4j SNOMED, details={details}")
            
            exact_query = get_exact_match_query(query_params)
            exact_result = await session.run(exact_query["query"], exact_query["params"])
            exact_records = await exact_result.data()
            
            if exact_records:
                details = {"term": term, "matches_found": len(exact_records), "match_type": MatchType.EXACT.value}
                logger.info(f"NEO4J_EXACT_MATCH_SUCCESS Found {len(exact_records)} exact matches for '{term}', details={details}")
                return self._format_snomed_records(exact_records, term, MatchType.EXACT.value)
            
            # If no exact match, try contains search
            details = {"term": term, "query_type": MatchType.CONTAINS.value, "language": language}
            logger.info(f"NEO4J_CONTAINS_SEARCH_QUERY No exact match found, trying contains search for '{term}', details={details}")
            
            contains_query = get_term_search_query(query_params)
            result = await session.run(contains_query["query"], contains_query["params"])
            records = await result.data()
            
            if records:
                details = {"term": term, "matches_found": len(records), "match_type": MatchType.CONTAINS.value}
                logger.info(f"NEO4J_CONTAINS_SEARCH_SUCCESS Found {len(records)} contains matches for '{term}', details={details}")
                return self._format_snomed_records(records, term, MatchType.CONTAINS.value)
            
            # If still no results, try semantic search
            details = {"term": term, "query_type": MatchType.SEMANTIC.value}
            logger.info(f"NEO4J_SEMANTIC_SEARCH_QUERY No contains match found, trying semantic search for '{term}', details={details}")
            
            semantic_query = get_semantic_search_query(query_params)
            semantic_result = await session.run(semantic_query["query"], semantic_query["params"])
            semantic_records = await semantic_result.data()
            
            if semantic_records:
                details = {"term": term, "matches_found": len(semantic_records), "match_type": MatchType.SEMANTIC.value}
                logger.info(f"NEO4J_SEMANTIC_SEARCH_SUCCESS Found {len(semantic_records)} semantic matches for '{term}', details={details}")
            else:
                details = {"term": term, "searches_attempted": [t.value for t in [MatchType.EXACT, MatchType.CONTAINS, MatchType.SEMANTIC]]}
                logger.warning(f"NEO4J_NO_MATCHES_FOUND No SNOMED matches found for term '{term}' in any search type, details={details}")
            
            return self._format_snomed_records(semantic_records, term, MatchType.SEMANTIC.value)
            
        except Exception as e:
            logger.warning(f"Failed to search SNOMED for term '{term}': {str(e)}")
            details = {"term": term, "error": str(e)}
            logger.error(f"NEO4J_SEARCH_ERROR Neo4j search failed for term '{term}': {str(e)}, details={details}")
            return []

    def _format_snomed_records(
        self, 
        records: List[Dict], 
        original_term: str,
        match_type: str = MatchType.UNKNOWN.value
    ) -> List[Dict[str, Any]]:
        """Format SNOMED database records into standardized mapping format."""
        mappings = []
        
        # Set confidence based on match type
        confidence_map = {
            MatchType.EXACT.value: ConfidenceScores.EXACT_MATCH,
            MatchType.CONTAINS.value: ConfidenceScores.LANGUAGE_SPECIFIC,
            MatchType.SEMANTIC.value: ConfidenceScores.SEMANTIC_MATCH,
            MatchType.UNKNOWN.value: ConfidenceScores.GENERIC_MATCH
        }
        
        for record in records:
            mappings.append({
                "concept_id": record.get("conceptId", ""),
                "preferred_term": record.get("preferredTerm", ""),
                "description": record.get("description", ""),
                "original_term": original_term,
                "confidence": float(confidence_map.get(match_type, ConfidenceScores.GENERIC_MATCH)),
                "match_type": match_type,
                "language": record.get("languageCode", Language.ENGLISH.value)
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