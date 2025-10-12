<!-- file: docs/cross-registry-todos/task-08/t08-part1.md -->
<!-- version: 1.1.0 -->
<!-- guid: t08-ci-consolidation-part1-b7c8d9e0-f1g2 -->

# Task 08 Part 1: CI Workflow Consolidation - Overview

> **Status:** ✅ Completed  
> **Updated:** `.github/workflows/reusable-ci.yml` v1.1.0 unifies change-detection,
> language-specific lint/test gates, coverage enforcement, protobuf generation hooks, and CI
> summaries for downstream callers.  
> **Verification:** Reusable CI entries now provide per-language jobs with shared inputs and
> guardrails, replacing bespoke logic present in downstream repositories.

## Task Overview

**Priority:** 3 (High) **Estimated Lines:** ~3,500 lines (6 parts) **Complexity:** High
**Dependencies:** Tasks 01-07

## Objective

Consolidate and merge the two CI workflow implementations:

1. **ghcommon/reusable-ci.yml** - Reusable workflow for cross-repository use
2. **ubuntu-autoinstall-agent/ci.yml** - Specific implementation with advanced features

Create a unified, feature-complete reusable CI workflow that can be used across all repositories
while maintaining backward compatibility and adding missing features.

## What This Task Accomplishes

### Primary Goals

1. **Analyze Both Workflows**: Comprehensive comparison of features and capabilities
2. **Identify Gaps**: Find missing features in reusable workflow
3. **Merge Implementations**: Combine best features from both workflows
4. **Maintain Compatibility**: Ensure existing callers continue to work
5. **Add Enhancements**: Implement missing features (coverage, security scanning, etc.)
6. **Update Documentation**: Complete usage guide for consolidated workflow

### Current Workflow Comparison

#### ghcommon/reusable-ci.yml (Reusable)

**Current Features:**

- Reusable workflow design (`workflow_call`)
- Change detection with intelligent file filtering
- Multi-language support (Go, Python, TypeScript, Rust)
- Build and test jobs
- Docker image building
- Basic matrix strategy

**Missing Features:**

- Code coverage reporting
- Security scanning (Trivy, Snyk)
- Super-linter integration
- Detailed test reports
- Cache optimization
- Advanced matrix configurations
- Performance benchmarking

#### ubuntu-autoinstall-agent/ci.yml (Specific)

**Current Features:**

- Comprehensive change detection
- Super-linter integration
- Code coverage (codecov, llvm-cov)
- Security scanning (Trivy)
- Dependency review
- Test result reporting
- Advanced caching strategies
- Performance benchmarks
- Detailed job outputs

**Limitations:**

- Not reusable across repositories
- Hard-coded repository-specific values
- Duplication with reusable workflow

## Consolidation Strategy

### Phase 1: Analysis

1. Extract all features from both workflows
2. Create feature matrix comparison
3. Identify overlapping functionality
4. Document unique features
5. Plan integration approach

### Phase 2: Design

1. Design unified workflow structure
2. Define reusable inputs/outputs
3. Plan backward compatibility
4. Design configuration system
5. Document migration path

### Phase 3: Implementation

1. Merge workflows into single reusable workflow
2. Add missing features from ubuntu-autoinstall-agent
3. Implement repository-config.yml integration
4. Add comprehensive caching
5. Enhance test reporting

### Phase 4: Migration

1. Update ghcommon to use consolidated workflow
2. Update ubuntu-autoinstall-agent to use consolidated workflow
3. Update other repositories
4. Remove old workflow implementations
5. Update documentation

## Feature Comparison Matrix

### Change Detection

| Feature                           | ghcommon/reusable-ci.yml | ubuntu-autoinstall-agent/ci.yml |
| --------------------------------- | ------------------------ | ------------------------------- |
| Go files detection                | ✅                       | ✅                              |
| Python files detection            | ✅                       | ✅                              |
| TypeScript/Frontend detection     | ✅                       | ✅                              |
| Rust files detection              | ✅                       | ✅                              |
| Docker files detection            | ✅                       | ✅                              |
| Documentation detection           | ❌                       | ✅                              |
| GitHub Actions workflow detection | ❌                       | ✅                              |
| Configuration file detection      | ❌                       | ✅                              |
| Test file detection               | ✅ Basic                 | ✅ Advanced                     |
| Output variables                  | ✅                       | ✅                              |

### Go Jobs

| Feature              | ghcommon/reusable-ci.yml | ubuntu-autoinstall-agent/ci.yml |
| -------------------- | ------------------------ | ------------------------------- |
| Build                | ✅                       | ✅                              |
| Test                 | ✅                       | ✅                              |
| Lint (golangci-lint) | ✅                       | ✅                              |
| Code coverage        | ❌                       | ✅ (codecov)                    |
| Multiple Go versions | ❌                       | ✅ Matrix                       |
| Dependency caching   | ✅ Basic                 | ✅ Advanced                     |
| Build artifacts      | ✅                       | ✅                              |
| Benchmarks           | ❌                       | ✅                              |
| Race detection       | ❌                       | ✅                              |

