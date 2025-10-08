<!-- file: docs/cross-registry-todos/task-16/t16-part1.md -->
<!-- version: 1.0.0 -->
<!-- guid: t16-deployment-automation-part1-y6z7a8b9-c0d1 -->

# Task 16 Part 1: Kubernetes Deployment Manifests and Configuration

## Kubernetes Deployment Strategy

### Namespace Configuration

```yaml
# file: k8s/base/namespace.yaml
# version: 1.0.0
# guid: k8s-namespace

apiVersion: v1
kind: Namespace
metadata:
  name: ubuntu-autoinstall
  labels:
    name: ubuntu-autoinstall
    environment: production
    team: infrastructure
```

### Application Deployment

```yaml
# file: k8s/base/deployment.yaml
# version: 1.0.0
# guid: k8s-deployment

apiVersion: apps/v1
kind: Deployment
metadata:
  name: ubuntu-autoinstall-agent
  namespace: ubuntu-autoinstall
  labels:
    app: ubuntu-autoinstall-agent
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: ubuntu-autoinstall-agent
  template:
    metadata:
      labels:
        app: ubuntu-autoinstall-agent
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: ubuntu-autoinstall-agent
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: ubuntu-autoinstall-agent
        image: ghcr.io/jdfalk/ubuntu-autoinstall-agent:v1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        - name: metrics
          containerPort: 9090
          protocol: TCP
        env:
        - name: RUST_LOG
          value: "info"
        - name: SERVER_PORT
          value: "8080"
        - name: METRICS_PORT
          value: "9090"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ubuntu-autoinstall-secrets
              key: database-url
        - name: QEMU_SOCKET
          value: "/var/run/libvirt/libvirt-sock"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: config
          mountPath: /etc/ubuntu-autoinstall
          readOnly: true
        - name: cache
          mountPath: /var/cache/ubuntu-autoinstall
        - name: libvirt-socket
          mountPath: /var/run/libvirt
      volumes:
      - name: config
        configMap:
          name: ubuntu-autoinstall-config
      - name: cache
        emptyDir:
          sizeLimit: 10Gi
      - name: libvirt-socket
        hostPath:
          path: /var/run/libvirt
          type: Directory
```

### Service Definition

```yaml
# file: k8s/base/service.yaml
# version: 1.0.0
# guid: k8s-service

apiVersion: v1
kind: Service
metadata:
  name: ubuntu-autoinstall-agent
  namespace: ubuntu-autoinstall
  labels:
    app: ubuntu-autoinstall-agent
spec:
  type: ClusterIP
  selector:
    app: ubuntu-autoinstall-agent
  ports:
  - name: http
    port: 80
    targetPort: http
    protocol: TCP
  - name: metrics
    port: 9090
    targetPort: metrics
    protocol: TCP
  sessionAffinity: None
```

### Ingress Configuration

```yaml
# file: k8s/base/ingress.yaml
# version: 1.0.0
# guid: k8s-ingress

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ubuntu-autoinstall-agent
  namespace: ubuntu-autoinstall
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
spec:
  tls:
  - hosts:
    - ubuntu-autoinstall.example.com
    secretName: ubuntu-autoinstall-tls
  rules:
  - host: ubuntu-autoinstall.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ubuntu-autoinstall-agent
            port:
              name: http
```

### ConfigMap

```yaml
# file: k8s/base/configmap.yaml
# version: 1.0.0
# guid: k8s-configmap

apiVersion: v1
kind: ConfigMap
metadata:
  name: ubuntu-autoinstall-config
  namespace: ubuntu-autoinstall
data:
  config.yaml: |
    server:
      host: 0.0.0.0
      port: 8080
      workers: 4

    iso:
      cache_dir: /var/cache/ubuntu-autoinstall/isos
      versions:
        - "20.04"
        - "22.04"
        - "24.04"
      architectures:
        - "amd64"
        - "arm64"

    qemu:
      socket: /var/run/libvirt/libvirt-sock
      default_memory: 2048
      default_cpus: 2
      default_disk_size: 20

    logging:
      level: info
      format: json
      output: stdout

  prometheus.yaml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    scrape_configs:
      - job_name: 'ubuntu-autoinstall-agent'
        kubernetes_sd_configs:
          - role: pod
            namespaces:
              names:
                - ubuntu-autoinstall
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
```

### Secret Template

