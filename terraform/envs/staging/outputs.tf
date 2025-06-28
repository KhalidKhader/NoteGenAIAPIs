# Staging environment outputs

# ECR Outputs
output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = module.ecr.repository_url
}

output "ecr_repository_name" {
  description = "Name of the ECR repository"
  value       = module.ecr.repository_name
}

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

# =============================================================================
# GitHub OIDC Outputs
# =============================================================================

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions IAM role"
  value       = module.github_oidc.github_actions_staging_role_arn
}

output "github_oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider"
  value       = module.github_oidc.github_oidc_provider_arn
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnet_ids
}

# ECS Outputs
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs_service.cluster_name
}

output "load_balancer_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.ecs_service.load_balancer_dns_name
}

output "application_url" {
  description = "URL to access the application"
  value       = "http://${module.ecs_service.load_balancer_dns_name}"
}

# Application Load Balancer
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.ecs_service.alb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = module.ecs_service.load_balancer_zone_id
}

# Neo4j Outputs
output "neo4j_endpoint" {
  description = "Neo4j service endpoint"
  value       = module.neo4j.neo4j_endpoint
}

output "neo4j_bolt_uri" {
  description = "Neo4j Bolt URI"
  value       = module.neo4j.neo4j_bolt_uri
}

# Secrets Manager ARNs
output "neo4j_password_secret_arn" {
  description = "ARN of Neo4j password secret"
  value       = module.neo4j.password_secret_arn
  sensitive   = true
} 