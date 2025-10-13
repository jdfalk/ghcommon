<!-- file: .github/test-files/README.md -->
<!-- version: 1.0.0 -->
<!-- guid: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e -->

# Super Linter Test Files

This directory contains sample files for testing Super Linter configurations.

## Purpose

These files are used by the `test-super-linter.yml` workflow to verify that all linter
configurations work correctly.

## Test Files

| File              | Language   | Purpose                                 |
| ----------------- | ---------- | --------------------------------------- |
| `test.md`         | Markdown   | Test markdownlint configuration         |
| `test.yaml`       | YAML       | Test yamllint configuration             |
| `test.json`       | JSON       | Test JSON linting                       |
| `test.sh`         | Shell/Bash | Test bash and shfmt configuration       |
| `test.py`         | Python     | Test Black, Pylint, Flake8, isort, mypy |
| `test.go`         | Go         | Test golangci-lint configuration        |
| `test.js`         | JavaScript | Test ESLint configuration               |
| `test.rs`         | Rust       | Test Clippy and rustfmt configuration   |
| `test.dockerfile` | Docker     | Test hadolint configuration             |

## Test Characteristics

### Valid Files

All files are syntactically valid and should pass basic linting checks:

- **Markdown**: Follows markdownlint rules (proper headings, lists, formatting)
- **YAML**: Valid YAML syntax with proper indentation
- **JSON**: Valid JSON structure
- **Shell**: Valid bash syntax with proper function definitions
- **Python**: Type-annotated, documented code
- **Go**: Standard Go formatting and structure
- **JavaScript**: ESLint-compliant with JSDoc comments
- **Rust**: Clippy-compliant with proper documentation
- **Docker**: Hadolint-compliant with best practices

### Intentional Linting Warnings

Some files include intentional minor linting issues for testing:

- **Python (`test.py`)**: Uses `print` statements (not recommended for production)
- **Python (`test.py`)**: Uses deprecated `typing.List` (should use `list`)
- **Python (`test.py`)**: Docstring formatting issues (multi-line summaries)

These warnings are intentional to test that linters catch common issues.

## Usage

### Run All Tests

```bash
# Via GitHub Actions workflow
gh workflow run test-super-linter.yml --ref main -f test_scenario=all

# Or push to test branch
git checkout -b test-super-linter/update
git push origin test-super-linter/update
```

### Run Specific Language Tests

```bash
# Test Markdown only
gh workflow run test-super-linter.yml --ref main -f test_scenario=markdown-only

# Test Python only
gh workflow run test-super-linter.yml --ref main -f test_scenario=python-only

# Test Rust only
gh workflow run test-super-linter.yml --ref main -f test_scenario=rust-only
```

### Local Testing

Test individual files locally with their respective linters:

```bash
# Markdown
markdownlint -c .markdownlint.json .github/test-files/test.md

# YAML
yamllint -c .yaml-lint.yml .github/test-files/test.yaml

# JSON
jsonlint .github/test-files/test.json

# Shell
shellcheck .github/test-files/test.sh
shfmt -d .github/test-files/test.sh

# Python
black --check .github/test-files/test.py
pylint --rcfile=.pylintrc .github/test-files/test.py
flake8 .github/test-files/test.py
isort --check .github/test-files/test.py
mypy .github/test-files/test.py

# Go
cd .github/test-files && golangci-lint run test.go

# JavaScript
eslint -c .eslintrc.yml .github/test-files/test.js

# Rust
cargo clippy -- -D warnings
rustfmt --check .github/test-files/test.rs

# Docker
hadolint .github/test-files/test.dockerfile
```

## Expected Results

### Passing Tests

Files should pass all tests when using the correct configuration:

- ✅ Markdown lint (with `.markdownlint.json`)
- ✅ YAML lint (with `.yaml-lint.yml`)
- ✅ JSON lint (default config)
- ✅ Bash lint (shellcheck + shfmt)
- ✅ Go lint (with `.golangci.yml`)
- ✅ JavaScript lint (with `.eslintrc.yml`)
- ✅ Rust lint (with `clippy.toml` and `rustfmt.toml`)
- ✅ Docker lint (hadolint defaults)

### Expected Warnings

Python file may produce warnings (intentional):

- ⚠️ Print statements detected (T201)
- ⚠️ Deprecated `typing.List` usage (UP006)
- ⚠️ Docstring format (D205, D212)

These are normal and expected for testing purposes.

## Maintenance

When updating these files:

1. Keep the file headers (file path, version, guid)
2. Bump version numbers when making changes
3. Maintain valid syntax for each language
4. Document any intentional linting issues
5. Update this README with new files or changes

## Related Documentation

- [Test Workflow](.github/workflows/test-super-linter.yml) - Main test workflow
- [Test Configs](.github/test-configs/) - Test-specific Super Linter configs
- [Super Linter Strategy](../docs/SUPER_LINTER_STRATEGY.md) - Overall strategy document
- [Linter Config Locations](../docs/LINTER_CONFIG_LOCATIONS.md) - List of all config files
