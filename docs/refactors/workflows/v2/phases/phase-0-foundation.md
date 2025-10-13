<!-- file: docs/refactors/workflows/v2/phases/phase-0-foundation.md -->
<!-- version: 1.0.0 -->
<!-- guid: d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a -->

# Phase 0: Foundation

## Overview

Phase 0 establishes the foundational infrastructure required for all subsequent phases. This includes shared utilities, configuration validation, security frameworks, and feature flags.

**Status**: 🟡 Planning
**Dependencies**: None
**Target Completion**: 2025-10-20
**Platforms**: ubuntu-latest, macos-latest (NO WINDOWS)

## Success Criteria

- [ ] `workflow_common.py` created with all shared utilities
- [ ] JSON Schema validation for `repository-config.yml`
- [ ] Security audit checklist completed
- [ ] Feature flag system operational
- [ ] All unit tests pass (100% coverage for new code)
- [ ] Documentation updated

## Design Principles

Every task in this phase MUST be:
- **Independent**: Can be executed without waiting for other tasks
- **Idempotent**: Running multiple times produces same result
- **Testable**: Unit tests exist and pass
- **Compliant**: Follows `.github/instructions/python.instructions.md` and `.github/instructions/general-coding.instructions.md`

---

## Task 0.1: Create Shared Utility Module

**Status**: Not Started
**Dependencies**: None (fully independent)
**Estimated Time**: 1-2 hours
**Idempotent**: Yes

### Description

Create `.github/workflows/scripts/workflow_common.py` containing shared utilities used by all workflow helpers.

### Code Style Requirements

**MUST follow**:
- `.github/instructions/python.instructions.md` - Type hints, docstrings, formatting
- `.github/instructions/general-coding.instructions.md` - File headers, versioning

### Implementation

Create file: `.github/workflows/scripts/workflow_common.py`

