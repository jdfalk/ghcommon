<!-- file: docs/cross-registry-todos/task-08/t08-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t08-ci-consolidation-part3-d9e0f1g2-h3i4 -->

# Task 08 Part 3: Consolidated Workflow Design & Implementation

## Complete Consolidated Workflow Structure

### File: .github/workflows/reusable-ci-consolidated.yml

```yaml
# file: .github/workflows/reusable-ci-consolidated.yml
# version: 1.0.0
# guid: consolidated-ci-workflow-a1b2c3d4-e5f6

name: Consolidated CI Workflow

on:
  workflow_call:
    inputs:
      # === Configuration ===
      config-file:
        description: 'Path to repository configuration file'
        type: string
        default: '.github/repository-config.yml'

      working-directory:
        description: 'Working directory for all jobs'
        type: string
        default: '.'

      # === Change Detection ===
      skip-change-detection:
        description: 'Skip change detection and run all jobs'
        type: boolean
        default: false

      # === Language Enable Flags ===
      enable-go:
        description: 'Enable Go jobs'
        type: boolean
        default: true

      enable-python:
        description: 'Enable Python jobs'
        type: boolean
        default: true

      enable-typescript:
        description: 'Enable TypeScript/Node.js jobs'
        type: boolean
        default: true

      enable-rust:
        description: 'Enable Rust jobs'
        type: boolean
        default: true

      enable-docker:
        description: 'Enable Docker jobs'
        type: boolean
        default: true

      enable-protobuf:
        description: 'Enable Protobuf jobs'
        type: boolean
        default: false

      # === Feature Flags ===
      enable-coverage:
        description: 'Enable code coverage reporting'
        type: boolean
        default: true

      enable-security-scan:
        description: 'Enable security scanning (CodeQL, Trivy)'
        type: boolean
        default: true

      enable-super-linter:
        description: 'Enable Super-Linter for comprehensive linting'
        type: boolean
        default: false

      enable-benchmarks:
        description: 'Enable performance benchmarks'
        type: boolean
        default: false

      enable-dependency-review:
        description: 'Enable dependency review (PRs only)'
        type: boolean
        default: true

      # === Version Matrices ===
      go-versions:
        description: 'JSON array of Go versions to test'
        type: string
        default: '["1.21"]'

      python-versions:
        description: 'JSON array of Python versions to test'
        type: string
        default: '["3.11"]'

      node-versions:
        description: 'JSON array of Node.js versions to test'
        type: string
        default: '["20"]'

      rust-versions:
        description: 'JSON array of Rust versions to test'
        type: string
        default: '["stable"]'

      # === Docker Configuration ===
      docker-platforms:
        description: 'Comma-separated list of platforms for Docker builds'
        type: string
        default: 'linux/amd64,linux/arm64'

      docker-registry:
        description: 'Docker registry to use'
        type: string
        default: 'ghcr.io'

      # === Coverage Configuration ===
      coverage-threshold:
        description: 'Minimum coverage percentage required'
        type: number
        default: 0

      # === Test Configuration ===
      test-timeout:
        description: 'Test timeout in minutes'
        type: number
        default: 30

    outputs:
      # === Change Detection Outputs ===
      has-go-changes:
        description: 'Whether Go files changed'
        value: ${{ jobs.detect-changes.outputs.has-go-changes }}

      has-python-changes:
        description: 'Whether Python files changed'
        value: ${{ jobs.detect-changes.outputs.has-python-changes }}

      has-typescript-changes:
        description: 'Whether TypeScript files changed'
        value: ${{ jobs.detect-changes.outputs.has-typescript-changes }}

      has-rust-changes:
        description: 'Whether Rust files changed'
        value: ${{ jobs.detect-changes.outputs.has-rust-changes }}

      has-docker-changes:
        description: 'Whether Docker files changed'
        value: ${{ jobs.detect-changes.outputs.has-docker-changes }}

      has-docs-changes:
        description: 'Whether documentation files changed'
        value: ${{ jobs.detect-changes.outputs.has-docs-changes }}

      has-workflow-changes:
        description: 'Whether workflow files changed'
        value: ${{ jobs.detect-changes.outputs.has-workflow-changes }}

      has-protobuf-changes:
        description: 'Whether protobuf files changed'
        value: ${{ jobs.detect-changes.outputs.has-protobuf-changes }}

      # === Test Result Outputs ===
      all-tests-passed:
        description: 'Whether all tests passed'
        value: ${{ jobs.report-results.outputs.all-tests-passed }}

      coverage-percentage:
        description: 'Overall coverage percentage'
        value: ${{ jobs.report-results.outputs.coverage-percentage }}

      security-issues:
        description: 'Number of security issues found'
        value: ${{ jobs.report-results.outputs.security-issues }}

jobs:
  # ============================================================================
  # Job 1: Load Configuration
  # ============================================================================
  load-config:
    name: Load Repository Configuration
    runs-on: ubuntu-latest
    outputs:
      config-exists: ${{ steps.check-config.outputs.exists }}
      config-json: ${{ steps.parse-config.outputs.json }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Check for repository config
        id: check-config
        run: |
          if [ -f "${{ inputs.config-file }}" ]; then
            echo "exists=true" >> $GITHUB_OUTPUT
            echo "✅ Repository config found: ${{ inputs.config-file }}"
          else
            echo "exists=false" >> $GITHUB_OUTPUT
            echo "ℹ️  No repository config found, using defaults"
          fi

      - name: Parse repository config
        id: parse-config
        if: steps.check-config.outputs.exists == 'true'
        run: |
          # Install yq for YAML parsing
          sudo wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
          sudo chmod +x /usr/local/bin/yq

          # Convert YAML to JSON
          config_json=$(yq eval -o=json "${{ inputs.config-file }}")
          echo "json<<EOF" >> $GITHUB_OUTPUT
          echo "$config_json" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

          echo "✅ Configuration parsed successfully"

      - name: Display effective configuration
        run: |
          echo "### Configuration Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Config File:** \`${{ inputs.config-file }}\`" >> $GITHUB_STEP_SUMMARY
          echo "**Exists:** ${{ steps.check-config.outputs.exists }}" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Enabled Languages:**" >> $GITHUB_STEP_SUMMARY
          echo "- Go: ${{ inputs.enable-go }}" >> $GITHUB_STEP_SUMMARY
          echo "- Python: ${{ inputs.enable-python }}" >> $GITHUB_STEP_SUMMARY
          echo "- TypeScript: ${{ inputs.enable-typescript }}" >> $GITHUB_STEP_SUMMARY
          echo "- Rust: ${{ inputs.enable-rust }}" >> $GITHUB_STEP_SUMMARY
          echo "- Docker: ${{ inputs.enable-docker }}" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Enabled Features:**" >> $GITHUB_STEP_SUMMARY
          echo "- Coverage: ${{ inputs.enable-coverage }}" >> $GITHUB_STEP_SUMMARY
          echo "- Security Scan: ${{ inputs.enable-security-scan }}" >> $GITHUB_STEP_SUMMARY
          echo "- Super-Linter: ${{ inputs.enable-super-linter }}" >> $GITHUB_STEP_SUMMARY
          echo "- Benchmarks: ${{ inputs.enable-benchmarks }}" >> $GITHUB_STEP_SUMMARY

  # ============================================================================
  # Job 2: Detect Changes
  # ============================================================================
  detect-changes:
    name: Detect File Changes
    runs-on: ubuntu-latest
    outputs:
      has-go-changes: ${{ steps.filter.outputs.go }}
      has-python-changes: ${{ steps.filter.outputs.python }}
      has-typescript-changes: ${{ steps.filter.outputs.typescript }}
      has-rust-changes: ${{ steps.filter.outputs.rust }}
      has-docker-changes: ${{ steps.filter.outputs.docker }}
      has-docs-changes: ${{ steps.filter.outputs.docs }}
      has-workflow-changes: ${{ steps.filter.outputs.workflows }}
      has-protobuf-changes: ${{ steps.filter.outputs.protobuf }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Detect file changes
        if: inputs.skip-change-detection == false
        uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            go:
              - '**/*.go'
              - 'go.mod'
              - 'go.sum'
              - '**/go.mod'
              - '**/go.sum'
              - '.github/workflows/*go*.yml'
            python:
              - '**/*.py'
              - 'requirements*.txt'
              - '**/requirements*.txt'
              - 'pyproject.toml'
              - '**/pyproject.toml'
              - 'setup.py'
              - 'setup.cfg'
              - 'tox.ini'
              - 'poetry.lock'
              - '.github/workflows/*python*.yml'
            typescript:
              - '**/*.ts'
              - '**/*.tsx'
              - '**/*.js'
              - '**/*.jsx'
              - 'package.json'
              - '**/package.json'
              - 'package-lock.json'
              - 'yarn.lock'
              - 'pnpm-lock.yaml'
              - 'tsconfig.json'
              - '**/tsconfig.json'
              - '.github/workflows/*frontend*.yml'
              - '.github/workflows/*typescript*.yml'
              - '.github/workflows/*node*.yml'
            rust:
              - '**/*.rs'
              - 'Cargo.toml'
              - '**/Cargo.toml'
              - 'Cargo.lock'
              - '.cargo/**'
              - 'rust-toolchain.toml'
              - 'rustfmt.toml'
              - 'clippy.toml'
              - '.github/workflows/*rust*.yml'
            docker:
              - '**/Dockerfile'
              - '**/Dockerfile.*'
              - 'docker-compose*.yml'
              - '.dockerignore'
              - '.github/workflows/*docker*.yml'
            docs:
              - '**/*.md'
              - 'docs/**'
              - 'README*'
              - 'CHANGELOG*'
              - 'LICENSE*'
              - 'CONTRIBUTING*'
              - 'CODE_OF_CONDUCT*'
            workflows:
              - '.github/workflows/**'
              - '.github/actions/**'
            protobuf:
              - '**/*.proto'
              - 'buf.yaml'
              - 'buf.gen.yaml'
              - 'buf.lock'
              - '.github/workflows/*proto*.yml'

      - name: Skip change detection
        if: inputs.skip-change-detection == true
        run: |
          echo "go=true" >> $GITHUB_OUTPUT
          echo "python=true" >> $GITHUB_OUTPUT
          echo "typescript=true" >> $GITHUB_OUTPUT
          echo "rust=true" >> $GITHUB_OUTPUT
          echo "docker=true" >> $GITHUB_OUTPUT
          echo "docs=true" >> $GITHUB_OUTPUT
          echo "workflows=true" >> $GITHUB_OUTPUT
          echo "protobuf=true" >> $GITHUB_OUTPUT
        shell: bash

      - name: Display change detection results
        run: |
          echo "### Change Detection Results" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| File Type | Changed |" >> $GITHUB_STEP_SUMMARY
          echo "|-----------|---------|" >> $GITHUB_STEP_SUMMARY
          echo "| Go | ${{ steps.filter.outputs.go == 'true' && '✅' || '⬜' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Python | ${{ steps.filter.outputs.python == 'true' && '✅' || '⬜' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| TypeScript | ${{ steps.filter.outputs.typescript == 'true' && '✅' || '⬜' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Rust | ${{ steps.filter.outputs.rust == 'true' && '✅' || '⬜' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Docker | ${{ steps.filter.outputs.docker == 'true' && '✅' || '⬜' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Docs | ${{ steps.filter.outputs.docs == 'true' && '✅' || '⬜' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Workflows | ${{ steps.filter.outputs.workflows == 'true' && '✅' || '⬜' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Protobuf | ${{ steps.filter.outputs.protobuf == 'true' && '✅' || '⬜' }} |" >> $GITHUB_STEP_SUMMARY

  # ============================================================================
  # Job 3: Super-Linter (Optional)
  # ============================================================================
  super-lint:
    name: Super-Linter
    if: inputs.enable-super-linter == true
    runs-on: ubuntu-latest
    permissions:
      contents: read
      statuses: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run Super-Linter
        uses: super-linter/super-linter@v6
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          VALIDATE_ALL_CODEBASE: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
          DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}
          FILTER_REGEX_EXCLUDE: '.*/(node_modules|target|dist|build|__pycache__|\.venv|venv|htmlcov|\.pytest_cache|\.mypy_cache)/.*'
          # Enable general linters
          VALIDATE_YAML: true
          VALIDATE_JSON: true
          VALIDATE_XML: true
          VALIDATE_MARKDOWN: true
          VALIDATE_BASH: true
          VALIDATE_SHELL_SHFMT: true
          VALIDATE_DOCKERFILE_HADOLINT: true
          # Disable linters handled by language-specific jobs
          VALIDATE_GO: false
          VALIDATE_PYTHON_BLACK: false
          VALIDATE_PYTHON_FLAKE8: false
          VALIDATE_PYTHON_PYLINT: false
          VALIDATE_JAVASCRIPT_ES: false
          VALIDATE_JAVASCRIPT_STANDARD: false
          VALIDATE_TYPESCRIPT_ES: false
          VALIDATE_TYPESCRIPT_STANDARD: false

  # ============================================================================
  # Job 4: Go - Build, Test, Coverage
  # ============================================================================
  test-go:
    name: Go ${{ matrix.go-version }}
    needs: detect-changes
    if: |
      inputs.enable-go == true &&
      (inputs.skip-change-detection == true || needs.detect-changes.outputs.has-go-changes == 'true')
    runs-on: ubuntu-latest
    timeout-minutes: ${{ fromJson(inputs.test-timeout) }}
    strategy:
      fail-fast: false
      matrix:
        go-version: ${{ fromJson(inputs.go-versions) }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go-version }}
          cache: true
          cache-dependency-path: |
            go.sum
            **/go.sum

      - name: Download dependencies
        run: go mod download

      - name: Build
        run: |
          echo "### 🔨 Building Go Project" >> $GITHUB_STEP_SUMMARY
          go build -v ./...

      - name: Run golangci-lint
        uses: golangci/golangci-lint-action@v4
        with:
          version: latest
          args: --timeout=5m

      - name: Test with coverage
        if: inputs.enable-coverage == true
        run: |
          echo "### 🧪 Running Go Tests with Coverage" >> $GITHUB_STEP_SUMMARY
          go test -v -race -coverprofile=coverage.out -covermode=atomic ./...

          # Display coverage summary
          go tool cover -func=coverage.out | tail -1

      - name: Test without coverage
        if: inputs.enable-coverage == false
        run: |
          echo "### 🧪 Running Go Tests" >> $GITHUB_STEP_SUMMARY
          go test -v -race ./...

      - name: Run benchmarks
        if: inputs.enable-benchmarks == true && github.event_name == 'push'
        run: |
          echo "### 📊 Running Benchmarks" >> $GITHUB_STEP_SUMMARY
          go test -bench=. -benchmem -run=^$ ./... | tee benchmark.txt

      - name: Check coverage threshold
        if: inputs.enable-coverage == true && inputs.coverage-threshold > 0
        run: |
          coverage=$(go tool cover -func=coverage.out | tail -1 | awk '{print $3}' | sed 's/%//')
          threshold=${{ inputs.coverage-threshold }}

          echo "Coverage: ${coverage}%"
          echo "Threshold: ${threshold}%"

          if (( $(echo "$coverage < $threshold" | bc -l) )); then
            echo "❌ Coverage ${coverage}% is below threshold ${threshold}%"
            exit 1
          else
            echo "✅ Coverage ${coverage}% meets threshold ${threshold}%"
          fi

      - name: Upload coverage to Codecov
        if: |
          inputs.enable-coverage == true &&
          matrix.go-version == fromJson(inputs.go-versions)[0]
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.out
          flags: go
          name: go-${{ matrix.go-version }}
          fail_ci_if_error: false

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: go-test-results-${{ matrix.go-version }}
          path: |
            coverage.out
            benchmark.txt
          retention-days: 30

  # ============================================================================
  # Job 5: Python - Build, Test, Coverage
  # ============================================================================
  test-python:
    name: Python ${{ matrix.python-version }}
    needs: detect-changes
    if: |
      inputs.enable-python == true &&
      (inputs.skip-change-detection == true || needs.detect-changes.outputs.has-python-changes == 'true')
    runs-on: ubuntu-latest
    timeout-minutes: ${{ fromJson(inputs.test-timeout) }}
    strategy:
      fail-fast: false
      matrix:
        python-version: ${{ fromJson(inputs.python-versions) }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
          cache-dependency-path: |
            requirements*.txt
            pyproject.toml

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip wheel setuptools

          # Install project dependencies
          if [ -f requirements.txt ]; then
            pip install -r requirements.txt
          fi

          if [ -f requirements-dev.txt ]; then
            pip install -r requirements-dev.txt
          fi

          # Install testing tools
          pip install pytest pytest-cov pytest-xdist ruff mypy

      - name: Lint with ruff
        run: |
          echo "### 🔍 Linting with Ruff" >> $GITHUB_STEP_SUMMARY
          ruff check . --output-format=github

      - name: Type check with mypy
        continue-on-error: true
        run: |
          echo "### 🔍 Type Checking with Mypy" >> $GITHUB_STEP_SUMMARY
          mypy . --ignore-missing-imports --no-error-summary || true

      - name: Test with pytest and coverage
        if: inputs.enable-coverage == true
        run: |
          echo "### 🧪 Running Python Tests with Coverage" >> $GITHUB_STEP_SUMMARY
          pytest -v -n auto --cov --cov-report=xml --cov-report=term --cov-report=html

      - name: Test with pytest
        if: inputs.enable-coverage == false
        run: |
          echo "### 🧪 Running Python Tests" >> $GITHUB_STEP_SUMMARY
          pytest -v -n auto

      - name: Check coverage threshold
        if: inputs.enable-coverage == true && inputs.coverage-threshold > 0
        run: |
          coverage=$(python -c "import xml.etree.ElementTree as ET; tree = ET.parse('coverage.xml'); print(tree.getroot().attrib['line-rate'])")
          coverage_pct=$(echo "$coverage * 100" | bc)
          threshold=${{ inputs.coverage-threshold }}

          echo "Coverage: ${coverage_pct}%"
          echo "Threshold: ${threshold}%"

          if (( $(echo "$coverage_pct < $threshold" | bc -l) )); then
            echo "❌ Coverage ${coverage_pct}% is below threshold ${threshold}%"
            exit 1
          else
            echo "✅ Coverage ${coverage_pct}% meets threshold ${threshold}%"
          fi

      - name: Upload coverage to Codecov
        if: |
          inputs.enable-coverage == true &&
          matrix.python-version == fromJson(inputs.python-versions)[0]
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: python
          name: python-${{ matrix.python-version }}
          fail_ci_if_error: false

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: python-test-results-${{ matrix.python-version }}
          path: |
            coverage.xml
            htmlcov/
            .pytest_cache/
          retention-days: 30

# Continue in Part 4...
```

