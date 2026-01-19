<!-- file: docs/cross-registry-todos/task-08/t08-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t08-ci-consolidation-part2-c8d9e0f1-g2h3 -->
<!-- last-edited: 2026-01-19 -->

# Task 08 Part 2: Detailed Workflow Feature Extraction

## Extracting Features from ghcommon/reusable-ci.yml

### Current File Location

**File:** `.github/workflows/reusable-ci.yml`

**Key Sections:**

```yaml
name: Reusable CI Workflow

on:
  workflow_call:
    inputs:
      go-version:
        required: false
        type: string
        default: '1.21'
      python-version:
        required: false
        type: string
        default: '3.11'
      node-version:
        required: false
        type: string
        default: '20'
      rust-version:
        required: false
        type: string
        default: 'stable'
```

### Feature 1: Change Detection Job

**Current Implementation:**

```yaml
jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      go_files: ${{ steps.filter.outputs.go }}
      python_files: ${{ steps.filter.outputs.python }}
      frontend_files: ${{ steps.filter.outputs.frontend }}
      rust_files: ${{ steps.filter.outputs.rust }}
      docker_files: ${{ steps.filter.outputs.docker }}

    steps:
      - uses: actions/checkout@v4

      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            go:
              - '**/*.go'
              - 'go.mod'
              - 'go.sum'
            python:
              - '**/*.py'
              - 'requirements*.txt'
              - 'pyproject.toml'
              - 'setup.py'
            frontend:
              - '**/*.ts'
              - '**/*.tsx'
              - '**/*.js'
              - '**/*.jsx'
              - 'package.json'
              - 'package-lock.json'
            rust:
              - '**/*.rs'
              - 'Cargo.toml'
              - 'Cargo.lock'
            docker:
              - '**/Dockerfile'
              - '**/Dockerfile.*'
              - 'docker-compose*.yml'
```

**Strengths:**

- Simple and effective
- Uses dorny/paths-filter action (reliable)
- Clear output variables
- Good default patterns

**Limitations:**

- Output names use reserved keywords (go, python, etc.)
- No documentation file detection
- No workflow file detection
- No protobuf detection
- Patterns not configurable

**Enhancements Needed:**

1. Rename outputs to avoid reserved keywords
2. Add more file type detections
3. Make patterns configurable via repository-config.yml
4. Add pattern exclusions

### Feature 2: Go Build and Test

**Current Implementation:**

```yaml
build-go:
  needs: detect-changes
  if: needs.detect-changes.outputs.go_files == 'true'
  runs-on: ubuntu-latest

  steps:
    - uses: actions/checkout@v4

    - uses: actions/setup-go@v5
      with:
        go-version: ${{ inputs.go-version }}
        cache: true

    - name: Build
      run: go build -v ./...

    - name: Test
      run: go test -v ./...

    - name: Lint
      uses: golangci/golangci-lint-action@v4
```

**Strengths:**

- Simple workflow
- Caching enabled
- Linting included

**Limitations:**

- No code coverage
- Single Go version only
- No race detection
- No benchmarks
- No artifact upload
- Basic test command (no options)

**Enhancements Needed:**

1. Add coverage with codecov upload
2. Support version matrix
3. Add race detection flag
4. Add benchmark job (optional)
5. Upload test results as artifacts
6. Make test command configurable

### Feature 3: Python Build and Test

**Current Implementation:**

```yaml
build-python:
  needs: detect-changes
  if: needs.detect-changes.outputs.python_files == 'true'
  runs-on: ubuntu-latest

  steps:
    - uses: actions/checkout@v4

    - uses: actions/setup-python@v5
      with:
        python-version: ${{ inputs.python-version }}
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi

    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

    - name: Test with pytest
      run: |
        pip install pytest
        pytest
```

**Strengths:**

- Pip caching
- Dependencies installed conditionally
- Basic linting

**Limitations:**

- No code coverage
- Single Python version
- Basic flake8 rules only
- No type checking (mypy)
- No modern linters (ruff)
- No test reports

**Enhancements Needed:**

1. Add pytest-cov for coverage
2. Support version matrix
3. Use ruff instead of flake8
4. Add mypy type checking
5. Upload test results
6. Upload coverage to codecov

### Feature 4: TypeScript/Frontend Build

**Current Implementation:**

```yaml
build-frontend:
  needs: detect-changes
  if: needs.detect-changes.outputs.frontend_files == 'true'
  runs-on: ubuntu-latest

  steps:
    - uses: actions/checkout@v4

    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Build
      run: npm run build

    - name: Test
      run: npm test

    - name: Lint
      run: npm run lint
```

**Strengths:**

- npm caching
- Standard npm scripts
- Build artifact generation

**Limitations:**

- No coverage reporting
- Single Node version
- Assumes npm (not yarn/pnpm)
- No type checking step
- No bundle size analysis

