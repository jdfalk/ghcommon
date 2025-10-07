<!-- file: docs/cross-registry-todos/task-09/t09-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t09-ci-migration-testing-part2-i4j5k6l7-m8n9 -->

# Task 09 Part 2: Phase 1 - ghcommon Repository Migration

## Phase 1 Overview

**Repository:** `jdfalk/ghcommon` **Migration Date:** Week 1-2 **Risk Level:** Low **Rollback
Complexity:** Low

## Pre-Migration State

### Current Workflow Structure

**File:** `.github/workflows/reusable-ci.yml`

```yaml
name: Reusable CI Workflow

on:
  workflow_call:
    inputs:
      go-version:
        type: string
        default: '1.21'
      python-version:
        type: string
        default: '3.11'

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      go_files: ${{ steps.filter.outputs.go }}
      python_files: ${{ steps.filter.outputs.python }}

    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            go:
              - '**/*.go'
              - 'go.mod'
              - 'go.sum'
            python:
              - '**/*.py'
              - 'requirements*.txt'

  build-go:
    needs: detect-changes
    if: needs.detect-changes.outputs.go_files == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: ${{ inputs.go-version }}
          cache: true
      - run: go build -v ./...
      - run: go test -v ./...

  build-python:
    needs: detect-changes
    if: needs.detect-changes.outputs.python_files == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python-version }}
          cache: 'pip'
      - run: pip install -r requirements.txt
      - run: pytest
```

### Current Limitations

1. **No coverage reporting**
2. **No security scanning**
3. **Basic linting only**
4. **Single version testing**
5. **No Docker support**
6. **No benchmarks**
7. **Limited artifact retention**

## Migration Steps

### Step 1: Create Consolidated Workflow

**Action:** Copy consolidated workflow from Task 08

**File:** `.github/workflows/reusable-ci-consolidated.yml`

```bash
#!/bin/bash
# Create consolidated workflow in ghcommon

cat > .github/workflows/reusable-ci-consolidated.yml << 'EOF'
# file: .github/workflows/reusable-ci-consolidated.yml
# version: 1.0.0
# guid: consolidated-ci-workflow-a1b2c3d4-e5f6

name: Consolidated CI Workflow

on:
  workflow_call:
    inputs:
      # [Full workflow from Task 08 Part 3-4]
      config-file:
        type: string
        default: '.github/repository-config.yml'

      enable-go:
        type: boolean
        default: true

      enable-python:
        type: boolean
        default: true

      # ... [all other inputs]

jobs:
  load-config:
    # [Full job implementation from Task 08]

  detect-changes:
    # [Full job implementation from Task 08]

  test-go:
    # [Full job implementation from Task 08]

  test-python:
    # [Full job implementation from Task 08]

  # ... [all other jobs]
EOF

echo "✅ Consolidated workflow created"
```

### Step 2: Create Repository Configuration

**File:** `.github/repository-config.yml`

```yaml
# file: .github/repository-config.yml
# version: 1.0.0
# guid: ghcommon-repo-config

ci:
  languages:
    go:
      enabled: false # ghcommon doesn't have Go code
      versions: []

    python:
      enabled: true
      versions: ['3.10', '3.11', '3.12']
      test-command: 'pytest -v --cov --cov-report=xml'
      lint-command: 'ruff check .'
      type-check-command: 'mypy scripts/ --ignore-missing-imports'
      coverage-threshold: 75

    typescript:
      enabled: false

    rust:
      enabled: false

  features:
    super-linter: true
    security-scan: true
    code-coverage: true
    benchmarks: false
    docker-build: false

  change-detection:
    python:
      - '**/*.py'
      - 'scripts/**/*.py'
      - 'requirements*.txt'
      - 'pyproject.toml'
      - '.github/workflows/*python*.yml'

    workflows:
      - '.github/workflows/**'
      - '.github/actions/**'

    docs:
      - '**/*.md'
      - 'docs/**'
```

**Script to create config:**

