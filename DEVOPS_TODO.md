# DevOps TODO List - NoteGen AI APIs

## 🚨 **CRITICAL - System Down Issues (Fix Immediately)**

### ✅ **COMPLETED INFRASTRUCTURE**
- [x] **OpenSearch Authentication (403 Error)** - Fixed secret structure to follow convention
- [x] **Neo4j Authentication (Missing Credentials)** - Fixed secret ARN reference 
- [x] **Terraform Secret Convention** - Updated to use individual secrets vs JSON extraction
- [x] **IAM Permissions** - Updated to access new OpenSearch secrets
- [x] **OpenSearch Username Secret** - Created and available

### 🔧 **READY TO DEPLOY - GitHub Actions Required**
- [ ] **Deploy Application Code Changes** - Commit/push OpenSearch auth changes
- [ ] **Update GitHub Actions** - Add new OpenSearch secrets to task definition
- [ ] **Trigger GitHub Actions Deployment** - Create new task definition version
- [ ] **Verify New Task Starts Successfully** - Monitor ECS logs

**Current Issue**: ECS tasks using old task definition (:11) without OpenSearch credentials
**Root Cause**: Task definitions managed by GitHub CI/CD, not terraform
**Solution**: Deploy application code to trigger new task definition creation

### 📋 **GitHub Actions Changes Needed**

The CI/CD pipeline needs to include these secrets in the task definition:
```yaml
# Add to GitHub Actions ECS task definition
secrets:
  - name: OPENSEARCH_USERNAME
    valueFrom: arn:aws:secretsmanager:ca-central-1:225989351675:secret:notegen-ai-api-staging-opensearch-username-Qp7bYY
  - name: OPENSEARCH_PASSWORD  
    valueFrom: arn:aws:secretsmanager:ca-central-1:225989351675:secret:notegen-ai-api-staging-opensearch-password-F4UaYe
  - name: NEO4J_PASSWORD
    valueFrom: arn:aws:secretsmanager:ca-central-1:225989351675:secret:notegen-ai-api-staging-neo4j-password-o4xkzI
```

---

## 🔐 **SECURITY IMPROVEMENTS (Coordinate with Dev Team)**

### **High Priority - OpenSearch Security**
- [ ] **Create Application-Specific OpenSearch User**
  - **Current**: Using admin user (security risk)
  - **Target**: Dedicated app user with limited permissions
  - **Benefits**: Principle of least privilege, better audit trail
  - **Coordinate with**: Dev team for user creation and permission scoping

### **Medium Priority - General Security**  
- [ ] **Rotate Admin Passwords** - Change from generated defaults
- [ ] **Enable MFA for Admin Access** - Add multi-factor authentication
- [ ] **Review IAM Policies** - Ensure minimal necessary permissions
- [ ] **Enable CloudTrail** - Full audit logging for compliance

---

## 📊 **MONITORING & ALERTING (Medium Priority)**

### **Application Health**
- [ ] **Enhanced Health Checks** - Include database connectivity
- [ ] **Custom Metrics** - OpenSearch/Neo4j connection status  
- [ ] **Performance Monitoring** - Response time and error rate alerts
- [ ] **Resource Monitoring** - Memory/CPU usage thresholds

### **Infrastructure Health**  
- [ ] **ECS Service Monitoring** - Task failure alerts
- [ ] **Load Balancer Health** - Target group health monitoring
- [ ] **Database Monitoring** - OpenSearch/Neo4j availability alerts
- [ ] **Secret Rotation Alerts** - Expiration notifications

---

## 🛠️ **INFRASTRUCTURE IMPROVEMENTS (Low Priority)**

### **Performance Optimization**
- [ ] **ECS Auto Scaling** - Automatic scaling based on load
- [ ] **Database Performance** - Optimize OpenSearch/Neo4j configurations
- [ ] **CDN Implementation** - CloudFront for static assets
- [ ] **Connection Pooling** - Optimize database connections

