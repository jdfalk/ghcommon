<!-- file: docs/LINTER_VALIDATION.md -->
<!-- version: 1.0.0 -->
<!-- guid: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e -->

# Linter Configuration Validation

This document describes the comprehensive linter configuration validation system for ensuring all linter configs comply with Google Style Guides.

## Overview

The repository contains multiple linter configuration files for different languages and tools. This validation system ensures:

1. All configuration files exist and are syntactically valid
2. Configurations follow Google Style Guide standards
3. Cross-references between configs are correct
4. Linters can be tested in isolation using Docker

## Google Style Guides

This repository follows these Google Style Guides:

- **JavaScript/TypeScript**: [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html)
- **Python**: [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- **Go**: [Google Go Style Guide](https://google.github.io/styleguide/go/)
- **Shell**: [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- **HTML/CSS**: [Google HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html)

## Key Style Guide Requirements

### Line Length Standards

- **JavaScript/TypeScript**: 80 characters (Google standard)
- **Python**: 80 characters (Google Python standard)
- **Go**: No strict limit, but gofmt handles formatting
- **Shell**: No strict limit, but readability matters

### Indentation Standards

- **JavaScript/TypeScript**: 2 spaces
- **Python**: 2 or 4 spaces (we use 2 for Google compliance)
- **Go**: Tabs (handled by gofmt)
- **YAML**: 2 spaces
- **JSON**: 2 spaces

## Configuration Files

### JavaScript/TypeScript

#### `.prettierrc.json`
```json
{
  "tabWidth": 2,
  "useTabs": false,
  "printWidth": 80,
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5"
}
```

**Google Compliance:**
- ✅ 2 spaces indentation
- ✅ 80 character line limit
- ✅ Semicolons required
- ✅ Single quotes preferred

#### `.eslintrc.yml`
Should extend `eslint-config-google` for full compliance.

### Python

#### `.python-black`
```
--line-length=80
--target-version=py311
```

**Google Compliance:**
- ✅ 80 character line limit
- ✅ Python 3.11+ target

#### `.pylintrc`
Should set `max-line-length=80`

#### `.isort.cfg`
```ini
[settings]
line_length = 80
profile = black
```

**Google Compliance:**
- ✅ 80 character line limit
- ✅ Black-compatible profile

### Go

#### `.golangci.yml`
Go formatting is handled by `gofmt` and `goimports`, which automatically comply with Go standards.

### Markdown

#### `.markdownlint.json`
Configured for consistent markdown formatting across documentation.

### YAML

#### `.yaml-lint.yml`
Ensures YAML files follow consistent formatting rules.

### Rust

#### `clippy.toml`
Rust linting rules via Clippy.

#### `rustfmt.toml`
Rust formatting rules.

## Validation Script

### Usage

Run the comprehensive validation script:

```bash
# Basic validation
python3 scripts/validate-linter-configs.py

# Verbose output
python3 scripts/validate-linter-configs.py --verbose

# From different directory
python3 scripts/validate-linter-configs.py --repo-root /path/to/repo
```

### What It Checks

1. **File Existence**: All referenced config files exist
2. **Syntax Validation**: JSON/YAML files are syntactically correct
3. **Google Compliance**: Line lengths, indentation match Google standards
4. **Cross-References**: Super Linter .env files reference existing configs
5. **Readability**: Config files are properly formatted

### Exit Codes

- `0`: All validations passed (warnings OK)
- `1`: Validation failed with errors

## VS Code Tasks

### Available Tasks

Run these tasks from VS Code's "Run Task" menu (`Cmd+Shift+P` → "Tasks: Run Task"):

#### 1. Validate Linter Configs
- **Task**: `Validate Linter Configs`
- **Description**: Runs comprehensive validation script
- **Usage**: Quick check before committing changes

#### 2. Run Super Linter in Docker (CI Mode)
- **Task**: `Run Super Linter in Docker (CI Mode)`
- **Description**: Runs Super Linter with CI configuration
- **Usage**: Test all files as CI would test them
- **Config**: Uses `super-linter-ci.env`

#### 3. Run Super Linter in Docker (PR Mode)
- **Task**: `Run Super Linter in Docker (PR Mode)`
- **Description**: Runs Super Linter with PR auto-fix configuration
- **Usage**: Test auto-fix functionality
- **Config**: Uses `super-linter-pr.env`

#### 4. Run Super Linter in Docker (Test Minimal)
- **Task**: `Run Super Linter in Docker (Test Minimal)`
- **Description**: Runs Super Linter with minimal test config
- **Usage**: Quick smoke test with 3 validators
- **Config**: Uses `.github/test-configs/test-minimal.env`

### Docker Requirements

To use the Docker-based Super Linter tasks, you need:

1. **Docker installed and running**
   ```bash
   docker --version
   ```

2. **Super Linter image pulled**
   ```bash
   docker pull ghcr.io/super-linter/super-linter:latest
   ```

3. **Sufficient Docker resources**
   - Memory: At least 4GB
   - Disk space: At least 2GB for the image

### Task Output

All tasks log output to the integrated terminal. Look for:

- ✅ Green checkmarks: Validation passed
- ❌ Red X marks: Errors found
- ⚠️ Yellow warnings: Non-critical issues

## Manual Docker Testing

### Basic Run

```bash
docker run --rm \
  -e RUN_LOCAL=true \
  -e VALIDATE_ALL_CODEBASE=true \
  -v $(pwd):/tmp/lint:ro \
  --env-file super-linter-ci.env \
  ghcr.io/super-linter/super-linter:latest
```

### Test Specific Linters

```bash
# Test only Python linters
docker run --rm \
  -e RUN_LOCAL=true \
  -e VALIDATE_PYTHON_BLACK=true \
  -e VALIDATE_PYTHON_PYLINT=true \
  -e VALIDATE_PYTHON_ISORT=true \
  -v $(pwd):/tmp/lint:ro \
  ghcr.io/super-linter/super-linter:latest
```

### Auto-Fix Mode

```bash
docker run --rm \
  -e RUN_LOCAL=true \
  -v $(pwd):/tmp/lint \
  --env-file super-linter-pr.env \
  ghcr.io/super-linter/super-linter:latest
```

**Note**: Remove `:ro` (read-only) flag to allow auto-fixing.

## Continuous Integration

### GitHub Actions Integration

The repository includes workflow files that run linter validation:

- `.github/workflows/ci.yml` - Runs Super Linter on all PRs
- `.github/workflows/test-super-linter.yml` - Comprehensive test suite

### Pre-Commit Hooks

Consider adding pre-commit hooks:

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install
```

## Troubleshooting

### Common Issues

#### "Config file not found"

**Solution**: Run validation script to identify missing files:
```bash
python3 scripts/validate-linter-configs.py --verbose
```

#### "Docker mount permission denied"

**Solution**: Ensure Docker has permission to access the repository:
```bash
# On macOS
# System Preferences → Privacy & Security → Files and Folders → Docker
```

#### "Line length violations"

**Solution**: Update config files to match Google standards (80 chars for Python/JS).

#### "Super Linter fails in Docker"

**Solution**: Check the specific linter logs:
```bash
docker run --rm \
  -e RUN_LOCAL=true \
  -e LOG_LEVEL=DEBUG \
  -v $(pwd):/tmp/lint:ro \
  --env-file super-linter-ci.env \
  ghcr.io/super-linter/super-linter:latest 2>&1 | less
```

### Debug Mode

Run validation with maximum verbosity:

```bash
# Validation script
python3 scripts/validate-linter-configs.py --verbose

# Super Linter
docker run --rm \
  -e RUN_LOCAL=true \
  -e LOG_LEVEL=DEBUG \
  -e LOG_FILE=super-linter.log \
  -v $(pwd):/tmp/lint:ro \
  --env-file super-linter-ci.env \
  ghcr.io/super-linter/super-linter:latest
```

## Best Practices

### Before Committing

1. Run validation script: `python3 scripts/validate-linter-configs.py`
2. Fix any errors reported
3. Run Super Linter in Docker: VS Code task "Run Super Linter in Docker (CI Mode)"
4. Address any linting issues
5. Commit changes

### When Adding New Linters

1. Add configuration file to repository root
2. Reference in appropriate `super-linter-*.env` file
3. Update `scripts/validate-linter-configs.py` with new validator
4. Update this documentation
5. Run full validation suite

### When Updating Configs

1. Check Google Style Guide for latest recommendations
2. Update config file
3. Run validation script
4. Test with Super Linter in Docker
5. Update documentation if behavior changes

## References

- [Super Linter Documentation](https://github.com/super-linter/super-linter)
- [Google Style Guides](https://google.github.io/styleguide/)
- [Prettier Documentation](https://prettier.io/docs/en/)
- [ESLint Documentation](https://eslint.org/docs/latest/)
- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)

## Version History

- **1.0.0** (2025-10-12): Initial comprehensive validation system
  - Created validation script
  - Added VS Code tasks for Docker testing
  - Documented Google Style Guide compliance
  - Added troubleshooting guide