```bash
#!/bin/bash
# file: scripts/create-ghcommon-config.sh
# version: 1.0.0
# guid: create-ghcommon-config-script

echo "=== Creating ghcommon Repository Config ==="

# Backup existing config if present
if [ -f ".github/repository-config.yml" ]; then
  cp .github/repository-config.yml .github/repository-config.yml.bak
  echo "✅ Backed up existing config"
fi

# Create new config
cat > .github/repository-config.yml << 'EOF'
# [Full config from above]
EOF

# Validate config
if command -v yamllint &> /dev/null; then
  yamllint .github/repository-config.yml
  echo "✅ Config validated"
else
  echo "⚠️  yamllint not available, skipping validation"
fi

# Display config
echo ""
echo "Repository configuration:"
cat .github/repository-config.yml

echo ""
echo "✅ Configuration created successfully"
```

### Step 3: Create Test Workflow

**File:** `.github/workflows/test-consolidated-ci.yml`

```yaml
# file: .github/workflows/test-consolidated-ci.yml
# version: 1.0.0
# guid: test-consolidated-ci-ghcommon

name: Test Consolidated CI

on:
  workflow_dispatch:
    inputs:
      enable-all-features:
        description: 'Enable all features for comprehensive test'
        type: boolean
        default: true

jobs:
  test-consolidated:
    name: Test Consolidated Workflow
    uses: ./.github/workflows/reusable-ci-consolidated.yml
    with:
      config-file: '.github/repository-config.yml'

      # Language enables
      enable-go: false
      enable-python: true
      enable-typescript: false
      enable-rust: false
      enable-docker: false

      # Feature flags
      enable-coverage: ${{ github.event.inputs.enable-all-features == 'true' }}
      enable-security-scan: ${{ github.event.inputs.enable-all-features == 'true' }}
      enable-super-linter: true
      enable-benchmarks: false

      # Python versions to test
      python-versions: '["3.10", "3.11", "3.12"]'

      # Coverage threshold
      coverage-threshold: 75

      # Test timeout
      test-timeout: 30

    secrets: inherit
```

### Step 4: Run Initial Tests

**Test Script:**

```bash
#!/bin/bash
# file: scripts/test-ghcommon-migration.sh
# version: 1.0.0
# guid: test-ghcommon-migration-script

set -e

echo "=== Testing ghcommon CI Migration ==="

# 1. Validate workflow syntax
echo "📋 Step 1: Validating workflow syntax..."
yamllint .github/workflows/reusable-ci-consolidated.yml
yamllint .github/workflows/test-consolidated-ci.yml
echo "✅ Workflow syntax valid"

# 2. Validate repository config
echo "📋 Step 2: Validating repository config..."
yamllint .github/repository-config.yml
echo "✅ Repository config valid"

# 3. Trigger test workflow
echo "📋 Step 3: Triggering test workflow..."
gh workflow run test-consolidated-ci.yml -f enable-all-features=true

# Wait a moment for workflow to start
sleep 5

# 4. Get run ID
run_id=$(gh run list --workflow=test-consolidated-ci.yml --limit 1 --json databaseId -q '.[0].databaseId')
echo "Workflow run ID: $run_id"

# 5. Watch workflow execution
echo "📋 Step 4: Watching workflow execution..."
gh run watch $run_id

# 6. Check results
echo "📋 Step 5: Checking results..."
status=$(gh run view $run_id --json conclusion -q '.conclusion')
echo "Workflow status: $status"

# 7. Download artifacts
echo "📋 Step 6: Downloading artifacts..."
mkdir -p test-artifacts
cd test-artifacts
gh run download $run_id
cd ..

# 8. Verify artifacts
echo "📋 Step 7: Verifying artifacts..."
echo "Artifacts downloaded:"
ls -lh test-artifacts/

# 9. Check for expected artifacts
expected_artifacts=(
  "python-test-results-3.10"
  "python-test-results-3.11"
  "python-test-results-3.12"
  "ci-summary-report"
)

missing_artifacts=()
for artifact in "${expected_artifacts[@]}"; do
  if [ ! -d "test-artifacts/$artifact" ]; then
    missing_artifacts+=("$artifact")
  fi
done

if [ ${#missing_artifacts[@]} -eq 0 ]; then
  echo "✅ All expected artifacts present"
else
  echo "⚠️  Missing artifacts: ${missing_artifacts[*]}"
fi

# 10. Final result
if [ "$status" = "success" ] && [ ${#missing_artifacts[@]} -eq 0 ]; then
  echo ""
  echo "✅ ghcommon migration test PASSED"
  exit 0
else
  echo ""
  echo "❌ ghcommon migration test FAILED"
  exit 1
fi
```

