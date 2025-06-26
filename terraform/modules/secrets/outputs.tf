# =============================================================================
# Secrets Module Outputs
# =============================================================================

output "neo4j_secret_arn" {
  description = "ARN of the Neo4j secret"
  value       = aws_secretsmanager_secret.neo4j.arn
  sensitive   = true
}

output "neo4j_password_secret_arn" {
  description = "ARN of the Neo4j password secret"
  value       = aws_secretsmanager_secret.neo4j_password.arn
  sensitive   = true
}

output "azure_openai_api_key_secret_arn" {
  description = "ARN of the Azure OpenAI API key secret"
  value       = aws_secretsmanager_secret.azure_openai_api_key.arn
  sensitive   = true
}

output "azure_openai_embedding_api_key_secret_arn" {
  description = "ARN of the Azure OpenAI Embedding API key secret"
  value       = aws_secretsmanager_secret.azure_openai_embedding_api_key.arn
  sensitive   = true
}

output "azure_openai_endpoint_secret_arn" {
  description = "ARN of the Azure OpenAI endpoint secret"
  value       = aws_secretsmanager_secret.azure_openai_endpoint.arn
  sensitive   = true
}

output "azure_openai_embedding_endpoint_secret_arn" {
  description = "ARN of the Azure OpenAI embedding endpoint secret"
  value       = aws_secretsmanager_secret.azure_openai_embedding_endpoint.arn
  sensitive   = true
}

output "langfuse_secret_key_secret_arn" {
  description = "ARN of the LangFuse secret key"
  value       = aws_secretsmanager_secret.langfuse_secret_key.arn
  sensitive   = true
}

output "langfuse_public_key_secret_arn" {
  description = "ARN of the LangFuse public key"
  value       = aws_secretsmanager_secret.langfuse_public_key.arn
  sensitive   = true
}

# Secret names for reference
output "neo4j_secret_name" {
  description = "Name of the Neo4j secret"
  value       = aws_secretsmanager_secret.neo4j.name
}

output "neo4j_password_secret_name" {
  description = "Name of the Neo4j password secret"
  value       = aws_secretsmanager_secret.neo4j_password.name
}

output "azure_openai_api_key_secret_name" {
  description = "Name of the Azure OpenAI API key secret"
  value       = aws_secretsmanager_secret.azure_openai_api_key.name
}

output "azure_openai_embedding_api_key_secret_name" {
  description = "Name of the Azure OpenAI Embedding API key secret"
  value       = aws_secretsmanager_secret.azure_openai_embedding_api_key.name
}

output "azure_openai_endpoint_secret_name" {
  description = "Name of the Azure OpenAI endpoint secret"
  value       = aws_secretsmanager_secret.azure_openai_endpoint.name
}

output "azure_openai_embedding_endpoint_secret_name" {
  description = "Name of the Azure OpenAI embedding endpoint secret"
  value       = aws_secretsmanager_secret.azure_openai_embedding_endpoint.name
}

output "langfuse_secret_key_secret_name" {
  description = "Name of the LangFuse secret key"
  value       = aws_secretsmanager_secret.langfuse_secret_key.name
}

output "langfuse_public_key_secret_name" {
  description = "Name of the LangFuse public key"
  value       = aws_secretsmanager_secret.langfuse_public_key.name
} 