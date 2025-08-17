<!-- file: .github/workflows/README.md -->
<!-- version: 1.0.0 -->
<!-- guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d -->

<!-- file: .github/workflows/README.md -->
<!-- version: 1.0.0 -->
<!-- guid: f6a7b8c9-d0e1-2f3a-4b5c-6d7e8f9a0b1c -->
<!-- DO NOT EDIT: This file is managed centrally in ghcommon repository -->
<!-- To update: Edit the version in jdfalk/ghcommon and it will be synced to all repos -->

# Release Workflow System

This repository implements a plugin-like modular release workflow system that automatically detects the programming language and runs the appropriate release workflow.

## Architecture Overview

The system consists of:

1. **Main Coordinator** (`release.yml`) - Detects language and triggers appropriate sub-workflow
2. **Language-Specific Workflows** - Handle releases for specific languages
3. **Semantic Versioning** - Uses conventional commits for automated versioning

## How It Works

### 1. Language Detection

The main `release.yml` workflow automatically detects the project type by checking for key files:

- **Rust**: `Cargo.toml`
- **Go**: `go.mod`
- **Python**: `pyproject.toml`, `setup.py`, or `requirements.txt`
- **JavaScript**: `package.json` (without TypeScript config)
- **TypeScript**: `package.json` + `tsconfig.json`

### 2. Workflow Execution

Based on the detected language, the coordinator calls the appropriate sub-workflow:

- `release-rust.yml` - Multi-platform Rust builds (6 targets)
- `release-go.yml` - Cross-platform Go builds (5 platforms)
- `release-python.yml` - Python package with PyPI publishing
- `release-javascript.yml` - npm package publishing
- `release-typescript.yml` - TypeScript compilation and npm publishing

## Usage

### Automated Releases (Recommended)

1. Use conventional commit messages:

   ```bash
   feat: add new feature (triggers minor release)
   fix: bug fix (triggers patch release)
   feat!: breaking change (triggers major release)
   ```

2. Push to main branch or merge PR - release happens automatically

### Manual Releases

Trigger manually via GitHub Actions UI with options:
- Release type: `major`, `minor`, `patch`, or `auto`
- Prerelease: `true`/`false`
- Draft: `true`/`false`

## Language-Specific Features

### Rust (`release-rust.yml`)
- Multi-platform builds: Linux (x86_64, aarch64), macOS (x86_64, aarch64), Windows (x86_64, aarch64)
- Cross-compilation with musl and gnu toolchains
- Semantic versioning via Cargo.toml updates
- GitHub releases with pre-built binaries

### Go (`release-go.yml`)
- Cross-compilation for 5 platforms: Linux, macOS, Windows (x86_64, aarch64)
- GoReleaser-style builds without external dependencies
- Module version management
- Lightweight binary releases

### Python (`release-python.yml`)
- Automated wheel building
- PyPI publishing (requires `PYPI_API_TOKEN` secret)
- Support for both `pyproject.toml` and `setup.py`
- Version updates in multiple files

### JavaScript (`release-javascript.yml`)
- npm package publishing (requires `NPM_TOKEN` secret)
- Semantic versioning via package.json
- Automated changelog generation
- Package tarball creation

### TypeScript (`release-typescript.yml`)
- TypeScript compilation and type checking
- npm publishing with built artifacts
- Supports both library and application projects
- Automated dependency and build management

## Setup Requirements

### Secrets Configuration

Each language workflow may require specific secrets:

- **Python**: `PYPI_API_TOKEN` for PyPI publishing
- **JavaScript/TypeScript**: `NPM_TOKEN` for npm publishing
- **All**: `GITHUB_TOKEN` (automatically provided)

### Repository Configuration

1. Enable GitHub Actions
2. Set up branch protection for `main`
3. Configure secrets as needed
4. Ensure conventional commit format

## Benefits

1. **Language Agnostic**: Automatically adapts to any supported language
2. **Zero Configuration**: Works out of the box with sensible defaults
3. **Portable**: Can be copied to any repository without modification
4. **Consistent**: Standardized release process across all projects
5. **Flexible**: Supports both automated and manual releases
6. **Comprehensive**: Handles building, testing, versioning, and publishing

## Conventional Commit Format

The system uses conventional commits for automated versioning:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types:
- `feat`: New feature (minor version bump)
- `fix`: Bug fix (patch version bump)
- `perf`: Performance improvement (patch version bump)
- `refactor`: Code refactoring (patch version bump)
- `docs`: Documentation only (no version bump)
- `style`: Code style changes (no version bump)
- `test`: Test changes (no version bump)
- `chore`: Maintenance (no version bump)
- `ci`: CI changes (no version bump)
- `build`: Build changes (no version bump)
- `revert`: Reverting changes (patch version bump)

### Breaking Changes:
Add `!` after type or include `BREAKING CHANGE:` in footer for major version bump:
```
feat!: remove deprecated API
```

## Troubleshooting

### Common Issues:

1. **No release triggered**: Check commit message format
2. **Build failures**: Verify language-specific requirements
3. **Publishing failures**: Check required secrets are configured
4. **Version conflicts**: Ensure clean working directory

### Debug Information:

Each workflow provides detailed logs for:
- Language detection results
- Version calculation
- Build process
- Publishing steps

## Migration from Reusable Workflows

This system replaces the previous reusable workflow approach that caused `GITHUB_TOKEN` secret conflicts. The new architecture:

1. Eliminates secret passing issues
2. Provides better debugging capabilities
3. Supports more complex language-specific logic
4. Maintains consistency across repositories
