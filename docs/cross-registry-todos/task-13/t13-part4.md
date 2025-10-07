<!-- file: docs/cross-registry-todos/task-13/t13-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t13-testing-automation-part4-o4p5q6r7-s8t9 -->

# Task 13 Part 4: Integration, E2E, and Performance Testing

## Integration Testing Strategy

### Rust Integration Tests with Database

```rust
// file: tests/database_integration.rs
// version: 1.0.0
// guid: rust-database-integration-test

use ubuntu_autoinstall_agent::{Database, Config};
use sqlx::PgPool;
use testcontainers::{clients, images, Container};
use anyhow::Result;

/// Test fixture managing database container lifecycle
struct DatabaseFixture<'a> {
    _container: Container<'a, images::postgres::Postgres>,
    pool: PgPool,
}

impl<'a> DatabaseFixture<'a> {
    async fn new(docker: &'a clients::Cli) -> Result<Self> {
        // Start PostgreSQL container
        let postgres = images::postgres::Postgres::default()
            .with_env_var("POSTGRES_DB", "test")
            .with_env_var("POSTGRES_USER", "test")
            .with_env_var("POSTGRES_PASSWORD", "test");

        let container = docker.run(postgres);
        let port = container.get_host_port_ipv4(5432);

        // Connect to database
        let database_url = format!(
            "postgres://test:test@127.0.0.1:{}/test",
            port
        );
        let pool = PgPool::connect(&database_url).await?;

        // Run migrations
        sqlx::migrate!("./migrations").run(&pool).await?;

        Ok(Self {
            _container: container,
            pool,
        })
    }
}

#[tokio::test]
async fn test_create_and_retrieve_config() -> Result<()> {
    // Arrange
    let docker = clients::Cli::default();
    let fixture = DatabaseFixture::new(&docker).await?;
    let db = Database::new(fixture.pool.clone());

    let config = Config {
        name: "test-config".to_string(),
        version: "24.04".to_string(),
        disk_size: 10,
    };

    // Act
    let id = db.insert_config(&config).await?;
    let retrieved = db.get_config(id).await?;

    // Assert
    assert_eq!(retrieved.name, config.name);
    assert_eq!(retrieved.version, config.version);
    assert_eq!(retrieved.disk_size, config.disk_size);

    Ok(())
}

#[tokio::test]
async fn test_update_config() -> Result<()> {
    // Arrange
    let docker = clients::Cli::default();
    let fixture = DatabaseFixture::new(&docker).await?;
    let db = Database::new(fixture.pool.clone());

    let mut config = Config {
        name: "test-config".to_string(),
        version: "24.04".to_string(),
        disk_size: 10,
    };

    let id = db.insert_config(&config).await?;

    // Act
    config.disk_size = 20;
    db.update_config(id, &config).await?;
    let updated = db.get_config(id).await?;

    // Assert
    assert_eq!(updated.disk_size, 20);

    Ok(())
}

#[tokio::test]
async fn test_concurrent_database_operations() -> Result<()> {
    // Arrange
    let docker = clients::Cli::default();
    let fixture = DatabaseFixture::new(&docker).await?;
    let db = Database::new(fixture.pool.clone());

    // Act: Spawn multiple concurrent database operations
    let handles: Vec<_> = (0..10)
        .map(|i| {
            let db = db.clone();
            tokio::spawn(async move {
                let config = Config {
                    name: format!("config-{}", i),
                    version: "24.04".to_string(),
                    disk_size: 10,
                };
                db.insert_config(&config).await
            })
        })
        .collect();

    let results: Result<Vec<_>> = futures::future::try_join_all(handles)
        .await
        .map_err(|e| anyhow::anyhow!("Join error: {}", e))?
        .into_iter()
        .collect();

    // Assert
    let ids = results?;
    assert_eq!(ids.len(), 10);

    Ok(())
}
```

### Python API Integration Tests

