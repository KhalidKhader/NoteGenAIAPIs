# =============================================================================
# Parameters Module Outputs
# =============================================================================

# Parameter ARNs for IAM policies
output "neo4j_uri_parameter_arn" {
  description = "ARN of the Neo4j URI parameter"
  value       = aws_ssm_parameter.neo4j_uri.arn
}

output "opensearch_endpoint_parameter_arn" {
  description = "ARN of the OpenSearch endpoint parameter"
  value       = aws_ssm_parameter.opensearch_endpoint.arn
}

output "azure_openai_endpoint_parameter_arn" {
  description = "ARN of the Azure OpenAI endpoint parameter"
  value       = aws_ssm_parameter.azure_openai_endpoint.arn
}

output "azure_openai_embedding_endpoint_parameter_arn" {
  description = "ARN of the Azure OpenAI embedding endpoint parameter"
  value       = aws_ssm_parameter.azure_openai_embedding_endpoint.arn
}

output "notegen_api_base_url_parameter_arn" {
  description = "ARN of the NoteGen API base URL parameter"
  value       = aws_ssm_parameter.notegen_api_base_url.arn
}

# Parameter names for reference
output "parameter_names" {
  description = "Map of parameter names"
  value = {
    neo4j_uri                        = aws_ssm_parameter.neo4j_uri.name
    opensearch_endpoint              = aws_ssm_parameter.opensearch_endpoint.name
    azure_openai_endpoint            = aws_ssm_parameter.azure_openai_endpoint.name
    azure_openai_embedding_endpoint  = aws_ssm_parameter.azure_openai_embedding_endpoint.name
    notegen_api_base_url            = aws_ssm_parameter.notegen_api_base_url.name
  }
}

# All parameter ARNs for IAM policy
output "all_parameter_arns" {
  description = "List of all parameter ARNs for IAM policies"
  value = [
    aws_ssm_parameter.neo4j_uri.arn,
    aws_ssm_parameter.opensearch_endpoint.arn,
    aws_ssm_parameter.azure_openai_endpoint.arn,
    aws_ssm_parameter.azure_openai_embedding_endpoint.arn,
    aws_ssm_parameter.notegen_api_base_url.arn
  ]
} 