### Step 5: Compare with Old Workflow

**Comparison Script:**

```bash
#!/bin/bash
# file: scripts/compare-old-new-workflow.sh
# version: 1.0.0
# guid: compare-old-new-workflow-script

echo "=== Comparing Old vs New Workflow ==="

# Run old workflow
echo "🔄 Running old workflow..."
gh workflow run reusable-ci.yml

sleep 5
old_run=$(gh run list --workflow=reusable-ci.yml --limit 1 --json databaseId -q '.[0].databaseId')
echo "Old workflow run: $old_run"

# Run new workflow
echo "🔄 Running new workflow..."
gh workflow run test-consolidated-ci.yml

sleep 5
new_run=$(gh run list --workflow=test-consolidated-ci.yml --limit 1 --json databaseId -q '.[0].databaseId')
echo "New workflow run: $new_run"

# Wait for both
echo "⏳ Waiting for workflows to complete..."
gh run watch $old_run &
old_pid=$!
gh run watch $new_run &
new_pid=$!

wait $old_pid
wait $new_pid

# Compare results
echo ""
echo "=== Comparison Results ==="

# Status
old_status=$(gh run view $old_run --json conclusion -q '.conclusion')
new_status=$(gh run view $new_run --json conclusion -q '.conclusion')

echo "Old workflow status: $old_status"
echo "New workflow status: $new_status"

# Timing
old_timing=$(gh run view $old_run --json timing -q '.timing.run_duration_ms')
new_timing=$(gh run view $new_run --json timing -q '.timing.run_duration_ms')

old_minutes=$((old_timing / 60000))
new_minutes=$((new_timing / 60000))

echo "Old workflow duration: ${old_minutes} minutes"
echo "New workflow duration: ${new_minutes} minutes"

# Calculate percentage difference
if [ $old_minutes -gt 0 ]; then
  diff_percent=$(echo "scale=2; (($new_minutes - $old_minutes) * 100) / $old_minutes" | bc)
  echo "Duration difference: ${diff_percent}%"
fi

# Artifacts
old_artifacts=$(gh run view $old_run --json artifacts -q '.artifacts | length')
new_artifacts=$(gh run view $new_run --json artifacts -q '.artifacts | length')

echo "Old workflow artifacts: $old_artifacts"
echo "New workflow artifacts: $new_artifacts"

# Jobs
old_jobs=$(gh run view $old_run --json jobs -q '.jobs | length')
new_jobs=$(gh run view $new_run --json jobs -q '.jobs | length')

echo "Old workflow jobs: $old_jobs"
echo "New workflow jobs: $new_jobs"

# Summary
echo ""
echo "=== Summary ==="

if [ "$old_status" = "$new_status" ] && [ "$new_status" = "success" ]; then
  echo "✅ Both workflows succeeded"
else
  echo "⚠️  Workflow status mismatch"
fi

if [ $new_artifacts -ge $old_artifacts ]; then
  echo "✅ New workflow has same or more artifacts"
else
  echo "⚠️  New workflow has fewer artifacts"
fi

if [ $new_minutes -le $((old_minutes + old_minutes / 5)) ]; then
  echo "✅ New workflow duration acceptable (within 20%)"
else
  echo "⚠️  New workflow significantly slower"
fi
```

### Step 6: Parallel Execution Period

**Duration:** 1 week **Purpose:** Run both workflows side-by-side to validate behavior

**Parallel Workflow Setup:**

