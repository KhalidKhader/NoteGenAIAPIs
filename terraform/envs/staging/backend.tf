// staging environment backend.tf 

# Uncomment and update this block after running remote_state_setup.tf to create the S3 bucket and DynamoDB table
terraform {
  backend "s3" {
    bucket         = "notegen-staging-tfstate"
    key            = "staging/terraform.tfstate"
    region         = "ca-central-1"
    dynamodb_table = "notegen-staging-tfstate-lock"
    encrypt        = true
  }
} 