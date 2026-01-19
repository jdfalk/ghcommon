<!-- file: docs/cross-registry-todos/task-13/t13-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t13-testing-automation-part2-m4n5o6p7-q8r9 -->
<!-- last-edited: 2026-01-19 -->

# Task 13 Part 2: Python and JavaScript Testing Automation

## Python Testing Infrastructure

### Pytest Configuration

```toml
# file: pyproject.toml
# version: 2.1.0
# guid: python-test-configuration

[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ghcommon-scripts"
version = "1.0.0"
description = "GitHub common workflow scripts"
dependencies = [
    "requests>=2.31.0",
    "pyyaml>=6.0.1",
    "click>=8.1.7",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "pytest-asyncio>=0.21.1",
    "pytest-xdist>=3.5.0",
    "pytest-timeout>=2.2.0",
    "hypothesis>=6.92.0",
    "freezegun>=1.4.0",
    "responses>=0.24.1",
]

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--cov=scripts",
    "--cov-branch",
    "--cov-report=term-missing:skip-covered",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=80",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "api: marks tests that call external APIs",
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["scripts"]
branch = true
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__pycache__/*",
    "*/venv/*",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]

[tool.coverage.html]
directory = "htmlcov"
```

### Python Unit Test Template

```python
#!/usr/bin/env python3
# file: tests/test_workflow_debugger.py
# version: 1.0.0
# guid: python-unit-test-example

"""Unit tests for workflow_debugger.py"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
from datetime import datetime, timedelta

# Assuming workflow_debugger.py exists
from scripts.workflow_debugger import (
    WorkflowDebugger,
    WorkflowFailure,
    FailureCategory,
)


class TestWorkflowFailure:
    """Test suite for WorkflowFailure dataclass"""

    @pytest.fixture
    def sample_failure(self):
        """Fixture providing sample failure data"""
        return WorkflowFailure(
            repo="jdfalk/ghcommon",
            workflow="CI",
            run_id=12345,
            status="failure",
            category=FailureCategory.PERMISSIONS,
            error_message="Permission denied",
            failed_at=datetime.now(),
        )

    def test_failure_initialization(self, sample_failure):
        """Test WorkflowFailure can be initialized correctly"""
        # Assert
        assert sample_failure.repo == "jdfalk/ghcommon"
        assert sample_failure.workflow == "CI"
        assert sample_failure.run_id == 12345
        assert sample_failure.category == FailureCategory.PERMISSIONS

    def test_failure_to_dict(self, sample_failure):
        """Test WorkflowFailure serialization to dict"""
        # Act
        result = sample_failure.to_dict()

        # Assert
        assert isinstance(result, dict)
        assert result["repo"] == "jdfalk/ghcommon"
        assert result["run_id"] == 12345
        assert "category" in result


class TestWorkflowDebugger:
    """Test suite for WorkflowDebugger class"""

    @pytest.fixture
    def debugger(self):
        """Fixture providing WorkflowDebugger instance"""
        return WorkflowDebugger(org="jdfalk", token="test-token")

    @pytest.fixture
    def mock_github_response(self):
        """Fixture providing mock GitHub API response"""
        return {
            "total_count": 2,
            "workflow_runs": [
                {
                    "id": 12345,
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "failure",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:10:00Z",
                },
                {
                    "id": 12346,
                    "name": "Release",
                    "status": "completed",
                    "conclusion": "success",
                    "created_at": "2024-01-01T01:00:00Z",
                    "updated_at": "2024-01-01T01:15:00Z",
                },
            ]
        }

    def test_debugger_initialization(self, debugger):
        """Test WorkflowDebugger initializes correctly"""
        # Assert
        assert debugger.org == "jdfalk"
        assert debugger.token == "test-token"
        assert hasattr(debugger, "session")

    @patch("scripts.workflow_debugger.requests.Session")
    def test_fetch_workflow_runs_success(
        self, mock_session, debugger, mock_github_response
    ):
        """Test fetching workflow runs from GitHub API"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_github_response
        mock_session.return_value.get.return_value = mock_response
        debugger.session = mock_session.return_value

        # Act
        result = debugger.fetch_workflow_runs("ghcommon")

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == 12345
        assert result[0]["conclusion"] == "failure"

    @patch("scripts.workflow_debugger.requests.Session")
    def test_fetch_workflow_runs_api_error(self, mock_session, debugger):
        """Test handling of API errors"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_session.return_value.get.return_value = mock_response
        debugger.session = mock_session.return_value

        # Act & Assert
        with pytest.raises(Exception, match="Not found"):
            debugger.fetch_workflow_runs("nonexistent-repo")

    def test_categorize_failure_permissions(self, debugger):
        """Test categorizing permission-related failures"""
        # Arrange
        error_log = """
        Error: Permission denied
        Resource not accessible by integration
        """

        # Act
        category = debugger.categorize_failure(error_log)

        # Assert
        assert category == FailureCategory.PERMISSIONS

    def test_categorize_failure_dependencies(self, debugger):
        """Test categorizing dependency-related failures"""
        # Arrange
        error_log = """
        Error: Failed to install package 'xyz'
        Could not find a version that satisfies the requirement
        """

        # Act
        category = debugger.categorize_failure(error_log)

        # Assert
        assert category == FailureCategory.DEPENDENCIES

    @pytest.mark.parametrize("error_msg,expected_category", [
        ("YAML syntax error on line 42", FailureCategory.SYNTAX),
        ("Disk space quota exceeded", FailureCategory.INFRASTRUCTURE),
        ("Connection timeout", FailureCategory.INFRASTRUCTURE),
        ("Unknown error occurred", FailureCategory.UNKNOWN),
    ])
    def test_categorize_failure_parametrized(
        self, debugger, error_msg, expected_category
    ):
        """Test failure categorization with multiple cases"""
        # Act
        category = debugger.categorize_failure(error_msg)

        # Assert
        assert category == expected_category

    @patch("scripts.workflow_debugger.Path.write_text")
    def test_generate_fix_task(self, mock_write, debugger, sample_failure):
        """Test fix task generation"""
        # Arrange
        output_dir = Path("/tmp/fix-tasks")

        # Act
        debugger.generate_fix_task(sample_failure, output_dir)

        # Assert
        mock_write.assert_called_once()
        call_args = mock_write.call_args[0][0]
        task_data = json.loads(call_args)
        assert task_data["repo"] == "jdfalk/ghcommon"
        assert task_data["category"] == "PERMISSIONS"


class TestWorkflowDebuggerIntegration:
    """Integration tests for WorkflowDebugger"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_scan_workflow(self, tmp_path):
        """Test complete scan workflow (requires valid GitHub token)"""
        # Arrange
        debugger = WorkflowDebugger(
            org="jdfalk",
            token="dummy-token",  # Would use real token in actual integration test
        )
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Act (would call real API in integration test)
        # result = debugger.scan_all_repos(output_dir)

        # Assert (placeholder)
        assert output_dir.exists()


# Property-based testing with Hypothesis
from hypothesis import given, strategies as st

class TestWorkflowDebuggerProperties:
    """Property-based tests for WorkflowDebugger"""

    @given(
        repo=st.text(min_size=1, max_size=100),
        run_id=st.integers(min_value=1, max_value=1000000),
    )
    def test_failure_creation_always_valid(self, repo, run_id):
        """Property: Any valid repo and run_id should create valid failure"""
        # Arrange & Act
        failure = WorkflowFailure(
            repo=repo,
            workflow="Test",
            run_id=run_id,
            status="failure",
            category=FailureCategory.UNKNOWN,
            error_message="Test error",
            failed_at=datetime.now(),
        )

        # Assert
        assert failure.repo == repo
        assert failure.run_id == run_id
        assert failure.category in FailureCategory
```

