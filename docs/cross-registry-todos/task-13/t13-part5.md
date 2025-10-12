<!-- file: docs/cross-registry-todos/task-13/t13-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t13-testing-automation-part5-p4q5r6s7-t8u9 -->

# Task 13 Part 5: Test Automation Workflows and CI/CD Integration

## Automated Test Orchestration

### Comprehensive Test Workflow

```yaml
# file: .github/workflows/automated-testing.yml
# version: 2.0.0
# guid: automated-testing-workflow

name: Automated Testing Suite

on:
  push:
    branches: [main, develop, 'feature/**']
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 0 * * *' # Daily at midnight
  workflow_dispatch:
    inputs:
      test_level:
        description: 'Test level to run'
        required: true
        type: choice
        options:
          - unit
          - integration
          - e2e
          - all
        default: 'all'

env:
  RUST_BACKTRACE: 1
  CARGO_TERM_COLOR: always
  FORCE_COLOR: 1

jobs:
  test-matrix:
    name: Test Matrix Strategy
    runs-on: ubuntu-latest
    outputs:
      rust-tests: ${{ steps.plan.outputs.rust-tests }}
      python-tests: ${{ steps.plan.outputs.python-tests }}
      js-tests: ${{ steps.plan.outputs.js-tests }}
      e2e-tests: ${{ steps.plan.outputs.e2e-tests }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Determine test plan
        id: plan
        run: |
          # Analyze changed files to determine which tests to run
          if [[ "${{ github.event_name }}" == "schedule" ]] || [[ "${{ inputs.test_level }}" == "all" ]]; then
            echo "rust-tests=true" >> $GITHUB_OUTPUT
            echo "python-tests=true" >> $GITHUB_OUTPUT
            echo "js-tests=true" >> $GITHUB_OUTPUT
            echo "e2e-tests=true" >> $GITHUB_OUTPUT
          else
            # Check for Rust changes
            if git diff --name-only origin/main | grep -E '\.(rs|toml)$'; then
              echo "rust-tests=true" >> $GITHUB_OUTPUT
            else
              echo "rust-tests=false" >> $GITHUB_OUTPUT
            fi

            # Check for Python changes
            if git diff --name-only origin/main | grep -E '\.py$'; then
              echo "python-tests=true" >> $GITHUB_OUTPUT
            else
              echo "python-tests=false" >> $GITHUB_OUTPUT
            fi

            # Check for JavaScript changes
            if git diff --name-only origin/main | grep -E '\.(js|ts|jsx|tsx)$'; then
              echo "js-tests=true" >> $GITHUB_OUTPUT
            else
              echo "js-tests=false" >> $GITHUB_OUTPUT
            fi

            # E2E tests only on PR or manual trigger
            if [[ "${{ github.event_name }}" == "pull_request" ]] || [[ "${{ inputs.test_level }}" == "e2e" ]]; then
              echo "e2e-tests=true" >> $GITHUB_OUTPUT
            else
              echo "e2e-tests=false" >> $GITHUB_OUTPUT
            fi
          fi

  rust-unit-tests:
    name: Rust Unit Tests
    needs: test-matrix
    if: needs.test-matrix.outputs.rust-tests == 'true'
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        rust: [stable, beta]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4

      - name: Install Rust ${{ matrix.rust }}
        uses: dtolnay/rust-toolchain@master
        with:
          toolchain: ${{ matrix.rust }}

      - name: Cache dependencies
        uses: Swatinem/rust-cache@v2
        with:
          key: ${{ matrix.os }}-${{ matrix.rust }}-test

      - name: Run unit tests
        run: |
          cargo test --lib --all-features --no-fail-fast -- --test-threads=4

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: rust-unit-test-results-${{ matrix.os }}-${{ matrix.rust }}
          path: target/debug/test-results/
          retention-days: 7

  rust-integration-tests:
    name: Rust Integration Tests
    needs: [test-matrix, rust-unit-tests]
    if: needs.test-matrix.outputs.rust-tests == 'true'
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
    env:
      DATABASE_URL: postgres://test:test@localhost:5432/test
    steps:
      - uses: actions/checkout@v4

      - name: Install Rust stable
        uses: dtolnay/rust-toolchain@stable

      - name: Cache dependencies
        uses: Swatinem/rust-cache@v2

      - name: Run database migrations
        run: |
          cargo install sqlx-cli --no-default-features --features postgres
          sqlx migrate run

      - name: Run integration tests
        run: |
          cargo test --test '*' --all-features -- --test-threads=1

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: rust-integration-test-results
          path: target/debug/test-results/
          retention-days: 7

  python-tests:
    name: Python Tests
    needs: test-matrix
    if: needs.test-matrix.outputs.python-tests == 'true'
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12']
        test-type: [unit, integration]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run ${{ matrix.test-type }} tests
        run: |
          if [[ "${{ matrix.test-type }}" == "unit" ]]; then
            pytest tests/ -v -m "not integration and not slow" \
              --junitxml=test-results/junit-${{ matrix.os }}-${{ matrix.python-version }}.xml \
              --cov=scripts --cov-report=xml
          else
            pytest tests/ -v -m "integration" \
              --junitxml=test-results/junit-integration-${{ matrix.os }}-${{ matrix.python-version }}.xml
          fi

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name:
            python-${{ matrix.test-type }}-results-${{ matrix.os }}-py${{ matrix.python-version }}
          path: test-results/
          retention-days: 7

      - name: Upload coverage
        if: matrix.test-type == 'unit'
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: coverage.xml
          flags: python-${{ matrix.os }}-${{ matrix.python-version }}
          fail_ci_if_error: false

  javascript-tests:
    name: JavaScript Tests
    needs: test-matrix
    if: needs.test-matrix.outputs.js-tests == 'true'
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        node-version: [18, 20, 21]
        test-type: [unit, integration]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run ${{ matrix.test-type }} tests
        run: |
          if [[ "${{ matrix.test-type }}" == "unit" ]]; then
            npm run test:unit -- --reporter=json --reporter=junit \
              --outputFile.junit=test-results/junit.xml
          else
            npm run test:integration -- --reporter=json --reporter=junit \
              --outputFile.junit=test-results/junit-integration.xml
          fi

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: js-${{ matrix.test-type }}-results-${{ matrix.os }}-node${{ matrix.node-version }}
          path: test-results/
          retention-days: 7

      - name: Upload coverage
        if: matrix.test-type == 'unit'
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: coverage/lcov.info
          flags: javascript-${{ matrix.os }}-node${{ matrix.node-version }}
          fail_ci_if_error: false

  e2e-tests:
    name: End-to-End Tests
    needs: [test-matrix, rust-integration-tests, python-tests, javascript-tests]
    if: needs.test-matrix.outputs.e2e-tests == 'true' && always()
    strategy:
      fail-fast: false
      matrix:
        browser: [chromium, firefox, webkit]
        shard: [1, 2, 3, 4]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: |
          npm ci
          npx playwright install --with-deps ${{ matrix.browser }}

      - name: Start application
        run: |
          npm run build
          npm run start &
          npx wait-on http://localhost:3000 --timeout 120000

      - name: Run E2E tests
        run: |
          npx playwright test --project=${{ matrix.browser }} \
            --shard=${{ matrix.shard }}/4 \
            --reporter=html,json,junit

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-results-${{ matrix.browser }}-shard${{ matrix.shard }}
          path: |
            playwright-report/
            test-results/
          retention-days: 7

      - name: Upload failure screenshots
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-failures-${{ matrix.browser }}-shard${{ matrix.shard }}
          path: test-results/**/*.png
          retention-days: 14

  performance-tests:
    name: Performance & Benchmark Tests
    needs: [rust-integration-tests]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Rust stable
        uses: dtolnay/rust-toolchain@stable

      - name: Cache dependencies
        uses: Swatinem/rust-cache@v2

      - name: Run Rust benchmarks
        run: |
          cargo bench --no-fail-fast -- --output-format bencher | \
            tee benchmark-results.txt

      - name: Store benchmark results
        uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: 'cargo'
          output-file-path: benchmark-results.txt
          github-token: ${{ secrets.GITHUB_TOKEN }}
          auto-push: true
          alert-threshold: '150%'
          comment-on-alert: true
          fail-on-alert: false

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Python dependencies
        run: |
          pip install -e ".[dev]"
          pip install locust

      - name: Run load tests
        run: |
          # Start application in background
          python -m scripts.api_server &
          sleep 5

          # Run Locust load test
          locust -f tests/load/locustfile.py \
            --headless \
            --users 100 \
            --spawn-rate 10 \
            --run-time 60s \
            --host http://localhost:8000 \
            --html load-test-report.html

      - name: Upload performance results
        uses: actions/upload-artifact@v4
        with:
          name: performance-results
          path: |
            benchmark-results.txt
            load-test-report.html
          retention-days: 30

  test-report:
    name: Aggregate Test Results
    needs: [rust-unit-tests, rust-integration-tests, python-tests, javascript-tests, e2e-tests]
    if: always()
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      checks: write
    steps:
      - uses: actions/checkout@v4

      - name: Download all test results
        uses: actions/download-artifact@v4
        with:
          path: all-test-results/

      - name: Publish test results
        uses: EnricoMi/publish-unit-test-result-action@v2
        with:
          files: |
            all-test-results/**/junit*.xml
            all-test-results/**/*junit*.xml
          check_name: Aggregated Test Results
          comment_title: Test Results Summary
          compare_to_earlier_commit: true
          report_individual_runs: true
          check_run_annotations: all tests, skipped tests

      - name: Generate test summary
        run: |
          cat >> $GITHUB_STEP_SUMMARY <<'EOF'
          # Test Results Summary

          ## Test Execution Status

          | Test Suite             | Status                                     |
          | ---------------------- | ------------------------------------------ |
          | Rust Unit Tests        | ${{ needs.rust-unit-tests.result }}        |
          | Rust Integration Tests | ${{ needs.rust-integration-tests.result }} |
          | Python Tests           | ${{ needs.python-tests.result }}           |
          | JavaScript Tests       | ${{ needs.javascript-tests.result }}       |
          | E2E Tests              | ${{ needs.e2e-tests.result }}              |

          ## Coverage Reports

          - [View Rust Coverage](https://codecov.io/gh/${{ github.repository }}/branch/${{ github.ref_name }}/graph/badge.svg?flag=rust)
          - [View Python Coverage](https://codecov.io/gh/${{ github.repository }}/branch/${{ github.ref_name }}/graph/badge.svg?flag=python)
          - [View JavaScript Coverage](https://codecov.io/gh/${{ github.repository }}/branch/${{ github.ref_name }}/graph/badge.svg?flag=javascript)

          ## Test Artifacts

          All test results, screenshots, and reports have been uploaded as artifacts.
          EOF

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const summary = `
            ## 🧪 Test Results

            | Suite            | Status                                                              |
            | ---------------- | ------------------------------------------------------------------- |
            | Rust Unit        | ${{ needs.rust-unit-tests.result == 'success' ? '✅' : '❌' }}        |
            | Rust Integration | ${{ needs.rust-integration-tests.result == 'success' ? '✅' : '❌' }} |
            | Python           | ${{ needs.python-tests.result == 'success' ? '✅' : '❌' }}           |
            | JavaScript       | ${{ needs.javascript-tests.result == 'success' ? '✅' : '❌' }}       |
            | E2E              | ${{ needs.e2e-tests.result == 'success' ? '✅' : '❌' }}              |

            [View detailed test results](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: summary
            });

  quality-gate:
    name: Quality Gate Check
    needs: [test-report, performance-tests]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Check quality criteria
        run: |
          echo "Checking quality gate criteria..."

          # All required tests must pass
          if [[ "${{ needs.rust-unit-tests.result }}" != "success" ]]; then
            echo "❌ Rust unit tests failed"
            exit 1
          fi

          if [[ "${{ needs.python-tests.result }}" != "success" ]]; then
            echo "❌ Python tests failed"
            exit 1
          fi

          if [[ "${{ needs.javascript-tests.result }}" != "success" ]]; then
            echo "❌ JavaScript tests failed"
            exit 1
          fi

          # Integration and E2E tests allowed to be skipped but not failed
          if [[ "${{ needs.rust-integration-tests.result }}" == "failure" ]]; then
            echo "❌ Rust integration tests failed"
            exit 1
          fi

          if [[ "${{ needs.e2e-tests.result }}" == "failure" ]]; then
            echo "❌ E2E tests failed"
            exit 1
          fi

          # Performance regression check (optional)
          if [[ "${{ needs.performance-tests.result }}" == "failure" ]]; then
            echo "⚠️ Performance tests failed (warning only)"
          fi

          echo "✅ All quality gate criteria passed!"

      - name: Update commit status
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.repos.createCommitStatus({
              owner: context.repo.owner,
              repo: context.repo.repo,
              sha: context.sha,
              state: 'success',
              target_url: `${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`,
              description: 'All quality gate criteria passed',
              context: 'Quality Gate'
            });
