# file: .github/workflows/scripts/README.md
# version: 1.0.0
# guid: 3f4a5b6c-7d8e-9f0a-1b2c-3d4e5f6a7b8c

# Workflow Scripts

This directory contains modular shell scripts extracted from the reusable release workflow for better maintainability, testing, and linting.

## Scripts

### `detect-languages.sh`
Detects project languages and technologies (Go, Python, Rust, Frontend, Docker, Protobuf) and generates build matrices.

**Usage:**
```bash
./detect-languages.sh skip_detection go_enabled python_enabled rust_enabled frontend_enabled docker_enabled protobuf_enabled
```

**Arguments:**
- `skip_detection`: Skip auto-detection and use manual inputs
- `go_enabled`: Force enable Go builds
- `python_enabled`: Force enable Python builds
- `rust_enabled`: Force enable Rust builds
- `frontend_enabled`: Force enable Frontend builds
- `docker_enabled`: Force enable Docker builds
- `protobuf_enabled`: Force enable Protobuf builds

### `release-strategy.sh`
Determines release strategy based on branch name and manual inputs.

**Usage:**
```bash
./release-strategy.sh branch_name input_prerelease input_draft
```

**Strategy Logic:**
- `main` branch → Stable release
- `develop` branch → Pre-release
- Feature branches → Draft release

### `generate-version.sh`
Generates semantic version tags based on release type, branch, and strategy.

**Usage:**
```bash
./generate-version.sh release_type branch_name auto_prerelease auto_draft
```

**Version Logic:**
- `main` branch: `v1.2.3` (stable)
- `develop` branch: `v1.3.0-dev.202510031234` (pre-release)
- Feature branches: `v1.2.4-dev-feature-name.202510031234` (draft)

### `generate-changelog.sh`
Generates changelog from git commits since the last tag.

**Usage:**
```bash
./generate-changelog.sh branch_name primary_language release_strategy auto_prerelease auto_draft
```

### `test-scripts.sh`
Comprehensive test suite for all workflow scripts to ensure they work correctly.

**Usage:**
```bash
./test-scripts.sh
```

## Testing

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

### Testing
- ✅ **Unit Tests**: Comprehensive test coverage for all scripts
- ✅ **Validation**: Test suite ensures scripts work in isolation
- ✅ **CI Integration**: Scripts can be tested independently

### Linting
- ✅ **ShellCheck**: Scripts can be linted with standard shell linting tools
- ✅ **Best Practices**: Following shell scripting best practices
- ✅ **Documentation**: Each script includes clear usage documentation

## Integration

These scripts are called from the main `reusable-release.yml` workflow with appropriate parameters passed from the GitHub Actions context.

Example workflow integration:
```yaml
- name: Detect project languages and generate matrices
  id: detect
  run: |
    ./.github/workflows/scripts/detect-languages.sh \
      "${{ inputs.skip-language-detection }}" \
      "${{ inputs.go-enabled }}" \
      "${{ inputs.python-enabled }}" \
      "${{ inputs.rust-enabled }}" \
      "${{ inputs.frontend-enabled }}" \
      "${{ inputs.docker-enabled }}" \
      "${{ inputs.protobuf-enabled }}"
```
