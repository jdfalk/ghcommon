<!-- file: docs/cross-registry-todos/task-16/t16-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t16-deployment-automation-part4-q4r5s6t7-u8v9 -->
<!-- last-edited: 2026-01-19 -->

# Task 16 Part 4: Progressive Delivery with Canary and Blue-Green Deployments

## Flagger Canary Deployment

### Flagger Canary Resource

```yaml
# file: k8s/progressive-delivery/canary.yaml
# version: 1.0.0
# guid: flagger-canary

apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: ubuntu-autoinstall-agent
  namespace: ubuntu-autoinstall-production
spec:
  # Target deployment
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ubuntu-autoinstall-agent

  # Progression deadline in minutes
  progressDeadlineSeconds: 600

  # HPA reference (optional)
  autoscalerRef:
    apiVersion: autoscaling/v2
    kind: HorizontalPodAutoscaler
    name: ubuntu-autoinstall-agent

  service:
    # Service port
    port: 80
    # Container port
    targetPort: 8080
    # Apex domain gateway
    gateways:
      - istio-system/public-gateway
    # Traffic destination
    hosts:
      - ubuntu-autoinstall.example.com
    # HTTP match conditions
    match:
      - uri:
          prefix: /
    # HTTP rewrite
    retries:
      attempts: 3
      perTryTimeout: 30s
    # Request timeout
    timeout: 30s

  analysis:
    # Schedule interval
    interval: 1m
    # Max number of failed metric checks
    threshold: 10
    # Max traffic percentage routed to canary
    maxWeight: 50
    # Canary increment step
    stepWeight: 5

    # Prometheus checks
    metrics:
      - name: request-success-rate
        # Minimum req success rate (non 5xx responses)
        thresholdRange:
          min: 99
        interval: 1m

      - name: request-duration
        # Maximum req duration P99
        thresholdRange:
          max: 500
        interval: 1m

      - name: error-rate
        # Custom metric query
        templateRef:
          name: error-rate
          namespace: flagger-system
        thresholdRange:
          max: 1
        interval: 1m

    # Load testing webhook
    webhooks:
      - name: load-test
        url: http://flagger-loadtester.flagger-system/
        timeout: 5s
        metadata:
          type: cmd
          cmd: 'hey -z 1m -q 10 -c 2 http://ubuntu-autoinstall-agent-canary/api/v1/status'

      - name: acceptance-test
        type: pre-rollout
        url: http://flagger-loadtester.flagger-system/
        timeout: 30s
        metadata:
          type: bash
          cmd: |
            curl -s http://ubuntu-autoinstall-agent-canary/health | grep -q '"status":"healthy"'

      - name: rollback-notification
        type: rollback
        url: http://slack-webhook/
        metadata:
          message: 'Canary rollback detected for ubuntu-autoinstall-agent'
```

### Flagger MetricTemplate

```yaml
# file: k8s/progressive-delivery/metric-template.yaml
# version: 1.0.0
# guid: flagger-metric-template

apiVersion: flagger.app/v1beta1
kind: MetricTemplate
metadata:
  name: error-rate
  namespace: flagger-system
spec:
  provider:
    type: prometheus
    address: http://prometheus.monitoring:9090
  query: |
    100 - sum(
      rate(
        http_requests_total{
          kubernetes_namespace="{{ namespace }}",
          kubernetes_pod_name=~"{{ target }}-[0-9a-zA-Z]+(-[0-9a-zA-Z]+)",
          status!~"5.."
        }[{{ interval }}]
      )
    )
    /
    sum(
      rate(
        http_requests_total{
          kubernetes_namespace="{{ namespace }}",
          kubernetes_pod_name=~"{{ target }}-[0-9a-zA-Z]+(-[0-9a-zA-Z]+)"
        }[{{ interval }}]
      )
    )
    * 100
```

## Argo Rollouts Canary

### Rollout Resource

