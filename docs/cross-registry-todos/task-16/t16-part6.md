<!-- file: docs/cross-registry-todos/task-16/t16-part6.md -->
<!-- version: 1.0.0 -->
<!-- guid: t16-deployment-automation-part6-c6d7e8f9-g0h1 -->
<!-- last-edited: 2026-01-19 -->

# Task 16 Part 6: Deployment Best Practices and Completion Checklist

## Deployment Best Practices

### Zero-Downtime Deployment Strategy

````markdown
# Zero-Downtime Deployment Checklist

## Pre-Deployment

1. **Health Checks Configured**
   - Liveness probe monitors application health
   - Readiness probe ensures pod ready for traffic
   - Startup probe for slow-starting applications

2. **Resource Limits Set**
   - CPU/memory requests prevent resource starvation
   - CPU/memory limits prevent resource exhaustion
   - Realistic values based on load testing

3. **Rolling Update Configuration**
   - `maxSurge`: Extra pods during rollout (25%)
   - `maxUnavailable`: 0 to ensure capacity
   - `minReadySeconds`: Time before pod considered available

4. **PodDisruptionBudget Created**
   - Minimum available replicas: N-1 or 50%
   - Protects against voluntary disruptions
   - Allows maintenance without downtime

## During Deployment

1. **Gradual Rollout**
   ```yaml
   strategy:
     type: RollingUpdate
     rollingUpdate:
       maxSurge: 25%
       maxUnavailable: 0
   ```
````

2. **Monitor Key Metrics**
   - Request rate
   - Error rate
   - Latency (p50, p95, p99)
   - Resource utilization

3. **Automated Rollback Triggers**
   - Error rate >5% for 5 minutes
   - P99 latency >2x baseline
   - Health check failures >20%

## Post-Deployment

1. **Smoke Tests**
   - Critical endpoints responding
   - Database connectivity verified
   - External integrations working

2. **Monitoring Period**
   - Watch for 30 minutes minimum
   - Monitor error logs
   - Track user reports

3. **Rollback Plan Ready**
   - Previous version images available
   - Rollback command documented
   - On-call team notified

````

### Deployment Rollback Strategy

```markdown
# Rollback Decision Matrix

## Automatic Rollback Triggers

| Metric         | Threshold        | Action        | Severity |
| -------------- | ---------------- | ------------- | -------- |
| Error rate     | >5% for 5min     | Auto rollback | Critical |
| P99 latency    | >2000ms for 5min | Auto rollback | Critical |
| Memory usage   | >95% for 2min    | Auto rollback | Critical |
| Pod crash loop | >3 restarts      | Auto rollback | Critical |
| Health checks  | >20% failing     | Manual review | High     |
| Traffic drop   | >50% decrease    | Manual review | High     |

## Manual Rollback Scenarios

### Immediate Rollback (No Questions)
- Data corruption detected
- Security vulnerability exploited
- Complete service outage
- Database migrations failed

### Evaluate Before Rollback
- Isolated feature issues
- Performance degradation <20%
- Non-critical bugs
- UI/UX issues

### No Rollback Needed
- Cosmetic issues
- Minor performance improvements possible
- Feature flags can disable problematic features
- Issues can be hot-fixed quickly
````

### Deployment Runbook

````markdown
# Deployment Runbook: ubuntu-autoinstall-agent

## Pre-Deployment Checklist

- [ ] All tests passing in CI
- [ ] Code review approved
- [ ] Security scan passed
- [ ] Performance benchmarks within thresholds
- [ ] Database migrations reviewed (if applicable)
- [ ] Feature flags configured
- [ ] On-call team notified
- [ ] Rollback plan documented
- [ ] Change management ticket created

## Deployment Steps

### Step 1: Deploy to Development

```bash
# Update image tag
kubectl set image deployment/ubuntu-autoinstall-agent \
  ubuntu-autoinstall-agent=ghcr.io/jdfalk/ubuntu-autoinstall-agent:v1.1.0 \
  -n ubuntu-autoinstall-dev

# Wait for rollout
kubectl rollout status deployment/ubuntu-autoinstall-agent \
  -n ubuntu-autoinstall-dev
```
````

**Verify**:

- [ ] Health endpoint responding
- [ ] Logs show no errors
- [ ] Smoke tests passing

### Step 2: Deploy to Staging

```bash
# Update ArgoCD application
argocd app set ubuntu-autoinstall-staging \
  --revision v1.1.0

