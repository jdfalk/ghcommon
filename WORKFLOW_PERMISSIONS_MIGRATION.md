# Workflow Permissions Migration Guide

## Overview

This document explains the migration from reusable workflows with embedded
permissions to a security-enhanced model where permissions are only defined in
calling workflows.

## What Changed

### Before (Security Risk)

```yaml
# reusable-workflow.yml
name: Reusable Workflow
on:
  workflow_call:

permissions: # ❌ This creates security conflicts
  contents: write
  issues: write

jobs:
  example:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
```

### After (Secure)

```yaml
# reusable-workflow.yml
name: Reusable Workflow
on:
  workflow_call:

# Permissions removed - should be set in calling workflow
# See: https://docs.github.com/en/actions/using-workflows/reusing-workflows#supported-keywords-for-jobs-that-call-a-reusable-workflow

jobs:
  example:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
```

```yaml
# calling-workflow.yml
name: Calling Workflow
on:
  push:
    branches: [main]

permissions: # ✅ Permissions defined here
  contents: write
  issues: write

jobs:
  call-reusable:
    uses: ./.github/workflows/reusable-workflow.yml
```

## Benefits

1. **No Permission Conflicts**: Eliminates GitHub's "allowed permissions" errors
2. **Better Security**: Calling workflows explicitly declare what permissions
   they grant
3. **Principle of Least Privilege**: Each calling workflow can grant only the
   minimal permissions needed
4. **Transparency**: Clear visibility of what permissions each workflow requires

## Migration Steps

### 1. Automated Migration (Completed)

We've automatically removed permissions from all reusable workflows using:

```bash
python3 scripts/remove-reusable-workflow-permissions.py
```

This script:

- ✅ Removed permissions blocks from 13 reusable workflows
- ✅ Created backups of original files (`.backup` extension)
- ✅ Added explanatory comments where permissions were removed

### 2. Update Calling Workflows

For each calling workflow, add the appropriate permissions based on which
reusable workflows it calls.

## Required Permissions by Reusable Workflow

### Core Workflows

#### `reusable-codeql.yml` (Security Scanning)

**Minimal required permissions:**

```yaml
permissions:
  contents: read
  security-events: write
```

#### `reusable-ci.yml` (Continuous Integration)

**Minimal required permissions:**

```yaml
permissions:
  contents: read
```

**Full permissions (if using all features):**

```yaml
permissions:
  contents: read
  security-events: write
  id-token: write
  attestations: write
  repository-projects: write
  actions: read
  packages: write
  pull-requests: write
```

#### `reusable-docker-build.yml` (Container Build)

**Minimal required permissions:**

```yaml
permissions:
  contents: read
  packages: write
```

### Issue & PR Management

#### `reusable-labeler.yml` (Auto Labeling)

**Required permissions:**

```yaml
permissions:
  contents: read
  issues: write
  pull-requests: write
```

#### `reusable-label-sync.yml` (Label Synchronization)

**Required permissions:**

```yaml
permissions:
  contents: read
  issues: write
  pull-requests: write
```

#### `reusable-stale.yml` (Stale Issue Management)

**Required permissions:**

```yaml
permissions:
  contents: read
  issues: write
  pull-requests: write
```

#### `reusable-intelligent-issue-labeling.yml` (AI Issue Labeling)

**Required permissions:**

```yaml
permissions:
  contents: read
  issues: write
```

#### `reusable-unified-issue-management.yml` (Comprehensive Issue Management)

**Minimal required permissions:**

```yaml
permissions:
  contents: read
  issues: write
```

**Full permissions (if using all features):**

```yaml
permissions:
  contents: write
  issues: write
  pull-requests: write
  repository-projects: write
  security-events: read
  checks: write
  statuses: write
  actions: write
```

### Documentation

#### `reusable-docs-update.yml` (Documentation Updates)

**Required permissions:**

```yaml
permissions:
  contents: write
  issues: write
  pull-requests: write
```

#### `reusable-enhanced-docs-update.yml` (Enhanced Documentation)

**Required permissions:**

```yaml
permissions:
  contents: write
```

### Release Management

#### `reusable-goreleaser.yml` (Go Release Management)

**Minimal required permissions:**

```yaml
permissions:
  contents: write
```

**Full permissions (if publishing packages):**

```yaml
permissions:
  contents: write
  packages: write
  issues: write
  pull-requests: write
```

#### `reusable-semantic-versioning.yml` (Semantic Versioning)

**Required permissions:**

```yaml
permissions:
  contents: write
  checks: write
  actions: read
  pull-requests: write
  issues: write
```

### Automation & Maintenance

#### `reusable-ai-rebase.yml` (AI-Assisted Rebasing)

**Required permissions:**

```yaml
permissions:
  contents: write
  pull-requests: write
```

#### `reusable-repo-settings.yml` (Repository Settings)

**Required permissions:**

```yaml
permissions:
  contents: write
```

#### `reusable-super-linter.yml` (Code Linting)

