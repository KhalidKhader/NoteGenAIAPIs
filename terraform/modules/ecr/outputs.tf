output "repository_name" {
  description = "Name of the ECR repository"
  value       = aws_ecr_repository.app.name
}

output "repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.app.arn
}

output "repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.app.repository_url
}

output "registry_id" {
  description = "Registry ID where the repository was created"
  value       = aws_ecr_repository.app.registry_id
}

output "repository_uri_with_tag" {
  description = "Repository URI with latest tag"
  value       = "${aws_ecr_repository.app.repository_url}:latest"
} 