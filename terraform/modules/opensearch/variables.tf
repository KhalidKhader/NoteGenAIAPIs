// OpenSearch module variables.tf 

variable "environment" {
  description = "Environment name (e.g., staging, prod)"
  type        = string
}

variable "domain_name" {
  description = "OpenSearch domain name"
  type        = string
}

variable "opensearch_version" {
  description = "OpenSearch version"
  type        = string
  default     = "2.11"
}

variable "instance_type" {
  description = "Instance type for OpenSearch cluster"
  type        = string
  default     = "t3.small.search"
}

variable "instance_count" {
  description = "Number of instances in the OpenSearch cluster"
  type        = number
  default     = 2
}

variable "dedicated_master_enabled" {
  description = "Whether dedicated master nodes are enabled"
  type        = bool
  default     = false
}

variable "master_instance_type" {
  description = "Instance type for dedicated master nodes"
  type        = string
  default     = "t3.small.search"
}

variable "master_instance_count" {
  description = "Number of dedicated master nodes"
  type        = number
  default     = 3
}

variable "ebs_enabled" {
  description = "Whether EBS volumes are attached"
  type        = bool
  default     = true
}

variable "volume_type" {
  description = "Type of EBS volumes"
  type        = string
  default     = "gp3"
}

variable "volume_size" {
  description = "Size of EBS volumes in GB"
  type        = number
  default     = 20
}

variable "vpc_id" {
  description = "VPC ID where OpenSearch will be deployed"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for OpenSearch"
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs for OpenSearch"
  type        = list(string)
  default     = []
}

variable "access_policies" {
  description = "IAM policy document for OpenSearch access"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
} 