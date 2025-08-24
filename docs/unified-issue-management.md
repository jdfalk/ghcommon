<!-- file: docs/unified-issue-management.md -->

# Unified Issue Management Workflow

A comprehensive, reusable GitHub Actions workflow for automated issue management across
repositories.

## Overview

The Unified Issue Management workflow provides centralized, automated issue management capabilities
that can be shared across multiple repositories. It consolidates multiple issue management
operations into a single, efficient workflow.

## Workflow Architecture

- **Canonical Workflow**:
  `jdfalk/ghcommon/.github/workflows/reusable-unified-issue-management.yml@main`
- **Documentation**: This file (`docs/unified-issue-management.md`)
- **Examples**: `/examples/workflows/issue-management-basic.yml` and
  `/examples/workflows/issue-management-advanced.yml`
- **Legacy Workflow**: `reusable-issue-management.yml` (deprecated, use unified version)

**Important**: Always use the `reusable-unified-issue-management.yml` workflow, which is the
canonical implementation with full feature support.

## Core Operations

- **Issue Updates**: Process issue updates from JSON files (create, update, comment, close, delete)
- **Copilot Tickets**: Manage tickets for GitHub Copilot review comments
- **Duplicate Management**: Automatically close duplicate issues by title
- **Security Alerts**: Generate tickets for CodeQL security alerts
- **Permalink Updates**: Update processed issue files with GitHub issue URLs

### Key Features

- **Dual-GUID Duplicate Prevention**: Prevent duplicate operations with both UUID and legacy GUID
  identifiers
- **Matrix-based Parallel Execution**: Run multiple operations efficiently
- **Auto-detection**: Automatically determine which operations to run based on context
- **Distributed File Support**: Process both legacy single-file and modern distributed formats
- **Comprehensive Logging**: Detailed summaries and progress tracking
- **Flexible Configuration**: Extensive customization options
- **Automatic Archiving**: Processed files are moved to archive directories with PR tracking

## File Management

### Distributed Files

- **Original files**: `.github/issue-updates/*.json`
- **Processed files**: `.github/issue-updates/processed/*.json`
- **Archive tracking**: Automatic via PR creation
- **Format**: Both files support dual-GUID format for enhanced duplicate prevention

When distributed files are processed, they are automatically moved to the `processed/` subdirectory
to prevent reprocessing. Both pending and processed files support the dual-GUID format:

**Pending file example** (`.github/issue-updates/feature-123.json`):

```json
{
  "action": "create",
  "title": "Feature: Add user profiles",
  "body": "Implement user profile management...",
  "guid": "a4d7a2e2-f643-466f-84c7-dcd476ec287f",
  "legacy_guid": "feature-user-profiles-2024-001"
}
```

**Processed file example** (`.github/issue-updates/processed/feature-123.json`):

```json
{
  "action": "create",
  "title": "Feature: Add user profiles",
  "body": "Implement user profile management...",
  "guid": "a4d7a2e2-f643-466f-84c7-dcd476ec287f",
  "legacy_guid": "feature-user-profiles-2024-001",
  "issue_url": "https://github.com/owner/repo/issues/123",
  "processed_at": "2024-06-23T10:30:00Z"
}
```

### Legacy Files

- **Original file**: `issue_updates.json`
- **Updated file**: Contains permalinks to created issues
- **Change tracking**: Via separate PR with link updates

### Advanced Features

- **Dual-GUID Duplicate Prevention**: Prevent duplicate operations with both UUID and legacy GUID
  identifiers
- **Matrix-based Parallel Execution**: Run multiple operations efficiently
- **Auto-detection**: Automatically determine which operations to run based on context
- **Distributed File Support**: Process both legacy single-file and modern distributed formats
- **Comprehensive Logging**: Detailed summaries and progress tracking
- **Flexible Configuration**: Extensive customization options

## Quick Start

### Basic Setup

1. **Copy the basic example** to `.github/workflows/issue-management.yml` in your repository:

```yaml
name: Issue Management

# Required permissions for the reusable workflow
permissions:
  contents: write # For creating commits and PRs
  issues: write # For creating and updating issues
  pull-requests: write # For creating PRs
  security-events: read # For reading CodeQL alerts (optional)
  repository-projects: read # For accessing project data (optional)
  actions: read # For workflow access
  checks: write # For workflow status

on:
  push:
    branches: [main]
    paths: [issue_updates.json]
  pull_request_review_comment:
    types: [created, edited, deleted]
  workflow_dispatch:

jobs:
  issue-management:
    uses: jdfalk/ghcommon/.github/workflows/reusable-unified-issue-management.yml@main
    secrets: inherit
```

