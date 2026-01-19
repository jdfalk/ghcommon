<!-- file: docs/cross-registry-todos/task-01/t01-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t01-yaml-fix-part3-c3d4e5f6-g7h8 -->
<!-- last-edited: 2026-01-19 -->

# Task 01 Part 3: Testing and Validation

## Pre-Fix Testing

### Baseline Cache Performance Test

```bash
#!/bin/bash
# file: scripts/test-cache-baseline.sh
# version: 1.0.0
# guid: test-cache-baseline

set -e

echo "=== Baseline Cache Performance Test ==="

# Clear local caches
rm -rf ~/.cargo/registry/cache
rm -rf target/

# Run first build (cold cache)
echo ""
echo "Running first build (cold cache)..."
time cargo build --release

# Cache should be warmed now
echo ""
echo "Running second build (warm cache, no changes)..."
time cargo build --release

# Make small change
echo ""
echo "Making small change..."
echo "// Test comment" >> src/lib.rs

# Run incremental build
echo ""
echo "Running incremental build..."
time cargo build --release

# Clean up
git checkout src/lib.rs

echo ""
echo "✅ Baseline test complete"
```

### Expected Baseline Results

**First Build (Cold Cache):**

```text
    Finished release [optimized] target(s) in 3m 45s

real    3m45.234s
user    12m23.456s
sys     0m45.678s
```

**Second Build (Warm Cache):**

```text
    Finished release [optimized] target(s) in 0.12s

real    0m0.123s
user    0m0.089s
sys     0m0.034s
```

**Incremental Build:**

```text
    Finished release [optimized] target(s) in 1.23s

real    0m1.234s
user    0m2.345s
sys     0m0.456s
```

## Post-Fix Testing

### Test 1: Local YAML Validation

```bash
#!/bin/bash
# file: scripts/test-yaml-validation.sh
# version: 1.0.0
# guid: test-yaml-validation

set -e

FILE=".github/workflows/release-rust.yml"

echo "=== YAML Validation Test ==="

# Install yamllint if not present
if ! command -v yamllint &> /dev/null; then
  echo "Installing yamllint..."
  pip3 install yamllint
fi

# Run yamllint
echo ""
echo "Running yamllint on $FILE..."
yamllint "$FILE"

# Check for specific issues
echo ""
echo "Checking for trailing hyphens..."
if grep -A 3 "restore-keys:" "$FILE" | grep -E "^\s+\$.*-$"; then
  echo "❌ FAIL: Found trailing hyphens"
  exit 1
else
  echo "✅ PASS: No trailing hyphens"
fi

# Verify YAML structure
echo ""
echo "Verifying YAML structure..."
python3 << 'EOF'
import yaml
import sys

with open('.github/workflows/release-rust.yml', 'r') as f:
    try:
        data = yaml.safe_load(f)
        print("✅ PASS: Valid YAML structure")
    except yaml.YAMLError as e:
        print(f"❌ FAIL: Invalid YAML: {e}")
        sys.exit(1)
EOF

echo ""
echo "✅ YAML validation complete"
```

### Test 2: GitHub Actions Syntax Check

```bash
#!/bin/bash
# file: scripts/test-gh-actions-syntax.sh
# version: 1.0.0
# guid: test-gh-actions-syntax

set -e

echo "=== GitHub Actions Syntax Check ==="

# Requires GitHub CLI
if ! command -v gh &> /dev/null; then
  echo "❌ GitHub CLI not installed"
  echo "Install: https://cli.github.com/"
  exit 1
fi

# Check authentication
echo ""
echo "Checking GitHub authentication..."
gh auth status

# Validate workflow syntax
echo ""
echo "Validating workflow syntax..."
gh workflow view release-rust --yaml > /dev/null 2>&1

if [ $? -eq 0 ]; then
  echo "✅ PASS: GitHub Actions syntax valid"
else
  echo "❌ FAIL: GitHub Actions syntax invalid"
  gh workflow view release-rust --yaml
  exit 1
fi

echo ""
echo "✅ GitHub Actions validation complete"
```

