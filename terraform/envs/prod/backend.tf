// prod environment backend.tf 
terraform {
  backend "s3" {
    bucket         = "notegen-prod-tfstate"
    key            = "prod/terraform.tfstate"
    region         = "ca-central-1"
    dynamodb_table = "notegen-prod-tfstate-lock"
    encrypt        = true
  }
} 