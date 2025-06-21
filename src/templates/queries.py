"""
SNOMED GraphRAG Queries for Medical Term Validation.

This module contains all Neo4j Cypher queries for SNOMED Canadian edition
medical term mapping and validation.
"""

# =============================================================================
# SNOMED Concept Search Queries
# =============================================================================

SNOMED_TERM_SEARCH_FRENCH = """
MATCH (c:Concept)-[:HAS_DESCRIPTION]->(d:Description)
WHERE toLower(d.term) CONTAINS $term
AND (d.languageCode = 'fr' OR d.languageCode = 'fr-CA' OR c.languageCode = 'fr')
AND c.active = true AND d.active = true
RETURN c.id as conceptId, 
       d.term as preferredTerm,
       d.term as description,
       COALESCE(d.languageCode, c.languageCode, 'fr') as languageCode,
       0.9 as confidence
ORDER BY size(d.term) ASC
LIMIT 3
"""

SNOMED_TERM_SEARCH_ENGLISH = """
MATCH (c:Concept)-[:HAS_DESCRIPTION]->(d:Description)
WHERE toLower(d.term) CONTAINS $term
AND (d.languageCode = 'en' OR d.languageCode = 'en-CA' OR c.languageCode = 'en' OR d.languageCode IS NULL)
AND c.active = true AND d.active = true
RETURN c.id as conceptId, 
       d.term as preferredTerm,
       d.term as description,
       COALESCE(d.languageCode, c.languageCode, 'en') as languageCode,
       0.9 as confidence
ORDER BY size(d.term) ASC
LIMIT 3
"""

SNOMED_TERM_SEARCH_GENERIC = """
MATCH (c:Concept)-[:HAS_DESCRIPTION]->(d:Description)
WHERE toLower(d.term) CONTAINS $term
AND c.active = true AND d.active = true
RETURN c.id as conceptId, 
       d.term as preferredTerm,
       d.term as description,
       COALESCE(d.languageCode, c.languageCode, 'en') as languageCode,
       0.8 as confidence
ORDER BY size(d.term) ASC
LIMIT 5
"""

# =============================================================================
# SNOMED Validation and Testing Queries
# =============================================================================

SNOMED_CONNECTION_TEST_QUERY = """
RETURN 1 as test
"""

# =============================================================================
# Advanced SNOMED Search Queries
# =============================================================================

SNOMED_EXACT_MATCH_QUERY = """
MATCH (c:Concept)-[:HAS_DESCRIPTION]->(d:Description)
WHERE toLower(d.term) = $term
AND c.active = true AND d.active = true
RETURN c.id as conceptId, 
       d.term as preferredTerm,
       d.term as description,
       COALESCE(d.languageCode, c.languageCode, 'en') as languageCode,
       1.0 as confidence
LIMIT 1
"""

SNOMED_SEMANTIC_SEARCH_QUERY = """
MATCH (c:Concept)-[:HAS_DESCRIPTION]->(d:Description)
WHERE any(word IN split($term, ' ') WHERE toLower(d.term) CONTAINS toLower(word))
AND c.active = true AND d.active = true
RETURN c.id as conceptId, 
       d.term as preferredTerm,
       d.term as description,
       COALESCE(d.languageCode, c.languageCode, 'en') as languageCode,
       0.7 as confidence
ORDER BY size(d.term) ASC
LIMIT 5
"""