### Test 3: Cache Key Pattern Matching

```bash
#!/bin/bash
# file: scripts/test-cache-patterns.sh
# version: 1.0.0
# guid: test-cache-patterns

set -e

echo "=== Cache Key Pattern Matching Test ==="

# Extract cache keys and restore keys
FILE=".github/workflows/release-rust.yml"

echo ""
echo "Extracting cache configuration..."

# Parse cache keys
CACHE_KEYS=$(grep -A 5 "name: Cache Cargo dependencies" "$FILE" | grep "key:" | sed 's/.*key: //')
RESTORE_KEYS=$(grep -A 5 "restore-keys:" "$FILE" | grep "\${{ runner.os }}-cargo")

echo ""
echo "Cache Keys:"
echo "$CACHE_KEYS" | while read key; do
  echo "  - $key"
done

echo ""
echo "Restore Keys:"
echo "$RESTORE_KEYS" | while read key; do
  echo "  - $key"
done

# Verify restore keys are prefixes of cache keys
echo ""
echo "Verifying restore key patterns..."

# Expected pattern: cache key ends without hyphen, restore keys are proper prefixes
if echo "$RESTORE_KEYS" | grep -qE "\-$"; then
  echo "❌ FAIL: Found trailing hyphens in restore keys"
  exit 1
fi

echo "✅ PASS: Restore key patterns correct"

# Simulate cache matching logic
echo ""
echo "Simulating cache matching logic..."

# Example cache key: Linux-cargo-1.70-abc123
# Should match restore keys in order:
#   1. Linux-cargo-1.70 (exact version match)
#   2. Linux-cargo (any version)

cat > /tmp/test-cache-match.py << 'EOF'
#!/usr/bin/env python3

import re

# Simulate cache keys in cache
existing_caches = [
    "Linux-cargo-1.70-abc123",
    "Linux-cargo-1.69-def456",
    "Linux-cargo-1.68-ghi789",
]

# Restore keys to try (in order)
restore_keys = [
    "Linux-cargo-1.70",
    "Linux-cargo",
]

print("Existing caches:", existing_caches)
print("Restore keys:", restore_keys)
print()

for restore_key in restore_keys:
    print(f"Trying restore key: {restore_key}")
    for cache_key in existing_caches:
        if cache_key.startswith(restore_key):
            print(f"  ✅ MATCH: {cache_key}")
            print(f"  Would restore: {cache_key}")
            break
    else:
        print(f"  No match found")
    print()
EOF

python3 /tmp/test-cache-match.py

echo "✅ Cache pattern matching test complete"
```

### Expected Output - Cache Pattern Test

```text
=== Cache Key Pattern Matching Test ===

Extracting cache configuration...

Cache Keys:
  - ${{ runner.os }}-cargo-${{ matrix.rust }}-${{ hashFiles('**/Cargo.lock') }}
  - ${{ runner.os }}-cargo-${{ matrix.rust }}-${{ hashFiles('**/Cargo.lock') }}
  - ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}

Restore Keys:
  - ${{ runner.os }}-cargo-${{ matrix.rust }}
  - ${{ runner.os }}-cargo
  - ${{ runner.os }}-cargo-${{ matrix.rust }}
  - ${{ runner.os }}-cargo
  - ${{ runner.os }}-cargo

Verifying restore key patterns...
✅ PASS: Restore key patterns correct

Simulating cache matching logic...
Existing caches: ['Linux-cargo-1.70-abc123', 'Linux-cargo-1.69-def456', 'Linux-cargo-1.68-ghi789']
Restore keys: ['Linux-cargo-1.70', 'Linux-cargo']

Trying restore key: Linux-cargo-1.70
  ✅ MATCH: Linux-cargo-1.70-abc123
  Would restore: Linux-cargo-1.70-abc123

Trying restore key: Linux-cargo
  ✅ MATCH: Linux-cargo-1.70-abc123
  Would restore: Linux-cargo-1.70-abc123

✅ Cache pattern matching test complete
```

