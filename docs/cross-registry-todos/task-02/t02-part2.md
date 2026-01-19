<!-- file: docs/cross-registry-todos/task-02/t02-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t02-docker-part2-b2c3d4e5-f6a7 -->
<!-- last-edited: 2026-01-19 -->

# Task 02 Part 2: Workflow Configuration Detection and Analysis

## Detect Current Workflow Configuration

### Step 1: Extract Complete Workflow

```bash
#!/bin/bash
# file: scripts/extract-docker-workflow.sh
# version: 1.0.0
# guid: extract-docker-workflow

set -e

echo "=== Extracting Docker Workflow Configuration ==="

WORKFLOW_FILE=".github/workflows/release-docker.yml"

if [ ! -f "$WORKFLOW_FILE" ]; then
  echo "❌ Workflow file not found: $WORKFLOW_FILE"
  exit 1
fi

# Extract key sections
echo ""
echo "=== Workflow Inputs ==="
yq '.on.workflow_call.inputs' "$WORKFLOW_FILE"

echo ""
echo "=== Jobs ==="
yq '.jobs | keys' "$WORKFLOW_FILE"

echo ""
echo "=== Build Job Steps ==="
yq '.jobs.build.steps[].name' "$WORKFLOW_FILE"

echo ""
echo "✅ Extraction complete"
```

### Step 2: Analyze Inputs

```bash
#!/bin/bash
# file: scripts/analyze-workflow-inputs.sh
# version: 1.0.0
# guid: analyze-workflow-inputs

set -e

WORKFLOW_FILE=".github/workflows/release-docker.yml"

echo "=== Analyzing Workflow Inputs ==="

# Check registry input
echo ""
echo "Registry Input:"
if grep -q "registry:" "$WORKFLOW_FILE"; then
  DEFAULT_REGISTRY=$(yq '.on.workflow_call.inputs.registry.default' "$WORKFLOW_FILE")
  echo "  Default: $DEFAULT_REGISTRY"
  echo "  ✅ Registry input configured"
else
  echo "  ❌ Registry input missing"
fi

# Check image-name input
echo ""
echo "Image Name Input:"
if grep -q "image-name:" "$WORKFLOW_FILE"; then
  REQUIRED=$(yq '.on.workflow_call.inputs.image-name.required' "$WORKFLOW_FILE")
  echo "  Required: $REQUIRED"
  echo "  ✅ Image name input configured"
else
  echo "  ❌ Image name input missing"
fi

# Check platforms input
echo ""
echo "Platforms Input:"
if grep -q "platforms:" "$WORKFLOW_FILE"; then
  DEFAULT_PLATFORMS=$(yq '.on.workflow_call.inputs.platforms.default' "$WORKFLOW_FILE")
  echo "  Default: $DEFAULT_PLATFORMS"
  echo "  ✅ Platforms input configured"
else
  echo "  ❌ Platforms input missing"
fi

# Check security scan input
echo ""
echo "Security Scan Input:"
if grep -q "enable-security-scan:" "$WORKFLOW_FILE"; then
  DEFAULT_SCAN=$(yq '.on.workflow_call.inputs.enable-security-scan.default' "$WORKFLOW_FILE")
  echo "  Default: $DEFAULT_SCAN"
  echo "  ✅ Security scan input configured"
else
  echo "  ❌ Security scan input missing"
fi

echo ""
echo "✅ Input analysis complete"
```

### Expected Input Configuration

```yaml
on:
  workflow_call:
    inputs:
      registry:
        description: 'Container registry (docker.io or ghcr.io)'
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
        description: 'Build arguments (key=value pairs, one per line)'
        required: false
        default: ''
        type: string

      enable-security-scan:
        description: 'Enable Trivy security scanning'
        required: false
        default: true
        type: boolean

      scan-severity:
        description: 'Severity levels to scan for'
        required: false
        default: 'CRITICAL,HIGH'
        type: string
```

## Analyze Build Steps

### Step 3: Check Docker Login

