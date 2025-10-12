<!-- file: docs/cross-registry-todos/task-15/t15-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t15-performance-monitoring-part3-c4d5e6f7-g8h9 -->

# Task 15 Part 3: Prometheus Configuration and Alerting

## Prometheus Server Configuration

### Main Prometheus Configuration

```yaml
# file: configs/prometheus.yml
# version: 1.0.0
# guid: prometheus-configuration

global:
  scrape_interval: 15s
  scrape_timeout: 10s
  evaluation_interval: 15s
  external_labels:
    cluster: 'production'
    region: 'us-west-2'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'alertmanager:9093'

# Load alerting rules
rule_files:
  - '/etc/prometheus/alerts/*.yml'

# Scrape configurations
scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Node exporters (system metrics)
  - job_name: 'node'
    static_configs:
      - targets:
          - 'node-exporter-1:9100'
          - 'node-exporter-2:9100'
          - 'node-exporter-3:9100'
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        regex: '([^:]+)(?::\d+)?'
        replacement: '${1}'

  # Application metrics (Rust services)
  - job_name: 'app-rust'
    static_configs:
      - targets:
          - 'app-1:8080'
          - 'app-2:8080'
          - 'app-3:8080'
    metrics_path: '/metrics'
    scrape_interval: 10s
    relabel_configs:
      - source_labels: [__address__]
        target_label: service
        replacement: 'ubuntu-autoinstall-agent'

  # Python services
  - job_name: 'app-python'
    static_configs:
      - targets:
          - 'python-service-1:8000'
          - 'python-service-2:8000'
    metrics_path: '/metrics'

  # Node.js services
  - job_name: 'app-nodejs'
    static_configs:
      - targets:
          - 'nodejs-service-1:3000'
          - 'nodejs-service-2:3000'
    metrics_path: '/metrics'

  # Kubernetes service discovery (optional)
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name

  # Pushgateway (for batch jobs)
  - job_name: 'pushgateway'
    honor_labels: true
    static_configs:
      - targets: ['pushgateway:9091']

  # Jaeger metrics
  - job_name: 'jaeger'
    static_configs:
      - targets: ['jaeger:14269']

# Remote write for long-term storage (optional)
remote_write:
  - url: 'http://thanos-receive:19291/api/v1/receive'
    queue_config:
      capacity: 10000
      max_shards: 10
      min_shards: 1
      max_samples_per_send: 5000
      batch_send_deadline: 5s

# Remote read for long-term storage (optional)
remote_read:
  - url: 'http://thanos-query:19291/api/v1/query'
    read_recent: true
```

## Alert Rules

### Application Performance Alerts

```yaml
# file: configs/alerts/application.yml
# version: 1.0.0
# guid: application-alerts

groups:
  - name: application_performance
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          (
            rate(http_requests_total{status=~"5.."}[5m])
            /
            rate(http_requests_total[5m])
          ) > 0.05
        for: 5m
        labels:
          severity: critical
          category: performance
        annotations:
          summary: 'High error rate detected'
          description: 'Error rate is {{ $value | humanizePercentage }} for {{ $labels.service }}'
          runbook: 'https://runbooks.example.com/high-error-rate'

      # High latency (P95)
      - alert: HighLatencyP95
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 1.0
        for: 10m
        labels:
          severity: warning
          category: performance
        annotations:
          summary: 'High P95 latency detected'
          description:
            'P95 latency is {{ $value }}s for {{ $labels.service }} on route {{ $labels.route }}'

      # High latency (P99)
      - alert: HighLatencyP99
        expr: |
          histogram_quantile(0.99,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 2.0
        for: 5m
        labels:
          severity: critical
          category: performance
        annotations:
          summary: 'High P99 latency detected'
          description: 'P99 latency is {{ $value }}s for {{ $labels.service }}'

      # Low throughput
      - alert: LowThroughput
        expr: |
          rate(http_requests_total[5m]) < 10
        for: 15m
        labels:
          severity: warning
          category: traffic
        annotations:
          summary: 'Low request throughput'
          description: 'Request rate is {{ $value }} req/s for {{ $labels.service }}'

      # Database query slow
      - alert: SlowDatabaseQueries
        expr: |
          histogram_quantile(0.95,
            rate(db_query_duration_seconds_bucket[5m])
          ) > 0.5
        for: 10m
        labels:
          severity: warning
          category: database
        annotations:
          summary: 'Slow database queries detected'
          description:
            'P95 query duration is {{ $value }}s for {{ $labels.operation }} on {{ $labels.table }}'

      # Memory leak detection (increasing memory over time)
      - alert: PossibleMemoryLeak
        expr: |
          (
            process_resident_memory_bytes
            - process_resident_memory_bytes offset 1h
          ) > 100000000  # 100MB increase
        for: 1h
        labels:
          severity: warning
          category: resource
        annotations:
          summary: 'Possible memory leak detected'
          description:
            'Memory usage increased by {{ $value | humanize }}B in the last hour for {{
            $labels.service }}'
```

