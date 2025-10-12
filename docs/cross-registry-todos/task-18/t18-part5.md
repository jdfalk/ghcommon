# Task 18 Part 5: Project Dashboards and Team Metrics

## Overview

This section provides comprehensive dashboards for tracking project health, cost efficiency, and
team productivity. These dashboards complement the operational monitoring covered in previous parts
by focusing on business metrics, development velocity, and resource optimization.

---

## CI/CD Health Dashboard

### Build Success Rate Over Time

Track the overall health of your CI/CD pipeline by monitoring build success rates across all
repositories and branches.

**Grafana Dashboard Panel - Build Success Rate**

```json
{
  "id": 1,
  "title": "Build Success Rate (7 Days)",
  "type": "graph",
  "targets": [
    {
      "expr": "sum(rate(github_workflow_run_conclusion_success_total[7d])) / sum(rate(github_workflow_run_conclusion_total[7d])) * 100",
      "legendFormat": "Overall Success Rate",
      "refId": "A"
    },
    {
      "expr": "sum(rate(github_workflow_run_conclusion_success_total{workflow='ci.yml'}[7d])) / sum(rate(github_workflow_run_conclusion_total{workflow='ci.yml'}[7d])) * 100",
      "legendFormat": "CI Workflow",
      "refId": "B"
    },
    {
      "expr": "sum(rate(github_workflow_run_conclusion_success_total{workflow='release.yml'}[7d])) / sum(rate(github_workflow_run_conclusion_total{workflow='release.yml'}[7d])) * 100",
      "legendFormat": "Release Workflow",
      "refId": "C"
    }
  ],
  "yaxes": [
    {
      "format": "percent",
      "label": "Success Rate",
      "min": 0,
      "max": 100
    }
  ],
  "alert": {
    "conditions": [
      {
        "evaluator": {
          "params": [95],
          "type": "lt"
        },
        "operator": {
          "type": "and"
        },
        "query": {
          "params": ["A", "5m", "now"]
        },
        "reducer": {
          "params": [],
          "type": "avg"
        },
        "type": "query"
      }
    ],
    "executionErrorState": "alerting",
    "frequency": "5m",
    "handler": 1,
    "name": "Build Success Rate Below 95%",
    "noDataState": "no_data",
    "notifications": [
      {
        "uid": "slack-engineering"
      }
    ]
  }
}
```

**Success Criteria:**

- Overall success rate > 95%
- CI workflow success rate > 98%
- Release workflow success rate > 90%
- Alert triggers if below 95% for 5 minutes

### Average Build Duration Trend

Monitor build performance to identify bottlenecks and optimize CI/CD pipeline efficiency.

**Prometheus Queries**

```promql
# Average build duration by workflow
avg(github_workflow_run_duration_seconds) by (workflow)

# P95 build duration
histogram_quantile(0.95, sum(rate(github_workflow_run_duration_bucket[1h])) by (le, workflow))

# Build duration trend (24 hour moving average)
avg_over_time(github_workflow_run_duration_seconds[24h])

# Slowest workflows (last 7 days)
topk(5, avg(github_workflow_run_duration_seconds{conclusion="success"}) by (workflow))
```

**Grafana Stat Panel - Build Duration**

```json
{
  "id": 2,
  "title": "Average Build Duration",
  "type": "stat",
  "targets": [
    {
      "expr": "avg(github_workflow_run_duration_seconds{conclusion='success'})",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "s",
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {
            "color": "green",
            "value": null
          },
          {
            "color": "yellow",
            "value": 300
          },
          {
            "color": "red",
            "value": 600
          }
        ]
      },
      "mappings": []
    }
  },
  "options": {
    "colorMode": "background",
    "graphMode": "area",
    "justifyMode": "auto",
    "orientation": "auto",
    "reduceOptions": {
      "calcs": ["lastNotNull"],
      "fields": "",
      "values": false
    },
    "textMode": "auto"
  }
}
```

**Performance Targets:**

- Average build duration < 5 minutes
- P95 build duration < 10 minutes
- No builds > 15 minutes
- 10% improvement quarter over quarter