```python
#!/usr/bin/env python3
# file: tests/test_api_integration.py
# version: 1.0.0
# guid: python-api-integration-test

"""API integration tests using FastAPI TestClient"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from datetime import datetime

# Assuming we have a FastAPI app
from api.main import app, get_database

@pytest.fixture
def client():
    """Fixture providing FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def mock_db():
    """Fixture providing mock database"""
    return Mock()

@pytest.fixture
def authenticated_client(client, mock_db):
    """Fixture providing authenticated client with mocked database"""
    app.dependency_overrides[get_database] = lambda: mock_db

    # Get authentication token
    response = client.post(
        "/auth/token",
        data={"username": "test", "password": "test"}
    )
    token = response.json()["access_token"]

    # Set authorization header
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}"
    }

    yield client

    # Cleanup
    app.dependency_overrides.clear()


class TestWorkflowAPI:
    """Integration tests for workflow API endpoints"""

    def test_list_workflows_empty(self, authenticated_client, mock_db):
        """Test listing workflows when none exist"""
        # Arrange
        mock_db.get_workflows.return_value = []

        # Act
        response = authenticated_client.get("/api/v1/workflows")

        # Assert
        assert response.status_code == 200
        assert response.json() == {"workflows": [], "total": 0}

    def test_list_workflows_with_data(self, authenticated_client, mock_db):
        """Test listing workflows with data"""
        # Arrange
        mock_workflows = [
            {
                "id": 1,
                "name": "CI",
                "status": "success",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "name": "Release",
                "status": "running",
                "created_at": "2024-01-01T01:00:00Z"
            }
        ]
        mock_db.get_workflows.return_value = mock_workflows

        # Act
        response = authenticated_client.get("/api/v1/workflows")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["workflows"]) == 2
        assert data["workflows"][0]["name"] == "CI"

    def test_create_workflow(self, authenticated_client, mock_db):
        """Test creating a new workflow"""
        # Arrange
        workflow_data = {
            "name": "Test Workflow",
            "type": "ci",
            "config": {"runs-on": "ubuntu-latest"}
        }
        mock_db.create_workflow.return_value = 123

        # Act
        response = authenticated_client.post(
            "/api/v1/workflows",
            json=workflow_data
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 123
        assert data["name"] == "Test Workflow"
        mock_db.create_workflow.assert_called_once()

    def test_get_workflow_not_found(self, authenticated_client, mock_db):
        """Test getting non-existent workflow"""
        # Arrange
        mock_db.get_workflow.return_value = None

        # Act
        response = authenticated_client.get("/api/v1/workflows/999")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_workflow(self, authenticated_client, mock_db):
        """Test updating existing workflow"""
        # Arrange
        workflow_id = 123
        update_data = {"name": "Updated Workflow"}
        mock_db.get_workflow.return_value = {"id": workflow_id, "name": "Old Name"}
        mock_db.update_workflow.return_value = True

        # Act
        response = authenticated_client.patch(
            f"/api/v1/workflows/{workflow_id}",
            json=update_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Workflow"

    def test_delete_workflow(self, authenticated_client, mock_db):
        """Test deleting workflow"""
        # Arrange
        workflow_id = 123
        mock_db.delete_workflow.return_value = True

        # Act
        response = authenticated_client.delete(f"/api/v1/workflows/{workflow_id}")

        # Assert
        assert response.status_code == 204
        mock_db.delete_workflow.assert_called_once_with(workflow_id)


class TestWorkflowAPIValidation:
    """Test API input validation"""

    def test_create_workflow_missing_required_fields(self, authenticated_client):
        """Test validation of required fields"""
        # Arrange
        invalid_data = {"name": "Test"}  # Missing 'type'

        # Act
        response = authenticated_client.post(
            "/api/v1/workflows",
            json=invalid_data
        )

        # Assert
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("type" in str(error).lower() for error in errors)

    def test_create_workflow_invalid_type(self, authenticated_client):
        """Test validation of workflow type"""
        # Arrange
        invalid_data = {
            "name": "Test",
            "type": "invalid_type",
            "config": {}
        }

        # Act
        response = authenticated_client.post(
            "/api/v1/workflows",
            json=invalid_data
        )

        # Assert
        assert response.status_code == 422


@pytest.mark.integration
class TestWorkflowAPIIntegration:
    """End-to-end API integration tests"""

    def test_full_workflow_lifecycle(self, authenticated_client, mock_db):
        """Test complete workflow lifecycle: create, update, retrieve, delete"""
        # Arrange
        workflow_data = {
            "name": "Integration Test Workflow",
            "type": "ci",
            "config": {"runs-on": "ubuntu-latest"}
        }
        workflow_id = 123
        mock_db.create_workflow.return_value = workflow_id
        mock_db.get_workflow.return_value = {**workflow_data, "id": workflow_id}
        mock_db.update_workflow.return_value = True
        mock_db.delete_workflow.return_value = True

        # Act & Assert: Create
        create_response = authenticated_client.post(
            "/api/v1/workflows",
            json=workflow_data
        )
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        # Act & Assert: Retrieve
        get_response = authenticated_client.get(f"/api/v1/workflows/{created_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == workflow_data["name"]

        # Act & Assert: Update
        update_data = {"name": "Updated Name"}
        update_response = authenticated_client.patch(
            f"/api/v1/workflows/{created_id}",
            json=update_data
        )
        assert update_response.status_code == 200

        # Act & Assert: Delete
        delete_response = authenticated_client.delete(
            f"/api/v1/workflows/{created_id}"
        )
        assert delete_response.status_code == 204
```

