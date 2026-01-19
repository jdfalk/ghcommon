<!-- file: docs/cross-registry-todos/task-15/t15-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t15-performance-monitoring-part4-i9j0k1l2-m3n4 -->
<!-- last-edited: 2026-01-19 -->

# Task 15 Part 4: Grafana Dashboards and Visualization

## Grafana Configuration

### Grafana Provisioning

```yaml
# file: configs/grafana/provisioning/datasources/prometheus.yml
# version: 1.0.0
# guid: grafana-datasource-prometheus

apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: '15s'
      queryTimeout: '60s'
      httpMethod: POST

  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686
    editable: false

  - name: Pyroscope
    type: phlare
    access: proxy
    url: http://pyroscope:4040
    editable: false
```

```yaml
# file: configs/grafana/provisioning/dashboards/default.yml
# version: 1.0.0
# guid: grafana-dashboard-provisioning

apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/dashboards
```

## Application Performance Dashboard

```json
{
  "comment": "file: configs/grafana/dashboards/application-performance.json",
  "comment": "version: 1.0.0",
  "comment": "guid: grafana-app-performance-dashboard",

  "dashboard": {
    "title": "Application Performance",
    "tags": ["application", "performance"],
    "timezone": "browser",
    "refresh": "30s",
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{service}} - {{method}} {{route}}"
          }
        ],
        "yaxes": [
          { "format": "reqps", "label": "Requests/s" },
          { "format": "short" }
        ]
      },
      {
        "id": 2,
        "title": "Error Rate",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 0 },
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "{{service}} error rate"
          }
        ],
        "yaxes": [
          { "format": "percentunit", "label": "Error Rate" },
          { "format": "short" }
        ],
        "alert": {
          "name": "High Error Rate",
          "conditions": [
            {
              "evaluator": { "type": "gt", "params": [0.05] },
              "operator": { "type": "and" },
              "query": { "params": ["A", "5m", "now"] },
              "reducer": { "type": "avg" }
            }
          ]
        }
      },
      {
        "id": 3,
        "title": "Latency Percentiles",
        "type": "graph",
        "gridPos": { "h": 8, "w": 24, "x": 0, "y": 8 },
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P99"
          }
        ],
        "yaxes": [{ "format": "s", "label": "Duration" }, { "format": "short" }]
      },
      {
        "id": 4,
        "title": "Active Connections",
        "type": "stat",
        "gridPos": { "h": 4, "w": 6, "x": 0, "y": 16 },
        "targets": [
          {
            "expr": "active_connections",
            "instant": true
          }
        ],
        "options": {
          "colorMode": "value",
          "graphMode": "area",
          "reduceOptions": { "values": false, "calcs": ["lastNotNull"] }
        }
      },
      {
        "id": 5,
        "title": "Throughput",
        "type": "stat",
        "gridPos": { "h": 4, "w": 6, "x": 6, "y": 16 },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m]))",
            "instant": true
          }
        ],
        "options": {
          "unit": "reqps",
          "colorMode": "value"
        }
      },
      {
        "id": 6,
        "title": "Success Rate",
        "type": "stat",
        "gridPos": { "h": 4, "w": 6, "x": 12, "y": 16 },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status!~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
            "instant": true
          }
        ],
        "options": {
          "unit": "percentunit",
          "colorMode": "value",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "value": null, "color": "red" },
              { "value": 0.95, "color": "yellow" },
              { "value": 0.99, "color": "green" }
            ]
          }
        }
      },
      {
        "id": 7,
        "title": "Apdex Score",
        "type": "stat",
        "gridPos": { "h": 4, "w": 6, "x": 18, "y": 16 },
        "targets": [
          {
            "expr": "(sum(rate(http_request_duration_seconds_bucket{le=\"0.5\"}[5m])) + sum(rate(http_request_duration_seconds_bucket{le=\"2.0\"}[5m])) / 2) / sum(rate(http_request_duration_seconds_count[5m]))",
            "instant": true
          }
        ],
        "options": {
          "colorMode": "value",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "value": null, "color": "red" },
              { "value": 0.85, "color": "yellow" },
              { "value": 0.95, "color": "green" }
            ]
          }
        }
      },
      {
        "id": 8,
        "title": "Top Slow Endpoints",
        "type": "table",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 20 },
        "targets": [
          {
            "expr": "topk(10, histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])))",
            "format": "table",
            "instant": true
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": { "Time": true },
              "indexByName": {
                "route": 0,
                "method": 1,
                "Value": 2
              },
              "renameByName": {
                "Value": "P95 Duration (s)"
              }
            }
          }
        ]
      },
      {
        "id": 9,
        "title": "Requests by Status Code",
        "type": "piechart",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 20 },
        "targets": [
          {
            "expr": "sum by (status) (rate(http_requests_total[5m]))",
            "legendFormat": "{{status}}"
          }
        ],
        "options": {
          "legend": { "displayMode": "table", "placement": "right" },
          "pieType": "donut"
        }
      }
    ]
  }
}
```

## System Resources Dashboard

