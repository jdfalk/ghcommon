<!-- file: docs/cross-registry-todos/task-15/t15-part6.md -->
<!-- version: 1.0.0 -->
<!-- guid: t15-performance-monitoring-part6-s0t1u2v3-w4x5 -->

# Task 15 Part 6: Monitoring Best Practices and Completion Checklist

## Monitoring Strategy Best Practices

### The Four Golden Signals

````markdown
# Golden Signals Monitoring Strategy

## 1. Latency

**Definition**: Time taken to service a request

**Implementation**:

- Track request duration with histograms, not averages
- Monitor percentiles: p50, p95, p99, p99.9
- Separate successful vs failed request latency
- Set SLOs based on user experience requirements

**Metrics to collect**:

```prometheus
# Request duration histogram
http_request_duration_seconds_bucket{le="0.1"} 245
http_request_duration_seconds_bucket{le="0.5"} 892
http_request_duration_seconds_bucket{le="1.0"} 975
http_request_duration_seconds_count 1000
http_request_duration_seconds_sum 342.5

# Query for P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```
````

**Alerts**:

- P95 latency > 500ms for 5 minutes
- P99 latency > 1s for 5 minutes
- Latency spike: >150% of baseline

## 2. Traffic

**Definition**: Demand on your system

**Implementation**:

- Monitor requests per second (RPS)
- Track by endpoint, method, status code
- Understand normal traffic patterns
- Detect traffic anomalies (spikes/drops)

**Metrics to collect**:

```prometheus
# Request rate
rate(http_requests_total[5m])

# By endpoint
sum by (endpoint) (rate(http_requests_total[5m]))

# By status code
sum by (status) (rate(http_requests_total[5m]))
```

**Alerts**:

- Traffic drop >50% for 5 minutes (possible outage)
- Traffic spike >200% of normal (potential attack)
- Unusual endpoint traffic patterns

## 3. Errors

**Definition**: Rate of failed requests

**Implementation**:

- Track error rate as percentage
- Separate client errors (4xx) from server errors (5xx)
- Monitor error types and patterns
- Correlate errors with deployments

**Metrics to collect**:

```prometheus
# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) /
sum(rate(http_requests_total[5m]))

# By error type
sum by (status) (rate(http_requests_total{status=~"5.."}[5m]))
```

**Alerts**:

- Error rate >1% for 5 minutes
- Any 5xx errors in critical endpoints
- Error budget exhaustion (<10% remaining)

## 4. Saturation

**Definition**: How full your service is

**Implementation**:

- Monitor resource utilization: CPU, memory, disk, network
- Track queue depths and thread pool utilization
- Identify bottlenecks before they cause failures
- Set capacity planning alerts

**Metrics to collect**:

```prometheus
# CPU usage
100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk usage
(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100

# Queue depth
queue_depth / queue_capacity
```

**Alerts**:

- CPU >80% for 10 minutes
- Memory >80% for 10 minutes
- Disk >85% (warning), >95% (critical)
- Queue >70% capacity

````

### USE Method (Utilization, Saturation, Errors)

```markdown
# USE Method for Resource Monitoring

## For Every Resource, Monitor:

### 1. Utilization
**Definition**: Average time resource was busy

**Resources to monitor**:
- CPU: % busy vs idle
- Memory: % used vs available
- Network: bandwidth utilization
- Disk: I/O utilization

**Prometheus queries**:
```prometheus
# CPU utilization
avg(irate(node_cpu_seconds_total{mode!="idle"}[5m]))

# Memory utilization
1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

# Network utilization
rate(node_network_transmit_bytes_total[5m]) /
  (node_network_speed_bytes * 0.8)  # 80% of link speed

# Disk utilization
rate(node_disk_io_time_seconds_total[5m])
````

### 2. Saturation

**Definition**: Amount of work resource cannot service (queued)

**Indicators**:

