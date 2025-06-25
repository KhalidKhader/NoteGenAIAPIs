// staging environment main.tf

# ECR Module
module "ecr" {
  source = "../../modules/ecr"

  environment     = var.environment
  repository_name = "notegen-ai-api"

  # Allow current AWS account to push/pull images
  allowed_principals = [data.aws_caller_identity.current.arn]

  tags = {
    Project = "notegen-ai"
  }
}

# Secrets Module
module "secrets" {
  source = "../../modules/secrets"

  environment = var.environment
  app_name    = "notegen-ai-api"

  # Neo4j secrets
  neo4j_password = var.neo4j_password

  # Azure OpenAI secrets
  azure_openai_api_key            = var.azure_openai_api_key
  azure_openai_endpoint           = var.azure_openai_endpoint
  azure_openai_embedding_api_key  = var.azure_openai_embedding_api_key
  azure_openai_embedding_endpoint = var.azure_openai_embedding_endpoint

  # LangFuse secrets
  langfuse_secret_key = var.langfuse_secret_key
  langfuse_public_key = var.langfuse_public_key

  tags = {
    Project = "notegen-ai"
  }
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  availability_zones   = var.availability_zones
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.20.0/24"]

  tags = {
    Project = "notegen-ai"
  }
}

# OpenSearch Module
module "opensearch" {
  source = "../../modules/opensearch"

  environment    = var.environment
  domain_name    = "notegenai-${var.environment}-search"
  instance_type  = var.opensearch_instance_type
  instance_count = var.opensearch_instance_count
  volume_size    = var.opensearch_volume_size

  vpc_id     = module.vpc.vpc_id
  subnet_ids = [module.vpc.private_subnet_ids[0]] # Use only first subnet for single instance

  tags = {
    Project = "notegen-ai"
  }
}

# Neo4j Module
module "neo4j" {
  source = "../../modules/neo4j"

  environment  = var.environment
  cluster_name = "notegen-ai-api-${var.environment}-cluster"
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.private_subnet_ids

  neo4j_cpu    = var.neo4j_cpu
  neo4j_memory = var.neo4j_memory

  tags = {
    Project = "notegen-ai"
  }

  depends_on = [module.vpc]
}

# Parameters Module - Creates SSM parameters from Terraform outputs
module "parameters" {
  source = "../../modules/parameters"

  environment = var.environment

  # Infrastructure endpoints from Terraform outputs
  neo4j_bolt_uri      = module.neo4j.neo4j_bolt_uri
  opensearch_endpoint = module.opensearch.domain_endpoint

  # Azure OpenAI endpoints from variables (these are managed externally)
  azure_openai_endpoint           = var.azure_openai_endpoint
  azure_openai_embedding_endpoint = var.azure_openai_embedding_endpoint

  # NoteGen API base URL (managed by other service's CI/CD)
  notegen_api_base_url = var.notegen_api_base_url

  tags = {
    Project = "notegen-ai"
  }

  depends_on = [module.neo4j, module.opensearch]
}

# ECS Service Module
module "ecs_service" {
  source = "../../modules/ecs_service"

  environment  = var.environment
  app_name     = "notegen-ai-api"
  cluster_name = "notegen-ai-api-${var.environment}-cluster"
  vpc_id       = module.vpc.vpc_id
  subnet_ids     = module.vpc.private_subnet_ids # ECS tasks should be in private subnets
  alb_subnet_ids = module.vpc.public_subnet_ids  # ALB should be in public subnets

  app_image       = var.app_image != "" ? var.app_image : module.ecr.repository_uri_with_tag
  app_cpu         = var.app_cpu
  app_memory      = var.app_memory
  desired_count   = var.desired_count
  certificate_arn = var.certificate_arn

  # Application configuration
  log_level    = var.log_level
  debug        = var.debug
  cors_origins = var.cors_origins

  # OpenSearch configuration
  opensearch_endpoint = module.opensearch.domain_endpoint
  opensearch_index    = var.opensearch_index

  # Neo4j configuration
  neo4j_uri      = module.neo4j.neo4j_bolt_uri
  neo4j_user     = var.neo4j_user
  neo4j_database = var.neo4j_database

  # NoteGen API configuration
  notegen_api_base_url = var.notegen_api_base_url

  # Secret ARNs
  neo4j_secret_arn        = module.secrets.neo4j_secret_arn
  azure_openai_secret_arn = module.secrets.azure_openai_secret_arn
  langfuse_secret_arn     = module.secrets.langfuse_secret_arn

  # Grant access to OpenSearch secret initially
  secrets_arns = [
    module.opensearch.password_secret_arn
  ]

  tags = {
    Project = "notegen-ai"
  }

  depends_on = [module.vpc, module.secrets, module.opensearch, module.neo4j, module.parameters]
}

# =============================================================================
# GitHub OIDC Module
# =============================================================================

module "github_oidc" {
  source = "../../modules/github_oidc"

  app_name               = "notegen-ai-api"
  environment            = var.environment
  github_repository      = var.github_repository
  ecr_repository_arn     = module.ecr.repository_arn
  ecs_cluster_name       = module.ecs_service.cluster_name
  ecs_service_name       = "notegen-ai-api-${var.environment}"
  ecs_execution_role_arn = module.ecs_service.execution_role_arn
  ecs_task_role_arn      = module.ecs_service.task_role_arn
  create_prod_role       = false

  tags = {
    Project = "notegen-ai"
  }

  depends_on = [module.ecs_service]
} 