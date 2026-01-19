<!-- file: docs/cross-registry-todos/task-18/t18-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t18-final-integration-part4-i5j6k7l8-m9n0 -->
<!-- last-edited: 2026-01-19 -->

# Task 18 Part 4: On-Call Playbooks and Incident Response

## On-Call Rotation Schedule

### Rotation Configuration

```yaml
# file: config/oncall/rotation.yaml
# version: 1.0.0
# guid: oncall-rotation-config

oncall_schedule:
  primary:
    name: 'Primary On-Call'
    rotation_type: weekly
    rotation_start: Monday 09:00 UTC
    members:
      - name: Alice Johnson
        email: alice@example.com
        phone: +1-555-0101
        slack: '@alice'
        timezone: America/New_York

      - name: Bob Smith
        email: bob@example.com
        phone: +1-555-0102
        slack: '@bob'
        timezone: America/Los_Angeles

      - name: Carol Williams
        email: carol@example.com
        phone: +1-555-0103
        slack: '@carol'
        timezone: Europe/London

    escalation_policy:
      - delay: 0
        notify: primary
      - delay: 15m
        notify: secondary
      - delay: 30m
        notify: manager
      - delay: 60m
        notify: director

  secondary:
    name: 'Secondary On-Call'
    rotation_type: weekly
    rotation_start: Monday 09:00 UTC
    members:
      - name: David Brown
        email: david@example.com
        phone: +1-555-0104
        slack: '@david'

      - name: Eve Davis
        email: eve@example.com
        phone: +1-555-0105
        slack: '@eve'

  manager:
    name: 'Engineering Manager'
    members:
      - name: Frank Miller
        email: frank@example.com
        phone: +1-555-0106
        slack: '@frank'

notification_channels:
  critical:
    - type: pagerduty
      api_key: '${PAGERDUTY_API_KEY}'
      urgency: high
    - type: phone
      provider: twilio
    - type: slack
      channel: '#incidents'
      mention: '@here'

  warning:
    - type: slack
      channel: '#alerts'
    - type: email

  info:
    - type: email
    - type: slack
      channel: '#monitoring'
```

## Incident Response Playbook

### Critical Service Down

````markdown
# Playbook: Critical Service Down

## Severity: P0 - Critical

**Impact**: Complete service outage, all users affected **Response Time**: Immediate (0-5 minutes)
**Escalation**: Immediate to manager if not resolved in 30 minutes

## Detection

- Alert: "ServiceDown" from Prometheus
- PagerDuty page sent to primary on-call
- Slack notification in #incidents channel
- Multiple user reports of 503 errors

## Immediate Response (0-5 minutes)

### 1. Acknowledge Alert

```bash
# Acknowledge in PagerDuty to stop escalation
pagerduty-cli incidents acknowledge --id ${INCIDENT_ID}

# Post in Slack
/incident create "API service down - investigating"
```
````

### 2. Initial Assessment

```bash
# Check service status
kubectl get pods -n production --selector=app=api-service

# Check recent events
kubectl get events -n production --sort-by='.lastTimestamp' | tail -20

# Check Grafana dashboard
open "http://grafana:3000/d/service-health"
```

### 3. Quick Status Update

```
Post in #incidents Slack channel:
"🚨 P0 Incident: API service down
Status: Investigating
Impact: All API requests failing
ETA: Investigating, update in 10 minutes
On-call: @username"
```

## Investigation (5-15 minutes)

### Check Pod Status

```bash
# Get pod details
kubectl describe pod <pod-name> -n production

# Check logs
kubectl logs deployment/api-service -n production --tail=100

# Previous logs if crashed
kubectl logs deployment/api-service -n production --previous
```

### Common Causes Checklist

- [ ] Recent deployment (last 1 hour)?
  - If yes: Consider immediate rollback
- [ ] Resource exhaustion (CPU/Memory)?
  - Scale up or increase limits
- [ ] Database connectivity issue?
  - Check database status and connection pool
- [ ] Configuration error?
  - Verify ConfigMap and Secrets
- [ ] Infrastructure issue?
  - Check node status and cluster health

## Resolution Actions

### Option 1: Rollback Deployment

```bash
# If deployed in last hour
kubectl rollout undo deployment/api-service -n production

# Monitor rollback
kubectl rollout status deployment/api-service -n production

# Verify service recovery
curl -I http://api-service:8080/health
```

### Option 2: Restart Service

```bash
# Simple restart
kubectl rollout restart deployment/api-service -n production

# Delete stuck pods
kubectl delete pod <pod-name> -n production --grace-period=0 --force
```

### Option 3: Scale Up Resources

```bash
# Increase replicas
kubectl scale deployment/api-service --replicas=10 -n production

# Apply resource increase
kubectl patch deployment api-service -n production --patch '
spec:
  template:
    spec:
      containers:
      - name: api-service
        resources:
          limits:
            memory: "4Gi"
            cpu: "2000m"
'
```

### Option 4: Enable Maintenance Mode

```yaml
# If extended downtime needed
# Update ingress to serve maintenance page
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: maintenance-mode
  namespace: production
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: maintenance-page
            port:
              number: 80
EOF
```

