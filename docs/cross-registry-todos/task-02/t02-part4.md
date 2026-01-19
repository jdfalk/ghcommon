<!-- file: docs/cross-registry-todos/task-02/t02-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t02-docker-part4-d4e5f6g7-h8i9 -->
<!-- last-edited: 2026-01-19 -->

# Task 02 Part 4: CI Integration and ghcr.io Publishing

## CI Workflow Testing

### Test 1: Trigger Release Docker Workflow

```bash
#!/bin/bash
# file: scripts/trigger-docker-release.sh
# version: 1.0.0
# guid: trigger-docker-release

set -e

echo "=== Triggering Docker Release Workflow ==="

# Check current branch
BRANCH=$(git branch --show-current)
echo "Current branch: $BRANCH"

# Trigger workflow
echo ""
echo "Triggering release-docker workflow..."
gh workflow run release-docker \
  --ref "$BRANCH" \
  --field image-name="test-app" \
  --field registry="ghcr.io" \
  --field dockerfile="Dockerfile" \
  --field context="." \
  --field platforms="linux/amd64,linux/arm64" \
  --field enable-security-scan="true"

# Wait for workflow to start
echo ""
echo "Waiting for workflow to start..."
sleep 5

# Get latest run
RUN_ID=$(gh run list --workflow=release-docker --limit 1 --json databaseId --jq '.[0].databaseId')
echo "Run ID: $RUN_ID"

# Monitor
echo ""
echo "Monitoring workflow (Ctrl+C to stop)..."
gh run watch "$RUN_ID"

echo ""
echo "✅ Workflow complete"
```

### Test 2: Monitor Build Progress

```bash
#!/bin/bash
# file: scripts/monitor-docker-build.sh
# version: 1.0.0
# guid: monitor-docker-build

set -e

echo "=== Monitoring Docker Build Progress ==="

RUN_ID="$1"

if [ -z "$RUN_ID" ]; then
  echo "Getting latest run..."
  RUN_ID=$(gh run list --workflow=release-docker --limit 1 --json databaseId --jq '.[0].databaseId')
fi

echo "Monitoring run: $RUN_ID"

# Get run details
echo ""
echo "Run Details:"
gh run view "$RUN_ID"

# Watch logs in real-time
echo ""
echo "Watching logs..."
gh run view "$RUN_ID" --log-failed || gh run view "$RUN_ID" --log

# Check final status
echo ""
echo "Final Status:"
STATUS=$(gh run view "$RUN_ID" --json conclusion --jq '.conclusion')
echo "  Status: $STATUS"

if [ "$STATUS" = "success" ]; then
  echo "  ✅ Build successful"
else
  echo "  ❌ Build failed"
  exit 1
fi

echo ""
echo "✅ Monitoring complete"
```

### Test 3: Verify Workflow Steps

```bash
#!/bin/bash
# file: scripts/verify-workflow-steps.sh
# version: 1.0.0
# guid: verify-workflow-steps

set -e

echo "=== Verifying Workflow Steps ==="

RUN_ID="$1"

if [ -z "$RUN_ID" ]; then
  RUN_ID=$(gh run list --workflow=release-docker --limit 1 --json databaseId --jq '.[0].databaseId')
fi

echo "Analyzing run: $RUN_ID"

# Get job list
echo ""
echo "Jobs:"
gh run view "$RUN_ID" --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'

# Check specific steps
echo ""
echo "Build Job Steps:"
gh run view "$RUN_ID" --json jobs --jq '.jobs[] | select(.name == "build") | .steps[] | "\(.name): \(.conclusion)"'

# Check for errors
echo ""
echo "Checking for errors..."
gh run view "$RUN_ID" --log 2>&1 | grep -i "error" || echo "  No errors found"

# Check build time
echo ""
echo "Build Duration:"
gh run view "$RUN_ID" --json jobs --jq '.jobs[] | select(.name == "build") | "Started: \(.startedAt)\nCompleted: \(.completedAt)"'

echo ""
echo "✅ Verification complete"
```

## ghcr.io Package Verification

### Test 4: Verify Package Appears on ghcr.io