```yaml
# file: k8s/progressive-delivery/rollout.yaml
# version: 1.0.0
# guid: argo-rollout

apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: ubuntu-autoinstall-agent
  namespace: ubuntu-autoinstall-production
spec:
  replicas: 5
  revisionHistoryLimit: 3

  selector:
    matchLabels:
      app: ubuntu-autoinstall-agent

  template:
    metadata:
      labels:
        app: ubuntu-autoinstall-agent
    spec:
      containers:
        - name: ubuntu-autoinstall-agent
          image: ghcr.io/jdfalk/ubuntu-autoinstall-agent:v1.0.0
          ports:
            - name: http
              containerPort: 8080
          resources:
            limits:
              cpu: 1000m
              memory: 1Gi
            requests:
              cpu: 500m
              memory: 512Mi

  strategy:
    canary:
      # Max surge
      maxSurge: '25%'
      # Max unavailable
      maxUnavailable: 0

      # Canary service
      canaryService: ubuntu-autoinstall-agent-canary
      # Stable service
      stableService: ubuntu-autoinstall-agent-stable

      # Traffic routing
      trafficRouting:
        istio:
          virtualService:
            name: ubuntu-autoinstall-agent
            routes:
              - primary

      # Analysis
      analysis:
        templates:
          - templateName: success-rate
          - templateName: latency
        startingStep: 2
        args:
          - name: service-name
            value: ubuntu-autoinstall-agent

      # Steps
      steps:
        # Step 1: 5% traffic to canary
        - setWeight: 5
        - pause:
            duration: 2m

        # Step 2: 10% traffic (analysis starts)
        - setWeight: 10
        - pause:
            duration: 5m

        # Step 3: 20% traffic
        - setWeight: 20
        - pause:
            duration: 5m

        # Step 4: 40% traffic
        - setWeight: 40
        - pause:
            duration: 5m

        # Step 5: 60% traffic
        - setWeight: 60
        - pause:
            duration: 5m

        # Step 6: 80% traffic
        - setWeight: 80
        - pause:
            duration: 5m

        # Step 7: 100% traffic (promote to stable)
        - setWeight: 100
        - pause:
            duration: 2m
```

### Argo Rollouts AnalysisTemplate

```yaml
# file: k8s/progressive-delivery/analysis-template.yaml
# version: 1.0.0
# guid: argo-analysis-template

apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
  namespace: ubuntu-autoinstall-production
spec:
  args:
    - name: service-name

  metrics:
    - name: success-rate
      interval: 1m
      successCondition: result[0] >= 0.95
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(
              http_requests_total{
                kubernetes_namespace="ubuntu-autoinstall-production",
                service="{{args.service-name}}",
                status!~"5.."
              }[5m]
            )) /
            sum(rate(
              http_requests_total{
                kubernetes_namespace="ubuntu-autoinstall-production",
                service="{{args.service-name}}"
              }[5m]
            ))
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: latency
  namespace: ubuntu-autoinstall-production
spec:
  args:
    - name: service-name

  metrics:
    - name: latency-p95
      interval: 1m
      successCondition: result[0] <= 0.5
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            histogram_quantile(0.95,
              sum(rate(
                http_request_duration_seconds_bucket{
                  kubernetes_namespace="ubuntu-autoinstall-production",
                  service="{{args.service-name}}"
                }[5m]
              )) by (le)
            )
```

## Blue-Green Deployment

### Blue-Green Rollout

```yaml
# file: k8s/progressive-delivery/rollout-bluegreen.yaml
# version: 1.0.0
# guid: argo-rollout-bluegreen

apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: ubuntu-autoinstall-agent-bg
  namespace: ubuntu-autoinstall-production
spec:
  replicas: 5
  revisionHistoryLimit: 2

  selector:
    matchLabels:
      app: ubuntu-autoinstall-agent-bg

  template:
    metadata:
      labels:
        app: ubuntu-autoinstall-agent-bg
    spec:
      containers:
        - name: ubuntu-autoinstall-agent
          image: ghcr.io/jdfalk/ubuntu-autoinstall-agent:v1.0.0
          ports:
            - name: http
              containerPort: 8080
          resources:
            limits:
              cpu: 1000m
              memory: 1Gi
            requests:
              cpu: 500m
              memory: 512Mi

  strategy:
    blueGreen:
      # Active service
      activeService: ubuntu-autoinstall-agent-active
      # Preview service
      previewService: ubuntu-autoinstall-agent-preview

      # Auto promotion
      autoPromotionEnabled: false
      autoPromotionSeconds: 300

      # Scale down delay
      scaleDownDelaySeconds: 30
      scaleDownDelayRevisionLimit: 2

      # Pre-promotion analysis
      prePromotionAnalysis:
        templates:
          - templateName: smoke-test
          - templateName: performance-test
        args:
          - name: service-name
            value: ubuntu-autoinstall-agent-preview

      # Post-promotion analysis
      postPromotionAnalysis:
        templates:
          - templateName: success-rate
          - templateName: latency
        args:
          - name: service-name
            value: ubuntu-autoinstall-agent-active

      # Anti-affinity
      antiAffinity:
        requiredDuringSchedulingIgnoredDuringExecution: {}
        preferredDuringSchedulingIgnoredDuringExecution:
          weight: 1
```