```python
#!/usr/bin/env python3
# file: .github/workflows/scripts/workflow_common.py
# version: 1.0.0
# guid: e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b

"""
Shared utilities for all GitHub Actions workflow helper scripts.

This module provides common functionality for config loading, GitHub Actions I/O,
error handling, and performance monitoring.
"""

from __future__ import annotations

import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import yaml

# Global config cache
_CONFIG_CACHE: dict[str, Any] | None = None


class WorkflowError(Exception):
    """
    Workflow execution error with recovery hints.

    Attributes:
        message: Error description
        hint: Suggested fix or recovery action
        docs_url: Link to relevant documentation
    """

    def __init__(
        self,
        message: str,
        hint: str = "",
        docs_url: str = "",
    ) -> None:
        """
        Initialize workflow error.

        Args:
            message: Error description
            hint: Optional recovery suggestion
            docs_url: Optional documentation link
        """
        self.message = message
        self.hint = hint
        self.docs_url = docs_url
        super().__init__(message)

    def __str__(self) -> str:
        """Format error with hints and documentation."""
        parts = [f"❌ {self.message}"]
        if self.hint:
            parts.append(f"💡 Hint: {self.hint}")
        if self.docs_url:
            parts.append(f"📚 Docs: {self.docs_url}")
        return "\n".join(parts)


def append_to_file(path_env: str, content: str) -> None:
    """
    Append content to GitHub Actions environment file.

    Args:
        path_env: Environment variable name containing file path
        content: Content to append

    Raises:
        WorkflowError: If environment variable not set or file doesn't exist

    Example:
        >>> append_to_file("GITHUB_OUTPUT", "my_var=value\\n")
    """
    file_path_str = os.environ.get(path_env)
    if not file_path_str:
        raise WorkflowError(
            f"Environment variable {path_env} not set",
            hint="This tool must be run inside GitHub Actions workflow",
            docs_url="https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions",
        )

    file_path = Path(file_path_str)
    if not file_path.exists():
        raise WorkflowError(
            f"File {file_path} does not exist",
            hint=f"Ensure GitHub Actions runner has created {path_env}",
        )

    with file_path.open("a", encoding="utf-8") as f:
        f.write(content)


def write_output(name: str, value: str) -> None:
    """
    Write value to GitHub Actions output.

    Args:
        name: Output variable name
        value: Output value (will be converted to string)

    Example:
        >>> write_output("coverage", "85.5")
    """
    append_to_file("GITHUB_OUTPUT", f"{name}={value}\n")


def append_env(name: str, value: str) -> None:
    """
    Add environment variable for subsequent workflow steps.

    Args:
        name: Environment variable name
        value: Environment variable value

    Example:
        >>> append_env("GO_VERSION", "1.24")
    """
    append_to_file("GITHUB_ENV", f"{name}={value}\n")


def append_summary(text: str) -> None:
    """
    Append text to GitHub Actions step summary.

    Args:
        text: Markdown-formatted text to display in summary

    Example:
        >>> append_summary("## Test Results\\n- ✅ All tests passed\\n")
    """
    append_to_file("GITHUB_STEP_SUMMARY", text)


def get_repository_config() -> dict[str, Any]:
    """
    Load and cache repository-config.yml.

    Returns:
        Parsed YAML configuration dictionary

    Raises:
        WorkflowError: If config file missing or invalid

    Example:
        >>> config = get_repository_config()
        >>> go_versions = config["languages"]["versions"]["go"]
    """
    global _CONFIG_CACHE

    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    config_path = Path(".github/repository-config.yml")
    if not config_path.exists():
        raise WorkflowError(
            "repository-config.yml not found",
            hint="Run: cp .github/repository-config.example.yml .github/repository-config.yml",
            docs_url="https://github.com/jdfalk/ghcommon/docs/refactors/workflows/v2/reference/config-schema.md",
        )

    try:
        with config_path.open(encoding="utf-8") as f:
            _CONFIG_CACHE = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise WorkflowError(
            f"Invalid YAML in repository-config.yml: {e}",
            hint="Validate YAML syntax with: yamllint .github/repository-config.yml",
        ) from e

    if not isinstance(_CONFIG_CACHE, dict):
        raise WorkflowError(
            "repository-config.yml must contain a YAML dictionary",
            hint="Ensure file starts with top-level keys, not a list",
        )

    return _CONFIG_CACHE


def config_path(default: Any, *path: str) -> Any:
    """
    Navigate config dict with fallback default.

    Args:
        default: Value to return if path doesn't exist
        *path: Path components to navigate (e.g., "languages", "versions", "go")

    Returns:
        Value at config path, or default if not found

    Example:
        >>> versions = config_path([], "languages", "versions", "go")
        >>> threshold = config_path(80, "testing", "coverage", "threshold")
    """
    current: Any = get_repository_config()

    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]

    return current


@contextmanager
def timed_operation(operation_name: str):
    """
    Context manager to time and report operation duration.

    Args:
        operation_name: Description of operation being timed

    Yields:
        None

    Example:
        >>> with timed_operation("Load configuration"):
        ...     config = get_repository_config()
        ⏱️  Load configuration took 0.05s
    """
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        print(f"⏱️  {operation_name} took {duration:.2f}s")
        append_summary(f"| {operation_name} | {duration:.2f}s |\n")


def handle_error(error: Exception, context: str) -> None:
    """
    Format and log workflow error, then exit.

    Args:
        error: Exception to handle
        context: Where error occurred (e.g., "generate_matrices")

    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     handle_error(e, "Phase 1 setup")
    """
    if isinstance(error, WorkflowError):
        print(str(error), file=sys.stderr)
    else:
        print(f"❌ Unexpected error in {context}: {error}", file=sys.stderr)

    sys.exit(1)


def sanitize_log(message: str) -> str:
    """
    Remove potential secrets from log output.

    Args:
        message: Log message to sanitize

    Returns:
        Sanitized message with secrets masked

    Example:
        >>> sanitize_log("Token: ghp_abc123...")
        'Token: ***GITHUB_TOKEN***'
    """
    import re

    # Mask GitHub tokens
    message = re.sub(r"ghp_[a-zA-Z0-9]{36}", "***GITHUB_TOKEN***", message)
    message = re.sub(r"ghs_[a-zA-Z0-9]{36}", "***GITHUB_SECRET***", message)

    # Mask generic Bearer tokens
    message = re.sub(r"Bearer\s+[a-zA-Z0-9\-._~+/]+=*", "Bearer ***TOKEN***", message)

    return message


def ensure_file(path: Path, content: str) -> bool:
    """
    Create file if missing (idempotent operation).

    Args:
        path: File path to create
        content: File content

    Returns:
        True if file was created, False if already existed

    Example:
        >>> created = ensure_file(Path("config.yml"), "default: true\\n")
        >>> if created:
        ...     print("Created new config file")
    """
    if path.exists():
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True
```