**Enhancements Needed:**

1. Add coverage reporting
2. Support version matrix
3. Support yarn/pnpm
4. Add explicit type checking
5. Bundle size analysis
6. Upload build artifacts

### Feature 5: Rust Build and Test

**Current Implementation:**

```yaml
build-rust:
  needs: detect-changes
  if: needs.detect-changes.outputs.rust_files == 'true'
  runs-on: ubuntu-latest

  steps:
    - uses: actions/checkout@v4

    - uses: dtolnay/rust-toolchain@stable
      with:
        components: rustfmt, clippy

    - uses: Swatinem/rust-cache@v2

    - name: Format check
      run: cargo fmt -- --check

    - name: Clippy
      run: cargo clippy -- -D warnings

    - name: Build
      run: cargo build --release

    - name: Test
      run: cargo test
```

**Strengths:**

- Rust caching (Swatinem)
- Format and lint checks
- Release build

**Limitations:**

- No code coverage
- Single Rust version
- No benchmarks
- No cross-compilation
- Basic test command

**Enhancements Needed:**

1. Add llvm-cov coverage
2. Support version matrix (stable/beta/nightly)
3. Add benchmarks
4. Cross-platform testing
5. Upload artifacts

### Feature 6: Docker Build

**Current Implementation:**

```yaml
build-docker:
  needs: detect-changes
  if: needs.detect-changes.outputs.docker_files == 'true'
  runs-on: ubuntu-latest

  steps:
    - uses: actions/checkout@v4

    - uses: docker/setup-buildx-action@v3

    - uses: docker/build-push-action@v5
      with:
        context: .
        push: false
        tags: ${{ github.repository }}:ci
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

**Strengths:**

- Buildx setup
- Layer caching via GitHub Actions cache

**Limitations:**

- No security scanning
- No multi-platform builds
- No SBOM generation
- No signing
- Single Dockerfile assumed

**Enhancements Needed:**

1. Add Trivy scanning
2. Multi-platform (amd64/arm64)
3. SBOM with syft
4. Cosign signing
5. Support multiple Dockerfiles

## Extracting Features from ubuntu-autoinstall-agent/ci.yml

### Current File Location

**File:** `.github/workflows/ci.yml`

**Key Sections:**

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: read
  checks: write
  security-events: write
```

### Feature 1: Enhanced Change Detection

**Current Implementation:**

```yaml
detect-changes:
  runs-on: ubuntu-latest
  outputs:
    go_files: ${{ steps.filter.outputs.go }}
    python_files: ${{ steps.filter.outputs.python }}
    frontend_files: ${{ steps.filter.outputs.frontend }}
    rust_files: ${{ steps.filter.outputs.rust }}
    docker_files: ${{ steps.filter.outputs.docker }}
    docs_files: ${{ steps.filter.outputs.docs }}
    workflows_files: ${{ steps.filter.outputs.workflows }}

  steps:
    - uses: actions/checkout@v4

    - uses: dorny/paths-filter@v3
      id: filter
      with:
        filters: |
          go:
            - '**/*.go'
            - 'go.mod'
            - 'go.sum'
            - '.github/workflows/*go*.yml'
          python:
            - '**/*.py'
            - 'requirements*.txt'
            - 'pyproject.toml'
            - 'setup.py'
            - 'setup.cfg'
            - 'tox.ini'
            - '.github/workflows/*python*.yml'
          frontend:
            - '**/*.ts'
            - '**/*.tsx'
            - '**/*.js'
            - '**/*.jsx'
            - 'package.json'
            - 'package-lock.json'
            - 'yarn.lock'
            - 'pnpm-lock.yaml'
            - '.github/workflows/*frontend*.yml'
          rust:
            - '**/*.rs'
            - 'Cargo.toml'
            - 'Cargo.lock'
            - '.cargo/**'
            - 'rust-toolchain.toml'
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
          workflows:
            - '.github/workflows/**'
            - '.github/actions/**'
```

**Strengths:**

- More comprehensive patterns
- Includes documentation
- Includes workflows
- Includes related workflow files
- More dependency file types

**Enhancements:**

- Configuration files included
- Lock files for all package managers

### Feature 2: Super-linter Integration

**Current Implementation:**

```yaml
super-lint:
  runs-on: ubuntu-latest
  permissions:
    contents: read
    statuses: write

  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Run Super-Linter
      uses: super-linter/super-linter@v6
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        VALIDATE_ALL_CODEBASE: false
        DEFAULT_BRANCH: main
        FILTER_REGEX_EXCLUDE: '.*/(node_modules|target|dist|build|__pycache__)/.*'
        # Language-specific linters
        VALIDATE_YAML: true
        VALIDATE_JSON: true
        VALIDATE_XML: true
        VALIDATE_MARKDOWN: true
        VALIDATE_BASH: true
        VALIDATE_DOCKERFILE: true
        VALIDATE_DOCKERFILE_HADOLINT: true
        # Disable linters handled elsewhere
        VALIDATE_GO: false # Using golangci-lint
        VALIDATE_PYTHON: false # Using ruff
        VALIDATE_JAVASCRIPT: false # Using eslint
        VALIDATE_TYPESCRIPT: false # Using eslint
```