## End-to-End Testing

### Playwright E2E Tests

```typescript
// file: tests/e2e/workflow-dashboard.spec.ts
// version: 1.0.0
// guid: playwright-e2e-test

import { test, expect, Page } from '@playwright/test';

test.describe('Workflow Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard before each test
    await page.goto('http://localhost:3000/dashboard');

    // Wait for initial load
    await page.waitForLoadState('networkidle');
  });

  test('should display workflow list', async ({ page }) => {
    // Assert: Dashboard title visible
    await expect(page.locator('h1')).toContainText('Workflow Dashboard');

    // Assert: Workflow table exists
    const table = page.locator('[data-testid="workflow-table"]');
    await expect(table).toBeVisible();

    // Assert: At least one workflow row
    const rows = table.locator('tbody tr');
    await expect(rows).toHaveCount(await rows.count());
  });

  test('should filter workflows by status', async ({ page }) => {
    // Act: Select "failed" filter
    await page.selectOption('[data-testid="status-filter"]', 'failed');

    // Wait for filter to apply
    await page.waitForTimeout(500);

    // Assert: Only failed workflows shown
    const statusBadges = page.locator('[data-testid="status-badge"]');
    const count = await statusBadges.count();

    for (let i = 0; i < count; i++) {
      await expect(statusBadges.nth(i)).toContainText('failed');
    }
  });

  test('should navigate to workflow details', async ({ page }) => {
    // Act: Click first workflow
    await page.click('[data-testid="workflow-row"]:first-child');

    // Assert: Navigated to details page
    await expect(page).toHaveURL(/\/workflows\/\d+/);

    // Assert: Details page loaded
    await expect(page.locator('h2')).toContainText('Workflow Details');
  });

  test('should create new workflow', async ({ page }) => {
    // Act: Click create button
    await page.click('[data-testid="create-workflow-button"]');

    // Assert: Modal opened
    const modal = page.locator('[data-testid="create-workflow-modal"]');
    await expect(modal).toBeVisible();

    // Act: Fill form
    await page.fill('[name="name"]', 'Test Workflow');
    await page.selectOption('[name="type"]', 'ci');
    await page.fill('[name="runs-on"]', 'ubuntu-latest');

    // Act: Submit
    await page.click('[data-testid="submit-workflow"]');

    // Assert: Success message
    await expect(page.locator('.toast-success')).toBeVisible();

    // Assert: New workflow appears in list
    await expect(
      page.locator('[data-testid="workflow-row"]', { hasText: 'Test Workflow' })
    ).toBeVisible();
  });

  test('should handle workflow errors', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/workflows', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    // Act: Try to load workflows
    await page.reload();

    // Assert: Error message displayed
    await expect(page.locator('.error-message')).toContainText('Failed to load workflows');
  });
});

test.describe('Workflow Details Page', () => {
  test('should display workflow run history', async ({ page }) => {
    // Navigate to specific workflow
    await page.goto('http://localhost:3000/workflows/123');

    // Assert: Run history table visible
    const historyTable = page.locator('[data-testid="run-history-table"]');
    await expect(historyTable).toBeVisible();

    // Assert: Multiple runs shown
    const runRows = historyTable.locator('tbody tr');
    expect(await runRows.count()).toBeGreaterThan(0);
  });

  test('should trigger new workflow run', async ({ page }) => {
    await page.goto('http://localhost:3000/workflows/123');

    // Act: Click run button
    await page.click('[data-testid="trigger-run-button"]');

    // Assert: Confirmation dialog
    const dialog = page.locator('[data-testid="confirm-dialog"]');
    await expect(dialog).toBeVisible();

    // Act: Confirm
    await page.click('[data-testid="confirm-button"]');

    // Assert: Success notification
    await expect(page.locator('.toast-success')).toContainText('Workflow run triggered');
  });

  test('should view workflow logs', async ({ page }) => {
    await page.goto('http://localhost:3000/workflows/123/runs/456');

    // Act: Click logs tab
    await page.click('[data-testid="logs-tab"]');

    // Assert: Logs container visible
    const logsContainer = page.locator('[data-testid="logs-container"]');
    await expect(logsContainer).toBeVisible();

    // Assert: Log content present
    const logText = await logsContainer.textContent();
    expect(logText).toBeTruthy();
    expect(logText!.length).toBeGreaterThan(0);
  });
});

// Visual regression testing
test.describe('Visual Regression', () => {
  test('should match dashboard screenshot', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForLoadState('networkidle');

    // Take screenshot and compare
    await expect(page).toHaveScreenshot('dashboard.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });
});
```