### Verification Steps

```bash
# 1. Verify file exists
test -f .github/workflows/scripts/workflow_common.py && echo "✅ File created"

# 2. Check Python syntax
python3 -m py_compile .github/workflows/scripts/workflow_common.py && echo "✅ Valid Python"

# 3. Verify imports work
python3 -c "import sys; sys.path.insert(0, '.github/workflows/scripts'); import workflow_common" && echo "✅ Module imports"

# 4. Run type checking
cd .github/workflows/scripts && mypy workflow_common.py && echo "✅ Type hints valid"
```

### Test Requirements

Create `tests/workflow_scripts/test_workflow_common.py` (see Task 0.5).

---

## Task 0.2: Create Configuration Schema

**Status**: Not Started
**Dependencies**: None (fully independent)
**Estimated Time**: 1 hour
**Idempotent**: Yes

### Description

Create JSON Schema for `repository-config.yml` validation.

### Implementation

Create file: `.github/schemas/repository-config.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Repository Configuration Schema",
  "description": "Configuration schema for ghcommon workflow system",
  "type": "object",
  "properties": {
    "languages": {
      "type": "object",
      "properties": {
        "versions": {
          "type": "object",
          "properties": {
            "go": {
              "type": "array",
              "items": {"type": "string", "pattern": "^1\\.(23|24)$"},
              "minItems": 1,
              "maxItems": 2,
              "description": "Supported Go versions (1.23, 1.24)"
            },
            "python": {
              "type": "array",
              "items": {"type": "string", "pattern": "^3\\.(13|14)$"},
              "minItems": 1,
              "maxItems": 2,
              "description": "Supported Python versions (3.13, 3.14)"
            },
            "node": {
              "type": "array",
              "items": {"type": "string", "pattern": "^(20|22)$"},
              "minItems": 1,
              "maxItems": 2,
              "description": "Supported Node.js LTS versions (20, 22)"
            },
            "rust": {
              "type": "array",
              "items": {"type": "string", "enum": ["stable", "stable-1"]},
              "minItems": 1,
              "maxItems": 2,
              "description": "Supported Rust channels"
            }
          }
        }
      }
    },
    "build": {
      "type": "object",
      "properties": {
        "platforms": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["ubuntu-latest", "macos-latest"]
          },
          "minItems": 1,
          "description": "Build platforms (NO WINDOWS)"
        }
      }
    },
    "testing": {
      "type": "object",
      "properties": {
        "coverage": {
          "type": "object",
          "properties": {
            "threshold": {
              "type": "number",
              "minimum": 0,
              "maximum": 100,
              "description": "Minimum coverage percentage"
            },
            "format": {
              "type": "string",
              "enum": ["lcov", "cobertura", "json"],
              "description": "Coverage report format"
            }
          }
        }
      }
    },
    "workflows": {
      "type": "object",
      "properties": {
        "experimental": {
          "type": "object",
          "properties": {
            "use_new_ci": {"type": "boolean"},
            "use_new_release": {"type": "boolean"},
            "use_config_matrices": {"type": "boolean"}
          },
          "description": "Feature flags for gradual rollout"
        }
      }
    }
  },
  "required": ["languages", "build"]
}
```

### Verification Steps

```bash
# 1. Verify schema file exists
test -f .github/schemas/repository-config.schema.json && echo "✅ Schema created"

# 2. Validate schema is valid JSON
cat .github/schemas/repository-config.schema.json | jq . > /dev/null && echo "✅ Valid JSON"

# 3. Validate against example config
pip install jsonschema
python3 -c "
import json
from jsonschema import validate
schema = json.load(open('.github/schemas/repository-config.schema.json'))
config = json.load(open('.github/repository-config.example.yml'))  # If exists
validate(config, schema)
print('✅ Schema validation works')
"
```

---

## Task 0.3: Create Config Validation Script