## Communication Updates

### Every 10 Minutes Until Resolved

```
Slack #incidents:
"⏱️ Update: API service
Status: [Investigating/Mitigating/Resolved]
Actions taken: [List actions]
Next step: [What you're doing next]
ETA: [Time estimate]"
```

### Resolution Message

```
Slack #incidents:
"✅ RESOLVED: API service
Duration: XX minutes
Root cause: [Brief description]
Fix applied: [What fixed it]
Monitoring: Will monitor for 1 hour
Post-mortem: Scheduled for [date/time]"
```

## Post-Incident (After Resolution)

### 1. Monitor for Stability (1 hour)

```bash
# Watch error rates
watch -n 10 'curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~\"5..\"}[5m])"'

# Monitor latency
watch -n 10 'curl -s "http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"'
```

### 2. Collect Incident Data

- Start time and end time
- Services affected
- User impact (number of failed requests)
- Actions taken and their results
- Root cause
- Prevention measures

### 3. Schedule Post-Mortem

- Within 48 hours of incident
- Invite all relevant stakeholders
- Prepare timeline and investigation findings
- Focus on process improvement, not blame

````

### Database Performance Degradation

```markdown
# Playbook: Database Performance Degradation

## Severity: P1 - High
**Impact**: Slow response times, degraded user experience
**Response Time**: 15 minutes
**Escalation**: To DBA team if not resolved in 1 hour

## Detection
- Alert: "SlowDatabaseQueries" firing
- P95 query latency > 1 second
- Users reporting slow page loads
- Grafana showing elevated database metrics

## Immediate Actions

### 1. Identify Slow Queries
```sql
-- Top slow queries
SELECT query, calls, total_time, mean_time, max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Long-running queries
SELECT pid, usename, query, state, query_start
FROM pg_stat_activity
WHERE state = 'active'
  AND query_start < NOW() - INTERVAL '30 seconds'
ORDER BY query_start;
````

### 2. Check Database Resources

```bash
# Connection count
kubectl exec -it postgres-0 -- psql -U postgres -c "
  SELECT count(*) as connections,
         state
  FROM pg_stat_activity
  GROUP BY state;
"

# Cache hit rate
kubectl exec -it postgres-0 -- psql -U postgres -c "
  SELECT sum(heap_blks_read) as heap_read,
         sum(heap_blks_hit) as heap_hit,
         sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as hit_rate
  FROM pg_statio_user_tables;
"
```

### 3. Quick Fixes

#### Terminate Long-Running Queries

```sql
-- Cancel query
SELECT pg_cancel_backend(pid)
FROM pg_stat_activity
WHERE pid = <slow_query_pid>;

-- Force terminate if needed
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE pid = <slow_query_pid>;
```

#### Increase Connection Pool

```yaml
# Update application config
env:
  - name: DATABASE_POOL_SIZE
    value: '50' # From 20
  - name: DATABASE_POOL_TIMEOUT
    value: '30' # 30 seconds
```

#### Add Missing Index

```sql
-- Identify missing indexes
SELECT schemaname, tablename, attname
FROM pg_stats
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  AND n_distinct > 100
  AND correlation < 0.1
ORDER BY n_distinct DESC;

-- Create index (use CONCURRENTLY to avoid locking)
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
```

## Long-Term Solutions

1. Implement query caching
2. Optimize N+1 queries
3. Add read replicas for read-heavy workloads
4. Set up connection pooler (PgBouncer)
5. Schedule regular VACUUM and ANALYZE

````

### Security Incident

```markdown
# Playbook: Security Incident

## Severity: P0 - Critical
**Impact**: Potential data breach or unauthorized access
**Response Time**: Immediate
**Escalation**: Immediate to Security Team and Legal

## Detection
- Alert: "MultipleFailedLogins" or "UnauthorizedAccess"
- IDS/IPS alerts
- Unusual traffic patterns
- User reports of suspicious activity

## Immediate Response

### 1. Contain the Threat
```bash
# Block suspicious IP
kubectl exec -it nginx-ingress-controller -- \
  iptables -A INPUT -s <suspicious_ip> -j DROP

# Disable compromised user account
kubectl exec -it auth-service -- \
  ./scripts/disable-user.sh --user-id <user_id>

# Revoke all sessions for user
kubectl exec -it auth-service -- \
  redis-cli DEL "session:user:<user_id>:*"
````

### 2. Preserve Evidence

```bash
# Export logs for analysis
kubectl logs deployment/api-service -n production --since=24h > incident-logs.txt

# Export database audit logs
kubectl exec -it postgres-0 -- pg_dump --table=audit_logs > audit-logs.sql

# Take snapshot of affected systems
kubectl exec -it api-service -- tar czf /tmp/incident-snapshot.tar.gz /app/logs /app/config
kubectl cp production/api-service:/tmp/incident-snapshot.tar.gz ./incident-snapshot.tar.gz
```

### 3. Notify Stakeholders

- Security team (immediate)
- Legal team (immediate if data breach suspected)
- Executive team (within 1 hour)
- Affected users (as required by regulations)

