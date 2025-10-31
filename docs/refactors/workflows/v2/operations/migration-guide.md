<!-- file: docs/refactors/workflows/v2/operations/migration-guide.md -->
<!-- version: 1.1.0 -->
<!-- guid: e6f7a8b9-c0d1-2e3f-4a5b-6c7d8e9f0a1b -->

# Migration Guide: v1 to v2 Workflow System

## Overview

This guide provides step-by-step instructions for migrating from the v1 workflow system to the v2
branch-aware workflow system with minimal disruption.

**Migration Time**: 2-4 weeks depending on repository complexity **Risk Level**: Low to Medium (can
be rolled back at any point) **Prerequisites**:

- Admin access to repository
- Understanding of current v1 workflows
- Access to create branches and GitHub secrets

## Migration Strategy

The migration follows a phased rollout approach:

```text
Phase 1: Preparation (Week 1)
├── Audit current workflows
├── Set up feature flags
├── Create stable branches
└── Configure version policies

Phase 2: Pilot (Week 2)
├── Enable v2 for one repository
├── Monitor and validate
├── Gather feedback
└── Fix issues

Phase 3: Gradual Rollout (Week 3)
├── Enable for 25% of repositories
├── Enable for 50% of repositories
├── Enable for 75% of repositories
└── Monitor each stage

Phase 4: Complete Migration (Week 4)
├── Enable for all repositories
├── Deprecate v1 workflows
├── Update documentation
└── Archive v1 code
```

## Pre-Migration Checklist

Before starting migration, complete these tasks:

- [ ] **Audit current workflows**: Document all active workflows
- [ ] **Backup configurations**: Save current workflow files
- [ ] **Review dependencies**: Identify external dependencies
- [ ] **Create test plan**: Define success criteria
- [ ] **Set up monitoring**: Configure alerting for failures
- [ ] **Schedule downtime**: If needed for critical changes
- [ ] **Notify stakeholders**: Inform team of migration timeline
- [ ] **Prepare rollback plan**: Document revert procedures

## Phase 1: Preparation

### Step 1.1: Audit Current Workflows

List all workflows in the repository:

```bash
# List all workflow files
find .github/workflows -name "*.yml" -type f

# Check workflow runs
gh run list --limit 50

# Identify active workflows
gh api repos/{owner}/{repo}/actions/workflows \
  --jq '.workflows[] | select(.state == "active") | .path'
```

Document each workflow:

```yaml
# Create workflow-inventory.yml
workflows:
  - name: ci.yml
    type: continuous-integration
    triggers: [push, pull_request]
    languages: [go, python]
    dependencies:
      - Super Linter
      - codecov

  - name: release.yml
    type: release
    triggers: [push]
    tags_pattern: v*
    languages: [go]
```

### Step 1.2: Set Up Feature Flags

Create feature flag configuration:

```yaml
# file: .github/workflow-feature-flags.yml
# version: 1.0.0

feature_flags:
  # Global v2 system toggle
  use_v2_workflows:
    enabled: false
    description: 'Enable v2 branch-aware workflow system'
    enabled_branches: [] # Start with empty, add gradually

  # Per-feature flags
  use_branch_aware_matrix:
    enabled: false
    description: 'Use branch-aware matrix generation'
    enabled_branches: []

  use_change_detection:
    enabled: false
    description: 'Use intelligent change detection'
    enabled_branches: []

  use_parallel_releases:
    enabled: false
    description: 'Enable parallel release tracks'
    enabled_branches: []
```

Commit and push:

```bash
git add .github/workflow-feature-flags.yml
git commit -m "feat(ci): add v2 workflow feature flags"
git push origin main
```

### Step 1.3: Create Stable Branches

Identify which stable branches are needed:

```bash
# Check Go version in go.mod
go list -m -json | jq -r '.GoVersion'

# Check Python version in pyproject.toml or setup.py
python --version

# Check Node version in .nvmrc or package.json
node --version

# Check Rust version
rustc --version
```

Create stable branches for current versions:

