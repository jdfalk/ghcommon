# Changelog

## [Unreleased]

### Fixed

#### December 26, 2025 - CI npm caching hardening

- Added directory creation step to prevent "paths not resolved" warnings in npm
  cache
- Expanded cache paths from `~/.npm` to `["~/.npm", "~/.cache/npm"]` for full
  coverage
- Included Node version in cache keys (`${{ inputs.node-version }}` for
  workflow-scripts; `${{ matrix.node-version }}` for frontend-ci)
- Improved restore-key fallback chain for better cache hit rates across Node
  version changes
- Resolves TODO-012 (npm cache path resolution) and strengthens CRITICAL-002
  (manual caching strategy)

## 2025-10-30

### Added

- Shared workflow foundation utilities (`workflow_common.py`) with config
  validation schema, feature flags, and supporting tests.
- Reusable CI workflow stack (helper, reusable workflow, feature-flagged caller)
  plus unit/integration coverage for change detection and matrix generation.
- Branch-aware release helper and reusable release workflow with GitHub Packages
  documentation, publish helper, release summary generator, and unit tests.
- GitHub Packages publishing helper (`publish_to_github_packages.py`), reusable
  workflow job integration, new documentation, and unit tests.
- GitHub Packages publishing script (`publish_to_github_packages.py`), workflow
  integration, and unit tests.
- Repository configuration updates enabling new CI and release systems,
  including registry preferences for future package publishing.

### Changed

- Modernized CI and release workflows to rely on repository feature flags
  instead of legacy configuration.
- Removed deprecated `.github/workflow-config.yaml` in favor of the new
  schema-driven configuration.
