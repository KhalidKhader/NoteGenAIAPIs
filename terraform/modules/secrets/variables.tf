# =============================================================================
# Secrets Module Variables
# =============================================================================

variable "environment" {
  description = "Environment name (e.g., staging, prod)"
  type        = string
}

variable "app_name" {
  description = "Name of the application"
  type        = string
  default     = "notegen-ai-api"
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# Neo4j Secrets
# =============================================================================

variable "neo4j_password" {
  description = "Neo4j database password"
  type        = string
  sensitive   = true
}

# =============================================================================
# Azure OpenAI Secrets
# =============================================================================

variable "azure_openai_api_key" {
  description = "Azure OpenAI API key"
  type        = string
  sensitive   = true
}

variable "azure_openai_endpoint" {
  description = "Azure OpenAI endpoint URL"
  type        = string
  sensitive   = true
}

variable "azure_openai_embedding_api_key" {
  description = "Azure OpenAI embedding API key"
  type        = string
  sensitive   = true
}

variable "azure_openai_embedding_endpoint" {
  description = "Azure OpenAI embedding endpoint URL"
  type        = string
  sensitive   = true
}

# =============================================================================
# LangFuse Secrets
# =============================================================================

variable "langfuse_secret_key" {
  description = "LangFuse secret key"
  type        = string
  sensitive   = true
}

variable "langfuse_public_key" {
  description = "LangFuse public key"
  type        = string
  sensitive   = true
} 