```

## Test Result Notifications

### Slack Notification Workflow

```yaml
# file: .github/workflows/test-notifications.yml
# version: 1.0.0
# guid: test-notifications-workflow

name: Test Notifications

on:
  workflow_run:
    workflows: ['Automated Testing Suite']
    types: [completed]

jobs:
  notify-slack:
    name: Send Slack Notification
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion != 'cancelled' }}
    steps:
      - name: Prepare notification
        id: prepare
        run: |
          if [[ "${{ github.event.workflow_run.conclusion }}" == "success" ]]; then
            echo "color=good" >> $GITHUB_OUTPUT
            echo "emoji=:white_check_mark:" >> $GITHUB_OUTPUT
            echo "status=PASSED" >> $GITHUB_OUTPUT
          else
            echo "color=danger" >> $GITHUB_OUTPUT
            echo "emoji=:x:" >> $GITHUB_OUTPUT
            echo "status=FAILED" >> $GITHUB_OUTPUT
          fi

      - name: Send Slack notification
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
          payload: |
            {
              "attachments": [
                {
                  "color": "${{ steps.prepare.outputs.color }}",
                  "title": "${{ steps.prepare.outputs.emoji }} Test Suite ${{ steps.prepare.outputs.status }}",
                  "fields": [
                    {
                      "title": "Repository",
                      "value": "${{ github.repository }}",
                      "short": true
                    },
                    {
                      "title": "Branch",
                      "value": "${{ github.event.workflow_run.head_branch }}",
                      "short": true
                    },
                    {
                      "title": "Commit",
                      "value": "<${{ github.event.workflow_run.html_url }}|${{ github.event.workflow_run.head_sha }}>",
                      "short": true
                    },
                    {
                      "title": "Duration",
                      "value": "${{ github.event.workflow_run.duration }}s",
                      "short": true
                    }
                  ],
                  "footer": "GitHub Actions",
                  "footer_icon": "https://github.com/favicon.ico",
                  "ts": ${{ github.event.workflow_run.updated_at }}
                }
              ]
            }
