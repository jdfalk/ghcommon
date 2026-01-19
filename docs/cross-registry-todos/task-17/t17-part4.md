<!-- file: docs/cross-registry-todos/task-17/t17-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t17-observability-logging-part4-y9z0a1b2-c3d4 -->
<!-- last-edited: 2026-01-19 -->

# Task 17 Part 4: Log Aggregation Infrastructure

## Loki Deployment

### Loki Configuration

```yaml
# file: config/loki/loki-config.yaml
# version: 1.0.0
# guid: loki-configuration

auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096
  log_level: info

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    cache_ttl: 24h
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

compactor:
  working_directory: /loki/boltdb-shipper-compactor
  shared_store: filesystem

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  ingestion_rate_mb: 16
  ingestion_burst_size_mb: 32
  per_stream_rate_limit: 10MB
  per_stream_rate_limit_burst: 20MB
  max_streams_per_user: 10000
  max_query_length: 721h
  max_query_parallelism: 32
  max_entries_limit_per_query: 10000

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: true
  retention_period: 720h

ruler:
  storage:
    type: local
    local:
      directory: /loki/rules
  rule_path: /loki/rules-temp
  alertmanager_url: http://alertmanager:9093
  ring:
    kvstore:
      store: inmemory
  enable_api: true

frontend:
  compress_responses: true
  max_outstanding_per_tenant: 2048
  log_queries_longer_than: 5s

query_range:
  align_queries_with_step: true
  max_retries: 5
  cache_results: true
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 500
        ttl: 24h
```

### Loki Kubernetes Deployment

```yaml
# file: k8s/loki/deployment.yaml
# version: 1.0.0
# guid: loki-k8s-deployment

apiVersion: v1
kind: ConfigMap
metadata:
  name: loki-config
  namespace: observability
data:
  loki.yaml: |
    # Contents from loki-config.yaml above
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: loki
  namespace: observability
spec:
  serviceName: loki
  replicas: 3
  selector:
    matchLabels:
      app: loki
  template:
    metadata:
      labels:
        app: loki
    spec:
      containers:
        - name: loki
          image: grafana/loki:2.9.3
          args:
            - -config.file=/etc/loki/loki.yaml
          ports:
            - containerPort: 3100
              name: http
            - containerPort: 9096
              name: grpc
          volumeMounts:
            - name: config
              mountPath: /etc/loki
            - name: storage
              mountPath: /loki
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              cpu: 2
              memory: 4Gi
          livenessProbe:
            httpGet:
              path: /ready
              port: 3100
            initialDelaySeconds: 45
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 3100
            initialDelaySeconds: 45
            periodSeconds: 10
      volumes:
        - name: config
          configMap:
            name: loki-config
  volumeClaimTemplates:
    - metadata:
        name: storage
      spec:
        accessModes: ['ReadWriteOnce']
        resources:
          requests:
            storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: loki
  namespace: observability
spec:
  type: ClusterIP
  ports:
    - port: 3100
      targetPort: 3100
      protocol: TCP
      name: http
    - port: 9096
      targetPort: 9096
      protocol: TCP
      name: grpc
  selector:
    app: loki
```

## Promtail Configuration

### Promtail Agent Setup

```yaml
# file: config/promtail/promtail-config.yaml
# version: 1.0.0
# guid: promtail-configuration

server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push
    tenant_id: tenant1
    batchwait: 1s
    batchsize: 1048576

scrape_configs:
  # Kubernetes pod logs
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod
    pipeline_stages:
      # Extract log level
      - regex:
          expression: '.*level=(?P<level>\w+).*'
      - labels:
          level:

      # Extract trace ID
      - regex:
          expression: '.*trace_id=(?P<trace_id>[a-f0-9]+).*'
      - labels:
          trace_id:

      # Parse JSON logs
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: message
            service: service
            trace_id: trace_id
            span_id: span_id

      # Set timestamp
      - timestamp:
          source: timestamp
          format: RFC3339

      # Add labels
      - labels:
          level:
          service:

    relabel_configs:
      # Add namespace
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace

      # Add pod name
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod

      # Add container name
      - source_labels: [__meta_kubernetes_pod_container_name]
        target_label: container

      # Add app label
      - source_labels: [__meta_kubernetes_pod_label_app]
        target_label: app

      # Add environment from namespace
      - source_labels: [__meta_kubernetes_namespace]
        regex: '.*-(dev|staging|prod)$'
        target_label: environment

  # System logs
  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: varlogs
          __path__: /var/log/*.log
    pipeline_stages:
      - match:
          selector: '{job="varlogs"}'
          stages:
            - regex:
                expression:
                  '(?P<timestamp>\w+ +\d+ \d+:\d+:\d+) (?P<hostname>\S+)
                  (?P<process>\S+)(\[(?P<pid>\d+)\])?: (?P<message>.+)'
            - timestamp:
                source: timestamp
                format: Jan 02 15:04:05
            - labels:
                hostname:
                process:

  # Application logs from files
  - job_name: app-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: app-logs
          __path__: /var/log/app/*.json
    pipeline_stages:
      # Parse JSON
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: message
            service: service
            environment: environment
            trace_id: trace_id
            request_id: request_id

      # Extract additional fields
      - labels:
          level:
          service:
          environment:

      # Timestamp from log
      - timestamp:
          source: timestamp
          format: RFC3339
```