```json
{
  "comment": "file: configs/grafana/dashboards/system-resources.json",
  "comment": "version: 1.0.0",
  "comment": "guid: grafana-system-resources-dashboard",

  "dashboard": {
    "title": "System Resources",
    "tags": ["system", "resources"],
    "timezone": "browser",
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "CPU Usage",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
        "targets": [
          {
            "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "{{instance}}"
          }
        ],
        "yaxes": [
          { "format": "percent", "min": 0, "max": 100 },
          { "format": "short" }
        ]
      },
      {
        "id": 2,
        "title": "Memory Usage",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 0 },
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "{{instance}}"
          }
        ],
        "yaxes": [
          { "format": "percent", "min": 0, "max": 100 },
          { "format": "short" }
        ]
      },
      {
        "id": 3,
        "title": "Disk Usage",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 8 },
        "targets": [
          {
            "expr": "(1 - (node_filesystem_avail_bytes{fstype!~\"tmpfs|fuse.*\"} / node_filesystem_size_bytes)) * 100",
            "legendFormat": "{{instance}} {{mountpoint}}"
          }
        ],
        "yaxes": [
          { "format": "percent", "min": 0, "max": 100 },
          { "format": "short" }
        ]
      },
      {
        "id": 4,
        "title": "Network Bandwidth",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 8 },
        "targets": [
          {
            "expr": "rate(node_network_receive_bytes_total[5m])",
            "legendFormat": "{{instance}} {{device}} RX"
          },
          {
            "expr": "rate(node_network_transmit_bytes_total[5m])",
            "legendFormat": "{{instance}} {{device}} TX"
          }
        ],
        "yaxes": [{ "format": "Bps" }, { "format": "short" }],
        "seriesOverrides": [{ "alias": "/TX/", "transform": "negative-Y" }]
      },
      {
        "id": 5,
        "title": "Load Average",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 16 },
        "targets": [
          {
            "expr": "node_load1",
            "legendFormat": "{{instance}} 1m"
          },
          {
            "expr": "node_load5",
            "legendFormat": "{{instance}} 5m"
          },
          {
            "expr": "node_load15",
            "legendFormat": "{{instance}} 15m"
          }
        ]
      },
      {
        "id": 6,
        "title": "Disk I/O",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 16 },
        "targets": [
          {
            "expr": "rate(node_disk_read_bytes_total[5m])",
            "legendFormat": "{{instance}} {{device}} read"
          },
          {
            "expr": "rate(node_disk_written_bytes_total[5m])",
            "legendFormat": "{{instance}} {{device}} write"
          }
        ],
        "yaxes": [{ "format": "Bps" }, { "format": "short" }],
        "seriesOverrides": [{ "alias": "/write/", "transform": "negative-Y" }]
      }
    ]
  }
}
```

## SLO Dashboard

```json
{
  "comment": "file: configs/grafana/dashboards/slo.json",
  "comment": "version: 1.0.0",
  "comment": "guid: grafana-slo-dashboard",

  "dashboard": {
    "title": "Service Level Objectives",
    "tags": ["slo", "sla"],
    "timezone": "browser",
    "refresh": "1m",
    "panels": [
      {
        "id": 1,
        "title": "Availability (30-day)",
        "type": "stat",
        "gridPos": { "h": 6, "w": 8, "x": 0, "y": 0 },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status!~\"5..\"}[30d])) / sum(rate(http_requests_total[30d]))",
            "instant": true
          }
        ],
        "options": {
          "unit": "percentunit",
          "colorMode": "background",
          "graphMode": "none",
          "textMode": "value_and_name",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "value": null, "color": "red" },
              { "value": 0.999, "color": "green" }
            ]
          }
        },
        "fieldConfig": {
          "defaults": {
            "mappings": [],
            "min": 0.995,
            "max": 1.0
          }
        }
      },
      {
        "id": 2,
        "title": "Latency SLO (30-day P95)",
        "type": "stat",
        "gridPos": { "h": 6, "w": 8, "x": 8, "y": 0 },
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[30d])) by (le))",
            "instant": true
          }
        ],
        "options": {
          "unit": "s",
          "colorMode": "background",
          "graphMode": "none",
          "textMode": "value_and_name",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "value": null, "color": "green" },
              { "value": 0.5, "color": "red" }
            ]
          }
        }
      },
      {
        "id": 3,
        "title": "Error Budget Remaining",
        "type": "gauge",
        "gridPos": { "h": 6, "w": 8, "x": 16, "y": 0 },
        "targets": [
          {
            "expr": "1 - ((sum(rate(http_requests_total{status=~\"5..\"}[30d])) / sum(rate(http_requests_total[30d]))) / 0.001)",
            "instant": true
          }
        ],
        "options": {
          "unit": "percentunit",
          "min": 0,
          "max": 1,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "value": 0, "color": "red" },
              { "value": 0.2, "color": "yellow" },
              { "value": 0.5, "color": "green" }
            ]
          }
        }
      },
      {
        "id": 4,
        "title": "Error Budget Burn Rate (1h)",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 6 },
        "targets": [
          {
            "expr": "(sum(rate(http_requests_total{status=~\"5..\"}[1h])) / sum(rate(http_requests_total[1h]))) / 0.001",
            "legendFormat": "Burn rate"
          },
          {
            "expr": "1",
            "legendFormat": "Target (1x)"
          }
        ],
        "yaxes": [
          { "format": "none", "label": "Burn Rate (x)" },
          { "format": "short" }
        ]
      },
      {
        "id": 5,
        "title": "SLO Compliance Trend (7 days)",
        "type": "graph",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 6 },
        "targets": [
          {
            "expr": "avg_over_time((sum(rate(http_requests_total{status!~\"5..\"}[1h])) / sum(rate(http_requests_total[1h])))[7d:1h])",
            "legendFormat": "Availability"
          },
          {
            "expr": "0.999",
            "legendFormat": "SLO Target (99.9%)"
          }
        ],
        "yaxes": [
          { "format": "percentunit", "min": 0.995, "max": 1.0 },
          { "format": "short" }
        ]
      },
      {
        "id": 6,
        "title": "Request Success Rate by Service",
        "type": "table",
        "gridPos": { "h": 8, "w": 24, "x": 0, "y": 14 },
        "targets": [
          {
            "expr": "sum by (service) (rate(http_requests_total{status!~\"5..\"}[30d])) / sum by (service) (rate(http_requests_total[30d]))",
            "format": "table",
            "instant": true
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": { "Time": true },
              "renameByName": {
                "Value": "Success Rate"
              }
            }
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percentunit",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                { "value": null, "color": "red" },
                { "value": 0.995, "color": "yellow" },
                { "value": 0.999, "color": "green" }
              ]
            }
          },
          "overrides": [
            {
              "matcher": { "id": "byName", "options": "Success Rate" },
              "properties": [
                { "id": "custom.displayMode", "value": "gradient-gauge" }
              ]
            }
          ]
        }
      }
    ]
  }
}
```

