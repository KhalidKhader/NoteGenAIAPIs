// OpenSearch module main.tf 

# Security Group for OpenSearch
resource "aws_security_group" "opensearch" {
  name_prefix = "notegen-ai-api-${var.environment}-opensearch-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"] # Allow from VPC
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "notegen-ai-api-${var.environment}-opensearch-sg"
    Environment = var.environment
  })
}

# OpenSearch Domain
resource "aws_opensearch_domain" "main" {
  domain_name    = var.domain_name
  engine_version = "OpenSearch_${var.opensearch_version}"

  cluster_config {
    instance_type            = var.instance_type
    instance_count           = var.instance_count
    dedicated_master_enabled = var.dedicated_master_enabled
    dedicated_master_type    = var.dedicated_master_enabled ? var.master_instance_type : null
    dedicated_master_count   = var.dedicated_master_enabled ? var.master_instance_count : null
    zone_awareness_enabled   = var.instance_count > 1
    
    dynamic "zone_awareness_config" {
      for_each = var.instance_count > 1 ? [1] : []
      content {
        availability_zone_count = 2
      }
    }
  }

  ebs_options {
    ebs_enabled = var.ebs_enabled
    volume_type = var.volume_type
    volume_size = var.volume_size
  }

  vpc_options {
    subnet_ids         = var.subnet_ids
    security_group_ids = concat([aws_security_group.opensearch.id], var.security_group_ids)
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  advanced_security_options {
    enabled                        = true
    anonymous_auth_enabled         = false
    internal_user_database_enabled = true
    master_user_options {
      master_user_name     = "admin"
      master_user_password = random_password.opensearch_password.result
    }
  }

  access_policies = var.access_policies != "" ? var.access_policies : jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "*"
        }
        Action = "es:*"
        Resource = "arn:aws:es:*:*:domain/${var.domain_name}/*"
      }
    ]
  })

  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      advanced_security_options[0].master_user_options[0].master_user_password,
      access_policies
    ]
  }

  tags = merge(var.tags, {
    Name        = var.domain_name
    Environment = var.environment
  })
}

# Generate random password for OpenSearch admin user
resource "random_password" "opensearch_password" {
  length  = 16
  special = true
  
  lifecycle {
    ignore_changes = [result]
  }
}

# Store OpenSearch password in Secrets Manager
resource "aws_secretsmanager_secret" "opensearch_password" {
  name                    = "notegen-ai-api-${var.environment}-opensearch-password"
  description             = "OpenSearch admin password for ${var.environment}"
  recovery_window_in_days = 7

  lifecycle {
    prevent_destroy = true
  }

  tags = merge(var.tags, {
    Name        = "notegen-ai-api-${var.environment}-opensearch-password"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "opensearch_password" {
  secret_id = aws_secretsmanager_secret.opensearch_password.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.opensearch_password.result
  })
  
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Default access policy for OpenSearch
data "aws_iam_policy_document" "opensearch_access" {
  statement {
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
    actions   = ["es:*"]
    resources = ["arn:aws:es:*:*:domain/${var.domain_name}/*"]
    
    condition {
      test     = "IpAddress"
      variable = "aws:SourceIp"
      values   = ["10.0.0.0/16"] # Allow from VPC
    }
  }
} 