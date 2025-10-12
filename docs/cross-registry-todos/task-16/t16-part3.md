<!-- file: docs/cross-registry-todos/task-16/t16-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t16-deployment-automation-part3-k8l9m0n1-o2p3 -->

# Task 16 Part 3: Kustomize Overlays and GitOps with ArgoCD

## Kustomize Directory Structure

```text
k8s/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   └── ...
├── overlays/
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   ├── deployment-patch.yaml
│   │   ├── configmap-patch.yaml
│   │   └── ingress-patch.yaml
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   ├── deployment-patch.yaml
│   │   └── resources-patch.yaml
│   └── production/
│       ├── kustomization.yaml
│       ├── deployment-patch.yaml
│       ├── hpa-patch.yaml
│       └── security-patch.yaml
└── components/
    ├── monitoring/
    │   ├── kustomization.yaml
    │   ├── servicemonitor.yaml
    │   └── prometheusrule.yaml
    └── istio/
        ├── kustomization.yaml
        ├── virtualservice.yaml
        └── destinationrule.yaml
```

## Development Overlay

### Dev Kustomization

```yaml
# file: k8s/overlays/dev/kustomization.yaml
# version: 1.0.0
# guid: kustomize-dev

apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: ubuntu-autoinstall-dev

namePrefix: dev-
nameSuffix: -v1

commonLabels:
  environment: development
  team: infrastructure
  version: v1

commonAnnotations:
  owner: dev-team
  managed-by: kustomize

bases:
  - ../../base

patchesStrategicMerge:
  - deployment-patch.yaml
  - configmap-patch.yaml
  - ingress-patch.yaml

replicas:
  - name: ubuntu-autoinstall-agent
    count: 1

images:
  - name: ghcr.io/jdfalk/ubuntu-autoinstall-agent
    newTag: latest

configMapGenerator:
  - name: ubuntu-autoinstall-config
    behavior: merge
    literals:
      - LOG_LEVEL=debug
      - ENVIRONMENT=development

secretGenerator:
  - name: ubuntu-autoinstall-secrets
    behavior: replace
    envs:
      - secrets-dev.env
```

### Dev Deployment Patch

```yaml
# file: k8s/overlays/dev/deployment-patch.yaml
# version: 1.0.0
# guid: kustomize-dev-deployment-patch

apiVersion: apps/v1
kind: Deployment
metadata:
  name: ubuntu-autoinstall-agent
spec:
  template:
    spec:
      containers:
        - name: ubuntu-autoinstall-agent
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
          env:
            - name: RUST_LOG
              value: debug
            - name: RUST_BACKTRACE
              value: '1'
```

### Dev Ingress Patch

```yaml
# file: k8s/overlays/dev/ingress-patch.yaml
# version: 1.0.0
# guid: kustomize-dev-ingress-patch

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ubuntu-autoinstall-agent
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-staging
spec:
  tls:
    - hosts:
        - ubuntu-autoinstall-dev.example.com
      secretName: ubuntu-autoinstall-dev-tls
  rules:
    - host: ubuntu-autoinstall-dev.example.com
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

## Staging Overlay

### Staging Kustomization

```yaml
# file: k8s/overlays/staging/kustomization.yaml
# version: 1.0.0
# guid: kustomize-staging

apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: ubuntu-autoinstall-staging

namePrefix: staging-

commonLabels:
  environment: staging
  team: infrastructure

bases:
  - ../../base

components:
  - ../../components/monitoring

patchesStrategicMerge:
  - deployment-patch.yaml
  - resources-patch.yaml

replicas:
  - name: ubuntu-autoinstall-agent
    count: 2

images:
  - name: ghcr.io/jdfalk/ubuntu-autoinstall-agent
    newTag: staging

configMapGenerator:
  - name: ubuntu-autoinstall-config
    behavior: merge
    literals:
      - LOG_LEVEL=info
      - ENVIRONMENT=staging

secretGenerator:
  - name: ubuntu-autoinstall-secrets
    behavior: replace
    envs:
      - secrets-staging.env
```

### Staging Deployment Patch

```yaml
# file: k8s/overlays/staging/deployment-patch.yaml
# version: 1.0.0
# guid: kustomize-staging-deployment-patch

apiVersion: apps/v1
kind: Deployment
metadata:
  name: ubuntu-autoinstall-agent
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      annotations:
        prometheus.io/scrape: 'true'
        prometheus.io/port: '9090'
    spec:
      containers:
        - name: ubuntu-autoinstall-agent
          resources:
            limits:
              cpu: 500m
              memory: 512Mi
            requests:
              cpu: 250m
              memory: 256Mi
          env:
            - name: RUST_LOG
              value: info
```

### Staging Resources Patch

```yaml
# file: k8s/overlays/staging/resources-patch.yaml
# version: 1.0.0
# guid: kustomize-staging-resources-patch

apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ubuntu-autoinstall-agent
spec:
  minReplicas: 2
  maxReplicas: 5
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
```

## Production Overlay

### Production Kustomization

```yaml
# file: k8s/overlays/production/kustomization.yaml
# version: 1.0.0
# guid: kustomize-production

apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: ubuntu-autoinstall-production

namePrefix: prod-

commonLabels:
  environment: production
  team: infrastructure
  criticality: high

commonAnnotations:
  owner: sre-team
  pagerduty: ubuntu-autoinstall-oncall

bases:
  - ../../base

components:
  - ../../components/monitoring
  - ../../components/istio

patchesStrategicMerge:
  - deployment-patch.yaml
  - hpa-patch.yaml
  - security-patch.yaml

patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
      name: ubuntu-autoinstall-agent
    path: affinity-patch.yaml

replicas:
  - name: ubuntu-autoinstall-agent
    count: 5

images:
  - name: ghcr.io/jdfalk/ubuntu-autoinstall-agent
    newTag: v1.0.0

configMapGenerator:
  - name: ubuntu-autoinstall-config
    behavior: merge
    literals:
      - LOG_LEVEL=warn
      - ENVIRONMENT=production
      - RATE_LIMIT=200

secretGenerator:
  - name: ubuntu-autoinstall-secrets
    behavior: replace
    envs:
      - secrets-production.env
```

### Production Deployment Patch

```yaml
# file: k8s/overlays/production/deployment-patch.yaml
# version: 1.0.0
# guid: kustomize-production-deployment-patch

apiVersion: apps/v1
kind: Deployment
metadata:
  name: ubuntu-autoinstall-agent
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      annotations:
        prometheus.io/scrape: 'true'
        prometheus.io/port: '9090'
        vault.hashicorp.com/agent-inject: 'true'
        vault.hashicorp.com/role: 'ubuntu-autoinstall-agent'
    spec:
      nodeSelector:
        workload: production
        node.kubernetes.io/instance-type: c5.xlarge
      containers:
        - name: ubuntu-autoinstall-agent
          resources:
            limits:
              cpu: 1000m
              memory: 1Gi
            requests:
              cpu: 500m
              memory: 512Mi
          env:
            - name: RUST_LOG
              value: warn
            - name: RUST_BACKTRACE
              value: '0'
            - name: MAX_CONNECTIONS
              value: '1000'
```

### Production HPA Patch

```yaml
# file: k8s/overlays/production/hpa-patch.yaml
# version: 1.0.0
# guid: kustomize-production-hpa-patch

apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ubuntu-autoinstall-agent
spec:
  minReplicas: 5
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: '2000'
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
          value: 4
          periodSeconds: 30
      selectPolicy: Max
```

### Production Security Patch

```yaml
# file: k8s/overlays/production/security-patch.yaml
# version: 1.0.0
# guid: kustomize-production-security-patch

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ubuntu-autoinstall-agent
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
        - namespaceSelector:
            matchLabels:
              name: istio-system
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
        - podSelector: {}
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

### Production Affinity Patch (JSON6902)

```yaml
# file: k8s/overlays/production/affinity-patch.yaml
# version: 1.0.0
# guid: kustomize-production-affinity-patch

- op: add
  path: /spec/template/spec/affinity
  value:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchExpressions:
              - key: app
                operator: In
                values:
                  - ubuntu-autoinstall-agent
          topologyKey: kubernetes.io/hostname
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: workload
                operator: In
                values:
                  - production
```

## Kustomize Components

### Monitoring Component

```yaml
# file: k8s/components/monitoring/kustomization.yaml
# version: 1.0.0
# guid: kustomize-component-monitoring

apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component

resources:
  - servicemonitor.yaml
  - prometheusrule.yaml
```

```yaml
# file: k8s/components/monitoring/servicemonitor.yaml
# version: 1.0.0
# guid: kustomize-servicemonitor

apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ubuntu-autoinstall-agent
  labels:
    app: ubuntu-autoinstall-agent
spec:
  selector:
    matchLabels:
      app: ubuntu-autoinstall-agent
  endpoints:
    - port: metrics
      interval: 30s
      path: /metrics
```

```yaml
# file: k8s/components/monitoring/prometheusrule.yaml
# version: 1.0.0
# guid: kustomize-prometheusrule

apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: ubuntu-autoinstall-agent
spec:
  groups:
    - name: ubuntu-autoinstall-agent
      interval: 30s
      rules:
        - alert: HighErrorRate
          expr: |
            sum(rate(http_requests_total{status=~"5..", job="ubuntu-autoinstall-agent"}[5m])) /
            sum(rate(http_requests_total{job="ubuntu-autoinstall-agent"}[5m])) > 0.05
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: High error rate detected
            description: Error rate is {{ $value | humanizePercentage }} for the last 5 minutes

        - alert: HighLatency
          expr: |
            histogram_quantile(0.95,
              sum(rate(http_request_duration_seconds_bucket{job="ubuntu-autoinstall-agent"}[5m])) by (le)
            ) > 1
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: High latency detected
            description: P95 latency is {{ $value }}s
```

### Istio Component

```yaml
# file: k8s/components/istio/kustomization.yaml
# version: 1.0.0
# guid: kustomize-component-istio

apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component

resources:
  - virtualservice.yaml
  - destinationrule.yaml
```