```yaml
# file: .github/workflows/ci-parallel.yml
# version: 1.0.0
# guid: ci-parallel-ghcommon

name: CI (Parallel Testing)

on:
  push:
    branches: [main, develop]
  pull_request:
  workflow_dispatch:

jobs:
  old-workflow:
    name: Old Workflow
    uses: ./.github/workflows/reusable-ci.yml
    with:
      python-version: '3.11'
    secrets: inherit

  new-workflow:
    name: New Workflow
    uses: ./.github/workflows/reusable-ci-consolidated.yml
    with:
      config-file: '.github/repository-config.yml'
      enable-python: true
      python-versions: '["3.10", "3.11", "3.12"]'
      enable-coverage: true
      enable-security-scan: true
      enable-super-linter: true
    secrets: inherit

  compare-results:
    name: Compare Results
    needs: [old-workflow, new-workflow]
    if: always()
    runs-on: ubuntu-latest

    steps:
      - name: Compare outcomes
        run: |
          echo "### Parallel Execution Comparison" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Workflow | Status |" >> $GITHUB_STEP_SUMMARY
          echo "|----------|--------|" >> $GITHUB_STEP_SUMMARY
          echo "| Old | ${{ needs.old-workflow.result }} |" >> $GITHUB_STEP_SUMMARY
          echo "| New | ${{ needs.new-workflow.result }} |" >> $GITHUB_STEP_SUMMARY

          if [ "${{ needs.old-workflow.result }}" = "${{ needs.new-workflow.result }}" ]; then
            echo "" >> $GITHUB_STEP_SUMMARY
            echo "✅ Both workflows have matching results" >> $GITHUB_STEP_SUMMARY
          else
            echo "" >> $GITHUB_STEP_SUMMARY
            echo "⚠️ Workflow results differ" >> $GITHUB_STEP_SUMMARY
          fi
```

### Step 7: Monitor and Validate

**Monitoring Script:**

```python
#!/usr/bin/env python3
# file: scripts/monitor-parallel-execution.py
# version: 1.0.0
# guid: monitor-parallel-execution-script

"""
Monitor parallel execution of old and new workflows.
Track success rates, timing, and artifact generation.
"""

import subprocess
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict

def get_workflow_runs(workflow_name, days=7):
    """Get workflow runs for the past N days."""
    since = (datetime.now() - timedelta(days=days)).isoformat()

    result = subprocess.run(
        [
            "gh", "run", "list",
            "--workflow", workflow_name,
            "--json", "conclusion,createdAt,databaseId,name",
            "--limit", "100"
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return []

    runs = json.loads(result.stdout)
    # Filter by date
    return [r for r in runs if r['createdAt'] >= since]

def analyze_runs(runs):
    """Analyze workflow runs."""
    stats = {
        'total': len(runs),
        'success': 0,
        'failure': 0,
        'cancelled': 0,
        'other': 0
    }

    for run in runs:
        conclusion = run.get('conclusion', 'other')
        if conclusion in stats:
            stats[conclusion] += 1
        else:
            stats['other'] += 1

    return stats

def main():
    print("=== Monitoring Parallel Execution ===\n")

    # Get runs for both workflows
    old_runs = get_workflow_runs("reusable-ci.yml")
    new_runs = get_workflow_runs("test-consolidated-ci.yml")

    print(f"Old workflow runs (last 7 days): {len(old_runs)}")
    print(f"New workflow runs (last 7 days): {len(new_runs)}")
    print()

    # Analyze old workflow
    old_stats = analyze_runs(old_runs)
    print("Old Workflow Statistics:")
    print(f"  Total: {old_stats['total']}")
    print(f"  Success: {old_stats['success']} ({old_stats['success']/old_stats['total']*100:.1f}%)")
    print(f"  Failure: {old_stats['failure']} ({old_stats['failure']/old_stats['total']*100:.1f}%)")
    print()

    # Analyze new workflow
    new_stats = analyze_runs(new_runs)
    print("New Workflow Statistics:")
    print(f"  Total: {new_stats['total']}")
    print(f"  Success: {new_stats['success']} ({new_stats['success']/new_stats['total']*100:.1f}%)")
    print(f"  Failure: {new_stats['failure']} ({new_stats['failure']/new_stats['total']*100:.1f}%)")
    print()

    # Compare success rates
    if old_stats['total'] > 0 and new_stats['total'] > 0:
        old_rate = old_stats['success'] / old_stats['total']
        new_rate = new_stats['success'] / new_stats['total']

        print("Success Rate Comparison:")
        print(f"  Old: {old_rate*100:.1f}%")
        print(f"  New: {new_rate*100:.1f}%")

        if new_rate >= old_rate:
            print("  ✅ New workflow success rate is equal or better")
        else:
            print("  ⚠️  New workflow success rate is lower")
            print(f"  Difference: {(new_rate - old_rate)*100:.1f}%")

if __name__ == "__main__":
    main()
```

