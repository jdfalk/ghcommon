<!-- file: docs/cross-registry-todos/task-16/t16-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t16-deployment-automation-part2-e2f3g4h5-i6j7 -->
<!-- last-edited: 2026-01-19 -->

# Task 16 Part 2: Helm Chart Configuration and Templating

## Helm Chart Structure

```text
helm/ubuntu-autoinstall-agent/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-staging.yaml
├── values-production.yaml
├── templates/
│   ├── NOTES.txt
│   ├── _helpers.tpl
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── serviceaccount.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   ├── networkpolicy.yaml
│   └── tests/
│       └── test-connection.yaml
├── .helmignore
└── README.md
```

## Chart.yaml

```yaml
# file: helm/ubuntu-autoinstall-agent/Chart.yaml
# version: 1.0.0
# guid: helm-chart-yaml

apiVersion: v2
name: ubuntu-autoinstall-agent
description: A Helm chart for Ubuntu Autoinstall Agent
type: application
version: 1.0.0
appVersion: '1.0.0'

keywords:
  - ubuntu
  - autoinstall
  - automation
  - infrastructure

home: https://github.com/jdfalk/ubuntu-autoinstall-agent
sources:
  - https://github.com/jdfalk/ubuntu-autoinstall-agent

maintainers:
  - name: jdfalk
    email: jdfalk@example.com

dependencies: []

annotations:
  category: Infrastructure
  licenses: Apache-2.0
```

## values.yaml (Default Configuration)

```yaml
# file: helm/ubuntu-autoinstall-agent/values.yaml
# version: 1.0.0
# guid: helm-values-yaml

# Default values for ubuntu-autoinstall-agent
# This is a YAML-formatted file.
# Declare variables to be passed into your templates.

replicaCount: 3

image:
  repository: ghcr.io/jdfalk/ubuntu-autoinstall-agent
  pullPolicy: IfNotPresent
  tag: '1.0.0'

imagePullSecrets: []
nameOverride: ''
fullnameOverride: ''

serviceAccount:
  create: true
  annotations: {}
  name: ''

podAnnotations:
  prometheus.io/scrape: 'true'
  prometheus.io/port: '9090'
  prometheus.io/path: '/metrics'

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

securityContext:
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false

service:
  type: ClusterIP
  port: 80
  targetPort: http
  annotations: {}

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: 'true'
    nginx.ingress.kubernetes.io/rate-limit: '100'
  hosts:
    - host: ubuntu-autoinstall.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: ubuntu-autoinstall-tls
      hosts:
        - ubuntu-autoinstall.example.com

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
  metrics:
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: '1000'

nodeSelector: {}

tolerations: []

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
              - key: app
                operator: In
                values:
                  - ubuntu-autoinstall-agent
          topologyKey: kubernetes.io/hostname

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

config:
  server:
    host: 0.0.0.0
    port: 8080
    workers: 4
  iso:
    cacheDir: /var/cache/ubuntu-autoinstall/isos
    versions:
      - '20.04'
      - '22.04'
      - '24.04'
    architectures:
      - 'amd64'
      - 'arm64'
  qemu:
    socket: /var/run/libvirt/libvirt-sock
    defaultMemory: 2048
    defaultCpus: 2
    defaultDiskSize: 20
  logging:
    level: info
    format: json
    output: stdout

secrets:
  databaseUrl: ''
  apiKey: ''
  jwtSecret: ''

podDisruptionBudget:
  enabled: true
  minAvailable: 2

networkPolicy:
  enabled: true
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
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: database
      ports:
        - protocol: TCP
          port: 5432

persistence:
  enabled: true
  storageClassName: nfs-client
  accessMode: ReadWriteMany
  size: 50Gi

postgresql:
  enabled: true
  auth:
    username: ubuntu_autoinstall
    password: ''
    database: ubuntu_autoinstall
  primary:
    persistence:
      enabled: true
      storageClass: fast-ssd
      size: 10Gi
```

## Environment-Specific Values

### values-dev.yaml

```yaml
# file: helm/ubuntu-autoinstall-agent/values-dev.yaml
# version: 1.0.0
# guid: helm-values-dev

replicaCount: 1

image:
  tag: 'latest'
  pullPolicy: Always

ingress:
  hosts:
    - host: ubuntu-autoinstall-dev.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: ubuntu-autoinstall-dev-tls
      hosts:
        - ubuntu-autoinstall-dev.example.com

resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi

autoscaling:
  enabled: false

config:
  logging:
    level: debug

postgresql:
  primary:
    persistence:
      size: 5Gi
```

