<!-- file: docs/label-synchronization.md -->
<!-- version: 1.0.0 -->
<!-- guid: 4a2a4a66-7b30-4256-b4ff-9a9551884ebe -->

# Label Synchronization Workflow

A comprehensive GitHub Actions workflow for standardizing labels across multiple repositories from a
central configuration.

## Overview

The Label Synchronization workflow provides centralized label management that automatically syncs a
standard set of labels from the ghcommon repository to target repositories. This ensures consistency
across all your projects.

## Workflow Architecture

- **Canonical Workflow**: `jdfalk/ghcommon/.github/workflows/reusable-label-sync.yml@main`
- **Configuration**: `labels.json` (JSON array of label definitions)
- **Repository List**: `repositories.txt` (optional file listing target repositories)
- **Examples**: `/examples/workflows/label-sync-basic.yml` and
  `/examples/workflows/label-sync-advanced.yml`

## Quick Start

### Basic Setup

1. **Copy the basic example** to `.github/workflows/label-sync.yml` in your repository:

```yaml
name: Sync Labels from ghcommon

on:
  workflow_dispatch:
  schedule:
    - cron: '0 3 1 * *' # Monthly

permissions:
  contents: read

jobs:
  sync-labels:
    uses: jdfalk/ghcommon/.github/workflows/reusable-label-sync.yml@main
    with:
      config-file: 'labels.json'
      repositories: ${{ github.repository }}
      source-repo: 'jdfalk/ghcommon'
    secrets: inherit
```

2. **Commit the workflow** and it will automatically:
   - Sync labels monthly from ghcommon's configuration
   - Create or update labels as needed
   - Skip labels that are already up to date

### Label Configuration Format

The `labels.json` file defines the standard labels in JSON format:

```json
[
  {
    "name": "bug",
    "color": "d73a49",
    "description": "Something isn't working"
  },
  {
    "name": "enhancement",
    "color": "a2eeef",
    "description": "New feature or request"
  }
]
```

**Required fields:**

- `name`: Label name (string)
- `color`: Hex color code without # (string)

**Optional fields:**

- `description`: Label description (string, defaults to empty)

## Configuration Options

### Input Parameters

| Parameter             | Type    | Default       | Description                                |
| --------------------- | ------- | ------------- | ------------------------------------------ |
| `config-file`         | string  | `labels.json` | Path to labels configuration file          |
| `repositories`        | string  | -             | Comma-separated list of repos (owner/name) |
| `repositories-file`   | string  | -             | File containing repository list            |
| `delete-extra-labels` | boolean | `false`       | Delete labels not in configuration         |
| `dry-run`             | boolean | `false`       | Show changes without applying them         |
| `source-repo`         | string  | current repo  | Repository to fetch config from            |
| `source-branch`       | string  | `main`        | Branch to fetch config from                |

### Repository List Options

You can specify target repositories in three ways:

1. **Inline list** via `repositories` parameter:

   ```yaml
   repositories: 'owner/repo1,owner/repo2,owner/repo3'
   ```

2. **File-based list** via `repositories-file` parameter:

   ```yaml
   repositories-file: 'repositories.txt'
   ```

3. **Combination** of both (they will be merged):
   ```yaml
   repositories: 'owner/repo1'
   repositories-file: 'more-repos.txt'
   ```

### Repository File Format

Create a text file with one repository per line:

```text
# Repository list for label sync
# Lines starting with # are comments

owner/repository1
owner/repository2
org/project-name
```

## Examples

### Example 1: Basic Monthly Sync

Sync labels to current repository monthly:

```yaml
name: Monthly Label Sync

on:
  schedule:
    - cron: '0 2 1 * *' # 1st of month at 2 AM UTC

jobs:
  sync:
    uses: jdfalk/ghcommon/.github/workflows/reusable-label-sync.yml@main
    with:
      repositories: ${{ github.repository }}
      source-repo: 'jdfalk/ghcommon'
    secrets: inherit
```

### Example 2: Multiple Repositories with Custom Config

Sync to multiple repositories using local configuration:

```yaml
name: Organization Label Sync

on:
  workflow_dispatch:
  push:
    paths: ['labels.json']

jobs:
  sync:
    uses: jdfalk/ghcommon/.github/workflows/reusable-label-sync.yml@main
    with:
      config-file: 'labels.json'
      repositories-file: 'target-repos.txt'
      delete-extra-labels: true
    secrets: inherit
```

### Example 3: Dry Run for Testing

Test changes without applying them:

```yaml
name: Test Label Changes

on:
  pull_request:
    paths: ['labels.json']

jobs:
  test-sync:
    uses: jdfalk/ghcommon/.github/workflows/reusable-label-sync.yml@main
    with:
      repositories: ${{ github.repository }}
      dry-run: true
    secrets: inherit
```

## Required Permissions

The workflow requires these permissions:

```yaml
permissions:
  contents: read # To read configuration files
  issues: read # For API access validation
  pull-requests: read # For API access validation
```

**Note**: The `GITHUB_TOKEN` automatically has sufficient permissions to manage labels in
repositories where the workflow runs.

## Operational Modes

### Safe Mode (Default)

- Creates missing labels
- Updates existing labels with different colors/descriptions
- **Never deletes** existing labels
- Recommended for most use cases

### Cleanup Mode

Add `delete-extra-labels: true` to:

- Remove labels not defined in configuration
- Ensures exact match with configuration
- **Use with caution** - will delete custom labels

### Dry Run Mode

Add `dry-run: true` to:

- Show what changes would be made
- No actual modifications
- Perfect for testing configuration changes

## Troubleshooting

### Common Issues

**Configuration file not found:**

```
Error: Configuration file 'labels.json' not found
```

- Ensure the file exists in the specified path
- Check file name spelling and case sensitivity

**Invalid JSON format:**

```
Expecting ',' delimiter: line 5 column 10 (char 123)
```

- Validate JSON syntax using a JSON validator
- Check for missing commas, quotes, or brackets

**Repository access denied:**

```
Error: Repository 'owner/repo' not found or not accessible
```

- Verify repository names are correct (owner/name format)
- Ensure GITHUB_TOKEN has access to target repositories
- Check if repositories are private and accessible

**API rate limiting:**

```
Error: API rate limit exceeded
```

- Wait for rate limit reset (usually 1 hour)
- Reduce number of repositories processed simultaneously
- Consider using GitHub App tokens for higher limits

### Debugging Tips

1. **Use dry-run mode** to test configuration changes
2. **Check workflow logs** for detailed operation results
3. **Validate JSON** before committing configuration changes
4. **Start with small repository lists** when testing
5. **Use workflow_dispatch** for manual testing

## Label Configuration Best Practices

### Standard Label Set

The default configuration includes these categories:

- **Issue Types**: `bug`, `enhancement`, `documentation`, `question`
- **Priorities**: `priority-high`, `priority-medium`, `priority-low`
- **Special**: `good first issue`, `help wanted`, `duplicate`, `wontfix`
- **Technical**: `security`, `breaking-change`, `dependencies`, `ci/cd`
- **Process**: `testing`, `refactoring`, `performance`, `ui/ux`

### Color Conventions

- **Red tones** (`d73a49`, `b60205`): Bugs, high priority, security
- **Green tones** (`0e8a16`, `008672`): Enhancements, low priority
- **Blue tones** (`0075ca`, `0366d6`): Documentation, dependencies
- **Purple tones** (`7057ff`, `d876e3`): Special labels, questions
- **Orange tones** (`fbca04`, `ff9500`): Medium priority, performance
- **Gray tones** (`cfd3d7`, `ffffff`): Meta labels, duplicates

### Naming Conventions

- Use **lowercase** with hyphens for multi-word labels
- Keep names **concise** but descriptive
- Use **consistent prefixes** for categories (e.g., `priority-*`)
- Avoid **special characters** that might cause URL encoding issues

## Integration with Issue Management

The label sync workflow integrates well with the existing issue management system:

```yaml
# Combined workflow example
jobs:
  sync-labels:
    uses: jdfalk/ghcommon/.github/workflows/reusable-label-sync.yml@main
    with:
      repositories: ${{ github.repository }}
    secrets: inherit

  process-issues:
    needs: sync-labels
    uses: jdfalk/ghcommon/.github/workflows/reusable-unified-issue-management.yml@main
    secrets: inherit
```

## Migration from Manual Label Management

### Step 1: Audit Current Labels

Export existing labels to compare with standard configuration:

```bash
# List current labels
gh label list --repo owner/repo --json name,color,description
```

### Step 2: Backup Important Custom Labels

Save any custom labels you want to preserve:

```bash
# Export to file
gh label list --repo owner/repo > current-labels.txt
```

### Step 3: Test with Dry Run

```yaml
jobs:
  test-sync:
    uses: jdfalk/ghcommon/.github/workflows/reusable-label-sync.yml@main
    with:
      repositories: 'owner/repo'
      dry-run: true
    secrets: inherit
```

### Step 4: Gradual Migration

Start with safe mode, then optionally enable cleanup:

```yaml
# Phase 1: Safe sync (no deletions)
delete-extra-labels: false

# Phase 2: Full sync (after review)
delete-extra-labels: true
```

## Support

For issues, questions, or contributions:

1. **Check existing issues** in the [ghcommon repository](https://github.com/jdfalk/ghcommon/issues)
2. **Create a new issue** with the `label-sync` label
3. **Include workflow logs** and configuration for debugging
4. **Provide minimal reproduction** steps when possible

## License

This workflow is part of the ghcommon repository and follows the same license terms.