### Test Execution Time by Suite

Track test suite performance to identify slow tests and optimize test execution.

**Test Execution Breakdown**

```json
{
  "id": 3,
  "title": "Test Execution Time by Suite",
  "type": "bargauge",
  "targets": [
    {
      "expr": "avg(test_suite_duration_seconds) by (suite, language)",
      "legendFormat": "{{language}} - {{suite}}",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "s",
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {
            "color": "green",
            "value": null
          },
          {
            "color": "yellow",
            "value": 60
          },
          {
            "color": "red",
            "value": 180
          }
        ]
      }
    }
  },
  "options": {
    "displayMode": "gradient",
    "orientation": "horizontal",
    "reduceOptions": {
      "calcs": ["lastNotNull"],
      "fields": "",
      "values": false
    },
    "showUnfilled": true
  }
}
```

**Example Test Suite Metrics**

| Language   | Suite       | Avg Duration | P95 Duration | Test Count | Flaky Rate |
| ---------- | ----------- | ------------ | ------------ | ---------- | ---------- |
| Rust       | Unit Tests  | 45s          | 62s          | 1,247      | 0.5%       |
| Rust       | Integration | 120s         | 180s         | 89         | 1.2%       |
| Python     | Unit Tests  | 30s          | 45s          | 892        | 0.8%       |
| Python     | Integration | 90s          | 135s         | 67         | 2.1%       |
| JavaScript | Unit Tests  | 25s          | 38s          | 1,456      | 0.3%       |
| JavaScript | E2E Tests   | 240s         | 360s         | 34         | 4.5%       |
| Go         | Unit Tests  | 20s          | 30s          | 678        | 0.2%       |
| Go         | Integration | 75s          | 110s         | 45         | 1.8%       |

**Optimization Priorities:**

1. JavaScript E2E tests (4.5% flaky rate - highest)
2. Python integration tests (90s average - optimize database setup)
3. Rust integration tests (120s average - consider parallelization)

### Deployment Frequency Histogram

Visualize deployment patterns to track development velocity and release cadence.

**Deployment Frequency Panel**

```json
{
  "id": 4,
  "title": "Deployment Frequency",
  "type": "graph",
  "targets": [
    {
      "expr": "sum(increase(deployment_total[1d])) by (environment)",
      "legendFormat": "{{environment}} (daily)",
      "refId": "A"
    },
    {
      "expr": "sum(increase(deployment_total[7d])) by (environment)",
      "legendFormat": "{{environment}} (weekly)",
      "refId": "B"
    },
    {
      "expr": "sum(increase(deployment_total[30d])) by (environment)",
      "legendFormat": "{{environment}} (monthly)",
      "refId": "C"
    }
  ],
  "xaxis": {
    "mode": "time",
    "show": true
  },
  "yaxes": [
    {
      "format": "short",
      "label": "Deployments",
      "min": 0
    }
  ],
  "bars": true,
  "lines": false
}
```

**DORA Metrics - Deployment Frequency**

```python
# Python script to calculate DORA deployment frequency metrics
import datetime
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class DeploymentMetrics:
    """DORA metrics for deployment frequency."""

    daily_avg: float
    weekly_avg: float
    monthly_total: int
    peak_day: str
    dora_level: str

    def calculate_dora_level(self) -> str:
        """Determine DORA maturity level based on deployment frequency."""
        if self.daily_avg >= 1:
            return "Elite"
        elif self.weekly_avg >= 1:
            return "High"
        elif self.monthly_total >= 1:
            return "Medium"
        else:
            return "Low"

def calculate_deployment_metrics(deployments: List[Dict]) -> DeploymentMetrics:
    """Calculate deployment frequency metrics from deployment history."""

    # Group deployments by date
    deployments_by_date = {}
    for deployment in deployments:
        date = deployment['timestamp'].date()
        deployments_by_date[date] = deployments_by_date.get(date, 0) + 1

    # Calculate averages
    total_days = 30
    daily_avg = len(deployments) / total_days
    weekly_avg = (len(deployments) / total_days) * 7
    monthly_total = len(deployments)

    # Find peak deployment day
    peak_day = max(deployments_by_date.items(), key=lambda x: x[1])

    metrics = DeploymentMetrics(
        daily_avg=daily_avg,
        weekly_avg=weekly_avg,
        monthly_total=monthly_total,
        peak_day=peak_day[0].strftime("%Y-%m-%d"),
        dora_level=""
    )

    metrics.dora_level = metrics.calculate_dora_level()

    return metrics

# Example usage
example_metrics = DeploymentMetrics(
    daily_avg=2.3,
    weekly_avg=16.1,
    monthly_total=69,
    peak_day="2024-01-15",
    dora_level="Elite"
)

print(f"Deployment Frequency: {example_metrics.daily_avg:.1f} per day")
print(f"DORA Level: {example_metrics.dora_level}")
```

