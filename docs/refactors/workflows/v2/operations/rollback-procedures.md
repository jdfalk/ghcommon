<!-- file: docs/refactors/workflows/v2/operations/rollback-procedures.md -->
<!-- version: 1.0.0 -->
<!-- guid: c45f8e91-2c3d-4e5a-b7d6-9f1a2c3d4e5f -->

# Rollback Procedures

This guide provides comprehensive procedures for rolling back from the v2 workflow system to v1, including emergency fixes, partial rollbacks, and version fallback strategies.

## Table of Contents

- [When to Rollback](#when-to-rollback)
- [Rollback Decision Criteria](#rollback-decision-criteria)
- [Quick Rollback (Feature Flags)](#quick-rollback-feature-flags)
- [Full Rollback (Workflow Reversion)](#full-rollback-workflow-reversion)
- [Partial Rollback (Specific Features)](#partial-rollback-specific-features)
- [Emergency Hotfix Procedures](#emergency-hotfix-procedures)
- [Version Fallback Strategies](#version-fallback-strategies)
- [Communication Procedures](#communication-procedures)
- [Post-Rollback Validation](#post-rollback-validation)
- [Rollback Testing](#rollback-testing)
- [Recovery Procedures](#recovery-procedures)
- [Lessons Learned Documentation](#lessons-learned-documentation)

---

## When to Rollback

### Critical Issues Requiring Immediate Rollback

**Complete Rollback Required:**

1. **Build Failures**: All CI builds failing across multiple repositories
1. **Release Blocking**: Unable to cut releases for critical hotfixes
1. **Security Issues**: v2 system introduces security vulnerabilities
1. **Data Corruption**: Helper scripts corrupting repository data
1. **Performance Degradation**: Workflow execution time increased by >200%

**Partial Rollback Sufficient:**

1. **Feature-Specific Failures**: Single feature (docs, maintenance, etc.) failing
1. **Language-Specific Issues**: Only affecting one language (Go, Python, etc.)
1. **Branch-Specific Problems**: Only affecting stable branches
1. **Cache Issues**: Caching causing intermittent failures
1. **Matrix Generation Errors**: Matrix too large or empty

### Non-Critical Issues (Do Not Rollback)

1. **Minor Linting Issues**: Can be fixed with linter config updates
1. **Documentation Generation Warnings**: Non-blocking issues
1. **Cache Misses**: Performance impact but not blocking
1. **Metric Collection Failures**: Analytics not critical
1. **Single Repository Issues**: Isolated problems

---

## Rollback Decision Criteria

### Decision Matrix

```mermaid
graph TD
    A[Issue Detected] --> B{Severity?}
    B -->|Critical| C{Affects All Repos?}
    B -->|High| D{Blocking Releases?}
    B -->|Medium| E{Fix Available in < 2 hours?}
    B -->|Low| F[Do Not Rollback]
    
    C -->|Yes| G[Full Rollback]
    C -->|No| H[Partial Rollback]
    
    D -->|Yes| G
    D -->|No| I{Affects > 50% Repos?}
    
    I -->|Yes| H
    I -->|No| J[Disable Feature Flag]
    
    E -->|Yes| F
    E -->|No| J
```text

### Severity Levels

**Critical (Immediate Full Rollback):**
- All CI/CD pipelines down
- Security vulnerability introduced
- Data corruption or loss
- Unable to deploy critical hotfixes

**High (Immediate Partial Rollback):**
- >50% of repositories affected
- Release pipeline blocked
- Performance degraded >200%
- Core functionality broken

**Medium (Disable Feature Flags):**
- 25-50% of repositories affected
- Non-critical features broken
- Performance degraded 100-200%
- Workaround available

**Low (Monitor and Fix):**
- <25% of repositories affected
- Minor issues or warnings
- Performance degraded <100%
- Easy fix available

---

## Quick Rollback (Feature Flags)

### Step 1: Identify Problematic Feature

```bash
#!/bin/bash
# Identify which feature is causing issues

# Check recent workflow runs
gh run list --workflow=ci.yml --limit 20 --json conclusion,url,displayTitle

# Check for common errors
gh run view --log | grep -E "ERROR|FATAL|Failed"

# Review helper script logs
gh run view --log | grep "workflow_common.py\|ci_workflow.py\|release_workflow.py"
```text

### Step 2: Disable Feature Flag

**Option 1: Repository-Level Disable**

```yaml
# .github/workflow-versions.yml
version: "1.0.0"

# Global feature flag - disables v2 entirely
use_workflow_v2: false  # Changed from true

feature_flags:
  # Individual flags still available
  use_change_detection: false
  use_matrix_generation: false
  use_release_automation: false
```text

**Option 2: Workflow-Level Disable**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, "stable-1-*"]

# Override feature flag for this workflow only
env:
  USE_WORKFLOW_V2: false  # Add this to disable v2

jobs:
  # Rest of workflow...
```text

**Option 3: Job-Level Disable**

```yaml
jobs:
  test-go:
    env:
      USE_WORKFLOW_V2: false  # Disable only for this job
    steps:
      - uses: actions/checkout@v4
      # Rest of job...
```text

### Step 3: Verify Flag Disable

```bash
#!/bin/bash
# Verify feature flag is disabled

# Check workflow file
cat .github/workflow-versions.yml | grep -A 5 "use_workflow_v2"

# Trigger a test run
gh workflow run ci.yml --ref main

# Monitor the run
gh run watch

# Verify v2 not being used
gh run view --log | grep -E "workflow-v2|matrix-generation|change-detection"
```text

### Step 4: Monitor Results

```python
#!/usr/bin/env python3
"""Monitor workflow runs after feature flag disable.

This script checks recent workflow runs to verify rollback success.
"""

import subprocess
import json
from datetime import datetime, timedelta


def check_recent_runs():
    """Check recent workflow runs for success rate.
    
    Returns:
        dict: Run statistics including success/failure counts.
    """
    # Get runs from last hour
    cutoff = (datetime.now() - timedelta(hours=1)).isoformat()
    
    cmd = [
        "gh", "run", "list",
        "--workflow=ci.yml",
        "--limit", "50",
        "--json", "conclusion,createdAt,durationMs"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    runs = json.loads(result.stdout)
    
    # Filter recent runs
    recent_runs = [
        r for r in runs
        if r["createdAt"] >= cutoff
    ]
    
    # Calculate stats
    stats = {
        "total": len(recent_runs),
        "success": sum(1 for r in recent_runs if r["conclusion"] == "success"),
        "failure": sum(1 for r in recent_runs if r["conclusion"] == "failure"),
        "avg_duration": sum(r.get("durationMs", 0) for r in recent_runs) / len(recent_runs) if recent_runs else 0
    }
    
    return stats


if __name__ == "__main__":
    stats = check_recent_runs()
    
    print(f"Workflow Statistics (Last Hour)")
    print(f"Total Runs: {stats['total']}")
    print(f"Success: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
    print(f"Failure: {stats['failure']} ({stats['failure']/stats['total']*100:.1f}%)")
    print(f"Avg Duration: {stats['avg_duration']/1000/60:.1f} minutes")
    
    # Alert if high failure rate
    if stats['failure'] / stats['total'] > 0.2:
        print("\n⚠️  WARNING: High failure rate detected!")
        print("Consider full rollback if issues persist.")


---

## Full Rollback (Workflow Reversion)

### Overview

Full rollback involves reverting all v2 workflows back to v1 versions and removing helper scripts.

### Prerequisites

1. **Backup Current State**

```bash
#!/bin/bash
# Backup current workflow state

BACKUP_DIR="workflow-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup workflows
cp -r .github/workflows "$BACKUP_DIR/"

# Backup helper scripts
cp -r .github/helpers "$BACKUP_DIR/"

# Backup configuration
cp .github/workflow-versions.yml "$BACKUP_DIR/" 2>/dev/null || true

# Create manifest
cat > "$BACKUP_DIR/MANIFEST.md" <<EOF
# Workflow Backup

Created: $(date)
Branch: $(git branch --show-current)
Commit: $(git rev-parse HEAD)

## Files Backed Up
$(find "$BACKUP_DIR" -type f | wc -l) files

## Workflow Files
$(ls "$BACKUP_DIR/workflows/")
EOF

echo "✅ Backup created: $BACKUP_DIR"
```text

1. **Identify v1 Baseline**

```bash
#!/bin/bash
# Find the last known good v1 state

# Look for v1 tag or commit
git log --all --grep="v1" --oneline | head -5

# Or find commit before v2 migration
git log --all --grep="feat(ci): implement workflow v2" --oneline

# Show diff from v1 to current
LAST_V1_COMMIT="abc123"  # Replace with actual commit
git diff $LAST_V1_COMMIT HEAD -- .github/workflows/
```text

### Step-by-Step Rollback

#### 1. Disable v2 Feature Flags

```yaml
# .github/workflow-versions.yml
version: "1.0.0"

# Disable v2 completely
use_workflow_v2: false

feature_flags:
  use_change_detection: false
  use_matrix_generation: false
  use_release_automation: false
  use_docs_automation: false
  use_maintenance_automation: false
  use_advanced_features: false
```text

#### 2. Revert Workflow Files

```bash
#!/bin/bash
# Revert workflows to v1 versions

# Option A: Revert to specific commit
LAST_V1_COMMIT="abc123"  # Replace with actual commit
git checkout $LAST_V1_COMMIT -- .github/workflows/

# Option B: Use backed up v1 workflows
V1_BACKUP="path/to/v1-workflows-backup"
cp -r "$V1_BACKUP/workflows/"* .github/workflows/

# Verify files reverted
git status .github/workflows/
```text

#### 3. Remove Helper Scripts

```bash
#!/bin/bash
# Remove v2 helper scripts

# Remove helper directory
rm -rf .github/helpers/

# Remove configuration
rm -f .github/workflow-versions.yml

# Verify removal
git status | grep -E "helpers|workflow-versions"
```text

#### 4. Update Dependencies

```yaml
# .github/workflows/ci.yml (v1 version)
name: CI

on:
  push:
    branches: [main, "stable-1-*"]
  pull_request:
    branches: [main]

jobs:
  test-go:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
          cache: true
      
      - name: Run tests
        run: go test -v ./...
      
      - name: Build
        run: go build -v ./...
```text

#### 5. Commit and Push Rollback

```bash
#!/bin/bash
# Commit rollback changes

git add .github/

git commit -m "revert(workflows): rollback to v1 workflow system

Reverted all workflows to v1 due to critical issues with v2:
- Removed .github/helpers/ directory
- Removed workflow-versions.yml configuration
- Restored v1 workflow files
- Disabled all v2 feature flags

Reason: [Brief description of issue]
Rollback Decision: [Link to decision document]
Recovery Plan: [Link to recovery plan]
"

# Push to main (requires force if needed)
git push origin main

# Or create rollback branch
git checkout -b rollback/v2-to-v1
git push origin rollback/v2-to-v1
```text

#### 6. Verify Rollback

```python
#!/usr/bin/env python3
"""Verify rollback to v1 completed successfully.

This script checks for v2 artifacts and v1 restoration.
"""

import os
import subprocess
from pathlib import Path


def check_v2_removed():
    """Verify v2 components removed.
    
    Returns:
        list: Any remaining v2 artifacts found.
    """
    artifacts = []
    
    # Check for helpers directory
    if Path(".github/helpers").exists():
        artifacts.append(".github/helpers/ still exists")
    
    # Check for workflow-versions.yml
    if Path(".github/workflow-versions.yml").exists():
        artifacts.append(".github/workflow-versions.yml still exists")
    
    # Check for v2 imports in workflows
    result = subprocess.run(
        ["grep", "-r", "workflow_common.py", ".github/workflows/"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        artifacts.append("v2 helper imports found in workflows")
    
    return artifacts


def check_v1_restored():
    """Verify v1 workflows present.
    
    Returns:
        list: Missing v1 workflow files.
    """
    required_workflows = [
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml",
    ]
    
    missing = []
    for workflow in required_workflows:
        if not Path(workflow).exists():
            missing.append(workflow)
    
    return missing


if __name__ == "__main__":
    print("Checking v2 removal...")
    v2_artifacts = check_v2_removed()
    
    if v2_artifacts:
        print("❌ V2 artifacts found:")
        for artifact in v2_artifacts:
            print(f"  - {artifact}")
    else:
        print("✅ V2 components removed")
    
    print("\nChecking v1 restoration...")
    missing_v1 = check_v1_restored()
    
    if missing_v1:
        print("❌ V1 workflows missing:")
        for workflow in missing_v1:
            print(f"  - {workflow}")
    else:
        print("✅ V1 workflows restored")
    
    # Overall status
    if not v2_artifacts and not missing_v1:
        print("\n✅ Rollback verified successfully")
    else:
        print("\n❌ Rollback incomplete - manual intervention required")


---

## Partial Rollback (Specific Features)

### Overview

Partial rollback disables specific v2 features while keeping others enabled.

### Feature-Specific Rollback

#### Disable Change Detection Only

```yaml
# .github/workflow-versions.yml
version: "1.0.0"

use_workflow_v2: true  # Keep v2 enabled

feature_flags:
  use_change_detection: false  # Disable this feature
  use_matrix_generation: true  # Keep these enabled
  use_release_automation: true
```text

```yaml
# .github/workflows/ci.yml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      go: steps.filter.outputs.go
      python: steps.filter.outputs.python
    steps:
      - uses: actions/checkout@v4
      
      # Use dorny/paths-filter instead of helper script
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
```text

#### Disable Matrix Generation Only

```yaml
# .github/workflow-versions.yml
version: "1.0.0"

use_workflow_v2: true

feature_flags:
  use_change_detection: true
  use_matrix_generation: false  # Disable matrix generation
  use_release_automation: true
```text

```yaml
# .github/workflows/ci.yml
jobs:
  test-go:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        # Hardcode matrix instead of generating
        go-version: ['1.23', '1.24', '1.25']
        os: [ubuntu-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go-version }}
      - run: go test -v ./...
```text

#### Disable Release Automation Only

```yaml
# .github/workflow-versions.yml
version: "1.0.0"

use_workflow_v2: true

feature_flags:
  use_change_detection: true
  use_matrix_generation: true
  use_release_automation: false  # Disable release automation
```text

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  release-go:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Use GoReleaser instead of helper script
      - uses: goreleaser/goreleaser-action@v6
        with:
          distribution: goreleaser
          version: latest
          args: release --clean
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```text

### Language-Specific Rollback

#### Disable v2 for Go Only

```yaml
# .github/workflows/ci.yml
jobs:
  test-go:
    env:
      USE_WORKFLOW_V2: false  # Disable v2 for Go
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
      - run: go test -v ./...
  
  test-python:
    # v2 still enabled for Python
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: python -m pytest
```text

---

## Emergency Hotfix Procedures

### Scenario: Critical Bug in Helper Script

#### 1. Identify Problematic Script

```bash
#!/bin/bash
# Find which helper script is causing issues

# Check recent workflow runs
gh run list --workflow=ci.yml --status=failure --limit=10

# Get logs from failed run
gh run view <run-id> --log > failed-run.log

# Search for Python errors
grep -A 10 "ERROR\|Traceback" failed-run.log | grep -E "workflow_common|ci_workflow|release_workflow"
```text

#### 2. Quick Fix and Deploy

```bash
#!/bin/bash
# Emergency patch for helper script

# Create hotfix branch
git checkout -b hotfix/helper-script-fix

# Fix the issue
vim .github/helpers/workflow_common.py

# Add quick test
python3 -c "from .github.helpers.workflow_common import *; validate_versions()"

# Commit with emergency tag
git add .github/helpers/workflow_common.py
git commit -m "fix(helpers): emergency patch for workflow_common.py

Critical bug in validate_versions() causing all workflows to fail.

Issue: [Brief description]
Fix: [Brief description]
Testing: [Minimal test performed]

Emergency hotfix - full testing to follow.
"

# Push and create PR
git push origin hotfix/helper-script-fix
gh pr create --title "🚨 Emergency: Fix helper script" --body "Emergency hotfix for critical workflow failure"

# Merge immediately (requires permissions)
gh pr merge --admin --squash
```text

#### 3. Verify Fix Deployed

```bash
#!/bin/bash
# Verify hotfix resolved issue

# Trigger workflow
gh workflow run ci.yml

# Watch for success
gh run watch

# Check multiple repos if using shared workflows
for repo in org/repo1 org/repo2 org/repo3; do
  echo "Checking $repo..."
  gh run list --repo=$repo --workflow=ci.yml --limit=5
done
```text

### Scenario: Emergency Rollback Needed

```bash
#!/bin/bash
# Emergency rollback script for immediate execution

set -e

echo "🚨 Starting emergency rollback..."

# 1. Disable v2 immediately via env variable
cat >> .github/workflows/ci.yml <<EOF

# EMERGENCY ROLLBACK - DO NOT REMOVE
env:
  USE_WORKFLOW_V2: false
EOF

git add .github/workflows/ci.yml
git commit -m "fix(ci): emergency rollback to v1"
git push origin main --force-with-lease

# 2. Trigger immediate workflow run
gh workflow run ci.yml

# 3. Monitor
echo "✅ Emergency rollback deployed"
echo "Monitoring workflow run..."
gh run watch

echo "✅ Emergency rollback complete"
echo "Next steps:"
echo "1. Review logs: gh run view --log"
echo "2. Document incident in issues"
echo "3. Plan proper rollback with team"
```text

---

## Version Fallback Strategies

### Language Version Rollback

#### Go Version Fallback

```yaml
# .github/workflow-versions.yml
# Rollback from Go 1.25 to 1.24

versions:
  go:
    main: "1.24"      # Rolled back from 1.25
    stable-1: "1.23"  # Rolled back from 1.24
    
branch_policies:
  "stable-1-go-1.24":
    go_version: "1.24"  # Keep stable branch locked
```text

```bash
#!/bin/bash
# Update code for Go 1.24 compatibility

# Remove Go 1.25 features
# - Integer range: for i := range n {} → for i := 0; i < n; i++ {}
# - os.Root(): Remove filesystem isolation code

# Update go.mod
go mod edit -go=1.24

# Test with Go 1.24
go test -v ./...

# Commit
git commit -am "fix(go): rollback to Go 1.24 compatibility"
```text

#### Python Version Fallback

```yaml
# .github/workflow-versions.yml
# Rollback from Python 3.14 to 3.13

versions:
  python:
    main: "3.13"      # Rolled back from 3.14
    stable-1: "3.12"  # Rolled back from 3.13
```text

```bash
#!/bin/bash
# Update code for Python 3.13 compatibility

# Check for Python 3.14 features
grep -r "PEP 735\|PEP 741" .

# Update version constraints
sed -i 's/python_requires=">=3.14"/python_requires=">=3.13"/' setup.py

# Test with Python 3.13
python3.13 -m pytest

# Commit
git commit -am "fix(python): rollback to Python 3.13 compatibility"
```text

### Dependency Version Rollback

```yaml
# Rollback specific dependencies in workflow-versions.yml

versions:
  actions:
    checkout: "v3"  # Rolled back from v4
    setup-go: "v4"   # Rolled back from v5
    upload-artifact: "v3"  # Rolled back from v4
```text

```bash
#!/bin/bash
# Update all workflows to use older action versions

# Find all workflows using new versions
grep -r "actions/checkout@v4" .github/workflows/

# Bulk replace
find .github/workflows -name "*.yml" -exec sed -i 's/@v4/@v3/g' {} \;

# Verify changes
git diff .github/workflows/

# Commit
git commit -am "fix(actions): rollback to stable action versions"
```text

---

## Communication Procedures

### Internal Team Communication

#### Rollback Announcement Template

```markdown
# Workflow v2 Rollback Announcement

## Status: ROLLING BACK TO V1

**Date:** [Current date/time]
**Severity:** [Critical/High/Medium]
**Impact:** [Description of impact]
**ETA:** [Estimated completion time]

## Issue Summary

Brief description of the issue requiring rollback.

## Affected Systems

- [ ] CI Workflows
- [ ] Release Workflows
- [ ] Documentation Generation
- [ ] Maintenance Automation

## Affected Repositories

- [ ] jdfalk/repo1
- [ ] jdfalk/repo2
- [ ] jdfalk/repo3

## Rollback Plan

1. [Step 1]
1. [Step 2]
1. [Step 3]

## Timeline

- **14:00** - Issue detected
- **14:15** - Rollback decision made
- **14:30** - Rollback initiated
- **15:00** - Rollback complete (estimated)

## Current Status

[Real-time updates as rollback progresses]

## Next Steps

[What happens after rollback completes]

## Contact

- **Incident Commander:** [Name]
- **Slack Channel:** #workflow-incident
- **GitHub Issue:** [Link]
```text

### External Stakeholder Communication

#### Status Page Update Template

```markdown
# Workflow System Maintenance

**Status:** Investigating / Rolling Back / Resolved
**Started:** [Date/time]
**Impact:** CI/CD pipeline delays

## Current Status

We are currently rolling back our workflow system to the previous version due to [brief issue description].

## Impact

- Build times may be longer than usual
- Some automated processes temporarily disabled
- Manual intervention may be required for releases

## Timeline

- **14:00 UTC** - Issue detected
- **14:15 UTC** - Rollback initiated
- **15:00 UTC** - Expected resolution

## Updates

We will provide updates every 30 minutes until resolved.

**Latest Update (14:30 UTC):**
Rollback in progress. 50% of repositories completed.
```text

### Post-Rollback Communication

```markdown
# Workflow v2 Rollback - Post-Mortem

## Summary

On [date], we rolled back from workflow v2 to v1 due to [issue].

## Timeline

- **14:00** - Issue detected in production
- **14:05** - Incident declared
- **14:15** - Rollback decision made
- **14:30** - Rollback initiated
- **15:00** - Rollback complete
- **15:30** - Systems verified stable

## Root Cause

[Detailed explanation of what went wrong]

## Impact

- [Number] repositories affected
- [Duration] of disruption
- [Number] failed builds/releases

## Resolution

Rolled back to v1 workflow system. All systems now stable.

## Action Items

1. [ ] Fix root cause in v2 system
1. [ ] Add test coverage for failure scenario
1. [ ] Update rollback procedures based on learnings
1. [ ] Plan v2 re-deployment with additional safeguards

## Lessons Learned

### What Went Well

- [Item 1]
- [Item 2]

### What Could Be Improved

- [Item 1]
- [Item 2]

### Action Items

- [Item 1] - Owner: [Name] - Due: [Date]
- [Item 2] - Owner: [Name] - Due: [Date]
```text

---

## Post-Rollback Validation

### Validation Checklist

```markdown
## Rollback Validation Checklist

### Workflow Functionality

- [ ] CI workflows run successfully
- [ ] Release workflows function correctly
- [ ] All tests pass in CI
- [ ] Build artifacts generated correctly
- [ ] Cache working as expected

### Repository State

- [ ] v2 helper scripts removed
- [ ] workflow-versions.yml removed or disabled
- [ ] v1 workflows restored
- [ ] No v2 references in workflow files
- [ ] Dependencies correct for v1

### Multi-Repository Validation

- [ ] All repositories rolled back
- [ ] Shared workflows updated
- [ ] No cross-repo dependencies on v2

### Performance Metrics

- [ ] Build times acceptable
- [ ] No workflow timeouts
- [ ] Resource usage normal
- [ ] Cache hit rate stable

### Documentation

- [ ] Rollback documented
- [ ] Team notified
- [ ] Stakeholders informed
- [ ] Post-mortem scheduled
```text

### Automated Validation Script

```python
#!/usr/bin/env python3
"""Automated validation after workflow rollback.

This script performs comprehensive validation of rollback.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List


def validate_v2_removed() -> Dict[str, bool]:
    """Validate v2 components removed.
    
    Returns:
        dict: Validation results for v2 removal.
    """
    checks = {}
    
    # Check helpers directory removed
    checks["helpers_removed"] = not Path(".github/helpers").exists()
    
    # Check workflow-versions.yml removed
    checks["config_removed"] = not Path(".github/workflow-versions.yml").exists()
    
    # Check no v2 imports in workflows
    result = subprocess.run(
        ["grep", "-r", "workflow_common", ".github/workflows/"],
        capture_output=True
    )
    checks["no_v2_imports"] = result.returncode != 0
    
    return checks


def validate_v1_working() -> Dict[str, bool]:
    """Validate v1 workflows functional.
    
    Returns:
        dict: Validation results for v1 functionality.
    """
    checks = {}
    
    # Check CI workflow exists
    checks["ci_exists"] = Path(".github/workflows/ci.yml").exists()
    
    # Trigger test run
    result = subprocess.run(
        ["gh", "workflow", "run", "ci.yml"],
        capture_output=True
    )
    checks["ci_triggered"] = result.returncode == 0
    
    # Check recent runs
    result = subprocess.run(
        ["gh", "run", "list", "--workflow=ci.yml", "--limit=5", "--json=conclusion"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        runs = json.loads(result.stdout)
        success_count = sum(1 for r in runs if r.get("conclusion") == "success")
        checks["recent_success_rate"] = success_count / len(runs) if runs else 0
    else:
        checks["recent_success_rate"] = 0
    
    return checks


def validate_performance() -> Dict[str, float]:
    """Validate workflow performance metrics.
    
    Returns:
        dict: Performance metrics.
    """
    metrics = {}
    
    # Get recent run durations
    result = subprocess.run(
        ["gh", "run", "list", "--workflow=ci.yml", "--limit=10", "--json=durationMs"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        runs = json.loads(result.stdout)
        durations = [r.get("durationMs", 0) for r in runs]
        metrics["avg_duration_minutes"] = sum(durations) / len(durations) / 1000 / 60 if durations else 0
        metrics["max_duration_minutes"] = max(durations) / 1000 / 60 if durations else 0
    else:
        metrics["avg_duration_minutes"] = 0
        metrics["max_duration_minutes"] = 0
    
    return metrics


if __name__ == "__main__":
    print("🔍 Validating Rollback...\n")
    
    # V2 removal validation
    print("Checking v2 removal...")
    v2_checks = validate_v2_removed()
    for check, result in v2_checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}: {result}")
    
    # V1 functionality validation
    print("\nChecking v1 functionality...")
    v1_checks = validate_v1_working()
    for check, result in v1_checks.items():
        if isinstance(result, bool):
            status = "✅" if result else "❌"
            print(f"{status} {check}: {result}")
        else:
            print(f"ℹ️  {check}: {result:.1%}")
    
    # Performance validation
    print("\nChecking performance...")
    perf_metrics = validate_performance()
    for metric, value in perf_metrics.items():
        print(f"ℹ️  {metric}: {value:.1f}")
    
    # Overall status
    all_v2_removed = all(v2_checks.values())
    all_v1_working = all(v if isinstance(v, bool) else v > 0.8 for v in v1_checks.values())
    perf_acceptable = perf_metrics.get("avg_duration_minutes", 999) < 30
    
    print("\n" + "="*50)
    if all_v2_removed and all_v1_working and perf_acceptable:
        print("✅ ROLLBACK VALIDATED SUCCESSFULLY")
    else:
        print("❌ ROLLBACK VALIDATION FAILED")
        if not all_v2_removed:
            print("   - V2 components not fully removed")
        if not all_v1_working:
            print("   - V1 workflows not functioning correctly")
        if not perf_acceptable:
            print("   - Performance metrics unacceptable")
```text

---

## Rollback Testing

### Pre-Rollback Testing

Before performing an actual rollback, test the process in a safe environment.

#### Test Repository Setup

```bash
#!/bin/bash
# Create test repository for rollback testing

# Fork or create test repo
gh repo create test-workflow-rollback --public --clone

cd test-workflow-rollback

# Copy current workflows
cp -r ../main-repo/.github .

# Initial commit
git add .
git commit -m "feat: initial setup for rollback testing"
git push origin main

echo "✅ Test repository created"
echo "Repository: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)"
```text

#### Rollback Dry Run

```bash
#!/bin/bash
# Perform rollback dry run

set -e

echo "🧪 Starting rollback dry run..."

# 1. Backup current state
BACKUP_DIR="rollback-test-$(date +%Y%m%d-%H%M%S)"
cp -r .github "$BACKUP_DIR"

# 2. Disable v2
cat > .github/workflow-versions.yml <<EOF
version: "1.0.0"
use_workflow_v2: false
EOF

# 3. Simulate workflow file changes (don't actually change)
echo "Would revert: $(find .github/workflows -name "*.yml" | wc -l) workflow files"

# 4. Simulate helper removal (don't actually remove)
echo "Would remove: .github/helpers/"

# 5. Test validation
if [ -d ".github/helpers" ]; then
  echo "❌ Helpers directory still exists (expected in dry run)"
else
  echo "✅ Helpers directory removed"
fi

# 6. Restore from backup
rm -rf .github
cp -r "$BACKUP_DIR" .github
rm -rf "$BACKUP_DIR"

echo "✅ Dry run complete - no changes made"
```text

#### Automated Rollback Test

```python
#!/usr/bin/env python3
"""Automated rollback testing.

This script tests the rollback process without affecting production.
"""

import subprocess
import tempfile
import shutil
from pathlib import Path


class RollbackTester:
    """Test rollback procedures in isolated environment."""
    
    def __init__(self, test_repo: str):
        """Initialize tester.
        
        Args:
            test_repo: Path to test repository.
        """
        self.test_repo = Path(test_repo)
        self.backup_dir = None
    
    def setup(self):
        """Set up test environment."""
        print("Setting up test environment...")
        
        # Create backup
        self.backup_dir = tempfile.mkdtemp(prefix="rollback-test-")
        shutil.copytree(
            self.test_repo / ".github",
            Path(self.backup_dir) / ".github"
        )
        
        print(f"✅ Backup created: {self.backup_dir}")
    
    def test_feature_flag_disable(self) -> bool:
        """Test disabling via feature flags.
        
        Returns:
            bool: Test passed.
        """
        print("\nTesting feature flag disable...")
        
        config_file = self.test_repo / ".github" / "workflow-versions.yml"
        
        # Modify config
        with open(config_file, 'r') as f:
            content = f.read()
        
        modified = content.replace(
            "use_workflow_v2: true",
            "use_workflow_v2: false"
        )
        
        with open(config_file, 'w') as f:
            f.write(modified)
        
        # Verify change
        with open(config_file, 'r') as f:
            new_content = f.read()
        
        success = "use_workflow_v2: false" in new_content
        
        status = "✅" if success else "❌"
        print(f"{status} Feature flag disable test")
        
        return success
    
    def test_file_removal(self) -> bool:
        """Test removing v2 files.
        
        Returns:
            bool: Test passed.
        """
        print("\nTesting file removal...")
        
        helpers_dir = self.test_repo / ".github" / "helpers"
        config_file = self.test_repo / ".github" / "workflow-versions.yml"
        
        # Remove files
        if helpers_dir.exists():
            shutil.rmtree(helpers_dir)
        
        if config_file.exists():
            config_file.unlink()
        
        # Verify removal
        success = not helpers_dir.exists() and not config_file.exists()
        
        status = "✅" if success else "❌"
        print(f"{status} File removal test")
        
        return success
    
    def test_workflow_trigger(self) -> bool:
        """Test triggering workflow after rollback.
        
        Returns:
            bool: Test passed.
        """
        print("\nTesting workflow trigger...")
        
        result = subprocess.run(
            ["gh", "workflow", "run", "ci.yml"],
            cwd=self.test_repo,
            capture_output=True
        )
        
        success = result.returncode == 0
        
        status = "✅" if success else "❌"
        print(f"{status} Workflow trigger test")
        
        return success
    
    def cleanup(self):
        """Restore from backup and cleanup."""
        print("\nCleaning up...")
        
        # Restore from backup
        if self.backup_dir:
            shutil.rmtree(self.test_repo / ".github")
            shutil.copytree(
                Path(self.backup_dir) / ".github",
                self.test_repo / ".github"
            )
            shutil.rmtree(self.backup_dir)
        
        print("✅ Test environment restored")
    
    def run_all_tests(self) -> bool:
        """Run all rollback tests.
        
        Returns:
            bool: All tests passed.
        """
        try:
            self.setup()
            
            results = [
                self.test_feature_flag_disable(),
                self.test_file_removal(),
                self.test_workflow_trigger()
            ]
            
            return all(results)
        
        finally:
            self.cleanup()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: test_rollback.py <test-repo-path>")
        sys.exit(1)
    
    tester = RollbackTester(sys.argv[1])
    success = tester.run_all_tests()
    
    print("\n" + "="*50)
    if success:
        print("✅ ALL ROLLBACK TESTS PASSED")
    else:
        print("❌ SOME ROLLBACK TESTS FAILED")
    
    sys.exit(0 if success else 1)
```text

---

## Recovery Procedures

### Recovering from Failed Rollback

If rollback itself fails, follow these procedures.

#### Scenario 1: Rollback Commit Failed to Push

```bash
#!/bin/bash
# Recover from failed rollback push

# Check git status
git status

# If changes staged but not pushed
if git log origin/main..HEAD | grep -q "rollback"; then
  echo "Rollback commit exists locally but not pushed"
  
  # Force push if necessary (requires permissions)
  git push origin main --force-with-lease
  
  # Or create new branch
  git branch rollback-recovery
  git push origin rollback-recovery
  
  # Create PR
  gh pr create \
    --title "Recovery: Complete workflow rollback" \
    --body "Rollback commit failed to push to main. Completing via PR."
fi
```text

#### Scenario 2: Workflows Broken After Rollback

```bash
#!/bin/bash
# Emergency fix for broken workflows after rollback

# Quick disable of all workflows
for workflow in .github/workflows/*.yml; do
  # Add env variable to disable
  sed -i '1a\
env:\
  WORKFLOW_DISABLED: true' "$workflow"
done

git add .github/workflows/
git commit -m "fix: emergency disable all workflows"
git push origin main

# Restore workflows one by one
git revert HEAD
git push origin main

echo "✅ Workflows reset - investigate issues individually"
```text

#### Scenario 3: Multiple Repositories in Inconsistent State

```python
#!/usr/bin/env python3
"""Recover multiple repositories after failed rollback.

This script checks status across repos and performs corrective actions.
"""

import subprocess
import json
from typing import List, Dict


def check_repo_status(repo: str) -> Dict[str, any]:
    """Check rollback status for a repository.
    
    Args:
        repo: Repository name (org/repo).
    
    Returns:
        dict: Status information.
    """
    # Check for v2 artifacts
    result = subprocess.run(
        ["gh", "api", f"/repos/{repo}/contents/.github/helpers"],
        capture_output=True
    )
    has_helpers = result.returncode == 0
    
    # Check recent workflow runs
    result = subprocess.run(
        ["gh", "run", "list", "--repo", repo, "--limit", "5", "--json", "conclusion"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        runs = json.loads(result.stdout)
        recent_success = sum(1 for r in runs if r.get("conclusion") == "success")
        success_rate = recent_success / len(runs) if runs else 0
    else:
        success_rate = 0
    
    return {
        "repo": repo,
        "has_v2_artifacts": has_helpers,
        "success_rate": success_rate,
        "status": "inconsistent" if has_helpers or success_rate < 0.8 else "ok"
    }


def fix_inconsistent_repo(repo: str):
    """Fix repository in inconsistent state.
    
    Args:
        repo: Repository name to fix.
    """
    print(f"\n🔧 Fixing {repo}...")
    
    # Clone repo
    subprocess.run(["gh", "repo", "clone", repo, f"temp-{repo.replace('/', '-')}"])
    
    repo_dir = f"temp-{repo.replace('/', '-')}"
    
    # Remove v2 artifacts
    subprocess.run(["rm", "-rf", f"{repo_dir}/.github/helpers"])
    subprocess.run(["rm", "-f", f"{repo_dir}/.github/workflow-versions.yml"])
    
    # Commit and push
    subprocess.run(["git", "add", "."], cwd=repo_dir)
    subprocess.run(
        ["git", "commit", "-m", "fix: complete rollback cleanup"],
        cwd=repo_dir
    )
    subprocess.run(["git", "push"], cwd=repo_dir)
    
    # Cleanup
    subprocess.run(["rm", "-rf", repo_dir])
    
    print(f"✅ Fixed {repo}")


if __name__ == "__main__":
    repos = [
        "jdfalk/repo1",
        "jdfalk/repo2",
        "jdfalk/repo3"
    ]
    
    print("Checking repository status...")
    statuses = [check_repo_status(repo) for repo in repos]
    
    # Report status
    print("\nRepository Status:")
    for status in statuses:
        icon = "❌" if status["status"] == "inconsistent" else "✅"
        print(f"{icon} {status['repo']}: {status['status']} (success: {status['success_rate']:.1%})")
    
    # Fix inconsistent repos
    inconsistent = [s["repo"] for s in statuses if s["status"] == "inconsistent"]
    
    if inconsistent:
        print(f"\nFound {len(inconsistent)} inconsistent repositories")
        response = input("Fix automatically? (yes/no): ")
        
        if response.lower() == "yes":
            for repo in inconsistent:
                fix_inconsistent_repo(repo)
            
            print("\n✅ All repositories fixed")
        else:
            print("\n⚠️  Manual intervention required")
            print("Inconsistent repos:", ", ".join(inconsistent))
    else:
        print("\n✅ All repositories consistent")
```text

### Re-deploying After Successful Rollback

Once issues are fixed, re-deploy v2 with additional safeguards.

```markdown
## V2 Re-Deployment Checklist

### Pre-Deployment

- [ ] Root cause fixed and tested
- [ ] Additional test coverage added
- [ ] Rollback procedures updated
- [ ] Team trained on new rollback process
- [ ] Monitoring enhanced
- [ ] Alerting configured

### Phased Re-Deployment

1. **Week 1: Single Test Repository**
   - [ ] Deploy to test repo only
   - [ ] Monitor for 3 days
   - [ ] Verify no issues
   - [ ] Document any problems

1. **Week 2: Pilot Repositories (3 repos)**
   - [ ] Deploy to pilot repos
   - [ ] Monitor for 5 days
   - [ ] Collect feedback
   - [ ] Adjust as needed

1. **Week 3: Gradual Rollout (25% of repos)**
   - [ ] Deploy to 25% of repositories
   - [ ] Monitor for 1 week
   - [ ] Verify metrics stable
   - [ ] No rollback triggers

1. **Week 4: Complete Rollout**
   - [ ] Deploy to remaining repositories
   - [ ] Continue monitoring
   - [ ] Document lessons learned
   - [ ] Update procedures

### Post-Deployment

- [ ] Verify all repositories using v2
- [ ] Remove v1 workflows
- [ ] Archive rollback procedures
- [ ] Celebrate success 🎉
```text

---

## Lessons Learned Documentation

### Incident Report Template

```markdown
# Workflow V2 Rollback - Incident Report

## Metadata

- **Incident Date:** [Date]
- **Incident Duration:** [Hours/Days]
- **Severity:** [Critical/High/Medium/Low]
- **Reporter:** [Name]
- **Incident Commander:** [Name]

## Executive Summary

[2-3 sentence summary of what happened and the outcome]

## Incident Timeline

| Time | Event |
|------|-------|
| 14:00 | Issue first detected |
| 14:05 | Incident declared |
| 14:15 | Rollback decision made |
| 14:30 | Rollback initiated |
| 15:00 | Rollback complete |
| 15:30 | Systems verified stable |

## Impact Analysis

### Affected Systems

- [System 1]: [Description of impact]
- [System 2]: [Description of impact]

### Affected Users

- **Internal Teams:** [Number] developers affected
- **External Users:** [Number/None]

### Business Impact

- [Number] failed builds
- [Number] delayed releases
- [Duration] of reduced productivity

## Root Cause Analysis

### Primary Cause

[Detailed explanation of the root cause]

### Contributing Factors

1. [Factor 1]
1. [Factor 2]
1. [Factor 3]

### Why It Wasn't Caught

- [Reason 1]
- [Reason 2]

## Resolution

### Immediate Actions

1. [Action 1]
1. [Action 2]

### Rollback Procedure

[Summary of rollback steps taken]

### Verification

[How resolution was verified]

## Prevention

### Short-term Actions (1-2 weeks)

1. [ ] [Action 1] - Owner: [Name] - Due: [Date]
1. [ ] [Action 2] - Owner: [Name] - Due: [Date]

### Long-term Actions (1-3 months)

1. [ ] [Action 1] - Owner: [Name] - Due: [Date]
1. [ ] [Action 2] - Owner: [Name] - Due: [Date]

## Lessons Learned

### What Went Well

1. [Item 1]
1. [Item 2]

### What Could Be Improved

1. [Item 1]
1. [Item 2]

### What We Learned

1. [Learning 1]
1. [Learning 2]

## Action Items

| Item | Owner | Due Date | Status |
|------|-------|----------|--------|
| [Item 1] | [Name] | [Date] | Open |
| [Item 2] | [Name] | [Date] | Open |

## Appendices

### Relevant Links

- GitHub Issue: [Link]
- Slack Thread: [Link]
- Post-Mortem Meeting: [Link]

### Supporting Documentation

- [Document 1]
- [Document 2]
```text

### Knowledge Base Article

```markdown
# Rollback Decision Framework

## When to Consider Rollback

Use this framework to decide if rollback is appropriate.

### Severity Assessment

1. **Critical** (Immediate Rollback)
   - All repositories affected
   - Unable to deploy critical fixes
   - Security vulnerability introduced
   - Data corruption or loss

1. **High** (Rollback Within 2 Hours)
   - >50% repositories affected
   - Release pipeline blocked
   - Performance degraded >200%

1. **Medium** (Consider Rollback)
   - 25-50% repositories affected
   - Feature-specific failures
   - Workaround available but complex

1. **Low** (Do Not Rollback)
   - <25% repositories affected
   - Minor issues
   - Easy fix available

### Decision Tree

```text
Is it affecting critical operations?
├─ Yes → Is >50% affected?
│  ├─ Yes → ROLLBACK IMMEDIATELY
│  └─ No → Consider partial rollback
└─ No → Is fix available in <2 hours?
   ├─ Yes → Fix forward
   └─ No → Consider feature flag disable
```text

### Consultation Requirements

| Severity | Required Approvals |
|----------|-------------------|
| Critical | Incident Commander |
| High | Engineering Lead + IC |
| Medium | Team Lead |
| Low | Individual Decision |

### Communication Requirements

| Severity | Communication Channels |
|----------|----------------------|
| Critical | All hands + status page |
| High | Team slack + email |
| Medium | Team slack |
| Low | Individual notification |
```text

---

## Summary

This rollback procedures guide provides:

1. **Decision Criteria**: When to rollback and what severity requires what action
1. **Quick Rollback**: Feature flag disable for immediate relief
1. **Full Rollback**: Complete reversion to v1 workflows
1. **Partial Rollback**: Disable specific features while keeping others
1. **Emergency Procedures**: Hotfix processes for critical issues
1. **Version Fallback**: Language and dependency version rollback strategies
1. **Communication**: Templates for internal and external communication
1. **Validation**: Automated scripts and checklists for verification
1. **Testing**: Procedures for testing rollback before execution
1. **Recovery**: Steps for recovering from failed rollback
1. **Documentation**: Incident reports and lessons learned templates

Use this guide to ensure safe and effective rollback when v2 issues arise. Always document incidents and update procedures based on learnings.