# Sync application
argocd app sync ubuntu-autoinstall-staging

# Wait for sync
argocd app wait ubuntu-autoinstall-staging
```

**Verify**:

- [ ] Integration tests passing
- [ ] Performance tests within bounds
- [ ] No anomalies in metrics

### Step 3: Deploy to Production (Canary)

```bash
# Start canary deployment
kubectl argo rollouts set image ubuntu-autoinstall-agent \
  ubuntu-autoinstall-agent=ghcr.io/jdfalk/ubuntu-autoinstall-agent:v1.1.0 \
  -n ubuntu-autoinstall-production

# Monitor canary progress
kubectl argo rollouts status ubuntu-autoinstall-agent \
  -n ubuntu-autoinstall-production --watch
```

**Monitoring during canary** (30-60 minutes):

- [ ] Error rate <0.1%
- [ ] P95 latency <500ms
- [ ] No increase in error logs
- [ ] Canary analysis passing
- [ ] No user complaints

### Step 4: Promote to Production

```bash
# Promote canary
kubectl argo rollouts promote ubuntu-autoinstall-agent \
  -n ubuntu-autoinstall-production

# Wait for full rollout
kubectl argo rollouts status ubuntu-autoinstall-agent \
  -n ubuntu-autoinstall-production
```

**Final verification**:

- [ ] All pods running new version
- [ ] Health checks passing
- [ ] Metrics stable
- [ ] No errors in logs

## Rollback Procedure

### Automatic Rollback (Triggered by Failure)

```bash
# Rollback will happen automatically
# Monitor rollback progress
kubectl argo rollouts status ubuntu-autoinstall-agent \
  -n ubuntu-autoinstall-production
```

### Manual Rollback

```bash
# Abort current rollout
kubectl argo rollouts abort ubuntu-autoinstall-agent \
  -n ubuntu-autoinstall-production

# Rollback to previous version
kubectl argo rollouts undo ubuntu-autoinstall-agent \
  -n ubuntu-autoinstall-production

# Verify rollback
kubectl argo rollouts status ubuntu-autoinstall-agent \
  -n ubuntu-autoinstall-production
```

## Post-Deployment

- [ ] Monitor for 30 minutes after deployment
- [ ] Update change management ticket
- [ ] Document any issues encountered
- [ ] Update runbook if needed
- [ ] Notify stakeholders of completion

## Emergency Contacts

- **On-Call Engineer**: PagerDuty
- **Team Lead**: Slack #team-infrastructure
- **Database Admin**: Slack #team-database (if migration issues)
- **Security Team**: Slack #team-security (if security issues)

````

## Disaster Recovery

### Backup and Restore Strategy

```yaml
# file: k8s/backup/velero-schedule.yaml
# version: 1.0.0
# guid: velero-backup-schedule

apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: ubuntu-autoinstall-daily
  namespace: velero
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  template:
    includedNamespaces:
    - ubuntu-autoinstall-production
    - ubuntu-autoinstall-staging

    includedResources:
    - deployments
    - services
    - configmaps
    - secrets
    - persistentvolumeclaims
    - persistentvolumes

    excludedResources:
    - events
    - pods

    storageLocation: default
    volumeSnapshotLocations:
    - default

    ttl: 720h  # 30 days

    hooks:
      resources:
      - name: postgres-backup
        includedNamespaces:
        - ubuntu-autoinstall-production
        labelSelector:
          matchLabels:
            app: postgres
        pre:
        - exec:
            container: postgres
            command:
            - /bin/bash
            - -c
            - pg_dump -U $POSTGRES_USER $POSTGRES_DB > /tmp/backup.sql
            onError: Fail
            timeout: 5m
````

### Disaster Recovery Runbook

````markdown
# Disaster Recovery Runbook

## Scenario 1: Complete Cluster Failure

### Recovery Steps

1. **Provision New Cluster**
   ```bash
   # Using Terraform
   cd terraform/
   terraform init
   terraform apply -var-file=production.tfvars
   ```
````

2. **Install Velero**

   ```bash
   velero install \
     --provider aws \
     --bucket ubuntu-autoinstall-backups \
     --backup-location-config region=us-east-1 \
     --snapshot-location-config region=us-east-1 \
     --secret-file ./credentials-velero
   ```