**Deployment Frequency Targets by Environment:**

- **Production**: 10+ deployments per week (Elite)
- **Staging**: 20+ deployments per week
- **Development**: 50+ deployments per week

### Change Failure Rate Trend

Monitor deployment quality by tracking failed deployments and rollbacks.

**Change Failure Rate Query**

```promql
# Change failure rate (failed deployments / total deployments)
sum(rate(deployment_total{status="failed"}[7d])) / sum(rate(deployment_total[7d])) * 100

# Rollback rate
sum(rate(deployment_rollback_total[7d])) / sum(rate(deployment_total[7d])) * 100

# Combined failure rate (failures + rollbacks)
(sum(rate(deployment_total{status="failed"}[7d])) + sum(rate(deployment_rollback_total[7d]))) / sum(rate(deployment_total[7d])) * 100
```

**Grafana Panel - Change Failure Rate**

```json
{
  "id": 5,
  "title": "Change Failure Rate",
  "type": "graph",
  "targets": [
    {
      "expr": "(sum(rate(deployment_total{status='failed'}[7d])) + sum(rate(deployment_rollback_total[7d]))) / sum(rate(deployment_total[7d])) * 100",
      "legendFormat": "Change Failure Rate",
      "refId": "A"
    }
  ],
  "yaxes": [
    {
      "format": "percent",
      "label": "Failure Rate",
      "min": 0,
      "max": 20
    }
  ],
  "thresholds": [
    {
      "value": 15,
      "colorMode": "critical",
      "op": "gt",
      "fill": true,
      "line": true
    }
  ],
  "alert": {
    "conditions": [
      {
        "evaluator": {
          "params": [15],
          "type": "gt"
        },
        "query": {
          "params": ["A", "1h", "now"]
        },
        "reducer": {
          "type": "avg"
        },
        "type": "query"
      }
    ],
    "name": "High Change Failure Rate",
    "notifications": [
      {
        "uid": "slack-engineering"
      }
    ]
  }
}
```

**DORA Change Failure Rate Targets:**

- **Elite**: < 5%
- **High**: 5-10%
- **Medium**: 10-15%
- **Low**: > 15%

### Mean Lead Time (Commit to Production)

Track development velocity by measuring the time from commit to production deployment.

**Lead Time Calculation**

