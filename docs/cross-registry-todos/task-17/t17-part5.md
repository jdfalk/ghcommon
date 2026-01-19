<!-- file: docs/cross-registry-todos/task-17/t17-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t17-observability-logging-part5-e5f6g7h8-i9j0 -->
<!-- last-edited: 2026-01-19 -->

# Task 17 Part 5: Log-Based Alerting and Anomaly Detection

## Loki Alerting Rules

### Loki Ruler Configuration

```yaml
# file: config/loki/rules.yaml
# version: 1.0.0
# guid: loki-alerting-rules

groups:
  - name: error_alerts
    interval: 1m
    rules:
      # High error rate alert
      - alert: HighErrorRate
        expr: |
          sum(rate({level="error"}[5m])) by (service) > 10
        for: 5m
        labels:
          severity: critical
          category: application
        annotations:
          summary: 'High error rate detected'
          description: 'Service {{ $labels.service }} has error rate of {{ $value }} errors/sec'
          runbook: 'https://runbooks.example.com/high-error-rate'

      # Error spike alert
      - alert: ErrorSpike
        expr: |
          (
            sum(rate({level="error"}[5m])) by (service)
            /
            sum(rate({level="error"}[5m] offset 1h)) by (service)
          ) > 5
        for: 2m
        labels:
          severity: warning
          category: application
        annotations:
          summary: 'Error spike detected'
          description: 'Service {{ $labels.service }} has 5x increase in errors'

      # Critical error pattern
      - alert: CriticalErrorPattern
        expr: |
          sum(rate({level="error"} |~ "OutOfMemoryError|StackOverflowError|FatalError"[5m])) by (service) > 0
        for: 1m
        labels:
          severity: critical
          category: fatal_error
        annotations:
          summary: 'Critical error detected'
          description: 'Service {{ $labels.service }} has critical errors'
          action: 'Immediate investigation required'

  - name: security_alerts
    interval: 1m
    rules:
      # Authentication failures
      - alert: HighAuthenticationFailures
        expr: |
          sum(rate({app="auth"} |= "authentication failed"[5m])) > 10
        for: 5m
        labels:
          severity: warning
          category: security
        annotations:
          summary: 'High authentication failure rate'
          description: '{{ $value }} authentication failures per second'
          action: 'Check for brute force attack'

      # Unauthorized access attempts
      - alert: UnauthorizedAccessAttempts
        expr: |
          sum(count_over_time({status="403"} |~ "unauthorized|forbidden"[5m])) by (remote_addr) > 50
        labels:
          severity: warning
          category: security
        annotations:
          summary: 'Multiple unauthorized access attempts'
          description: 'IP {{ $labels.remote_addr }} attempted {{ $value }} unauthorized accesses'
          action: 'Consider blocking IP address'

      # SQL injection attempts
      - alert: SQLInjectionAttempt
        expr: |
          sum(count_over_time({} |~ "(?i)(union.*select|insert.*into|delete.*from|drop.*table)"[5m])) > 0
        labels:
          severity: critical
          category: security
        annotations:
          summary: 'Possible SQL injection attempt detected'
          description: '{{ $value }} potential SQL injection attempts'
          action: 'Review security logs immediately'

  - name: performance_alerts
    interval: 1m
    rules:
      # Slow queries
      - alert: SlowDatabaseQueries
        expr: |
          sum(rate({} |= "slow query" | json | duration_ms > 1000[5m])) by (service) > 5
        for: 5m
        labels:
          severity: warning
          category: performance
        annotations:
          summary: 'Slow database queries detected'
          description: 'Service {{ $labels.service }} has {{ $value }} slow queries/sec (>1s)'

      # High latency
      - alert: HighRequestLatency
        expr: |
          quantile_over_time(0.95, {job="api"} | json | unwrap duration_ms [5m]) by (endpoint) > 1000
        for: 10m
        labels:
          severity: warning
          category: performance
        annotations:
          summary: 'High request latency'
          description: 'Endpoint {{ $labels.endpoint }} has P95 latency of {{ $value }}ms'

  - name: availability_alerts
    interval: 1m
    rules:
      # Service not logging
      - alert: ServiceNotLogging
        expr: |
          absent_over_time({service="critical-service"}[5m])
        labels:
          severity: critical
          category: availability
        annotations:
          summary: 'Service stopped logging'
          description: 'No logs from critical-service for 5 minutes'
          action: 'Check service health immediately'

      # Pod restart loop
      - alert: PodRestartLoop
        expr: |
          sum(count_over_time({} |= "Starting application"[10m])) by (pod) > 5
        labels:
          severity: critical
          category: availability
        annotations:
          summary: 'Pod restart loop detected'
          description: 'Pod {{ $labels.pod }} restarted {{ $value }} times in 10 minutes'
          action: 'Check pod logs and events'

  - name: business_alerts
    interval: 5m
    rules:
      # Payment failures
      - alert: HighPaymentFailureRate
        expr: |
          (
            sum(rate({service="payment"} |= "payment failed"[10m]))
            /
            sum(rate({service="payment"} |~ "payment (success|failed)"[10m]))
          ) * 100 > 5
        for: 10m
        labels:
          severity: critical
          category: business
        annotations:
          summary: 'High payment failure rate'
          description: '{{ $value }}% of payments are failing'
          action: 'Contact payment provider immediately'

      # Order processing delays
      - alert: OrderProcessingDelay
        expr: |
          quantile_over_time(0.95, {service="orders"} |= "order processed" | json | unwrap processing_time_ms [15m]) > 60000
        for: 15m
        labels:
          severity: warning
          category: business
        annotations:
          summary: 'Order processing delays'
          description: 'P95 order processing time is {{ $value }}ms (>1 minute)'
```