### Blue-Green Analysis Templates

```yaml
# file: k8s/progressive-delivery/bluegreen-analysis.yaml
# version: 1.0.0
# guid: bluegreen-analysis-template

apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: smoke-test
  namespace: ubuntu-autoinstall-production
spec:
  args:
    - name: service-name

  metrics:
    - name: smoke-test
      count: 1
      provider:
        job:
          spec:
            backoffLimit: 0
            template:
              spec:
                restartPolicy: Never
                containers:
                  - name: smoke-test
                    image: curlimages/curl:latest
                    command:
                      - sh
                      - -c
                      - |
                        set -e
                        echo "Running smoke tests..."

                        # Health check
                        curl -f http://{{args.service-name}}/health

                        # API status
                        curl -f http://{{args.service-name}}/api/v1/status

                        # Metrics endpoint
                        curl -f http://{{args.service-name}}:9090/metrics

                        echo "Smoke tests passed!"
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: performance-test
  namespace: ubuntu-autoinstall-production
spec:
  args:
    - name: service-name

  metrics:
    - name: performance-test
      count: 1
      provider:
        job:
          spec:
            backoffLimit: 0
            template:
              spec:
                restartPolicy: Never
                containers:
                  - name: performance-test
                    image: williamyeh/hey:latest
                    command:
                      - sh
                      - -c
                      - |
                        set -e
                        echo "Running performance tests..."

                        # Load test: 100 requests, 10 concurrent
                        hey -n 100 -c 10 -m GET http://{{args.service-name}}/api/v1/status

                        echo "Performance tests completed!"
```

## Deployment Workflows

### GitHub Actions Progressive Deployment

```yaml
# file: .github/workflows/progressive-deployment.yml
# version: 1.0.0
# guid: workflow-progressive-deployment

name: Progressive Deployment

on:
  push:
    branches:
      - main
    tags:
      - 'v*'

jobs:
  deploy-canary:
    name: Deploy Canary
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Setup kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'latest'

      - name: Configure kubeconfig
        run: |
          mkdir -p $HOME/.kube
          echo "${{ secrets.KUBECONFIG }}" | base64 -d > $HOME/.kube/config

      - name: Update image tag
        run: |
          kubectl set image deployment/ubuntu-autoinstall-agent \
            ubuntu-autoinstall-agent=ghcr.io/jdfalk/ubuntu-autoinstall-agent:${{ github.sha }} \
            -n ubuntu-autoinstall-production

      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/ubuntu-autoinstall-agent \
            -n ubuntu-autoinstall-production \
            --timeout=10m

      - name: Check canary status
        run: |
          kubectl get canary ubuntu-autoinstall-agent \
            -n ubuntu-autoinstall-production \
            -o jsonpath='{.status.phase}'

      - name: Promote canary
        if: success()
        run: |
          kubectl argo rollouts promote ubuntu-autoinstall-agent \
            -n ubuntu-autoinstall-production

  deploy-production:
    name: Deploy Production
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')

    steps:
      - uses: actions/checkout@v4

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

      - name: Setup kubectl
        uses: azure/setup-kubectl@v3

      - name: Setup Argo Rollouts plugin
        run: |
          curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
          chmod +x kubectl-argo-rollouts-linux-amd64
          sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts

      - name: Configure kubeconfig
        run: |
          mkdir -p $HOME/.kube
          echo "${{ secrets.KUBECONFIG }}" | base64 -d > $HOME/.kube/config

      - name: Update rollout image
        run: |
          kubectl argo rollouts set image ubuntu-autoinstall-agent-bg \
            ubuntu-autoinstall-agent=ghcr.io/jdfalk/ubuntu-autoinstall-agent:${{ steps.version.outputs.VERSION }} \
            -n ubuntu-autoinstall-production

      - name: Wait for preview
        run: |
          kubectl argo rollouts status ubuntu-autoinstall-agent-bg \
            -n ubuntu-autoinstall-production \
            --timeout=10m

      - name: Run smoke tests
        run: |
          # Tests run automatically via AnalysisTemplate
          sleep 60

      - name: Promote to production
        run: |
          kubectl argo rollouts promote ubuntu-autoinstall-agent-bg \
            -n ubuntu-autoinstall-production

      - name: Wait for promotion
        run: |
          kubectl argo rollouts status ubuntu-autoinstall-agent-bg \
            -n ubuntu-autoinstall-production \
            --timeout=15m

      - name: Notify success
        if: success()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "✅ Production deployment successful: ${{ steps.version.outputs.VERSION }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

      - name: Rollback on failure
        if: failure()
        run: |
          kubectl argo rollouts abort ubuntu-autoinstall-agent-bg \
            -n ubuntu-autoinstall-production
          kubectl argo rollouts undo ubuntu-autoinstall-agent-bg \
            -n ubuntu-autoinstall-production
```