```typescript
// TypeScript interface for lead time tracking
interface LeadTimeMetrics {
  commitToMerge: number; // Time from commit to PR merge (minutes)
  mergeToStaging: number; // Time from merge to staging deployment (minutes)
  stagingToProduction: number; // Time from staging to production (minutes)
  totalLeadTime: number; // Total time commit to production (minutes)
  doraLevel: 'Elite' | 'High' | 'Medium' | 'Low';
}

function calculateLeadTime(
  commitTimestamp: Date,
  mergeTimestamp: Date,
  stagingTimestamp: Date,
  productionTimestamp: Date
): LeadTimeMetrics {
  const commitToMerge = (mergeTimestamp.getTime() - commitTimestamp.getTime()) / 1000 / 60;
  const mergeToStaging = (stagingTimestamp.getTime() - mergeTimestamp.getTime()) / 1000 / 60;
  const stagingToProduction =
    (productionTimestamp.getTime() - stagingTimestamp.getTime()) / 1000 / 60;
  const totalLeadTime = commitToMerge + mergeToStaging + stagingToProduction;

  let doraLevel: 'Elite' | 'High' | 'Medium' | 'Low';
  if (totalLeadTime < 60) {
    // < 1 hour
    doraLevel = 'Elite';
  } else if (totalLeadTime < 1440) {
    // < 1 day
    doraLevel = 'High';
  } else if (totalLeadTime < 10080) {
    // < 1 week
    doraLevel = 'Medium';
  } else {
    doraLevel = 'Low';
  }

  return {
    commitToMerge,
    mergeToStaging,
    stagingToProduction,
    totalLeadTime,
    doraLevel,
  };
}

// Prometheus query for lead time
const leadTimeQuery = `
  histogram_quantile(0.50,
    sum(rate(deployment_lead_time_seconds_bucket[7d])) by (le)
  ) / 60
`;

// Example metrics
const exampleLeadTime: LeadTimeMetrics = {
  commitToMerge: 45, // 45 minutes for code review
  mergeToStaging: 10, // 10 minutes to deploy to staging
  stagingToProduction: 30, // 30 minutes for validation + prod deploy
  totalLeadTime: 85, // 1 hour 25 minutes total
  doraLevel: 'High',
};
```

**Lead Time Breakdown Dashboard**

```json
{
  "id": 6,
  "title": "Mean Lead Time Breakdown",
  "type": "piechart",
  "targets": [
    {
      "expr": "avg(lead_time_commit_to_merge_minutes)",
      "legendFormat": "Code Review",
      "refId": "A"
    },
    {
      "expr": "avg(lead_time_merge_to_staging_minutes)",
      "legendFormat": "Staging Deploy",
      "refId": "B"
    },
    {
      "expr": "avg(lead_time_staging_to_prod_minutes)",
      "legendFormat": "Production Deploy",
      "refId": "C"
    }
  ],
  "options": {
    "legend": {
      "displayMode": "table",
      "placement": "right",
      "values": ["value", "percent"]
    },
    "pieType": "pie",
    "tooltip": {
      "mode": "single"
    }
  }
}
```

**Lead Time Targets:**

- **Total lead time**: < 2 hours (Elite)
- **Code review time**: < 30 minutes
- **CI/CD pipeline**: < 10 minutes
- **Staging validation**: < 20 minutes
- **Production deployment**: < 15 minutes

### Rollback Frequency

Track deployment stability by monitoring rollback frequency and reasons.

**Rollback Metrics Dashboard**

```json
{
  "id": 7,
  "title": "Rollback Frequency by Reason",
  "type": "table",
  "targets": [
    {
      "expr": "sum(increase(deployment_rollback_total[7d])) by (reason)",
      "format": "table",
      "instant": true,
      "refId": "A"
    }
  ],
  "transformations": [
    {
      "id": "organize",
      "options": {
        "excludeByName": {
          "Time": true
        },
        "indexByName": {
          "reason": 0,
          "Value": 1
        },
        "renameByName": {
          "reason": "Rollback Reason",
          "Value": "Count (7 days)"
        }
      }
    }
  ],
  "fieldConfig": {
    "defaults": {
      "custom": {
        "align": "left",
        "displayMode": "color-background"
      },
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {
            "color": "green",
            "value": null
          },
          {
            "color": "yellow",
            "value": 5
          },
          {
            "color": "red",
            "value": 10
          }
        ]
      }
    }
  }
}
```

**Common Rollback Reasons:**

- High error rate (> 1%)
- Performance degradation (P95 latency > 1000ms)
- Failed health checks
- Database migration failure
- Configuration error
- Dependency incompatibility

---

## Cost Efficiency Tracking

### Infrastructure Cost Breakdown by Service

Monitor cloud spending to identify cost optimization opportunities.

**Cost Attribution Dashboard**