1. **Commit the workflow** and it will automatically handle:
   - Processing `issue_updates.json` files when they're pushed
   - Managing Copilot review comment tickets
   - Manual execution via workflow dispatch

### Issue Updates Format

The workflow supports both legacy single-file and modern distributed file formats:

#### Distributed Format (Recommended)

Store individual issue updates in `.github/issue-updates/` directory:

**File**: `.github/issue-updates/feature-request-123.json`

```json
{
  "action": "create",
  "title": "Feature: Add dark mode support",
  "body": "Users have requested dark mode support...",
  "labels": ["enhancement", "ui"],
  "repo": "jdfalk/example-repo",
  "guid": "a4d7a2e2-f643-466f-84c7-dcd476ec287f",
  "legacy_guid": "feat-dark-mode-2024-001"
}
```

**File**: `.github/issue-updates/bug-fix-456.json`

```json
{
  "action": "comment",
  "number": null,
  "parent": "a4d7a2e2-f643-466f-84c7-dcd476ec287f",
  "body": "Progress update: 50% complete",
  "repo": "jdfalk/example-repo",
  "guid": "8c237a09-3dbf-4bb6-b992-4674bb07c3f3",
  "legacy_guid": "progress-update-2024-001"
}
```

Use the `parent` field when the issue number is unknown. Keep the `number` field set to `null` so it
can be filled in later. The workflow resolves the parent GUID to the created issue number and
updates the file during processing.

Add a `repo` field to target another repository under the `jdfalk` account. Each repository should
include the same workflows to process its updates.

#### Legacy Single-File Format (Still Supported)

Create an `issue_updates.json` file in your repository root:

#### Simple Format (Legacy)

```json
[
  {
    "action": "create",
    "title": "Bug: Application crashes on startup",
    "body": "Description of the bug...",
    "labels": ["bug", "priority-high"]
  },
  {
    "action": "comment",
    "number": 123,
    "body": "Adding more details..."
  }
]
```

#### Grouped Format (Recommended)

```json
{
  "create": [
    {
      "title": "Feature: Add dark mode",
      "body": "Users have requested dark mode support...",
      "labels": ["enhancement", "ui"],
      "guid": "feat-dark-mode-2024-001"
    }
  ],
  "update": [
    {
      "number": 456,
      "title": "Updated: Feature request for dark mode",
      "labels": ["enhancement", "ui", "in-progress"],
      "guid": "update-dark-mode-2024-001"
    }
  ],
  "comment": [
    {
      "number": 123,
      "body": "Progress update: 50% complete",
      "guid": "progress-update-2024-001"
    }
  ],
  "close": [
    {
      "number": 789,
      "state_reason": "completed",
      "guid": "close-completed-2024-001"
    }
  ]
}
```

## Configuration Options

### Input Parameters

| Parameter               | Type    | Default                | Description                                   |
| ----------------------- | ------- | ---------------------- | --------------------------------------------- |
| `operations`            | string  | `"auto"`               | Operations to run (comma-separated or "auto") |
| `dry_run`               | boolean | `false`                | Run without making changes                    |
| `force_update`          | boolean | `false`                | Force update existing tickets                 |
| `issue_updates_file`    | string  | `"issue_updates.json"` | Path to issue updates file                    |
| `cleanup_issue_updates` | boolean | `true`                 | Clean up file after processing                |
| `python_version`        | string  | `"3.11"`               | Python version to use                         |

### Operations

| Operation          | Description                     | Trigger Events       |
| ------------------ | ------------------------------- | -------------------- |
| `update-issues`    | Process issue updates from JSON | File changes, manual |
| `copilot-tickets`  | Manage Copilot review tickets   | PR events, push      |
| `close-duplicates` | Close duplicate issues          | Scheduled, manual    |
| `codeql-alerts`    | Generate security alert tickets | Scheduled, manual    |

### Auto-Detection Behavior

When `operations: "auto"` (default), the workflow automatically determines which operations to run:

- **Issue Updates File Present**: Runs `update-issues`
- **Pull Request Events**: Runs `copilot-tickets`
- **Scheduled Events**: Runs `close-duplicates` and `codeql-alerts`
- **Push Events**: Runs `copilot-tickets`

## Examples

### Example 1: Basic Issue Management

See
[`examples/workflows/issue-management-basic.yml`](../examples/workflows/issue-management-basic.yml)

