# =============================================================================
# SSM Parameter Store for NoteGen AI APIs Configuration
# =============================================================================

# Neo4j Configuration Parameters
resource "aws_ssm_parameter" "neo4j_uri" {
  name        = "/notegen-ai-api/${var.environment}/neo4j/uri"
  description = "Neo4j connection URI for ${var.environment}"
  type        = "String"
  value       = var.neo4j_bolt_uri

  tags = merge(var.tags, {
    Name        = "neo4j-uri"
    Environment = var.environment
    Component   = "neo4j"
  })
}

# OpenSearch Configuration Parameters  
resource "aws_ssm_parameter" "opensearch_endpoint" {
  name        = "/notegen-ai-api/${var.environment}/opensearch/endpoint"
  description = "OpenSearch endpoint for ${var.environment}"
  type        = "String"
  value       = "https://${var.opensearch_endpoint}:443"

  tags = merge(var.tags, {
    Name        = "opensearch-endpoint"
    Environment = var.environment
    Component   = "opensearch"
  })
}

# Azure OpenAI Configuration Parameters
resource "aws_ssm_parameter" "azure_openai_endpoint" {
  name        = "/notegen-ai-api/${var.environment}/azure-openai/endpoint"
  description = "Azure OpenAI endpoint for ${var.environment}"
  type        = "String"
  value       = var.azure_openai_endpoint

  tags = merge(var.tags, {
    Name        = "azure-openai-endpoint"
    Environment = var.environment
    Component   = "azure-openai"
  })
}

resource "aws_ssm_parameter" "azure_openai_embedding_endpoint" {
  name        = "/notegen-ai-api/${var.environment}/azure-openai/embedding-endpoint"
  description = "Azure OpenAI embedding endpoint for ${var.environment}"
  type        = "String"
  value       = var.azure_openai_embedding_endpoint

  tags = merge(var.tags, {
    Name        = "azure-openai-embedding-endpoint"
    Environment = var.environment
    Component   = "azure-openai"
  })
}

# NoteGen API Configuration Parameters
resource "aws_ssm_parameter" "notegen_api_base_url" {
  name        = "/notegen-ai-api/${var.environment}/notegen-api/base-url"
  description = "NoteGen API base URL for ${var.environment}"
  type        = "String"
  value       = var.notegen_api_base_url

  tags = merge(var.tags, {
    Name        = "notegen-api-base-url"
    Environment = var.environment
    Component   = "notegen-api"
  })
} 