**Status**: Not Started
**Dependencies**: Task 0.2 (needs schema), Task 0.1 (needs workflow_common)
**Estimated Time**: 30 minutes
**Idempotent**: Yes

### Description

Create validation script that checks `repository-config.yml` against schema.

### Implementation

Create file: `.github/workflows/scripts/validate_config.py`

```python
#!/usr/bin/env python3
# file: .github/workflows/scripts/validate_config.py
# version: 1.0.0
# guid: f6a7b8c9-d0e1-2f3a-4b5c-6d7e8f9a0b1c

"""
Validate repository-config.yml against JSON schema.

Usage:
    python validate_config.py [--schema PATH] [--config PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from jsonschema import ValidationError, validate

import workflow_common


def validate_repository_config(
    schema_path: Path,
    config_path: Path,
) -> bool:
    """
    Validate config file against schema.

    Args:
        schema_path: Path to JSON schema file
        config_path: Path to repository config YAML file

    Returns:
        True if valid, False otherwise
    """
    # Load schema
    try:
        with schema_path.open(encoding="utf-8") as f:
            schema = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load schema from {schema_path}: {e}")
        return False

    # Load config
    try:
        with config_path.open(encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load config from {config_path}: {e}")
        return False

    # Validate
    try:
        validate(config, schema)
        print(f"✅ Configuration valid: {config_path}")
        return True
    except ValidationError as e:
        print(f"❌ Configuration invalid: {config_path}")
        print(f"   Error: {e.message}")
        print(f"   Path: {'.'.join(str(p) for p in e.path)}")
        return False


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate repository-config.yml",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(".github/schemas/repository-config.schema.json"),
        help="Path to JSON schema",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(".github/repository-config.yml"),
        help="Path to repository config",
    )

    args = parser.parse_args()

    if not args.schema.exists():
        print(f"❌ Schema not found: {args.schema}")
        sys.exit(1)

    if not args.config.exists():
        print(f"❌ Config not found: {args.config}")
        sys.exit(1)

    if not validate_repository_config(args.schema, args.config):
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Verification Steps

```bash
# 1. Create test config
cat > /tmp/test-config.yml << 'EOF'
languages:
  versions:
    go: ["1.23", "1.24"]
    python: ["3.13", "3.14"]
build:
  platforms:
    - ubuntu-latest
    - macos-latest
testing:
  coverage:
    threshold: 80
EOF

# 2. Run validation
python3 .github/workflows/scripts/validate_config.py \
  --config /tmp/test-config.yml && echo "✅ Validation works"

# 3. Test with invalid config
cat > /tmp/invalid-config.yml << 'EOF'
languages:
  versions:
    go: ["1.99"]  # Invalid version
build:
  platforms:
    - windows-latest  # Not allowed!
EOF

python3 .github/workflows/scripts/validate_config.py \
  --config /tmp/invalid-config.yml && echo "❌ Should have failed" || echo "✅ Correctly rejected invalid config"
```

---

## Task 0.4: Create Security Audit Checklist

**Status**: Not Started
**Dependencies**: None (fully independent)
**Estimated Time**: 30 minutes
**Idempotent**: Yes

### Description

Create security audit checklist template for workflow reviews.

### Implementation

Create file: `.github/SECURITY_CHECKLIST.md`

```markdown
<!-- file: .github/SECURITY_CHECKLIST.md -->
<!-- version: 1.0.0 -->
<!-- guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d -->

# Workflow Security Audit Checklist

Complete this checklist before deploying new workflows or workflow changes.

## Date: ________________
## Reviewer: ________________
## Phase/PR: ________________

---

## 1. Secret Management

- [ ] No secrets hardcoded in workflow files
- [ ] All secrets use `${{ secrets.SECRET_NAME }}` syntax
- [ ] Secrets are referenced from GitHub Secrets, not environment variables
- [ ] No secret values appear in logs or outputs
- [ ] `::add-mask::` used where needed to prevent accidental exposure

**Notes:**

---

## 2. Permissions

- [ ] Workflow uses minimal required permissions
- [ ] No `permissions: write-all` or overly broad scopes
- [ ] Each job declares specific permissions needed
- [ ] Third-party actions granted minimal permissions
- [ ] Pull requests from forks have restricted permissions

