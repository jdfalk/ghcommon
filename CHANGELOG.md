# file: CHANGELOG.md

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added\n\n- Added reusable CodeQL workflow with unique caching keys

### Changed

- **BREAKING**: Removed protobuf definitions; moved to gcommon repository

### Added

- Implemented cache service protobuf definitions

### Added

- Added unified automation workflow for manual invocation
- Added initial queue module protobuf definitions
- Added logging protobuf definitions
- Added comprehensive manual unified automation workflow options
- Added unified automation orchestrator workflow with extensive customization options
- Common system prompt file for AI rebase workflow
- AI rebase workflow now uses file-based prompts to avoid long command lines
- Added manual workflow_dispatch trigger for unified automation
- Added reusable stale issue handler
- Added centralized CodeQL configuration
- Added GitHub Projects automation script

### Changed

- Enhanced AI rebase workflow to auto-merge and handle unknown mergeable states
- Rebase launcher now auto-commits AI conflict resolutions and force pushes

### Fixed

- Fix syntax error in reusable docs update workflow
- Fixed YAML Prettier configuration to avoid super-linter error
- Enabled YAML Prettier validation for super linter

### Removed

- Deprecated custom add-to-project workflows in favor of GitHub's built-in project automation

## [1.0.0] - 2025-06-14

### Added

- Initial release of GitHub Common Workflows repository
- Three core reusable workflows:
  - Semantic versioning with conventional commits
  - Multi-architecture container builds with security features
  - Automated releases with artifact management
- Template workflows for different project types
- Setup and validation automation scripts
- Comprehensive documentation and security guidelines
