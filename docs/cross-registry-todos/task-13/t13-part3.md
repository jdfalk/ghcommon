<!-- file: docs/cross-registry-todos/task-13/t13-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t13-testing-automation-part3-n4o5p6q7-r8s9 -->

# Task 13 Part 3: Test Coverage and CI Automation

## Coverage Enforcement Strategy

### Multi-Language Coverage Configuration

```yaml
# file: .github/workflows/test-coverage.yml
# version: 1.0.0
# guid: test-coverage-workflow

name: Test Coverage

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  COVERAGE_THRESHOLD: 80
  CARGO_TERM_COLOR: always

jobs:
  rust-coverage:
    name: Rust Test Coverage
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Rust toolchain
        uses: dtolnay/rust-toolchain@stable
        with:
          components: llvm-tools-preview

      - name: Install cargo-llvm-cov
        uses: taiki-e/install-action@v2
        with:
          tool: cargo-llvm-cov

      - name: Setup cache
        uses: Swatinem/rust-cache@v2
        with:
          cache-on-failure: true

      - name: Run tests with coverage
        run: |
          cargo llvm-cov test \
            --all-features \
            --workspace \
            --lcov \
            --output-path lcov.info

      - name: Generate HTML coverage report
        run: |
          cargo llvm-cov report \
            --html \
            --output-dir htmlcov

      - name: Check coverage threshold
        run: |
          COVERAGE=$(cargo llvm-cov report --summary-only | grep -oP 'TOTAL.*?\K\d+\.\d+' | head -1)
          echo "Current coverage: ${COVERAGE}%"
          if (( $(echo "$COVERAGE < $COVERAGE_THRESHOLD" | bc -l) )); then
            echo "Coverage ${COVERAGE}% is below threshold ${COVERAGE_THRESHOLD}%"
            exit 1
          fi

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: lcov.info
          flags: rust
          name: rust-coverage
          fail_ci_if_error: true

      - name: Upload HTML coverage
        uses: actions/upload-artifact@v4
        with:
          name: rust-coverage-report
          path: htmlcov/
          retention-days: 30

  python-coverage:
    name: Python Test Coverage
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run tests with coverage
        run: |
          pytest \
            --cov=scripts \
            --cov-branch \
            --cov-report=xml \
            --cov-report=html \
            --cov-report=term-missing \
            --cov-fail-under=${{ env.COVERAGE_THRESHOLD }}

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: coverage.xml
          flags: python
          name: python-coverage
          fail_ci_if_error: true

      - name: Upload HTML coverage
        uses: actions/upload-artifact@v4
        with:
          name: python-coverage-report
          path: htmlcov/
          retention-days: 30

      - name: Comment coverage on PR
        if: github.event_name == 'pull_request'
        uses: py-cov-action/python-coverage-comment-action@v3
        with:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          MINIMUM_GREEN: 90
          MINIMUM_ORANGE: 80

  javascript-coverage:
    name: JavaScript Test Coverage
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests with coverage
        run: |
          npm run test:coverage -- \
            --reporter=json \
            --reporter=html

      - name: Check coverage threshold
        run: |
          COVERAGE=$(jq '.total.lines.pct' coverage/coverage-summary.json)
          echo "Current coverage: ${COVERAGE}%"
          if (( $(echo "$COVERAGE < $COVERAGE_THRESHOLD" | bc -l) )); then
            echo "Coverage ${COVERAGE}% is below threshold ${COVERAGE_THRESHOLD}%"
            exit 1
          fi

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: coverage/lcov.info
          flags: javascript
          name: javascript-coverage
          fail_ci_if_error: true

      - name: Upload HTML coverage
        uses: actions/upload-artifact@v4
        with:
          name: javascript-coverage-report
          path: coverage/
          retention-days: 30

  coverage-report:
    name: Combined Coverage Report
    needs: [rust-coverage, python-coverage, javascript-coverage]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - uses: actions/checkout@v4

      - name: Download all coverage reports
        uses: actions/download-artifact@v4
        with:
          path: coverage-reports/

      - name: Generate combined report
        run: |
          cat > coverage-reports/README.md <<'EOF'
          # Test Coverage Report

          ## Coverage by Language

          | Language   | Coverage                                                                                                                                   | Status          |
          | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
          | Rust       | [![Rust Coverage](https://codecov.io/gh/jdfalk/ghcommon/branch/main/graph/badge.svg?flag=rust)](https://codecov.io/gh/jdfalk/ghcommon)     | View in Codecov |
          | Python     | [![Python Coverage](https://codecov.io/gh/jdfalk/ghcommon/branch/main/graph/badge.svg?flag=python)](https://codecov.io/gh/jdfalk/ghcommon) | View in Codecov |
          | JavaScript | [![JS Coverage](https://codecov.io/gh/jdfalk/ghcommon/branch/main/graph/badge.svg?flag=javascript)](https://codecov.io/gh/jdfalk/ghcommon) | View in Codecov |

          ## Individual Reports

          - [Rust Coverage Report](rust-coverage-report/index.html)
          - [Python Coverage Report](python-coverage-report/index.html)
          - [JavaScript Coverage Report](javascript-coverage-report/index.html)
          EOF

      - name: Upload combined report
        uses: actions/upload-artifact@v4
        with:
          name: combined-coverage-report
          path: coverage-reports/
          retention-days: 30
```

