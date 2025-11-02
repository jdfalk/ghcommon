<!-- file: .github/workflows/scripts/README.md -->
<!-- version: 1.1.0 -->
<!-- guid: 3f4a5b6c-7d8e-9f0a-1b2c-3d4e5f6a7b8c -->

# Workflow Scripts

This directory contains modular shell scripts extracted from the reusable release workflow for
better maintainability, testing, and linting.

## Scripts

### `detect-languages.sh`

Detects project languages and technologies (Go, Python, Rust, Frontend, Docker, Protobuf) and
generates build matrices.

**Environment Variables:**

- `SKIP_LANGUAGE_DETECTION`: Skip auto-detection and use manual inputs
- `GO_ENABLED`: Force enable Go builds
- `PYTHON_ENABLED`: Force enable Python builds
- `RUST_ENABLED`: Force enable Rust builds
- `FRONTEND_ENABLED`: Force enable Frontend builds
- `DOCKER_ENABLED`: Force enable Docker builds
- `PROTOBUF_ENABLED`: Force enable Protobuf builds

### `release-strategy.sh`

Determines release strategy based on branch name and manual inputs.

**Environment Variables:**

- `BRANCH_NAME`: Git branch name
- `INPUT_PRERELEASE`: Force prerelease flag
- `INPUT_DRAFT`: Force draft flag

**Strategy Logic:**

- `main` branch → Stable release (created as DRAFT for review)
- `develop` branch → Pre-release (published DIRECTLY)
- Feature branches → Pre-release (published DIRECTLY)

### `generate-version.sh`

Generates semantic version tags based on release type, branch, and strategy.

**Environment Variables:**

- `RELEASE_TYPE`: Version increment type (auto, major, minor, patch)
- `BRANCH_NAME`: Git branch name
- `AUTO_PRERELEASE`: Automatic prerelease flag
- `AUTO_DRAFT`: Automatic draft flag

**Version Logic:**

- `main` branch: `v1.2.3` (stable, created as draft)
- `develop` branch: `v1.3.0-dev.202510031234` (pre-release, published directly)
- Feature branches: `v1.2.4-alpha.202510031234` (pre-release, published directly)

### `generate-changelog.sh`

Generates changelog from git commits since the last tag.

**Environment Variables:**

- `BRANCH_NAME`: Git branch name
- `PRIMARY_LANGUAGE`: Primary project language
- `RELEASE_STRATEGY`: Release strategy (stable, prerelease, draft)
- `AUTO_PRERELEASE`: Automatic prerelease flag
- `AUTO_DRAFT`: Automatic draft flag

### `test-scripts.sh`

Comprehensive test suite for all workflow scripts to ensure they work correctly.

**Usage:**

```bash
./test-scripts.sh
```

## Script Testing

All scripts are thoroughly tested with the included test suite. The tests validate:

- Language detection for various project types
- Release strategy logic for different branches
- Version generation and semantic versioning
- Changelog generation from git history

## Benefits

### Maintainability

- ✅ **Modular Design**: Each script handles a specific responsibility
- ✅ **Version Control**: Each script has its own version tracking
- ✅ **Error Handling**: Consistent `set -euo pipefail` for robust error handling

### Test Coverage

- ✅ **Unit Tests**: Comprehensive test coverage for all scripts
- ✅ **Validation**: Test suite ensures scripts work in isolation
- ✅ **CI Integration**: Scripts can be tested independently

### Linting

- ✅ **ShellCheck**: Scripts can be linted with standard shell linting tools
- ✅ **Best Practices**: Following shell scripting best practices
- ✅ **Documentation**: Each script includes clear usage documentation

## Integration

These scripts are called from the main `reusable-release.yml` workflow with environment variables
set from the GitHub Actions context.

Example workflow integration:

```yaml
- name: Detect project languages and generate matrices
  id: detect
  env:
    SKIP_LANGUAGE_DETECTION: ${{ inputs.skip-language-detection }}
    GO_ENABLED: ${{ inputs.go-enabled }}
    PYTHON_ENABLED: ${{ inputs.python-enabled }}
    RUST_ENABLED: ${{ inputs.rust-enabled }}
    FRONTEND_ENABLED: ${{ inputs.frontend-enabled }}
    DOCKER_ENABLED: ${{ inputs.docker-enabled }}
    PROTOBUF_ENABLED: ${{ inputs.protobuf-enabled }}
  run: |
    ./.github/workflows/scripts/detect-languages.sh
```