```json
{
  "id": 8,
  "title": "Infrastructure Cost Breakdown",
  "type": "piechart",
  "targets": [
    {
      "expr": "sum(cloud_cost_usd) by (service)",
      "legendFormat": "{{service}}",
      "refId": "A"
    }
  ],
  "options": {
    "legend": {
      "displayMode": "table",
      "placement": "right",
      "values": ["value", "percent"]
    },
    "pieType": "donut",
    "tooltip": {
      "mode": "multi"
    }
  }
}
```

**Example Cost Breakdown (Monthly)**

| Service Category | Monthly Cost | % of Total | Trend    | Optimization Opportunity  |
| ---------------- | ------------ | ---------- | -------- | ------------------------- |
| Compute (EC2)    | $4,200       | 35%        | ↑ 5%     | Rightsize instances       |
| Kubernetes (EKS) | $3,800       | 32%        | ↔ 0%    | None                      |
| Database (RDS)   | $2,100       | 17%        | ↓ 3%     | Read replica optimization |
| Storage (S3/EBS) | $1,200       | 10%        | ↑ 8%     | Lifecycle policies        |
| Networking       | $500         | 4%         | ↔ 0%    | None                      |
| Monitoring       | $200         | 2%         | ↔ 0%    | None                      |
| **Total**        | **$12,000**  | **100%**   | **↑ 2%** |                           |

### Cost Per Request Calculation

Track unit economics by calculating cost per request/transaction.

**Cost Per Request Python Script**

```python
#!/usr/bin/env python3
# file: scripts/calculate_cost_per_request.py
# version: 1.0.0
# guid: 7c8d9e0f-1a2b-3c4d-5e6f-7a8b9c0d1e2f

"""
Calculate cost per request metrics for cost efficiency tracking.
"""

from dataclasses import dataclass
from typing import Dict
import datetime

@dataclass
class CostMetrics:
    """Cost efficiency metrics."""

    total_requests: int
    total_cost_usd: float
    cost_per_request: float
    cost_per_1k_requests: float
    cost_per_user: float
    efficiency_score: float

def calculate_cost_per_request(
    total_cost: float,
    total_requests: int,
    active_users: int
) -> CostMetrics:
    """Calculate cost efficiency metrics."""

    cost_per_request = total_cost / total_requests if total_requests > 0 else 0
    cost_per_1k_requests = cost_per_request * 1000
    cost_per_user = total_cost / active_users if active_users > 0 else 0

    # Efficiency score (lower is better)
    # Target: $0.001 per request = 100% efficiency
    target_cost = 0.001
    efficiency_score = (target_cost / cost_per_request * 100) if cost_per_request > 0 else 0

    return CostMetrics(
        total_requests=total_requests,
        total_cost_usd=total_cost,
        cost_per_request=cost_per_request,
        cost_per_1k_requests=cost_per_1k_requests,
        cost_per_user=cost_per_user,
        efficiency_score=efficiency_score
    )

# Example calculation
example_metrics = calculate_cost_per_request(
    total_cost=12000.0,  # $12,000 monthly cost
    total_requests=15_000_000,  # 15M requests per month
    active_users=50_000  # 50K active users
)

print(f"Cost per request: ${example_metrics.cost_per_request:.4f}")
print(f"Cost per 1K requests: ${example_metrics.cost_per_1k_requests:.2f}")
print(f"Cost per user: ${example_metrics.cost_per_user:.2f}")
print(f"Efficiency score: {example_metrics.efficiency_score:.1f}%")
```

**Prometheus Query for Cost Per Request**

```promql
# Cost per request (last 30 days)
sum(cloud_cost_usd) / sum(http_requests_total)

# Cost per request by service
sum(cloud_cost_usd) by (service) / sum(http_requests_total) by (service)

# Trending cost per request (7-day moving average)
avg_over_time(
  (sum(cloud_cost_usd) / sum(http_requests_total))[7d:]
)
```

### Resource Utilization Efficiency

Monitor CPU and memory utilization to identify underutilized resources.

**Resource Utilization Dashboard**