3. **Restore from Backup**

   ```bash
   # List available backups
   velero backup get

   # Restore latest backup
   velero restore create --from-backup ubuntu-autoinstall-daily-20240101

   # Monitor restore
   velero restore describe ubuntu-autoinstall-daily-20240101 --details
   ```

4. **Verify Application**

   ```bash
   # Check pods
   kubectl get pods -n ubuntu-autoinstall-production

   # Check services
   kubectl get svc -n ubuntu-autoinstall-production

   # Test health endpoint
   curl https://ubuntu-autoinstall.example.com/health
   ```

## Scenario 2: Data Corruption

### Recovery Steps

1. **Identify Corruption Scope**

   ```bash
   # Check database logs
   kubectl logs -n ubuntu-autoinstall-production postgres-0 --tail=100

   # Check application logs
   kubectl logs -n ubuntu-autoinstall-production -l app=ubuntu-autoinstall-agent
   ```

2. **Stop Writes**

   ```bash
   # Scale deployment to 0
   kubectl scale deployment ubuntu-autoinstall-agent \
     --replicas=0 \
     -n ubuntu-autoinstall-production
   ```

3. **Restore Database**

   ```bash
   # Restore from latest backup
   kubectl exec -n ubuntu-autoinstall-production postgres-0 -- \
     psql -U postgres -d ubuntu_autoinstall < /tmp/backup.sql
   ```

4. **Restart Application**
   ```bash
   # Scale back up
   kubectl scale deployment ubuntu-autoinstall-agent \
     --replicas=5 \
     -n ubuntu-autoinstall-production
   ```

## Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)

| Component        | RTO     | RPO      | Strategy                        |
| ---------------- | ------- | -------- | ------------------------------- |
| Application      | 15 min  | 0        | Rolling deployment rollback     |
| Database         | 30 min  | 24 hours | Daily backups with PITR         |
| Configuration    | 5 min   | 1 hour   | Git-based, can redeploy anytime |
| Persistent Data  | 1 hour  | 24 hours | Volume snapshots daily          |
| Complete Cluster | 4 hours | 24 hours | IaC + Velero restore            |

````

## Multi-Region Deployment

```yaml
# file: k8s/multi-region/federation.yaml
# version: 1.0.0
# guid: multi-region-federation

apiVersion: types.kubefed.io/v1beta1
kind: FederatedDeployment
metadata:
  name: ubuntu-autoinstall-agent
  namespace: ubuntu-autoinstall-production
spec:
  template:
    metadata:
      labels:
        app: ubuntu-autoinstall-agent
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: ubuntu-autoinstall-agent
      template:
        metadata:
          labels:
            app: ubuntu-autoinstall-agent
        spec:
          containers:
          - name: ubuntu-autoinstall-agent
            image: ghcr.io/jdfalk/ubuntu-autoinstall-agent:v1.0.0
            resources:
              limits:
                cpu: 500m
                memory: 512Mi
              requests:
                cpu: 250m
                memory: 256Mi

  placement:
    clusters:
    - name: us-east-1
    - name: us-west-2
    - name: eu-west-1

  overrides:
  - clusterName: us-east-1
    clusterOverrides:
    - path: "/spec/replicas"
      value: 5

  - clusterName: us-west-2
    clusterOverrides:
    - path: "/spec/replicas"
      value: 3

  - clusterName: eu-west-1
    clusterOverrides:
    - path: "/spec/replicas"
      value: 3
````

## Security Best Practices

```markdown
# Deployment Security Checklist

## Image Security

- [ ] Images scanned for vulnerabilities (Trivy, Snyk)
- [ ] Images signed with Cosign
- [ ] Images stored in private registry
- [ ] Image pull secrets configured
- [ ] Base images regularly updated
- [ ] Minimal base images used (distroless/alpine)

## Pod Security

- [ ] RunAsNonRoot enabled
- [ ] ReadOnlyRootFilesystem where possible
- [ ] No privileged containers
- [ ] Capabilities dropped (ALL)
- [ ] SecurityContext configured
- [ ] AppArmor/SELinux profiles applied

## Network Security

- [ ] NetworkPolicy configured
- [ ] Ingress rules restrict traffic
- [ ] Egress rules limit outbound
- [ ] TLS/SSL enabled for ingress
- [ ] Service mesh for mTLS (optional)
- [ ] DDoS protection enabled