```

## Test Data Management

### Test Fixture Generator

```python
#!/usr/bin/env python3
# file: tests/fixtures/generator.py
# version: 1.0.0
# guid: test-fixture-generator

"""Test fixture generator for creating realistic test data"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

class TestDataGenerator:
    """Generate realistic test data for workflows, runs, and configurations"""

    def __init__(self, seed: int = 42):
        """Initialize generator with optional seed for reproducibility"""
        random.seed(seed)
        self.workflow_names = [
            "CI", "Release", "Deploy", "Test", "Build",
            "Lint", "Security Scan", "Backup", "Monitoring"
        ]
        self.statuses = ["queued", "in_progress", "completed"]
        self.conclusions = ["success", "failure", "cancelled", "skipped"]

    def generate_workflow(self, id: int) -> Dict[str, Any]:
        """Generate a single workflow definition"""
        return {
            "id": id,
            "name": random.choice(self.workflow_names),
            "path": f".github/workflows/workflow-{id}.yml",
            "state": random.choice(["active", "disabled"]),
            "created_at": self._random_datetime(days_ago=365),
            "updated_at": self._random_datetime(days_ago=30),
        }

    def generate_workflow_run(
        self,
        id: int,
        workflow_id: int,
        status: str = None,
        conclusion: str = None
    ) -> Dict[str, Any]:
        """Generate a workflow run with specified or random status/conclusion"""
        status = status or random.choice(self.statuses)
        conclusion = conclusion or (
            random.choice(self.conclusions) if status == "completed" else None
        )

        created = self._random_datetime(days_ago=30)
        updated = created + timedelta(minutes=random.randint(1, 60))

        return {
            "id": id,
            "workflow_id": workflow_id,
            "status": status,
            "conclusion": conclusion,
            "run_number": id,
            "event": random.choice(["push", "pull_request", "schedule"]),
            "created_at": created.isoformat(),
            "updated_at": updated.isoformat(),
            "duration_seconds": (updated - created).total_seconds(),
        }

    def generate_test_dataset(
        self,
        num_workflows: int = 10,
        runs_per_workflow: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate complete test dataset with workflows and runs"""
        workflows = [
            self.generate_workflow(i) for i in range(1, num_workflows + 1)
        ]

        runs = []
        run_id = 1
        for workflow in workflows:
            for _ in range(runs_per_workflow):
                runs.append(
                    self.generate_workflow_run(run_id, workflow["id"])
                )
                run_id += 1

        return {
            "workflows": workflows,
            "runs": runs,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_workflows": num_workflows,
                "total_runs": len(runs),
            }
        }

    def _random_datetime(self, days_ago: int) -> datetime:
        """Generate random datetime within last N days"""
        now = datetime.now()
        random_days = random.randint(0, days_ago)
        random_hours = random.randint(0, 23)
        random_minutes = random.randint(0, 59)
        return now - timedelta(
            days=random_days,
            hours=random_hours,
            minutes=random_minutes
        )

    def save_fixtures(
        self,
        output_dir: Path,
        num_workflows: int = 10,
        runs_per_workflow: int = 50
    ):
        """Generate and save test fixtures to files"""
        output_dir.mkdir(parents=True, exist_ok=True)

        dataset = self.generate_test_dataset(num_workflows, runs_per_workflow)

        # Save workflows
        with open(output_dir / "workflows.json", "w") as f:
            json.dump(dataset["workflows"], f, indent=2)

        # Save runs
        with open(output_dir / "runs.json", "w") as f:
            json.dump(dataset["runs"], f, indent=2)

        # Save metadata
        with open(output_dir / "metadata.json", "w") as f:
            json.dump(dataset["metadata"], f, indent=2)

        print(f"Generated {len(dataset['workflows'])} workflows")
        print(f"Generated {len(dataset['runs'])} runs")
        print(f"Saved to {output_dir}")


if __name__ == "__main__":
    generator = TestDataGenerator()
    generator.save_fixtures(
        Path(__file__).parent / "data",
        num_workflows=20,
        runs_per_workflow=100
    )
```

---

**Part 5 Complete**: Comprehensive test automation workflows (intelligent test matrix with change
detection, parallel execution, test sharding), test result aggregation and reporting, quality gates,
Slack notifications, and test data management. ✅

**Continue to Part 6** for best practices, testing documentation, and Task 13 completion checklist.
