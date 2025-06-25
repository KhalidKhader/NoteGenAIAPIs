// Neo4j module variables.tf 

variable "environment" {
  description = "Environment name (e.g., staging, prod)"
  type        = string
}

variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where Neo4j will be deployed"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for Neo4j ECS service"
  type        = list(string)
}

variable "neo4j_image" {
  description = "Neo4j Docker image"
  type        = string
  default     = "public.ecr.aws/docker/library/neo4j:5.15-community"
}

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



variable "backup_bucket" {
  description = "S3 bucket name for Neo4j data backup"
  type        = string
  default     = "notegen-neo4j-data-backup"
}

variable "backup_key" {
  description = "S3 key for Neo4j data backup file"
  type        = string
  default     = "neo4j-data-volume.tar.gz"
}

variable "volume_size" {
  description = "Size of EFS volume for Neo4j data in GB"
  type        = number
  default     = 20
}

variable "desired_count" {
  description = "Desired number of Neo4j tasks"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
} 