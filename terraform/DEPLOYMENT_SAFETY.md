# Terraform Deployment Safety Guide

## CRITICAL: Preventing Resource Destruction

This guide ensures your Terraform deployments are **idempotent** and won't destroy/recreate resources on subsequent runs.

## 🔒 Safety Measures Implemented

### 1. Remote State Backend
- **ENABLED**: S3 backend with DynamoDB locking
- **Location**: `notegen-staging-tfstate` bucket
- **Locking**: DynamoDB table for state locking
- **Encryption**: State files are encrypted at rest

### 2. Lifecycle Rules Applied

#### Critical Resources with `prevent_destroy`:
- VPC and Internet Gateway
- Subnets (public/private) and NAT Gateway
- EFS file systems (Neo4j data)
- EFS mount targets
- OpenSearch domain
- Secrets Manager secrets
- CloudWatch log groups

#### Resources with `ignore_changes`:
- Random passwords (`result` attribute)
- Secret versions (`secret_string` attribute)  
- OpenSearch master password and access policies
- ECS task definitions (`container_definitions`)
- ECS services (`task_definition`, `desired_count`)

### 3. Password/Secret Management
- Random passwords are generated once and then ignored
- Secrets Manager versions ignore changes to prevent regeneration
- Database credentials are stable across deployments

## 🚀 Safe Deployment Process

### Initial Setup (One-time)
```bash
# 1. Create remote state infrastructure
cd terraform/envs/staging
terraform init
terraform apply -target=aws_s3_bucket.tfstate -target=aws_dynamodb_table.tfstate_lock

# 2. Migrate to remote state (backend is now uncommented)
terraform init  # Will prompt to migrate state

# 3. Deploy infrastructure
terraform plan    # Review changes
terraform apply   # Deploy
```

### Subsequent Deployments
```bash
cd terraform/envs/staging

# Always check plan first
terraform plan

# Look for these SAFE operations:
# ✅ Plan: X to add, Y to change, 0 to destroy
# ✅ ~ (modify in-place)
# ✅ + (create)

# DANGER SIGNS - STOP if you see:
# ❌ -/+ (destroy and recreate)
# ❌ - (destroy)
# ❌ Force replacement indicators

terraform apply
```

## 🔍 Pre-Deployment Checklist

Before running `terraform apply`, verify:

- [ ] `terraform plan` shows **0 to destroy**
- [ ] No `-/+` (replace) operations for critical resources
- [ ] State is stored remotely (not locally)
- [ ] Changes are expected and documented
- [ ] Backup strategy is in place

## 🚨 Emergency Procedures

### If Terraform Wants to Destroy Resources:

1. **STOP** - Don't run `terraform apply`
2. **Investigate** the root cause:
   ```bash
   terraform plan -detailed-exitcode
   terraform show
   ```
3. **Common fixes**:
   - Check for configuration drift
   - Verify variable values haven't changed unexpectedly
   - Use `terraform import` for resources created outside Terraform
   - Add `ignore_changes` for computed attributes

### State Recovery:
```bash
# List state resources
terraform state list

# Show specific resource
terraform state show <resource_name>

# Import existing resource
terraform import <resource_type>.<name> <resource_id>
```

## 📋 Module-Specific Protections

### VPC Module
- All network resources protected from destruction
- Elastic IPs and NAT Gateways have lifecycle protection

### OpenSearch Module  
- Domain protected from destruction
- Passwords ignore regeneration
- Access policies ignore drift

### Neo4j Module
- EFS storage protected from destruction
- Mount targets protected
- Passwords stable across deployments

### ECS Service Module
- Log groups protected from destruction
- Task definitions ignore container changes
- Services ignore task definition updates for blue/green deployments

## 🔧 Maintenance Commands

```bash
# Check state integrity
terraform validate
terraform fmt -check -recursive

# Refresh state without changes
terraform refresh

# Show current state
terraform show

# Plan with specific target
terraform plan -target=module.vpc

# Force unlock if state is locked
terraform force-unlock <lock_id>
```

## 📊 Monitoring Deployments

Monitor these metrics:
- State file size and version
- Resource drift detection
- Failed apply operations
- State lock duration

## 🆘 Support Contacts

If you encounter issues:
1. Check this guide first
2. Review Terraform documentation
3. Contact DevOps team with:
   - Error messages
   - Plan output
   - State backup location 