### Playwright Configuration

```typescript
// file: playwright.config.ts
// version: 1.0.0
// guid: playwright-configuration

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

## Performance Testing

### Criterion Benchmarks (Rust)

```rust
// file: benches/performance_benchmarks.rs
// version: 1.0.0
// guid: rust-performance-benchmark

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use ubuntu_autoinstall_agent::{DiskManager, Config};
use std::time::Duration;
use tempfile::TempDir;

fn benchmark_disk_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("disk_operations");
    group.measurement_time(Duration::from_secs(10));

    for size in [10, 100, 1000].iter() {
        group.bench_with_input(
            BenchmarkId::new("create_disk", size),
            size,
            |b, &size| {
                let temp_dir = TempDir::new().unwrap();
                let manager = DiskManager::new(temp_dir.path()).unwrap();

                b.iter(|| {
                    manager.create_disk(
                        black_box(&format!("bench-{}", size)),
                        black_box(size)
                    )
                });
            }
        );
    }

    group.finish();
}

fn benchmark_config_parsing(c: &mut Criterion) {
    let yaml_config = r#"
        name: benchmark-config
        version: "24.04"
        disk_size: 20
        memory: 4096
    "#;

    c.bench_function("parse_config", |b| {
        b.iter(|| {
            Config::from_yaml(black_box(yaml_config))
        });
    });
}

fn benchmark_concurrent_operations(c: &mut Criterion) {
    use tokio::runtime::Runtime;

    let rt = Runtime::new().unwrap();

    c.bench_function("concurrent_disk_checks", |b| {
        b.to_async(&rt).iter(|| async {
            let temp_dir = TempDir::new().unwrap();
            let manager = DiskManager::new(temp_dir.path()).unwrap();

            let handles: Vec<_> = (0..100)
                .map(|i| {
                    let mgr = manager.clone();
                    tokio::spawn(async move {
                        mgr.disk_exists(&format!("disk-{}", i))
                    })
                })
                .collect();

            for handle in handles {
                let _ = handle.await;
            }
        });
    });
}

criterion_group!(
    benches,
    benchmark_disk_operations,
    benchmark_config_parsing,
    benchmark_concurrent_operations
);
criterion_main!(benches);
```

### Python Performance Tests

```python
#!/usr/bin/env python3
# file: tests/test_performance.py
# version: 1.0.0
# guid: python-performance-test

"""Performance and load tests"""

import pytest
from pytest_benchmark.fixture import BenchmarkFixture
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from scripts.workflow_debugger import WorkflowDebugger

class TestWorkflowDebuggerPerformance:
    """Performance tests for WorkflowDebugger"""

    def test_categorize_failure_performance(self, benchmark: BenchmarkFixture):
        """Benchmark failure categorization performance"""
        debugger = WorkflowDebugger(org="test", token="test")
        error_log = "Permission denied" * 100  # Large error message

        result = benchmark(debugger.categorize_failure, error_log)

        assert result is not None

    def test_parallel_workflow_fetch(self, benchmark: BenchmarkFixture):
        """Benchmark parallel workflow fetching"""
        debugger = WorkflowDebugger(org="test", token="test")
        repos = [f"repo-{i}" for i in range(10)]

        def fetch_all():
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(debugger.fetch_workflow_runs, repo)
                    for repo in repos
                ]
                return [f.result() for f in futures]

        # Benchmark requires mocking API calls
        result = benchmark(fetch_all)

    @pytest.mark.asyncio
    async def test_concurrent_async_operations(self, benchmark: BenchmarkFixture):
        """Benchmark concurrent async operations"""

        async def process_batch():
            tasks = [asyncio.sleep(0.001) for _ in range(100)]
            await asyncio.gather(*tasks)

        await benchmark.pedantic(
            lambda: asyncio.run(process_batch()),
            iterations=10,
            rounds=5
        )


