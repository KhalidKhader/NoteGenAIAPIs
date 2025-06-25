#!/bin/bash

# Terraform Safety Validation Script
# This script checks for common issues that could cause resource destruction

set -e

echo "🔍 Terraform Safety Validation"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "backend.tf" ]; then
    echo -e "${RED}❌ Error: Run this script from the terraform environment directory (e.g., envs/staging)${NC}"
    exit 1
fi

echo "📂 Current directory: $(pwd)"

# Check 1: Backend configuration
echo -e "\n1. Checking backend configuration..."
if grep -q "^terraform {" backend.tf && grep -q "backend.*s3" backend.tf; then
    echo -e "${GREEN}✅ Remote backend is configured${NC}"
else
    echo -e "${RED}❌ Remote backend is not properly configured${NC}"
    echo "   Fix: Uncomment backend configuration in backend.tf"
fi

# Check 2: Terraform format
echo -e "\n2. Checking Terraform format..."
if terraform fmt -check -recursive > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Terraform files are properly formatted${NC}"
else
    echo -e "${YELLOW}⚠️  Terraform files need formatting${NC}"
    echo "   Fix: Run 'terraform fmt -recursive'"
fi

# Check 3: Terraform validation
echo -e "\n3. Validating Terraform configuration..."
if terraform validate > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Terraform configuration is valid${NC}"
else
    echo -e "${RED}❌ Terraform configuration has errors${NC}"
    echo "   Fix: Run 'terraform validate' to see errors"
fi

# Check 4: Plan for destructive operations
echo -e "\n4. Checking for destructive operations..."
if terraform plan -detailed-exitcode > /tmp/tf-plan.out 2>&1; then
    # Plan succeeded, check for destroys
    if grep -q "destroy" /tmp/tf-plan.out; then
        echo -e "${RED}❌ Plan contains destructive operations${NC}"
        echo "   Review the plan output carefully before applying"
        grep -A 2 -B 2 "destroy" /tmp/tf-plan.out || true
    else
        echo -e "${GREEN}✅ No destructive operations detected${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Unable to generate plan (this is normal for first run)${NC}"
fi

# Check 5: Look for lifecycle rules in modules
echo -e "\n5. Checking for lifecycle protection rules..."
lifecycle_count=$(find ../../modules -name "*.tf" -exec grep -l "prevent_destroy\|ignore_changes" {} \; | wc -l)
if [ "$lifecycle_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Found lifecycle protection rules in $lifecycle_count files${NC}"
else
    echo -e "${YELLOW}⚠️  No lifecycle protection rules found${NC}"
    echo "   Consider adding lifecycle rules to critical resources"
fi

# Check 6: State file location
echo -e "\n6. Checking state file location..."
if [ -f ".terraform/terraform.tfstate" ]; then
    echo -e "${YELLOW}⚠️  Local state file detected${NC}"
    echo "   Consider migrating to remote state"
elif [ -f "terraform.tfstate" ]; then
    echo -e "${RED}❌ Local state file in current directory${NC}"
    echo "   Must migrate to remote state before production use"
else
    echo -e "${GREEN}✅ No local state files detected${NC}"
fi

# Check 7: Random passwords handling
echo -e "\n7. Checking for random password stability..."
random_password_files=$(find ../../modules -name "*.tf" -exec grep -l "random_password" {} \; 2>/dev/null | wc -l)
if [ "$random_password_files" -gt 0 ]; then
    protected_passwords=$(find ../../modules -name "*.tf" -exec grep -A 10 "random_password" {} \; | grep -c "ignore_changes.*result" || echo "0")
    if [ "$protected_passwords" -gt 0 ]; then
        echo -e "${GREEN}✅ Random passwords are protected from regeneration${NC}"
    else
        echo -e "${YELLOW}⚠️  Random passwords may regenerate on each apply${NC}"
        echo "   Add 'ignore_changes = [result]' to random_password resources"
    fi
else
    echo -e "${GREEN}✅ No random passwords detected${NC}"
fi

# Check 8: Secrets Manager protection
echo -e "\n8. Checking Secrets Manager protection..."
secrets_files=$(find ../../modules -name "*.tf" -exec grep -l "aws_secretsmanager_secret" {} \; 2>/dev/null | wc -l)
if [ "$secrets_files" -gt 0 ]; then
    protected_secrets=$(find ../../modules -name "*.tf" -exec grep -A 10 "aws_secretsmanager_secret" {} \; | grep -c "prevent_destroy" || echo "0")
    if [ "$protected_secrets" -gt 0 ]; then
        echo -e "${GREEN}✅ Secrets Manager secrets are protected${NC}"
    else
        echo -e "${YELLOW}⚠️  Secrets Manager secrets may not be protected${NC}"
        echo "   Add 'prevent_destroy = true' to secrets"
    fi
else
    echo -e "${GREEN}✅ No Secrets Manager resources detected${NC}"
fi

# Summary
echo -e "\n🏁 Validation Summary"
echo "====================="
echo "Review the output above for any issues marked with ❌ or ⚠️"
echo "Always run 'terraform plan' before 'terraform apply'"
echo "Never apply a plan that shows unexpected destructive operations"

# Clean up
rm -f /tmp/tf-plan.out

echo -e "\n${GREEN}✅ Safety validation complete${NC}" 