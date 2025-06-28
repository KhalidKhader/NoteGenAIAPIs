output "collection_arn" {
  description = "ARN of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.arn
}

output "collection_id" {
  description = "ID of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.id
}

output "collection_name" {
  description = "Name of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.name
}

output "collection_endpoint" {
  description = "Endpoint URL of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.collection_endpoint
} 