<!-- file: docs/cross-registry-todos/task-02/t02-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t02-docker-part3-c3d4e5f6-g7h8 -->
<!-- last-edited: 2026-01-19 -->

# Task 02 Part 3: Local Testing and Multi-Platform Validation

## Local Build Testing

### Test 1: Single Platform Build

```bash
#!/bin/bash
# file: scripts/test-single-platform-build.sh
# version: 1.0.0
# guid: test-single-platform-build

set -e

echo "=== Testing Single Platform Build ==="

# Build for current platform only
IMAGE="test-image"
TAG="local-test"

echo ""
echo "Building for current platform..."
time docker build -t "$IMAGE:$TAG" .

# Inspect
echo ""
echo "Image info:"
docker images "$IMAGE:$TAG"

echo ""
echo "Image layers:"
docker history "$IMAGE:$TAG"

echo ""
echo "Image size analysis:"
docker inspect "$IMAGE:$TAG" | jq '.[0].Size' | numfmt --to=iec

# Test run
echo ""
echo "Test run:"
docker run --rm "$IMAGE:$TAG" --version || echo "No --version flag"

echo ""
echo "✅ Single platform build complete"
```

### Test 2: Multi-Platform Build with BuildX

```bash
#!/bin/bash
# file: scripts/test-multiplatform-build.sh
# version: 1.0.0
# guid: test-multiplatform-build

set -e

echo "=== Testing Multi-Platform Build ==="

IMAGE="test-image"
TAG="multiplatform-test"
PLATFORMS="linux/amd64,linux/arm64"

# Create builder
echo ""
echo "Creating buildx builder..."
docker buildx create --use --name multiplatform-builder || echo "Builder exists"

# Inspect builder
echo ""
echo "Builder info:"
docker buildx inspect --bootstrap

# Build for multiple platforms
echo ""
echo "Building for platforms: $PLATFORMS"
time docker buildx build \
  --platform "$PLATFORMS" \
  --tag "$IMAGE:$TAG" \
  --load \
  .

# Note: --load only works with single platform
# For multi-platform, use --push or save to tarball

echo ""
echo "✅ Multi-platform build complete"
```

### Test 3: Multi-Platform with Push to Local Registry

```bash
#!/bin/bash
# file: scripts/test-multiplatform-local-registry.sh
# version: 1.0.0
# guid: test-multiplatform-local-registry

set -e

echo "=== Testing Multi-Platform with Local Registry ==="

# Start local registry
echo ""
echo "Starting local registry..."
docker run -d -p 5000:5000 --restart=always --name registry registry:2 || echo "Registry already running"

# Wait for registry
sleep 2

IMAGE="localhost:5000/test-image"
TAG="multiplatform"
PLATFORMS="linux/amd64,linux/arm64"

# Create builder
echo ""
echo "Setting up builder..."
docker buildx create --use --name local-builder || echo "Builder exists"

# Build and push to local registry
echo ""
echo "Building and pushing to local registry..."
time docker buildx build \
  --platform "$PLATFORMS" \
  --tag "$IMAGE:$TAG" \
  --push \
  .

# Verify manifest
echo ""
echo "Checking manifest:"
docker buildx imagetools inspect "$IMAGE:$TAG"

# Pull and test amd64
echo ""
echo "Pulling amd64 image:"
docker pull --platform linux/amd64 "$IMAGE:$TAG"

# Pull and test arm64
echo ""
echo "Pulling arm64 image:"
docker pull --platform linux/arm64 "$IMAGE:$TAG"

# Clean up
echo ""
echo "Cleaning up local registry..."
docker stop registry || true
docker rm registry || true

echo ""
echo "✅ Multi-platform local registry test complete"
```

## BuildX Configuration Testing

### Test 4: BuildX Features

```bash
#!/bin/bash
# file: scripts/test-buildx-features.sh
# version: 1.0.0
# guid: test-buildx-features

set -e

echo "=== Testing BuildX Features ==="

# Check BuildX version
echo ""
echo "BuildX version:"
docker buildx version

# List builders
echo ""
echo "Available builders:"
docker buildx ls

# Create custom builder with configuration
echo ""
echo "Creating custom builder..."
docker buildx create \
  --name feature-test-builder \
  --driver docker-container \
  --driver-opt image=moby/buildkit:latest \
  --driver-opt network=host \
  --config - << 'EOF'
[worker.oci]
  max-parallelism = 4

[registry."docker.io"]
  mirrors = ["mirror.gcr.io"]
EOF

# Inspect
echo ""
echo "Builder configuration:"
docker buildx inspect feature-test-builder

# Remove builder
echo ""
echo "Cleaning up..."
docker buildx rm feature-test-builder

echo ""
echo "✅ BuildX features test complete"
```