## Prometheus Alertmanager Integration

### Alertmanager Configuration

```yaml
# file: config/alertmanager/alertmanager.yml
# version: 1.0.0
# guid: alertmanager-configuration

global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

# Templates
templates:
  - '/etc/alertmanager/templates/*.tmpl'

# Route tree
route:
  receiver: 'default'
  group_by: ['alertname', 'service', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

  routes:
    # Critical alerts to PagerDuty
    - receiver: 'pagerduty-critical'
      match:
        severity: critical
      group_wait: 10s
      group_interval: 5m
      repeat_interval: 1h

    # Security alerts
    - receiver: 'security-team'
      match:
        category: security
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 2h

    # Business alerts
    - receiver: 'business-team'
      match:
        category: business
      group_wait: 1m
      group_interval: 10m
      repeat_interval: 4h

    # Warning alerts to Slack
    - receiver: 'slack-warnings'
      match:
        severity: warning
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h

    # Info alerts to email
    - receiver: 'email-info'
      match:
        severity: info
      group_wait: 5m
      group_interval: 30m
      repeat_interval: 24h

# Inhibition rules
inhibit_rules:
  # Inhibit warning if critical is firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'service']

  # Inhibit error spike if high error rate is firing
  - source_match:
      alertname: 'HighErrorRate'
    target_match:
      alertname: 'ErrorSpike'
    equal: ['service']

# Receivers
receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        severity: '{{ .CommonLabels.severity }}'
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
        details:
          firing: '{{ .Alerts.Firing | len }}'
          resolved: '{{ .Alerts.Resolved | len }}'
          num_alerts: '{{ .Alerts | len }}'

    slack_configs:
      - channel: '#incidents'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          *Summary:* {{ .Annotations.summary }}
          *Description:* {{ .Annotations.description }}
          *Service:* {{ .Labels.service }}
          *Action:* {{ .Annotations.action }}
          {{ end }}
        color: 'danger'

  - name: 'security-team'
    slack_configs:
      - channel: '#security-alerts'
        title: '🔒 Security Alert: {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          {{ .Annotations.description }}
          *Action:* {{ .Annotations.action }}
          {{ end }}
        color: 'warning'

    email_configs:
      - to: 'security-team@example.com'
        from: 'alertmanager@example.com'
        subject: 'Security Alert: {{ .GroupLabels.alertname }}'
        html: |
          <h2>{{ .GroupLabels.alertname }}</h2>
          {{ range .Alerts }}
          <p><strong>Description:</strong> {{ .Annotations.description }}</p>
          <p><strong>Action:</strong> {{ .Annotations.action }}</p>
          {{ end }}

  - name: 'business-team'
    slack_configs:
      - channel: '#business-alerts'
        title: '💰 Business Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        color: '#FFA500'

    email_configs:
      - to: 'business-team@example.com'
        from: 'alertmanager@example.com'
        subject: 'Business Alert: {{ .GroupLabels.alertname }}'

  - name: 'slack-warnings'
    slack_configs:
      - channel: '#warnings'
        title: '⚠️ Warning: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        color: 'warning'

  - name: 'email-info'
    email_configs:
      - to: 'dev-team@example.com'
        from: 'alertmanager@example.com'
        subject: 'Info: {{ .GroupLabels.alertname }}'
```

