// staging environment variables.tf

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ca-central-1"
}

variable "app_image" {
  description = "Docker image for the FastAPI application (leave empty to use auto-created ECR repository)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ARN of SSL certificate for HTTPS (leave empty for staging)"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Domain name for the application (optional for staging)"
  type        = string
  default     = ""
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["ca-central-1a", "ca-central-1b"]
}

# ECS Configuration
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

variable "desired_count" {
  description = "Desired number of application tasks"
  type        = number
  default     = 1
}

# Neo4j Configuration
variable "neo4j_cpu" {
  description = "CPU units for Neo4j container"
  type        = number
  default     = 1024
}

variable "neo4j_memory" {
  description = "Memory for Neo4j container in MB"
  type        = number
  default     = 2048
}

# OpenSearch Configuration
variable "opensearch_instance_type" {
  description = "Instance type for OpenSearch cluster"
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_instance_count" {
  description = "Number of instances in OpenSearch cluster"
  type        = number
  default     = 1
}

variable "opensearch_volume_size" {
  description = "Size of EBS volumes for OpenSearch in GB"
  type        = number
  default     = 10
}

# =============================================================================
# Application Configuration
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

variable "opensearch_index" {
  description = "OpenSearch index name"
  type        = string
  default     = "medical-conversations"
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

variable "notegen_api_base_url" {
  description = "Base URL for the NoteGen API service"
  type        = string
  default     = "http://localhost:3000"
}

# =============================================================================
# Secrets Configuration (managed in AWS Secrets Manager)
# =============================================================================

variable "neo4j_password" {
  description = "Neo4j database password (managed in AWS Secrets Manager)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "azure_openai_api_key" {
  description = "Azure OpenAI API key (managed in AWS Secrets Manager)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "azure_openai_endpoint" {
  description = "Azure OpenAI endpoint URL"
  type        = string
  sensitive   = true
  default     = ""
}

variable "azure_openai_embedding_api_key" {
  description = "Azure OpenAI embedding API key (managed in AWS Secrets Manager)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "azure_openai_embedding_endpoint" {
  description = "Azure OpenAI embedding endpoint URL"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_secret_key" {
  description = "LangFuse secret key (managed in AWS Secrets Manager)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_public_key" {
  description = "LangFuse public key (managed in AWS Secrets Manager)"
  type        = string
  sensitive   = true
  default     = ""
} 