### Test 5: Cache Optimization

```bash
#!/bin/bash
# file: scripts/test-cache-optimization.sh
# version: 1.0.0
# guid: test-cache-optimization

set -e

echo "=== Testing Cache Optimization ==="

IMAGE="test-image"
TAG="cache-test"

# First build (cold cache)
echo ""
echo "First build (cold cache)..."
rm -rf /tmp/.buildx-cache
time docker buildx build \
  --tag "$IMAGE:$TAG" \
  --cache-to type=local,dest=/tmp/.buildx-cache,mode=max \
  --load \
  .

# Check cache size
echo ""
echo "Cache size:"
du -sh /tmp/.buildx-cache

# Second build (warm cache, no changes)
echo ""
echo "Second build (warm cache, no changes)..."
time docker buildx build \
  --tag "$IMAGE:$TAG" \
  --cache-from type=local,src=/tmp/.buildx-cache \
  --cache-to type=local,dest=/tmp/.buildx-cache,mode=max \
  --load \
  .

# Make small change
echo ""
echo "Third build (warm cache, with change)..."
echo "# Test comment" >> Dockerfile
time docker buildx build \
  --tag "$IMAGE:$TAG" \
  --cache-from type=local,src=/tmp/.buildx-cache \
  --cache-to type=local,dest=/tmp/.buildx-cache,mode=max \
  --load \
  .

# Restore Dockerfile
git checkout Dockerfile

# Clean up
rm -rf /tmp/.buildx-cache

echo ""
echo "✅ Cache optimization test complete"
```

## Security Scanning Tests

### Test 6: Local Trivy Scan

```bash
#!/bin/bash
# file: scripts/test-trivy-local.sh
# version: 1.0.0
# guid: test-trivy-local

set -e

echo "=== Testing Trivy Security Scanning ==="

IMAGE="test-image:local-test"

# Install Trivy if needed
if ! command -v trivy &> /dev/null; then
  echo "Installing Trivy..."
  brew install trivy
fi

# Update vulnerability database
echo ""
echo "Updating Trivy database..."
trivy image --download-db-only

# Scan for all vulnerabilities
echo ""
echo "Scanning image: $IMAGE"
echo ""
trivy image "$IMAGE"

# Scan for specific severities
echo ""
echo "Scanning for CRITICAL and HIGH vulnerabilities..."
trivy image \
  --severity CRITICAL,HIGH \
  --exit-code 1 \
  "$IMAGE" || echo "⚠️  Vulnerabilities found"

# Generate JSON report
echo ""
echo "Generating JSON report..."
trivy image \
  --format json \
  --output trivy-report.json \
  "$IMAGE"

# Generate SARIF report
echo ""
echo "Generating SARIF report..."
trivy image \
  --format sarif \
  --output trivy-report.sarif \
  "$IMAGE"

# Generate HTML report
echo ""
echo "Generating HTML report..."
trivy image \
  --format template \
  --template "@/usr/local/share/trivy/templates/html.tpl" \
  --output trivy-report.html \
  "$IMAGE"

echo ""
echo "Reports generated:"
ls -lh trivy-report.*

echo ""
echo "✅ Trivy scan complete"
```

### Test 7: Grype Alternative Scanner

