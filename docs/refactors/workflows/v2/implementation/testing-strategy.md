<!-- file: docs/refactors/workflows/v2/implementation/testing-strategy.md -->
<!-- version: 1.0.0 -->
<!-- guid: c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f -->

# Testing Strategy Implementation Guide

## Overview

This guide provides comprehensive testing strategies for the v2 workflow system, covering unit tests, integration tests, workflow testing, and helper module validation.

**Target Audience**: Developers implementing and maintaining workflow tests
**Prerequisites**:
- Python 3.13+ and pytest installed
- Go 1.23+ for Go testing
- Rust stable for Rust testing
- Understanding of testing fundamentals

## Testing Pyramid

The v2 workflow system follows a testing pyramid approach:

```text
       /\
      /  \     E2E Tests (Few)
     /────\    - Full workflow runs
    /      \   - GitHub Actions integration
   /────────\  Integration Tests (Some)
  /          \ - Helper module interactions
 /────────────\ Unit Tests (Many)
/              \ - Individual functions
────────────────── - Pure logic
```

### Test Distribution

- **Unit Tests**: 70% - Fast, isolated, no dependencies
- **Integration Tests**: 25% - Module interactions, mocked APIs
- **E2E Tests**: 5% - Full workflows, actual GitHub Actions

## Unit Testing

### Helper Module Tests

Each helper module has comprehensive unit tests:

```text
.github/workflows/scripts/tests/
├── test_workflow_common.py      # Foundation functions
├── test_ci_workflow.py          # CI matrix and change detection
├── test_release_workflow.py     # Release version management
├── test_docs_workflow.py        # Documentation generation
├── test_maintenance_workflow.py # Dependency and security checks
└── test_automation_workflow.py  # GitHub Apps and caching
```

### Test Structure

Follow Arrange-Act-Assert pattern with Google Python Style Guide:

```python
#!/usr/bin/env python3
# file: .github/workflows/scripts/tests/test_example.py
# version: 1.0.0
# guid: d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a

"""Unit tests for example module.

This module tests the example functionality with comprehensive coverage
of normal operation, edge cases, and error conditions.
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import example_module


class TestExampleFunction(unittest.TestCase):
    """Test example_function with various inputs."""

    def setUp(self):
        """Set up test fixtures.

        This method is called before each test method. Use it to create
        common test data and mock objects.
        """
        self.test_data = {"key": "value"}
        self.mock_config = {"setting": True}

    def tearDown(self):
        """Clean up after each test.

        This method is called after each test method. Use it to clean up
        resources and reset state.
        """
        # Clean up temporary files, reset mocks, etc.
        pass

    def test_basic_functionality(self):
        """Test basic operation with valid inputs.

        Verifies that the function works correctly with standard inputs
        and returns expected output format.
        """
        # Arrange
        input_value = "test"
        expected_output = "processed_test"

        # Act
        result = example_module.example_function(input_value)

        # Assert
        self.assertEqual(result, expected_output)
        self.assertIsInstance(result, str)

    def test_edge_case_empty_input(self):
        """Test handling of empty input.

        Verifies that the function gracefully handles empty strings
        without raising exceptions.
        """
        # Arrange
        input_value = ""

        # Act
        result = example_module.example_function(input_value)

        # Assert
        self.assertEqual(result, "")

    def test_error_handling(self):
        """Test error handling for invalid input.

        Verifies that appropriate exceptions are raised for invalid
        input types or values.
        """
        # Arrange
        invalid_input = None

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            example_module.example_function(invalid_input)

        self.assertIn("Input cannot be None", str(context.exception))

    @patch("example_module.external_api_call")
    def test_with_mocked_dependency(self, mock_api):
        """Test function with mocked external dependency.

        Verifies function behavior when external API is mocked to return
        specific values.

        Args:
            mock_api: Mock object for external API calls.
        """
        # Arrange
        mock_api.return_value = {"status": "success"}
        input_value = "test"

        # Act
        result = example_module.example_function(input_value)

        # Assert
        mock_api.assert_called_once_with(input_value)
        self.assertEqual(result["status"], "success")


if __name__ == "__main__":
    unittest.main()
```

### Mocking Best Practices

**Mock external dependencies**:

```python
@patch("requests.get")
def test_github_api_call(self, mock_get):
    """Test GitHub API interaction with mocked response."""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_get.return_value = mock_response

    # Act
    result = workflow_common.fetch_github_data("test-repo")

    # Assert
    self.assertEqual(result["data"], "test")
    mock_get.assert_called_once()
```

**Mock file operations**:

```python
@patch("pathlib.Path.exists")
@patch("pathlib.Path.read_text")
def test_config_loading(self, mock_read, mock_exists):
    """Test configuration file loading."""
    # Arrange
    mock_exists.return_value = True
    mock_read.return_value = "key: value\n"

    # Act
    config = workflow_common.load_yaml_config("config.yml")

    # Assert
    self.assertEqual(config["key"], "value")
```

**Mock environment variables**:

```python
@patch.dict("os.environ", {
    "GITHUB_REPOSITORY": "owner/repo",
    "GITHUB_REF": "refs/heads/main"
})
def test_environment_detection(self):
    """Test branch detection from environment."""
    # Act
    branch = workflow_common.get_current_branch()

    # Assert
    self.assertEqual(branch, "main")
```

### Coverage Requirements

Maintain high test coverage:

```bash
# Run tests with coverage
pytest .github/workflows/scripts/tests/ \
  --cov=.github/workflows/scripts \
  --cov-report=html \
  --cov-report=term-missing

# Coverage requirements:
# - Overall: >= 90%
# - Per module: >= 85%
# - Critical paths: 100%
```

**Coverage configuration** (`.coveragerc`):

```ini
[run]
source = .github/workflows/scripts
omit =
    */tests/*
    */test_*.py

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
```

## Integration Testing

### Module Interaction Tests

Test how helper modules work together:

```python
#!/usr/bin/env python3
# file: .github/workflows/scripts/tests/test_integration.py
# version: 1.0.0
# guid: e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b

"""Integration tests for workflow system.

Tests interactions between multiple helper modules and validates
end-to-end scenarios.
"""

import unittest
from pathlib import Path
from unittest.mock import patch

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import workflow_common
import ci_workflow
import release_workflow


class TestCIReleaseIntegration(unittest.TestCase):
    """Test CI and release workflow integration."""

    @patch("workflow_common.load_yaml_config")
    def test_version_detection_for_release(self, mock_load):
        """Test version detection flows from CI to release.

        Verifies that version configuration loaded in CI can be used
        for release workflows.
        """
        # Arrange
        mock_load.return_value = {
            "version_policies": {
                "main": {
                    "go": {"versions": ["1.25"], "default": "1.25"}
                }
            }
        }

        # Act
        branch = "main"
        ci_config = ci_workflow.generate_matrix(branch, "go")
        release_version = release_workflow.get_target_version(branch, "go")

        # Assert
        self.assertIn("1.25", ci_config["matrix"]["go"])
        self.assertEqual(release_version, "1.25")

    def test_change_detection_triggers_appropriate_workflows(self):
        """Test that change detection correctly triggers workflows.

        Verifies that detected changes in specific file types trigger
        the appropriate workflow jobs.
        """
        # Arrange - simulate git diff with Go files changed
        with patch("ci_workflow.detect_changes") as mock_detect:
            mock_detect.return_value = {
                "go_files": ["main.go", "pkg/app/app.go"],
                "python_files": [],
                "has_code_changes": True
            }

            # Act
            changes = ci_workflow.detect_changes("main", "HEAD")

            # Assert
            self.assertTrue(changes["has_code_changes"])
            self.assertEqual(len(changes["go_files"]), 2)
            # Would trigger Go CI workflow


class TestMaintenanceDocumentationIntegration(unittest.TestCase):
    """Test maintenance and documentation workflow integration."""

    def test_dependency_update_triggers_documentation(self):
        """Test that dependency updates trigger doc regeneration.

        When dependencies are updated, documentation should be
        regenerated to reflect new API surfaces.
        """
        # This would be tested in actual workflow runs
        pass


if __name__ == "__main__":
    unittest.main()
```

### API Integration Tests

Test actual API interactions (requires credentials):

```python
@unittest.skipUnless(
    os.getenv("GITHUB_TOKEN"),
    "GitHub token required for API tests"
)
class TestGitHubAPIIntegration(unittest.TestCase):
    """Integration tests with real GitHub API."""

    def test_fetch_workflow_runs(self):
        """Test fetching actual workflow runs from API."""
        # Arrange
        repo = os.getenv("GITHUB_REPOSITORY", "owner/repo")

        # Act
        runs = automation_workflow.collect_workflow_metrics("ci.yml")

        # Assert
        self.assertIsInstance(runs, list)
        if runs:
            self.assertIn("workflow_name", runs[0].__dict__)
```

## Workflow Testing

### Local Workflow Validation

Use `act` to test workflows locally:

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Test specific workflow
act -W .github/workflows/ci.yml \
  -s GITHUB_TOKEN="$(gh auth token)" \
  --container-architecture linux/amd64