```json
{
  "id": 9,
  "title": "Resource Utilization Efficiency",
  "type": "graph",
  "targets": [
    {
      "expr": "avg(container_cpu_usage_seconds_total) / avg(container_spec_cpu_quota) * 100",
      "legendFormat": "CPU Utilization",
      "refId": "A"
    },
    {
      "expr": "avg(container_memory_working_set_bytes) / avg(container_spec_memory_limit_bytes) * 100",
      "legendFormat": "Memory Utilization",
      "refId": "B"
    }
  ],
  "yaxes": [
    {
      "format": "percent",
      "label": "Utilization",
      "min": 0,
      "max": 100
    }
  ],
  "thresholds": [
    {
      "value": 30,
      "colorMode": "custom",
      "fillColor": "rgba(255, 152, 0, 0.2)",
      "op": "lt",
      "line": true
    },
    {
      "value": 80,
      "colorMode": "custom",
      "fillColor": "rgba(255, 82, 82, 0.2)",
      "op": "gt",
      "line": true
    }
  ]
}
```

**Efficiency Targets:**

- **Optimal range**: 50-70% utilization
- **Underutilized**: < 30% (candidate for rightsizing)
- **Overutilized**: > 80% (candidate for scaling up)

**Rightsizing Recommendations Query**

```promql
# Pods with low CPU utilization (< 30%) - candidates for downsizing
topk(10,
  avg(rate(container_cpu_usage_seconds_total[7d])) by (pod, namespace)
  / on(pod, namespace) group_left
  avg(container_spec_cpu_quota) by (pod, namespace)
) < 0.30

# Pods with high memory allocation but low usage - waste detection
topk(10,
  (avg(container_spec_memory_limit_bytes) by (pod, namespace)
   - avg(container_memory_working_set_bytes) by (pod, namespace))
  / avg(container_spec_memory_limit_bytes) by (pod, namespace)
) > 0.50
```

### Budget Alerts and Forecasting

Implement proactive budget monitoring with forecasting and alerts.

**Budget Forecasting Script**

```python
#!/usr/bin/env python3
# file: scripts/budget_forecasting.py
# version: 1.0.0
# guid: 8d9e0f1a-2b3c-4d5e-6f7a-8b9c0d1e2f3a

"""
Budget forecasting and alerting for cost management.
"""

from dataclasses import dataclass
from typing import List
import datetime

@dataclass
class BudgetAlert:
    """Budget alert configuration and status."""

    monthly_budget: float
    current_spend: float
    days_elapsed: int
    days_in_month: int
    projected_spend: float
    budget_remaining: float
    utilization_pct: float
    alert_level: str

    def calculate_projection(self) -> float:
        """Project end-of-month spend based on current burn rate."""
        daily_burn = self.current_spend / self.days_elapsed if self.days_elapsed > 0 else 0
        return daily_burn * self.days_in_month

    def get_alert_level(self) -> str:
        """Determine alert level based on budget utilization."""
        if self.utilization_pct >= 100:
            return "CRITICAL"
        elif self.utilization_pct >= 90:
            return "WARNING"
        elif self.utilization_pct >= 80:
            return "INFO"
        else:
            return "OK"

def check_budget_status(
    monthly_budget: float,
    current_spend: float,
    current_date: datetime.date
) -> BudgetAlert:
    """Check budget status and return alert if needed."""

    days_elapsed = current_date.day
    days_in_month = 30  # Approximate

    projected_spend = (current_spend / days_elapsed) * days_in_month
    budget_remaining = monthly_budget - current_spend
    utilization_pct = (current_spend / monthly_budget) * 100

    alert = BudgetAlert(
        monthly_budget=monthly_budget,
        current_spend=current_spend,
        days_elapsed=days_elapsed,
        days_in_month=days_in_month,
        projected_spend=projected_spend,
        budget_remaining=budget_remaining,
        utilization_pct=utilization_pct,
        alert_level=""
    )

    alert.alert_level = alert.get_alert_level()

    return alert

# Example usage
example_alert = check_budget_status(
    monthly_budget=15000.0,
    current_spend=11500.0,
    current_date=datetime.date(2024, 1, 20)
)

print(f"Budget Utilization: {example_alert.utilization_pct:.1f}%")
print(f"Projected Spend: ${example_alert.projected_spend:,.2f}")
print(f"Alert Level: {example_alert.alert_level}")
```

