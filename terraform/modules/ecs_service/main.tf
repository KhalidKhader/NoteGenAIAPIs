// ECS service module main.tf 

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = merge(var.tags, {
    Name        = var.cluster_name
    Environment = var.environment
  })
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name_prefix = var.alb_name_override != "" ? "${var.alb_name_override}-alb-" : "${var.app_name}-${var.environment}-alb-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = var.alb_name_override != "" ? "${var.alb_name_override}-alb-sg" : "${var.app_name}-${var.environment}-alb-sg"
    Environment = var.environment
  })
}

# Security Group for ECS Service
resource "aws_security_group" "ecs_service" {
  name_prefix = "${var.app_name}-${var.environment}-ecs-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-ecs-sg"
    Environment = var.environment
  })
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = var.alb_name_override != "" ? "${var.alb_name_override}-alb" : "${var.app_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = length(var.alb_subnet_ids) > 0 ? var.alb_subnet_ids : var.subnet_ids

  enable_deletion_protection = false

  tags = merge(var.tags, {
    Name        = var.alb_name_override != "" ? "${var.alb_name_override}-alb" : "${var.app_name}-${var.environment}-alb"
    Environment = var.environment
  })
}

# ALB Target Group
resource "aws_lb_target_group" "app" {
  name        = var.alb_name_override != "" ? "${var.alb_name_override}-tg" : "${var.app_name}-${var.environment}-tg"
  port        = var.app_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = var.health_check_path
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = merge(var.tags, {
    Name        = var.alb_name_override != "" ? "${var.alb_name_override}-tg" : "${var.app_name}-${var.environment}-tg"
    Environment = var.environment
  })
}

# ALB Listener - conditional based on certificate
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  dynamic "default_action" {
    for_each = var.certificate_arn != "" ? [1] : []
    content {
      type = "redirect"
      redirect {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }

  dynamic "default_action" {
    for_each = var.certificate_arn == "" ? [1] : []
    content {
      type             = "forward"
      target_group_arn = aws_lb_target_group.app.arn
    }
  }
}

# ALB Listener (HTTPS) - conditional on certificate
resource "aws_lb_listener" "https" {
  count             = var.certificate_arn != "" ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.app_name}-${var.environment}-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-execution-role"
    Environment = var.environment
  })
}

# Attach ECS Task Execution Role Policy
resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Policy for ECS Execution Role to access secrets
resource "aws_iam_role_policy" "ecs_execution_role_secrets_policy" {
  name = "${var.app_name}-${var.environment}-execution-secrets-policy"
  role = aws_iam_role.ecs_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      # Secrets Manager permissions for core secrets
      [
        {
          Effect = "Allow"
          Action = [
            "secretsmanager:GetSecretValue"
          ]
          Resource = [
            var.neo4j_secret_arn,
            var.azure_openai_api_key_secret_arn,
            var.azure_openai_endpoint_secret_arn,
            var.azure_openai_embedding_api_key_secret_arn,
            var.azure_openai_embedding_endpoint_secret_arn,
            var.langfuse_secret_key_secret_arn,
            var.langfuse_public_key_secret_arn
          ]
        }
      ],
      # Additional secrets permissions
      length(var.secrets_arns) > 0 ? [
        {
          Effect = "Allow"
          Action = [
            "secretsmanager:GetSecretValue"
          ]
          Resource = var.secrets_arns
        }
      ] : [],
      # SSM Parameter Store permissions for all required parameters
      [
        {
          Effect = "Allow"
          Action = [
            "ssm:GetParameter",
            "ssm:GetParameters"
          ]
          Resource = [
            "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/notegen-ai-api/${var.environment}/neo4j/uri",
            "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/notegen-ai-api/${var.environment}/opensearch/endpoint",
            "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/notegen-ai-api/${var.environment}/azure-openai/endpoint",
            "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/notegen-ai-api/${var.environment}/azure-openai/embedding-endpoint",
            "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/notegen-ai-api/${var.environment}/notegen-api/base-url"
          ]
        }
      ]
    )
  })
}

# IAM Role for ECS Task
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.app_name}-${var.environment}-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-task-role"
    Environment = var.environment
  })
}