```bash
#!/bin/bash
# file: scripts/check-docker-login.sh
# version: 1.0.0
# guid: check-docker-login

set -e

WORKFLOW_FILE=".github/workflows/release-docker.yml"

echo "=== Checking Docker Login Configuration ==="

# Extract login step
echo ""
echo "Docker Login Step:"
yq '.jobs.build.steps[] | select(.uses | contains("docker/login-action"))' "$WORKFLOW_FILE"

# Check for credentials
echo ""
echo "Credentials Check:"

if grep -q "docker/login-action" "$WORKFLOW_FILE"; then
  echo "  ✅ Login action found"

  # Check registry
  if yq '.jobs.build.steps[] | select(.uses | contains("docker/login-action")) | .with.registry' "$WORKFLOW_FILE" | grep -q "inputs.registry"; then
    echo "  ✅ Registry from inputs"
  else
    echo "  ⚠️  Registry hardcoded"
  fi

  # Check username
  if yq '.jobs.build.steps[] | select(.uses | contains("docker/login-action")) | .with.username' "$WORKFLOW_FILE" | grep -q "github.actor"; then
    echo "  ✅ Username: github.actor"
  else
    echo "  ⚠️  Username: custom"
  fi

  # Check password
  if yq '.jobs.build.steps[] | select(.uses | contains("docker/login-action")) | .with.password' "$WORKFLOW_FILE" | grep -q "GITHUB_TOKEN"; then
    echo "  ✅ Password: GITHUB_TOKEN"
  else
    echo "  ⚠️  Password: custom secret"
  fi
else
  echo "  ❌ Login action not found"
fi

echo ""
echo "✅ Login check complete"
```

### Expected Login Configuration

```yaml
- name: Log in to Container Registry
  uses: docker/login-action@v3
  with:
    registry: ${{ inputs.registry }}
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}

# For Docker Hub
- name: Log in to Docker Hub
  if: inputs.registry == 'docker.io'
  uses: docker/login-action@v3
  with:
    registry: docker.io
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

### Step 4: Check BuildX Setup

```bash
#!/bin/bash
# file: scripts/check-buildx-setup.sh
# version: 1.0.0
# guid: check-buildx-setup

set -e

WORKFLOW_FILE=".github/workflows/release-docker.yml"

echo "=== Checking Docker BuildX Setup ==="

# Check for setup-buildx-action
echo ""
echo "BuildX Setup:"
if grep -q "docker/setup-buildx-action" "$WORKFLOW_FILE"; then
  echo "  ✅ BuildX action found"

  # Check version
  VERSION=$(yq '.jobs.build.steps[] | select(.uses | contains("docker/setup-buildx-action")) | .uses' "$WORKFLOW_FILE")
  echo "  Version: $VERSION"

  # Check config
  if yq '.jobs.build.steps[] | select(.uses | contains("docker/setup-buildx-action")) | .with.buildkitd-flags' "$WORKFLOW_FILE" | grep -q "debug"; then
    echo "  ✅ Debug flags enabled"
  else
    echo "  ⚠️  Debug flags not set"
  fi
else
  echo "  ❌ BuildX action not found"
fi

# Check for QEMU setup (required for multi-platform)
echo ""
echo "QEMU Setup:"
if grep -q "docker/setup-qemu-action" "$WORKFLOW_FILE"; then
  echo "  ✅ QEMU action found"
else
  echo "  ⚠️  QEMU action missing (required for ARM builds)"
fi

echo ""
echo "✅ BuildX check complete"
```

### Expected BuildX Configuration

```yaml
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
```

### Step 5: Check Metadata Extraction

```bash
#!/bin/bash
# file: scripts/check-metadata-extraction.sh
# version: 1.0.0
# guid: check-metadata-extraction

set -e

WORKFLOW_FILE=".github/workflows/release-docker.yml"

echo "=== Checking Metadata Extraction ==="

# Check for docker/metadata-action
echo ""
echo "Metadata Action:"
if grep -q "docker/metadata-action" "$WORKFLOW_FILE"; then
  echo "  ✅ Metadata action found"

  # Check images config
  if yq '.jobs.build.steps[] | select(.uses | contains("docker/metadata-action")) | .with.images' "$WORKFLOW_FILE" | grep -q "inputs.registry"; then
    echo "  ✅ Images configured from inputs"
  else
    echo "  ⚠️  Images hardcoded"
  fi

  # Check tags config
  echo ""
  echo "  Tag Configuration:"
  yq '.jobs.build.steps[] | select(.uses | contains("docker/metadata-action")) | .with.tags' "$WORKFLOW_FILE"
else
  echo "  ❌ Metadata action not found"
fi

