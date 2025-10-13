<!-- file: docs/SUPER_LINTER_STRATEGY.md -->
<!-- version: 1.0.0 -->
<!-- guid: f7a8b9c0-d1e2-3f4a-5b6c-7d8e9f0a1b2c -->

# Super Linter Configuration Strategy

This document explains ghcommon's Super Linter configuration approach, design decisions, and best
practices for maintaining linter configurations across repositories.

## Table of Contents

- [Configuration Philosophy](#configuration-philosophy)
- [Root Directory Pattern](#root-directory-pattern)
- [Configuration Variables](#configuration-variables)
- [Never Use Symlinks](#never-use-symlinks)
- [Multi-Language Support](#multi-language-support)
- [Configuration File Structure](#configuration-file-structure)
- [Versioning and Maintenance](#versioning-and-maintenance)
- [Related Documentation](#related-documentation)

## Configuration Philosophy

ghcommon follows these core principles for Super Linter configuration:

1. **Explicit is better than implicit**: Always set `*_CONFIG_FILE` variables explicitly
2. **Root directory pattern**: Store all linter configs in repository root
3. **Never use symlinks**: Symlinks cause path resolution issues in Docker containers
4. **Version everything**: All configuration files must have version headers
5. **Document thoroughly**: Configuration decisions must be documented

## Root Directory Pattern

All 15 linter configuration files in ghcommon are stored in the repository root directory, not in
`.github/linters/`:

```bash
# ✅ CORRECT: Root directory
.eslintrc.yml
.markdownlint.json
.yaml-lint.yml
.yamllint
.pylintrc
ruff.toml
.python-black
clippy.toml
rustfmt.toml
.golangci.yml
.prettierrc
.prettierignore
.commitlintrc.js
super-linter-ci.env
super-linter-pr.env

# ❌ INCORRECT: .github/linters/ directory
.github/linters/.eslintrc.yml    # Don't do this
.github/linters/.markdownlint.json
```

### Why Root Directory?

1. **Simplicity**: Shorter paths, easier to find files
2. **Tool compatibility**: Many linters naturally look for configs in root
3. **No Docker path issues**: Root directory avoids Super Linter container path resolution problems
4. **Industry standard**: Most repositories follow this pattern
5. **Maintenance**: Easier to update and version control

## Configuration Variables

Super Linter supports two types of configuration variables:

### `*_CONFIG_FILE` Variables (Preferred)

These variables specify the **exact path** to a configuration file:

```bash
# ✅ CORRECT: Explicit CONFIG_FILE variables
JAVASCRIPT_ES_CONFIG_FILE=.eslintrc.yml
MARKDOWN_CONFIG_FILE=.markdownlint.json
YAML_CONFIG_FILE=.yaml-lint.yml
PYTHON_BLACK_CONFIG_FILE=.python-black
PYTHON_PYLINT_CONFIG_FILE=.pylintrc
RUST_CLIPPY_CONFIG_FILE=clippy.toml
```

**Best Practices:**

- Always set these explicitly, never rely on defaults
- Use root-relative paths (no leading `/` or `./`)
- Point to actual files, not symlinks
- Keep paths consistent across CI and PR configs

### `*_LINTER_RULES` Variables (Avoid)

These variables are **deprecated** and cause path resolution issues:

```bash
# ❌ AVOID: LINTER_RULES variables
JAVASCRIPT_ES_LINTER_RULES=.github/linters/.eslintrc.yml  # Can cause issues
MARKDOWN_LINTER_RULES=.markdownlint.json                  # Use CONFIG_FILE instead
```

**Why Avoid `*_LINTER_RULES`?**

- Docker container path resolution issues
- Inconsistent behavior with symlinks
- Less explicit than `*_CONFIG_FILE`
- Deprecated in favor of `*_CONFIG_FILE`
- Harder to debug when paths are wrong

**Migration:**

```bash
# Before (old pattern)
MARKDOWN_LINTER_RULES=.github/linters/.markdownlint.json

# After (correct pattern)
MARKDOWN_CONFIG_FILE=.markdownlint.json
```

## Never Use Symlinks

**CRITICAL RULE: Never use symlinks for linter configuration files.**

### Why Symlinks Cause Problems

1. **Docker container path resolution**: Super Linter runs in a Docker container where symlinks may
   resolve to incorrect paths
2. **Cross-platform issues**: Symlinks behave differently on Windows, macOS, and Linux
3. **Git repository problems**: Symlinks can cause issues in different git configurations
4. **Debugging difficulty**: Hard to trace which file is actually being used
5. **Maintenance overhead**: Symlinks add complexity without benefits

### Common Symlink Anti-Pattern

```bash
# ❌ WRONG: Using symlinks
cd .github/linters
ln -s ../../.markdownlint.json .markdownlint.json

# This causes Super Linter to fail with:
# "MARKDOWN_CONFIG_FILE rules file doesn't exist"
```

### Correct Approach

```bash
# ✅ CORRECT: Direct file reference
MARKDOWN_CONFIG_FILE=.markdownlint.json

# File exists in root directory:
ls -la .markdownlint.json
# -rw-r--r--  1 user  staff  123 Jan 1 12:00 .markdownlint.json
```

## Multi-Language Support

ghcommon supports 15+ programming languages and file formats:

### Enabled Validators

```bash
# Core languages
VALIDATE_BASH=true
VALIDATE_GO=true
VALIDATE_PYTHON=true
VALIDATE_RUST=true

# Web technologies
VALIDATE_JAVASCRIPT_ES=true
VALIDATE_JAVASCRIPT_STANDARD=true
VALIDATE_TYPESCRIPT_ES=true
VALIDATE_TYPESCRIPT_STANDARD=true
VALIDATE_HTML=true

# Configuration formats
VALIDATE_YAML=true
VALIDATE_JSON=true
VALIDATE_XML=true

# Documentation
VALIDATE_MARKDOWN=true

# Infrastructure
VALIDATE_DOCKER=true
VALIDATE_GITHUB_ACTIONS=true
VALIDATE_EDITORCONFIG=true

# Protobuf
VALIDATE_PROTOBUF=true

# Shell
VALIDATE_SHELL_SHFMT=true
```

### Python-Specific Configuration

Python uses **5 different validators**:

```bash
VALIDATE_PYTHON_BLACK=true       # Code formatting
VALIDATE_PYTHON_FLAKE8=true      # Style guide enforcement
VALIDATE_PYTHON_ISORT=true       # Import sorting
VALIDATE_PYTHON_MYPY=true        # Static type checking
VALIDATE_PYTHON_PYLINT=true      # Code analysis

# Explicit config files
PYTHON_BLACK_CONFIG_FILE=.python-black
PYTHON_PYLINT_CONFIG_FILE=.pylintrc
# Note: Flake8, isort, mypy use default discovery
```

### Language-Specific Config Files

Each language validator may have its own configuration:

| Language              | Validator     | Config File          |
| --------------------- | ------------- | -------------------- |
| JavaScript/TypeScript | ESLint        | `.eslintrc.yml`      |
| Python                | Black         | `.python-black`      |
| Python                | Pylint        | `.pylintrc`          |
| Python                | Ruff          | `ruff.toml`          |
| Markdown              | markdownlint  | `.markdownlint.json` |
| YAML                  | yamllint      | `.yaml-lint.yml`     |
| Rust                  | Clippy        | `clippy.toml`        |
| Rust                  | rustfmt       | `rustfmt.toml`       |
| Go                    | golangci-lint | `.golangci.yml`      |
| Shell                 | shfmt         | (uses defaults)      |
| Docker                | hadolint      | (uses defaults)      |

## Configuration File Structure

### super-linter-ci.env

CI validation configuration (read-only checks):

```bash
# file: super-linter-ci.env
# version: 1.1.3
# guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d

# Core Configuration
VALIDATE_ALL_CODEBASE=false      # Only validate changed files
DEFAULT_BRANCH=main               # Compare against main branch
LOG_LEVEL=INFO                    # Detailed logging

# Auto-Fix Mode: DISABLED for CI
FIX_BASH=false
FIX_JAVASCRIPT_ES=false
# ... all FIX_* variables set to false

# Validators: ENABLED for all languages
VALIDATE_BASH=true
VALIDATE_JAVASCRIPT_ES=true
# ... all VALIDATE_* variables set appropriately

# Config Files: EXPLICIT paths
JAVASCRIPT_ES_CONFIG_FILE=.eslintrc.yml
MARKDOWN_CONFIG_FILE=.markdownlint.json
# ... all *_CONFIG_FILE variables set explicitly

# Filter Patterns: Exclude generated code
FILTER_REGEX_EXCLUDE=(vendor/|node_modules/|\.pb\.go$|_pb2\.py$)
```

### super-linter-pr.env

PR automation configuration (auto-fix mode):

```bash
# file: super-linter-pr.env
# version: 1.0.0
# guid: c3d4e5f6-7a8b-9c0d-1e2f-3a4b5c6d7e8f

# Core Configuration
VALIDATE_ALL_CODEBASE=false      # Only validate changed files
DEFAULT_BRANCH=main               # Compare against main branch

# Auto-Fix Mode: ENABLED for supported linters
FIX_BASH=true
FIX_JAVASCRIPT_ES=true
FIX_MARKDOWN=true
# ... selective FIX_* variables enabled

# Validators: ENABLED (same as CI)
VALIDATE_BASH=true
# ... all VALIDATE_* variables match super-linter-ci.env

# Config Files: EXPLICIT paths (same as CI)
JAVASCRIPT_ES_CONFIG_FILE=.eslintrc.yml
# ... all *_CONFIG_FILE variables match super-linter-ci.env
```

### Key Differences Between CI and PR Configs

| Aspect            | CI Config            | PR Config                 |
| ----------------- | -------------------- | ------------------------- |
| Purpose           | Validation only      | Validation + auto-fix     |
| `FIX_*` variables | All `false`          | Selectively `true`        |
| Commit changes    | No                   | Yes (auto-commit fixes)   |
| Use case          | Pre-merge validation | Automated PR improvements |
| Failure mode      | Block merge          | Fix and update PR         |

## Versioning and Maintenance

### Version Headers

All configuration files must include version headers:

```bash
# file: super-linter-ci.env
# version: 1.1.3
# guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d
```

### Version Update Rules

**When modifying configuration files, ALWAYS update the version number:**

- **Patch version** (x.y.Z): Bug fixes, typo corrections, comment updates
  - Example: `1.1.2` → `1.1.3` (fix incorrect path)

- **Minor version** (x.Y.z): New validators, config additions, feature changes
  - Example: `1.1.3` → `1.2.0` (add new language support)

- **Major version** (X.y.z): Breaking changes, structural overhauls, pattern changes
  - Example: `1.2.0` → `2.0.0` (move from .github/linters/ to root)

### Synchronization Across Repositories

When updating Super Linter configurations:

1. **Update ghcommon first**: Make changes in the canonical repository
2. **Document changes**: Update this file and related docs
3. **Test thoroughly**: Run test workflow (see Task 17-23)
4. **Sync to other repos**: Use manual sync process (see MANUAL_SYNC_PROCESS.md)
5. **Verify each repo**: Each repository may have different needs

### Cross-Repository Consistency

**Same pattern, different locations:**

- **ghcommon, subtitle-manager**: Config files in root directory
- **audiobook-organizer, copilot-agent-util-rust, gcommon-proto**: Config files in
  `.github/linters/`
- **ubuntu-autoinstall-agent**: Config files in root directory, Rust-focused

**Key point**: The _pattern_ (explicit `*_CONFIG_FILE` variables) is consistent, but the _location_
varies by repository needs.

## Related Documentation

- [LINTER_CONFIG_LOCATIONS.md](./LINTER_CONFIG_LOCATIONS.md) - Complete list of all 15 linter
  configs
- [SUPER_LINTER_CONFIG_COMPARISON.md](./SUPER_LINTER_CONFIG_COMPARISON.md) - Comparison with
  ubuntu-autoinstall-agent
- [MANUAL_SYNC_PROCESS.md](./MANUAL_SYNC_PROCESS.md) - How to sync configs to other repos (Task 24)
- [SUPER_LINTER_TESTING_RESULTS.md](./SUPER_LINTER_TESTING_RESULTS.md) - Test results and
  verification (Task 23)

## Troubleshooting

### Common Issues and Solutions

#### Issue: "CONFIG_FILE rules file doesn't exist"

```bash
# Error message:
MARKDOWN_CONFIG_FILE rules file doesn't exist: .github/linters/.markdownlint.json

# Cause: Config file not found at specified path

# Solution 1: Verify file exists
ls -la .markdownlint.json

# Solution 2: Check path in super-linter-ci.env
MARKDOWN_CONFIG_FILE=.markdownlint.json  # Should match actual location

# Solution 3: Never use symlinks
rm .github/linters/.markdownlint.json    # Remove symlink
```

#### Issue: Linter ignoring configuration

```bash
# Symptom: Linter runs but doesn't use custom rules

# Cause: Using deprecated *_LINTER_RULES instead of *_CONFIG_FILE

# Solution: Migrate to CONFIG_FILE pattern
# Before:
MARKDOWN_LINTER_RULES=.markdownlint.json

# After:
MARKDOWN_CONFIG_FILE=.markdownlint.json
```

#### Issue: Different behavior in CI vs local

```bash
# Symptom: Linter passes locally but fails in CI

# Cause: Different config file paths or versions

# Solution 1: Check config version
head -5 super-linter-ci.env
# version: 1.1.3

# Solution 2: Verify paths match
grep CONFIG_FILE super-linter-ci.env | grep -v "^#"

# Solution 3: Test with Super Linter Docker container
docker run --rm -v "$PWD":/tmp/lint github/super-linter:latest
```

## Best Practices Summary

1. ✅ **Store configs in root directory** for simplicity
2. ✅ **Use `*_CONFIG_FILE` variables** explicitly
3. ✅ **Never use symlinks** for config files
4. ✅ **Version all configuration files** with semantic versioning
5. ✅ **Test changes** with test workflow before merging
6. ✅ **Document decisions** in this file and related docs
7. ✅ **Keep CI and PR configs in sync** for consistency
8. ✅ **Update versions** when modifying configs
9. ✅ **Reference actual files** not directories
10. ✅ **Avoid `*_LINTER_RULES`** variables (deprecated)

## Next Steps

After reading this document:

1. Review [LINTER_CONFIG_LOCATIONS.md](./LINTER_CONFIG_LOCATIONS.md) for complete config list
2. Compare with other repositories using
   [SUPER_LINTER_CONFIG_COMPARISON.md](./SUPER_LINTER_CONFIG_COMPARISON.md)
3. Learn manual sync process from [MANUAL_SYNC_PROCESS.md](./MANUAL_SYNC_PROCESS.md) (when created)
4. Run test workflow to verify configurations (Tasks 17-23)
5. Review test results in [SUPER_LINTER_TESTING_RESULTS.md](./SUPER_LINTER_TESTING_RESULTS.md) (when
   created)
