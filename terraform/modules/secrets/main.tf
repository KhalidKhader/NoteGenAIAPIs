# =============================================================================
# Secrets Management for NoteGen AI APIs
# =============================================================================

# Neo4j Secrets
resource "aws_secretsmanager_secret" "neo4j" {
  name        = "${var.app_name}-${var.environment}-neo4j"
  description = "Neo4j database credentials for ${var.app_name} ${var.environment}"

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-neo4j"
    Environment = var.environment
    Component   = "neo4j"
  })
}

resource "aws_secretsmanager_secret_version" "neo4j" {
  secret_id     = aws_secretsmanager_secret.neo4j.id
  secret_string = jsonencode({
    password = var.neo4j_password
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Azure OpenAI Secrets
resource "aws_secretsmanager_secret" "azure_openai" {
  name        = "${var.app_name}-${var.environment}-azure-openai"
  description = "Azure OpenAI API credentials for ${var.app_name} ${var.environment}"

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-azure-openai"
    Environment = var.environment
    Component   = "azure-openai"
  })
}

resource "aws_secretsmanager_secret_version" "azure_openai" {
  secret_id     = aws_secretsmanager_secret.azure_openai.id
  secret_string = jsonencode({
    api_key              = var.azure_openai_api_key
    embedding_api_key    = var.azure_openai_embedding_api_key
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# LangFuse Secrets
resource "aws_secretsmanager_secret" "langfuse" {
  name        = "${var.app_name}-${var.environment}-langfuse"
  description = "LangFuse observability credentials for ${var.app_name} ${var.environment}"

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-langfuse"
    Environment = var.environment
    Component   = "langfuse"
  })
}

resource "aws_secretsmanager_secret_version" "langfuse" {
  secret_id     = aws_secretsmanager_secret.langfuse.id
  secret_string = jsonencode({
    secret_key = var.langfuse_secret_key
    public_key = var.langfuse_public_key
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
} 