- Load average (CPU queue)
- Swap usage (memory saturation)
- Network packet drops
- Disk I/O wait time

**Prometheus queries**:

```prometheus
# CPU saturation (load average)
node_load1 / count(node_cpu_seconds_total{mode="idle"})

# Memory saturation (swap)
node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes

# Network saturation (drops)
rate(node_network_transmit_drop_total[5m]) +
rate(node_network_receive_drop_total[5m])

# Disk saturation (queue depth)
node_disk_io_time_weighted_seconds_total
```

### 3. Errors

**Definition**: Count of error events

**Examples**:

- Failed disk operations
- Network errors
- Memory allocation failures
- CPU thermal throttling

**Prometheus queries**:

```prometheus
# Disk errors
rate(node_disk_read_errors_total[5m]) +
rate(node_disk_write_errors_total[5m])

# Network errors
rate(node_network_receive_errs_total[5m]) +
rate(node_network_transmit_errs_total[5m])
```

````

### RED Method (Rate, Errors, Duration)

```markdown
# RED Method for Request-Driven Services

## For Every Service Endpoint:

### 1. Rate
**Definition**: Number of requests per second

**Why it matters**:
- Understand load patterns
- Capacity planning
- Detect traffic anomalies

**Implementation**:
```prometheus
# Overall request rate
sum(rate(http_requests_total[5m]))

# By endpoint
sum by (endpoint) (rate(http_requests_total[5m]))

# By method
sum by (method) (rate(http_requests_total[5m]))
````

### 2. Errors

**Definition**: Number of failed requests per second

**Why it matters**:

- Service health indicator
- SLO compliance
- User impact assessment

**Implementation**:

```prometheus
# Error count
sum(rate(http_requests_total{status=~"5.."}[5m]))

# Error rate (percentage)
sum(rate(http_requests_total{status=~"5.."}[5m])) /
sum(rate(http_requests_total[5m]))

# By endpoint
sum by (endpoint) (rate(http_requests_total{status=~"5.."}[5m]))
```

### 3. Duration

**Definition**: Time each request takes

**Why it matters**:

- User experience
- Performance degradation detection
- SLO compliance

**Implementation**:

```prometheus
# P50 (median)
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))

# P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# P99
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Average (use sparingly)
rate(http_request_duration_seconds_sum[5m]) /
rate(http_request_duration_seconds_count[5m])
```

## Dashboard Best Practices

````markdown
# Grafana Dashboard Design Guidelines

## 1. Dashboard Organization

### High-Level Overview Dashboard

**Purpose**: Quick health check for entire system

**Panels**:

- Overall SLO compliance (availability, latency, error budget)
- Request rate and error rate trends
- Resource utilization summary (CPU, memory)
- Active alerts count
- Service dependency status

**Refresh**: 30s-1m

### Service-Specific Dashboards

**Purpose**: Deep dive into individual service metrics

**Panels**:

- RED metrics (Rate, Errors, Duration) for the service
- Resource utilization specific to service
- Database query performance
- Cache hit rates
- External API call latencies
- Business metrics (conversions, transactions)

**Refresh**: 30s

### Resource Dashboards

**Purpose**: Infrastructure and resource monitoring

**Panels**:

- CPU, memory, disk, network per host
- Container/pod resource usage
- Database performance
- Message queue depths
- Storage I/O

**Refresh**: 1m

## 2. Panel Design Best Practices

### Use Appropriate Visualization Types

- **Time series graphs**: Trends over time (latency, traffic)
- **Stat panels**: Current values (error rate, active connections)
- **Gauges**: Percentage metrics (CPU usage, SLO compliance)
- **Tables**: Top N queries (slowest endpoints, highest error rates)
- **Heatmaps**: Distribution over time (latency distribution)

### Color Coding

- **Green**: Good state, within SLO
- **Yellow**: Warning state, approaching threshold
- **Red**: Critical state, SLO breach

### Thresholds

Always set meaningful thresholds:

```json
{
  "thresholds": {
    "mode": "absolute",
    "steps": [
      { "value": null, "color": "green" },
      { "value": 80, "color": "yellow" },
      { "value": 90, "color": "red" }
    ]
  }
}
```
````

### Units

Always specify units:

- Time: `s` (seconds), `ms` (milliseconds)
- Data: `bytes`, `Bps` (bytes per second)
- Percentage: `percent` or `percentunit` (0-1)
- Count: `short` or specific unit (ops, req/s)

## 3. Dashboard Variables

### Use template variables for flexibility:

```yaml
variables:
  - name: cluster
    type: query
    query: label_values(up, cluster)

  - name: namespace
    type: query
    query: label_values(up{cluster="$cluster"}, namespace)

  - name: service
    type: query
    query: label_values(up{cluster="$cluster",namespace="$namespace"}, service)
```

### Benefits:

- Single dashboard for multiple environments
- Filter by service, region, cluster
- Reduce dashboard sprawl

````

## Alert Design Best Practices

```markdown
# Alert Design and Management

## 1. Alert Principles

### Actionable
Every alert must require immediate human action
- **Good**: "Database connection pool exhausted, requests failing"
- **Bad**: "CPU usage above 50%"

### Relevant
Alert on symptoms, not causes
- **Good**: "Error rate >1%, users affected"
- **Bad**: "Process crashed" (if service is still healthy)

### Timely
Alert with appropriate urgency
- **Critical**: Immediate response needed (pager)
- **Warning**: Investigation within hours
- **Info**: Log only, no notification

## 2. Alert Composition

### Multi-Window Multi-Burn-Rate Alerts
Combine multiple time windows to reduce false positives:

```yaml
# Fast burn (1h window, 14.4x burn rate)
alert: ErrorBudgetFastBurn
expr: |
  (
    sum(rate(http_requests_total{status=~"5.."}[1h])) /
    sum(rate(http_requests_total[1h]))
  ) > (14.4 * 0.001)  # 14.4x 0.1% error rate
for: 5m
severity: critical

# Slow burn (24h window, 3x burn rate)
alert: ErrorBudgetSlowBurn
expr: |
  (
    sum(rate(http_requests_total{status=~"5.."}[24h])) /
    sum(rate(http_requests_total[24h]))
  ) > (3 * 0.001)  # 3x 0.1% error rate
for: 1h
severity: warning
````

### Alert Grouping

Group related alerts to avoid alert storms:

```yaml
# Alertmanager grouping
route:
  group_by: ['service', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
```

## 3. Alert Fatigue Prevention

### Strategies:

1. **Use inhibition rules**: Suppress redundant alerts

   ```yaml
   inhibit_rules:
     - source_match:
         severity: critical
       target_match:
         severity: warning
       equal: ['service', 'cluster']
   ```

2. **Silence during maintenance**: Use Alertmanager silences

   ```bash
   amtool silence add \
     alertname=HighLatency \
     --duration 2h \
     --comment "Deploying new version"
   ```

3. **Tune alert thresholds**: Regularly review and adjust
   - Track alert frequency
   - Measure time-to-resolution
   - Identify false positives

4. **Progressive severity**: Start with warnings, escalate to critical

   ```yaml
   - alert: HighErrorRate
     expr: error_rate > 0.01
     for: 5m
     labels:
       severity: warning

   - alert: VeryHighErrorRate
     expr: error_rate > 0.05
     for: 2m
     labels:
       severity: critical
   ```

````

## Monitoring Maturity Model