## Key Design Decisions

### 1. Configuration Hierarchy

The workflow uses a three-tier configuration system:

1. **Workflow Inputs**: Default values and basic configuration
2. **Repository Config File**: Repository-specific overrides (`.github/repository-config.yml`)
3. **Runtime Detection**: Dynamic decisions based on file changes

### 2. Output Variable Naming

To avoid GitHub Actions reserved keywords, all output variables use prefixes:

- `has-go-changes` instead of `go`
- `has-python-changes` instead of `python`
- etc.

### 3. Job Conditionals

Each job uses compound conditionals:

```yaml
if: |
  inputs.enable-{language} == true &&
  (inputs.skip-change-detection == true || needs.detect-changes.outputs.has-{language}-changes == 'true')
```

This ensures jobs run when:

- The language is enabled
- AND either change detection is skipped OR relevant files changed

### 4. Matrix Strategy

Version matrices are JSON arrays passed as inputs:

```yaml
strategy:
  fail-fast: false
  matrix:
    go-version: ${{ fromJson(inputs.go-versions) }}
```

### 5. Coverage Handling

Coverage is optional and controlled by `enable-coverage` input. When enabled:

- Tests run with coverage collection
- Coverage uploaded to Codecov
- Optional threshold checking
- Only upload from first version in matrix

### 6. Artifact Management

All test results uploaded as artifacts with:

- Descriptive names including version
- 30-day retention
- Always uploaded (even on failure)

## Continue to Part 4

Next part will complete the workflow implementation with:

- TypeScript/Node.js jobs
- Rust jobs
- Docker jobs
- Security scanning jobs
- Result aggregation job
