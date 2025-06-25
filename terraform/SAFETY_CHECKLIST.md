# 🛡️ Terraform Safety Checklist

## ✅ Pre-Deployment Checklist

**BEFORE running `terraform apply`, ensure:**

- [ ] Remote state backend is active (S3 + DynamoDB)
- [ ] Run `terraform plan` first - review ALL changes
- [ ] Plan shows **`0 to destroy`** for existing infrastructure
- [ ] No unexpected `-/+` (replace) operations
- [ ] Random passwords won't regenerate
- [ ] Critical resources have `prevent_destroy` lifecycle rules

## 🚨 DANGER SIGNS - STOP if you see:

- ❌ `Plan: X to add, Y to change, Z to destroy` where Z > 0
- ❌ `-/+` operations on existing critical resources
- ❌ `random_password` resources without `ignore_changes`
- ❌ Local state files (terraform.tfstate in current directory)

## 🔧 Quick Validation

```bash
# Run from terraform/envs/staging/
../../validate-safety.sh

# Manual checks
terraform validate
terraform fmt -check -recursive
terraform plan | grep -E "(destroy|replace)"
```

## 🔒 Critical Resources Protected

- ✅ VPC, subnets, NAT gateway, Internet gateway
- ✅ EFS file systems and mount targets
- ✅ OpenSearch domains
- ✅ Secrets Manager secrets
- ✅ CloudWatch log groups
- ✅ Random passwords (stable generation)

## 🆘 Emergency Commands

```bash
# If state is corrupted
terraform state list
terraform state show <resource>

# If resources exist but not in state
terraform import <resource_type>.<name> <aws_resource_id>

# If state is locked
terraform force-unlock <lock_id>

# Targeted operations (safer)
terraform plan -target=module.vpc
terraform apply -target=module.vpc
```

## 📞 When to Seek Help

Contact DevOps if:
- Plan shows unexpected destructions
- Resources created outside Terraform need importing
- State file corruption or locking issues
- Need to remove lifecycle protection temporarily

---
**Remember: Better safe than sorry! Always plan first, never skip the safety checks.** 