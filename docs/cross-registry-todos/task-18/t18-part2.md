<!-- file: docs/cross-registry-todos/task-18/t18-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t18-final-integration-part2-w3x4y5z6-a7b8 -->

# Task 18 Part 2: Unified Monitoring and Observability Dashboard

## Single Pane of Glass Dashboard

### Grafana Unified Dashboard

```json
{
  "dashboard": {
    "title": "Unified Observability - Single Pane of Glass",
    "tags": ["unified", "observability", "sre"],
    "timezone": "browser",
    "refresh": "30s",
    "rows": [
      {
        "title": "System Health Overview",
        "panels": [
          {
            "title": "Service Status",
            "type": "stat",
            "targets": [
              {
                "expr": "up{job=~\"api-service|auth-service|worker-service\"}",
                "legendFormat": "{{job}}"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "thresholds": {
                  "steps": [
                    { "value": 0, "color": "red" },
                    { "value": 1, "color": "green" }
                  ]
                },
                "mappings": [
                  { "value": 0, "text": "Down" },
                  { "value": 1, "text": "Up" }
                ]
              }
            }
          },
          {
            "title": "Active Alerts",
            "type": "stat",
            "targets": [
              {
                "expr": "count(ALERTS{alertstate=\"firing\"})"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "thresholds": {
                  "steps": [
                    { "value": 0, "color": "green" },
                    { "value": 1, "color": "yellow" },
                    { "value": 5, "color": "red" }
                  ]
                }
              }
            }
          },
          {
            "title": "Error Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) by (service)",
                "legendFormat": "{{service}}"
              }
            ],
            "alert": {
              "name": "High Error Rate",
              "conditions": [
                {
                  "evaluator": { "params": [10], "type": "gt" },
                  "query": { "params": ["A", "5m", "now"] },
                  "type": "query"
                }
              ]
            }
          },
          {
            "title": "Request Latency P95",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (service, le))",
                "legendFormat": "{{service}}"
              }
            ],
            "yaxes": [{ "format": "s", "label": "Latency" }]
          }
        ]
      },
      {
        "title": "CI/CD Pipeline Health",
        "panels": [
          {
            "title": "Build Success Rate",
            "type": "stat",
            "targets": [
              {
                "expr": "sum(rate(github_actions_workflow_runs_total{status=\"success\"}[1h])) / sum(rate(github_actions_workflow_runs_total[1h])) * 100"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percent",
                "thresholds": {
                  "steps": [
                    { "value": 0, "color": "red" },
                    { "value": 90, "color": "yellow" },
                    { "value": 95, "color": "green" }
                  ]
                }
              }
            }
          },
          {
            "title": "Deployment Frequency",
            "type": "stat",
            "targets": [
              {
                "expr": "sum(increase(deployments_total[24h]))"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "short",
                "decimals": 0
              }
            }
          },
          {
            "title": "Mean Time to Recovery",
            "type": "stat",
            "targets": [
              {
                "expr": "avg(alert_resolution_duration_seconds) / 60"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "m",
                "thresholds": {
                  "steps": [
                    { "value": 0, "color": "green" },
                    { "value": 30, "color": "yellow" },
                    { "value": 60, "color": "red" }
                  ]
                }
              }
            }
          },
          {
            "title": "Change Failure Rate",
            "type": "stat",
            "targets": [
              {
                "expr": "sum(rate(deployments_total{status=\"failed\"}[24h])) / sum(rate(deployments_total[24h])) * 100"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percent",
                "thresholds": {
                  "steps": [
                    { "value": 0, "color": "green" },
                    { "value": 15, "color": "yellow" },
                    { "value": 30, "color": "red" }
                  ]
                }
              }
            }
          }
        ]
      },
      {
        "title": "SLO Compliance",
        "panels": [
          {
            "title": "Availability SLO (99.9%)",
            "type": "gauge",
            "targets": [
              {
                "expr": "(1 - sum(rate(http_requests_total{status=~\"5..\"}[30d])) / sum(rate(http_requests_total[30d]))) * 100"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percent",
                "min": 99,
                "max": 100,
                "thresholds": {
                  "steps": [
                    { "value": 99, "color": "red" },
                    { "value": 99.5, "color": "yellow" },
                    { "value": 99.9, "color": "green" }
                  ]
                }
              }
            }
          },
          {
            "title": "Latency SLO (<500ms P95)",
            "type": "gauge",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[30d])) by (le)) * 1000"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "ms",
                "min": 0,
                "max": 1000,
                "thresholds": {
                  "steps": [
                    { "value": 0, "color": "green" },
                    { "value": 500, "color": "yellow" },
                    { "value": 800, "color": "red" }
                  ]
                }
              }
            }
          },
          {
            "title": "Error Budget Remaining",
            "type": "stat",
            "targets": [
              {
                "expr": "(1 - (sum(rate(http_requests_total{status=~\"5..\"}[30d])) / sum(rate(http_requests_total[30d]))) - 0.999) / 0.001 * 100"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percent",
                "thresholds": {
                  "steps": [
                    { "value": 0, "color": "red" },
                    { "value": 25, "color": "yellow" },
                    { "value": 50, "color": "green" }
                  ]
                }
              }
            }
          }
        ]
      },
      {
        "title": "Recent Logs with Trace Correlation",
        "panels": [
          {
            "title": "Error Logs",
            "type": "logs",
            "targets": [
              {
                "expr": "{level=\"error\"} |= \"\" | json",
                "refId": "A",
                "datasource": "Loki"
              }
            ],
            "options": {
              "showLabels": true,
              "showTime": true,
              "wrapLogMessage": true,
              "prettifyLogMessage": true,
              "enableLogDetails": true,
              "dedupStrategy": "none",
              "sortOrder": "Descending"
            },
            "transformations": [
              {
                "id": "extractFields",
                "options": {
                  "source": "labels",
                  "replace": false,
                  "keepLabels": ["trace_id", "service", "level"]
                }
              }
            ]
          }
        ]
      },
      {
        "title": "Active Traces",
        "panels": [
          {
            "title": "Trace Search",
            "type": "traces",
            "targets": [
              {
                "query": "",
                "refId": "A",
                "datasource": "Tempo",
                "queryType": "search",
                "serviceName": "",
                "spanName": "",
                "tags": "",
                "minDuration": "",
                "maxDuration": "",
                "limit": 20
              }
            ],
            "options": {
              "columns": ["Service", "Operation", "Duration", "Start Time", "Trace ID"]
            }
          }
        ]
      }
    ],
    "links": [
      {
        "title": "Prometheus",
        "url": "http://prometheus:9090",
        "type": "link",
        "icon": "external link"
      },
      {
        "title": "Jaeger",
        "url": "http://jaeger:16686",
        "type": "link",
        "icon": "external link"
      },
      {
        "title": "Loki",
        "url": "http://loki:3100",
        "type": "link",
        "icon": "external link"
      }
    ],
    "templating": {
      "list": [
        {
          "name": "service",
          "type": "query",
          "query": "label_values(up, job)",
          "refresh": 1,
          "includeAll": true,
          "multi": true
        },
        {
          "name": "environment",
          "type": "custom",
          "query": "production,staging,development",
          "current": {
            "value": "production"
          }
        }
      ]
    }
  }
}
```

