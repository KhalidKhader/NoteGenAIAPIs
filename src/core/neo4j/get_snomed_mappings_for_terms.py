from typing import Dict, List, Any
from src.core.settings.config import settings
from src.core.settings.logging import logger
from src.core.neo4j.snomed_rag_service import SNOMEDRAGService

async def get_snomed_mappings_for_terms(
    medical_terms: List[str], 
    language: str = "en",
) -> List[Dict[str, Any]]:
    """
    Get SNOMED mappings for medical terms using Neo4j GraphRAG.
    
    Args:
        medical_terms: List of medical terms to map
        language: Language code provided by NestJS API ("en" or "fr")
        logger: Optional medical processing logger
    
    Returns:
        List of SNOMED mappings with concept IDs and preferred terms
    """
    snomed_rag_service = SNOMEDRAGService()
    if not snomed_rag_service._initialized or not snomed_rag_service.driver:
        await snomed_rag_service.initialize()
    
    if not medical_terms:
        return []
    
    logger.info(f"Getting SNOMED mappings for {len(medical_terms)} terms in language: {language}")
    
    
    details = {
        "medical_terms": medical_terms,
        "language": language,
        "database": "NEO4J_SNOMED_CANADIAN_EDITION",
        "query_strategy": "EXACT_MATCH_THEN_CONTAINS_THEN_SEMANTIC"
    }
    logger.info(f"NEO4J_SNOMED_MAPPING_START Starting SNOMED mapping for {len(medical_terms)} medical terms, details={details}")

    try:
        mappings = []
        
        async with snomed_rag_service.driver.session(database=settings.neo4j_database) as session:
            for i, term in enumerate(medical_terms):
                
                details = {
                        "term": term,
                        "term_index": i + 1,
                        "total_terms": len(medical_terms),
                        "language": language
                    }
                logger.info(f"NEO4J_TERM_QUERY_START Querying Neo4j for term '{term}' ({i+1}/{len(medical_terms)}), details={details}")
                
                term_mappings = await snomed_rag_service._search_snomed_term(session, term, language)
                mappings.extend(term_mappings)
                
                
                for mapping in term_mappings:
                    logger.info(f"{term}, {mapping}")
        
        
            details={"total_mappings_found": len(mappings),
                    "terms_processed": len(medical_terms),
                    "success_rate": len(mappings) / len(medical_terms) if medical_terms else 0,
                    "database": "NEO4J_SNOMED_CANADIAN_EDITION"
                }
            logger.info(f"NEO4J_SNOMED_MAPPING_COMPLETED SNOMED mapping completed: {len(mappings)} mappings found, details={details}")
        
        logger.info(f"Found {len(mappings)} SNOMED mappings")
        return mappings
        
    except Exception as e:
        logger.error(f"Failed to get SNOMED mappings: {str(e)}")
        
        details = {"error": str(e), "terms": medical_terms}
        logger.error(f"NEO4J_SNOMED_MAPPING_FAILED SNOMED mapping failed: {str(e)}, details={details}")
        raise RuntimeError(f"SNOMED mapping failed: {str(e)}")