# =============================================================================
# GitHub OIDC Provider and IAM Roles for GitHub Actions
# =============================================================================

# GitHub OIDC Provider
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com",
  ]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1", # GitHub Actions thumbprint
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd", # Backup thumbprint
  ]

  tags = merge(var.tags, {
    Name        = "github-actions-oidc-provider"
    Environment = var.environment
    Component   = "github-actions"
  })
}

# Data source to get current AWS account ID and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# =============================================================================
# GitHub Actions IAM Role for Staging
# =============================================================================

# Trust policy for staging GitHub Actions role
data "aws_iam_policy_document" "github_actions_staging_assume_role" {
  statement {
    effect = "Allow"
    
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    
    actions = ["sts:AssumeRoleWithWebIdentity"]
    
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [
        "repo:${var.github_repository}:ref:refs/heads/develop",
        "repo:${var.github_repository}:ref:refs/heads/v3",
        "repo:${var.github_repository}:environment:staging",
        "repo:${var.github_repository}:ref:refs/heads/main"
      ]
    }
  }
}

# IAM Role for GitHub Actions Staging
resource "aws_iam_role" "github_actions_staging" {
  name               = "${var.app_name}-${var.environment}-github-actions-role"
  assume_role_policy = data.aws_iam_policy_document.github_actions_staging_assume_role.json

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-github-actions-role"
    Environment = var.environment
    Component   = "github-actions"
  })
}

# IAM Policy for GitHub Actions Staging
data "aws_iam_policy_document" "github_actions_staging_policy" {
  # ECR permissions
  statement {
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:GetRepositoryPolicy",
      "ecr:DescribeRepositories",
      "ecr:ListImages",
      "ecr:DescribeImages",
      "ecr:BatchGetImage",
      "ecr:GetLifecyclePolicy",
      "ecr:GetLifecyclePolicyPreview",
      "ecr:ListTagsForResource",
      "ecr:DescribeImageScanFindings",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage"
    ]
    resources = [var.ecr_repository_arn]
  }

  # ECR token permissions
  statement {
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken"
    ]
    resources = ["*"]
  }

  # ECS permissions for staging (scoped)
  statement {
    effect = "Allow"
    actions = [
      "ecs:RegisterTaskDefinition",
      "ecs:DescribeTaskDefinition",
      "ecs:DescribeServices",
      "ecs:DescribeTasks",
      "ecs:UpdateService",
      "ecs:DescribeClusters",
      "ecs:ListTasks"
    ]
    resources = [
      "arn:aws:ecs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:cluster/${var.ecs_cluster_name}",
      "arn:aws:ecs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:service/${var.ecs_cluster_name}/${var.ecs_service_name}",
      "arn:aws:ecs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:task-definition/${var.app_name}-${var.environment}:*",
      "arn:aws:ecs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:container-instance/${var.ecs_cluster_name}/*",
      "arn:aws:ecs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:task/${var.ecs_cluster_name}/*"
    ]
  }

  # ECS permissions that require wildcard resource
  statement {
    effect    = "Allow"
    actions   = ["ecs:ListTaskDefinitions"]
    resources = ["*"]
  }

  # ECS wait permissions
  statement {
    effect = "Allow"
    actions = [
      "ecs:DescribeServices"
    ]
    resources = ["*"]
  }

  # Load balancer permissions for health checks
  statement {
    effect = "Allow"
    actions = [
      "elasticloadbalancing:DescribeTargetGroups",
      "elasticloadbalancing:DescribeLoadBalancers"
    ]
    resources = ["*"]
  }

  # IAM permissions to pass roles to ECS
  statement {
    effect = "Allow"
    actions = [
      "iam:PassRole"
    ]
    resources = [
      var.ecs_execution_role_arn,
      var.ecs_task_role_arn
    ]
  }

  # STS permissions for getting account info
  statement {
    effect = "Allow"
    actions = [
      "sts:GetCallerIdentity"
    ]
    resources = ["*"]
  }
}

# Attach policy to staging role
resource "aws_iam_role_policy" "github_actions_staging" {
  name   = "${var.app_name}-${var.environment}-github-actions-policy"
  role   = aws_iam_role.github_actions_staging.id
  policy = data.aws_iam_policy_document.github_actions_staging_policy.json
}

# =============================================================================
# GitHub Actions IAM Role for Production (Optional)
# =============================================================================

# Trust policy for production GitHub Actions role
data "aws_iam_policy_document" "github_actions_prod_assume_role" {
  count = var.create_prod_role ? 1 : 0
  
  statement {
    effect = "Allow"
    
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    
    actions = ["sts:AssumeRoleWithWebIdentity"]
    
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [
        "repo:${var.github_repository}:ref:refs/heads/main"
      ]
    }
  }
}

# IAM Role for GitHub Actions Production
resource "aws_iam_role" "github_actions_prod" {
  count = var.create_prod_role ? 1 : 0
  
  name               = "${var.app_name}-prod-github-actions-role"
  assume_role_policy = data.aws_iam_policy_document.github_actions_prod_assume_role[0].json

  tags = merge(var.tags, {
    Name        = "${var.app_name}-prod-github-actions-role"
    Environment = "prod"
    Component   = "github-actions"
  })
} 