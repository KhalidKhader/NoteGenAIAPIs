# =============================================================================
# Parameters Module Variables
# =============================================================================

variable "environment" {
  description = "Environment name (e.g., staging, prod)"
  type        = string
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# Neo4j Configuration
# =============================================================================

variable "neo4j_bolt_uri" {
  description = "Neo4j Bolt connection URI from Terraform output"
  type        = string
}

# =============================================================================
# OpenSearch Configuration
# =============================================================================

variable "opensearch_endpoint" {
  description = "OpenSearch endpoint URL"
  type        = string
}

# =============================================================================
# Azure OpenAI Configuration
# =============================================================================

variable "azure_openai_endpoint" {
  description = "Azure OpenAI endpoint URL"
  type        = string
}

variable "azure_openai_embedding_endpoint" {
  description = "Azure OpenAI embedding endpoint URL"
  type        = string
}

# =============================================================================
# NoteGen API Configuration
# =============================================================================

variable "notegen_api_base_url" {
  description = "NoteGen API base URL"
  type        = string
} 