**Required permissions:**

```yaml
permissions:
  contents: read
```

## Example Calling Workflows

### Basic CI with Security Scanning

```yaml
name: CI with Security

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  security-events: write

jobs:
  ci:
    uses: ./.github/workflows/reusable-ci.yml

  security-scan:
    uses: ./.github/workflows/reusable-codeql.yml
    secrets:
      github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Comprehensive Issue Management

```yaml
name: Issue Management

on:
  issues:
    types: [opened, edited, labeled]
  pull_request:
    types: [opened, edited, labeled]

permissions:
  contents: read
  issues: write
  pull-requests: write

jobs:
  auto-label:
    uses: ./.github/workflows/reusable-labeler.yml

  intelligent-labeling:
    uses: ./.github/workflows/reusable-intelligent-issue-labeling.yml

  manage-stale:
    uses: ./.github/workflows/reusable-stale.yml
```

### Release Pipeline

```yaml
name: Release

on:
  push:
    tags: ['v*']

permissions:
  contents: write
  packages: write
  issues: write
  pull-requests: write

jobs:
  release:
    uses: ./.github/workflows/reusable-goreleaser.yml
    secrets:
      github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Best Practices

### 1. Principle of Least Privilege

Only grant the minimal permissions required for your specific use case:

```yaml
# ✅ Good - minimal permissions
permissions:
  contents: read

# ❌ Avoid - excessive permissions
permissions:
  contents: write
  issues: write
  pull-requests: write
  packages: write
  # ... (when you only need contents: read)
```

### 2. Separate Workflows by Permission Requirements

Consider splitting workflows that require different permission levels:

```yaml
# ci.yml - read-only operations
permissions:
  contents: read

# release.yml - write operations
permissions:
  contents: write
  packages: write
```

### 3. Document Permission Requirements

Always document why specific permissions are needed:

```yaml
permissions:
  contents: read # For checking out code
  security-events: write # For uploading SARIF results
  packages: write # For publishing Docker images
```

### 4. Regular Permission Audits

Periodically review and minimize permissions:

- Remove unused permissions
- Split workflows with different security requirements
- Use separate tokens for different permission levels when possible

## Troubleshooting

### "Required permission not granted" Error

If you see this error, add the missing permission to your calling workflow:

```yaml
# Error: security-events permission required
permissions:
  contents: read
  security-events: write # Add this
```

### Multiple Reusable Workflows with Different Permissions

Use the union of all required permissions:

```yaml
# Workflow calls both CI (needs contents: read) and labeler (needs issues: write)
permissions:
  contents: read # For CI
  issues: write # For labeler
  pull-requests: write # For labeler
```

### Token Scope Issues

Ensure your workflow token has the necessary scopes:

```yaml
# In repository settings → Actions → General → Workflow permissions
# Choose "Read and write permissions" if needed
```

## Migration Checklist

- [ ] ✅ Reusable workflows updated (permissions removed)
- [ ] Update calling workflows with appropriate permissions
- [ ] Test workflows to ensure they work with new permissions
- [ ] Remove any workflow-level permission overrides that are no longer needed
- [ ] Document permission requirements for your team
- [ ] Set up permission monitoring/alerting if needed

## Files Changed

### Reusable Workflows Modified (13 files)

- `reusable-labeler.yml` - Removed 1 permissions block
- `reusable-ci.yml` - Removed 6 permissions blocks
- `reusable-docs-update.yml` - Removed 1 permissions block
- `reusable-docker-build.yml` - Removed 1 permissions block
- `reusable-codeql.yml` - Removed 1 permissions block
- `reusable-stale.yml` - Removed 1 permissions block
- `reusable-ai-rebase.yml` - Removed 1 permissions block
- `reusable-unified-issue-management.yml` - Removed 4 permissions blocks
- `reusable-goreleaser.yml` - Removed 1 permissions block
- `reusable-semantic-versioning.yml` - Removed 1 permissions block
- `reusable-repo-settings.yml` - Removed 1 permissions block
- `reusable-label-sync.yml` - Removed 1 permissions block
- `reusable-intelligent-issue-labeling.yml` - Removed 1 permissions block

### Backup Files Created

All original files are preserved with `.backup` extension in case rollback is
needed.

### Analysis Files Generated

- `workflow-permissions-analysis.json` - Detailed analysis of permission
  requirements
- `workflow-templates/` - Example calling workflow templates

## Support

For questions about this migration:

1. Check the generated templates in `workflow-templates/`
2. Review the analysis in `workflow-permissions-analysis.json`
3. Refer to
   [GitHub's official documentation](https://docs.github.com/en/actions/using-workflows/reusing-workflows#supported-keywords-for-jobs-that-call-a-reusable-workflow)

## Scripts Used

- `scripts/remove-reusable-workflow-permissions.py` - Removes permissions from
  reusable workflows
- `scripts/analyze-reusable-workflow-permissions.py` - Analyzes permission
  requirements and generates templates