### Example 2: Advanced Configuration

See
[`examples/workflows/issue-management-advanced.yml`](../examples/workflows/issue-management-advanced.yml)

### Example 3: Scheduled Maintenance

```yaml
name: Scheduled Issue Maintenance

on:
  schedule:
    - cron: '0 2 * * *' # Daily at 2 AM UTC

jobs:
  maintenance:
    uses: jdfalk/ghcommon/.github/workflows/reusable-unified-issue-management.yml@main
    with:
      operations: 'close-duplicates,codeql-alerts'
    secrets: inherit
```

### Example 4: Manual Operations

```yaml
name: Manual Issue Operations

on:
  workflow_dispatch:
    inputs:
      operation:
        type: choice
        options: [update-issues, copilot-tickets, close-duplicates, codeql-alerts]
        required: true
      dry_run:
        type: boolean
        default: true

jobs:
  manual-operation:
    uses: jdfalk/ghcommon/.github/workflows/reusable-unified-issue-management.yml@main
    with:
      operations: ${{ github.event.inputs.operation }}
      dry_run: ${{ github.event.inputs.dry_run == 'true' }}
    secrets: inherit
```

## Dual-GUID Duplicate Prevention

The workflow supports dual-GUID tracking for enhanced duplicate prevention and migration
compatibility:

### Modern Format (Dual-GUID)

```json
{
  "create": [
    {
      "title": "Bug: Memory leak in parser",
      "body": "Detailed description...",
      "guid": "a4d7a2e2-f643-466f-84c7-dcd476ec287f",
      "legacy_guid": "bug-memory-leak-2024-06-20-001"
    }
  ],
  "comment": [
    {
      "number": 123,
      "body": "Update: Fix is ready for testing",
      "guid": "8c237a09-3dbf-4bb6-b992-4674bb07c3f3",
      "legacy_guid": "status-update-2024-06-20-001"
    }
  ]
}
```

### Legacy Format (Still Supported)

```json
{
  "create": [
    {
      "title": "Bug: Memory leak in parser",
      "body": "Detailed description...",
      "guid": "bug-memory-leak-2024-06-20-001"
    }
  ]
}
```

### GUID Format Details

#### Primary GUID (`guid`)

- **Format**: UUID v4 (e.g., `a4d7a2e2-f643-466f-84c7-dcd476ec287f`)
- **Purpose**: Primary unique identifier for robust duplicate prevention
- **Generation**: Automatically generated UUID or manually specified
- **Recommendation**: Use auto-generated UUIDs for new entries

#### Legacy GUID (`legacy_guid`)

- **Format**: Descriptive string (e.g., `bug-memory-leak-2024-06-20-001`)
- **Purpose**: Backward compatibility and human-readable identification
- **Migration**: Automatically populated when migrating from legacy format
- **Optional**: Can be omitted for new entries

### Duplicate Prevention Logic

The workflow uses both GUIDs for comprehensive duplicate detection:

1. **Primary Check**: Compares `guid` field (UUID-based)
2. **Fallback Check**: Compares `legacy_guid` field if primary GUID not found
3. **Content Check**: Compares title and action type for additional safety
4. **Migration Support**: Handles files being migrated from legacy to dual-GUID format

### Dual-GUID Best Practices

1. **Use UUIDs for new entries**: Generate UUID v4 for the `guid` field
2. **Keep legacy GUIDs descriptive**: When migrating, preserve human-readable legacy GUIDs
3. **Migration strategy**: Use migration tools to convert legacy single-GUID to dual-GUID format
4. **Unique identifiers**: Never reuse either GUID across different operations
5. **Backward compatibility**: Support both formats during transition periods

### GUID Migration

For repositories transitioning from legacy GUID format:

```bash
# Use the smart migration script to convert to dual-GUID format
python scripts/smart-issue-migration.py migrate-dual-guid
```

This automatically:

- Converts existing `guid` to `legacy_guid`
- Generates new UUID for `guid` field
- Preserves all content and metadata
- Handles both pending and processed files

## Required Permissions

The workflow requires the following GitHub token permissions:

```yaml
permissions:
  issues: write # Create, update, close issues
  contents: write # Read repository files, create PRs
  pull-requests: write # Comment on PRs, manage reviews
  security-events: read # Access CodeQL alerts
  repository-projects: read # Access project information
```

These are automatically inherited when using `secrets: inherit`.

## Troubleshooting

### Common Issues

1. **"No operations were required"**
   - Check that your trigger events match your use case
   - Verify the `issue_updates.json` file exists and is valid JSON
   - Consider using explicit operations instead of "auto"

