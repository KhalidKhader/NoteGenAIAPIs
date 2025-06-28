// Neo4j module main.tf 

# Security Group for Neo4j
resource "aws_security_group" "neo4j" {
  name_prefix = "notegen-ai-api-${var.environment}-neo4j-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 7474
    to_port     = 7474
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"] # HTTP interface
  }

  ingress {
    from_port   = 7687
    to_port     = 7687
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"] # Bolt protocol
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "notegen-ai-api-${var.environment}-neo4j-sg"
    Environment = var.environment
  })
}

# EFS File System for Neo4j data persistence
resource "aws_efs_file_system" "neo4j_data" {
  creation_token = "notegen-ai-api-${var.environment}-neo4j-data"
  encrypted      = true

  lifecycle {
    prevent_destroy = true
  }

  tags = merge(var.tags, {
    Name        = "notegen-ai-api-${var.environment}-neo4j-data"
    Environment = var.environment
  })
}

# EFS Mount Targets
resource "aws_efs_mount_target" "neo4j_data" {
  count           = length(var.subnet_ids)
  file_system_id  = aws_efs_file_system.neo4j_data.id
  subnet_id       = var.subnet_ids[count.index]
  security_groups = [aws_security_group.efs.id]
  
  lifecycle {
    prevent_destroy = true
  }
}

# Security Group for EFS
resource "aws_security_group" "efs" {
  name_prefix = "notegen-ai-api-${var.environment}-neo4j-efs-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.neo4j.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "notegen-ai-api-${var.environment}-neo4j-efs-sg"
    Environment = var.environment
  })
}

# Generate random password for Neo4j
resource "random_password" "neo4j_password" {
  length  = 16
  special = true
}

# Store Neo4j password in Secrets Manager
resource "aws_secretsmanager_secret" "neo4j_password" {
  name                    = "notegen-ai-api-${var.environment}-neo4j-password"
  description             = "Neo4j admin password for ${var.environment}"
  recovery_window_in_days = 7

  lifecycle {
    prevent_destroy = true
  }

  tags = merge(var.tags, {
    Name        = "notegen-ai-api-${var.environment}-neo4j-password"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "neo4j_password" {
  secret_id = aws_secretsmanager_secret.neo4j_password.id
  secret_string = jsonencode({
    username = "neo4j"
    password = random_password.neo4j_password.result
  })
  
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Backup Restoration Infrastructure
# IAM Role for backup restoration task
resource "aws_iam_role" "backup_restore_role" {
  name = "notegen-ai-api-${var.environment}-backup-restore-role"

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
    Name        = "notegen-ai-api-${var.environment}-backup-restore-role"
    Environment = var.environment
  })
}

# IAM Policy for backup restoration
resource "aws_iam_role_policy" "backup_restore_policy" {
  name = "notegen-ai-api-${var.environment}-backup-restore-policy"
  role = aws_iam_role.backup_restore_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.backup_bucket}",
          "arn:aws:s3:::${var.backup_bucket}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Role for backup restoration execution
resource "aws_iam_role" "backup_restore_execution_role" {
  name = "notegen-ai-api-${var.environment}-backup-restore-execution-role"

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
    Name        = "notegen-ai-api-${var.environment}-backup-restore-execution-role"
    Environment = var.environment
  })
}