### Python Async Test Template

```python
#!/usr/bin/env python3
# file: tests/test_async_operations.py
# version: 1.0.0
# guid: python-async-test-example

"""Async operation tests"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import aiohttp


class TestAsyncAPIClient:
    """Test suite for async API operations"""

    @pytest.fixture
    async def client(self):
        """Fixture providing async HTTP client"""
        async with aiohttp.ClientSession() as session:
            yield session

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, client):
        """Test successful async data fetch"""
        # Arrange
        url = "https://api.github.com/repos/jdfalk/ghcommon"

        # Act
        async with client.get(url) as response:
            data = await response.json()

        # Assert (would use mocked response in real test)
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test multiple concurrent async requests"""
        # Arrange
        urls = [
            "https://api.github.com/repos/jdfalk/ghcommon",
            "https://api.github.com/repos/jdfalk/ubuntu-autoinstall-agent",
        ]

        async def fetch(session, url):
            async with session.get(url) as response:
                return await response.json()

        # Act
        async with aiohttp.ClientSession() as session:
            tasks = [fetch(session, url) for url in urls]
            results = await asyncio.gather(*tasks)

        # Assert
        assert len(results) == 2

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_request_timeout(self):
        """Test async request timeout handling"""
        # Arrange
        async def slow_operation():
            await asyncio.sleep(10)  # Intentionally slow
            return "done"

        # Act & Assert
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_operation(), timeout=1.0)
```