2. **"Permission denied" errors**
   - Ensure `secrets: inherit` is included in your workflow
   - Check that the GitHub token has required permissions
   - Verify the repository settings allow Actions to write to issues

3. **"File not found" errors**
   - Check the `issue_updates_file` parameter points to the correct path
   - Ensure the file is committed to the repository
   - Verify the file is in the correct branch

### Debug Mode

Enable debug logging by setting the workflow to dry-run mode:

```yaml
jobs:
  debug:
    uses: jdfalk/ghcommon/.github/workflows/reusable-unified-issue-management.yml@main
    with:
      dry_run: true
      operations: 'update-issues'
    secrets: inherit
```

## Migration from Individual Workflows

If you're currently using separate workflows for issue management:

1. **Backup existing workflows** before replacement
2. **Combine configuration** from multiple workflows into one call
3. **Update file paths** if your issue updates files are in different locations
4. **Test with dry-run** before going live

### Migration Checklist

- [ ] Backup existing `.github/workflows/` files
- [ ] Create new unified workflow file
- [ ] Update `issue_updates.json` format if needed
- [ ] Test with `dry_run: true`
- [ ] Remove old workflow files
- [ ] Update documentation and team processes

## Workflow Outcomes

### Automatic Pull Request Creation

The workflow automatically creates pull requests for file management operations:

#### Processed Files Archive PR

When distributed issue update files are processed, they are automatically moved to a `processed/`
subdirectory and a PR is created:

```
📦 Archive processed issue update files

Summary:
- Moved X processed issue update files from .github/issue-updates/ to .github/issue-updates/processed/
- Files processed by workflow run: 123456789
- Operation: update-issues
```

#### Legacy File Updates PR

When using legacy `issue_updates.json` files, a separate PR is created with permalinks:

```
🔗 Update issue tracking with permalinks

Summary:
- Updated issue_updates.json with permalinks to processed issues
- Allows tracking which issues have been processed
```

### Workflow Summary Reports

Each workflow run generates comprehensive summary reports including:

- **Operation Status**: Success/failure status for each operation
- **File Processing**: Count of processed files and archive status
- **Pull Request Links**: Direct links to created PRs for review
- **Timestamp and Context**: When and how the workflow was triggered

Example summary:

```
🎯 Operation Summary: update-issues

Status: ✅ Completed successfully
Event: push
Repository: owner/repo
Timestamp: 2025-06-21 12:00:00 UTC
Details: Processed issue updates from issue_updates.json and .github/issue-updates/
Processed Files: 3 files moved to archive

📋 Pull Request Summary:
📦 Processed Files PR: #42
   - URL: https://github.com/owner/repo/pull/42
   - Branch: archive-processed-files-123456789
```

## Sub-Issues Support

The workflow supports creating sub-issues (child issues) that are linked to parent issues:

### Creating a Sub-Issue

**Using the create script**:

```bash
# Using the create script
./scripts/create-issue-update.sh create "Sub-task: Implement authentication" \
  "This implements the authentication component" \
  "enhancement,sub-issue" \
  123  # Parent issue number
```

**JSON format**:

```json
{
  "action": "create",
  "title": "Sub-task: Implement authentication",
  "body": "This implements the authentication component",
  "labels": ["enhancement", "sub-issue"],
  "parent_issue": 123,
  "guid": "a4d7a2e2-f643-466f-84c7-dcd476ec287f",
  "legacy_guid": "sub-task-implement-authentication-2024-06-23"
}
```

### Sub-Issue Behavior

Sub-issues will:

- Automatically reference their parent issue in the body
- Include a "sub-issue" label
- Add a comment on the parent issue linking to the new sub-issue

### Example Sub-Issue Body

When a sub-issue is created, its body will be formatted like this:

```markdown
Sub-issue of #123

Parent issue: https://github.com/owner/repo/issues/123

---

This implements the authentication component
```

### Parent Issue Comment

The parent issue will receive a comment like:

```markdown
Created sub-issue #456:
[Sub-task: Implement authentication](https://github.com/owner/repo/issues/456)
```

## Support

For issues, questions, or contributions:

1. **Check existing issues** in the [ghcommon repository](https://github.com/jdfalk/ghcommon/issues)
2. **Create a new issue** with the `issue-management` label
3. **Include workflow logs** and configuration for debugging
4. **Provide minimal reproduction** steps when possible

## License

This workflow is part of the ghcommon repository and follows the same license terms.