```bash
# Example: Repository using Go 1.24
git checkout -b stable-1-go-1.24
git push origin stable-1-go-1.24

# Set branch protection
gh api repos/{owner}/{repo}/branches/stable-1-go-1.24/protection \
  -X PUT \
  -f required_status_checks[strict]=true \
  -f required_status_checks[contexts][]=ci \
  -f enforce_admins=true \
  -f required_pull_request_reviews[required_approving_review_count]=1
```

### Step 1.4: Configure Version Policies

Create version policy configuration:

```yaml
# file: .github/workflow-versions.yml
# version: 1.0.0

version_policies:
  # Main branch - latest versions
  main:
    created: '2025-10-14'
    description: 'Latest stable versions'
    go:
      versions: ['1.25']
      default: '1.25'
    python:
      versions: ['3.14']
      default: '3.14'
    node:
      versions: ['22']
      default: '22'
    rust:
      versions: ['stable']
      default: 'stable'

  # Stable branch for Go 1.24
  stable-1-go-1.24:
    created: '2025-10-14'
    description: 'Go 1.24 maintenance branch'
    work_stops_at: '2026-04-14' # 6 months
    lock_after_days: 180
    go:
      versions: ['1.24']
      default: '1.24'
      locked: true
    python:
      versions: ['3.13', '3.14']
      default: '3.14'
    node:
      versions: ['20', '22']
      default: '22'
    rust:
      versions: ['stable']
      default: 'stable'
```

Commit configuration:

```bash
git add .github/workflow-versions.yml
git commit -m "feat(ci): add v2 version policies for main and stable branches"
git push origin main

# Cherry-pick to stable branch
git checkout stable-1-go-1.24
git cherry-pick main
git push origin stable-1-go-1.24
```

### Step 1.5: Install Helper Scripts

Copy helper scripts from ghcommon repository:

```bash
# Create scripts directory
mkdir -p .github/workflows/scripts

# Copy helper modules
curl -o .github/workflows/scripts/workflow_common.py \
  https://raw.githubusercontent.com/jdfalk/ghcommon/main/.github/workflows/scripts/workflow_common.py

curl -o .github/workflows/scripts/ci_workflow.py \
  https://raw.githubusercontent.com/jdfalk/ghcommon/main/.github/workflows/scripts/ci_workflow.py

curl -o .github/workflows/scripts/release_workflow.py \
  https://raw.githubusercontent.com/jdfalk/ghcommon/main/.github/workflows/scripts/release_workflow.py

# Make executable
chmod +x .github/workflows/scripts/*.py

# Test helper scripts
python .github/workflows/scripts/workflow_common.py --version
```

Install dependencies:

```bash
# Create requirements.txt for workflow scripts
cat > .github/workflows/scripts/requirements.txt << 'EOF'
PyYAML>=6.0
requests>=2.31.0
PyJWT>=2.8.0
cryptography>=41.0.0
EOF

# Test installation
pip install -r .github/workflows/scripts/requirements.txt
```

## Phase 2: Pilot Migration

### Step 2.1: Choose Pilot Repository

Select a repository for pilot migration:

**Good pilot candidates**:

- Medium complexity (not too simple, not too complex)
- Active development (to test thoroughly)
- Willing team (receptive to changes)
- Non-critical (can tolerate issues)

**Avoid for pilot**:

- Production-critical repositories
- Rarely updated repositories
- Repositories with complex custom workflows

### Step 2.2: Create v2 CI Workflow

Create new v2 CI workflow alongside v1:

```yaml
# file: .github/workflows/ci-v2.yml
# version: 1.0.0

name: CI v2 (Branch-Aware)

on:
  push:
    branches: [main, 'stable-*']
  pull_request:
    branches: [main, 'stable-*']

jobs:
  # Check if v2 is enabled
  check-feature-flag:
    name: Check v2 Feature Flag
    runs-on: ubuntu-latest
    outputs:
      enabled: ${{ steps.check.outputs.enabled }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Check feature flag
        id: check
        run: |
          python .github/workflows/scripts/workflow_common.py check-feature \
            --flag use_v2_workflows \
            --branch ${{ github.ref_name }}

  # Change detection
  detect-changes:
    name: Detect Changes
    needs: check-feature-flag
    if: needs.check-feature-flag.outputs.enabled == 'true'
    runs-on: ubuntu-latest
    outputs:
      go_files: ${{ steps.changes.outputs.go_files }}
      python_files: ${{ steps.changes.outputs.python_files }}
      has_code_changes: ${{ steps.changes.outputs.has_code_changes }}
    steps:
      - name: Checkout with history
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Detect changes
        id: changes
        run: |
          python .github/workflows/scripts/ci_workflow.py detect-changes \
            --base origin/${{ github.base_ref || 'main' }} \
            --head HEAD

  # Generate test matrix
  generate-matrix:
    name: Generate Test Matrix
    needs: [check-feature-flag, detect-changes]
    if: needs.check-feature-flag.outputs.enabled == 'true'
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.matrix.outputs.matrix }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Generate matrix
        id: matrix
        run: |
          python .github/workflows/scripts/ci_workflow.py generate-matrix \
            --branch ${{ github.ref_name }} \
            --languages go python

  # Run tests with generated matrix
  test:
    name: Test (${{ matrix.language }} ${{ matrix.version }})
    needs: [generate-matrix, detect-changes]
    if: needs.detect-changes.outputs.has_code_changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJSON(needs.generate-matrix.outputs.matrix) }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up ${{ matrix.language }}
        uses: actions/setup-${{ matrix.language }}@v5
        with:
          ${{ matrix.language }}-version: ${{ matrix.version }}

      - name: Run tests
        run: |
          # Language-specific test commands
          echo "Running tests for ${{ matrix.language }} ${{ matrix.version }}"
```

### Step 2.3: Enable Feature Flag for Pilot

Enable v2 for the pilot repository:

```bash
# Edit feature flags
vim .github/workflow-feature-flags.yml
```

```yaml
feature_flags:
  use_v2_workflows:
    enabled: true
    enabled_branches:
      - main # Enable for main branch only initially
```

Commit and push:

```bash
git add .github/workflow-feature-flags.yml
git commit -m "feat(ci): enable v2 workflows for main branch (pilot)"
git push origin main
```

### Step 2.4: Monitor Pilot Execution

Monitor the pilot workflow:

```bash
# Watch workflow runs
gh run list --workflow=ci-v2.yml --limit 10

# View specific run
gh run view <run-id>

# Check for failures
gh run list --workflow=ci-v2.yml --status failure
```

Create monitoring dashboard:

```python
#!/usr/bin/env python3
# file: scripts/monitor-pilot.py
# version: 1.0.0
# guid: f7a8b9c0-d1e2-3f4a-5b6c-7d8e9f0a1b2c

"""Monitor pilot migration workflow runs."""

import sys
from datetime import datetime, timedelta

import requests


def monitor_pilot(repo: str, days: int = 7) -> dict:
    """Monitor pilot workflow runs.

    Args:
        repo: Repository in format owner/repo
        days: Number of days to look back

    Returns:
        Dictionary with monitoring metrics
    """
    since = (datetime.now() - timedelta(days=days)).isoformat()

    # Fetch workflow runs
    response = requests.get(
        f"https://api.github.com/repos/{repo}/actions/runs",
        params={"created": f">={since}"},
        headers={"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
    )

    runs = response.json()["workflow_runs"]

    # Filter for v2 workflows
    v2_runs = [r for r in runs if "v2" in r["name"].lower()]

    # Calculate metrics
    total = len(v2_runs)
    successes = len([r for r in v2_runs if r["conclusion"] == "success"])
    failures = len([r for r in v2_runs if r["conclusion"] == "failure"])

    return {
        "total_runs": total,
        "success_rate": (successes / total * 100) if total > 0 else 0,
        "failure_count": failures,
        "avg_duration": sum(r["run_duration_ms"] for r in v2_runs) / total if total > 0 else 0
    }


if __name__ == "__main__":
    metrics = monitor_pilot("jdfalk/pilot-repo")
    print(f"Success Rate: {metrics['success_rate']:.1f}%")
    print(f"Total Runs: {metrics['total_runs']}")
    print(f"Failures: {metrics['failure_count']}")
```

### Step 2.5: Validate and Fix Issues

Run validation checklist:

- [ ] **CI passes**: All tests pass on main branch
- [ ] **Matrix generation works**: Correct versions for branch
- [ ] **Change detection accurate**: Only runs needed tests
- [ ] **No regressions**: Same test coverage as v1
- [ ] **Performance acceptable**: Similar or better runtime
- [ ] **Logs clear**: Easy to debug failures
- [ ] **Team feedback positive**: Developers find it useful

Common issues and fixes:

#### Issue: Feature flag not detected

```bash
# Verify feature flag file exists
ls -la .github/workflow-feature-flags.yml

# Check file is valid YAML
python -c "import yaml; yaml.safe_load(open('.github/workflow-feature-flags.yml'))"

# Verify branch name matches
git branch --show-current
```

#### Issue: Matrix generation fails

```bash
# Test matrix generation locally
python .github/workflows/scripts/ci_workflow.py generate-matrix \
  --branch main \
  --languages go python \
  --debug

# Check version policy exists for branch
grep -A 10 "^  main:" .github/workflow-versions.yml
```

#### Issue: Change detection too broad

```bash
# Test change detection locally
python .github/workflows/scripts/ci_workflow.py detect-changes \
  --base origin/main \
  --head HEAD \
  --verbose

# Adjust change patterns if needed
vim .github/workflows/scripts/ci_workflow.py
```

## Phase 3: Gradual Rollout

### Step 3.1: Expand to 25% of Repositories

After successful pilot (1-2 weeks), expand to more repositories:

```bash
# Select 25% of repositories
repos=(
  "jdfalk/repo1"
  "jdfalk/repo2"
  "jdfalk/repo3"
)

for repo in "${repos[@]}"; do
  echo "Migrating $repo..."

  # Clone and migrate
  gh repo clone "$repo"
  cd "$(basename $repo)"

  # Copy v2 files
  cp -r ../pilot-repo/.github/workflows/ci-v2.yml .github/workflows/
  cp -r ../pilot-repo/.github/workflows/scripts .github/workflows/
  cp ../pilot-repo/.github/workflow-feature-flags.yml .github/
  cp ../pilot-repo/.github/workflow-versions.yml .github/

  # Enable feature flag
  sed -i.bak 's/enabled: false/enabled: true/' .github/workflow-feature-flags.yml

  # Commit and push
  git add .github/
  git commit -m "feat(ci): migrate to v2 workflow system"
  git push origin main

  cd ..
done
```

### Step 3.2: Monitor Rollout

Create rollout monitoring script:

```bash
#!/bin/bash
# file: scripts/monitor-rollout.sh
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d

# Monitor v2 rollout across repositories

repos=(
  "jdfalk/repo1"
  "jdfalk/repo2"
  "jdfalk/repo3"
)

echo "=== V2 Rollout Status ==="
echo ""

for repo in "${repos[@]}"; do
  echo "Repository: $repo"

  # Check if v2 enabled
  enabled=$(gh api "repos/$repo/contents/.github/workflow-feature-flags.yml" \
    --jq '.content' | base64 -d | grep -A1 "use_v2_workflows:" | grep "enabled:" | awk '{print $2}')

  # Get recent workflow runs
  success_rate=$(gh api "repos/$repo/actions/runs?per_page=10" \
    --jq '[.workflow_runs[] | select(.name | contains("v2"))] |
           (map(select(.conclusion == "success")) | length) / length * 100')

  echo "  V2 Enabled: $enabled"
  echo "  Success Rate: ${success_rate}%"
  echo ""
done
```

### Step 3.3: Gradual Expansion

Continue expanding in phases:

**Week 3, Day 1-2**: 25% → 50%

```bash
# Enable for another 25% of repositories
# Monitor for 2 days
```

**Week 3, Day 3-4**: 50% → 75%

```bash
# Enable for another 25% of repositories
# Monitor for 2 days
```

**Week 3, Day 5-7**: 75% → 100%

```bash
# Enable for remaining repositories
# Monitor for 3 days
```

### Step 3.4: Create Stable Branches

For each repository, create stable branches as needed:

```bash
#!/bin/bash
# file: scripts/create-stable-branches.sh
# version: 1.0.0
# guid: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e

# Create stable branches for all repositories

repos=(
  "jdfalk/repo1:go:1.24"
  "jdfalk/repo2:python:3.13"
  "jdfalk/repo3:rust:1.75"
)

for entry in "${repos[@]}"; do
  IFS=':' read -r repo lang version <<< "$entry"

  echo "Creating stable branch for $repo ($lang $version)"

  # Clone repository
  gh repo clone "$repo" temp-repo
  cd temp-repo

  # Create stable branch
  branch_name="stable-1-$lang-$version"
  git checkout -b "$branch_name"

  # Update version policy
  python ../scripts/update-version-policy.py \
    --branch "$branch_name" \
    --language "$lang" \
    --version "$version"

  # Commit and push
  git add .github/workflow-versions.yml
  git commit -m "feat(ci): create $branch_name stable branch"
  git push origin "$branch_name"

  # Set branch protection
  gh api "repos/$repo/branches/$branch_name/protection" \
    -X PUT \
    -f required_status_checks[strict]=true \
    -f enforce_admins=true

  cd ..
  rm -rf temp-repo
done
```

## Phase 4: Complete Migration

### Step 4.1: Deprecate v1 Workflows

Once v2 is stable across all repositories:

```bash
# Rename v1 workflows
for file in .github/workflows/ci.yml .github/workflows/release.yml; do
  if [ -f "$file" ]; then
    mv "$file" "${file%.yml}-v1-deprecated.yml"
  fi
done

# Rename v2 workflows to standard names
mv .github/workflows/ci-v2.yml .github/workflows/ci.yml
mv .github/workflows/release-v2.yml .github/workflows/release.yml

# Commit
git add .github/workflows/
git commit -m "refactor(ci): deprecate v1 workflows, promote v2 to standard"
git push origin main
```

### Step 4.2: Update Documentation

Update all documentation references:

```bash
# Update README.md
sed -i.bak 's/CI v1/CI/g' README.md
sed -i.bak 's/ci-v2.yml/ci.yml/g' README.md

# Update CONTRIBUTING.md
sed -i.bak 's/workflow v1/workflow/g' CONTRIBUTING.md

# Commit documentation updates
git add README.md CONTRIBUTING.md
git commit -m "docs: update workflow references to v2"
git push origin main
```

### Step 4.3: Remove Feature Flags

After v2 is stable (2-4 weeks), remove feature flags:

```yaml
# Simplify workflow - remove feature flag check
# Before:
jobs:
  check-feature-flag:
    # ...

# After: (just remove the job and dependencies)
jobs:
  detect-changes:
    # Direct execution, no feature flag
```

### Step 4.4: Archive v1 Code

Archive v1 workflows for reference:

```bash
# Create archive directory
mkdir -p .github/workflows/archive/v1

# Move deprecated workflows
mv .github/workflows/*-v1-deprecated.yml .github/workflows/archive/v1/

# Add README
cat > .github/workflows/archive/v1/README.md << 'EOF'
# V1 Workflow Archive

These workflows were deprecated on 2025-10-28 and replaced with v2 branch-aware workflows.

For historical reference only. Do not use in production.

Migration completed: 2025-10-28
EOF

# Commit archive
git add .github/workflows/archive/
git commit -m "chore(ci): archive v1 workflows"
git push origin main
```

## Phase 5: Advanced Automation Rollout

With v2 core workflows stable, enable the advanced features delivered in Phase 5 across repositories.

### Step 5.1: Adopt cache-plan powered reusable caching

1. Copy `.github/workflows/reusable-advanced-cache.yml` into the target repository.
2. Ensure the repository includes `.github/workflows/scripts/automation_workflow.py` v1.2.0 or newer.
3. Replace ad-hoc `actions/cache` invocations with: 
   ```yaml
   uses: ./.github/workflows/reusable-advanced-cache.yml
   with:
     language: go # or rust/python/node
     cache-prefix: go-build
     include-branch: true
   ```
4. For ecosystems beyond the built-in profiles, extend the workflow call with `cache-plan` extras: 
   ```yaml
   with:
     language: python
     cache-prefix: py-venv
     include-branch: true
     extra-file: poetry.lock
     extra-path: ~/.cache/pip-tools
   ```