## CI Test Automation

### Comprehensive CI Test Workflow

```yaml
# file: .github/workflows/ci-tests.yml
# version: 2.0.0
# guid: ci-tests-workflow

name: CI Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *' # Daily at 2 AM UTC

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  RUST_BACKTRACE: 1
  CARGO_TERM_COLOR: always

jobs:
  detect-changes:
    name: Detect Changes
    runs-on: ubuntu-latest
    outputs:
      rust: ${{ steps.filter.outputs.rust }}
      python: ${{ steps.filter.outputs.python }}
      javascript: ${{ steps.filter.outputs.javascript }}
      workflows: ${{ steps.filter.outputs.workflows }}
    steps:
      - uses: actions/checkout@v4

      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            rust:
              - 'src/**/*.rs'
              - 'Cargo.toml'
              - 'Cargo.lock'
            python:
              - 'scripts/**/*.py'
              - 'tests/**/*.py'
              - 'pyproject.toml'
              - 'requirements*.txt'
            javascript:
              - 'src/**/*.{js,ts,jsx,tsx}'
              - 'package.json'
              - 'package-lock.json'
            workflows:
              - '.github/workflows/**'

  rust-tests:
    name: Rust Tests
    needs: detect-changes
    if: needs.detect-changes.outputs.rust == 'true' || github.event_name == 'schedule'
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        rust: [stable, beta, nightly]
        exclude:
          - os: macos-latest
            rust: nightly
          - os: windows-latest
            rust: nightly
    runs-on: ${{ matrix.os }}
    continue-on-error: ${{ matrix.rust == 'nightly' }}
    steps:
      - uses: actions/checkout@v4

      - name: Install Rust ${{ matrix.rust }}
        uses: dtolnay/rust-toolchain@master
        with:
          toolchain: ${{ matrix.rust }}
          components: rustfmt, clippy

      - name: Setup cache
        uses: Swatinem/rust-cache@v2
        with:
          key: ${{ matrix.os }}-${{ matrix.rust }}

      - name: Check formatting
        if: matrix.rust == 'stable'
        run: cargo fmt --all -- --check

      - name: Run clippy
        if: matrix.rust == 'stable'
        run: |
          cargo clippy --all-targets --all-features -- \
            -D warnings \
            -D clippy::all \
            -D clippy::pedantic

      - name: Run unit tests
        run: cargo test --lib --all-features

      - name: Run integration tests
        run: cargo test --test '*' --all-features

      - name: Run doc tests
        run: cargo test --doc --all-features

      - name: Test examples
        run: |
          for example in examples/*.rs; do
            cargo test --example $(basename $example .rs)
          done

  rust-benchmarks:
    name: Rust Benchmarks
    needs: rust-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Rust stable
        uses: dtolnay/rust-toolchain@stable

      - name: Setup cache
        uses: Swatinem/rust-cache@v2

      - name: Run benchmarks
        run: cargo bench --no-fail-fast -- --output-format bencher | tee benchmark-results.txt

      - name: Store benchmark results
        uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: 'cargo'
          output-file-path: benchmark-results.txt
          github-token: ${{ secrets.GITHUB_TOKEN }}
          auto-push: ${{ github.ref == 'refs/heads/main' }}
          alert-threshold: '150%'
          comment-on-alert: true

  python-tests:
    name: Python Tests
    needs: detect-changes
    if: needs.detect-changes.outputs.python == 'true' || github.event_name == 'schedule'
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12']
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

      - name: Run linters
        run: |
          black --check scripts/ tests/
          ruff check scripts/ tests/
          mypy scripts/ tests/

      - name: Run unit tests
        run: |
          pytest tests/ \
            -v \
            -m "not integration and not slow" \
            --durations=10

      - name: Run integration tests
        run: |
          pytest tests/ \
            -v \
            -m "integration" \
            --durations=10

      - name: Test with different markers
        run: |
          pytest tests/ -m "not slow" --tb=short

  javascript-tests:
    name: JavaScript Tests
    needs: detect-changes
    if: needs.detect-changes.outputs.javascript == 'true' || github.event_name == 'schedule'
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        node-version: [18, 20, 21]
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

      - name: Run linters
        run: |
          npm run lint
          npm run type-check

      - name: Run unit tests
        run: npm run test:unit

      - name: Run integration tests
        run: npm run test:integration

  mutation-testing:
    name: Mutation Testing
    needs: [rust-tests, python-tests]
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Install cargo-mutants
        run: cargo install cargo-mutants

      - name: Run mutation tests
        run: |
          cargo mutants --no-shuffle -j 2 -- --all-features

      - name: Upload mutation report
        uses: actions/upload-artifact@v4
        with:
          name: mutation-testing-report
          path: mutants.out/
          retention-days: 30

  test-results:
    name: Test Results Summary
    needs: [rust-tests, python-tests, javascript-tests]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Generate summary
        run: |
          cat >> $GITHUB_STEP_SUMMARY <<'EOF'
          # Test Results Summary

          ## Status

          | Test Suite       | Status                               |
          | ---------------- | ------------------------------------ |
          | Rust Tests       | ${{ needs.rust-tests.result }}       |
          | Python Tests     | ${{ needs.python-tests.result }}     |
          | JavaScript Tests | ${{ needs.javascript-tests.result }} |

          ## Details

          - **Rust**: Tested on Ubuntu, macOS, Windows with stable, beta, nightly
          - **Python**: Tested on Python 3.9, 3.10, 3.11, 3.12
          - **JavaScript**: Tested on Node.js 18, 20, 21

          EOF
```

