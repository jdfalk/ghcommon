# Changelog

## [Unreleased]

### Security

#### January 2, 2026 - Action Security Hardening

- Pinned all external GitHub Actions to full-length commit SHAs across 9 action
  repositories
- Updated action format to `owner/action@FULL_SHA # vX.Y.Z` for security +
  dependabot compatibility
- Audited and fetched latest versions for 15 external action dependencies:
  - GitHub official actions: checkout v6.0.1, setup-go v5.6.0, setup-node
    v6.1.0, setup-python v6.1.0, upload-artifact v6.0.0
  - Third-party actions: yamllint v3.1.1, gh-release v2.5.0, rust-toolchain
    v1.15.2, goreleaser v6.4.0, buf-setup v1.50.0
  - Docker actions: login v3.6.0, setup-buildx v3.12.0, setup-qemu v3.7.0,
    build-push v6.18.0, metadata v5.10.0
- Updated 9 repos with pinned hashes: get-frontend-config-action,
  auto-module-tagging-action, load-config-action, release-docker-action,
  release-frontend-action, release-go-action, release-protobuf-action,
  release-python-action, release-rust-action
- Enabled "require actions to be pinned to full-length commit SHA" repository
  setting on 17 action repos via GitHub API
- Deployed pre-commit hooks configuration (.pre-commit-config.yaml) to all 17
  action repos
- Deployed linter configurations (.markdownlint.json, .prettierrc.json,
  ruff.toml) to all 17 action repos
- All changes committed and pushed individually per repository
- Ensures consistent code quality enforcement and security best practices across
  all action repositories

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