### Python Jobs

| Feature                  | ghcommon/reusable-ci.yml | ubuntu-autoinstall-agent/ci.yml |
| ------------------------ | ------------------------ | ------------------------------- |
| Build/Install            | ✅                       | ✅                              |
| Test (pytest)            | ✅                       | ✅                              |
| Lint (flake8/black)      | ✅                       | ✅ (ruff)                       |
| Type checking (mypy)     | ❌                       | ✅                              |
| Code coverage            | ❌                       | ✅ (pytest-cov)                 |
| Multiple Python versions | ❌                       | ✅ Matrix                       |
| Virtual environment      | ✅                       | ✅                              |
| Requirements caching     | ✅                       | ✅                              |
| Test reports             | ❌                       | ✅                              |

### TypeScript/Frontend Jobs

| Feature                | ghcommon/reusable-ci.yml | ubuntu-autoinstall-agent/ci.yml |
| ---------------------- | ------------------------ | ------------------------------- |
| Build                  | ✅                       | ✅                              |
| Test                   | ✅                       | ✅                              |
| Lint (eslint)          | ✅                       | ✅                              |
| Type checking (tsc)    | ✅                       | ✅                              |
| Code coverage          | ❌                       | ✅ (jest/vitest)                |
| Multiple Node versions | ❌                       | ✅ Matrix                       |
| npm/yarn/pnpm support  | ✅                       | ✅                              |
| Build artifact upload  | ✅                       | ✅                              |
| Bundle size analysis   | ❌                       | ✅                              |

### Rust Jobs

| Feature                | ghcommon/reusable-ci.yml | ubuntu-autoinstall-agent/ci.yml |
| ---------------------- | ------------------------ | ------------------------------- |
| Build                  | ✅                       | ✅                              |
| Test                   | ✅                       | ✅                              |
| Clippy linting         | ✅                       | ✅                              |
| Rustfmt checking       | ✅                       | ✅                              |
| Code coverage          | ❌                       | ✅ (llvm-cov)                   |
| Multiple Rust versions | ❌                       | ✅ Matrix                       |
| Cargo caching          | ✅                       | ✅ Advanced                     |
| Cross-compilation      | ❌                       | ✅                              |
| Benchmarks             | ❌                       | ✅                              |

### Docker Jobs

| Feature               | ghcommon/reusable-ci.yml | ubuntu-autoinstall-agent/ci.yml |
| --------------------- | ------------------------ | ------------------------------- |
| Image building        | ✅                       | ✅                              |
| Multi-platform builds | ✅                       | ✅                              |
| Security scanning     | ❌                       | ✅ (Trivy)                      |
| SBOM generation       | ❌                       | ✅ (syft)                       |
| Image signing         | ❌                       | ✅ (Cosign)                     |
| Layer caching         | ✅                       | ✅                              |
| Registry push         | ✅                       | ✅                              |
| Size optimization     | ❌                       | ✅                              |

### Quality & Security

| Feature            | ghcommon/reusable-ci.yml | ubuntu-autoinstall-agent/ci.yml |
| ------------------ | ------------------------ | ------------------------------- |
| Super-linter       | ❌                       | ✅                              |
| CodeQL             | ❌                       | ✅                              |
| Dependency review  | ❌                       | ✅                              |
| License checking   | ❌                       | ✅                              |
| Secret scanning    | ❌                       | ✅                              |
| SARIF upload       | ❌                       | ✅                              |
| Security reporting | ❌                       | ✅                              |

### Reporting & Artifacts

| Feature             | ghcommon/reusable-ci.yml | ubuntu-autoinstall-agent/ci.yml |
| ------------------- | ------------------------ | ------------------------------- |
| Test result upload  | ❌                       | ✅                              |
| Coverage reports    | ❌                       | ✅                              |
| Build artifacts     | ✅                       | ✅                              |
| Performance metrics | ❌                       | ✅                              |
| Job summaries       | ❌                       | ✅                              |
| Badge generation    | ❌                       | ✅                              |
| Retention policies  | ✅ Basic                 | ✅ Advanced                     |

## Proposed Consolidated Workflow Structure

