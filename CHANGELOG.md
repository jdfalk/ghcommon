# file: CHANGELOG.md

## Table of Contents

- [file: CHANGELOG.md](#file-changelog-md)
- [Changelog](#changelog)
  - [[Unreleased]](#-unreleased)
    - [Added](#added)
    - [Fixed](#fixed)
    - [Added](#added)
    - [Changed](#changed)
    - [Fixed](#fixed)
  - [[1.1.0] - 2025-08-02](#-1-1-0-2025-08-02)
    - [Added](#added)
    - [Changed](#changed)
    - [Fixed](#fixed)
    - [Removed](#removed)
  - [[1.0.0] - 2025-06-14](#-1-0-0-2025-06-14)
    - [Added](#added)


# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Add script to submit codex jobs

### Fixed

- Ensure Super Linter auto-fixes issues, pushes commits, runs before other jobs,
  and validates entire codebase

### Added

- Added concise output mode to Super Linter workflow (default behavior)
- Added `show-detailed-summary` parameter to control Super Linter verbosity
- Added focused GitHub Job Summary for Super Linter results
- Added improved PR comment formatting with actionable issue details
- Added example workflows demonstrating both concise and detailed modes
- Added reusable CodeQL workflow with unique caching keys

### Changed

- **BREAKING**: Super Linter now defaults to concise output mode (shows only
  issues/changes)
- Improved Super Linter error extraction and presentation
- Restructured Super Linter PR comments to be more actionable
- Updated Super Linter configuration to reduce verbose processing logs
- Minimized configuration details in summaries (moved to collapsible sections)
- **BREAKING**: Removed protobuf definitions; moved to gcommon repository

### Fixed

- Fixed verbose Super Linter output showing all processed files instead of just
  issues
- Fixed poor formatting in Super Linter summaries and comments
- Fixed unhelpful configuration dumps in final summaries

## [1.1.0] - 2025-08-02

### Added

- Implemented cache service protobuf definitions
- Added unified automation workflow for manual invocation
- Added initial queue module protobuf definitions
- Added logging protobuf definitions
- Added comprehensive manual unified automation workflow options
- Added unified automation orchestrator workflow with extensive customization
  options
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

- Deprecated custom add-to-project workflows in favor of GitHub's built-in
  project automation

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