## Drill-Down Navigation

### Log to Trace Navigation

```typescript
// file: src/observability/drill-down.ts
// version: 1.0.0
// guid: drill-down-navigation

import { DataLink, DataFrame } from '@grafana/data';

/**
 * Create data link from log to trace
 */
export function createLogToTraceLink(traceId: string): DataLink {
  return {
    title: 'View Trace in Jaeger',
    url: `http://jaeger:16686/trace/${traceId}`,
    targetBlank: true,
  };
}

/**
 * Create data link from metric to logs
 */
export function createMetricToLogsLink(service: string, timestamp: number): DataLink {
  const start = timestamp - 300000; // 5 minutes before
  const end = timestamp + 300000; // 5 minutes after

  const lokiQuery = encodeURIComponent(`{service="${service}"}`);

  return {
    title: 'View Logs in Grafana',
    url: `http://grafana:3000/explore?left={"datasource":"Loki","queries":[{"expr":"${lokiQuery}","refId":"A"}],"range":{"from":"${start}","to":"${end}"}}`,
    targetBlank: true,
  };
}

/**
 * Create data link from trace to logs
 */
export function createTraceToLogsLink(traceId: string, spanId: string): DataLink {
  const lokiQuery = encodeURIComponent(`{} |= "${traceId}"`);

  return {
    title: 'View Related Logs',
    url: `http://grafana:3000/explore?left={"datasource":"Loki","queries":[{"expr":"${lokiQuery}","refId":"A"}]}`,
    targetBlank: true,
  };
}

/**
 * Add exemplar links to metrics
 */
