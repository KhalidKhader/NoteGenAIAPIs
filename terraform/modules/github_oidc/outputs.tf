# =============================================================================
# Outputs for GitHub OIDC Module
# =============================================================================

output "github_oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider"
  value       = aws_iam_openid_connect_provider.github.arn
}

output "github_actions_staging_role_arn" {
  description = "ARN of the GitHub Actions IAM role for staging"
  value       = aws_iam_role.github_actions_staging.arn
}

output "github_actions_staging_role_name" {
  description = "Name of the GitHub Actions IAM role for staging"
  value       = aws_iam_role.github_actions_staging.name
}

output "github_actions_prod_role_arn" {
  description = "ARN of the GitHub Actions IAM role for production"
  value       = var.create_prod_role ? aws_iam_role.github_actions_prod[0].arn : null
}

output "github_actions_prod_role_name" {
  description = "Name of the GitHub Actions IAM role for production"
  value       = var.create_prod_role ? aws_iam_role.github_actions_prod[0].name : null
} 