# IAM Policy for ECS Task
resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${var.app_name}-${var.environment}-task-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      # Secrets Manager permissions for core secrets
      [
        {
          Effect = "Allow"
          Action = [
            "secretsmanager:GetSecretValue"
          ]
          Resource = [
            var.neo4j_secret_arn,
            var.azure_openai_api_key_secret_arn,
            var.azure_openai_endpoint_secret_arn,
            var.azure_openai_embedding_api_key_secret_arn,
            var.azure_openai_embedding_endpoint_secret_arn,
            var.langfuse_secret_key_secret_arn,
            var.langfuse_public_key_secret_arn
          ]
        }
      ],
      # Additional secrets permissions
      length(var.secrets_arns) > 0 ? [
        {
          Effect = "Allow"
          Action = [
            "secretsmanager:GetSecretValue"
          ]
          Resource = var.secrets_arns
        }
      ] : [],
      # Parameter Store permissions for all required parameters
      length(var.parameter_arns) > 0 ? [
        {
          Effect = "Allow"
          Action = [
            "ssm:GetParameter",
            "ssm:GetParameters"
          ]
          Resource = var.parameter_arns
        }
      ] : [],
      # CloudWatch Logs permissions
      [
        {
          Effect = "Allow"
          Action = [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents"
          ]
          Resource = "*"
        }
      ],
      # OpenSearch Serverless (AOSS) permissions for collection
      [
        {
          Effect = "Allow"
          Action = [
            "aoss:APIAccessAll"
          ]
          Resource = [
            "arn:aws:aoss:${var.aws_region}:${data.aws_caller_identity.current.account_id}:collection/notegen-ai-api-transcripts-${var.environment}"
          ]
        }
      ]
    )
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.app_name}-${var.environment}"
  retention_in_days = 7

  lifecycle {
    prevent_destroy = true
  }

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-logs"
    Environment = var.environment
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.app_name}-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.app_cpu
  memory                   = var.app_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = var.app_name
      image = var.app_image

      portMappings = [
        {
          containerPort = var.app_port
          protocol      = "tcp"
        }
      ]

      # Environment variables from Parameter Store
      environment = concat(
        # Static environment variables
        [
          {
            name  = "APP_NAME"
            value = var.app_name
          },
          {
            name  = "ENVIRONMENT"
            value = var.environment
          },
          {
            name  = "LOG_LEVEL"
            value = var.log_level
          },
          {
            name  = "DEBUG"
            value = tostring(var.debug)
          },
          {
            name  = "CORS_ORIGINS"
            value = var.cors_origins
          },
          {
            name  = "OPENSEARCH_ENDPOINT"
            value = can(regex("^https?://", var.opensearch_endpoint)) ? var.opensearch_endpoint : "https://${var.opensearch_endpoint}"
          },
          {
            name  = "OPENSEARCH_INDEX"
            value = var.opensearch_index
          },
          {
            name  = "NEO4J_URI"
            value = var.neo4j_uri
          },
          {
            name  = "NEO4J_USER"
            value = var.neo4j_user
          },
          {
            name  = "NEO4J_DATABASE"
            value = var.neo4j_database
          },
          {
            name  = "NOTEGEN_API_BASE_URL"
            value = var.notegen_api_base_url
          },
          {
            name  = "AZURE_OPENAI_DEPLOYMENT_NAME"
            value = var.azure_openai_deployment_name
          },
          {
            name  = "AZURE_OPENAI_API_VERSION"
            value = var.azure_openai_api_version
          },
          {
            name  = "AZURE_OPENAI_MODEL"
            value = var.azure_openai_model
          },
          {
            name  = "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"
            value = var.azure_openai_embedding_deployment_name
          },
          {
            name  = "AZURE_OPENAI_EMBEDDING_MODEL"
            value = var.azure_openai_embedding_model
          },
          {
            name  = "LANGFUSE_HOST"
            value = var.langfuse_host
          },

        ],
        # Additional environment variables from input
        var.environment_variables
      )

      # Secrets from AWS Secrets Manager
      secrets = concat(
        # Core secrets
        [
          {
            name      = "NEO4J_PASSWORD"
            valueFrom = var.neo4j_secret_arn
          },
          {
            name      = "AZURE_OPENAI_API_KEY"
            valueFrom = var.azure_openai_api_key_secret_arn
          },
          {
            name      = "AZURE_OPENAI_ENDPOINT"
            valueFrom = var.azure_openai_endpoint_secret_arn
          },
          {
            name      = "AZURE_OPENAI_EMBEDDING_API_KEY"
            valueFrom = var.azure_openai_embedding_api_key_secret_arn
          },
          {
            name      = "AZURE_OPENAI_EMBEDDING_ENDPOINT"
            valueFrom = var.azure_openai_embedding_endpoint_secret_arn
          },
          {
            name      = "LANGFUSE_SECRET_KEY"
            valueFrom = var.langfuse_secret_key_secret_arn
          },
          {
            name      = "LANGFUSE_PUBLIC_KEY"
            valueFrom = var.langfuse_public_key_secret_arn
          }
        ],
        # Additional secrets from input
        var.additional_secrets
      )

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command = [
          "CMD-SHELL",
          "curl -f http://localhost:${var.app_port}${var.health_check_path} || exit 1"
        ]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      essential = true
    }
  ])

  lifecycle {
    ignore_changes = [
      container_definitions
    ]
  }

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-task"
    Environment = var.environment
  })
}

# ECS Service
resource "aws_ecs_service" "app" {
  name            = "${var.app_name}-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.subnet_ids
    security_groups = [aws_security_group.ecs_service.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = var.app_name
    container_port   = var.app_port
  }

  lifecycle {
    ignore_changes = [
      task_definition,
      desired_count
    ]
  }

  depends_on = [
    aws_lb_listener.http,
    aws_lb_listener.https
  ]

  tags = merge(var.tags, {
    Name        = "${var.app_name}-${var.environment}-service"
    Environment = var.environment
  })
}

# Data source for current AWS region
data "aws_region" "current" {}

# Data source for current AWS account
data "aws_caller_identity" "current" {} 