**Budget Alert Thresholds:**

- **INFO**: 80% of budget consumed
- **WARNING**: 90% of budget consumed or projected overspend
- **CRITICAL**: 100% of budget consumed

---

## Team Productivity Metrics

### Engineering Dashboard

Track team performance with key development metrics.

**Pull Requests Merged Per Day/Week**

```promql
# PRs merged per day
sum(increase(github_pull_requests_merged_total[1d]))

# PRs merged per week by team
sum(increase(github_pull_requests_merged_total[7d])) by (team)

# Average PR size (lines changed)
avg(github_pull_request_changed_lines) by (repository)
```

**Grafana Dashboard - Team Productivity**

```json
{
  "id": 10,
  "title": "Team Productivity Overview",
  "type": "row",
  "panels": [
    {
      "id": 11,
      "title": "PRs Merged (7 Days)",
      "type": "stat",
      "targets": [
        {
          "expr": "sum(increase(github_pull_requests_merged_total[7d]))",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": {
            "steps": [
              { "color": "red", "value": null },
              { "color": "yellow", "value": 20 },
              { "color": "green", "value": 40 }
            ]
          }
        }
      }
    },
    {
      "id": 12,
      "title": "Average PR Size",
      "type": "stat",
      "targets": [
        {
          "expr": "avg(github_pull_request_changed_lines)",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": {
            "steps": [
              { "color": "green", "value": null },
              { "color": "yellow", "value": 300 },
              { "color": "red", "value": 500 }
            ]
          }
        }
      }
    }
  ]
}
```

### Issues Resolved with Categorization

Track issue resolution by type to understand team focus areas.

**Issue Resolution Metrics**

| Category      | Resolved (7d) | Avg Time to Close | Priority Distribution |
| ------------- | ------------- | ----------------- | --------------------- |
| Bug           | 23            | 2.3 days          | P0: 2, P1: 8, P2: 13  |
| Feature       | 15            | 5.7 days          | P0: 0, P1: 6, P2: 9   |
| Tech Debt     | 8             | 8.2 days          | P1: 3, P2: 5          |
| Documentation | 5             | 1.8 days          | P2: 5                 |
| Security      | 3             | 0.5 days          | P0: 3                 |

### Code Review Turnaround Time

Monitor code review efficiency to identify bottlenecks in development workflow.

**Code Review Metrics Dashboard**

```json
{
  "id": 13,
  "title": "Code Review Turnaround Time",
  "type": "graph",
  "targets": [
    {
      "expr": "histogram_quantile(0.50, sum(rate(github_pull_request_review_time_bucket[7d])) by (le))",
      "legendFormat": "P50 Review Time",
      "refId": "A"
    },
    {
      "expr": "histogram_quantile(0.95, sum(rate(github_pull_request_review_time_bucket[7d])) by (le))",
      "legendFormat": "P95 Review Time",
      "refId": "B"
    }
  ],
  "yaxes": [
    {
      "format": "h",
      "label": "Review Time",
      "min": 0
    }
  ]
}
```

**Review Turnaround Targets:**

- **P50**: < 4 hours
- **P95**: < 24 hours
- **Critical PRs**: < 2 hours

### Incident Response Metrics

Track incident management effectiveness with MTTR, MTBF, and incident counts.

**Incident Metrics Table**

| Severity | Count (30d) | MTTR    | MTBF   | Primary Cause        |
| -------- | ----------- | ------- | ------ | -------------------- |
| P0       | 2           | 45 min  | 15 d   | Database connection  |
| P1       | 8           | 2.5 hrs | 3.75 d | Memory leak          |
| P2       | 23          | 4 hrs   | 1.3 d  | Configuration errors |
| P3       | 67          | 8 hrs   | 11 hrs | Minor bugs           |