# Test specific job
act -W .github/workflows/ci.yml \
  -j test-go

# Dry run to see what would execute
act -W .github/workflows/ci.yml --dry-run
```

### Workflow Syntax Validation

Use `actionlint` to validate workflow syntax:

```bash
# Install actionlint
brew install actionlint  # macOS
# or
go install github.com/rhysd/actionlint/cmd/actionlint@latest

# Validate all workflows
actionlint .github/workflows/*.yml

# Validate specific workflow
actionlint .github/workflows/ci.yml

# With custom config
actionlint -config .github/actionlint.yml
```

**Actionlint configuration** (`.github/actionlint.yml`):

```yaml
self-hosted-runner:
  labels:
    - ubuntu-latest
    - macos-latest

config-variables:
  - GITHUB_TOKEN
  - GITHUB_REPOSITORY
```

### Workflow Test Matrix

Test workflows across different scenarios:

```yaml
# file: .github/workflows/test-workflows.yml
# version: 1.0.0

name: Test Workflows

on:
  pull_request:
    paths:
      - '.github/workflows/**'
      - '.github/workflows/scripts/**'

jobs:
  test-matrix-generation:
    name: Test CI Matrix Generation
    runs-on: ubuntu-latest
    strategy:
      matrix:
        branch: [main, stable-1-go-1.24, stable-1-go-1.23]
        language: [go, python, rust]
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Generate matrix
        run: |
          python .github/workflows/scripts/ci_workflow.py generate-matrix \
            --branch ${{ matrix.branch }} \
            --language ${{ matrix.language }}

      - name: Validate matrix output
        run: |
          # Verify JSON is valid and contains expected fields
          python -c "import json; json.loads(open('matrix.json').read())"

  test-change-detection:
    name: Test Change Detection
    runs-on: ubuntu-latest
    steps:
      - name: Checkout with history
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Test change detection
        run: |
          python .github/workflows/scripts/ci_workflow.py detect-changes \
            --base origin/main \
            --head HEAD

      - name: Verify outputs
        run: |
          # Check that expected outputs are present
          test -f changes.json
```

## Go Testing

### Test Organization

```text
pkg/
├── app/
│   ├── app.go
│   └── app_test.go       # Unit tests
├── integration/
│   └── app_test.go       # Integration tests
└── e2e/
    └── app_test.go       # End-to-end tests
```

### Unit Tests

```go
// file: pkg/app/app_test.go
// version: 1.0.0
// guid: f6a7b8c9-d0e1-2f3a-4b5c-6d7e8f9a0b1c

package app

import (
    "testing"
)

func TestProcessData(t *testing.T) {
    // Arrange
    input := "test data"
    expected := "processed: test data"

    // Act
    result := ProcessData(input)

    // Assert
    if result != expected {
        t.Errorf("ProcessData(%q) = %q; want %q", input, result, expected)
    }
}

// Table-driven tests
func TestProcessDataVariants(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        expected string
    }{
        {"empty", "", "processed: "},
        {"single word", "hello", "processed: hello"},
        {"multiple words", "hello world", "processed: hello world"},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := ProcessData(tt.input)
            if result != tt.expected {
                t.Errorf("got %q; want %q", result, tt.expected)
            }
        })
    }
}

// Benchmark tests (Go 1.24+)
func BenchmarkProcessData(b *testing.B) {
    input := "test data"
    b.ResetTimer()

    for i := range b.Loop() {
        _ = ProcessData(input)
    }
}
```

### Integration Tests

```go
// file: pkg/integration/app_test.go
// version: 1.0.0
// guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d

//go:build integration

package integration

import (
    "testing"
    "github.com/owner/repo/pkg/app"
)

func TestDatabaseIntegration(t *testing.T) {
    // Arrange
    db := setupTestDatabase(t)
    defer db.Close()

    // Act
    err := app.SaveData(db, "test")

    // Assert
    if err != nil {
        t.Fatalf("SaveData failed: %v", err)
    }
}
```

### Running Go Tests

```bash
# Unit tests only (fast)
go test -short ./...

# All tests
go test ./...

# Integration tests only
go test -tags=integration ./...

# With coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out

# Race detection
go test -race ./...

# Benchmarks
go test -bench=. ./...
```

## Rust Testing

### Test Organization

```rust
// file: src/lib.rs
// version: 1.0.0
// guid: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e

pub fn process_data(input: &str) -> String {
    format!("processed: {}", input)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_process_data() {
        // Arrange
        let input = "test";
        let expected = "processed: test";

        // Act
        let result = process_data(input);

        // Assert
        assert_eq!(result, expected);
    }

    #[test]
    #[should_panic(expected = "invalid input")]
    fn test_process_data_panics() {
        process_data("");
    }
}
```

### Integration Tests

```rust
// file: tests/integration_test.rs
// version: 1.0.0
// guid: c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f

use myapp;

#[test]
fn test_end_to_end_flow() {
    let input = "test data";
    let result = myapp::process_data(input);
    assert!(result.starts_with("processed:"));
}
```

### Running Rust Tests

```bash
# All tests
cargo test

# Specific test
cargo test test_process_data

# With output
cargo test -- --nocapture

# Integration tests only
cargo test --test integration_test

# Benchmarks
cargo bench
```

## Test Automation in CI

### Continuous Testing

Run tests on every commit:

```yaml
jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt

      - name: Run unit tests
        run: |
          pytest .github/workflows/scripts/tests/ -v

      - name: Run integration tests
        run: |
          pytest tests/integration/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### Fail-Fast vs Complete Testing

**Fail-fast** (quick feedback):

```yaml
strategy:
  fail-fast: true
  matrix:
    python: ['3.13', '3.14']
```

**Complete testing** (see all failures):

```yaml
strategy:
  fail-fast: false
  matrix:
    python: ['3.13', '3.14']
```

## Test Data Management

### Fixtures

Create reusable test fixtures:

```python
# file: .github/workflows/scripts/tests/fixtures.py
# version: 1.0.0
# guid: d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a

"""Test fixtures for workflow testing."""

import pytest


@pytest.fixture
def sample_workflow_config():
    """Provide sample workflow configuration."""
    return {
        "version_policies": {
            "main": {
                "go": {"versions": ["1.25"], "default": "1.25"}
            }
        }
    }


@pytest.fixture
def mock_github_api(monkeypatch):
    """Mock GitHub API responses."""
    def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"data": "test"}
        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get)
```

Use fixtures in tests:

```python
def test_with_fixture(sample_workflow_config):
    """Test using fixture data."""
    config = sample_workflow_config
    assert "main" in config["version_policies"]
```

## Performance Testing

### Benchmark Workflows

Test workflow execution time:

```python
import time
import pytest


@pytest.mark.benchmark
def test_matrix_generation_performance(benchmark):
    """Benchmark matrix generation speed."""
    def generate():
        return ci_workflow.generate_matrix("main", "go")

    result = benchmark(generate)
    assert result is not None
```

### Load Testing

Test with large datasets:

```python
def test_large_repository_handling():
    """Test change detection with large number of files."""
    # Simulate 1000 changed files
    files = [f"file{i}.go" for i in range(1000)]

    start = time.time()
    result = ci_workflow.detect_changes_for_files(files)
    duration = time.time() - start

    # Should complete in under 5 seconds
    assert duration < 5.0
```

## Troubleshooting Tests

### Common Issues

#### Test fails locally but passes in CI

```bash
# Ensure same Python version
python --version

# Check dependencies
pip list

# Clear cache
pytest --cache-clear
```

#### Flaky tests

```python
# Add retry decorator for flaky tests
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_api_call():
    # Test that might fail intermittently
    pass
```

#### Slow tests

```python
# Mark slow tests
@pytest.mark.slow
def test_comprehensive_integration():
    pass

# Run without slow tests
# pytest -m "not slow"
```

## Best Practices

1. **Write tests first** (TDD when possible)
2. **One assertion per test** (or closely related assertions)
3. **Clear test names** describing what is tested
4. **Arrange-Act-Assert** pattern consistently
5. **Mock external dependencies** for unit tests
6. **Test edge cases** and error conditions
7. **Maintain >= 90% coverage** for critical code
8. **Fast tests** (unit tests < 1s, integration < 10s)
9. **Deterministic tests** (no random failures)
10. **Clean up** after tests (temp files, mocks)

## Next Steps

1. Set up pytest with coverage reporting
2. Write unit tests for all helper modules
3. Add integration tests for module interactions
4. Configure CI to run tests automatically
5. Set up coverage reporting (Codecov)
6. Read [Migration Guide](../operations/migration-guide.md)

## References

- [Phase 0: Foundation](../phases/phase-0-foundation.md)
- [All Phase Documents](../phases/)
- [Helper Scripts API](../reference/helper-scripts-api.md)
- [CI Workflows Guide](ci-workflows.md)
- [pytest Documentation](https://docs.pytest.org/)
- [Go Testing](https://go.dev/doc/tutorial/add-a-test)
- [Rust Testing](https://doc.rust-lang.org/book/ch11-00-testing.html)