## Distributed Tracing Dashboard

```json
{
  "comment": "file: configs/grafana/dashboards/tracing.json",
  "comment": "version: 1.0.0",
  "comment": "guid: grafana-tracing-dashboard",

  "dashboard": {
    "title": "Distributed Tracing",
    "tags": ["tracing", "jaeger"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Trace Search",
        "type": "jaeger-search",
        "gridPos": { "h": 12, "w": 24, "x": 0, "y": 0 },
        "datasource": "Jaeger",
        "options": {
          "service": "",
          "operation": "",
          "tags": "",
          "minDuration": "",
          "maxDuration": "",
          "limit": 20
        }
      },
      {
        "id": 2,
        "title": "Service Dependency Graph",
        "type": "nodeGraph",
        "gridPos": { "h": 12, "w": 24, "x": 0, "y": 12 },
        "datasource": "Jaeger",
        "targets": [
          {
            "queryType": "dependencies",
            "service": ""
          }
        ]
      }
    ]
  }
}
```

## Profiling Dashboard

```json
{
  "comment": "file: configs/grafana/dashboards/profiling.json",
  "comment": "version: 1.0.0",
  "comment": "guid: grafana-profiling-dashboard",

  "dashboard": {
    "title": "Continuous Profiling",
    "tags": ["profiling", "pyroscope"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "CPU Profile Flamegraph",
        "type": "flamegraph",
        "gridPos": { "h": 12, "w": 24, "x": 0, "y": 0 },
        "datasource": "Pyroscope",
        "targets": [
          {
            "queryType": "profile",
            "profileTypeId": "cpu",
            "labelSelector": "{service=\"ubuntu-autoinstall-agent\"}",
            "groupBy": []
          }
        ]
      },
      {
        "id": 2,
        "title": "Memory Profile",
        "type": "flamegraph",
        "gridPos": { "h": 12, "w": 24, "x": 0, "y": 12 },
        "datasource": "Pyroscope",
        "targets": [
          {
            "queryType": "profile",
            "profileTypeId": "memory",
            "labelSelector": "{service=\"ubuntu-autoinstall-agent\"}",
            "groupBy": []
          }
        ]
      },
      {
        "id": 3,
        "title": "Profile Comparison (CPU)",
        "type": "flamegraph-diff",
        "gridPos": { "h": 12, "w": 24, "x": 0, "y": 24 },
        "datasource": "Pyroscope",
        "targets": [
          {
            "queryType": "profile-diff",
            "leftQuery": "{service=\"ubuntu-autoinstall-agent\",version=\"v1.0.0\"}",
            "rightQuery": "{service=\"ubuntu-autoinstall-agent\",version=\"v1.1.0\"}"
          }
        ]
      }
    ]
  }
}
```

---

**Part 4 Complete**: Grafana configuration with datasource provisioning (Prometheus, Jaeger,
Pyroscope), comprehensive dashboards for application performance (request rate, error rate, latency
percentiles, active connections, throughput, Apdex), system resources (CPU, memory, disk, network,
load average), SLO monitoring (availability, latency, error budget burn rate, compliance trends),
distributed tracing integration, and continuous profiling with flamegraphs. ✅

**Continue to Part 5** for performance testing automation and benchmarking workflows.