**Strengths:**

- Comprehensive linting across file types
- Excludes build directories
- Selective validation
- Doesn't duplicate language-specific linters

**Integration:**

- Should be optional via input flag
- Configuration via repository-config.yml
- Respect existing linter configurations

### Feature 3: Go with Coverage

**Current Implementation:**

```yaml
test-go:
  needs: detect-changes
  if: needs.detect-changes.outputs.go_files == 'true'
  runs-on: ubuntu-latest
  strategy:
    matrix:
      go-version: ['1.21', '1.22']

  steps:
    - uses: actions/checkout@v4

    - uses: actions/setup-go@v5
      with:
        go-version: ${{ matrix.go-version }}
        cache: true
        cache-dependency-path: |
          go.sum
          **/go.sum

    - name: Build
      run: go build -v ./...

    - name: Test with coverage
      run: |
        go test -v -race -coverprofile=coverage.out -covermode=atomic ./...

    - name: Run benchmarks
      if: github.event_name == 'push' && github.ref == 'refs/heads/main'
      run: |
        go test -bench=. -benchmem -run=^$ ./... | tee benchmark.txt

    - name: Upload coverage
      if: matrix.go-version == '1.22'
      uses: codecov/codecov-action@v4
      with:
        files: ./coverage.out
        flags: go
        name: go-${{ matrix.go-version }}

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: go-test-results-${{ matrix.go-version }}
        path: |
          coverage.out
          benchmark.txt
```

**Strengths:**

- Version matrix
- Race detection
- Coverage upload to codecov
- Benchmark support
- Test result artifacts
- Coverage only from latest version

**Enhancements:**

- Configurable via repository-config.yml
- Optional benchmark flag
- Coverage threshold checking

### Feature 4: Python with Full Testing

**Current Implementation:**

```yaml
test-python:
  needs: detect-changes
  if: needs.detect-changes.outputs.python_files == 'true'
  runs-on: ubuntu-latest
  strategy:
    matrix:
      python-version: ['3.10', '3.11', '3.12']

  steps:
    - uses: actions/checkout@v4

    - uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
        cache: 'pip'
        cache-dependency-path: |
          requirements*.txt
          pyproject.toml

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip wheel
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        pip install pytest pytest-cov ruff mypy

    - name: Lint with ruff
      run: ruff check .

    - name: Type check with mypy
      run: mypy . --ignore-missing-imports

    - name: Test with pytest
      run: |
        pytest -v --cov --cov-report=xml --cov-report=term

    - name: Upload coverage
      if: matrix.python-version == '3.12'
      uses: codecov/codecov-action@v4
      with:
        files: ./coverage.xml
        flags: python
        name: python-${{ matrix.python-version }}

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: python-test-results-${{ matrix.python-version }}
        path: |
          coverage.xml
          .pytest_cache
```

**Strengths:**

- Version matrix
- Modern linter (ruff)
- Type checking (mypy)
- Coverage with pytest-cov
- Upload to codecov
- Test artifacts

**Enhancements:**

- Configurable tools
- Coverage threshold
- Separate type checking job (optional)

### Feature 5: Rust with llvm-cov

**Current Implementation:**

```yaml
test-rust:
  needs: detect-changes
  if: needs.detect-changes.outputs.rust_files == 'true'
  runs-on: ubuntu-latest
  strategy:
    matrix:
      rust-version: ['stable', 'nightly']

  steps:
    - uses: actions/checkout@v4

    - uses: dtolnay/rust-toolchain@master
      with:
        toolchain: ${{ matrix.rust-version }}
        components: rustfmt, clippy, llvm-tools-preview

    - uses: Swatinem/rust-cache@v2
      with:
        cache-all-crates: true

    - name: Install cargo-llvm-cov
      run: cargo install cargo-llvm-cov

    - name: Format check
      run: cargo fmt -- --check

    - name: Clippy
      run: cargo clippy --all-features --all-targets -- -D warnings

    - name: Build
      run: cargo build --release --all-features

    - name: Test
      run: cargo test --all-features

    - name: Coverage
      if: matrix.rust-version == 'stable'
      run: |
        mkdir -p htmlcov
        cargo llvm-cov --all-features --lcov --output-path lcov.info --verbose

    - name: Upload coverage
      if: matrix.rust-version == 'stable'
      uses: codecov/codecov-action@v4
      with:
        files: ./lcov.info
        flags: rust
        name: rust-${{ matrix.rust-version }}

    - name: Run benchmarks
      if: matrix.rust-version == 'nightly' && github.ref == 'refs/heads/main'
      run: cargo bench --no-fail-fast
```