5. Verify caching locally: `python .github/workflows/scripts/automation_workflow.py cache-plan --language go`.

### Step 5.2: Enable workflow analytics reporting

1. Copy `.github/workflows/workflow-analytics.yml` to the repository.
2. Confirm the repository grants the workflow `actions:read` and `contents:read` permissions (defaults).
3. Schedule the workflow (Monday 03:00 UTC by default) or trigger manually via `gh workflow run workflow-analytics.yml -f lookback-days=14`.
4. Review the generated `workflow-analytics.md` summary and artifacts for accuracy.
5. Optional: integrate the artifact into dashboards or Slack by extending the summary step.

### Step 5.3: Update documentation and training

- Reference `docs/refactors/workflows/v2/github-apps-setup.md` for GitHub App provisioning and token management.
- Share the updated helper API (`automation_workflow.cache-plan`, lookback filtering) with maintainers.
- Record caching/analytics adoption in each repository's migration tracker.

Once Steps 5.1–5.3 are complete across repositories, mark Phase 5 finished in the rollout plan and proceed to continuous monitoring.


## Post-Migration Tasks

### Monitoring and Metrics

Set up ongoing monitoring with the shared analytics workflow:

```yaml
# file: .github/workflows/workflow-analytics.yml
# version: 1.0.0

name: Workflow Analytics

on:
  schedule:
    - cron: '0 3 * * 1' # Weekly analysis
  workflow_dispatch:
    inputs:
      lookback-days:
        description: Number of days to analyze
        required: false
        default: '30'
        type: string

jobs:
  analytics:
    uses: ./.github/workflows/workflow-analytics.yml
```

Review the generated `workflow-analytics.md` artifact each week and feed findings into reliability tracking.

### Team Training

Conduct training sessions:

- **Session 1**: Overview of v2 system (30 minutes)
- **Session 2**: Branch management (45 minutes)
- **Session 3**: Troubleshooting (30 minutes)
- **Session 4**: Q&A and best practices (30 minutes)

### Documentation Updates

Create or update documentation:

- [ ] **Developer Guide**: How to work with branch-aware CI
- [ ] **Release Guide**: How releases work with parallel tracks
- [ ] **Troubleshooting Guide**: Common issues and solutions
- [ ] **Architecture Docs**: System design and decisions

## Rollback Procedures

If critical issues occur, follow rollback procedures in [Rollback Guide](rollback-procedures.md):

```bash
# Quick rollback: Disable feature flag
sed -i.bak 's/enabled: true/enabled: false/' .github/workflow-feature-flags.yml
git commit -am "revert(ci): disable v2 workflows due to issues"
git push origin main

# Full rollback: Restore v1 workflows
git revert <migration-commit>
git push origin main
```

## Success Criteria

Migration is successful when:

- ✅ All repositories running v2 workflows
- ✅ Success rate >= 95% across all repositories
- ✅ No increase in average workflow duration
- ✅ Team feedback is positive
- ✅ Documentation is complete
- ✅ Monitoring is in place
- ✅ Rollback procedures tested
- ✅ V1 workflows archived

## Timeline Summary

| Week | Phase           | Activities                   | Success Metric       |
| ---- | --------------- | ---------------------------- | -------------------- |
| 1    | Preparation     | Audit, configure, set up     | All configs in place |
| 2    | Pilot           | One repository, monitor, fix | 95%+ success rate    |
| 3    | Gradual Rollout | 25% → 50% → 75% → 100%       | No regressions       |
| 4    | Complete        | Deprecate v1, update docs    | All repos on v2      |

## Next Steps

1. **Review** this migration guide thoroughly
2. **Prepare** by completing pre-migration checklist
3. **Execute** Phase 1 preparation tasks
4. **Monitor** pilot repository closely
5. **Adjust** based on pilot feedback
6. **Continue** with gradual rollout
7. **Complete** migration and celebrate!

## References

- [Phase 0: Foundation](../phases/phase-0-foundation.md)
- [CI Workflows Guide](../implementation/ci-workflows.md)
- [Release Workflows Guide](../implementation/release-workflows.md)
- [Testing Strategy](../implementation/testing-strategy.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Rollback Procedures](rollback-procedures.md)