resource "aws_iam_role_policy_attachment" "backup_restore_execution_policy" {
  role       = aws_iam_role.backup_restore_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# CloudWatch Log Group for backup restoration
resource "aws_cloudwatch_log_group" "backup_restore" {
  name              = "/ecs/notegen-ai-api-${var.environment}-backup-restore"
  retention_in_days = 7

  tags = merge(var.tags, {
    Name        = "notegen-ai-api-${var.environment}-backup-restore-logs"
    Environment = var.environment
  })
}

# ECS Task Definition for backup restoration
resource "aws_ecs_task_definition" "backup_restore" {
  family                   = "notegen-ai-api-${var.environment}-backup-restore"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.backup_restore_execution_role.arn
  task_role_arn            = aws_iam_role.backup_restore_role.arn

  volume {
    name = "neo4j-data"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.neo4j_data.id
      root_directory = "/"
    }
  }

  container_definitions = jsonencode([
    {
      name  = "backup-restore"
      image = "amazonlinux:latest"
      
      entryPoint = ["/bin/bash"]
      command = [
        "-c",
        "yum update -y && yum install -y awscli tar gzip && echo 'Starting backup restoration' && if aws s3 ls s3://${var.backup_bucket}/${var.backup_key}; then echo 'Backup found, downloading...' && aws s3 cp s3://${var.backup_bucket}/${var.backup_key} /tmp/backup.tar.gz && cd /data && tar -xzf /tmp/backup.tar.gz --strip-components=1 && rm /tmp/backup.tar.gz && echo 'Restore complete'; else echo 'No backup found, skipping'; fi"
      ]

      environment = [
        {
          name  = "AWS_DEFAULT_REGION"
          value = data.aws_region.current.name
        }
      ]

      mountPoints = [
        {
          sourceVolume  = "neo4j-data"
          containerPath = "/data"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backup_restore.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = merge(var.tags, {
    Name        = "notegen-ai-api-${var.environment}-backup-restore-task"
    Environment = var.environment
  })
}

# Backup restoration task - Fixed container issues
resource "null_resource" "restore_backup" {
  triggers = {
    backup_bucket = var.backup_bucket
    backup_key    = var.backup_key
    efs_id        = aws_efs_file_system.neo4j_data.id
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e  # Exit on any error
      
      # Set variables
      CLUSTER_NAME="${var.cluster_name}"
      TASK_DEFINITION="${aws_ecs_task_definition.backup_restore.arn}"
      REGION="${data.aws_region.current.name}"
      SUBNETS="${join(",", var.subnet_ids)}"
      SECURITY_GROUP="${aws_security_group.neo4j.id}"
      
      echo "Running backup restoration task..."
      echo "Cluster: $CLUSTER_NAME"
      echo "Task Definition: $TASK_DEFINITION"
      echo "Region: $REGION"
      
      # Check if backup file exists in S3
      echo "Checking if backup file exists..."
      if ! aws s3 ls "s3://${var.backup_bucket}/${var.backup_key}" --region "$REGION" > /dev/null 2>&1; then
        echo "Warning: Backup file s3://${var.backup_bucket}/${var.backup_key} not found. Skipping restore."
        exit 0
      fi
      
      # Run the backup restoration task
      TASK_ARN=$(aws ecs run-task \
        --cluster "$CLUSTER_NAME" \
        --task-definition "$TASK_DEFINITION" \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUP],assignPublicIp=DISABLED}" \
        --query 'tasks[0].taskArn' \
        --output text \
        --region "$REGION")
      
      if [ "$TASK_ARN" = "None" ] || [ -z "$TASK_ARN" ]; then
        echo "Failed to start backup restoration task"
        exit 1
      fi
      
      echo "Started backup restoration task: $TASK_ARN"
      echo "Waiting for task to complete..."
      
      # Wait for task to complete
      aws ecs wait tasks-stopped \
        --cluster "$CLUSTER_NAME" \
        --tasks "$TASK_ARN" \
        --region "$REGION"
      
      # Check if task completed successfully
      TASK_DETAILS=$(aws ecs describe-tasks \
        --cluster "$CLUSTER_NAME" \
        --tasks "$TASK_ARN" \
        --query 'tasks[0]' \
        --region "$REGION")
      
      EXIT_CODE=$(echo "$TASK_DETAILS" | jq -r '.containers[0].exitCode // "null"')
      STOP_REASON=$(echo "$TASK_DETAILS" | jq -r '.stoppedReason // "null"')
      
      echo "Task stopped with exit code: $EXIT_CODE"
      echo "Stop reason: $STOP_REASON"
      
      if [ "$EXIT_CODE" != "0" ] && [ "$EXIT_CODE" != "null" ]; then
        echo "Backup restoration failed with exit code: $EXIT_CODE"
        # Get task logs for debugging
        echo "Fetching task logs..."
        aws logs describe-log-streams \
          --log-group-name "${aws_cloudwatch_log_group.backup_restore.name}" \
          --region "$REGION" \
          --query 'logStreams[?starts_with(logStreamName, `ecs/backup-restore`)].[logStreamName]' \
          --output text | head -1 | xargs -I {} aws logs get-log-events \
          --log-group-name "${aws_cloudwatch_log_group.backup_restore.name}" \
          --log-stream-name {} \
          --region "$REGION" \
          --query 'events[].message' \
          --output text
        exit 1
      fi
      
      echo "Backup restoration completed successfully"
    EOT
  }

  depends_on = [
    aws_efs_mount_target.neo4j_data,
    aws_ecs_task_definition.backup_restore
  ]
}

# IAM Role for Neo4j ECS Task
resource "aws_iam_role" "neo4j_task_role" {
  name = "notegen-ai-api-${var.environment}-neo4j-task-role"

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
    Name        = "notegen-ai-api-${var.environment}-neo4j-task-role"
    Environment = var.environment
  })
}

# IAM Policy for Neo4j Task
resource "aws_iam_role_policy" "neo4j_task_policy" {
  name = "notegen-ai-api-${var.environment}-neo4j-task-policy"
  role = aws_iam_role.neo4j_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.neo4j_password.arn
        ]
      },
# S3 and SSM permissions removed - Neo4j task no longer needs backup access
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "neo4j_execution_role" {
  name = "notegen-ai-api-${var.environment}-neo4j-execution-role"

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
    Name        = "notegen-ai-api-${var.environment}-neo4j-execution-role"
    Environment = var.environment
  })
}