## Pre-Commit Hook Configuration

### Git Pre-Commit Hooks

```yaml
# file: .pre-commit-config.yaml
# version: 1.0.0
# guid: pre-commit-configuration

repos:
  # General file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
        args: ['--unsafe'] # Allow custom YAML tags
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: mixed-line-ending
        args: ['--fix=lf']

  # Rust hooks
  - repo: local
    hooks:
      - id: cargo-fmt
        name: cargo fmt
        entry: cargo fmt
        language: system
        types: [rust]
        pass_filenames: false

      - id: cargo-clippy
        name: cargo clippy
        entry: cargo clippy
        language: system
        args: ['--all-targets', '--all-features', '--', '-D', 'warnings']
        types: [rust]
        pass_filenames: false

      - id: cargo-test
        name: cargo test
        entry: cargo test
        language: system
        args: ['--lib', '--all-features']
        types: [rust]
        pass_filenames: false
        stages: [push]

  # Python hooks
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.11
    hooks:
      - id: ruff
        args: ['--fix', '--exit-non-zero-on-fix']

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: ['--strict', '--ignore-missing-imports']

  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        args: ['-v', '-m', 'not slow']
        types: [python]
        pass_filenames: false
        stages: [push]

  # JavaScript/TypeScript hooks
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.(js|ts|jsx|tsx)$
        types: [file]
        args: ['--fix']
        additional_dependencies:
          - eslint@8.56.0
          - '@typescript-eslint/eslint-plugin@6.18.1'
          - '@typescript-eslint/parser@6.18.1'

  - repo: local
    hooks:
      - id: vitest-check
        name: vitest-check
        entry: npm run test:unit
        language: system
        types: [javascript, typescript]
        pass_filenames: false
        stages: [push]

  # Security checks
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.1
    hooks:
      - id: gitleaks

  # Commit message linting
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.13.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

### Pre-Commit Installation Script

```bash
#!/bin/bash
# file: scripts/setup-pre-commit.sh
# version: 1.0.0
# guid: setup-pre-commit-script

