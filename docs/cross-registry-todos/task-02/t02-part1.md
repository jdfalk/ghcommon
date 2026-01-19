<!-- file: docs/cross-registry-todos/task-02/t02-part1.md -->
<!-- version: 1.0.0 -->
<!-- guid: t02-docker-part1-a1b2c3d4-e5f6 -->
<!-- last-edited: 2026-01-19 -->

# Task 02 Part 1: Docker Package Publishing - Overview and Analysis

## Task Overview

### Purpose

**What**: Verify and optimize Docker image publishing to GitHub Container Registry (ghcr.io)

**Why**: Ensure Docker images are correctly published with proper tagging, security scanning, SBOM
generation, and provenance attestation

**Where**:

- Primary: `.github/workflows/release-docker.yml`
- Related: `Dockerfile`, `.dockerignore`, container scanning configs

**Expected Outcome**: Confirmed working Docker image publishing with:

- ✅ Correct multi-platform builds (linux/amd64, linux/arm64)
- ✅ Proper semantic version tagging
- ✅ Security scanning (Trivy/Grype)
- ✅ SBOM generation
- ✅ Provenance attestation
- ✅ Image optimization (multi-stage builds, layer caching)

**Estimated Time**: 2-3 hours (comprehensive verification, optimization, and testing)

**Risk Level**: Low (verification and optimization task, non-breaking changes)

## Repository Context

### ghcr.io Registry

**GitHub Container Registry provides:**

- Free unlimited public packages
- Private packages (limited by organization plan)
- Docker Hub compatibility
- GitHub Actions integration
- Fine-grained access control
- Automatic cleanup policies

**ghcr.io URL structure:**

```
ghcr.io/<owner>/<repo>/<image>:<tag>

Examples:
ghcr.io/jdfalk/ghcommon/example-app:latest
ghcr.io/jdfalk/ghcommon/example-app:v1.2.3
ghcr.io/jdfalk/ghcommon/example-app:sha-abc1234
```

### Current Implementation Status

From `.github/workflows/release-docker.yml`:

**Workflow Features:**

- ✅ Reusable workflow design
- ✅ Multi-platform builds (linux/amd64, linux/arm64)
- ✅ Semantic version tagging
- ✅ Docker Hub/ghcr.io support
- ✅ BuildKit with layer caching
- ⚠️ Security scanning (needs verification)
- ⚠️ SBOM generation (needs verification)
- ⚠️ Provenance attestation (needs verification)

**Inputs:**

```yaml
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

  enable-security-scan:
    description: 'Enable Trivy security scanning'
    required: false
    default: true
    type: boolean
```

## Problem Analysis

### Issue 1: Verify Push to ghcr.io

**Current State:**

```yaml
- name: Log in to Container Registry
  uses: docker/login-action@v3
  with:
    registry: ${{ inputs.registry }}
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

**Analysis:**

- ✅ Uses `docker/login-action@v3` (correct)
- ✅ Supports both docker.io and ghcr.io via input
- ✅ Uses `GITHUB_TOKEN` for authentication (correct for ghcr.io)
- ⚠️ Username `github.actor` works for ghcr.io but requires different approach for docker.io

**Verification Needed:**

1. Confirm images appear in GitHub Packages UI
2. Verify pull access without authentication (for public images)
3. Test multi-platform manifest correctness
4. Check image metadata and labels

### Issue 2: Tagging Strategy

**Current Tags:**

```yaml
tags: |
  type=semver,pattern={{version}}
  type=semver,pattern={{major}}.{{minor}}
  type=semver,pattern={{major}}
  type=sha,prefix=sha-
  type=raw,value=latest,enable={{is_default_branch}}