# Attach ECS Task Execution Role Policy
resource "aws_iam_role_policy_attachment" "neo4j_execution_role_policy" {
  role       = aws_iam_role.neo4j_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "neo4j" {
  name              = "/ecs/notegen-ai-api-${var.environment}-neo4j"
  retention_in_days = 7

  tags = merge(var.tags, {
    Name        = "notegen-ai-api-${var.environment}-neo4j-logs"
    Environment = var.environment
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "neo4j" {
  family                   = "notegen-ai-api-${var.environment}-neo4j"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.neo4j_cpu
  memory                   = var.neo4j_memory
  execution_role_arn       = aws_iam_role.neo4j_execution_role.arn
  task_role_arn            = aws_iam_role.neo4j_task_role.arn

  volume {
    name = "neo4j-data"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.neo4j_data.id
      root_directory = "/"
    }
  }

  container_definitions = jsonencode([
    {
      name  = "neo4j"
      image = var.neo4j_image
      
      portMappings = [
        {
          containerPort = 7474
          protocol      = "tcp"
        },
        {
          containerPort = 7687
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "NEO4J_AUTH"
          value = "neo4j/${random_password.neo4j_password.result}"
        },
        {
          name  = "NEO4J_PLUGINS"
          value = "[\"apoc\", \"graph-data-science\"]"
        }
      ]

      mountPoints = [
        {
          sourceVolume  = "neo4j-data"
          containerPath = "/data"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.neo4j.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command = [
          "CMD-SHELL",
          "wget --no-verbose --tries=1 --spider http://localhost:7474 || exit 1"
        ]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      essential = true
    }
  ])

  tags = merge(var.tags, {
    Name        = "notegen-ai-api-${var.environment}-neo4j-task"
    Environment = var.environment
  })
}

# ECS Service - Re-enabled now that cluster exists
resource "aws_ecs_service" "neo4j" {
  name            = "notegen-ai-api-${var.environment}-neo4j"
  cluster         = var.cluster_name
  task_definition = aws_ecs_task_definition.neo4j.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.neo4j.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.neo4j.arn
  }

  tags = merge(var.tags, {
    Name        = "notegen-ai-api-${var.environment}-neo4j-service"
    Environment = var.environment
  })

  depends_on = [
    aws_efs_mount_target.neo4j_data,
    null_resource.restore_backup
  ]
}

# Service Discovery
resource "aws_service_discovery_private_dns_namespace" "neo4j" {
  name        = "notegen-ai-api-${var.environment}.local"
  description = "Private DNS namespace for NoteGen ${var.environment}"
  vpc         = var.vpc_id

  tags = merge(var.tags, {
    Name        = "notegen-ai-api-${var.environment}-dns-namespace"
    Environment = var.environment
  })
}

resource "aws_service_discovery_service" "neo4j" {
  name = "neo4j"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.neo4j.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  tags = merge(var.tags, {
    Name        = "notegen-ai-api-${var.environment}-neo4j-discovery"
    Environment = var.environment
  })
}

# Data source for current AWS region
data "aws_region" "current" {} 