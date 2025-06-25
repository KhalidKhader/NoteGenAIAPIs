// Neo4j module outputs.tf 

# Neo4j Service Outputs
output "cluster_name" {
  description = "ECS cluster name where Neo4j is running"
  value       = var.cluster_name
}

output "service_name" {
  description = "ECS service name for Neo4j"
  value       = aws_ecs_service.neo4j.name
}

output "task_definition_arn" {
  description = "ARN of the Neo4j task definition"
  value       = aws_ecs_task_definition.neo4j.arn
}

output "security_group_id" {
  description = "ID of the Neo4j security group"
  value       = aws_security_group.neo4j.id
}

output "efs_file_system_id" {
  description = "ID of the EFS file system for Neo4j data"
  value       = aws_efs_file_system.neo4j_data.id
}

output "password_secret_arn" {
  description = "ARN of the Secrets Manager secret containing Neo4j password"
  value       = aws_secretsmanager_secret.neo4j_password.arn
}

output "service_discovery_arn" {
  description = "ARN of the service discovery service"
  value       = aws_service_discovery_service.neo4j.arn
}

output "neo4j_endpoint" {
  description = "Neo4j service endpoint (for internal VPC access)"
  value       = "neo4j.notegen-ai-api-${var.environment}.local"
}

output "neo4j_bolt_uri" {
  description = "Neo4j Bolt URI for application connections"
  value       = "bolt://neo4j.notegen-ai-api-${var.environment}.local:7687"
}

output "neo4j_http_uri" {
  description = "Neo4j HTTP URI for browser access"
  value       = "http://neo4j.notegen-ai-api-${var.environment}.local:7474"
}

output "neo4j_generated_password" {
  description = "Generated Neo4j password (stored in Secrets Manager)"
  value       = random_password.neo4j_password.result
  sensitive   = true
} 