```yaml
name: Consolidated CI

on:
  workflow_call:
    inputs:
      # Change detection
      skip-change-detection:
        type: boolean
        default: false

      # Language enables
      enable-go:
        type: boolean
        default: true
      enable-python:
        type: boolean
        default: true
      enable-typescript:
        type: boolean
        default: true
      enable-rust:
        type: boolean
        default: true
      enable-docker:
        type: boolean
        default: true

      # Feature flags
      enable-coverage:
        type: boolean
        default: true
      enable-security-scan:
        type: boolean
        default: true
      enable-super-linter:
        type: boolean
        default: true
      enable-benchmarks:
        type: boolean
        default: false

      # Version matrices
      go-versions:
        type: string
        default: '["1.21"]'
      python-versions:
        type: string
        default: '["3.11"]'
      node-versions:
        type: string
        default: '["20"]'
      rust-versions:
        type: string
        default: '["stable"]'

      # Configuration
      config-file:
        type: string
        default: '.github/repository-config.yml'
      working-directory:
        type: string
        default: '.'

    outputs:
      # Change detection outputs
      has-go-changes:
        value: ${{ jobs.detect-changes.outputs.go }}
      has-python-changes:
        value: ${{ jobs.detect-changes.outputs.python }}
      has-typescript-changes:
        value: ${{ jobs.detect-changes.outputs.typescript }}
      has-rust-changes:
        value: ${{ jobs.detect-changes.outputs.rust }}
      has-docker-changes:
        value: ${{ jobs.detect-changes.outputs.docker }}

      # Test result outputs
      tests-passed:
        value: ${{ jobs.report-results.outputs.all-tests-passed }}
      coverage-percentage:
        value: ${{ jobs.report-results.outputs.coverage }}

jobs:
  # 1. Load configuration
  load-config:
    # Read repository-config.yml

  # 2. Detect changes
  detect-changes:
    # Enhanced change detection with configurable patterns

  # 3. Super-linter
  super-lint:
    # Comprehensive linting across all file types

  # 4. Language-specific jobs (with matrices)
  test-go:
    strategy:
      matrix:
        go-version: ${{ fromJson(inputs.go-versions) }}

  test-python:
    strategy:
      matrix:
        python-version: ${{ fromJson(inputs.python-versions) }}

  test-typescript:
    strategy:
      matrix:
        node-version: ${{ fromJson(inputs.node-versions) }}

  test-rust:
    strategy:
      matrix:
        rust-version: ${{ fromJson(inputs.rust-versions) }}

  # 5. Security scanning
  security-scan:
    # CodeQL, Trivy, dependency review

  # 6. Build Docker images
  build-docker:
    # Multi-platform with security scanning

  # 7. Collect and report results
  report-results:
    # Aggregate all test results, coverage, metrics
```

## Repository-Config Integration

### Example repository-config.yml

```yaml
# .github/repository-config.yml
ci:
  # Language configurations
  languages:
    go:
      enabled: true
      versions: ['1.21', '1.22']
      test-command: 'go test -v -race -coverprofile=coverage.out ./...'
      lint-command: 'golangci-lint run'
      benchmark-command: 'go test -bench=. -benchmem'
      coverage-threshold: 80

    python:
      enabled: true
      versions: ['3.10', '3.11', '3.12']
      test-command: 'pytest -v --cov --cov-report=xml'
      lint-command: 'ruff check .'
      type-check-command: 'mypy .'
      coverage-threshold: 85

    typescript:
      enabled: true
      versions: ['18', '20']
      test-command: 'npm test'
      lint-command: 'npm run lint'
      build-command: 'npm run build'
      coverage-threshold: 75

    rust:
      enabled: true
      versions: ['stable', 'nightly']
      test-command: 'cargo test --all-features'
      lint-command: 'cargo clippy -- -D warnings'
      coverage-command: 'cargo llvm-cov --all-features --lcov'
      coverage-threshold: 90

  # Feature flags
  features:
    super-linter: true
    security-scan: true
    code-coverage: true
    benchmarks: false
    docker-build: true

  # Docker configuration
  docker:
    platforms: ['linux/amd64', 'linux/arm64']
    registry: 'ghcr.io'
    scan-security: true
    generate-sbom: true

  # Change detection patterns
  change-detection:
    go:
      - '**/*.go'
      - 'go.mod'
      - 'go.sum'
    python:
      - '**/*.py'
      - 'requirements*.txt'
      - 'pyproject.toml'
      - 'setup.py'
    typescript:
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
```

## Migration Path

### Step 1: Create Consolidated Workflow

Create `.github/workflows/reusable-ci-consolidated.yml` with all features from both workflows.

### Step 2: Update Callers Gradually

```yaml
# Repository workflow (.github/workflows/ci.yml)
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  ci:
    uses: jdfalk/ghcommon/.github/workflows/reusable-ci-consolidated.yml@main
    with:
      enable-go: true
      enable-python: true
      enable-coverage: true
      enable-security-scan: true
    secrets: inherit
```

### Step 3: Deprecate Old Workflows

1. Add deprecation notice to `reusable-ci.yml`
2. Update all repositories to use consolidated workflow
3. After migration period, remove old workflow

## Success Criteria

- [ ] All features from both workflows merged
- [ ] Backward compatibility maintained
- [ ] Repository-config.yml integration complete
- [ ] Comprehensive test coverage
- [ ] Security scanning included
- [ ] Documentation complete
- [ ] All repositories migrated
- [ ] Performance equivalent or better

## Expected Benefits

1. **Single Source of Truth**: One reusable workflow for all CI needs
2. **Feature Parity**: Best features from both workflows
3. **Configuration**: Repository-specific customization via config file
4. **Maintainability**: Single workflow to update and improve
5. **Consistency**: Same CI experience across all repositories
6. **Enhanced Quality**: Better test coverage, security scanning, reporting

## Next Steps

**Continue to Part 2:** Detailed feature analysis and extraction from both workflows.