```yaml
# file: k8s/base/secret.yaml.template
# version: 1.0.0
# guid: k8s-secret-template

apiVersion: v1
kind: Secret
metadata:
  name: ubuntu-autoinstall-secrets
  namespace: ubuntu-autoinstall
type: Opaque
stringData:
  database-url: "postgresql://user:password@postgres:5432/ubuntu_autoinstall"
  api-key: "your-api-key-here"
  jwt-secret: "your-jwt-secret-here"
```

### ServiceAccount and RBAC

```yaml
# file: k8s/base/serviceaccount.yaml
# version: 1.0.0
# guid: k8s-serviceaccount

apiVersion: v1
kind: ServiceAccount
metadata:
  name: ubuntu-autoinstall-agent
  namespace: ubuntu-autoinstall
  labels:
    app: ubuntu-autoinstall-agent
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ubuntu-autoinstall-agent
  namespace: ubuntu-autoinstall
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ubuntu-autoinstall-agent
  namespace: ubuntu-autoinstall
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: ubuntu-autoinstall-agent
subjects:
- kind: ServiceAccount
  name: ubuntu-autoinstall-agent
  namespace: ubuntu-autoinstall
```

## HorizontalPodAutoscaler

```yaml
# file: k8s/base/hpa.yaml
# version: 1.0.0
# guid: k8s-hpa

apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ubuntu-autoinstall-agent
  namespace: ubuntu-autoinstall
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ubuntu-autoinstall-agent
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
      selectPolicy: Max
```

## PodDisruptionBudget

```yaml
# file: k8s/base/pdb.yaml
# version: 1.0.0
# guid: k8s-pdb

apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: ubuntu-autoinstall-agent
  namespace: ubuntu-autoinstall
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: ubuntu-autoinstall-agent
```

## NetworkPolicy

```yaml
# file: k8s/base/networkpolicy.yaml
# version: 1.0.0
# guid: k8s-networkpolicy

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ubuntu-autoinstall-agent
  namespace: ubuntu-autoinstall
spec:
  podSelector:
    matchLabels:
      app: ubuntu-autoinstall-agent
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8080
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 9090
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 443
```

## StatefulSet for Database

```yaml
# file: k8s/base/statefulset-postgres.yaml
# version: 1.0.0
# guid: k8s-statefulset-postgres

apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: ubuntu-autoinstall
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_DB
          value: "ubuntu_autoinstall"
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - postgres
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - postgres
          initialDelaySeconds: 10
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: "fast-ssd"
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: ubuntu-autoinstall
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: postgres
  clusterIP: None
```

## PersistentVolumeClaim for Cache

```yaml
# file: k8s/base/pvc.yaml
# version: 1.0.0
# guid: k8s-pvc

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: iso-cache
  namespace: ubuntu-autoinstall
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: nfs-client
  resources:
    requests:
      storage: 50Gi
```

## Kustomization Base

```yaml
# file: k8s/base/kustomization.yaml
# version: 1.0.0
# guid: k8s-kustomization-base

apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: ubuntu-autoinstall

resources:
  - namespace.yaml
  - deployment.yaml
  - service.yaml
  - ingress.yaml
  - configmap.yaml
  - serviceaccount.yaml
  - hpa.yaml
  - pdb.yaml
  - networkpolicy.yaml
  - statefulset-postgres.yaml
  - pvc.yaml

commonLabels:
  app.kubernetes.io/name: ubuntu-autoinstall-agent
  app.kubernetes.io/component: backend
  app.kubernetes.io/managed-by: kustomize

configMapGenerator:
  - name: ubuntu-autoinstall-config
    files:
      - config.yaml
      - prometheus.yaml

secretGenerator:
  - name: ubuntu-autoinstall-secrets
    envs:
      - secrets.env

images:
  - name: ghcr.io/jdfalk/ubuntu-autoinstall-agent
    newTag: v1.0.0
```

---

**Part 1 Complete**: Kubernetes deployment manifests including Deployment with rolling updates, Service
with ClusterIP, Ingress with TLS and rate limiting, ConfigMap with application configuration,
ServiceAccount with RBAC, HorizontalPodAutoscaler with CPU/memory/custom metrics, PodDisruptionBudget
for availability, NetworkPolicy for security, StatefulSet for PostgreSQL, PersistentVolumeClaim for
cache, and Kustomization base configuration. ✅

**Continue to Part 2** for Helm chart configuration and templating.