```bash
#!/bin/bash
# file: scripts/test-grype-scanner.sh
# version: 1.0.0
# guid: test-grype-scanner

set -e

echo "=== Testing Grype Security Scanning ==="

IMAGE="test-image:local-test"

# Install Grype if needed
if ! command -v grype &> /dev/null; then
  echo "Installing Grype..."
  brew install grype
fi

# Scan image
echo ""
echo "Scanning image with Grype: $IMAGE"
grype "$IMAGE"

# Scan with severity threshold
echo ""
echo "Checking for HIGH and CRITICAL vulnerabilities..."
grype "$IMAGE" \
  --fail-on high \
  || echo "⚠️  Vulnerabilities found"

# Generate JSON report
echo ""
echo "Generating JSON report..."
grype "$IMAGE" -o json > grype-report.json

# Generate SARIF report
echo ""
echo "Generating SARIF report..."
grype "$IMAGE" -o sarif > grype-report.sarif

# Compare with Trivy
echo ""
echo "Comparing Grype and Trivy results..."
python3 << 'EOF'
import json

# Load Grype results
with open('grype-report.json', 'r') as f:
    grype = json.load(f)

# Load Trivy results
with open('trivy-report.json', 'r') as f:
    trivy = json.load(f)

grype_vulns = len(grype.get('matches', []))
trivy_vulns = len(trivy.get('Results', [{}])[0].get('Vulnerabilities', []))

print(f"Grype found: {grype_vulns} vulnerabilities")
print(f"Trivy found: {trivy_vulns} vulnerabilities")

EOF

echo ""
echo "✅ Grype scan complete"
```

## SBOM Generation Tests

### Test 8: Local SBOM with Syft

```bash
#!/bin/bash
# file: scripts/test-sbom-syft.sh
# version: 1.0.0
# guid: test-sbom-syft

set -e

echo "=== Testing SBOM Generation with Syft ==="

IMAGE="test-image:local-test"

# Install Syft if needed
if ! command -v syft &> /dev/null; then
  echo "Installing Syft..."
  brew install syft
fi

# Generate SPDX JSON SBOM
echo ""
echo "Generating SPDX JSON SBOM..."
syft "$IMAGE" -o spdx-json > sbom.spdx.json

# Generate CycloneDX JSON SBOM
echo ""
echo "Generating CycloneDX JSON SBOM..."
syft "$IMAGE" -o cyclonedx-json > sbom.cyclonedx.json

# Generate human-readable text SBOM
echo ""
echo "Generating text SBOM..."
syft "$IMAGE" -o table > sbom.txt

# Show summary
echo ""
echo "SBOM Summary:"
cat sbom.txt | head -20

# Count packages
echo ""
echo "Package count:"
PACKAGE_COUNT=$(jq '.packages | length' sbom.spdx.json)
echo "  Total packages: $PACKAGE_COUNT"

# Show package types
echo ""
echo "Package types:"
jq -r '.packages[].type' sbom.spdx.json | sort | uniq -c | sort -rn

echo ""
echo "SBOM files generated:"
ls -lh sbom.*

echo ""
echo "✅ SBOM generation complete"
```

### Test 9: Docker Scout SBOM

```bash
#!/bin/bash
# file: scripts/test-docker-scout-sbom.sh
# version: 1.0.0
# guid: test-docker-scout-sbom

set -e

echo "=== Testing Docker Scout SBOM ==="

IMAGE="test-image:local-test"

# Check if Docker Scout is available
if ! docker scout version &> /dev/null; then
  echo "Installing Docker Scout..."
  docker scout install
fi

# Generate SBOM
echo ""
echo "Generating SBOM with Docker Scout..."
docker scout sbom "$IMAGE" \
  --format spdx \
  --output sbom-scout.spdx.json

# Analyze vulnerabilities
echo ""
echo "Analyzing vulnerabilities..."
docker scout cves "$IMAGE"

# Generate recommendations
echo ""
echo "Getting recommendations..."
docker scout recommendations "$IMAGE"

# Compare with base image
echo ""
echo "Comparing with base image..."
docker scout compare --to alpine:latest "$IMAGE"

echo ""
echo "✅ Docker Scout SBOM complete"
```

## Platform-Specific Testing

### Test 10: ARM64 Emulation

```bash
#!/bin/bash
# file: scripts/test-arm64-emulation.sh
# version: 1.0.0
# guid: test-arm64-emulation

set -e

echo "=== Testing ARM64 Emulation ==="

IMAGE="test-image"
TAG="arm64-test"

# Check QEMU
echo ""
echo "Checking QEMU installation..."
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Build ARM64 image on x86_64
echo ""
echo "Building ARM64 image on x86_64..."
docker buildx build \
  --platform linux/arm64 \
  --tag "$IMAGE:$TAG" \
  --load \
  .

# Run ARM64 image
echo ""
echo "Running ARM64 image (emulated)..."
docker run --rm --platform linux/arm64 "$IMAGE:$TAG" uname -m

echo ""
echo "✅ ARM64 emulation test complete"
```

## Continue to Part 4

Next part covers CI testing, ghcr.io publishing verification, and automated workflows.
