# Changelog

## 2025-10-30

### Added

- Shared workflow foundation utilities (`workflow_common.py`) with config validation schema, feature
  flags, and supporting tests.
- Reusable CI workflow stack (helper, reusable workflow, feature-flagged caller) plus
  unit/integration coverage for change detection and matrix generation.
- Branch-aware release helper and reusable release workflow with GitHub Packages documentation,
  publish helper, release summary generator, and unit tests.
- GitHub Packages publishing helper (`publish_to_github_packages.py`), reusable workflow job
  integration, new documentation, and unit tests.
- GitHub Packages publishing script (`publish_to_github_packages.py`), workflow integration, and
  unit tests.
- Repository configuration updates enabling new CI and release systems, including registry
  preferences for future package publishing.

### Changed

- Modernized CI and release workflows to rely on repository feature flags instead of legacy
  configuration.
- Removed deprecated `.github/workflow-config.yaml` in favor of the new schema-driven configuration.