## Secrets Management

- [ ] Secrets encrypted at rest
- [ ] External secrets operator used (Vault, AWS Secrets Manager)
- [ ] No secrets in environment variables
- [ ] Secrets rotated regularly
- [ ] RBAC restricts secret access
- [ ] Audit logging for secret access

## RBAC

- [ ] ServiceAccounts per application
- [ ] Principle of least privilege
- [ ] Role/RoleBinding for namespace resources
- [ ] ClusterRole/ClusterRoleBinding only when necessary
- [ ] Regular RBAC audit

## Audit and Compliance

- [ ] Audit logging enabled
- [ ] Pod security policies/standards enforced
- [ ] Compliance scanning (CIS benchmarks)
- [ ] Regular security reviews
- [ ] Incident response plan documented
```

## Deployment Completion Checklist

```markdown
# Task 16: Deployment Automation - Completion Checklist

## Infrastructure

- [x] Kubernetes namespace created with proper labels
- [x] Deployment manifest with rolling update strategy
- [x] Service (ClusterIP) configured
- [x] Ingress with TLS and rate limiting
- [x] ConfigMap for application configuration
- [x] Secret for sensitive data
- [x] ServiceAccount with RBAC
- [x] HorizontalPodAutoscaler configured
- [x] PodDisruptionBudget for availability
- [x] NetworkPolicy for security

## Helm

- [x] Helm chart created with proper structure
- [x] Chart.yaml with metadata
- [x] values.yaml with comprehensive configuration
- [x] Environment-specific values files (dev/staging/production)
- [x] Template helpers for reusability
- [x] Deployment/Service/Ingress templates
- [x] NOTES.txt for post-install instructions

## Kustomize

- [x] Base manifests created
- [x] Development overlay with patches
- [x] Staging overlay with patches
- [x] Production overlay with patches
- [x] Components for monitoring and Istio
- [x] Kustomization files for each environment

## GitOps

- [x] ArgoCD Application definitions
- [x] AppProject for production with RBAC
- [x] Automated sync policies configured
- [x] Sync phases and hooks defined
- [x] Repository structure for GitOps

## Progressive Delivery

- [x] Flagger Canary resource configured
- [x] Flagger MetricTemplate for custom metrics
- [x] Argo Rollouts canary strategy
- [x] Argo Rollouts blue-green strategy
- [x] AnalysisTemplate for automated testing
- [x] GitHub Actions workflow for progressive deployment
- [x] Manual promotion and rollback scripts

## Infrastructure as Code

- [x] Terraform providers configured
- [x] Terraform variables defined
- [x] Kubernetes deployment module
- [x] Helm release with Terraform
- [x] Pulumi TypeScript program
- [x] Pulumi stack configurations

## Documentation

- [x] Deployment runbook created
- [x] Rollback procedures documented
- [x] Disaster recovery plan
- [x] Security best practices checklist
- [x] Multi-region deployment strategy
- [x] Backup and restore procedures

## Validation

- [ ] Deploy to development successful
- [ ] Deploy to staging successful
- [ ] Canary deployment to production successful
- [ ] Blue-green deployment tested
- [ ] Rollback procedure tested
- [ ] Disaster recovery tested
- [ ] Security scan passed
- [ ] Performance benchmarks met
- [ ] Documentation reviewed
- [ ] Team trained on deployment procedures

## Monitoring

- [ ] Deployment metrics in Grafana
- [ ] Alerts configured for deployment failures
- [ ] Rollout status tracked
- [ ] SLO compliance monitored
- [ ] Audit logs reviewed
```

---

**Task 16 Complete**: Comprehensive deployment automation covering Kubernetes manifests, Helm charts
with multi-environment values, Kustomize overlays with components, GitOps with ArgoCD, progressive
delivery with Flagger canary and Argo Rollouts blue-green strategies, Infrastructure as Code with
Terraform and Pulumi, zero-downtime deployment strategies, rollback procedures, disaster recovery
plans, multi-region deployment, security best practices, and complete deployment runbook. Total:
~3,900 lines across 6 parts. ✅

**Next**: Begin Task 17 - Observability and Centralized Logging with structured logging, log
aggregation, correlation with traces and metrics, and log-based alerting.
