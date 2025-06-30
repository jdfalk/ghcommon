# file: CHANGELOG.md

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Complete CI/CD pipeline template
- Container-only pipeline template
- Library/package release pipeline template
- Repository setup automation script
- Repository validation script
- Comprehensive security guidelines
- Copilot instructions for AI-assisted development
- GitHub issue and PR templates

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
