"""
SNOMED GraphRAG Queries for Medical Term Validation.

This module contains all Neo4j Cypher queries for SNOMED Canadian edition
medical term mapping and validation.
"""
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum, auto

class MatchType(str, Enum):
    """Types of SNOMED term matches."""
    EXACT = "exact"
    CONTAINS = "contains"
    SEMANTIC = "semantic"
    UNKNOWN = "unknown"

class ConfidenceScores(float, Enum):
    """Confidence scores for different match types."""
    EXACT_MATCH = 1.0
    LANGUAGE_SPECIFIC = 0.9
    GENERIC_MATCH = 0.8
    SEMANTIC_MATCH = 0.7

class ResultLimits(int, Enum):
    """Result limits for different query types."""
    EXACT_MATCH = 1
    LANGUAGE_SPECIFIC = 3
    GENERIC_MATCH = 5
    SEMANTIC_MATCH = 5

class Language(str, Enum):
    """Supported languages with their variants."""
    ENGLISH = "en"
    ENGLISH_CA = "en-CA"
    FRENCH = "fr"
    FRENCH_CA = "fr-CA"
    
    @classmethod
    def get_variants(cls, base_lang: str) -> List[str]:
        """Get all variants for a base language."""
        if base_lang == "en":
            return [cls.ENGLISH.value, cls.ENGLISH_CA.value]
        elif base_lang == "fr":
            return [cls.FRENCH.value, cls.FRENCH_CA.value]
        return [base_lang]

@dataclass
class SNOMEDQueryParams:
    """Parameters for SNOMED queries with proper typing."""
    term: str
    language: str = Language.ENGLISH.value
    limit: int = ResultLimits.LANGUAGE_SPECIFIC
    confidence: float = ConfidenceScores.LANGUAGE_SPECIFIC
    match_type: MatchType = MatchType.CONTAINS

def get_term_search_query(params: SNOMEDQueryParams) -> Dict[str, Any]:
    """
    Generate Cypher query for SNOMED term search with language support.
    
    Args:
        params: SNOMEDQueryParams containing search parameters
        
    Returns:
        Dict containing query string and parameters
    """
    # Get language variants for the search
    lang_variants = Language.get_variants(params.language)
    
    # Build the language filter dynamically
    lang_conditions = " OR ".join([
        f"d.languageCode = '{lang}'" for lang in lang_variants
    ] + [f"c.languageCode = '{params.language}'"])
    
    # Add NULL check for English as fallback
    if params.language == Language.ENGLISH.value:
        lang_conditions += " OR d.languageCode IS NULL"

    base_query = """
MATCH (c:Concept)-[:HAS_DESCRIPTION]->(d:Description)
    WHERE toLower(d.term) {match_type} $term
    AND ({lang_conditions})
AND c.active = true AND d.active = true
    {with_clause}
RETURN c.id as conceptId, 
       d.term as preferredTerm,
       d.term as description,
           COALESCE(d.languageCode, c.languageCode, $default_lang) as languageCode,
           {confidence_calc} as confidence
    ORDER BY {order_by}
    LIMIT $limit
    """

    # Customize query based on match type
    match_type_map = {
        MatchType.EXACT: "=",
        MatchType.CONTAINS: "CONTAINS",
        MatchType.SEMANTIC: "CONTAINS"  # Will be handled differently
    }

    if params.match_type == MatchType.SEMANTIC:
        with_clause = """
        WITH c, d, size(split($term, ' ')) as queryWords,
        size([word IN split($term, ' ') WHERE toLower(d.term) CONTAINS toLower(word)]) as matchedWords
        WHERE matchedWords > 0"""
        confidence_calc = "$confidence * (matchedWords * 1.0 / queryWords)"
        order_by = "confidence DESC, size(d.term) ASC"
    else:
        with_clause = ""
        confidence_calc = "$confidence"
        order_by = "size(d.term) ASC"

    query = base_query.format(
        match_type=match_type_map.get(params.match_type, "CONTAINS"),
        lang_conditions=lang_conditions,
        with_clause=with_clause,
        confidence_calc=confidence_calc,
        order_by=order_by
    )

    return {
        "query": query,
        "params": {
            "term": params.term.lower(),
            "limit": params.limit,
            "confidence": params.confidence,
            "default_lang": params.language
        }
    }

def get_exact_match_query(params: SNOMEDQueryParams) -> Dict[str, Any]:
    """Generate Cypher query for exact SNOMED term match."""
    return get_term_search_query(SNOMEDQueryParams(
        term=params.term,
        language=params.language,
        limit=ResultLimits.EXACT_MATCH,
        confidence=ConfidenceScores.EXACT_MATCH,
        match_type=MatchType.EXACT
    ))

def get_semantic_search_query(params: SNOMEDQueryParams) -> Dict[str, Any]:
    """Generate Cypher query for semantic SNOMED term search using word tokenization."""
    return get_term_search_query(SNOMEDQueryParams(
        term=params.term,
        language=params.language,
        limit=ResultLimits.SEMANTIC_MATCH,
        confidence=ConfidenceScores.SEMANTIC_MATCH,
        match_type=MatchType.SEMANTIC
    ))

def get_connection_test_query() -> Dict[str, Any]:
    """Generate Cypher query for testing Neo4j connection."""
    return {
        "query": "RETURN 1 as test",
        "params": {}
    }
