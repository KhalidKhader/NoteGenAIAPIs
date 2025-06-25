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

# OpenSearch Outputs
output "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = module.opensearch.domain_endpoint
}

output "opensearch_kibana_endpoint" {
  description = "OpenSearch Kibana endpoint"
  value       = module.opensearch.kibana_endpoint
}

# Secrets Manager ARNs
output "opensearch_password_secret_arn" {
  description = "ARN of OpenSearch password secret"
  value       = module.opensearch.password_secret_arn
  sensitive   = true
}

output "neo4j_password_secret_arn" {
  description = "ARN of Neo4j password secret"
  value       = module.neo4j.password_secret_arn
  sensitive   = true
} 