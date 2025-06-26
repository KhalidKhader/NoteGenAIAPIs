# OpenSearch Fix Commands:

# 1. Reset the master user password
aws opensearch update-domain-config --domain-name notegenai-staging-search --advanced-security-options='AdvancedSecurityEnabled=true,InternalUserDatabaseEnabled=true,MasterUserOptions={MasterUserName=admin,MasterUserPassword=NewSecurePassword123!}' --region ca-central-1 --profile notegen

# 2. Or create the user via OpenSearch API (after domain is accessible)
curl -X PUT "https://vpc-notegenai-staging-search-hrrjaqryo42zvlg33vivxtubfy.ca-central-1.es.amazonaws.com/_plugins/_security/api/internalusers/admin" -H "Content-Type: application/json" -d '{"password": "YourNewPassword", "roles": ["all_access"]}'