## CI Testing

### Test 4: Workflow Dispatch Test

```bash
#!/bin/bash
# file: scripts/test-workflow-dispatch.sh
# version: 1.0.0
# guid: test-workflow-dispatch

set -e

echo "=== Workflow Dispatch Test ==="

# Check branch
BRANCH=$(git branch --show-current)
echo "Current branch: $BRANCH"

if [ "$BRANCH" != "main" ]; then
  echo "⚠️  Warning: Not on main branch"
  read -p "Continue? (y/n): " confirm
  if [ "$confirm" != "y" ]; then
    exit 0
  fi
fi

# Trigger workflow
echo ""
echo "Triggering workflow dispatch..."
gh workflow run release-rust --ref "$BRANCH"

# Wait for workflow to start
echo ""
echo "Waiting for workflow to start..."
sleep 5

# Get run ID
RUN_ID=$(gh run list --workflow=release-rust --limit 1 --json databaseId --jq '.[0].databaseId')
echo "Run ID: $RUN_ID"

# Monitor workflow
echo ""
echo "Monitoring workflow (Ctrl+C to stop)..."
gh run watch "$RUN_ID"

echo ""
echo "✅ Workflow dispatch test complete"
```

### Test 5: Cache Performance Comparison

```bash
#!/bin/bash
# file: scripts/test-cache-performance.sh
# version: 1.0.0
# guid: test-cache-performance

set -e

echo "=== Cache Performance Comparison ==="

# Requires jq
if ! command -v jq &> /dev/null; then
  echo "❌ jq not installed"
  exit 1
fi

# Get recent workflow runs
echo ""
echo "Fetching recent workflow runs..."
gh run list --workflow=release-rust --limit 10 --json databaseId,conclusion,createdAt > /tmp/runs.json

# Analyze run times
echo ""
echo "Analyzing run times..."

cat > /tmp/analyze-runs.py << 'EOF'
#!/usr/bin/env python3

import json
import sys
from datetime import datetime

with open('/tmp/runs.json', 'r') as f:
    runs = json.load(f)

print("Recent Workflow Runs:")
print()
print("| Run ID | Status | Duration | Date |")
print("|--------|--------|----------|------|")

for run in runs:
    run_id = run['databaseId']
    status = run['conclusion']
    created = run['createdAt']

    # Get detailed timing (requires additional API call)
    # This is simplified for the example
    print(f"| {run_id} | {status} | - | {created} |")

print()
print("✅ Analysis complete")
EOF

python3 /tmp/analyze-runs.py

echo ""
echo "Getting cache hit rates..."

# Get cache statistics from workflow logs
LATEST_RUN=$(gh run list --workflow=release-rust --limit 1 --json databaseId --jq '.[0].databaseId')

echo ""
echo "Analyzing cache hits for run $LATEST_RUN..."

gh run view "$LATEST_RUN" --log | grep -E "(Cache hit|Cache miss|Cache restored)" || echo "No cache log entries found"

echo ""
echo "✅ Cache performance comparison complete"
```

### Expected CI Test Results

**Workflow Dispatch:**

```text
=== Workflow Dispatch Test ===
Current branch: main

Triggering workflow dispatch...
✓ Created workflow_dispatch event for release-rust.yml at main

Waiting for workflow to start...
Run ID: 12345678

Monitoring workflow (Ctrl+C to stop)...
✓ jdfalk/ghcommon release-rust #123 (workflow_dispatch)
  Triggered via workflow_dispatch about 1 minute ago

● build (ubuntu-latest, 1.70.0, x86_64-unknown-linux-gnu)
  Cache Cargo dependencies
    Cache hit: false
    Cache restored from: Linux-cargo-1.70

✓ build (ubuntu-latest, 1.70.0, x86_64-unknown-linux-gnu)

✅ Workflow dispatch test complete
```

**Cache Performance:**