## Anomaly Detection

### Statistical Anomaly Detection

```python
# file: scripts/anomaly_detection.py
# version: 1.0.0
# guid: python-anomaly-detection

import numpy as np
from typing import List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests
import structlog

logger = structlog.get_logger()

@dataclass
class Anomaly:
    """Detected anomaly."""
    timestamp: datetime
    value: float
    expected_value: float
    deviation: float
    severity: str

class LogAnomalyDetector:
    """Detect anomalies in log metrics using statistical methods."""

    def __init__(
        self,
        loki_url: str,
        lookback_window: timedelta = timedelta(hours=1),
        baseline_window: timedelta = timedelta(days=7),
        threshold_sigma: float = 3.0,
    ):
        self.loki_url = loki_url
        self.lookback_window = lookback_window
        self.baseline_window = baseline_window
        self.threshold_sigma = threshold_sigma

    def query_loki(
        self,
        query: str,
        start: datetime,
        end: datetime,
    ) -> List[Tuple[datetime, float]]:
        """Query Loki for log metrics."""
        params = {
            'query': query,
            'start': int(start.timestamp() * 1e9),
            'end': int(end.timestamp() * 1e9),
            'step': '1m',
        }

        response = requests.get(
            f"{self.loki_url}/loki/api/v1/query_range",
            params=params,
        )
        response.raise_for_status()

        data = response.json()['data']['result']
        if not data:
            return []

        # Extract values
        values = []
        for result in data:
            for value in result['values']:
                timestamp = datetime.fromtimestamp(float(value[0]))
                metric_value = float(value[1])
                values.append((timestamp, metric_value))

        return values

    def calculate_baseline(
        self,
        query: str,
    ) -> Tuple[float, float]:
        """Calculate baseline mean and std deviation."""
        end = datetime.now()
        start = end - self.baseline_window

        values = self.query_loki(query, start, end)

        if not values:
            logger.warning("No baseline data available", query=query)
            return 0.0, 0.0

        metric_values = [v[1] for v in values]
        mean = np.mean(metric_values)
        std = np.std(metric_values)

        logger.info(
            "Baseline calculated",
            query=query,
            mean=mean,
            std=std,
            samples=len(metric_values),
        )

        return mean, std

    def detect_anomalies(
        self,
        query: str,
        service: str,
    ) -> List[Anomaly]:
        """Detect anomalies in log metrics."""
        # Calculate baseline
        baseline_mean, baseline_std = self.calculate_baseline(query)

        if baseline_std == 0:
            logger.warning("Baseline std is 0, skipping anomaly detection")
            return []

        # Query recent data
        end = datetime.now()
        start = end - self.lookback_window
        values = self.query_loki(query, start, end)

        # Detect anomalies
        anomalies = []
        for timestamp, value in values:
            deviation = abs(value - baseline_mean) / baseline_std

            if deviation > self.threshold_sigma:
                # Determine severity
                if deviation > 5.0:
                    severity = "critical"
                elif deviation > 4.0:
                    severity = "high"
                else:
                    severity = "medium"

                anomaly = Anomaly(
                    timestamp=timestamp,
                    value=value,
                    expected_value=baseline_mean,
                    deviation=deviation,
                    severity=severity,
                )
                anomalies.append(anomaly)

                logger.warning(
                    "Anomaly detected",
                    service=service,
                    timestamp=timestamp.isoformat(),
                    value=value,
                    expected=baseline_mean,
                    deviation=deviation,
                    severity=severity,
                )

        return anomalies

    def run_checks(self) -> List[Anomaly]:
        """Run anomaly detection for all services."""
        checks = [
            {
                'name': 'error_rate',
                'query': 'sum(rate({level="error"}[5m])) by (service)',
                'service': 'all',
            },
            {
                'name': 'request_rate',
                'query': 'sum(rate({job="api"}[5m])) by (service)',
                'service': 'api',
            },
            {
                'name': 'response_time',
                'query': 'quantile_over_time(0.95, {job="api"} | json | unwrap duration_ms [5m]) by (service)',
                'service': 'api',
            },
        ]

        all_anomalies = []
        for check in checks:
            anomalies = self.detect_anomalies(
                check['query'],
                check['service'],
            )
            all_anomalies.extend(anomalies)

        return all_anomalies


def main():
    """Run anomaly detection."""
    detector = LogAnomalyDetector(
        loki_url='http://localhost:3100',
        lookback_window=timedelta(hours=1),
        baseline_window=timedelta(days=7),
        threshold_sigma=3.0,
    )

    anomalies = detector.run_checks()

    if anomalies:
        logger.info(
            "Anomaly detection complete",
            total_anomalies=len(anomalies),
            critical=len([a for a in anomalies if a.severity == 'critical']),
        )
    else:
        logger.info("No anomalies detected")


if __name__ == '__main__':
    main()
```

