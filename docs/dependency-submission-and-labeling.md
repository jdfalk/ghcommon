<!-- file: docs/dependency-submission-and-labeling.md -->
<!-- version: 1.0.0 -->
<!-- guid: d4e5f6a7-b8c9-4a0d-1e2f-3a4b5c6d7e8f -->

# Dependency Submission and Pull Request Labeling

This document explains how to use the enhanced CI workflows with dependency submission and automatic pull request labeling.

## Dependency Submission

The reusable CI workflow now includes automatic dependency submission to GitHub's dependency graph, providing better security insights and Dependabot alerts.

### Features

- **Go Dependency Submission**: Automatically detects and submits Go module dependencies
- **Conditional Execution**: Only runs on main branch pushes to avoid duplicate submissions
- **Flexible Configuration**: Can be enabled/disabled with the `enable-dependency-submission` input

### Benefits

1. **Security Insights**: Dependencies appear in your repository's dependency graph
2. **Dependabot Alerts**: Get notified about vulnerable dependencies
3. **Dependabot Updates**: Automatic pull requests for dependency updates
4. **Compliance**: Better visibility into your software supply chain

### Usage

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: write
  actions: read
  checks: write
  security-events: write
  id-token: write
  # Additional permissions for dependency submission
  repository-projects: write
  packages: write
  attestations: write

jobs:
  ci:
    uses: jdfalk/ghcommon/.github/workflows/reusable-ci.yml@main
    with:
      enable-dependency-submission: true # Enable dependency submission
      go-version: "1.22"
      # ... other inputs
    secrets: inherit
```

### Requirements

- Must run on `main` branch (configurable in the workflow)
- Requires enhanced permissions for dependency submission:
  - `contents: read`
  - `id-token: write`
  - `security-events: write`
  - `repository-projects: write`
  - `pull-requests: write`
  - `packages: write`
  - `attestations: write`
- Go projects need `go.mod` file in repository root

### Authentication

The workflow supports enhanced authentication via Personal Access Token (PAT):

- **Default**: Uses `github.token` (standard GitHub Actions token)
- **Enhanced**: Uses `JF_CI_GH_PAT` repository secret if available
- **Fallback**: Automatically falls back to `github.token` if PAT is not configured

To use enhanced authentication:

1. Create a Personal Access Token with appropriate permissions
2. Add it as a repository secret named `JF_CI_GH_PAT`
3. The workflow will automatically detect and use it

Benefits of using PAT:

- Higher rate limits for GitHub API calls
- Enhanced permissions for dependency submission
- Better support for private repositories
- Reduced 403 permission errors
- Docker projects: Dockerfile will be built and scanned for dependencies

## Pull Request Labeling

The new reusable labeler workflow automatically applies labels to pull requests based on:

- Changed files (using glob patterns)
- Branch names (using regex patterns)
- Combination of both with complex logic

### Features

- **Automatic Labeling**: Labels are applied when PRs are opened or updated
- **File-based Labels**: Different labels for documentation, backend, frontend, etc.
- **Branch-based Labels**: Labels based on branch naming conventions
- **Label Synchronization**: Optional removal of labels when files are reverted
- **V5 Format**: Uses the latest labeler action with enhanced matching capabilities

### Default Label Categories

The included `.github/labeler.yml` provides labels for:

- **File Types**: `documentation`, `config`, `backend`, `frontend`, `python`, `tests`, `scripts`
- **Dependencies**: `dependencies`, `security`
- **Branch Types**: `feature`, `bugfix`, `release`, `maintenance`, `refactor`, `performance`
- **Special**: `breaking-change`, `release-ready`

### Usage

```yaml
jobs:
  labeler:
    uses: jdfalk/ghcommon/.github/workflows/reusable-labeler.yml@main
    with:
      configuration-path: ".github/labeler.yml" # Path to config file
      sync-labels: true # Remove labels when files revert
      dot: true # Include dotfiles in matching
```

### Configuration

The labeler uses `.github/labeler.yml` for configuration. Example:

```yaml
# Label PRs that modify documentation
documentation:
  - changed-files:
      - any-glob-to-any-file:
          - "**/*.md"
          - "docs/**/*"

# Label PRs from feature branches
feature:
  - head-branch:
      - "^feature"
      - "^feat"
      - "feature"

# Complex example: backend changes excluding docs
backend-only:
  - all:
      - changed-files:
          - any-glob-to-any-file: "**/*.go"
      - changed-files:
          - all-globs-to-all-files: "!**/*.md"
```

## Complete Workflow Example

Here's a complete workflow that uses both features:

```yaml
name: CI/CD with Dependency Submission and Labeling

on:
  pull_request_target:
    types: [opened, synchronize, reopened]
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  # Label pull requests (runs on pull_request_target for write access)
  label:
    if: github.event_name == 'pull_request_target'
    uses: jdfalk/ghcommon/.github/workflows/reusable-labeler.yml@main
    with:
      sync-labels: true

  # Run CI/CD pipeline (runs on pull_request/push for security)
  ci:
    if: github.event_name != 'pull_request_target'
    uses: jdfalk/ghcommon/.github/workflows/reusable-ci.yml@main
    with:
      enable-dependency-submission: true
      go-version: "1.22"
      run-lint: true
      run-test: true
```

## Security Considerations

### Dependency Submission

- Only runs on main branch to avoid unauthorized submissions
- Uses minimal required permissions (`contents: read`, `id-token: write`)
- Scans only the checked-out code, not external sources

### Pull Request Labeling

- Uses `pull_request_target` for write access to labels
- Runs labeler code from the base branch (more secure than PR branch)
- Only modifies labels, cannot access repository secrets
- Recommended to use trusted labeler configurations

## Troubleshooting

### Dependency Submission Issues

1. **No Dependencies Detected**

   - Ensure `go.mod` exists in repository root
   - Check that Go files are present in the repository
   - Verify the workflow runs on the main branch

2. **Permission Errors**
   - Ensure `id-token: write` permission is granted
   - Check that the repository has dependency submission enabled

### Labeling Issues

1. **Labels Not Applied**

   - Verify the labeler configuration syntax
   - Check that the labels exist in the repository
   - Ensure the workflow has `pull-requests: write` permission

2. **Wrong Labels Applied**
   - Review the glob patterns in `.github/labeler.yml`
   - Test patterns using tools like [globster](https://globster.xyz/)
   - Check for conflicting label rules

## Migration from V4 Labeler

If upgrading from labeler v4, note these breaking changes:

1. **Configuration Format**: New nested structure with `changed-files`, `base-branch`, `head-branch`
2. **Default Dot Behavior**: Now includes dotfiles by default (`dot: true`)
3. **Sync Labels**: Input name is now read correctly

Example migration:

```yaml
# V4 format (old)
documentation: 'docs/**'

# V5 format (new)
documentation:
  - changed-files:
    - any-glob-to-any-file: 'docs/**'
```

## Additional Resources

- [GitHub Dependency Submission API](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/using-the-dependency-submission-api)
- [Actions Labeler V5 Documentation](https://github.com/actions/labeler)
- [Glob Pattern Testing](https://globster.xyz/)
- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