```bash
#!/bin/bash
# file: scripts/verify-ghcr-package.sh
# version: 1.0.0
# guid: verify-ghcr-package

set -e

echo "=== Verifying Package on ghcr.io ==="

OWNER="jdfalk"
REPO="ghcommon"
IMAGE="test-app"
REGISTRY="ghcr.io"

FULL_IMAGE="$REGISTRY/$OWNER/$IMAGE"

# Check if package exists via API
echo ""
echo "Checking GitHub Packages API..."
gh api "/users/$OWNER/packages/container/$IMAGE" > /tmp/package-info.json

if [ $? -eq 0 ]; then
  echo "  ✅ Package found on ghcr.io"

  # Get package details
  echo ""
  echo "Package Details:"
  jq -r '
    "ID: \(.id)",
    "Name: \(.name)",
    "Visibility: \(.visibility)",
    "Created: \(.created_at)",
    "Updated: \(.updated_at)"
  ' /tmp/package-info.json

  # Get versions
  echo ""
  echo "Available Versions:"
  gh api "/users/$OWNER/packages/container/$IMAGE/versions" | \
    jq -r '.[] | "- \(.name) (created: \(.created_at))"' | head -10
else
  echo "  ❌ Package not found"
  exit 1
fi

echo ""
echo "✅ Package verification complete"
```

### Test 5: Pull Image from ghcr.io

```bash
#!/bin/bash
# file: scripts/pull-from-ghcr.sh
# version: 1.0.0
# guid: pull-from-ghcr

set -e

echo "=== Pulling Image from ghcr.io ==="

IMAGE="ghcr.io/jdfalk/ghcommon/test-app"
TAG="latest"

FULL_IMAGE="$IMAGE:$TAG"

# Authenticate (if private)
echo ""
echo "Authenticating with ghcr.io..."
echo "$GITHUB_TOKEN" | docker login ghcr.io -u jdfalk --password-stdin

# Pull image
echo ""
echo "Pulling image: $FULL_IMAGE"
docker pull "$FULL_IMAGE"

# Verify image
echo ""
echo "Image info:"
docker images "$IMAGE"

# Inspect image
echo ""
echo "Image details:"
docker inspect "$FULL_IMAGE" | jq -r '
  .[0] |
  "Created: \(.Created)",
  "Architecture: \(.Architecture)",
  "OS: \(.Os)",
  "Size: \(.Size)"
'

# Check labels
echo ""
echo "Image labels:"
docker inspect "$FULL_IMAGE" | jq '.[0].Config.Labels'

# Test run
echo ""
echo "Test run:"
docker run --rm "$FULL_IMAGE" --version || echo "No --version flag"

echo ""
echo "✅ Pull and verification complete"
```

### Test 6: Verify Multi-Platform Manifest

```bash
#!/bin/bash
# file: scripts/verify-manifest.sh
# version: 1.0.0
# guid: verify-manifest

set -e

echo "=== Verifying Multi-Platform Manifest ==="

IMAGE="ghcr.io/jdfalk/ghcommon/test-app"
TAG="latest"

FULL_IMAGE="$IMAGE:$TAG"

# Get manifest
echo ""
echo "Fetching manifest..."
docker manifest inspect "$FULL_IMAGE" > /tmp/manifest.json

# Parse manifest
echo ""
echo "Manifest Summary:"
jq -r '
  "Schema Version: \(.schemaVersion)",
  "Media Type: \(.mediaType)",
  "Platforms:"
' /tmp/manifest.json

jq -r '.manifests[] | "  - \(.platform.os)/\(.platform.architecture)"' /tmp/manifest.json

# Detailed platform info
echo ""
echo "Detailed Platform Information:"
jq -r '.manifests[] |
  "Platform: \(.platform.os)/\(.platform.architecture)",
  "  Digest: \(.digest)",
  "  Size: \(.size) bytes",
  "  Media Type: \(.mediaType)",
  ""
' /tmp/manifest.json

# Verify expected platforms
echo ""
echo "Platform Coverage Check:"
if jq -r '.manifests[].platform | "\(.os)/\(.architecture)"' /tmp/manifest.json | grep -q "linux/amd64"; then
  echo "  ✅ linux/amd64 present"
else
  echo "  ❌ linux/amd64 missing"
fi

if jq -r '.manifests[].platform | "\(.os)/\(.architecture)"' /tmp/manifest.json | grep -q "linux/arm64"; then
  echo "  ✅ linux/arm64 present"
else
  echo "  ❌ linux/arm64 missing"
fi

echo ""
echo "✅ Manifest verification complete"
```