### System Resource Alerts

```yaml
# file: configs/alerts/system.yml
# version: 1.0.0
# guid: system-alerts

groups:
  - name: system_resources
    interval: 30s
    rules:
      # High CPU usage
      - alert: HighCPUUsage
        expr: |
          (
            100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
          ) > 80
        for: 10m
        labels:
          severity: warning
          category: cpu
        annotations:
          summary: 'High CPU usage'
          description: 'CPU usage is {{ $value }}% on {{ $labels.instance }}'

      # Critical CPU usage
      - alert: CriticalCPUUsage
        expr: |
          (
            100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
          ) > 95
        for: 5m
        labels:
          severity: critical
          category: cpu
        annotations:
          summary: 'Critical CPU usage'
          description: 'CPU usage is {{ $value }}% on {{ $labels.instance }}'

      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          (
            1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
          ) > 0.85
        for: 10m
        labels:
          severity: warning
          category: memory
        annotations:
          summary: 'High memory usage'
          description: 'Memory usage is {{ $value | humanizePercentage }} on {{ $labels.instance }}'

      # Out of memory imminent
      - alert: OutOfMemory
        expr: |
          (
            node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes
          ) < 0.05
        for: 5m
        labels:
          severity: critical
          category: memory
        annotations:
          summary: 'Out of memory imminent'
          description:
            'Only {{ $value | humanizePercentage }} memory available on {{ $labels.instance }}'

      # High disk usage
      - alert: HighDiskUsage
        expr: |
          (
            1 - (node_filesystem_avail_bytes{fstype!~"tmpfs|fuse.*"} / node_filesystem_size_bytes)
          ) > 0.85
        for: 10m
        labels:
          severity: warning
          category: disk
        annotations:
          summary: 'High disk usage'
          description:
            'Disk usage is {{ $value | humanizePercentage }} on {{ $labels.instance }} at {{
            $labels.mountpoint }}'

      # Disk will fill in 4 hours (prediction)
      - alert: DiskWillFillSoon
        expr: |
          predict_linear(node_filesystem_avail_bytes{fstype!~"tmpfs|fuse.*"}[1h], 4 * 3600) < 0
        for: 10m
        labels:
          severity: warning
          category: disk
        annotations:
          summary: 'Disk will fill in 4 hours'
          description:
            'Disk {{ $labels.mountpoint }} on {{ $labels.instance }} will fill in approximately 4
            hours'

      # High disk I/O
      - alert: HighDiskIO
        expr: |
          rate(node_disk_io_time_seconds_total[5m]) > 0.9
        for: 10m
        labels:
          severity: warning
          category: disk
        annotations:
          summary: 'High disk I/O'
          description:
            'Disk I/O utilization is {{ $value | humanizePercentage }} on {{ $labels.instance }}
            device {{ $labels.device }}'

      # Network bandwidth high
      - alert: HighNetworkBandwidth
        expr: |
          rate(node_network_receive_bytes_total[5m]) > 100000000  # 100 MB/s
        for: 10m
        labels:
          severity: warning
          category: network
        annotations:
          summary: 'High network receive bandwidth'
          description:
            'Network receive is {{ $value | humanize }}B/s on {{ $labels.instance }} interface {{
            $labels.device }}'
```

### Service Level Objective (SLO) Alerts

