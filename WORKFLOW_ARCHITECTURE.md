# GitHub Actions Workflow Architecture

This document clarifies the intended structure and usage of the issue management
workflows in this repository.

## Canonical Workflow

**Use this workflow**:
`jdfalk/ghcommon/.github/workflows/reusable-unified-issue-management.yml@main`

This is the single, comprehensive, and actively maintained reusable workflow
that provides all issue management functionality.

## Documentation

**Primary documentation**:
[`docs/unified-issue-management.md`](docs/unified-issue-management.md)

This contains complete usage instructions, configuration options, examples, and
troubleshooting guidance.

## Examples

**Basic setup**:
[`examples/workflows/issue-management-basic.yml`](examples/workflows/issue-management-basic.yml)
**Advanced setup**:
[`examples/workflows/issue-management-advanced.yml`](examples/workflows/issue-management-advanced.yml)

Copy these examples to your repository's `.github/workflows/` directory and
customize as needed.

## Legacy Files

**Deprecated**: `.github/workflows/reusable-issue-management.yml`

This file is deprecated and will be removed in a future version. It has been
marked with deprecation notices and migration instructions.

## Migration Path

If you're currently using the legacy workflow:

1. **Replace the workflow call** in your repository from:

   ```yaml
   uses: jdfalk/ghcommon/.github/workflows/reusable-issue-management.yml@main
   ```

2. **To the unified workflow**:

   ```yaml
   uses: jdfalk/ghcommon/.github/workflows/reusable-unified-issue-management.yml@main
   ```

3. **Add required permissions** to your calling workflow:

   ```yaml
   permissions:
     contents: write # For creating commits and PRs
     issues: write # For creating and updating issues
     pull-requests: write # For creating PRs
     security-events: read # For reading CodeQL alerts (optional)
     repository-projects: read # For accessing project data (optional)
     actions: read # For workflow access
     checks: write # For workflow status
   ```

4. **Update input parameters** if needed (the unified workflow has more options)

5. **Test with dry-run mode** before going live:
   ```yaml
   with:
     dry_run: true
   ```

## Repository Settings

For automatic PR creation, ensure these repository settings:

- **Settings → Actions → General → Workflow permissions**:
  - ✅ Read and write permissions
  - ✅ Allow GitHub Actions to create and approve pull requests

## Quick Start

1. Copy
   [`examples/workflows/issue-management-basic.yml`](examples/workflows/issue-management-basic.yml)
   to `.github/workflows/issue-management.yml` in your repository
2. Commit the file
3. The workflow will automatically handle issue management based on file changes
   and events

## Support

- **Documentation**:
  [`docs/unified-issue-management.md`](docs/unified-issue-management.md)
- **Examples**: [`examples/workflows/`](examples/workflows/)
- **Issues**: Create an issue in this repository for support

## Summary

- ✅ **Use**: `reusable-unified-issue-management.yml` (canonical workflow)
- ✅ **Read**: `docs/unified-issue-management.md` (complete documentation)
- ✅ **Copy**: `examples/workflows/issue-management-basic.yml` (quick start)
- ❌ **Avoid**: `reusable-issue-management.yml` (deprecated)
