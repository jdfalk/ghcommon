<!-- file: docs/cross-registry-todos/task-02/t02-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t02-docker-part5-e5f6g7h8-i9j0 -->
<!-- last-edited: 2026-01-19 -->

# Task 02 Part 5: Optimization and Advanced Configuration

## Image Optimization Strategies

### Strategy 1: Multi-Stage Build Optimization

```dockerfile
# file: Dockerfile.optimized
# version: 1.0.0
# guid: dockerfile-optimized

# Build stage
FROM rust:1.70-alpine AS builder

# Install build dependencies
RUN apk add --no-cache musl-dev openssl-dev

# Create app directory
WORKDIR /app

# Copy manifests
COPY Cargo.toml Cargo.lock ./

# Build dependencies (cached layer)
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Copy source
COPY src ./src

# Build application
RUN cargo build --release && \
    strip target/release/app

# Runtime stage
FROM alpine:3.18

# Install runtime dependencies only
RUN apk add --no-cache libgcc openssl ca-certificates

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/app .

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["/app/app", "--health-check"]

ENTRYPOINT ["/app/app"]
```

### Strategy 2: Layer Caching Optimization

```dockerfile
# file: Dockerfile.cached
# version: 1.0.0
# guid: dockerfile-cached

FROM node:18-alpine

WORKDIR /app

# Copy package files first (cached)
COPY package.json package-lock.json ./

# Install dependencies (cached unless package files change)
RUN npm ci --only=production && \
    npm cache clean --force

# Copy source (changes frequently, separate layer)
COPY . .

# Build (cached unless source changes)
RUN npm run build

# Optimize final image
RUN rm -rf node_modules && \
    npm ci --only=production && \
    npm cache clean --force

EXPOSE 3000

CMD ["npm", "start"]
```

### Strategy 3: Minimal Base Images

```dockerfile
# file: Dockerfile.minimal
# version: 1.0.0
# guid: dockerfile-minimal

# Using distroless base image (minimal attack surface)
FROM gcr.io/distroless/static-debian11

# Copy binary (built separately or in multi-stage)
COPY --from=builder /app/binary /app/binary

# Set user
USER nonroot:nonroot

# Run
ENTRYPOINT ["/app/binary"]
```

## Build Arguments and Configuration

### Enhanced Build Configuration

````yaml
# file: .github/workflows/release-docker-enhanced.yml
# version: 1.0.0
# guid: release-docker-enhanced

name: Release Docker (Enhanced)

on:
  workflow_call:
    inputs:
      registry:
        description: 'Container registry'
        required: false
        default: 'ghcr.io'
        type: string

      image-name:
        description: 'Docker image name'
        required: true
        type: string

      dockerfile:
        description: 'Path to Dockerfile'
        required: false
        default: 'Dockerfile'
        type: string

      context:
        description: 'Build context directory'
        required: false
        default: '.'
        type: string

      platforms:
        description: 'Target platforms'
        required: false
        default: 'linux/amd64,linux/arm64'
        type: string

      build-args:
        description: 'Build arguments'
        required: false
        default: ''
        type: string

      enable-security-scan:
        description: 'Enable security scanning'
        required: false
        default: true
        type: boolean

      scan-severity:
        description: 'Scan severity threshold'
        required: false
        default: 'CRITICAL,HIGH'
        type: string

      enable-sbom:
        description: 'Enable SBOM generation'
        required: false
        default: true
        type: boolean

      enable-provenance:
        description: 'Enable provenance attestation'
        required: false
        default: true
        type: boolean

      enable-signing:
        description: 'Enable image signing with Cosign'
        required: false
        default: false
        type: boolean

      cache-mode:
        description: 'Cache mode (min/max)'
        required: false
        default: 'max'
        type: string

