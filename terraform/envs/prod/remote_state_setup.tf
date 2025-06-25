# Remote State Setup for Production Environment
# 
# IMPORTANT: Run this file FIRST and SEPARATELY to create the S3 bucket and DynamoDB table
# for storing Terraform state before running the main Terraform configuration.
#
# Commands:
# 1. terraform init
# 2. terraform apply -target=aws_s3_bucket.tfstate -target=aws_dynamodb_table.tfstate_lock
# 3. Uncomment the backend configuration in backend.tf
# 4. terraform init (to migrate state to S3)

resource "aws_s3_bucket" "tfstate" {
  bucket = "notegen-prod-tfstate"
  tags = {
    Name        = "notegen-prod-tfstate"
    Environment = "prod"
    Project     = "notegen-ai"
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "tfstate_lock" {
  name         = "notegen-prod-tfstate-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
  
  tags = {
    Name        = "notegen-prod-tfstate-lock"
    Environment = "prod"
    Project     = "notegen-ai"
  }
} 