## JavaScript/TypeScript Testing Infrastructure

### Vitest Configuration

```typescript
// file: vitest.config.ts
// version: 1.0.0
// guid: vitest-configuration

import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'dist/',
        '**/*.test.ts',
        '**/*.spec.ts',
        '**/types/**',
      ],
      all: true,
      lines: 80,
      functions: 80,
      branches: 80,
      statements: 80,
    },
    include: ['**/*.{test,spec}.{js,ts,jsx,tsx}'],
    exclude: ['node_modules', 'dist', '.next'],
    setupFiles: ['./tests/setup.ts'],
    testTimeout: 10000,
    hookTimeout: 10000,
    teardownTimeout: 5000,
    isolate: true,
    maxConcurrency: 5,
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@tests': path.resolve(__dirname, './tests'),
    },
  },
});
```

### JavaScript Unit Test Template

```typescript
// file: tests/workflow-parser.test.ts
// version: 1.0.0
// guid: javascript-unit-test-example

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { WorkflowParser, WorkflowConfig } from '@/workflow-parser';
import fs from 'fs/promises';
import path from 'path';

describe('WorkflowParser', () => {
  let parser: WorkflowParser;

  beforeEach(() => {
    parser = new WorkflowParser();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('parseYaml', () => {
    it('should parse valid YAML workflow', () => {
      // Arrange
      const yaml = `
        name: CI
        on: [push, pull_request]
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
      `;

      // Act
      const result = parser.parseYaml(yaml);

      // Assert
      expect(result).toBeDefined();
      expect(result.name).toBe('CI');
      expect(result.on).toContain('push');
    });

    it('should throw error on invalid YAML', () => {
      // Arrange
      const invalidYaml = 'invalid: yaml: syntax:';

      // Act & Assert
      expect(() => parser.parseYaml(invalidYaml)).toThrow();
    });
  });

  describe('validateWorkflow', () => {
    it('should validate workflow with required fields', () => {
      // Arrange
      const config: WorkflowConfig = {
        name: 'CI',
        on: ['push'],
        jobs: {
          test: {
            'runs-on': 'ubuntu-latest',
            steps: [{ uses: 'actions/checkout@v4' }],
          },
        },
      };

      // Act
      const result = parser.validateWorkflow(config);

      // Assert
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should detect missing required fields', () => {
      // Arrange
      const config = {
        name: 'CI',
        // Missing 'on' and 'jobs'
      } as WorkflowConfig;

      // Act
      const result = parser.validateWorkflow(config);

      // Assert
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing required field: on');
      expect(result.errors).toContain('Missing required field: jobs');
    });
  });

  describe('extractSecrets', () => {
    it('should extract secrets from workflow steps', () => {
      // Arrange
      const config: WorkflowConfig = {
        name: 'CI',
        on: ['push'],
        jobs: {
          test: {
            'runs-on': 'ubuntu-latest',
            steps: [
              {
                run: 'echo ${{ secrets.GITHUB_TOKEN }}',
              },
              {
                env: {
                  API_KEY: '${{ secrets.API_KEY }}',
                },
              },
            ],
          },
        },
      };

      // Act
      const secrets = parser.extractSecrets(config);

      // Assert
      expect(secrets).toContain('GITHUB_TOKEN');
      expect(secrets).toContain('API_KEY');
      expect(secrets).toHaveLength(2);
    });
  });
});

describe('WorkflowParser Integration', () => {
  it('should parse real workflow file', async () => {
    // Arrange
    const parser = new WorkflowParser();
    const workflowPath = path.join(__dirname, '../.github/workflows/ci.yml');

    // Act
    const content = await fs.readFile(workflowPath, 'utf-8');
    const config = parser.parseYaml(content);
    const validation = parser.validateWorkflow(config);

    // Assert
    expect(validation.valid).toBe(true);
    expect(config.name).toBeDefined();
  });
});

// Mocking example
describe('WorkflowParser with Mocks', () => {
  it('should use mocked file system', async () => {
    // Arrange
    const mockReadFile = vi.spyOn(fs, 'readFile');
    mockReadFile.mockResolvedValue('name: Test\non: push\njobs: {}');

    const parser = new WorkflowParser();

    // Act
    const content = await fs.readFile('fake-path.yml', 'utf-8');
    const config = parser.parseYaml(content);

    // Assert
    expect(mockReadFile).toHaveBeenCalledWith('fake-path.yml', 'utf-8');
    expect(config.name).toBe('Test');

    // Cleanup
    mockReadFile.mockRestore();
  });
});
```