**Current Permissions:**
```yaml
permissions:
  contents: read
  pull-requests: write
  # ... list all permissions
```

---

## 3. Action Pinning

- [ ] All third-party actions pinned to commit SHA, not tags
- [ ] SHA documented with tag in comment (e.g., `# v4.1.1`)
- [ ] Dependabot configured to update pinned actions
- [ ] No mutable references (`@main`, `@v1`)

**Example:**
```yaml
- uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab  # v4.1.1
```

---

## 4. Input Validation

- [ ] All workflow_dispatch inputs validated
- [ ] User-provided inputs sanitized before use
- [ ] No command injection vulnerabilities (e.g., `eval`, `shell: bash`)
- [ ] File paths validated (no directory traversal)
- [ ] Regular expressions tested for ReDoS vulnerabilities

---

## 5. Code Execution

- [ ] No arbitrary code execution from PR comments
- [ ] `pull_request_target` trigger avoided or carefully scoped
- [ ] Artifact downloads validated before extraction
- [ ] No execution of code from untrusted sources
- [ ] Scripts run with minimal privileges

---

## 6. Token Scoping

- [ ] `GITHUB_TOKEN` has appropriate scopes
- [ ] Personal Access Tokens (PATs) avoided when `GITHUB_TOKEN` sufficient
- [ ] Token expiration configured
- [ ] Tokens not passed to untrusted actions
- [ ] API calls use authenticated endpoints

---

## 7. Dependency Security

- [ ] Python dependencies pinned with hashes (`requirements.txt`)
- [ ] Go modules use `go.sum` for integrity
- [ ] npm packages locked with `package-lock.json`
- [ ] Rust dependencies audited with `cargo audit`
- [ ] Dependabot enabled for dependency updates

---

## 8. Environment Isolation

- [ ] No cross-contamination between jobs
- [ ] Temporary files cleaned up
- [ ] Secrets not persisted to disk
- [ ] Build artifacts scanned before upload
- [ ] Containers use non-root users

---

## 9. Logging and Monitoring

- [ ] Sensitive data sanitized from logs
- [ ] Failed runs don't expose credentials
- [ ] Audit trail maintained for security events
- [ ] Anomalous activity detection configured
- [ ] Security incidents have response plan

---

## 10. Compliance

- [ ] Code follows `.github/instructions/security.instructions.md`
- [ ] SAST tools run on workflow code
- [ ] No compliance violations (SOC2, HIPAA, etc.)
- [ ] Security review completed
- [ ] Sign-off from security team

---

## Review Sign-off

- [ ] All items checked and passing
- [ ] Issues documented and tracked
- [ ] Deployment approved

**Reviewer Signature:** ________________

**Date:** ________________

**Notes:**
```

### Verification Steps

```bash
# 1. Verify checklist exists
test -f .github/SECURITY_CHECKLIST.md && echo "✅ Checklist created"

# 2. Verify markdown is valid
npx markdownlint-cli .github/SECURITY_CHECKLIST.md && echo "✅ Valid markdown"
```

---

## Task 0.5: Create Unit Tests for workflow_common

**Status**: Not Started
**Dependencies**: Task 0.1 (needs workflow_common.py)
**Estimated Time**: 2 hours
**Idempotent**: Yes

### Description

Create comprehensive unit tests for `workflow_common.py`.

### Code Style Requirements

**MUST follow**:
- `.github/instructions/test-generation.instructions.md` - Arrange-Act-Assert, independence

### Implementation

Create file: `tests/workflow_scripts/test_workflow_common.py`

```python
#!/usr/bin/env python3
# file: tests/workflow_scripts/test_workflow_common.py
# version: 1.0.0
# guid: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e