set -euo pipefail

echo "Setting up pre-commit hooks..."

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Install hooks
echo "Installing pre-commit hooks..."
pre-commit install --install-hooks
pre-commit install --hook-type commit-msg

# Test hooks
echo "Testing pre-commit configuration..."
pre-commit run --all-files || true

echo "Pre-commit hooks installed successfully!"
echo "To skip hooks for a commit, use: git commit --no-verify"
```

## Test Reporting and Dashboards

### Test Results Artifact Workflow

```yaml
# file: .github/workflows/test-reports.yml
# version: 1.0.0
# guid: test-reports-workflow

name: Test Reports

on:
  workflow_run:
    workflows: ['CI Tests']
    types: [completed]

jobs:
  generate-report:
    name: Generate Test Report
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion != 'cancelled' }}
    permissions:
      contents: write
      pull-requests: write
      checks: write
    steps:
      - uses: actions/checkout@v4

      - name: Download test results
        uses: actions/download-artifact@v4
        with:
          name: test-results
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Publish test results
        uses: EnricoMi/publish-unit-test-result-action@v2
        with:
          files: |
            **/test-results/**/*.xml
            **/junit/**/*.xml
          check_name: Test Results
          comment_title: Test Results
          compare_to_earlier_commit: true
          report_individual_runs: true

      - name: Generate test report page
        run: |
          cat > test-report.html <<'EOF'
          <!DOCTYPE html>
          <html>
          <head>
            <title>Test Report</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 20px; }
              .summary { background: #f0f0f0; padding: 15px; margin-bottom: 20px; }
              .passed { color: green; font-weight: bold; }
              .failed { color: red; font-weight: bold; }
              table { border-collapse: collapse; width: 100%; }
              th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
              th { background-color: #4CAF50; color: white; }
            </style>
          </head>
          <body>
            <h1>Test Report</h1>
            <div class="summary">
              <h2>Summary</h2>
              <p>Total Tests: <span id="total"></span></p>
              <p class="passed">Passed: <span id="passed"></span></p>
              <p class="failed">Failed: <span id="failed"></span></p>
            </div>
            <h2>Detailed Results</h2>
            <table id="results">
              <thead>
                <tr>
                  <th>Test Suite</th>
                  <th>Total</th>
                  <th>Passed</th>
                  <th>Failed</th>
                  <th>Duration</th>
                </tr>
              </thead>
              <tbody></tbody>
            </table>
          </body>
          </html>
          EOF

      - name: Deploy report to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        if: github.ref == 'refs/heads/main'
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./
          destination_dir: test-reports
```

---

**Part 3 Complete**: Coverage enforcement (Rust cargo-llvm-cov, Python pytest-cov, JavaScript Vitest
coverage with Codecov integration), comprehensive CI test workflows with matrix builds, pre-commit
hooks, and test reporting dashboards. ✅

**Continue to Part 4** for integration testing, E2E testing, and performance testing.