### Step 8: Switchover

**After 1 week of successful parallel execution:**

**Update main CI workflow:**

```yaml
# file: .github/workflows/ci.yml
# version: 2.0.0
# guid: ghcommon-ci-workflow-v2

name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
  workflow_dispatch:

jobs:
  ci:
    name: Continuous Integration
    uses: ./.github/workflows/reusable-ci-consolidated.yml
    with:
      config-file: '.github/repository-config.yml'

      # Enable Python only
      enable-go: false
      enable-python: true
      enable-typescript: false
      enable-rust: false
      enable-docker: false

      # Enable all features
      enable-coverage: true
      enable-security-scan: true
      enable-super-linter: true
      enable-benchmarks: false

      # Python versions
      python-versions: '["3.10", "3.11", "3.12"]'

      # Coverage threshold
      coverage-threshold: 75

      # Test timeout
      test-timeout: 30

    secrets: inherit
```

### Step 9: Verification

**Post-switchover validation:**

```bash
#!/bin/bash
# file: scripts/verify-switchover.sh
# version: 1.0.0
# guid: verify-switchover-script

echo "=== Verifying Switchover ==="

# 1. Check CI workflow is updated
echo "📋 Checking CI workflow..."
if grep -q "reusable-ci-consolidated.yml" .github/workflows/ci.yml; then
  echo "✅ CI workflow using consolidated version"
else
  echo "❌ CI workflow not updated"
  exit 1
fi

# 2. Trigger CI workflow
echo "📋 Triggering CI workflow..."
gh workflow run ci.yml

sleep 5
run_id=$(gh run list --workflow=ci.yml --limit 1 --json databaseId -q '.[0].databaseId')

# 3. Watch execution
echo "📋 Watching execution..."
gh run watch $run_id

# 4. Check status
status=$(gh run view $run_id --json conclusion -q '.conclusion')

if [ "$status" = "success" ]; then
  echo "✅ Switchover verification PASSED"
else
  echo "❌ Switchover verification FAILED"
  exit 1
fi
```

### Step 10: Cleanup

**After 1 more week of stable operation:**

```bash
#!/bin/bash
# file: scripts/cleanup-old-workflow.sh
# version: 1.0.0
# guid: cleanup-old-workflow-script

echo "=== Cleaning Up Old Workflow ==="

# 1. Archive old workflow
mkdir -p .github/workflows-archive
mv .github/workflows/reusable-ci.yml .github/workflows-archive/
echo "✅ Old workflow archived"

# 2. Remove parallel testing workflow
rm .github/workflows/ci-parallel.yml
echo "✅ Parallel testing workflow removed"

# 3. Remove test workflow
rm .github/workflows/test-consolidated-ci.yml
echo "✅ Test workflow removed"

# 4. Update .gitignore
if ! grep -q "workflows-archive" .gitignore; then
  echo ".github/workflows-archive/" >> .gitignore
  echo "✅ Updated .gitignore"
fi

# 5. Commit changes
git add .github/workflows .gitignore
git commit -m "chore(ci): remove old CI workflows after successful migration

- Archived reusable-ci.yml to workflows-archive/
- Removed parallel testing workflow
- Removed test workflow
- Updated .gitignore to exclude archive

Migration to consolidated CI workflow complete."

echo "✅ Cleanup complete"
```

## Success Criteria

- [ ] Consolidated workflow created and validated
- [ ] Repository config created
- [ ] Test workflow passes all checks
- [ ] Parallel execution successful for 1 week
- [ ] New workflow success rate ≥ old workflow
- [ ] Switchover completed without issues
- [ ] Cleanup completed

## Continue to Part 3

Next part covers Phase 2: ubuntu-autoinstall-agent migration (more complex).