**Strengths:**

- Version matrix (stable/nightly)
- llvm-cov for coverage
- All features tested
- Benchmarks on nightly
- Comprehensive clippy

**Enhancements:**

- Cross-compilation matrix
- Coverage threshold
- Artifact uploads

### Feature 6: Docker with Security

**Current Implementation:**

```yaml
build-docker:
  needs: detect-changes
  if: needs.detect-changes.outputs.docker_files == 'true'
  runs-on: ubuntu-latest
  permissions:
    security-events: write

  steps:
    - uses: actions/checkout@v4

    - uses: docker/setup-qemu-action@v3

    - uses: docker/setup-buildx-action@v3

    - name: Build image
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: false
        tags: ${{ github.repository }}:ci
        cache-from: type=gha
        cache-to: type=gha,mode=max
        outputs: type=docker,dest=/tmp/image.tar

    - name: Load image
      run: docker load --input /tmp/image.tar

    - name: Run Trivy scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ github.repository }}:ci
        format: 'sarif'
        output: 'trivy-results.sarif'
        severity: 'CRITICAL,HIGH'

    - name: Upload Trivy results
      uses: github/codeql-action/upload-sarif@v3
      with:
        sarif_file: 'trivy-results.sarif'

    - name: Generate SBOM
      uses: anchore/sbom-action@v0
      with:
        image: ${{ github.repository }}:ci
        format: spdx-json
        output-file: sbom.spdx.json

    - name: Upload SBOM
      uses: actions/upload-artifact@v4
      with:
        name: docker-sbom
        path: sbom.spdx.json
```

**Strengths:**

- Multi-platform builds
- Trivy security scanning
- SBOM generation
- SARIF upload for security
- Image export/load for scanning

**Enhancements:**

- Cosign signing
- Vulnerability thresholds
- Multiple Dockerfile support

### Feature 7: Security Scanning

**Current Implementation:**

```yaml
security-scan:
  runs-on: ubuntu-latest
  permissions:
    security-events: write
    contents: read

  steps:
    - uses: actions/checkout@v4

    - name: Run CodeQL
      uses: github/codeql-action/init@v3
      with:
        languages: go, python, javascript

    - name: Autobuild
      uses: github/codeql-action/autobuild@v3

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v3

    - name: Dependency Review
      if: github.event_name == 'pull_request'
      uses: actions/dependency-review-action@v4
      with:
        fail-on-severity: high
```

**Strengths:**

- CodeQL for multiple languages
- Dependency review on PRs
- Configurable severity

**Integration:**

- Should run alongside other jobs
- Optional via feature flag

## Merged Feature Set

### Combined Change Detection

```yaml
detect-changes:
  runs-on: ubuntu-latest
  outputs:
    # Avoid reserved keywords
    has-go-changes: ${{ steps.filter.outputs.go }}
    has-python-changes: ${{ steps.filter.outputs.python }}
    has-typescript-changes: ${{ steps.filter.outputs.typescript }}
    has-rust-changes: ${{ steps.filter.outputs.rust }}
    has-docker-changes: ${{ steps.filter.outputs.docker }}
    has-docs-changes: ${{ steps.filter.outputs.docs }}
    has-workflow-changes: ${{ steps.filter.outputs.workflows }}
    has-protobuf-changes: ${{ steps.filter.outputs.protobuf }}

  steps:
    - uses: actions/checkout@v4

    - name: Load repository config
      id: config
      run: |
        if [ -f ".github/repository-config.yml" ]; then
          # Parse config and set patterns
          echo "config_exists=true" >> $GITHUB_OUTPUT
        fi

    - uses: dorny/paths-filter@v3
      id: filter
      with:
        filters: |
          go:
            - '**/*.go'
            - 'go.mod'
            - 'go.sum'
            - '.github/workflows/*go*.yml'
          python:
            - '**/*.py'
            - 'requirements*.txt'
            - 'pyproject.toml'
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
            - 'package-lock.json'
            - 'yarn.lock'
            - 'pnpm-lock.yaml'
            - 'tsconfig.json'
            - '.github/workflows/*frontend*.yml'
            - '.github/workflows/*typescript*.yml'
          rust:
            - '**/*.rs'
            - 'Cargo.toml'
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
          workflows:
            - '.github/workflows/**'
            - '.github/actions/**'
          protobuf:
            - '**/*.proto'
            - 'buf.yaml'
            - 'buf.gen.yaml'
            - 'buf.lock'
            - '.github/workflows/*proto*.yml'
```

## Next Steps

**Continue to Part 3:** Design the consolidated workflow structure with all features integrated.