```

**Analysis:**

- ✅ Semantic versioning support (v1.2.3 → 1.2.3, 1.2, 1)
- ✅ SHA-based tags for commit tracking
- ✅ Latest tag only on default branch
- ⚠️ No staging/beta/rc tags
- ⚠️ No date-based tags for debugging

**Recommended Additions:**

```yaml
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
```

### Issue 3: Multi-Platform Builds

**Current Configuration:**

```yaml
platforms: ${{ inputs.platforms }}
# Default: 'linux/amd64,linux/arm64'
```

**Analysis:**

- ✅ Supports linux/amd64 (Intel/AMD x86_64)
- ✅ Supports linux/arm64 (ARM 64-bit, Apple Silicon, AWS Graviton)
- ❌ Missing linux/arm/v7 (32-bit ARM, Raspberry Pi)
- ❌ Missing windows/amd64 (Windows containers)

**Platform Coverage:**

| Platform      | Support | Use Cases                                       |
| ------------- | ------- | ----------------------------------------------- |
| linux/amd64   | ✅      | Standard x86_64 servers, most cloud instances   |
| linux/arm64   | ✅      | Apple Silicon, AWS Graviton, modern ARM servers |
| linux/arm/v7  | ❌      | Raspberry Pi, older ARM devices                 |
| linux/arm/v6  | ❌      | Older Raspberry Pi models                       |
| windows/amd64 | ❌      | Windows containers                              |

**Recommendation:**

- Keep current platforms for most use cases
- Add linux/arm/v7 only if Raspberry Pi support needed
- Windows containers require separate Dockerfile

### Issue 4: Build Optimization

**Layer Caching:**

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
  with:
    buildkitd-flags: --debug
```

**Analysis:**

- ✅ BuildKit enabled (modern Docker build engine)
- ✅ Debug flags for troubleshooting
- ⚠️ Missing GitHub Actions cache integration
- ⚠️ No local cache optimization

**Recommended Cache Configuration:**

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
  with:
    buildkitd-flags: --debug
    config-inline: |
      [registry."docker.io"]
        mirrors = ["mirror.gcr.io"]
      [worker.oci]
        max-parallelism = 4

- name: Cache Docker layers
  uses: actions/cache@v4
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-buildx-
```

### Issue 5: Security Scanning

**Current Implementation:**

```yaml
- name: Run Trivy security scanner
  if: inputs.enable-security-scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ steps.meta.outputs.tags }}
    format: 'sarif'
    output: 'trivy-results.sarif'
```

**Analysis:**

- ✅ Trivy scanner integration
- ✅ SARIF output format (GitHub Security tab compatible)
- ⚠️ Uses `@master` (should pin to version)
- ⚠️ Only scans first tag (multi-tag issue)
- ❌ Missing vulnerability database update
- ❌ No severity threshold enforcement
- ❌ Missing Grype alternative scanner

**Enhanced Security Configuration:**

```yaml
- name: Update Trivy DB
  if: inputs.enable-security-scan
  run: |
    trivy image --download-db-only

- name: Run Trivy security scanner
  if: inputs.enable-security-scan
  uses: aquasecurity/trivy-action@0.16.1 # Pinned version
  with:
    image-ref: ${{ inputs.registry }}/${{ inputs.image-name }}:${{ steps.meta.outputs.version }}
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'
    exit-code: '1' # Fail on critical vulnerabilities
    vuln-type: 'os,library'
    scanners: 'vuln,secret,config'

- name: Upload Trivy results to GitHub Security
  if: always()
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: 'trivy-results.sarif'
    category: 'trivy'

- name: Run Grype scanner (alternative)
  if: inputs.enable-security-scan
  uses: anchore/scan-action@v3
  with:
    image: ${{ inputs.registry }}/${{ inputs.image-name }}:${{ steps.meta.outputs.version }}
    fail-build: true
    severity-cutoff: high
```

### Issue 6: SBOM Generation

**Current Implementation:**

- ❌ No SBOM generation found in workflow

**Analysis:** SBOM (Software Bill of Materials) provides:

- Complete dependency inventory
- License compliance tracking
- Supply chain security
- Vulnerability tracking

**Recommended SBOM Configuration:**

```yaml
- name: Generate SBOM with Syft
  uses: anchore/sbom-action@v0
  with:
    image: ${{ inputs.registry }}/${{ inputs.image-name }}:${{ steps.meta.outputs.version }}
    format: spdx-json
    output-file: sbom.spdx.json
    upload-artifact: true
    upload-release-assets: true

- name: Generate SBOM with Docker Scout
  run: |
    docker scout sbom ${{ inputs.registry }}/${{ inputs.image-name }}:${{ steps.meta.outputs.version }} \
      --format spdx \
      --output sbom-scout.spdx.json