```yaml
# file: configs/alerts/slo.yml
# version: 1.0.0
# guid: slo-alerts

groups:
  - name: slo_alerts
    interval: 30s
    rules:
      # Availability SLO (99.9%)
      - alert: AvailabilitySLOBreach
        expr: |
          (
            sum(rate(http_requests_total{status!~"5.."}[30d]))
            /
            sum(rate(http_requests_total[30d]))
          ) < 0.999
        for: 5m
        labels:
          severity: critical
          category: slo
          slo: availability
        annotations:
          summary: 'Availability SLO breach'
          description: '30-day availability is {{ $value | humanizePercentage }} (SLO: 99.9%)'
          impact: 'Service reliability below acceptable threshold'

      # Latency SLO (95% < 500ms)
      - alert: LatencySLOBreach
        expr: |
          (
            histogram_quantile(0.95,
              sum(rate(http_request_duration_seconds_bucket[30d])) by (le)
            )
          ) > 0.5
        for: 5m
        labels:
          severity: critical
          category: slo
          slo: latency
        annotations:
          summary: 'Latency SLO breach'
          description: '30-day P95 latency is {{ $value }}s (SLO: <500ms)'

      # Error budget burn rate (fast)
      - alert: FastErrorBudgetBurn
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[1h]))
            /
            sum(rate(http_requests_total[1h]))
          ) > (0.001 * 14.4)  # 14.4x normal error rate
        for: 2m
        labels:
          severity: critical
          category: slo
        annotations:
          summary: 'Fast error budget burn'
          description: 'Burning through error budget at 14.4x rate'
          action: 'Page on-call engineer immediately'

      # Error budget burn rate (slow)
      - alert: SlowErrorBudgetBurn
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[6h]))
            /
            sum(rate(http_requests_total[6h]))
          ) > (0.001 * 3)  # 3x normal error rate
        for: 15m
        labels:
          severity: warning
          category: slo
        annotations:
          summary: 'Slow error budget burn'
          description: 'Burning through error budget at 3x rate'
```

## Alertmanager Configuration

```yaml
# file: configs/alertmanager.yml
# version: 1.0.0
# guid: alertmanager-configuration

global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

# Templates for alert notifications
templates:
  - '/etc/alertmanager/templates/*.tmpl'

# Routing tree
route:
  receiver: 'default'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    # Critical alerts go to PagerDuty
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

    # Critical alerts also to Slack
    - match:
        severity: critical
      receiver: 'slack-critical'

    # Warning alerts to Slack only
    - match:
        severity: warning
      receiver: 'slack-warnings'

    # Performance alerts
    - match:
        category: performance
      receiver: 'slack-performance'
      group_by: ['alertname', 'service']
      group_wait: 1m

    # SLO alerts
    - match:
        category: slo
      receiver: 'pagerduty'
      continue: true
    - match:
        category: slo
      receiver: 'slack-slo'

# Inhibition rules (suppress alerts)
inhibit_rules:
  # Inhibit warning if critical is firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']

  # Inhibit specific alerts if service is down
  - source_match:
      alertname: 'ServiceDown'
    target_match_re:
      alertname: '(HighLatency|HighErrorRate|.*)'
    equal: ['service']

# Receivers
receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
        severity: '{{ .GroupLabels.severity }}'

  - name: 'slack-critical'
    slack_configs:
      - channel: '#alerts-critical'
        username: 'Alertmanager'
        color: 'danger'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          *Summary:* {{ .Annotations.summary }}
          *Description:* {{ .Annotations.description }}
          *Runbook:* {{ .Annotations.runbook }}
          {{ end }}

  - name: 'slack-warnings'
    slack_configs:
      - channel: '#alerts-warnings'
        username: 'Alertmanager'
        color: 'warning'
        title: '⚠️ WARNING: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'slack-performance'
    slack_configs:
      - channel: '#performance'
        username: 'Alertmanager'
        color: '#FFA500'
        title: '📊 Performance Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'slack-slo'
    slack_configs:
      - channel: '#slo-alerts'
        username: 'Alertmanager'
        color: 'danger'
        title: '🎯 SLO Alert: {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          *Summary:* {{ .Annotations.summary }}
          *Impact:* {{ .Annotations.impact }}
          *30-day trend:* Check dashboard
          {{ end }}
```

## Alert Notification Templates

```go-template
<!-- file: configs/alertmanager-templates/slack.tmpl -->
<!-- version: 1.0.0 -->
<!-- guid: alertmanager-slack-template -->

{{ define "slack.default.title" }}
[{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ end }}] {{ .GroupLabels.alertname }}
{{ end }}

{{ define "slack.default.text" }}
{{ range .Alerts }}
*Alert:* {{ .Labels.alertname }} - `{{ .Labels.severity }}`
*Summary:* {{ .Annotations.summary }}
*Description:* {{ .Annotations.description }}
{{ if .Annotations.runbook }}*Runbook:* {{ .Annotations.runbook }}{{ end }}
*Details:*
{{ range .Labels.SortedPairs }} • *{{ .Name }}:* `{{ .Value }}`
{{ end }}
{{ end }}
{{ end }}
```

---

**Part 3 Complete**: Prometheus server configuration with service discovery, comprehensive alert
rules (application performance, system resources, SLO monitoring), Alertmanager configuration with
routing, inhibition rules, and multi-channel notifications (PagerDuty, Slack), alert templates. ✅

**Continue to Part 4** for Grafana dashboards and visualization.
