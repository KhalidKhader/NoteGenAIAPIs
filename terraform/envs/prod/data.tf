# Data sources for production environment
# Use these to reference existing AWS resources instead of hardcoding values

# Get current AWS caller identity
data "aws_caller_identity" "current" {}

# Get current AWS region
data "aws_region" "current" {}

# Get available AZs in the region
data "aws_availability_zones" "available" {
  state = "available"
}

# Example: Reference existing VPC if needed
# data "aws_vpc" "existing" {
#   filter {
#     name   = "tag:Name"
#     values = ["existing-vpc-name"]
#   }
# }

# Example: Reference existing subnets if needed
# data "aws_subnets" "existing_private" {
#   filter {
#     name   = "vpc-id"
#     values = [data.aws_vpc.existing.id]
#   }
#   filter {
#     name   = "tag:Type"
#     values = ["private"]
#   }
# }

# Example: Reference existing security groups if needed  
# data "aws_security_group" "existing" {
#   filter {
#     name   = "tag:Name"
#     values = ["existing-sg-name"]
#   }
# }

# ECR repository (if it exists)
# data "aws_ecr_repository" "app" {
#   name = "notegen-ai-api"
# }

# Route53 hosted zone (if needed for domain)
# data "aws_route53_zone" "main" {
#   count        = var.domain_name != "" ? 1 : 0
#   name         = var.domain_name
#   private_zone = false
# } 