permissions:
  contents: read
  packages: write
  id-token: write # For Cosign
  security-events: write # For SARIF upload

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3
        with:
          platforms: 'arm64,arm'

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        with:
          version: latest
          buildkitd-flags: --debug
          driver-opts: |
            image=moby/buildkit:buildx-stable-1
            network=host
          config-inline: |
            [worker.oci]
              max-parallelism = 4
            [registry."docker.io"]
              mirrors = ["mirror.gcr.io"]

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ inputs.registry }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ inputs.registry }}/${{ github.repository_owner }}/${{ inputs.image-name }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=semver,pattern={{version}}-{{sha}},enable={{is_default_branch}}
            type=sha,prefix=sha-,format=short
            type=ref,event=branch
            type=ref,event=pr
            type=raw,value=latest,enable={{is_default_branch}}
            type=schedule,pattern={{date 'YYYYMMDD'}}
          labels: |
            org.opencontainers.image.title=${{ inputs.image-name }}
            org.opencontainers.image.description=${{ github.event.repository.description }}
            org.opencontainers.image.url=${{ github.event.repository.html_url }}
            org.opencontainers.image.source=${{ github.event.repository.clone_url }}
            org.opencontainers.image.version=${{ steps.meta.outputs.version }}
            org.opencontainers.image.created=${{ steps.meta.outputs.created }}
            org.opencontainers.image.revision=${{ github.sha }}
            org.opencontainers.image.licenses=${{ github.event.repository.license.spdx_id }}

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: ${{ inputs.context }}
          file: ${{ inputs.dockerfile }}
          platforms: ${{ inputs.platforms }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=${{ inputs.cache-mode }}
          provenance: ${{ inputs.enable-provenance }}
          sbom: ${{ inputs.enable-sbom }}
          build-args: ${{ inputs.build-args }}
          outputs: |
            type=image,push=true
            type=image,push=true,oci-mediatypes=true,compression=zstd,compression-level=3,force-compression=true

      - name: Update Trivy database
        if: inputs.enable-security-scan
        run: |
          echo "Updating Trivy vulnerability database..."
          docker run --rm aquasec/trivy:latest image --download-db-only

      - name: Run Trivy security scanner
        if: inputs.enable-security-scan
        uses: aquasecurity/trivy-action@0.16.1
        with:
          image-ref:
            ${{ inputs.registry }}/${{ github.repository_owner }}/${{ inputs.image-name }}@${{
            steps.build.outputs.digest }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: ${{ inputs.scan-severity }}
          exit-code: '0' # Don't fail build, just report
          vuln-type: 'os,library'
          scanners: 'vuln,secret,config,license'
          ignore-unfixed: false
          timeout: '10m'

      - name: Upload Trivy results
        if: always() && inputs.enable-security-scan
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
          category: 'trivy-${{ inputs.image-name }}'

      - name: Generate SBOM with Syft
        if: inputs.enable-sbom
        uses: anchore/sbom-action@v0
        with:
          image:
            ${{ inputs.registry }}/${{ github.repository_owner }}/${{ inputs.image-name }}@${{
            steps.build.outputs.digest }}
          format: spdx-json
          output-file: sbom-${{ inputs.image-name }}.spdx.json
          upload-artifact: true
          upload-release-assets: ${{ github.event_name == 'release' }}

      - name: Install Cosign
        if: inputs.enable-signing
        uses: sigstore/cosign-installer@v3

      - name: Sign image with Cosign
        if: inputs.enable-signing && github.event_name != 'pull_request'
        env:
          COSIGN_EXPERIMENTAL: 'true'
        run: |
          cosign sign --yes \
            ${{ inputs.registry }}/${{ github.repository_owner }}/${{ inputs.image-name }}@${{ steps.build.outputs.digest }}

      - name: Generate build summary
        if: always()
        run: |
          cat >> $GITHUB_STEP_SUMMARY << 'EOF'
          ## Docker Build Summary

          **Image**: `${{ inputs.registry }}/${{ github.repository_owner }}/${{ inputs.image-name }}`
          **Digest**: `${{ steps.build.outputs.digest }}`
          **Platforms**: `${{ inputs.platforms }}`

          ### Tags
          ```
          ${{ steps.meta.outputs.tags }}
          ```

          ### Security Scan
          - Trivy: ${{ inputs.enable-security-scan && '✅ Enabled' || '❌ Disabled' }}
          - SBOM: ${{ inputs.enable-sbom && '✅ Generated' || '❌ Skipped' }}
          - Provenance: ${{ inputs.enable-provenance && '✅ Attested' || '❌ Skipped' }}
          - Signing: ${{ inputs.enable-signing && '✅ Signed' || '❌ Unsigned' }}
          EOF
````

## Advanced Caching Strategies

### GitHub Actions Cache

```yaml
- name: Cache Docker layers
  uses: actions/cache@v4
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-buildx-
```

### Registry Cache

```yaml
- name: Build with registry cache
  uses: docker/build-push-action@v5
  with:
    cache-from: |
      type=registry,ref=${{ inputs.registry }}/${{ github.repository_owner }}/${{ inputs.image-name }}:buildcache
    cache-to: |
      type=registry,ref=${{ inputs.registry }}/${{ github.repository_owner }}/${{ inputs.image-name }}:buildcache,mode=max
```

### Local Cache

```yaml
- name: Build with local cache
  uses: docker/build-push-action@v5
  with:
    cache-from: type=local,src=/tmp/.buildx-cache
    cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max

- name: Move cache
  run: |
    rm -rf /tmp/.buildx-cache
    mv /tmp/.buildx-cache-new /tmp/.buildx-cache
```

## Image Signing and Verification

### Cosign Configuration

```bash
#!/bin/bash
# file: scripts/setup-cosign.sh
# version: 1.0.0
# guid: setup-cosign

set -e

echo "=== Setting Up Cosign ==="

# Install Cosign
if ! command -v cosign &> /dev/null; then
  echo "Installing Cosign..."
  brew install cosign
fi

# Generate key pair (optional, keyless signing preferred)
echo ""
echo "Generating key pair..."
cosign generate-key-pair

echo ""
echo "Keys generated:"
ls -la cosign.*

# Store private key in GitHub Secrets
echo ""
echo "⚠️  Store cosign.key contents in GitHub Secret: COSIGN_PRIVATE_KEY"
echo "⚠️  Store cosign.pub in repository for verification"

echo ""
echo "✅ Cosign setup complete"
```

### Sign Image Manually

```bash
#!/bin/bash
# file: scripts/sign-image.sh
# version: 1.0.0
# guid: sign-image

set -e

echo "=== Signing Docker Image ==="

IMAGE="$1"

if [ -z "$IMAGE" ]; then
  echo "Usage: $0 <image>"
  exit 1
fi

# Sign with keyless (recommended)
echo ""
echo "Signing image (keyless)..."
COSIGN_EXPERIMENTAL=1 cosign sign --yes "$IMAGE"

# Or sign with key
# cosign sign --key cosign.key "$IMAGE"

echo ""
echo "✅ Image signed"
```

### Verify Signature

```bash
#!/bin/bash
# file: scripts/verify-signature.sh
# version: 1.0.0
# guid: verify-signature

set -e

echo "=== Verifying Image Signature ==="

IMAGE="$1"

if [ -z "$IMAGE" ]; then
  echo "Usage: $0 <image>"
  exit 1
fi

# Verify with keyless
echo ""
echo "Verifying signature..."
COSIGN_EXPERIMENTAL=1 cosign verify "$IMAGE"

# Or verify with public key
# cosign verify --key cosign.pub "$IMAGE"

echo ""
echo "✅ Signature verified"
```

## Provenance Attestation

### Generate Provenance

```yaml
- name: Generate provenance attestation
  uses: docker/build-push-action@v5
  with:
    provenance: mode=max
    sbom: true
```

### Verify Provenance

```bash
#!/bin/bash
# file: scripts/verify-provenance.sh
# version: 1.0.0
# guid: verify-provenance

set -e

echo "=== Verifying Image Provenance ==="

IMAGE="$1"

if [ -z "$IMAGE" ]; then
  echo "Usage: $0 <image>"
  exit 1
fi

# Verify provenance
echo ""
echo "Fetching provenance attestation..."
cosign verify-attestation \
  --type slsaprovenance \
  "$IMAGE"

# Download and inspect
echo ""
echo "Downloading attestation..."
cosign download attestation "$IMAGE" > provenance.json

echo ""
echo "Provenance Summary:"
jq -r '
  .payload | @base64d | fromjson |
  "Builder: \(.builder.id)",
  "Build Type: \(.buildType)",
  "Invocation ID: \(.invocation.configSource.entryPoint)"
' provenance.json

echo ""
echo "✅ Provenance verified"
```

## Monitoring and Alerting

### Set Up Image Monitoring

```bash
#!/bin/bash
# file: scripts/setup-image-monitoring.sh
# version: 1.0.0
# guid: setup-image-monitoring

set -e

echo "=== Setting Up Image Monitoring ==="

# Create monitoring script
cat > .github/monitoring/check-image-health.sh << 'EOF'
#!/bin/bash
# file: .github/monitoring/check-image-health.sh
# version: 1.0.0
# guid: check-image-health

set -e

IMAGE="ghcr.io/jdfalk/ghcommon/test-app:latest"

echo "=== Image Health Check ==="

# Pull latest
docker pull "$IMAGE"

# Check size
SIZE=$(docker inspect "$IMAGE" | jq -r '.[0].Size')
SIZE_MB=$((SIZE / 1024 / 1024))

echo "Image size: ${SIZE_MB} MB"

if [ "$SIZE_MB" -gt 500 ]; then
  echo "⚠️  Warning: Image size exceeds 500 MB"
fi

# Check vulnerabilities
trivy image --severity CRITICAL,HIGH "$IMAGE" | tee /tmp/vuln-check.txt

CRITICAL=$(grep -c "CRITICAL" /tmp/vuln-check.txt || echo "0")
HIGH=$(grep -c "HIGH" /tmp/vuln-check.txt || echo "0")

echo ""
echo "Vulnerabilities:"
echo "  CRITICAL: $CRITICAL"
echo "  HIGH: $HIGH"

if [ "$CRITICAL" -gt 0 ]; then
  echo "❌ CRITICAL vulnerabilities found"
  exit 1
fi

echo ""
echo "✅ Health check passed"
EOF

chmod +x .github/monitoring/check-image-health.sh

echo ""
echo "✅ Monitoring setup complete"
```

### Create Monitoring Workflow

```yaml
# file: .github/workflows/image-health-check.yml
# version: 1.0.0
# guid: image-health-check

name: Image Health Check

on:
  schedule:
    - cron: '0 */6 * * *' # Every 6 hours
  workflow_dispatch:

permissions:
  contents: read
  packages: read
  issues: write

jobs:
  health-check:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install tools
        run: |
          brew install trivy

      - name: Run health check
        run: |
          .github/monitoring/check-image-health.sh

      - name: Create issue on failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '🚨 Image Health Check Failed',
              body: 'Image health check detected issues. Please investigate.\n\nRun: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}',
              labels: ['bug', 'docker', 'security', 'automated']
            });
```

## Continue to Part 6

Next part covers troubleshooting, lessons learned, and task completion.