```markdown
# Monitoring Maturity Progression

## Level 1: Basic Monitoring
- Infrastructure metrics (CPU, memory, disk)
- Basic application metrics (request count, errors)
- Manual dashboards
- Email alerts

**Goal**: Visibility into system health

## Level 2: Proactive Monitoring
- Application performance metrics (latency, throughput)
- Custom business metrics
- Automated alerting
- Incident response procedures
- Basic SLOs

**Goal**: Detect issues before users report them

## Level 3: Observability
- Distributed tracing
- Structured logging with correlation
- Real-time dashboards
- Multi-window alerts
- Error budgets and SLO tracking
- Root cause analysis tools

**Goal**: Understand complex system behavior

## Level 4: Predictive Monitoring
- Anomaly detection with ML
- Capacity forecasting
- Automated remediation
- Chaos engineering integration
- Continuous optimization

**Goal**: Prevent issues before they occur

## Level 5: Self-Healing Systems
- Automated failover
- Auto-scaling based on predictions
- Self-tuning thresholds
- Incident-less operations

**Goal**: Autonomous reliability
````

## Runbook Template

````markdown
# Service Runbook Template

## Service Overview

- **Name**: ubuntu-autoinstall-agent
- **Purpose**: Ubuntu automated installation orchestration
- **Architecture**: Rust web service with QEMU integration
- **Dependencies**: QEMU, libvirt, cloud-init
- **SLO**: 99.9% availability, P95 latency <500ms, error rate <0.1%

## Common Alerts and Responses

### High Error Rate

**Alert**: `error_rate > 0.05 for 5 minutes`

**Symptoms**:

- Users experiencing failures
- Increased 5xx response codes
- Error logs increasing

**Investigation**:

1. Check service logs for error patterns
   ```bash
   kubectl logs -l app=ubuntu-autoinstall-agent --tail=100 | grep ERROR
   ```
````

2. Verify dependencies

   ```bash
   curl http://qemu-service:8080/health
   ```

3. Check resource utilization
   - CPU >80%? Scale up
   - Memory >80%? Investigate memory leak
   - Disk full? Clean up old images

**Resolution**:

- If dependency down: Wait for recovery or fail over
- If resource exhaustion: Scale horizontally
- If application bug: Roll back to previous version

**Escalation**: If unresolved in 30 minutes, page on-call engineer

### High Latency

**Alert**: `p95_latency > 1s for 5 minutes`

**Investigation**:

1. Identify slow endpoints

   ```promql
   topk(5, histogram_quantile(0.95,
     rate(http_request_duration_seconds_bucket[5m])))
   ```

2. Check database query performance
   - Slow queries?
   - Connection pool exhausted?

3. Review traces for slow spans
   - External API calls timing out?
   - CPU-intensive operations?

**Resolution**:

- Add caching for expensive operations
- Optimize slow queries
- Increase timeout for external calls
- Scale service if under heavy load

### Service Down

**Alert**: `up{service="ubuntu-autoinstall-agent"} == 0`

**Investigation**:

1. Check if service is running

   ```bash
   kubectl get pods -l app=ubuntu-autoinstall-agent
   ```

2. Check recent deployments

   ```bash
   kubectl rollout history deployment/ubuntu-autoinstall-agent
   ```

3. Review crash logs
   ```bash
   kubectl logs -l app=ubuntu-autoinstall-agent --previous
   ```

**Resolution**:

- If deployment failed: Roll back
  ```bash
  kubectl rollout undo deployment/ubuntu-autoinstall-agent
  ```
- If OOM killed: Increase memory limits
- If crash loop: Fix application bug

## Deployment Procedures

1. Deploy to staging first
2. Run smoke tests
3. Monitor error rates and latency for 10 minutes
4. Deploy to production with gradual rollout
5. Monitor for 30 minutes before marking complete

## Rollback Procedures

```bash
# Kubernetes
kubectl rollout undo deployment/ubuntu-autoinstall-agent

# Verify
kubectl rollout status deployment/ubuntu-autoinstall-agent
```

## Emergency Contacts

- **On-call Engineer**: PagerDuty
- **Team Lead**: Slack #team-infrastructure
- **Database Team**: For query optimization issues
- **Platform Team**: For infrastructure issues

````

## Monitoring Completion Checklist

```markdown
# Task 15: Performance Monitoring - Completion Checklist