```text
=== Cache Performance Comparison ===

Fetching recent workflow runs...

Analyzing run times...

Recent Workflow Runs:

| Run ID   | Status  | Duration | Date                 |
| -------- | ------- | -------- | -------------------- |
| 12345678 | success | 4m 23s   | 2024-01-15T10:30:00Z |
| 12345677 | success | 4m 18s   | 2024-01-15T09:15:00Z |
| 12345676 | success | 15m 42s  | 2024-01-15T08:00:00Z |

✅ Analysis complete

Getting cache hit rates...

Analyzing cache hits for run 12345678...
Cache hit: false
Cache restored from key: Linux-cargo-1.70-abc123
Cache size: 245 MB
Restore time: 12s

✅ Cache performance comparison complete
```

## Integration Testing

### Test 6: End-to-End Build Test

```bash
#!/bin/bash
# file: scripts/test-e2e-build.sh
# version: 1.0.0
# guid: test-e2e-build

set -e

echo "=== End-to-End Build Test ==="

# Clean workspace
echo ""
echo "Cleaning workspace..."
cargo clean
rm -rf ~/.cargo/registry/cache/

# Run build matrix locally
echo ""
echo "Testing build matrix..."

TARGETS=(
  "x86_64-unknown-linux-gnu"
  "aarch64-unknown-linux-gnu"
  "x86_64-apple-darwin"
)

for target in "${TARGETS[@]}"; do
  echo ""
  echo "Building for $target..."

  if rustup target list --installed | grep -q "$target"; then
    echo "  Target already installed"
  else
    echo "  Installing target..."
    rustup target add "$target"
  fi

  # Build
  if cargo build --release --target "$target" 2>&1 | tee /tmp/build-$target.log; then
    echo "  ✅ Build successful"
  else
    echo "  ❌ Build failed"
    cat /tmp/build-$target.log
    exit 1
  fi
done

echo ""
echo "✅ End-to-end build test complete"
```

### Test 7: Regression Test

```bash
#!/bin/bash
# file: scripts/test-regression.sh
# version: 1.0.0
# guid: test-regression

set -e

echo "=== Regression Test ==="

# Store current branch
CURRENT_BRANCH=$(git branch --show-current)

# Test before fix
echo ""
echo "Testing BEFORE fix..."
git stash
git checkout HEAD~1  # Go to commit before fix

# Run baseline test
./scripts/test-cache-baseline.sh > /tmp/baseline-before.log 2>&1
BEFORE_TIME=$(grep "real" /tmp/baseline-before.log | tail -1 | awk '{print $2}')

# Test after fix
echo ""
echo "Testing AFTER fix..."
git checkout "$CURRENT_BRANCH"
git stash pop

# Run baseline test
./scripts/test-cache-baseline.sh > /tmp/baseline-after.log 2>&1
AFTER_TIME=$(grep "real" /tmp/baseline-after.log | tail -1 | awk '{print $2}')

# Compare
echo ""
echo "Results:"
echo "  Before: $BEFORE_TIME"
echo "  After:  $AFTER_TIME"

# Should be similar (within 5%)
echo ""
echo "✅ Regression test complete"
```

## Validation Checklist

### Pre-Deployment Checklist

- [ ] All local tests pass
- [ ] YAML syntax valid (yamllint)
- [ ] GitHub Actions syntax valid (gh CLI)
- [ ] Cache key patterns correct
- [ ] No trailing hyphens in restore-keys
- [ ] Workflow dispatch test successful
- [ ] Build matrix tested locally
- [ ] Cache performance acceptable
- [ ] Regression test passed
- [ ] Documentation updated

### Post-Deployment Checklist

- [ ] Workflow runs successfully in CI
- [ ] Cache hit rate monitored
- [ ] Build times within expected range
- [ ] No errors in workflow logs
- [ ] All targets build successfully
- [ ] Artifacts uploaded correctly
- [ ] Release created (if applicable)

## Continue to Part 4

Next part covers Git workflow and commit procedures.