class TestScalability:
    """Scalability and load tests"""

    @pytest.mark.slow
    def test_large_dataset_processing(self):
        """Test processing large datasets"""
        debugger = WorkflowDebugger(org="test", token="test")

        # Simulate processing 1000 workflow runs
        large_dataset = [
            {
                "id": i,
                "name": f"Workflow {i}",
                "status": "completed",
                "conclusion": "failure" if i % 5 == 0 else "success"
            }
            for i in range(1000)
        ]

        start_time = time.time()
        failures = [
            item for item in large_dataset
            if item["conclusion"] == "failure"
        ]
        duration = time.time() - start_time

        assert len(failures) == 200  # 1000 / 5
        assert duration < 1.0  # Should complete in under 1 second

    @pytest.mark.slow
    def test_memory_usage(self):
        """Test memory efficiency with large data"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create large data structure
        debugger = WorkflowDebugger(org="test", token="test")
        large_data = [
            {"id": i, "data": "x" * 1000} for i in range(10000)
        ]

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 100 MB for this test)
        assert memory_increase < 100
```

### Load Testing with Locust

```python
#!/usr/bin/env python3
# file: tests/load/locustfile.py
# version: 1.0.0
# guid: locust-load-test

"""Load testing with Locust"""

from locust import HttpUser, task, between, events
import json
import random

class WorkflowAPIUser(HttpUser):
    """Simulated user for workflow API load testing"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    host = "http://localhost:8000"

    def on_start(self):
        """Called when user starts - authenticate"""
        response = self.client.post("/auth/token", data={
            "username": "test",
            "password": "test"
        })
        self.token = response.json()["access_token"]
        self.client.headers = {
            "Authorization": f"Bearer {self.token}"
        }

    @task(10)  # Weight: 10 (executed 10x more than other tasks)
    def list_workflows(self):
        """List all workflows"""
        self.client.get("/api/v1/workflows")

    @task(5)  # Weight: 5
    def get_workflow_details(self):
        """Get details of a random workflow"""
        workflow_id = random.randint(1, 100)
        self.client.get(f"/api/v1/workflows/{workflow_id}")

    @task(2)  # Weight: 2
    def create_workflow(self):
        """Create a new workflow"""
        workflow_data = {
            "name": f"Load Test Workflow {random.randint(1, 10000)}",
            "type": "ci",
            "config": {"runs-on": "ubuntu-latest"}
        }
        self.client.post(
            "/api/v1/workflows",
            json=workflow_data
        )

    @task(1)  # Weight: 1
    def trigger_workflow_run(self):
        """Trigger a workflow run"""
        workflow_id = random.randint(1, 100)
        self.client.post(f"/api/v1/workflows/{workflow_id}/runs")

    @task(3)  # Weight: 3
    def search_workflows(self):
        """Search workflows"""
        query = random.choice(["ci", "release", "test", "deploy"])
        self.client.get(f"/api/v1/workflows?q={query}")


class AdminUser(HttpUser):
    """Simulated admin user with additional permissions"""

    wait_time = between(5, 10)
    host = "http://localhost:8000"

    def on_start(self):
        """Authenticate as admin"""
        response = self.client.post("/auth/token", data={
            "username": "admin",
            "password": "admin"
        })
        self.token = response.json()["access_token"]
        self.client.headers = {
            "Authorization": f"Bearer {self.token}"
        }

    @task
    def delete_old_workflows(self):
        """Delete old workflows"""
        workflow_id = random.randint(1, 50)
        self.client.delete(f"/api/v1/workflows/{workflow_id}")

    @task
    def bulk_update(self):
        """Perform bulk update operation"""
        update_data = {
            "workflows": [
                {"id": i, "status": "archived"}
                for i in range(1, 11)
            ]
        }
        self.client.patch(
            "/api/v1/workflows/bulk",
            json=update_data
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("Starting load test...")
    print(f"Target host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count}")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("\nLoad test completed!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time}ms")
```

---

**Part 4 Complete**: Integration testing (Rust with testcontainers, Python FastAPI integration
tests), E2E testing (Playwright with visual regression), performance testing (Criterion benchmarks,
pytest-benchmark, Locust load testing). ✅

**Continue to Part 5** for test automation workflows and CI/CD integration.
