# file: .github/WORKFLOW_CONFIG_GUIDE.md

# version: 1.0.0

# guid: 8b9c0d1e-2f34-5678-9abc-def012345678

# Workflow Configuration System Guide

This document explains how the centralized workflow configuration system works, what the
`.github/workflow-config.yaml` file controls, and how it enables consistent CI/CD across all
repositories.

## Overview

The `workflow-config.yaml` file is the **central configuration hub** that controls:

- **Build matrices** for all supported languages (Go, Python, Node.js, Rust)
- **Repository synchronization** settings for cross-repo workflow deployment
- **Quality gates** and automation features
- **Platform and version support** across the ecosystem

## Key Principle: Repository-Specific Configuration

**CRITICAL**: The `workflow-config.yaml` file is **NOT synced** between repositories. Each
repository maintains its own version, allowing for:

- Custom language version requirements
- Repository-specific feature flags
- Different automation settings
- Tailored quality gates

## Configuration Structure

### 1. Build Configuration

```yaml
build:
  # Language version matrices
  go_versions:
    - '1.22'
    - '1.23'
    - '1.24'

  python_versions:
    - '3.11'
    - '3.12'
    - '3.13'

  node_versions:
    - '20'
    - '22'
    - '24'

  rust_versions: # Added in this update
    - '1.75'
    - '1.76'
    - '1.77'

  # Platform support
  platforms:
    - 'linux/amd64'
    - 'linux/arm64'

  operating_systems:
    - 'ubuntu-latest'
    - 'macos-latest'
    - 'windows-latest'

  # Feature flags
  enable_protobuf: true
  enable_docker: true
  enable_cross_compile: true
  enable_coverage: true
  enable_security_scan: true
```

**How it works:**

- The reusable matrix build workflow reads these versions to create build matrices
- Each repository can customize which language versions to support
- Feature flags control which build steps are executed

### 2. Repository Sync Configuration

```yaml
repositories:
  - name: 'subtitle-manager'
    url: 'https://github.com/jdfalk/subtitle-manager'
    sync_enabled: true
    custom_build_config:
      go_versions: ['1.23', '1.24'] # Override default versions
      enable_protobuf: true
      enable_docker: true

  - name: 'copilot-agent-util-rust'
    url: 'https://github.com/jdfalk/copilot-agent-util-rust'
    sync_enabled: true
    custom_build_config:
      rust_versions: ['1.75', '1.76', '1.77'] # Rust-specific config
      enable_protobuf: false
      enable_docker: true
```

**How it works:**

- The manager-sync-dispatcher workflow uses this configuration to deploy workflows
- Each target repository can override the default build settings
- Sync can be enabled/disabled per repository

### 3. Sync Control

```yaml
sync:
  auto_sync: true
  sync_on_push: true
  sync_on_schedule: true

  # Files that get synced to other repositories
  sync_paths:
    - '.github/workflows/matrix-build.yml'
    - '.github/workflows/ci.yml'
    - '.github/workflows/pr-automation.yml'
    - '.github/instructions/'
    - '.github/linters/'
    - '.pre-commit-config.yaml'

  # Files explicitly excluded from sync (repo-specific)
  exclude_files:
    - '.github/workflow-config.yaml' # Each repo has its own!
    - '.github/super-linter.env'
    - '.github/unified-automation-config.json'

  # Prevent infinite loops
  exclude_repos:
    - 'ghcommon' # Source repo doesn't sync to itself
```

**How it works:**

- Common workflows and configurations are synced across repositories
- Repository-specific configuration files are never synced
- This ensures consistency while preserving customization

### 4. Automation Features

```yaml
automation:
  issue_management:
    enabled: true
    auto_process: true
    migration_enabled: true

  dependency_updates:
    enabled: true
    auto_merge_minor: false
    schedule: '0 0 * * 1' # Weekly on Monday

  security_scanning:
    enabled: true
    auto_fix: false
    schedule: '0 0 * * 2' # Weekly on Tuesday
```

### 5. Quality Gates

```yaml
quality:
  coverage_threshold: 80
  security_scan_required: true
  lint_required: true
  tests_required: true

  # Branch protection rules
  branch_protection:
    required_status_checks:
      - 'Matrix Build System'
      - 'Lint Code'
      - 'Security Scan'

    require_code_review: true
    dismiss_stale_reviews: true
    require_review_from_codeowners: true
```

## Workflow Integration

### Reusable Matrix Build

The `reusable-matrix-build.yml` workflow can be called with custom parameters:

```yaml
# In any repository's workflow
uses: jdfalk/gcommon/.github/workflows/reusable-matrix-build.yml@main
with:
  go-versions: '["1.23", "1.24"]' # Override default
  rust-versions: '["1.76", "1.77"]' # Rust support added
  python-versions: '["3.12", "3.13"]' # Subset of versions
  enable-protobuf: true
  enable-docker: true
  skip-tests: false
```

### CI Workflow Integration

The main CI workflow automatically:

1. Detects project types (Go, Python, Node.js, Rust, Docker, Protobuf)
2. Reads language versions from workflow-config.yaml
3. Creates appropriate test matrices
4. Respects commit message overrides (e.g., `[skip tests]`)

### Commit Override System

New override keywords added:

- `[skip tests]`, `[no tests]`, `SKIP TESTS` - Skip all test execution
- `[skip validation]`, `[skip lint]` - Skip linting and validation
- `[skip ci]`, `[ci skip]` - Skip entire CI pipeline
- `[skip build]`, `[no build]` - Skip build steps

## Repository Customization Examples

### Go-Only Repository

```yaml
build:
  go_versions: ['1.23', '1.24']
  enable_protobuf: false
  enable_docker: true
  enable_coverage: true
```

### Rust-Only Repository

```yaml
build:
  rust_versions: ['1.75', '1.76', '1.77']
  enable_protobuf: false
  enable_docker: true
  enable_coverage: true
```

### Full-Stack Repository

```yaml
build:
  go_versions: ['1.23', '1.24']
  python_versions: ['3.12', '3.13']
  node_versions: ['20', '22']
  rust_versions: ['1.76', '1.77']
  enable_protobuf: true
  enable_docker: true
  enable_coverage: true
```

## Pre-commit Integration

New comprehensive pre-commit configuration:

- **Google-standard linter configs** for all languages
- **Automatic formatting** and fixing
- **Security scanning** with detect-secrets
- **Multi-language support** including new Rust support

Install and use:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## AI Rebasing System

The PR automation includes AI-powered conflict resolution:

- **Automatic detection** of merge conflicts
- **AI-assisted rebasing** using GPT models
- **Conflict resolution suggestions** in PR comments
- **Status tracking** with labels (`needs-rebase`)

Located in:

- `.github/workflows/pr-automation.yml` (main workflow)
- `.github/scripts/ai-rebase.sh` (rebasing script)
- `.github/prompts/ai-rebase-*.md` (AI prompts)

## Validation System

GitHub Actions validation is built into the CI:

- **VALIDATE_GITHUB_ACTIONS: true** in all linting steps
- **Workflow syntax checking** with yamllint
- **Security scanning** for workflow files
- **Best practices enforcement** via Super Linter

## Universal Compatibility

The workflows are designed to work in every repository:

- **Automatic project detection** (no manual configuration)
- **Language-agnostic approach** (works with any combination)
- **Graceful degradation** (missing languages are skipped)
- **Zero-configuration setup** (sensible defaults)

## Configuration Management

### Creating a New Repository Config

1. Copy from gcommon: `cp .github/workflow-config.yaml ../new-repo/.github/`
2. Customize language versions and features for your project
3. Update repository list in gcommon to enable sync
4. Deploy workflows: Run manager-sync-dispatcher workflow

### Updating Existing Configs

1. Modify your repository's `workflow-config.yaml`
2. Changes take effect on next workflow run
3. Common workflow updates come via sync from gcommon
4. Repository-specific settings remain unchanged

## Troubleshooting

### Common Issues

1. **Build matrix too large**: Reduce language version arrays
2. **Missing language support**: Check project detection in workflows
3. **Sync conflicts**: Ensure exclude_files includes repo-specific configs
4. **Override not working**: Check commit message format and spelling

### Debug Information

Enable debug mode:

```yaml
development:
  debug_mode: true
  verbose_logging: true
  dry_run_default: false
```

View workflow logs for:

- Project detection results
- Matrix generation output
- Override keyword detection
- Sync operation details

## Summary

The workflow configuration system provides:

- **Centralized control** with **repository flexibility**
- **Consistent CI/CD** across all projects
- **Language-specific optimizations** with universal compatibility
- **Advanced features** like AI rebasing and commit overrides
- **Comprehensive quality gates** with Google-standard linting

Each repository gets its own `workflow-config.yaml` to customize behavior while benefiting from
shared workflow infrastructure and automatic updates.