## Tag Verification

### Test 7: Verify All Tags

```bash
#!/bin/bash
# file: scripts/verify-tags.sh
# version: 1.0.0
# guid: verify-tags

set -e

echo "=== Verifying Image Tags ==="

IMAGE="ghcr.io/jdfalk/ghcommon/test-app"

# Get all tags via API
echo ""
echo "Fetching tags from GitHub API..."
gh api "/users/jdfalk/packages/container/test-app/versions" > /tmp/tags.json

echo ""
echo "Available Tags:"
jq -r '.[] | .metadata.container.tags[]' /tmp/tags.json | sort | uniq

# Expected tags for semantic versioning
echo ""
echo "Expected Tag Patterns:"
echo "  - Semantic version: v1.2.3, 1.2.3"
echo "  - Major.minor: 1.2"
echo "  - Major: 1"
echo "  - SHA: sha-abc1234"
echo "  - Latest: latest (on default branch only)"

# Verify specific tags exist
echo ""
echo "Tag Verification:"

TAGS=$(jq -r '.[] | .metadata.container.tags[]' /tmp/tags.json)

if echo "$TAGS" | grep -q "latest"; then
  echo "  ✅ latest tag present"
else
  echo "  ⚠️  latest tag missing"
fi

if echo "$TAGS" | grep -qE "^[0-9]+\.[0-9]+\.[0-9]+$"; then
  echo "  ✅ Semantic version tag present"
else
  echo "  ⚠️  Semantic version tag missing"
fi

if echo "$TAGS" | grep -qE "^sha-"; then
  echo "  ✅ SHA tag present"
else
  echo "  ⚠️  SHA tag missing"
fi

echo ""
echo "✅ Tag verification complete"
```

### Test 8: Pull Specific Platform

```bash
#!/bin/bash
# file: scripts/pull-specific-platform.sh
# version: 1.0.0
# guid: pull-specific-platform

set -e

echo "=== Pulling Specific Platform Images ==="

IMAGE="ghcr.io/jdfalk/ghcommon/test-app"
TAG="latest"

# Pull amd64
echo ""
echo "Pulling linux/amd64..."
docker pull --platform linux/amd64 "$IMAGE:$TAG"

# Verify architecture
echo ""
echo "Verifying amd64:"
docker inspect --format='{{.Architecture}}' "$IMAGE:$TAG"

# Pull arm64
echo ""
echo "Pulling linux/arm64..."
docker pull --platform linux/arm64 "$IMAGE:$TAG"

# Verify architecture
echo ""
echo "Verifying arm64:"
docker inspect --format='{{.Architecture}}' "$IMAGE:$TAG"

# Compare sizes
echo ""
echo "Size Comparison:"
echo "amd64:"
docker images "$IMAGE:$TAG" --format "{{.Size}}" | head -1

echo "arm64:"
docker images "$IMAGE:$TAG" --format "{{.Size}}" | tail -1

echo ""
echo "✅ Platform-specific pull complete"
```

## Security Scan Verification

### Test 9: Verify Trivy Results