### values-staging.yaml

```yaml
# file: helm/ubuntu-autoinstall-agent/values-staging.yaml
# version: 1.0.0
# guid: helm-values-staging

replicaCount: 2

image:
  tag: 'staging'
  pullPolicy: IfNotPresent

ingress:
  hosts:
    - host: ubuntu-autoinstall-staging.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: ubuntu-autoinstall-staging-tls
      hosts:
        - ubuntu-autoinstall-staging.example.com

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5

config:
  logging:
    level: info
```

### values-production.yaml

```yaml
# file: helm/ubuntu-autoinstall-agent/values-production.yaml
# version: 1.0.0
# guid: helm-values-production

replicaCount: 5

image:
  tag: '1.0.0'
  pullPolicy: IfNotPresent

ingress:
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: '200'
    nginx.ingress.kubernetes.io/enable-modsecurity: 'true'
    nginx.ingress.kubernetes.io/modsecurity-snippet: |
      SecRuleEngine On
      SecRequestBodyAccess On
  hosts:
    - host: ubuntu-autoinstall.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: ubuntu-autoinstall-prod-tls
      hosts:
        - ubuntu-autoinstall.example.com

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 20
  targetCPUUtilizationPercentage: 60
  targetMemoryUtilizationPercentage: 70

podDisruptionBudget:
  enabled: true
  minAvailable: 3

affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
            - key: app
              operator: In
              values:
                - ubuntu-autoinstall-agent
        topologyKey: kubernetes.io/hostname

nodeSelector:
  workload: production

config:
  logging:
    level: warn

postgresql:
  primary:
    persistence:
      size: 50Gi
```

## Helm Templates

### \_helpers.tpl

```yaml
{{/*
file: helm/ubuntu-autoinstall-agent/templates/_helpers.tpl
version: 1.0.0
guid: helm-helpers-tpl
*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "ubuntu-autoinstall-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "ubuntu-autoinstall-agent.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ubuntu-autoinstall-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ubuntu-autoinstall-agent.labels" -}}
helm.sh/chart: {{ include "ubuntu-autoinstall-agent.chart" . }}
{{ include "ubuntu-autoinstall-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ubuntu-autoinstall-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ubuntu-autoinstall-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "ubuntu-autoinstall-agent.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ubuntu-autoinstall-agent.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the appropriate apiVersion for HPA
*/}}
{{- define "ubuntu-autoinstall-agent.hpa.apiVersion" -}}
{{- if semverCompare ">=1.23-0" .Capabilities.KubeVersion.GitVersion }}
{{- print "autoscaling/v2" }}
{{- else }}
{{- print "autoscaling/v2beta2" }}
{{- end }}
{{- end }}

{{/*
Return the appropriate apiVersion for PodDisruptionBudget
*/}}
{{- define "ubuntu-autoinstall-agent.pdb.apiVersion" -}}
{{- if semverCompare ">=1.21-0" .Capabilities.KubeVersion.GitVersion }}
{{- print "policy/v1" }}
{{- else }}
{{- print "policy/v1beta1" }}
{{- end }}
{{- end }}
```

### deployment.yaml Template

```yaml
{{/*
file: helm/ubuntu-autoinstall-agent/templates/deployment.yaml
version: 1.0.0
guid: helm-deployment-template
*/}}

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "ubuntu-autoinstall-agent.fullname" . }}
  labels:
    {{- include "ubuntu-autoinstall-agent.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      {{- include "ubuntu-autoinstall-agent.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        checksum/secret: {{ include (print $.Template.BasePath "/secret.yaml") . | sha256sum }}
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
      labels:
        {{- include "ubuntu-autoinstall-agent.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "ubuntu-autoinstall-agent.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
      - name: {{ .Chart.Name }}
        securityContext:
          {{- toYaml .Values.securityContext | nindent 12 }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.config.server.port }}
          protocol: TCP
        - name: metrics
          containerPort: 9090
          protocol: TCP
        env:
        - name: RUST_LOG
          value: {{ .Values.config.logging.level }}
        - name: SERVER_PORT
          value: {{ .Values.config.server.port | quote }}
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: {{ include "ubuntu-autoinstall-agent.fullname" . }}-secret
              key: database-url
        livenessProbe:
          {{- toYaml .Values.livenessProbe | nindent 12 }}
        readinessProbe:
          {{- toYaml .Values.readinessProbe | nindent 12 }}
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
        volumeMounts:
        - name: config
          mountPath: /etc/ubuntu-autoinstall
          readOnly: true
        {{- if .Values.persistence.enabled }}
        - name: cache
          mountPath: /var/cache/ubuntu-autoinstall
        {{- end }}
      volumes:
      - name: config
        configMap:
          name: {{ include "ubuntu-autoinstall-agent.fullname" . }}-config
      {{- if .Values.persistence.enabled }}
      - name: cache
        persistentVolumeClaim:
          claimName: {{ include "ubuntu-autoinstall-agent.fullname" . }}-cache
      {{- else }}
      - name: cache
        emptyDir: {}
      {{- end }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

### hpa.yaml Template

```yaml
{{/*
file: helm/ubuntu-autoinstall-agent/templates/hpa.yaml
version: 1.0.0
guid: helm-hpa-template
*/}}