### React Component Test Template

```typescript
// file: tests/WorkflowStatus.test.tsx
// version: 1.0.0
// guid: react-component-test-example

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkflowStatus } from '@/components/WorkflowStatus';
import type { WorkflowRun } from '@/types';

describe('WorkflowStatus Component', () => {
  const mockWorkflow: WorkflowRun = {
    id: 12345,
    name: 'CI',
    status: 'completed',
    conclusion: 'success',
    createdAt: '2024-01-01T00:00:00Z',
  };

  it('should render workflow name', () => {
    // Arrange & Act
    render(<WorkflowStatus workflow={mockWorkflow} />);

    // Assert
    expect(screen.getByText('CI')).toBeInTheDocument();
  });

  it('should show success status', () => {
    // Arrange & Act
    render(<WorkflowStatus workflow={mockWorkflow} />);

    // Assert
    const statusBadge = screen.getByTestId('status-badge');
    expect(statusBadge).toHaveClass('bg-green-500');
    expect(screen.getByText('success')).toBeInTheDocument();
  });

  it('should handle click event', async () => {
    // Arrange
    const handleClick = vi.fn();
    render(<WorkflowStatus workflow={mockWorkflow} onClick={handleClick} />);

    // Act
    const button = screen.getByRole('button');
    fireEvent.click(button);

    // Assert
    await waitFor(() => {
      expect(handleClick).toHaveBeenCalledTimes(1);
      expect(handleClick).toHaveBeenCalledWith(mockWorkflow.id);
    });
  });

  it('should render loading state', () => {
    // Arrange
    const loadingWorkflow = { ...mockWorkflow, status: 'in_progress' };

    // Act
    render(<WorkflowStatus workflow={loadingWorkflow} />);

    // Assert
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });
});
```

---

**Part 2 Complete**: Python testing (pytest, async tests, property-based testing with Hypothesis),
JavaScript/TypeScript testing (Vitest, React Testing Library, mocking). ✅

**Continue to Part 3** for coverage enforcement and test automation workflows.