echo ""
echo "✅ Metadata check complete"
```

### Expected Metadata Configuration

```yaml
- name: Extract metadata
  id: meta
  uses: docker/metadata-action@v5
  with:
    images: ${{ inputs.registry }}/${{ inputs.image-name }}
    tags: |
      type=semver,pattern={{version}}
      type=semver,pattern={{major}}.{{minor}}
      type=semver,pattern={{major}}
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
```

### Step 6: Check Build and Push

```bash
#!/bin/bash
# file: scripts/check-build-push.sh
# version: 1.0.0
# guid: check-build-push

set -e

WORKFLOW_FILE=".github/workflows/release-docker.yml"

echo "=== Checking Build and Push Configuration ==="

# Check for build-push-action
echo ""
echo "Build and Push Action:"
if grep -q "docker/build-push-action" "$WORKFLOW_FILE"; then
  echo "  ✅ Build-push action found"

  # Check version
  VERSION=$(yq '.jobs.build.steps[] | select(.uses | contains("docker/build-push-action")) | .uses' "$WORKFLOW_FILE")
  echo "  Version: $VERSION"

  # Check key configurations
  echo ""
  echo "  Configuration:"

  # Push enabled
  if yq '.jobs.build.steps[] | select(.uses | contains("docker/build-push-action")) | .with.push' "$WORKFLOW_FILE" | grep -q "true"; then
    echo "    ✅ Push enabled"
  else
    echo "    ⚠️  Push not enabled"
  fi

  # Platforms
  if yq '.jobs.build.steps[] | select(.uses | contains("docker/build-push-action")) | .with.platforms' "$WORKFLOW_FILE" | grep -q "inputs.platforms"; then
    echo "    ✅ Platforms from inputs"
  else
    echo "    ⚠️  Platforms hardcoded"
  fi

  # Cache
  if yq '.jobs.build.steps[] | select(.uses | contains("docker/build-push-action")) | .with.cache-from' "$WORKFLOW_FILE" | grep -q "type=gha"; then
    echo "    ✅ GitHub Actions cache configured"
  else
    echo "    ⚠️  Cache not configured"
  fi

  # Provenance
  if yq '.jobs.build.steps[] | select(.uses | contains("docker/build-push-action")) | .with.provenance' "$WORKFLOW_FILE" | grep -q "true"; then
    echo "    ✅ Provenance enabled"
  else
    echo "    ⚠️  Provenance not enabled"
  fi

  # SBOM
  if yq '.jobs.build.steps[] | select(.uses | contains("docker/build-push-action")) | .with.sbom' "$WORKFLOW_FILE" | grep -q "true"; then
    echo "    ✅ SBOM enabled"
  else
    echo "    ⚠️  SBOM not enabled"
  fi
else
  echo "  ❌ Build-push action not found"
fi

echo ""
echo "✅ Build and push check complete"
```

### Expected Build Configuration

```yaml
- name: Build and push Docker image
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
    cache-to: type=gha,mode=max
    provenance: true
    sbom: true
    build-args: ${{ inputs.build-args }}
    outputs: |
      type=image,push=true
      type=image,push=true,oci-mediatypes=true,compression=zstd
```

## Security Scanning Analysis

### Step 7: Check Trivy Configuration

```bash
#!/bin/bash
# file: scripts/check-trivy-config.sh
# version: 1.0.0
# guid: check-trivy-config

set -e

WORKFLOW_FILE=".github/workflows/release-docker.yml"

echo "=== Checking Trivy Security Scanning ==="

# Check for trivy-action
echo ""
echo "Trivy Action:"
if grep -q "trivy-action" "$WORKFLOW_FILE"; then
  echo "  ✅ Trivy action found"

  # Check version pinning
  VERSION=$(yq '.jobs.build.steps[] | select(.uses | contains("trivy-action")) | .uses' "$WORKFLOW_FILE")
  if echo "$VERSION" | grep -q "@master"; then
    echo "  ⚠️  Using @master (should pin version)"
  else
    echo "  ✅ Version pinned: $VERSION"
  fi

  # Check image ref
  if yq '.jobs.build.steps[] | select(.uses | contains("trivy-action")) | .with.image-ref' "$WORKFLOW_FILE" | grep -q "steps.meta.outputs.tags"; then
    echo "  ⚠️  Using all tags (may scan wrong image)"
  else
    echo "  ✅ Image ref configured"
  fi

  # Check format
  FORMAT=$(yq '.jobs.build.steps[] | select(.uses | contains("trivy-action")) | .with.format' "$WORKFLOW_FILE")
  echo "  Output format: $FORMAT"

  # Check severity
  if yq '.jobs.build.steps[] | select(.uses | contains("trivy-action")) | .with.severity' "$WORKFLOW_FILE" | grep -q "."; then
    SEVERITY=$(yq '.jobs.build.steps[] | select(.uses | contains("trivy-action")) | .with.severity' "$WORKFLOW_FILE")
    echo "  Severity filter: $SEVERITY"
  else
    echo "  ⚠️  No severity filter"
  fi