```bash
#!/bin/bash
# file: scripts/verify-trivy-results.sh
# version: 1.0.0
# guid: verify-trivy-results

set -e

echo "=== Verifying Trivy Scan Results ==="

RUN_ID="$1"

if [ -z "$RUN_ID" ]; then
  RUN_ID=$(gh run list --workflow=release-docker --limit 1 --json databaseId --jq '.[0].databaseId')
fi

echo "Checking run: $RUN_ID"

# Download artifacts
echo ""
echo "Downloading artifacts..."
gh run download "$RUN_ID" --name trivy-results || echo "No trivy-results artifact"

# Check for SARIF file
if [ -f "trivy-results.sarif" ]; then
  echo ""
  echo "Trivy SARIF Results:"

  # Parse SARIF
  jq -r '
    .runs[0].results[] |
    "\(.ruleId): \(.message.text) (Severity: \(.level))"
  ' trivy-results.sarif | head -20

  # Count by severity
  echo ""
  echo "Vulnerability Count by Severity:"
  jq -r '.runs[0].results[] | .level' trivy-results.sarif | sort | uniq -c
else
  echo "  ⚠️  No SARIF file found"
fi

# Check GitHub Security tab
echo ""
echo "Checking GitHub Security tab..."
gh api "/repos/jdfalk/ghcommon/code-scanning/alerts" | \
  jq -r '.[] | select(.tool.name == "Trivy") | "- \(.rule.description) (\(.rule.severity))"' | head -10

echo ""
echo "✅ Trivy results verification complete"
```

### Test 10: Verify SBOM Generation

```bash
#!/bin/bash
# file: scripts/verify-sbom-generation.sh
# version: 1.0.0
# guid: verify-sbom-generation

set -e

echo "=== Verifying SBOM Generation ==="

RUN_ID="$1"

if [ -z "$RUN_ID" ]; then
  RUN_ID=$(gh run list --workflow=release-docker --limit 1 --json databaseId --jq '.[0].databaseId')
fi

echo "Checking run: $RUN_ID"

# Download SBOM artifacts
echo ""
echo "Downloading SBOM artifacts..."
gh run download "$RUN_ID" --name sbom-test-app || echo "No SBOM artifact"

# Check for SBOM files
if [ -f "sbom-test-app.spdx.json" ]; then
  echo ""
  echo "SBOM Summary:"

  # Count packages
  PACKAGES=$(jq '.packages | length' sbom-test-app.spdx.json)
  echo "  Total packages: $PACKAGES"

  # Package types
  echo ""
  echo "  Package types:"
  jq -r '.packages[].type' sbom-test-app.spdx.json | sort | uniq -c

  # License summary
  echo ""
  echo "  License summary:"
  jq -r '.packages[].licenseConcluded' sbom-test-app.spdx.json | grep -v "NOASSERTION" | sort | uniq -c | head -10
else
  echo "  ⚠️  No SBOM file found"
fi

echo ""
echo "✅ SBOM verification complete"
```

## Performance Metrics

### Test 11: Build Time Analysis

```bash
#!/bin/bash
# file: scripts/analyze-build-time.sh
# version: 1.0.0
# guid: analyze-build-time

set -e

echo "=== Analyzing Build Time ==="

# Get last 10 successful runs
gh run list \
  --workflow=release-docker \
  --limit 10 \
  --json databaseId,conclusion,startedAt,updatedAt \
  --jq '.[] | select(.conclusion == "success")' > /tmp/docker-runs.json

# Calculate durations
python3 << 'EOF'
import json
from datetime import datetime

with open('/tmp/docker-runs.json', 'r') as f:
    runs = [json.loads(line) for line in f]

print("| Run ID   | Duration | Started            |")
print("|----------|----------|--------------------|")

durations = []

for run in runs:
    run_id = run['databaseId']
    started = datetime.fromisoformat(run['startedAt'].replace('Z', '+00:00'))
    updated = datetime.fromisoformat(run['updatedAt'].replace('Z', '+00:00'))

    duration = (updated - started).total_seconds()
    durations.append(duration)

    minutes = int(duration // 60)
    seconds = int(duration % 60)

    print(f"| {run_id} | {minutes}m {seconds}s | {started.strftime('%Y-%m-%d %H:%M')} |")

if durations:
    print()
    print(f"Average: {sum(durations)/len(durations):.1f}s ({sum(durations)/len(durations)/60:.1f}m)")
    print(f"Min: {min(durations):.1f}s ({min(durations)/60:.1f}m)")
    print(f"Max: {max(durations):.1f}s ({max(durations)/60:.1f}m)")
EOF

echo ""
echo "✅ Build time analysis complete"
```

## Continue to Part 5

Next part covers optimization recommendations and advanced configurations.
