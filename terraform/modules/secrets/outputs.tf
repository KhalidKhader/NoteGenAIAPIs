# =============================================================================
# Secrets Module Outputs
# =============================================================================

output "neo4j_secret_arn" {
  description = "ARN of the Neo4j secret"
  value       = aws_secretsmanager_secret.neo4j.arn
  sensitive   = true
}

output "azure_openai_secret_arn" {
  description = "ARN of the Azure OpenAI secret"
  value       = aws_secretsmanager_secret.azure_openai.arn
  sensitive   = true
}

output "langfuse_secret_arn" {
  description = "ARN of the LangFuse secret"
  value       = aws_secretsmanager_secret.langfuse.arn
  sensitive   = true
}

# Secret names for reference
output "neo4j_secret_name" {
  description = "Name of the Neo4j secret"
  value       = aws_secretsmanager_secret.neo4j.name
}

output "azure_openai_secret_name" {
  description = "Name of the Azure OpenAI secret"
  value       = aws_secretsmanager_secret.azure_openai.name
}

output "langfuse_secret_name" {
  description = "Name of the LangFuse secret"
  value       = aws_secretsmanager_secret.langfuse.name
} 