else
  echo "  ❌ Trivy action not found"
fi

echo ""
echo "✅ Trivy check complete"
```

### Enhanced Trivy Configuration

```yaml
- name: Update Trivy database
  if: inputs.enable-security-scan
  run: |
    echo "Updating Trivy vulnerability database..."
    trivy image --download-db-only
    echo "✅ Database updated"

- name: Run Trivy security scanner
  if: inputs.enable-security-scan
  uses: aquasecurity/trivy-action@0.16.1
  with:
    image-ref: ${{ inputs.registry }}/${{ inputs.image-name }}:${{ steps.meta.outputs.version }}
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: ${{ inputs.scan-severity }}
    exit-code: '1'
    vuln-type: 'os,library'
    scanners: 'vuln,secret,config,license'
    ignore-unfixed: false
    skip-dirs: '/usr/local/go'
    timeout: '10m'

- name: Upload Trivy results to GitHub Security
  if: always() && inputs.enable-security-scan
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: 'trivy-results.sarif'
    category: 'trivy-${{ inputs.image-name }}'

- name: Generate Trivy HTML report
  if: always() && inputs.enable-security-scan
  uses: aquasecurity/trivy-action@0.16.1
  with:
    image-ref: ${{ inputs.registry }}/${{ inputs.image-name }}:${{ steps.meta.outputs.version }}
    format: 'template'
    template: '@/contrib/html.tpl'
    output: 'trivy-report.html'

- name: Upload Trivy HTML report
  if: always() && inputs.enable-security-scan
  uses: actions/upload-artifact@v4
  with:
    name: trivy-report-${{ inputs.image-name }}
    path: trivy-report.html
    retention-days: 30
```

## SBOM Generation Analysis

### Step 8: Check SBOM Configuration

```bash
#!/bin/bash
# file: scripts/check-sbom-config.sh
# version: 1.0.0
# guid: check-sbom-config

set -e

WORKFLOW_FILE=".github/workflows/release-docker.yml"

echo "=== Checking SBOM Generation ==="

# Check in build-push-action
echo ""
echo "Build-Push SBOM:"
if yq '.jobs.build.steps[] | select(.uses | contains("docker/build-push-action")) | .with.sbom' "$WORKFLOW_FILE" | grep -q "true"; then
  echo "  ✅ SBOM enabled in build-push-action"
else
  echo "  ⚠️  SBOM not enabled in build-push-action"
fi

# Check for dedicated SBOM action
echo ""
echo "Dedicated SBOM Action:"
if grep -q "sbom-action" "$WORKFLOW_FILE" || grep -q "syft-action" "$WORKFLOW_FILE"; then
  echo "  ✅ Dedicated SBOM action found"
else
  echo "  ⚠️  No dedicated SBOM action"
fi

echo ""
echo "✅ SBOM check complete"
```

### Enhanced SBOM Configuration

```yaml
- name: Generate SBOM with Syft
  uses: anchore/sbom-action@v0
  with:
    image: ${{ inputs.registry }}/${{ inputs.image-name }}:${{ steps.meta.outputs.version }}
    format: spdx-json
    output-file: sbom-${{ inputs.image-name }}.spdx.json
    upload-artifact: true
    upload-release-assets: ${{ github.event_name == 'release' }}

- name: Generate CycloneDX SBOM
  run: |
    syft ${{ inputs.registry }}/${{ inputs.image-name }}:${{ steps.meta.outputs.version }} \
      -o cyclonedx-json \
      > sbom-${{ inputs.image-name }}.cyclonedx.json

- name: Upload SBOM artifacts
  uses: actions/upload-artifact@v4
  with:
    name: sbom-${{ inputs.image-name }}
    path: |
      sbom-${{ inputs.image-name }}.spdx.json
      sbom-${{ inputs.image-name }}.cyclonedx.json
    retention-days: 90
```

## Continue to Part 3

Next part covers local testing procedures and validation scripts.
