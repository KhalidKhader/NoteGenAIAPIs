// ECS service module variables.tf 

variable "environment" {
  description = "Environment name (e.g., staging, prod)"
  type        = string
}

variable "app_name" {
  description = "Name of the application"
  type        = string
  default     = "notegen-ai-api"
}

variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where ECS service will be deployed"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for ECS service (tasks)"
  type        = list(string)
}

variable "alb_subnet_ids" {
  description = "List of subnet IDs for ALB (should be public subnets)"
  type        = list(string)
  default     = []
}

variable "app_image" {
  description = "Docker image for the application"
  type        = string
}

variable "app_cpu" {
  description = "CPU units for the application container"
  type        = number
  default     = 512
}

variable "app_memory" {
  description = "Memory for the application container in MB"
  type        = number
  default     = 1024
}

variable "app_port" {
  description = "Port the application listens on"
  type        = number
  default     = 8000
}

variable "desired_count" {
  description = "Desired number of application tasks"
  type        = number
  default     = 2
}

variable "health_check_path" {
  description = "Health check path for the application"
  type        = string
  default     = "/health"
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "secrets_arns" {
  description = "List of Secrets Manager ARNs the application needs access to"
  type        = list(string)
  default     = []
}

variable "parameter_arns" {
  description = "List of SSM Parameter ARNs the application needs access to"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# Application Configuration Variables
# =============================================================================

variable "log_level" {
  description = "Log level for the application"
  type        = string
  default     = "INFO"
}

variable "debug" {
  description = "Enable debug mode"
  type        = bool
  default     = false
}

variable "cors_origins" {
  description = "CORS origins for the application"
  type        = string
  default     = "http://localhost:3000,http://localhost:8000"
}

# =============================================================================
# OpenSearch Configuration
# =============================================================================

variable "opensearch_index" {
  description = "OpenSearch index name"
  type        = string
  default     = "medical-conversations"
}

variable "opensearch_endpoint" {
  description = "OpenSearch Serverless collection endpoint URL"
  type        = string
}

# =============================================================================
# Neo4j Configuration
# =============================================================================

variable "neo4j_uri" {
  description = "Neo4j connection URI"
  type        = string
}

variable "neo4j_user" {
  description = "Neo4j username"
  type        = string
  default     = "neo4j"
}

variable "neo4j_database" {
  description = "Neo4j database name"
  type        = string
  default     = "neo4j"
}

variable "neo4j_secret_arn" {
  description = "ARN of the Neo4j secrets in AWS Secrets Manager"
  type        = string
}

# =============================================================================
# NoteGen API Configuration
# =============================================================================

variable "notegen_api_base_url" {
  description = "Base URL for the NoteGen API service"
  type        = string
  default     = "http://localhost:3000"
}

# =============================================================================
# Azure OpenAI Configuration
# =============================================================================

variable "azure_openai_deployment_name" {
  description = "Azure OpenAI deployment name"
  type        = string
  default     = "gpt-4o"
}

variable "azure_openai_api_version" {
  description = "Azure OpenAI API version"
  type        = string
  default     = "2024-05-01-preview"
}

variable "azure_openai_model" {
  description = "Azure OpenAI model name"
  type        = string
  default     = "gpt-4o"
}

variable "azure_openai_embedding_deployment_name" {
  description = "Azure OpenAI embedding deployment name"
  type        = string
  default     = "text-embedding-ada-002"
}

variable "azure_openai_embedding_model" {
  description = "Azure OpenAI embedding model name"
  type        = string
  default     = "text-embedding-ada-002"
}

variable "azure_openai_api_key_secret_arn" {
  description = "ARN of the Azure OpenAI API key secret in AWS Secrets Manager"
  type        = string
}

variable "azure_openai_endpoint_secret_arn" {
  description = "ARN of the Azure OpenAI endpoint secret in AWS Secrets Manager"
  type        = string
}

variable "azure_openai_embedding_api_key_secret_arn" {
  description = "ARN of the Azure OpenAI Embedding API key secret in AWS Secrets Manager"
  type        = string
}

variable "azure_openai_embedding_endpoint_secret_arn" {
  description = "ARN of the Azure OpenAI embedding endpoint secret in AWS Secrets Manager"
  type        = string
}

# =============================================================================
# LangFuse Configuration
# =============================================================================

variable "langfuse_host" {
  description = "LangFuse host URL"
  type        = string
  default     = "https://us.cloud.langfuse.com"
}

variable "langfuse_secret_key_secret_arn" {
  description = "ARN of the LangFuse secret key in AWS Secrets Manager"
  type        = string
}

variable "langfuse_public_key_secret_arn" {
  description = "ARN of the LangFuse public key in AWS Secrets Manager"
  type        = string
}

# =============================================================================
# Additional Configuration
# =============================================================================

variable "alb_name_override" {
  description = "Override ALB naming prefix (useful for migration scenarios)"
  type        = string
  default     = ""
}

variable "environment_variables" {
  description = "Additional environment variables for the container"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "additional_secrets" {
  description = "Additional secrets for the container"
  type = list(object({
    name      = string
    valueFrom = string
  }))
  default = []
}

variable "aws_region" {
  description = "AWS region for resource construction (used for AOSS ARN)"
  type        = string
} 