## Investigation

### Analyze Attack Pattern

```bash
# Query failed login attempts
curl -G 'http://loki:3100/loki/api/v1/query' \
  --data-urlencode 'query={service="auth"} |= "failed" | json' \
  --data-urlencode 'start=-24h'

# Check for SQL injection attempts
curl -G 'http://loki:3100/loki/api/v1/query' \
  --data-urlencode 'query={} |~ "(?i)(union.*select|drop.*table)" | json'

# Identify affected resources
kubectl get pods -n production -o json | \
  jq '.items[] | select(.metadata.labels.compromised=="true")'
```

### Security Checklist

- [ ] Identify attack vector
- [ ] Determine scope of access
- [ ] Check for data exfiltration
- [ ] Verify system integrity
- [ ] Review access logs
- [ ] Check for backdoors or persistence mechanisms

## Recovery

### Rotate Credentials

```bash
# Rotate database passwords
kubectl create secret generic db-credentials \
  --from-literal=password=$(openssl rand -base64 32) \
  --dry-run=client -o yaml | kubectl apply -f -

# Rotate API keys
kubectl exec -it auth-service -- ./scripts/rotate-api-keys.sh

# Regenerate JWT signing keys
kubectl exec -it auth-service -- ./scripts/regenerate-jwt-keys.sh
```

### Patch Vulnerabilities

```bash
# Update vulnerable dependencies
kubectl set image deployment/api-service api-service=api-service:patched-version

# Apply security patches
kubectl apply -f security-patches/
```

## Documentation

- Timeline of events
- Attack vector and method
- Systems compromised
- Data accessed/exfiltrated
- Actions taken
- Preventive measures implemented

````

## Escalation Matrix

### Escalation Levels

| Level | Title                   | Contact Method          | Response Time | Conditions                  |
| ----- | ----------------------- | ----------------------- | ------------- | --------------------------- |
| L1    | Primary On-Call         | PagerDuty, Phone, Slack | 5 minutes     | All P0/P1 alerts            |
| L2    | Secondary On-Call       | PagerDuty, Phone        | 15 minutes    | If L1 doesn't ack in 15min  |
| L3    | Engineering Manager     | Phone, Slack            | 30 minutes    | Issue not resolved in 30min |
| L4    | Director of Engineering | Phone                   | 60 minutes    | Major outage >1 hour        |
| L5    | CTO                     | Phone                   | As needed     | Business-critical, >4 hours |

### Escalation Triggers

```python
# file: scripts/auto_escalate.py
# version: 1.0.0
# guid: auto-escalation-logic

from datetime import datetime, timedelta
from typing import Dict, List

class EscalationManager:
    """Manage incident escalation."""

    ESCALATION_LEVELS = {
        'L1': {'delay': timedelta(minutes=0), 'role': 'primary_oncall'},
        'L2': {'delay': timedelta(minutes=15), 'role': 'secondary_oncall'},
        'L3': {'delay': timedelta(minutes=30), 'role': 'manager'},
        'L4': {'delay': timedelta(hours=1), 'role': 'director'},
        'L5': {'delay': timedelta(hours=4), 'role': 'cto'},
    }

    def should_escalate(
        self,
        incident_start: datetime,
        current_level: str,
        severity: str,
    ) -> bool:
        """Determine if incident should escalate to next level."""
        elapsed = datetime.now() - incident_start

        # Get next level
        levels = list(self.ESCALATION_LEVELS.keys())
        current_index = levels.index(current_level)

        if current_index >= len(levels) - 1:
            return False  # Already at highest level

        next_level = levels[current_index + 1]
        next_delay = self.ESCALATION_LEVELS[next_level]['delay']

        # Escalate if elapsed time exceeds delay
        if elapsed >= next_delay:
            return True

        # Immediate escalation for critical severity
        if severity == 'P0' and next_level in ['L3', 'L4']:
            if elapsed >= timedelta(minutes=30):
                return True

        return False
````

---

**Part 4 Complete**: On-call playbooks with rotation configuration including primary/secondary/
manager schedules with contact info (email/phone/Slack) and escalation policy (0min→primary, 15min→
secondary, 30min→manager, 60min→director), incident response playbooks for critical service down (P0
severity, 0-5min response, immediate acknowledgment, initial assessment with kubectl commands, quick
status updates every 10min, investigation checklist, resolution actions including rollback/
restart/scale-up/maintenance mode, post-incident monitoring for 1 hour and post-mortem scheduling),
database performance degradation (P1 severity, identify slow queries with pg_stat_statements, check
resources and connection count, quick fixes with query termination/connection pool increase/missing
indexes, long-term solutions), security incident playbook (P0 critical, immediate containment with
IP blocking and account disabling, evidence preservation with log exports and snapshots, stakeholder
notification, attack pattern analysis, security checklist, recovery with credential rotation and
vulnerability patching), escalation matrix with 5 levels (L1→L5) and response times (5min→as
needed), auto-escalation logic with time-based triggers and severity-based immediate escalation. ✅

**Continue to Part 5** for project dashboards showing CI/CD metrics, cost tracking, and team
productivity.
