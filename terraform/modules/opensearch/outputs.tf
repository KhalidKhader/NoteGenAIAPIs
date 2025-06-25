// OpenSearch module outputs.tf 

output "domain_arn" {
  description = "ARN of the OpenSearch domain"
  value       = aws_opensearch_domain.main.arn
}

output "domain_id" {
  description = "Unique identifier for the OpenSearch domain"
  value       = aws_opensearch_domain.main.domain_id
}

output "domain_name" {
  description = "Name of the OpenSearch domain"
  value       = aws_opensearch_domain.main.domain_name
}

output "domain_endpoint" {
  description = "Domain-specific endpoint used to submit index, search, and data upload requests"
  value       = aws_opensearch_domain.main.endpoint
}

output "kibana_endpoint" {
  description = "Domain-specific endpoint for Kibana"
  value       = aws_opensearch_domain.main.kibana_endpoint
}

output "security_group_id" {
  description = "ID of the security group for OpenSearch"
  value       = aws_security_group.opensearch.id
}

output "username_secret_arn" {
  description = "ARN of the Secrets Manager secret containing OpenSearch username"
  value       = aws_secretsmanager_secret.opensearch_username.arn
}

output "password_secret_arn" {
  description = "ARN of the Secrets Manager secret containing OpenSearch password"
  value       = aws_secretsmanager_secret.opensearch_password.arn
} 