## Infrastructure Setup
- [x] Prometheus server deployed and configured
- [x] Alertmanager deployed with notification channels
- [x] Grafana deployed with datasources configured
- [x] Jaeger deployed for distributed tracing
- [x] Pyroscope deployed for continuous profiling
- [x] Metrics exporters deployed (node-exporter, cAdvisor)

## Application Instrumentation
- [x] Rust services instrumented with metrics crate
- [x] Rust services instrumented with tracing
- [x] JavaScript services instrumented with OpenTelemetry
- [x] Python services instrumented with OpenTelemetry
- [x] Custom business metrics defined and collected
- [x] Distributed tracing context propagation working

## Metrics Collection
- [x] Prometheus scrape configurations defined
- [x] Recording rules created for common aggregations
- [x] Service discovery configured (Kubernetes/Consul)
- [x] Remote write to long-term storage configured

## Dashboards
- [x] Application performance dashboard created
- [x] System resources dashboard created
- [x] SLO compliance dashboard created
- [x] Distributed tracing dashboard configured
- [x] Profiling dashboard configured
- [x] Dashboard variables configured for multi-environment
- [x] All panels have appropriate units and thresholds

## Alerting
- [x] Alerting rules defined in Prometheus
- [x] Alertmanager routing configured by severity
- [x] PagerDuty integration configured for critical alerts
- [x] Slack integration configured for warnings
- [x] Email notifications configured for info alerts
- [x] Inhibition rules configured to prevent alert storms
- [x] Multi-window multi-burn-rate alerts configured

## SLOs and Error Budgets
- [x] SLOs defined: Availability >99.9%, Latency P95 <500ms, Error rate <0.1%
- [x] Error budget calculations automated
- [x] Error budget burn rate alerts configured
- [x] SLO compliance tracked in dashboards

## Performance Testing
- [x] k6 load tests written and automated
- [x] k6 stress tests configured
- [x] k6 spike tests configured
- [x] Rust Criterion benchmarks implemented
- [x] Python pytest-benchmark tests created
- [x] Performance testing CI workflows created
- [x] Performance regression detection automated
- [x] k6 metrics exported to Prometheus

## Documentation
- [x] Monitoring architecture documented
- [x] Dashboard usage guide created
- [x] Alert runbooks written for common scenarios
- [x] SLO definitions documented
- [x] Performance testing procedures documented
- [x] Troubleshooting guide created
- [x] On-call procedures documented

## Validation
- [ ] All metrics appearing in Prometheus
- [ ] All dashboards displaying data correctly
- [ ] Test alerts firing and routing correctly
- [ ] Distributed traces appearing in Jaeger
- [ ] Profiling data appearing in Pyroscope
- [ ] Performance tests running successfully
- [ ] SLO compliance meeting targets
- [ ] Team trained on monitoring tools and procedures

## Maintenance
- [ ] Prometheus data retention policy configured (30 days)
- [ ] Grafana dashboard backup configured
- [ ] Alert rule review schedule established (quarterly)
- [ ] Performance test schedule established (weekly)
- [ ] Monitoring metrics review process defined
- [ ] Continuous improvement process documented
````

---

**Task 15 Complete**: Comprehensive performance monitoring and profiling automation covering
monitoring strategy with Golden Signals/USE Method/RED Method, Prometheus/Alertmanager
configuration, Grafana dashboards for application performance/system resources/SLO tracking,
distributed tracing with Jaeger, continuous profiling with Pyroscope, performance testing with
k6/Criterion/pytest-benchmark, regression detection, monitoring best practices, alert design
principles, runbook templates, and completion checklist. Total: ~3,900 lines across 6 parts. ✅

**Next**: Begin Task 16 - Deployment Automation and Orchestration with Kubernetes, Helm, GitOps, and
progressive delivery strategies.