### Promtail DaemonSet

```yaml
# file: k8s/promtail/daemonset.yaml
# version: 1.0.0
# guid: promtail-k8s-daemonset

apiVersion: v1
kind: ServiceAccount
metadata:
  name: promtail
  namespace: observability
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: promtail
rules:
  - apiGroups: ['']
    resources:
      - nodes
      - nodes/proxy
      - services
      - endpoints
      - pods
    verbs: ['get', 'watch', 'list']
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: promtail
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: promtail
subjects:
  - kind: ServiceAccount
    name: promtail
    namespace: observability
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: promtail-config
  namespace: observability
data:
  promtail.yaml: |
    # Contents from promtail-config.yaml above
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: promtail
  namespace: observability
spec:
  selector:
    matchLabels:
      app: promtail
  template:
    metadata:
      labels:
        app: promtail
    spec:
      serviceAccountName: promtail
      containers:
        - name: promtail
          image: grafana/promtail:2.9.3
          args:
            - -config.file=/etc/promtail/promtail.yaml
          env:
            - name: HOSTNAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
          ports:
            - containerPort: 9080
              name: http
          volumeMounts:
            - name: config
              mountPath: /etc/promtail
            - name: positions
              mountPath: /tmp
            - name: varlog
              mountPath: /var/log
              readOnly: true
            - name: varlibdockercontainers
              mountPath: /var/lib/docker/containers
              readOnly: true
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 200m
              memory: 256Mi
      volumes:
        - name: config
          configMap:
            name: promtail-config
        - name: positions
          hostPath:
            path: /tmp/promtail-positions
        - name: varlog
          hostPath:
            path: /var/log
        - name: varlibdockercontainers
          hostPath:
            path: /var/lib/docker/containers
      tolerations:
        - effect: NoSchedule
          operator: Exists
```

## ELK Stack Alternative

### Elasticsearch Configuration

```yaml
# file: config/elasticsearch/elasticsearch.yml
# version: 1.0.0
# guid: elasticsearch-configuration

cluster.name: 'logging-cluster'
network.host: 0.0.0.0

# Disable X-Pack security for development
xpack.security.enabled: false
xpack.monitoring.collection.enabled: true

# Node roles
node.roles: [master, data, ingest]

# Discovery
discovery.type: single-node

# Index settings
index.number_of_shards: 1
index.number_of_replicas: 1

# Memory settings
bootstrap.memory_lock: true

# Index lifecycle management
action.auto_create_index: true
indices.lifecycle.poll_interval: 10m

# Slow log thresholds
index.search.slowlog.threshold.query.warn: 10s
index.search.slowlog.threshold.query.info: 5s
index.search.slowlog.threshold.query.debug: 2s

index.indexing.slowlog.threshold.index.warn: 10s
index.indexing.slowlog.threshold.index.info: 5s
index.indexing.slowlog.threshold.index.debug: 2s

# Retention policies
indices.lifecycle.policies:
  logs-policy:
    phases:
      hot:
        min_age: 0ms
        actions:
          rollover:
            max_size: 50GB
            max_age: 1d
      warm:
        min_age: 7d
        actions:
          allocate:
            number_of_replicas: 1
          forcemerge:
            max_num_segments: 1
      cold:
        min_age: 30d
        actions:
          allocate:
            number_of_replicas: 0
          freeze: {}
      delete:
        min_age: 90d
        actions:
          delete: {}
```

