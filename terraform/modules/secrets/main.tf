# =============================================================================
# Secrets Management for NoteGen AI APIs
# =============================================================================

# Neo4j Secrets - Plain string format for compatibility
resource "aws_secretsmanager_secret" "neo4j" {
  name        = "${var.app_name}-${var.environment}-neo4j"
  description = "Neo4j database credentials for ${var.app_name} ${var.environment}"

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-neo4j"
    Environment = var.environment
    Component   = "neo4j"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_secretsmanager_secret_version" "neo4j" {
  secret_id     = aws_secretsmanager_secret.neo4j.id
  secret_string = var.neo4j_password  # Plain string instead of JSON

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Neo4j Password Secret (separate for compatibility)
resource "aws_secretsmanager_secret" "neo4j_password" {
  name        = "${var.app_name}-${var.environment}-neo4j-password"
  description = "Neo4j password for ${var.app_name} ${var.environment}"

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-neo4j-password"
    Environment = var.environment
    Component   = "neo4j"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_secretsmanager_secret_version" "neo4j_password" {
  secret_id     = aws_secretsmanager_secret.neo4j_password.id
  secret_string = var.neo4j_password

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Azure OpenAI API Key Secret
resource "aws_secretsmanager_secret" "azure_openai_api_key" {
  name        = "${var.app_name}-${var.environment}-azure-openai-api-key"
  description = "Azure OpenAI API key for ${var.app_name} ${var.environment}"

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-azure-openai-api-key"
    Environment = var.environment
    Component   = "azure-openai"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_secretsmanager_secret_version" "azure_openai_api_key" {
  count         = var.azure_openai_api_key != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.azure_openai_api_key.id
  secret_string = var.azure_openai_api_key

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Azure OpenAI Embedding API Key Secret
resource "aws_secretsmanager_secret" "azure_openai_embedding_api_key" {
  name        = "${var.app_name}-${var.environment}-azure-openai-embedding-api-key"
  description = "Azure OpenAI Embedding API key for ${var.app_name} ${var.environment}"

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-azure-openai-embedding-api-key"
    Environment = var.environment
    Component   = "azure-openai"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_secretsmanager_secret_version" "azure_openai_embedding_api_key" {
  count         = var.azure_openai_embedding_api_key != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.azure_openai_embedding_api_key.id
  secret_string = var.azure_openai_embedding_api_key

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# LangFuse Secret Key
resource "aws_secretsmanager_secret" "langfuse_secret_key" {
  name        = "${var.app_name}-${var.environment}-langfuse-secret-key"
  description = "LangFuse secret key for ${var.app_name} ${var.environment}"

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-langfuse-secret-key"
    Environment = var.environment
    Component   = "langfuse"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_secretsmanager_secret_version" "langfuse_secret_key" {
  secret_id     = aws_secretsmanager_secret.langfuse_secret_key.id
  secret_string = var.langfuse_secret_key

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# LangFuse Public Key
resource "aws_secretsmanager_secret" "langfuse_public_key" {
  name        = "${var.app_name}-${var.environment}-langfuse-public-key"
  description = "LangFuse public key for ${var.app_name} ${var.environment}"

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-langfuse-public-key"
    Environment = var.environment
    Component   = "langfuse"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_secretsmanager_secret_version" "langfuse_public_key" {
  secret_id     = aws_secretsmanager_secret.langfuse_public_key.id
  secret_string = var.langfuse_public_key

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Azure OpenAI Endpoint Secrets (for sensitive endpoint URLs)
resource "aws_secretsmanager_secret" "azure_openai_endpoint" {
  name        = "${var.app_name}-${var.environment}-azure-openai-endpoint"
  description = "Azure OpenAI endpoint URL for ${var.app_name} ${var.environment}"

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-azure-openai-endpoint"
    Environment = var.environment
    Component   = "azure-openai"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_secretsmanager_secret_version" "azure_openai_endpoint" {
  secret_id     = aws_secretsmanager_secret.azure_openai_endpoint.id
  secret_string = var.azure_openai_endpoint

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Azure OpenAI Embedding Endpoint Secret
resource "aws_secretsmanager_secret" "azure_openai_embedding_endpoint" {
  name        = "${var.app_name}-${var.environment}-azure-openai-embedding-endpoint"
  description = "Azure OpenAI embedding endpoint URL for ${var.app_name} ${var.environment}"

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-azure-openai-embedding-endpoint"
    Environment = var.environment
    Component   = "azure-openai"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_secretsmanager_secret_version" "azure_openai_embedding_endpoint" {
  secret_id     = aws_secretsmanager_secret.azure_openai_embedding_endpoint.id
  secret_string = var.azure_openai_embedding_endpoint

  lifecycle {
    ignore_changes = [secret_string]
  }
} 