variable "collection_name" {
  description = "Name of the OpenSearch Serverless collection"
  type        = string
}

variable "description" {
  description = "Description for the collection"
  type        = string
  default     = "OpenSearch Serverless collection for NoteGen transcripts"
}

variable "allow_from_public" {
  description = "Whether to allow public access to the collection (true/false)"
  type        = bool
  default     = false
}

variable "vpc_id" {
  description = "VPC ID for the VPC Endpoint"
  type        = string
  default     = null
}

variable "subnet_ids" {
  description = "Subnet IDs for the VPC Endpoint"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security Group IDs to associate with the VPC Endpoint"
  type        = list(string)
  default     = []
} 