# Go Module Tagging System

<!-- file: docs/go-module-tagging.md -->
<!-- version: 1.0.0 -->
<!-- guid: 7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d -->

This document explains how the automatic Go module tagging system works and how to integrate it into your workflows.

## Overview

When working with Go modules that are published to GitHub, each module needs its own version tag for proper module resolution. For a repository with multiple Go SDK packages like `gcommon`, we need module-specific tags such as:

- `sdks/go/v1/common/v1.3.0`
- `sdks/go/v1/config/v1.3.0`
- `sdks/go/v1/database/v1.3.0`
- etc.

This system automatically creates these module-specific tags whenever a main version tag is created.

## Components

### 1. Core Script: `scripts/create-module-tags.py`

This script:
- Detects all Go SDK modules in `sdks/go/v1/`
- Creates module-specific tags for each package
- Can be run manually or from CI/CD
- Supports both local and remote tag creation

**Usage:**
```bash
# Create module tags for v1.3.0
python3 scripts/create-module-tags.py v1.3.0

# In CI environment (automatically pushes tags)
PUSH_TAGS=true python3 scripts/create-module-tags.py v1.3.0
```

### 2. Automatic Workflow: `.github/workflows/auto-module-tagging.yml`

This workflow:
- Triggers when version tags are pushed (`v*.*.*`)
- Can be manually triggered for existing tags
- Automatically creates module-specific tags
- Only runs on repositories with Go SDK modules

### 3. Post-Tag Hook: `scripts/post-tag-hook.py`

This script can be integrated into existing workflows:
- Lightweight wrapper around the module tagging script
- Gracefully handles repositories without Go SDK modules
- Can be called as a step in existing release workflows

## Integration Methods

### Method 1: Automatic (Recommended)

The auto-module-tagging workflow automatically handles tag creation when you push version tags:

```bash
# Create and push a version tag
git tag v1.4.0
git push origin v1.4.0

# Module-specific tags are automatically created and pushed
```

### Method 2: Manual Workflow Trigger

You can manually trigger the workflow for existing tags:

1. Go to Actions → "Automatic Module Tagging"
2. Click "Run workflow"
3. Enter the version tag (e.g., `v1.3.0`)
4. Click "Run workflow"

### Method 3: Integration into Existing Workflows

Add this step to your existing release workflows:

```yaml
- name: Create module-specific tags
  run: |
    python3 scripts/post-tag-hook.py ${{ steps.version.outputs.tag }}
  env:
    PUSH_TAGS: true
```

### Method 4: Manual Script Execution

For local development or testing:

```bash
# Create tags locally (don't push)
python3 scripts/create-module-tags.py v1.3.0

# Create and push tags
PUSH_TAGS=true python3 scripts/create-module-tags.py v1.3.0
```

## Repository Requirements

### Required Structure

For the system to work, your repository must have:

```
sdks/
└── go/
    └── v1/
        ├── common/
        │   └── go.mod
        ├── config/
        │   └── go.mod
        └── database/
            └── go.mod
```

### Required Scripts

The following scripts must be present:
- `scripts/create-module-tags.py` - Core tagging functionality
- `scripts/post-tag-hook.py` - Workflow integration helper

### Workflow Files (Optional)

- `.github/workflows/auto-module-tagging.yml` - Automatic tagging workflow

## Sync Integration

Since this system is designed to work with the `ghcommon` sync system:

1. **Add to ghcommon first**: New functionality goes into the `ghcommon` repository
2. **Sync to other repos**: The sync system distributes the scripts and workflows
3. **Repository-specific customization**: Each repo can customize behavior via environment variables

### For Non-Go Repositories

The system gracefully handles repositories without Go SDK modules:
- Scripts detect the absence of `sdks/go/v1/` and exit cleanly
- Workflows skip execution if no SDK modules are found
- No errors or failures occur

## Example Integration

Here's how to add module tagging to an existing release workflow:

```yaml
name: Release

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  version:
    runs-on: ubuntu-latest
    outputs:
      tag: ${{ steps.version.outputs.tag }}
    steps:
      - uses: actions/checkout@v5

      - name: Calculate version
        id: version
        run: |
          # Your version calculation logic
          echo "tag=v1.4.0" >> $GITHUB_OUTPUT

      - name: Create version tag
        run: |
          git tag ${{ steps.version.outputs.tag }}
          git push origin ${{ steps.version.outputs.tag }}

      - name: Create module-specific tags
        run: |
          python3 scripts/post-tag-hook.py ${{ steps.version.outputs.tag }}
        env:
          PUSH_TAGS: true
```

## Troubleshooting

### Common Issues

1. **"No SDK modules found"**
   - This is normal for repositories without Go protobuf SDKs
   - The system will skip tagging and exit successfully

2. **"Version tag does not exist"**
   - Ensure the main version tag exists before creating module tags
   - Check that the tag format matches `v*.*.*`

3. **"Failed to create tag"**
   - Check that you have write permissions to the repository
   - Verify that the tag doesn't already exist

### Debugging

To debug the tagging process:

```bash
# Run with verbose output
python3 scripts/create-module-tags.py v1.3.0

# Check existing tags
git tag -l | grep "sdks/go/v1"

# Verify module structure
find sdks/go/v1 -name "go.mod" -type f
```

## Benefits

1. **Automatic**: No manual intervention required for module tagging
2. **Safe**: Only creates tags, never deletes or modifies existing ones
3. **Flexible**: Works with manual triggers, automatic workflows, or script integration
4. **Repository-agnostic**: Gracefully handles repositories with and without Go modules
5. **Sync-compatible**: Designed to work with the ghcommon sync system