### Logstash Pipeline

```ruby
# file: config/logstash/pipeline/logs.conf
# version: 1.0.0
# guid: logstash-pipeline

input {
  # Beats input
  beats {
    port => 5044
    codec => json
  }

  # TCP input for application logs
  tcp {
    port => 5000
    codec => json_lines
  }

  # HTTP input
  http {
    port => 8080
    codec => json
  }
}

filter {
  # Parse JSON logs
  if [message] {
    json {
      source => "message"
      target => "parsed"
    }
  }

  # Extract log level
  if [parsed][level] {
    mutate {
      add_field => { "log_level" => "%{[parsed][level]}" }
      uppercase => [ "log_level" ]
    }
  }

  # Extract trace context
  if [parsed][trace_id] {
    mutate {
      add_field => { "trace_id" => "%{[parsed][trace_id]}" }
    }
  }

  if [parsed][span_id] {
    mutate {
      add_field => { "span_id" => "%{[parsed][span_id]}" }
    }
  }

  # Parse timestamp
  if [parsed][timestamp] {
    date {
      match => [ "[parsed][timestamp]", "ISO8601" ]
      target => "@timestamp"
    }
  }

  # GeoIP enrichment
  if [parsed][remote_addr] {
    geoip {
      source => "[parsed][remote_addr]"
      target => "geoip"
    }
  }

  # User agent parsing
  if [parsed][user_agent] {
    useragent {
      source => "[parsed][user_agent]"
      target => "user_agent_parsed"
    }
  }

  # Error categorization
  if [log_level] == "ERROR" {
    if [parsed][error] =~ /timeout/i {
      mutate {
        add_field => { "error_category" => "timeout" }
      }
    } else if [parsed][error] =~ /connection/i {
      mutate {
        add_field => { "error_category" => "connection" }
      }
    } else if [parsed][error] =~ /database/i {
      mutate {
        add_field => { "error_category" => "database" }
      }
    } else {
      mutate {
        add_field => { "error_category" => "general" }
      }
    }
  }

  # Add metadata
  mutate {
    add_field => {
      "indexed_at" => "%{@timestamp}"
    }
  }

  # Remove unnecessary fields
  mutate {
    remove_field => [ "message", "host", "agent" ]
  }
}

output {
  # Elasticsearch output
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "logs-%{[parsed][service]}-%{+YYYY.MM.dd}"
    template_name => "logs"
    template_overwrite => true
  }

  # Stdout for debugging
  if [log_level] == "ERROR" {
    stdout {
      codec => rubydebug
    }
  }
}
```

### Kibana Configuration

```yaml
# file: config/kibana/kibana.yml
# version: 1.0.0
# guid: kibana-configuration

server.name: kibana
server.host: '0.0.0.0'
server.port: 5601

elasticsearch.hosts: ['http://elasticsearch:9200']
elasticsearch.requestTimeout: 30000

# Monitoring
monitoring.ui.container.elasticsearch.enabled: true

# Logging
logging.dest: stdout
logging.verbose: false

# Index patterns
kibana.index: '.kibana'
kibana.defaultAppId: 'discover'

# Security (disable for development)
xpack.security.enabled: false

# Saved objects
xpack.encryptedSavedObjects.encryptionKey: 'something_at_least_32_characters_long'

# Alerting
xpack.alerting.enabled: true

# Visualization
xpack.canvas.enabled: true
xpack.graph.enabled: true
```

---

**Part 4 Complete**: Log aggregation infrastructure with Loki configuration for log storage using
BoltDB shipper and filesystem, retention policies for 30-day log retention, compactor for index
optimization, ruler for alerting rules, query frontend with caching, Loki Kubernetes StatefulSet
with 3 replicas and persistent volumes, Promtail configuration for scraping Kubernetes pod logs with
pipeline stages for JSON parsing and label extraction, system log collection, trace ID correlation,
Promtail DaemonSet with RBAC for cluster-wide log collection, ELK stack alternative with
Elasticsearch cluster configuration including index lifecycle management (hot/warm/cold/delete
phases), Logstash pipeline for log parsing with JSON decoding, GeoIP enrichment, user-agent parsing,
error categorization, and Elasticsearch output with daily indices, Kibana configuration for log
visualization and analysis. ✅

**Continue to Part 5** for log-based alerting rules, anomaly detection, and alert throttling.