## Deployment Scripts

### Manual Canary Promotion

```bash
#!/bin/bash
# file: scripts/promote-canary.sh
# version: 1.0.0
# guid: script-promote-canary

set -euo pipefail

NAMESPACE="${NAMESPACE:-ubuntu-autoinstall-production}"
ROLLOUT_NAME="${ROLLOUT_NAME:-ubuntu-autoinstall-agent}"

echo "🚀 Promoting canary for ${ROLLOUT_NAME} in ${NAMESPACE}"

# Check current status
echo "📊 Current rollout status:"
kubectl argo rollouts status "${ROLLOUT_NAME}" -n "${NAMESPACE}"

# Get current step
CURRENT_STEP=$(kubectl argo rollouts get rollout "${ROLLOUT_NAME}" -n "${NAMESPACE}" -o json | jq -r '.status.currentStepIndex')
echo "Current step: ${CURRENT_STEP}"

# Check analysis results
echo "📈 Checking analysis results..."
ANALYSIS_RUN=$(kubectl get analysisrun -n "${NAMESPACE}" -l rollout="${ROLLOUT_NAME}" --sort-by=.metadata.creationTimestamp -o json | jq -r '.items[-1].metadata.name')

if [ -n "${ANALYSIS_RUN}" ]; then
  ANALYSIS_STATUS=$(kubectl get analysisrun "${ANALYSIS_RUN}" -n "${NAMESPACE}" -o jsonpath='{.status.phase}')
  echo "Analysis status: ${ANALYSIS_STATUS}"

  if [ "${ANALYSIS_STATUS}" != "Successful" ]; then
    echo "❌ Analysis not successful. Current status: ${ANALYSIS_STATUS}"
    exit 1
  fi
fi

# Confirm promotion
read -p "Promote canary to next step? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Promotion cancelled"
  exit 0
fi

# Promote
echo "⏫ Promoting canary..."
kubectl argo rollouts promote "${ROLLOUT_NAME}" -n "${NAMESPACE}"

# Wait for next step
echo "⏳ Waiting for rollout to complete..."
kubectl argo rollouts status "${ROLLOUT_NAME}" -n "${NAMESPACE}" --timeout=5m

echo "✅ Canary promoted successfully!"
```

### Manual Rollback

```bash
#!/bin/bash
# file: scripts/rollback-deployment.sh
# version: 1.0.0
# guid: script-rollback-deployment

set -euo pipefail

NAMESPACE="${NAMESPACE:-ubuntu-autoinstall-production}"
ROLLOUT_NAME="${ROLLOUT_NAME:-ubuntu-autoinstall-agent}"

echo "⚠️  Rolling back ${ROLLOUT_NAME} in ${NAMESPACE}"

# Confirm rollback
read -p "Are you sure you want to rollback? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Rollback cancelled"
  exit 0
fi

# Abort current rollout
echo "🛑 Aborting current rollout..."
kubectl argo rollouts abort "${ROLLOUT_NAME}" -n "${NAMESPACE}" || true

# Rollback to previous version
echo "⏪ Rolling back to previous version..."
kubectl argo rollouts undo "${ROLLOUT_NAME}" -n "${NAMESPACE}"

# Wait for rollback
echo "⏳ Waiting for rollback to complete..."
kubectl argo rollouts status "${ROLLOUT_NAME}" -n "${NAMESPACE}" --timeout=5m

# Verify health
echo "🏥 Verifying application health..."
sleep 10

POD_STATUS=$(kubectl get pods -n "${NAMESPACE}" -l app="${ROLLOUT_NAME}" -o jsonpath='{.items[*].status.phase}' | tr ' ' '\n' | sort | uniq -c)
echo "Pod status:"
echo "${POD_STATUS}"

echo "✅ Rollback completed!"
```

---

**Part 4 Complete**: Progressive delivery with Flagger canary deployment (Prometheus metrics,
webhooks, load testing), Argo Rollouts canary strategy with traffic routing and analysis templates,
blue-green deployment with pre/post-promotion analysis, smoke tests and performance tests, GitHub
Actions workflows for automated progressive deployment, manual promotion and rollback scripts. ✅

**Continue to Part 5** for infrastructure as code with Terraform and deployment automation best
practices.