## Alert Throttling and Deduplication

### Alert Grouping Strategy

````yaml
# file: docs/alerting-strategy.md
# version: 1.0.0
# guid: alerting-strategy-doc

# Alert Throttling and Deduplication Strategy

## Grouping Rules

### By Service and Severity
```yaml
route:
  group_by: ['alertname', 'service', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
````

- **group_wait**: Wait 10s before sending initial notification (allows grouping)
- **group_interval**: Wait 10s before sending updates on same group
- **repeat_interval**: Repeat notification every 12h if still firing

### Time-Based Throttling

**Critical Alerts**:

- First notification: Immediate (10s group_wait)
- Updates: Every 5 minutes
- Repeat: Every 1 hour if unresolved

**Warning Alerts**:

- First notification: After 30s
- Updates: Every 5 minutes
- Repeat: Every 4 hours if unresolved

**Info Alerts**:

- First notification: After 5 minutes
- Updates: Every 30 minutes
- Repeat: Every 24 hours if unresolved

## Deduplication

### By Fingerprint

Alertmanager automatically deduplicates alerts with same:

- Alert name
- Label set
- Annotations (optional)

### Custom Deduplication

```python
# file: scripts/alert_deduplication.py

from typing import Dict, List, Set
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class Alert:
    name: str
    labels: Dict[str, str]
    timestamp: datetime

class AlertDeduplicator:
    """Deduplicate alerts based on custom logic."""

    def __init__(self, window: timedelta = timedelta(minutes=5)):
        self.window = window
        self.seen_alerts: Dict[str, datetime] = {}

    def get_fingerprint(self, alert: Alert) -> str:
        """Generate fingerprint for alert."""
        label_str = ','.join(f"{k}={v}" for k, v in sorted(alert.labels.items()))
        return f"{alert.name}:{label_str}"

    def should_send(self, alert: Alert) -> bool:
        """Check if alert should be sent."""
        fingerprint = self.get_fingerprint(alert)
        now = alert.timestamp

        if fingerprint in self.seen_alerts:
            last_sent = self.seen_alerts[fingerprint]
            if now - last_sent < self.window:
                return False

        self.seen_alerts[fingerprint] = now
        return True
```

## Alert Silencing

### Maintenance Windows

```yaml
# file: config/alertmanager/silences.yml
# version: 1.0.0
# guid: alertmanager-silences

# Silence alerts during maintenance
- matchers:
    - service="payment-service"
  startsAt: '2024-01-15T02:00:00Z'
  endsAt: '2024-01-15T04:00:00Z'
  createdBy: 'ops-team'
  comment: 'Scheduled database maintenance'

# Silence known issue
- matchers:
    - alertname="HighLatency"
    - endpoint="/legacy-api"
  startsAt: '2024-01-10T00:00:00Z'
  endsAt: '2024-02-01T00:00:00Z'
  createdBy: 'dev-team'
  comment: 'Known issue - migration in progress'
```

---

**Part 5 Complete**: Log-based alerting with Loki ruler configuration including error rate alerts
(HighErrorRate >10 errors/sec, ErrorSpike 5x increase, CriticalErrorPattern for fatal errors),
security alerts (authentication failures, unauthorized access attempts, SQL injection detection),
performance alerts (slow database queries >1s, high request latency P95>1s), availability alerts
(ServiceNotLogging, PodRestartLoop), business alerts (payment failures >5%, order processing delays

> 1min), Alertmanager integration with routing by severity (critical to PagerDuty, warnings to
> Slack, info to email), inhibition rules to prevent alert storms, receiver configurations for
> multiple channels, statistical anomaly detection using Z-score with configurable baseline window
> (7 days) and threshold (3 sigma), alert throttling with time-based grouping (critical: 1h repeat,
> warning: 4h, info: 24h), deduplication by fingerprint, alert silencing for maintenance windows. ✅

**Continue to Part 6** for logging best practices, retention policies, and completion checklist.