**MTTR Calculation**

```python
# Mean Time To Resolution
def calculate_mttr(incidents: List[Dict]) -> float:
    """Calculate MTTR in minutes."""
    total_resolution_time = sum(
        (i['resolved_at'] - i['created_at']).total_seconds() / 60
        for i in incidents
    )
    return total_resolution_time / len(incidents) if incidents else 0

# Mean Time Between Failures
def calculate_mtbf(incidents: List[Dict], observation_period_days: int) -> float:
    """Calculate MTBF in days."""
    incident_count = len(incidents)
    return observation_period_days / incident_count if incident_count > 0 else float('inf')
```

### On-Call Statistics

Monitor on-call burden and identify opportunities to reduce after-hours incidents.

**On-Call Metrics Dashboard**

```json
{
  "id": 14,
  "title": "On-Call Statistics",
  "type": "table",
  "targets": [
    {
      "expr": "sum(increase(pagerduty_incidents_total[30d])) by (severity, time_of_day)",
      "format": "table",
      "refId": "A"
    }
  ]
}
```

**On-Call Burden Analysis**

| Engineer     | Total Pages | Business Hours | After Hours | Weekend       | Avg Response Time |
| ------------ | ----------- | -------------- | ----------- | ------------- | ----------------- |
| Alice        | 12          | 8 (67%)        | 3 (25%)     | 1 (8%)        | 3.2 min           |
| Bob          | 15          | 9 (60%)        | 5 (33%)     | 1 (7%)        | 2.8 min           |
| Charlie      | 9           | 7 (78%)        | 2 (22%)     | 0 (0%)        | 4.1 min           |
| Diana        | 18          | 11 (61%)       | 6 (33%)     | 1 (6%)        | 2.5 min           |
| **Team Avg** | **13.5**    | **8.75 (65%)** | **4 (30%)** | **0.75 (5%)** | **3.2 min**       |

**Goals for On-Call Health:**

- < 5 pages per week per engineer
- < 20% of pages after business hours
- < 5% of pages on weekends
- Response time < 5 minutes

### Deployment Lead Time Per Engineer/Team

Track individual and team velocity to identify high performers and coaching opportunities.

**Engineer Performance Dashboard**

```json
{
  "id": 15,
  "title": "Deployment Lead Time by Engineer",
  "type": "bargauge",
  "targets": [
    {
      "expr": "avg(deployment_lead_time_minutes) by (engineer)",
      "legendFormat": "{{engineer}}",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "m",
      "thresholds": {
        "steps": [
          { "color": "green", "value": null },
          { "color": "yellow", "value": 120 },
          { "color": "red", "value": 240 }
        ]
      }
    }
  }
}
```

**Team Velocity Comparison**

| Team        | Avg Lead Time | Deployments/Week | PRs/Week | Code Review Time |
| ----------- | ------------- | ---------------- | -------- | ---------------- |
| Backend     | 95 min        | 18               | 24       | 3.2 hrs          |
| Frontend    | 110 min       | 15               | 20       | 4.1 hrs          |
| Platform    | 140 min       | 12               | 16       | 5.5 hrs          |
| Data        | 180 min       | 8                | 12       | 6.2 hrs          |
| **Company** | **131 min**   | **13.25**        | **18**   | **4.75 hrs**     |

---

## Summary

Task 18 Part 5 provides comprehensive project dashboards covering:

1. **CI/CD Health Metrics**: Build success rates, duration trends, test execution times, deployment
   frequency, change failure rates, lead time, and rollback tracking
2. **Cost Efficiency**: Infrastructure cost breakdowns, cost per request calculations, resource
   utilization monitoring, and budget forecasting with alerts
3. **Team Productivity**: PR merge rates, issue resolution tracking, code review turnaround times,
   incident response metrics (MTTR/MTBF), on-call statistics, and deployment velocity

These dashboards enable data-driven decision making for optimizing development processes,
controlling costs, and improving team performance.

**Next**: Part 6 will provide the completion summary covering all 18 tasks with line counts and
success criteria validation.