{{- if .Values.autoscaling.enabled }}
apiVersion: {{ include "ubuntu-autoinstall-agent.hpa.apiVersion" . }}
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "ubuntu-autoinstall-agent.fullname" . }}
  labels:
    {{- include "ubuntu-autoinstall-agent.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "ubuntu-autoinstall-agent.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
  {{- if .Values.autoscaling.targetCPUUtilizationPercentage }}
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
  {{- end }}
  {{- if .Values.autoscaling.targetMemoryUtilizationPercentage }}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
  {{- end }}
  {{- with .Values.autoscaling.metrics }}
  {{- toYaml . | nindent 2 }}
  {{- end }}
{{- end }}
```

### NOTES.txt

```text
{{/*
file: helm/ubuntu-autoinstall-agent/templates/NOTES.txt
version: 1.0.0
guid: helm-notes-txt
*/}}

1. Get the application URL by running these commands:
{{- if .Values.ingress.enabled }}
{{- range $host := .Values.ingress.hosts }}
  {{- range .paths }}
  http{{ if $.Values.ingress.tls }}s{{ end }}://{{ $host.host }}{{ .path }}
  {{- end }}
{{- end }}
{{- else if contains "NodePort" .Values.service.type }}
  export NODE_PORT=$(kubectl get --namespace {{ .Release.Namespace }} -o jsonpath="{.spec.ports[0].nodePort}" services {{ include "ubuntu-autoinstall-agent.fullname" . }})
  export NODE_IP=$(kubectl get nodes --namespace {{ .Release.Namespace }} -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT
{{- else if contains "LoadBalancer" .Values.service.type }}
     NOTE: It may take a few minutes for the LoadBalancer IP to be available.
           You can watch the status of by running 'kubectl get --namespace {{ .Release.Namespace }} svc -w {{ include "ubuntu-autoinstall-agent.fullname" . }}'
  export SERVICE_IP=$(kubectl get svc --namespace {{ .Release.Namespace }} {{ include "ubuntu-autoinstall-agent.fullname" . }} --template "{{"{{ range (index .status.loadBalancer.ingress 0) }}{{.}}{{ end }}"}}")
  echo http://$SERVICE_IP:{{ .Values.service.port }}
{{- else if contains "ClusterIP" .Values.service.type }}
  export POD_NAME=$(kubectl get pods --namespace {{ .Release.Namespace }} -l "app.kubernetes.io/name={{ include "ubuntu-autoinstall-agent.name" . }},app.kubernetes.io/instance={{ .Release.Name }}" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace {{ .Release.Namespace }} $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace {{ .Release.Namespace }} port-forward $POD_NAME 8080:$CONTAINER_PORT
{{- end }}

2. Check deployment status:
   kubectl --namespace {{ .Release.Namespace }} get deployments {{ include "ubuntu-autoinstall-agent.fullname" . }}

3. View logs:
   kubectl --namespace {{ .Release.Namespace }} logs -l "app.kubernetes.io/name={{ include "ubuntu-autoinstall-agent.name" . }},app.kubernetes.io/instance={{ .Release.Name }}"
```

---

**Part 2 Complete**: Helm chart with Chart.yaml metadata, comprehensive values.yaml with all
configuration options, environment-specific values files (dev/staging/production), helper templates
for name generation and labels, deployment template with checksums and conditional autoscaling, HPA
template with version compatibility, and NOTES.txt for post-install instructions. ✅

**Continue to Part 3** for Kustomize overlays and GitOps configuration with ArgoCD.