```yaml
# file: k8s/components/istio/virtualservice.yaml
# version: 1.0.0
# guid: kustomize-istio-virtualservice

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: ubuntu-autoinstall-agent
spec:
  hosts:
    - ubuntu-autoinstall-agent
  http:
    - match:
        - headers:
            canary:
              exact: 'true'
      route:
        - destination:
            host: ubuntu-autoinstall-agent
            subset: canary
          weight: 100
    - route:
        - destination:
            host: ubuntu-autoinstall-agent
            subset: stable
          weight: 100
```

```yaml
# file: k8s/components/istio/destinationrule.yaml
# version: 1.0.0
# guid: kustomize-istio-destinationrule

apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: ubuntu-autoinstall-agent
spec:
  host: ubuntu-autoinstall-agent
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 1000
      http:
        http1MaxPendingRequests: 1000
        http2MaxRequests: 1000
        maxRequestsPerConnection: 2
    loadBalancer:
      simple: LEAST_REQUEST
    outlierDetection:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
  subsets:
    - name: stable
      labels:
        version: v1
    - name: canary
      labels:
        version: v2
```

## ArgoCD Application Configuration

### ArgoCD Application for Dev

```yaml
# file: argocd/applications/ubuntu-autoinstall-dev.yaml
# version: 1.0.0
# guid: argocd-app-dev

apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ubuntu-autoinstall-dev
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default

  source:
    repoURL: https://github.com/jdfalk/ubuntu-autoinstall-agent.git
    targetRevision: develop
    path: k8s/overlays/dev

  destination:
    server: https://kubernetes.default.svc
    namespace: ubuntu-autoinstall-dev

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
      - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m

  revisionHistoryLimit: 10
```

### ArgoCD Application for Staging

```yaml
# file: argocd/applications/ubuntu-autoinstall-staging.yaml
# version: 1.0.0
# guid: argocd-app-staging

apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ubuntu-autoinstall-staging
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default

  source:
    repoURL: https://github.com/jdfalk/ubuntu-autoinstall-agent.git
    targetRevision: staging
    path: k8s/overlays/staging

  destination:
    server: https://kubernetes.default.svc
    namespace: ubuntu-autoinstall-staging

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true

  revisionHistoryLimit: 10
```

### ArgoCD Application for Production

```yaml
# file: argocd/applications/ubuntu-autoinstall-production.yaml
# version: 1.0.0
# guid: argocd-app-production

apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ubuntu-autoinstall-production
  namespace: argocd
  annotations:
    notifications.argoproj.io/subscribe.on-sync-succeeded.slack: deployment-notifications
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: production

  source:
    repoURL: https://github.com/jdfalk/ubuntu-autoinstall-agent.git
    targetRevision: v1.0.0
    path: k8s/overlays/production

  destination:
    server: https://kubernetes.default.svc
    namespace: ubuntu-autoinstall-production

  syncPolicy:
    automated:
      prune: false
      selfHeal: false
    syncOptions:
      - CreateNamespace=true
      - ApplyOutOfSyncOnly=true
    retry:
      limit: 3
      backoff:
        duration: 10s
        factor: 2
        maxDuration: 5m

  revisionHistoryLimit: 20

  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas
```

### ArgoCD AppProject for Production

```yaml
# file: argocd/projects/production.yaml
# version: 1.0.0
# guid: argocd-project-production

apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: production
  namespace: argocd
spec:
  description: Production environment applications

  sourceRepos:
    - https://github.com/jdfalk/ubuntu-autoinstall-agent.git

  destinations:
    - namespace: ubuntu-autoinstall-production
      server: https://kubernetes.default.svc
    - namespace: ubuntu-autoinstall-canary
      server: https://kubernetes.default.svc

  clusterResourceWhitelist:
    - group: ''
      kind: Namespace
    - group: 'rbac.authorization.k8s.io'
      kind: ClusterRole
    - group: 'rbac.authorization.k8s.io'
      kind: ClusterRoleBinding

  namespaceResourceWhitelist:
    - group: '*'
      kind: '*'

  roles:
    - name: admin
      description: Admin privileges
      policies:
        - p, proj:production:admin, applications, *, production/*, allow
        - p, proj:production:admin, repositories, *, production/*, allow
      groups:
        - sre-team

    - name: deployer
      description: Deployment privileges
      policies:
        - p, proj:production:deployer, applications, sync, production/*, allow
        - p, proj:production:deployer, applications, get, production/*, allow
      groups:
        - deployment-team
```

---

**Part 3 Complete**: Kustomize overlays for dev/staging/production environments with patches for
deployment/resources/security, Kustomize components for monitoring (ServiceMonitor, PrometheusRule)
and Istio (VirtualService, DestinationRule), ArgoCD Application definitions with automated sync
policies, ArgoCD AppProject configuration with RBAC, and GitOps workflow integration. ✅

**Continue to Part 4** for progressive delivery strategies with canary deployments and blue-green
deployments.