export function addExemplarLinks(dataFrame: DataFrame): DataFrame {
  // Add trace links to exemplars
  if (dataFrame.fields) {
    for (const field of dataFrame.fields) {
      if (field.config && field.config.links) {
        field.config.links.push({
          title: 'View Trace',
          url: 'http://jaeger:16686/trace/${__value.raw}',
          targetBlank: true,
        });
      }
    }
  }

  return dataFrame;
}
```

## Executive Dashboard

### High-Level Metrics for Leadership

```json
{
  "dashboard": {
    "title": "Executive Dashboard - System Health",
    "tags": ["executive", "kpi", "business"],
    "refresh": "5m",
    "rows": [
      {
        "title": "Business Metrics",
        "panels": [
          {
            "title": "System Uptime (30 days)",
            "type": "stat",
            "targets": [
              {
                "expr": "(1 - sum(rate(http_requests_total{status=~\"5..\"}[30d])) / sum(rate(http_requests_total[30d]))) * 100"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percent",
                "decimals": 3,
                "thresholds": {
                  "steps": [
                    { "value": 99, "color": "red" },
                    { "value": 99.9, "color": "yellow" },
                    { "value": 99.99, "color": "green" }
                  ]
                }
              }
            }
          },
          {
            "title": "Requests Per Day",
            "type": "stat",
            "targets": [
              {
                "expr": "sum(increase(http_requests_total[24h]))"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "short",
                "decimals": 0
              }
            }
          },
          {
            "title": "Average Response Time",
            "type": "stat",
            "targets": [
              {
                "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[24h])) by (le)) * 1000"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "ms",
                "decimals": 0,
                "thresholds": {
                  "steps": [
                    { "value": 0, "color": "green" },
                    { "value": 200, "color": "yellow" },
                    { "value": 500, "color": "red" }
                  ]
                }
              }
            }
          },
          {
            "title": "Error Rate",
            "type": "stat",
            "targets": [
              {
                "expr": "sum(rate(http_requests_total{status=~\"5..\"}[24h])) / sum(rate(http_requests_total[24h])) * 100"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percent",
                "decimals": 2,
                "thresholds": {
                  "steps": [
                    { "value": 0, "color": "green" },
                    { "value": 0.5, "color": "yellow" },
                    { "value": 1, "color": "red" }
                  ]
                }
              }
            }
          }
        ]
      },
      {
        "title": "Development Velocity",
        "panels": [
          {
            "title": "Deployments (7 days)",
            "type": "stat",
            "targets": [
              {
                "expr": "sum(increase(deployments_total[7d]))"
              }
            ]
          },
          {
            "title": "Deployment Success Rate",
            "type": "gauge",
            "targets": [
              {
                "expr": "sum(rate(deployments_total{status=\"success\"}[7d])) / sum(rate(deployments_total[7d])) * 100"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percent",
                "min": 0,
                "max": 100
              }
            }
          },
          {
            "title": "Mean Lead Time",
            "type": "stat",
            "targets": [
              {
                "expr": "avg(deployment_lead_time_seconds) / 3600"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "h"
              }
            }
          },
          {
            "title": "MTTR",
            "type": "stat",
            "targets": [
              {
                "expr": "avg(alert_resolution_duration_seconds) / 60"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "m"
              }
            }
          }
        ]
      },
      {
        "title": "Cost Efficiency",
        "panels": [
          {
            "title": "Infrastructure Cost (Monthly)",
            "type": "stat",
            "targets": [
              {
                "expr": "sum(aws_billing_estimated_charges) by (service)"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "currencyUSD"
              }
            }
          },
          {
            "title": "Cost Per Request",
            "type": "stat",
            "targets": [
              {
                "expr": "sum(aws_billing_estimated_charges) / sum(increase(http_requests_total[30d]))"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "currencyUSD",
                "decimals": 6
              }
            }
          },
          {
            "title": "Resource Utilization",
            "type": "gauge",
            "targets": [
              {
                "expr": "avg(container_cpu_usage_seconds_total) * 100"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percent",
                "min": 0,
                "max": 100
              }
            }
          }
        ]
      },
      {
        "title": "Security Posture",
        "panels": [
          {
            "title": "Critical Vulnerabilities",
            "type": "stat",
            "targets": [
              {
                "expr": "sum(vulnerability_count{severity=\"critical\"})"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "thresholds": {
                  "steps": [
                    { "value": 0, "color": "green" },
                    { "value": 1, "color": "red" }
                  ]
                }
              }
            }
          },
          {
            "title": "Failed Login Attempts",
            "type": "graph",
            "targets": [
              {
                "expr": "sum(rate(auth_failures_total[1h]))"
              }
            ]
          },
          {
            "title": "Security Incidents (30 days)",
            "type": "stat",
            "targets": [
              {
                "expr": "sum(increase(security_incidents_total[30d]))"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

---

**Part 2 Complete**: Unified monitoring dashboard with single pane of glass Grafana configuration
showing system health (service status, active alerts, error rate, latency P95), CI/CD pipeline
health (build success rate >95%, deployment frequency, MTTR <30min, change failure rate <15%), SLO
compliance (availability 99.9%, latency <500ms P95, error budget remaining), integrated log panel
with trace correlation links, active traces panel with search capabilities, drill-down navigation
with log-to-trace links using trace IDs, metric-to-logs links with time range context, trace-to-logs
correlation, exemplar links from Prometheus metrics to Jaeger traces, executive dashboard with
business metrics (uptime 99.99%, requests per day, response time <200ms, error rate <0.5%),
development velocity (deployment frequency, success rate, lead time, MTTR), cost efficiency
(infrastructure cost, cost per request, resource utilization), and security posture (critical
vulnerabilities, failed logins, security incidents). ✅

**Continue to Part 3** for comprehensive troubleshooting guide with common failure scenarios and
diagnostic workflows.
