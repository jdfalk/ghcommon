# file: CHANGELOG.md

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed\n- Deprecated custom add-to-project workflows in favor of GitHub's built-in project automation.

### Added

- Added GitHub Projects automation script

### Changed\n- Enhanced AI rebase workflow to auto-merge and handle unknown mergeable states

### Added

- Common system prompt file for AI rebase workflow

### Added

- AI rebase workflow now uses file-based prompts to avoid long command lines

### Added

- Added reusable stale issue handler

### Added

- Added centralized CodeQL configuration

### Removed\n- Deprecated custom add-to-project workflows in favor of GitHub's built-in project automation.

### Added

- Added GitHub Projects automation script

### Changed\n- Enhanced AI rebase workflow to auto-merge and handle unknown mergeable states

### Added

- AI rebase workflow now uses file-based prompts to avoid long command lines

### Added

- Added reusable stale issue handler

### Added

- Added centralized CodeQL configuration

### Removed\n- Deprecated custom add-to-project workflows in favor of GitHub's built-in project automation.

### Added

- Added GitHub Projects automation script

### Changed\n- Enhanced AI rebase workflow to auto-merge and handle unknown mergeable states

### Added

- AI rebase workflow now uses file-based prompts to avoid long command lines

### Added

- Added reusable stale issue handler

### Removed\n- Deprecated custom add-to-project workflows in favor of GitHub's built-in project automation.

### Added

- Added GitHub Projects automation script

### Changed\n- Enhanced AI rebase workflow to auto-merge and handle unknown mergeable states

### Added

- AI rebase workflow now uses file-based prompts to avoid long command lines

### Removed\n- Deprecated custom add-to-project workflows in favor of GitHub's built-in project automation.

### Added

- Added GitHub Projects automation script

### Changed\n- Enhanced AI rebase workflow to auto-merge and handle unknown mergeable states

### Removed\n- Deprecated custom add-to-project workflows in favor of GitHub's built-in project automation.

### Added

- Added GitHub Projects automation script

### Added

- Added --ignore-errors option to doc_update_manager

### Removed\n- Deprecated custom add-to-project workflows in favor of GitHub's built-in project automation.

### Added

- Added GitHub Projects automation script

### Added

- Added GitHub Projects automation script

### Added

- Completed comprehensive documentation update system implementation across all repositories

### Added

- Enhanced documentation update system with comprehensive templates and workflow automation

### Added

- Initial reusable workflow repository setup
- Semantic versioning workflow with conventional commits support
- Multi-architecture container build workflow with Buildah
- Automatic release workflow with comprehensive artifact management
- **Unified Issue Management System**: Comprehensive reusable workflow for automated issue management
  - Advanced Python script (963 lines) with full GitHub API integration
  - Support for JSON-driven issue updates (create, update, comment, close, delete)
  - **Sub-issue support**: Parent-child issue linking with automatic labeling and comments
  - Copilot review comment ticket management
  - Automatic duplicate issue closure
  - CodeQL security alert ticket generation
  - GUID-based duplicate prevention system
  - Matrix-based parallel execution
  - Auto-detection of operations based on event context
  - Comprehensive documentation and migration guides
  - Example workflows for basic and advanced usage
- **Enhanced CI/CD with Dependency Submission**: Updated reusable CI workflow with automatic dependency submission
  - Go dependency submission using `actions/go-dependency-submission@v1`
  - Automatic detection of Go modules and dependencies
  - Integration with GitHub's dependency graph for security insights
  - Dependabot alerts and updates for vulnerable dependencies
  - Configurable dependency submission with `enable-dependency-submission` input
- **Automatic Pull Request Labeling**: New reusable workflow for intelligent PR labeling
  - File-based labeling using glob patterns (documentation, backend, frontend, tests, etc.)
  - Branch-based labeling using regex patterns (feature, bugfix, release, etc.)
  - Support for complex matching logic with v5.0.0 labeler action
  - Comprehensive default configuration with 15+ label categories
  - Label synchronization to remove labels when files are reverted
  - Security-conscious implementation using `pull_request_target` event
- Complete CI/CD pipeline template
- Container-only pipeline template
- Library/package release pipeline template
- Repository setup automation script
- Repository validation script
- Comprehensive security guidelines
- Copilot instructions for AI-assisted development
- GitHub issue and PR templates

### Changed

- **Updated reusable-ci.yml**: Enhanced with dependency submission capabilities
  - Added `enable-dependency-submission` input parameter
  - Integrated Go dependency submission for projects with Go modules
  - Improved permissions configuration for dependency graph access

### Files Added

- `.github/workflows/reusable-labeler.yml`: New reusable workflow for automatic PR labeling
- `.github/labeler.yml`: Comprehensive labeler configuration with 15+ label categories
- `.github/workflows/example-usage.yml`: Example demonstrating both CI and labeler workflows
- `docs/dependency-submission-and-labeling.md`: Complete documentation for new features

### Security

- SBOM generation for all container builds
- Vulnerability scanning with Grype
- Container image signing with Cosign
- Security attestation for releases
- Least privilege access patterns
- Secret management best practices

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