"""Unit tests for workflow_common module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".github/workflows/scripts"))

import workflow_common


@pytest.fixture(autouse=True)
def reset_config_cache():
    """Reset global config cache between tests."""
    workflow_common._CONFIG_CACHE = None
    yield
    workflow_common._CONFIG_CACHE = None


def test_workflow_error_formatting():
    """Test WorkflowError formats message with hints."""
    # Arrange
    error = workflow_common.WorkflowError(
        "Test error",
        hint="Try this fix",
        docs_url="https://example.com/docs",
    )

    # Act
    result = str(error)

    # Assert
    assert "❌ Test error" in result
    assert "💡 Hint: Try this fix" in result
    assert "📚 Docs: https://example.com/docs" in result


def test_append_to_file_missing_env(tmp_path, monkeypatch):
    """Test append_to_file raises error when env var not set."""
    # Arrange
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)

    # Act & Assert
    with pytest.raises(workflow_common.WorkflowError) as exc_info:
        workflow_common.append_to_file("GITHUB_OUTPUT", "test")

    assert "GITHUB_OUTPUT" in str(exc_info.value)


def test_write_output(tmp_path, monkeypatch):
    """Test write_output appends to GITHUB_OUTPUT file."""
    # Arrange
    output_file = tmp_path / "output.txt"
    output_file.write_text("")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    # Act
    workflow_common.write_output("my_var", "my_value")

    # Assert
    content = output_file.read_text()
    assert "my_var=my_value\n" in content


def test_get_repository_config_missing_file(tmp_path, monkeypatch):
    """Test get_repository_config raises error when config missing."""
    # Arrange
    monkeypatch.chdir(tmp_path)

    # Act & Assert
    with pytest.raises(workflow_common.WorkflowError) as exc_info:
        workflow_common.get_repository_config()

    assert "repository-config.yml not found" in str(exc_info.value)


def test_get_repository_config_caches_result(tmp_path, monkeypatch):
    """Test config is cached after first load."""
    # Arrange
    config_file = tmp_path / ".github" / "repository-config.yml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("test: value\n")
    monkeypatch.chdir(tmp_path)

    # Act
    config1 = workflow_common.get_repository_config()
    config2 = workflow_common.get_repository_config()

    # Assert
    assert config1 is config2  # Same object (cached)
    assert config1["test"] == "value"


def test_config_path_nested(tmp_path, monkeypatch):
    """Test config_path navigates nested dictionaries."""
    # Arrange
    config_file = tmp_path / ".github" / "repository-config.yml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("""
languages:
  versions:
    go: ["1.23", "1.24"]