### **Reliability Improvements**
- [ ] **Multi-AZ Deployment** - High availability setup
- [ ] **Backup Strategy** - Automated backup and recovery procedures  
- [ ] **Disaster Recovery** - Cross-region failover capability
- [ ] **Blue-Green Deployment** - Zero-downtime deployment strategy

---

## 🎯 **LONG-TERM GOALS**

### **Production Readiness**
- [ ] **Load Testing** - Validate system under expected load
- [ ] **Security Audit** - Third-party security assessment
- [ ] **Compliance Review** - HIPAA/healthcare compliance validation
- [ ] **Documentation** - Complete operational runbooks

### **Operational Excellence**
- [ ] **Infrastructure as Code** - Complete terraform coverage
- [ ] **GitOps Workflow** - Automated infrastructure deployments
- [ ] **Observability Platform** - Centralized logging and monitoring
- [ ] **Cost Optimization** - Resource usage analysis and optimization

---

## ⚡ **IMMEDIATE NEXT STEPS**

1. **Deploy Application Code** → Trigger GitHub Actions
2. **Monitor New Task Deployment** → Verify authentication fixes  
3. **Test System Functionality** → Confirm OpenSearch/Neo4j connectivity
4. **Update Monitoring** → Add alerts for new deployment

**Target Resolution**: Within 30 minutes of GitHub Actions deployment

---

## 📝 **DOCUMENTATION**

### **Runbooks**
- [ ] **Create Incident Response Runbooks**
  - OpenSearch authentication issues
  - Neo4j connection problems  
  - ECS task failure troubleshooting
  - Secret rotation procedures

### **Architecture Documentation**
- [ ] **Update Infrastructure Diagrams**
  - Document current 3-tier RAG architecture
  - Show authentication flows
  - Network topology and security groups

---

## 🧪 **TESTING & VALIDATION**

### **Load Testing**
- [ ] **Performance Baselines**
  - Test OpenSearch under medical conversation load
  - Validate Neo4j SNOMED query performance
  - Establish SLA baselines for response times

### **Disaster Recovery**
- [ ] **Backup & Recovery Testing**
  - Test EFS backup/restore for Neo4j data
  - Validate OpenSearch snapshot/restore
  - Document RTO/RPO for medical data

---

## 🎯 **PRODUCTION READINESS**

### **Security Compliance**
- [ ] **HIPAA/PIPEDA Compliance Review**
  - Audit all data flows for PHI handling
  - Validate encryption at rest and in transit
  - Review access logs and audit trails

### **Scalability Planning**
- [ ] **Auto-Scaling Configuration**
  - ECS service auto-scaling based on CPU/memory
  - OpenSearch cluster scaling policies
  - Cost optimization for development vs production

---

## 📅 **TIMELINE RECOMMENDATIONS**

| Priority | Item | Timeline | Dependencies |
|----------|------|----------|--------------|
| P0 | Deploy current terraform fixes | Immediate | None |
| P1 | OpenSearch app user creation | 1-2 weeks | Coordinate with dev team |
| P2 | Monitoring & alerting setup | 2-3 weeks | System stability |
| P3 | Security compliance review | 1 month | Legal/compliance team |
| P4 | Production scaling preparation | 2 months | Load testing results |

---

## 🤝 **COORDINATION NEEDED**

### **With Development Team**
- **OpenSearch User Permissions**: Test app functionality with restricted user
- **Health Check Enhancement**: Update endpoint to include dependency checks
- **Error Handling**: Improve application retry logic for transient failures

### **With Security/Compliance**
- **Data Classification**: Review PHI handling in OpenSearch/Neo4j
- **Access Audit**: Validate who has access to production credentials
- **Pen Testing**: Schedule security assessment of infrastructure

---

*Last Updated: 2025-06-25*
*Next Review: After deployment of current fixes* 