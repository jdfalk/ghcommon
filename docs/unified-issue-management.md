<!-- file: docs/unified-issue-management.md -->

# Unified Issue Management Workflow

A comprehensive, reusable GitHub Actions workflow for automated issue management across repositories.

## Overview

The Unified Issue Management workflow provides centralized, automated issue management capabilities that can be shared across multiple repositories. It consolidates multiple issue management operations into a single, efficient workflow.

## Features

### Core Operations

- **Issue Updates**: Process issue updates from JSON files (create, update, comment, close, delete)
- **Copilot Tickets**: Manage tickets for GitHub Copilot review comments
- **Duplicate Management**: Automatically close duplicate issues by title
- **Security Alerts**: Generate tickets for CodeQL security alerts

### Advanced Features

- **GUID-based Duplicate Prevention**: Prevent duplicate operations with unique identifiers
- **Matrix-based Parallel Execution**: Run multiple operations efficiently
- **Auto-detection**: Automatically determine which operations to run based on context
- **Comprehensive Logging**: Detailed summaries and progress tracking
- **Flexible Configuration**: Extensive customization options

## Quick Start

### Basic Setup

1. **Copy the basic example** to `.github/workflows/issue-management.yml` in your repository:

```yaml
name: Issue Management

on:
  push:
    branches: [main]
    paths: [issue_updates.json]
  pull_request_review_comment:
    types: [created, edited, deleted]
  workflow_dispatch:

jobs:
  issue-management:
    uses: jdfalk/ghcommon/.github/workflows/unified-issue-management.yml@main
    secrets: inherit
```

1. **Commit the workflow** and it will automatically handle:

   - Processing `issue_updates.json` files when they're pushed
   - Managing Copilot review comment tickets
   - Manual execution via workflow dispatch

### Issue Updates Format

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
See [`examples/workflows/issue-management-basic.yml`](../examples/workflows/issue-management-basic.yml)

### Example 2: Advanced Configuration
See [`examples/workflows/issue-management-advanced.yml`](../examples/workflows/issue-management-advanced.yml)

### Example 3: Scheduled Maintenance
```yaml
name: Scheduled Issue Maintenance

on:
  schedule:
    - cron: "0 2 * * *"  # Daily at 2 AM UTC

jobs:
  maintenance:
    uses: jdfalk/ghcommon/.github/workflows/unified-issue-management.yml@main
    with:
      operations: "close-duplicates,codeql-alerts"
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
    uses: jdfalk/ghcommon/.github/workflows/unified-issue-management.yml@main
    with:
      operations: ${{ github.event.inputs.operation }}
      dry_run: ${{ github.event.inputs.dry_run == 'true' }}
    secrets: inherit
```

## GUID-Based Duplicate Prevention

The workflow supports GUID (Globally Unique Identifier) tracking to prevent duplicate operations:

```json
{
  "create": [
    {
      "title": "Bug: Memory leak in parser",
      "body": "Detailed description...",
      "guid": "bug-memory-leak-2024-06-20-001"
    }
  ],
  "comment": [
    {
      "number": 123,
      "body": "Update: Fix is ready for testing",
      "guid": "status-update-2024-06-20-001"
    }
  ]
}
```

### GUID Best Practices

1. **Use descriptive GUIDs**: Include operation type, date, and sequence
2. **Format consistently**: `{type}-{description}-{date}-{sequence}`
3. **Keep them unique**: Never reuse GUIDs across different operations

## Required Permissions

The workflow requires the following GitHub token permissions:

```yaml
permissions:
  issues: write          # Create, update, close issues
  contents: write        # Read repository files, create PRs
  pull-requests: write   # Comment on PRs, manage reviews
  security-events: read  # Access CodeQL alerts
  repository-projects: read  # Access project information
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
    uses: jdfalk/ghcommon/.github/workflows/unified-issue-management.yml@main
    with:
      dry_run: true
      operations: "update-issues"
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
When distributed issue update files are processed, they are automatically moved to a `processed/` subdirectory and a PR is created:

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

### File Management

#### Distributed Files
- Original files: `.github/issue-updates/*.json`
- Processed files: `.github/issue-updates/processed/*.json`
- Archive tracking: Automatic via PR creation

#### Legacy Files
- Original file: `issue_updates.json`
- Updated file: Contains permalinks to created issues
- Change tracking: Via separate PR with link updates

## Support

For issues, questions, or contributions:

1. **Check existing issues** in the [ghcommon repository](https://github.com/jdfalk/ghcommon/issues)
2. **Create a new issue** with the `issue-management` label
3. **Include workflow logs** and configuration for debugging
4. **Provide minimal reproduction** steps when possible

## License

This workflow is part of the ghcommon repository and follows the same license terms.