""")
    monkeypatch.chdir(tmp_path)

    # Act
    result = workflow_common.config_path([], "languages", "versions", "go")

    # Assert
    assert result == ["1.23", "1.24"]


def test_config_path_uses_default(tmp_path, monkeypatch):
    """Test config_path returns default for missing keys."""
    # Arrange
    config_file = tmp_path / ".github" / "repository-config.yml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("empty: {}\n")
    monkeypatch.chdir(tmp_path)

    # Act
    result = workflow_common.config_path(42, "missing", "key")

    # Assert
    assert result == 42


def test_timed_operation(tmp_path, monkeypatch, capsys):
    """Test timed_operation prints duration."""
    # Arrange
    summary_file = tmp_path / "summary.md"
    summary_file.write_text("")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))

    # Act
    with workflow_common.timed_operation("Test operation"):
        pass  # Quick operation

    # Assert
    captured = capsys.readouterr()
    assert "⏱️  Test operation took" in captured.out
    summary = summary_file.read_text()
    assert "Test operation" in summary


def test_sanitize_log_masks_github_token():
    """Test sanitize_log masks GitHub tokens."""
    # Arrange
    message = "Token: ghp_abcdefghijklmnopqrstuvwxyz1234567890"

    # Act
    result = workflow_common.sanitize_log(message)

    # Assert
    assert "ghp_" not in result
    assert "***GITHUB_TOKEN***" in result


def test_ensure_file_creates_new_file(tmp_path):
    """Test ensure_file creates file if missing."""
    # Arrange
    target = tmp_path / "subdir" / "test.txt"

    # Act
    created = workflow_common.ensure_file(target, "content\n")

    # Assert
    assert created is True
    assert target.exists()
    assert target.read_text() == "content\n"


def test_ensure_file_idempotent(tmp_path):
    """Test ensure_file is idempotent (doesn't overwrite)."""
    # Arrange
    target = tmp_path / "test.txt"
    target.write_text("original\n")

    # Act
    created = workflow_common.ensure_file(target, "new content\n")

    # Assert
    assert created is False
    assert target.read_text() == "original\n"  # Unchanged
```

Create file: `tests/workflow_scripts/__init__.py`

```python
# file: tests/workflow_scripts/__init__.py
# version: 1.0.0
# guid: c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f

"""Test package for workflow scripts."""
```

### Verification Steps

```bash
# 1. Install test dependencies
pip install pytest pytest-cov pyyaml

# 2. Run tests
python -m pytest tests/workflow_scripts/test_workflow_common.py -v

# 3. Check coverage
python -m pytest tests/workflow_scripts/test_workflow_common.py --cov=workflow_common --cov-report=term-missing

# 4. Verify 100% coverage achieved
```

---

## Task 0.6: Create Feature Flag System

**Status**: Not Started
**Dependencies**: Task 0.1 (needs workflow_common)
**Estimated Time**: 30 minutes
**Idempotent**: Yes

### Description

Add feature flag helper functions to enable gradual rollout.

### Implementation

Add to `.github/workflows/scripts/workflow_common.py`:

```python
def get_feature_flag(flag_name: str, default: bool = False) -> bool:
    """
    Check if experimental feature is enabled.

    Args:
        flag_name: Feature flag name (e.g., "use_new_ci")
        default: Default value if flag not set

    Returns:
        True if feature enabled, False otherwise

    Example:
        >>> if get_feature_flag("use_new_ci"):
        ...     run_new_ci_workflow()
        ... else:
        ...     run_legacy_ci_workflow()
    """
    return config_path(default, "workflows", "experimental", flag_name)


def require_feature_flag(flag_name: str) -> None:
    """
    Exit if feature flag is not enabled.

    Args:
        flag_name: Required feature flag name

    Raises:
        WorkflowError: If feature not enabled

    Example:
        >>> require_feature_flag("use_config_matrices")
        # Continues if enabled, exits if disabled
    """
    if not get_feature_flag(flag_name):
        raise WorkflowError(
            f"Feature '{flag_name}' not enabled",
            hint=f"Enable in repository-config.yml: workflows.experimental.{flag_name}: true",
            docs_url="https://github.com/jdfalk/ghcommon/docs/refactors/workflows/v2/architecture.md#migration-strategy",
        )
```

### Verification Steps

```bash
# 1. Test with feature enabled
cat > /tmp/config-enabled.yml << 'EOF'
workflows:
  experimental:
    use_new_ci: true
EOF

python3 -c "
import sys
sys.path.insert(0, '.github/workflows/scripts')
import workflow_common
# Mock config
workflow_common._CONFIG_CACHE = {'workflows': {'experimental': {'use_new_ci': True}}}
assert workflow_common.get_feature_flag('use_new_ci') == True
print('✅ Feature flag enabled works')
"

# 2. Test with feature disabled
python3 -c "
import sys
sys.path.insert(0, '.github/workflows/scripts')
import workflow_common
workflow_common._CONFIG_CACHE = {'workflows': {'experimental': {'use_new_ci': False}}}
assert workflow_common.get_feature_flag('use_new_ci') == False
print('✅ Feature flag disabled works')
"
```

---

## Phase 0 Completion Checklist

- [ ] All 6 tasks completed
- [ ] All unit tests passing
- [ ] Code follows `.github/instructions/python.instructions.md`
- [ ] Security checklist completed
- [ ] Documentation updated
- [ ] No Windows references anywhere
- [ ] Git commit made with conventional commit message

## Commit Message Template

```
feat(workflows): implement Phase 0 foundation infrastructure

Implemented core workflow foundation with shared utilities, config validation,
security framework, and feature flags for gradual rollout.

Tasks completed:
- Task 0.1: Created workflow_common.py with shared utilities
- Task 0.2: Created JSON Schema for repository-config.yml
- Task 0.3: Created config validation script
- Task 0.4: Created security audit checklist
- Task 0.5: Created comprehensive unit tests (100% coverage)
- Task 0.6: Implemented feature flag system

Code style compliance:
- Follows .github/instructions/python.instructions.md
- Follows .github/instructions/general-coding.instructions.md
- All tasks independent and idempotent

Platforms: ubuntu-latest, macos-latest (NO WINDOWS)
Language versions: Go 1.23/1.24, Python 3.13/3.14
```

---

**Last Updated**: 2025-10-12
**Phase Owner**: Workflow Refactoring Team
**Status**: Ready for implementation