```

### Issue 7: Provenance Attestation

**Current Implementation:**

- ❌ No provenance attestation found

**Analysis:** Provenance attestation provides:

- Build reproducibility
- Supply chain verification
- SLSA compliance
- Cosign signing support

**Recommended Provenance Configuration:**

```yaml
- name: Generate provenance
  uses: docker/build-push-action@v5
  with:
    provenance: true
    sbom: true
    attestation-manifest-push: true

- name: Sign image with Cosign
  if: github.event_name != 'pull_request'
  env:
    COSIGN_EXPERIMENTAL: 'true'
  run: |
    cosign sign --yes \
      ${{ inputs.registry }}/${{ inputs.image-name }}@${{ steps.build.outputs.digest }}
```

## Prerequisites

### Required Tools

```bash
# Verify installation
docker --version          # >= 20.10
docker buildx version     # >= 0.10
gh --version             # >= 2.20
trivy --version          # >= 0.40 (for local testing)
syft version             # >= 0.70 (for SBOM)
cosign version           # >= 2.0 (for signing)
```

### Install Missing Tools

```bash
#!/bin/bash
# file: scripts/install-docker-tools.sh
# version: 1.0.0
# guid: install-docker-tools

set -e

echo "=== Installing Docker Publishing Tools ==="

# Trivy
if ! command -v trivy &> /dev/null; then
  echo "Installing Trivy..."
  brew install trivy
else
  echo "✅ Trivy installed: $(trivy --version)"
fi

# Syft
if ! command -v syft &> /dev/null; then
  echo "Installing Syft..."
  brew install syft
else
  echo "✅ Syft installed: $(syft version)"
fi

# Cosign
if ! command -v cosign &> /dev/null; then
  echo "Installing Cosign..."
  brew install cosign
else
  echo "✅ Cosign installed: $(cosign version)"
fi

# Docker Buildx
if ! docker buildx version &> /dev/null; then
  echo "Installing Docker Buildx..."
  docker buildx install
else
  echo "✅ Docker Buildx installed: $(docker buildx version)"
fi

echo ""
echo "✅ All tools installed"
```

### Required Permissions

**Repository Settings:**

- Actions: Read and write permissions
- Packages: Read and write permissions
- Security: Write access for SARIF upload

**Secrets Required:**

- `GITHUB_TOKEN` - Automatic (for ghcr.io)
- `DOCKERHUB_TOKEN` - Optional (for Docker Hub)
- `COSIGN_PASSWORD` - Optional (for image signing)

**Environment Variables:**

- `DOCKER_BUILDKIT=1` - BuildKit enabled
- `BUILDX_NO_DEFAULT_ATTESTATIONS=1` - Control attestations

## Validation Strategy

### Phase 1: Static Analysis

```bash
# Validate workflow syntax
gh workflow view release-docker --yaml > /dev/null && echo "✅ Syntax valid"

# Check for required components
grep -q "docker/login-action" .github/workflows/release-docker.yml && echo "✅ Login configured"
grep -q "docker/build-push-action" .github/workflows/release-docker.yml && echo "✅ Build/push configured"
grep -q "trivy-action" .github/workflows/release-docker.yml && echo "✅ Security scan configured"
```

### Phase 2: Local Testing

```bash
# Test multi-platform build locally
docker buildx create --use --name multiplatform
docker buildx build --platform linux/amd64,linux/arm64 -t test:local .
docker buildx imagetools inspect test:local
```

### Phase 3: CI Testing

```bash
# Trigger workflow
gh workflow run release-docker \
  --ref main \
  --field image-name="test-image" \
  --field registry="ghcr.io"

# Monitor
gh run watch
```

### Phase 4: Post-Push Verification

```bash
# Verify image on ghcr.io
docker pull ghcr.io/jdfalk/ghcommon/test-image:latest

# Check manifest
docker manifest inspect ghcr.io/jdfalk/ghcommon/test-image:latest

# Verify platforms
docker buildx imagetools inspect ghcr.io/jdfalk/ghcommon/test-image:latest
```

## Continue to Part 2

Next part covers detailed workflow analysis and configuration detection.
