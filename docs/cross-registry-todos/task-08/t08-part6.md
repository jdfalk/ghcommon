<!-- file: docs/cross-registry-todos/task-08/t08-part6.md -->
<!-- version: 1.0.0 -->
<!-- guid: t08-ci-consolidation-part6-g2h3i4j5-k6l7 -->
<!-- last-edited: 2026-01-19 -->

# Task 08 Part 6: Troubleshooting & Best Practices

## Troubleshooting Guide

### Issue 1: Change Detection Not Working

**Symptoms:**

- Jobs not running when files change
- All jobs skipped unexpectedly
- Jobs running when they shouldn't

**Causes:**

1. Incorrect path patterns in `paths-filter` configuration
2. Reserved keyword conflicts in output names
3. Branch protection rules blocking job execution
4. Missing `fetch-depth: 0` for proper diff

**Solutions:**

**Solution 1: Verify path patterns**

```bash
# Test path patterns locally
git diff --name-only HEAD~1 | grep -E '\.go$|go\.mod|go\.sum'

# Check which files changed
git log -1 --name-only
```

**Solution 2: Check output variable names**

```yaml
# ❌ WRONG - uses reserved keywords
outputs:
  go: ${{ steps.filter.outputs.go }}
  python: ${{ steps.filter.outputs.python }}

# ✅ CORRECT - avoids reserved keywords
outputs:
  has-go-changes: ${{ steps.filter.outputs.go }}
  has-python-changes: ${{ steps.filter.outputs.python }}
```

**Solution 3: Update conditionals**

```yaml
# Make sure job conditionals reference correct output names
if: |
  inputs.enable-go == true &&
  (inputs.skip-change-detection == true || needs.detect-changes.outputs.has-go-changes == 'true')
```

**Solution 4: Debug change detection**

```yaml
- name: Debug change detection
  run: |
    echo "Changed files:"
    git diff --name-only ${{ github.event.before }} ${{ github.sha }}

    echo "Filter outputs:"
    echo "go: ${{ steps.filter.outputs.go }}"
    echo "python: ${{ steps.filter.outputs.python }}"
```

### Issue 2: Matrix Jobs Failing

**Symptoms:**

- Some versions pass, others fail
- Inconsistent test results across versions
- Version-specific dependency conflicts

**Causes:**

1. Version-specific syntax or feature differences
2. Dependency compatibility issues
3. Test environment differences
4. Cache conflicts between versions

**Solutions:**

**Solution 1: Isolate version-specific issues**

```bash
# Test locally with specific version
docker run --rm -v "$PWD:/app" -w /app golang:1.21 go test ./...
docker run --rm -v "$PWD:/app" -w /app golang:1.22 go test ./...

# Python
docker run --rm -v "$PWD:/app" -w /app python:3.10 pytest
docker run --rm -v "$PWD:/app" -w /app python:3.12 pytest
```

**Solution 2: Add version-specific conditionals**

```yaml
- name: Install version-specific dependencies
  run: |
    if [[ "${{ matrix.python-version }}" == "3.12" ]]; then
      # Python 3.12 specific setup
      pip install setuptools  # Required in 3.12
    fi
```

**Solution 3: Use separate cache keys per version**

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('**/requirements*.txt') }}
```

**Solution 4: Allow failure for experimental versions**

```yaml
strategy:
  matrix:
    go-version: ['1.21', '1.22', '1.23-rc']
  fail-fast: false

steps:
  - name: Test
    continue-on-error: ${{ matrix.go-version == '1.23-rc' }}
    run: go test ./...
```

### Issue 3: Coverage Not Uploading

**Symptoms:**

- Coverage files generated but not uploaded
- Codecov upload fails
- Coverage percentage incorrect

**Causes:**

1. Coverage file not found
2. Codecov token missing or incorrect
3. Multiple uploads from matrix jobs
4. Coverage format incompatible

**Solutions:**

**Solution 1: Verify coverage file generation**

```yaml
- name: Test with coverage
  run: |
    go test -v -race -coverprofile=coverage.out ./...

    # Verify file exists and has content
    ls -lh coverage.out
    head -n 5 coverage.out
```

**Solution 2: Upload only from specific version**

```yaml
- name: Upload coverage
  if: matrix.go-version == '1.22' # Only latest version
  uses: codecov/codecov-action@v4
  with:
    files: ./coverage.out
    flags: go
    name: go-${{ matrix.go-version }}
    fail_ci_if_error: false # Don't fail CI on upload error
```

**Solution 3: Use correct coverage format**

```yaml
# Go - use -coverprofile
go test -v -coverprofile=coverage.out -covermode=atomic ./...

# Python - use pytest-cov
pytest --cov --cov-report=xml --cov-report=term

# Rust - use cargo-llvm-cov
cargo llvm-cov --all-features --lcov --output-path lcov.info

# TypeScript - configure in jest/vitest config
npm test -- --coverage --coverageReporters=lcov
```

**Solution 4: Debug upload**

```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    files: ./coverage.out
    flags: go
    verbose: true # Enable verbose logging
    fail_ci_if_error: true # Fail to see error details
```

### Issue 4: Security Scan False Positives

**Symptoms:**

- Many low-priority security issues
- Vulnerabilities in transitive dependencies
- Issues in test/dev dependencies

**Causes:**

1. Overly strict severity settings
2. Including dev/test dependencies in scan
3. Known issues without fixes available
4. False positives in scanning tools

**Solutions:**

**Solution 1: Adjust severity threshold**

```yaml
- name: Run Trivy scanner
  uses: aquasecurity/trivy-action@master
  with:
    severity: 'CRITICAL,HIGH' # Only critical and high
    ignore-unfixed: true # Ignore issues without fixes
```

**Solution 2: Exclude test dependencies**

```yaml
# Python - separate production and dev requirements
pip install -r requirements.txt  # Production only

# Node.js - use --production
npm ci --production

# Go - use -tags
go build -tags production
```

**Solution 3: Create ignore file**

```yaml
# .trivyignore
CVE-2021-12345  # False positive - see issue #123
CVE-2022-67890  # Accepted risk - dev dependency only
```

**Solution 4: Use allowlist for known issues**

```yaml
- name: Security scan with exceptions
  run: |
    # Run scan and filter known issues
    trivy image myimage:tag \
      --severity CRITICAL,HIGH \
      --ignore-unfixed \
      --ignorefile .trivyignore \
      --exit-code 1
```

### Issue 5: Docker Build Platform Failures

**Symptoms:**

- ARM64 build fails while AMD64 succeeds
- Platform-specific test failures
- Architecture-specific dependencies missing

**Causes:**

1. Platform-specific build tools missing
2. Architecture-specific dependencies
3. Emulation overhead causing timeouts
4. Platform-specific base image issues

**Solutions:**

**Solution 1: Install cross-platform tools**

```dockerfile
# Dockerfile - use multi-arch base images
FROM --platform=$BUILDPLATFORM golang:1.22-alpine AS builder

# Install platform-specific tools
RUN apk add --no-cache \
    gcc \
    musl-dev \
    $([ "$TARGETARCH" = "arm64" ] && echo "gcc-aarch64-linux-gnu" || echo "")
```

**Solution 2: Use native runners**

```yaml
strategy:
  matrix:
    platform:
      - runner: ubuntu-latest
        arch: amd64
      - runner: ubuntu-latest-arm64
        arch: arm64

steps:
  - uses: docker/build-push-action@v5
    with:
      platforms: linux/${{ matrix.arch }}
```

**Solution 3: Increase timeout for ARM builds**

```yaml
- name: Build Docker image
  timeout-minutes: 60 # Increased from 30
  uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64,linux/arm64
```

**Solution 4: Test platforms separately**

```yaml
# Build all platforms
- name: Build multi-platform image
  uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64,linux/arm64
    push: false
    outputs: type=docker,dest=/tmp/image.tar

# Test each platform
- name: Test AMD64
  run: |
    docker load --input /tmp/image.tar
    docker run --platform linux/amd64 myimage:test

- name: Test ARM64
  run: |
    docker run --platform linux/arm64 myimage:test
```

### Issue 6: Workflow Timeout

**Symptoms:**

- Jobs timeout after 6 hours (default)
- Some tests never complete
- Hanging processes

**Causes:**

1. Infinite loops in tests
2. Deadlocks in concurrent code
3. Waiting for external resources
4. Insufficient resources

**Solutions:**

**Solution 1: Set reasonable timeouts**

```yaml
jobs:
  test-go:
    timeout-minutes: 30 # Per-job timeout

    steps:
      - name: Test
        timeout-minutes: 20 # Per-step timeout
        run: go test -timeout=15m ./...
```

**Solution 2: Add test timeouts**

```go
// Go - use testing.Short() for long tests
func TestLongRunning(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping long-running test")
    }
    // Long test here
}

// Run with timeout
// go test -short -timeout=5m ./...
```

```python
# Python - use pytest timeout plugin
import pytest

@pytest.mark.timeout(10)
def test_slow_function():
    slow_function()
```

**Solution 3: Identify hanging tests**

```bash
# Run tests with verbose output
go test -v -timeout=5m ./... 2>&1 | tee test-output.log

# Find last test before hang
tail -n 50 test-output.log
```

**Solution 4: Use test parallelization limits**

```yaml
# Limit parallel test execution
- name: Test
  run: |
    # Go - limit parallel tests
    go test -p 4 ./...

    # Python - limit pytest workers
    pytest -n 4

    # Rust - limit parallel jobs
    cargo test -j 4
```

### Issue 7: Artifact Upload Failures

**Symptoms:**

- Artifacts not appearing in workflow
- Upload fails with "no files found"
- Artifact size exceeds limit

**Causes:**

1. Incorrect path specification
2. Files not generated yet
3. Artifact too large (10GB limit)
4. Insufficient permissions

**Solutions:**

**Solution 1: Verify file paths**

```yaml
- name: Upload artifacts
  run: |
    # List files to upload
    echo "Files to upload:"
    find . -name "coverage.out" -o -name "*.log"

    # Check sizes
    du -sh coverage.out test-results/
```

**Solution 2: Use wildcards correctly**

```yaml
# ❌ WRONG - missing files
- uses: actions/upload-artifact@v4
  with:
    path: coverage.out # Only this exact file

# ✅ CORRECT - includes all coverage files
- uses: actions/upload-artifact@v4
  with:
    path: |
      coverage.out
      **/coverage.out
      htmlcov/
```

**Solution 3: Split large artifacts**

```yaml
# Upload separately instead of one large artifact
- uses: actions/upload-artifact@v4
  with:
    name: coverage-reports
    path: |
      coverage.out
      htmlcov/
    retention-days: 7 # Shorter retention for large files

- uses: actions/upload-artifact@v4
  with:
    name: test-logs
    path: |
      test-*.log
    retention-days: 3
```

**Solution 4: Compress before upload**

```yaml
- name: Compress artifacts
  run: |
    tar -czf artifacts.tar.gz coverage/ htmlcov/ logs/

- uses: actions/upload-artifact@v4
  with:
    name: compressed-artifacts
    path: artifacts.tar.gz
```

### Issue 8: Repository Config Not Loading

**Symptoms:**

- Default values used instead of config
- Config parsing errors
- Config file not found

**Causes:**

1. Config file in wrong location
2. YAML syntax errors
3. Invalid config structure
4. File not committed to repository

**Solutions:**

**Solution 1: Validate config file**

```bash
# Validate YAML syntax
yamllint .github/repository-config.yml

# Check structure with yq
yq eval '.ci' .github/repository-config.yml
```

**Solution 2: Debug config loading**

```yaml
- name: Load repository config
  id: config
  run: |
    if [ -f "${{ inputs.config-file }}" ]; then
      echo "✅ Config file found"
      cat "${{ inputs.config-file }}"
    else
      echo "❌ Config file not found: ${{ inputs.config-file }}"
      echo "Files in .github/:"
      ls -la .github/
    fi
```

**Solution 3: Provide fallback values**

```yaml
- name: Parse config with fallbacks
  run: |
    if [ -f ".github/repository-config.yml" ]; then
      go_versions=$(yq eval '.ci.languages.go.versions' .github/repository-config.yml)
    else
      go_versions='["1.21"]'  # Fallback
    fi

    echo "go_versions=$go_versions" >> $GITHUB_OUTPUT
```

### Issue 9: Permission Denied Errors

**Symptoms:**

- Cannot push to registry
- Cannot write SARIF results
- Cannot create releases

**Causes:**

1. Missing workflow permissions
2. Incorrect secrets
3. Token expiration
4. Organization security policies

**Solutions:**

**Solution 1: Add required permissions**

```yaml
jobs:
  build-docker:
    permissions:
      contents: read # Read repository
      packages: write # Push to GHCR
      security-events: write # Upload SARIF
      actions: read # Read workflow artifacts
```

**Solution 2: Use correct token**

```yaml
# Use GITHUB_TOKEN for most operations
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

# Use PAT for cross-repository operations
env:
  GH_TOKEN: ${{ secrets.PERSONAL_ACCESS_TOKEN }}
```

**Solution 3: Check token scopes**

```bash
# List scopes of GitHub token
gh auth status

# Required scopes for common operations:
# - repo (full repository access)
# - packages:write (push packages)
# - workflow (update workflows)
```

### Issue 10: Cache Invalidation

**Symptoms:**

- Tests fail after dependency updates
- Builds use old dependencies
- Cache never refreshes

**Causes:**

1. Cache key doesn't include dependency files
2. Dependencies changed without updating lockfile
3. Cache size limit exceeded
4. Cache corruption

**Solutions:**

**Solution 1: Include lockfiles in cache key**

```yaml
# ✅ CORRECT - cache invalidates when dependencies change
- uses: actions/cache@v4
  with:
    path: ~/.cache/go-build
    key: ${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}
    restore-keys: |
      ${{ runner.os }}-go-
```

**Solution 2: Clear cache manually**

```bash
# Delete workflow caches
gh cache list
gh cache delete <cache-id>

# Or delete all caches
gh cache list | awk '{print $1}' | xargs -I {} gh cache delete {}
```

**Solution 3: Add cache version to key**

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: v2-${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
    #    ^^ increment when cache needs refresh
```

**Solution 4: Set cache size limits**

```yaml
- name: Prune cache
  run: |
    # Go - clean build cache
    go clean -cache -modcache

    # Rust - target directory cleanup
    cargo clean --release

    # Node - remove node_modules
    rm -rf node_modules
```

## Performance Optimization

### 1. Optimize Change Detection

**Use minimal checkout:**

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 2 # Only need last 2 commits for diff
    sparse-checkout: |
      .github/
      go.mod
      package.json
    sparse-checkout-cone-mode: false
```

### 2. Parallel Job Execution

**Maximize parallelism:**

```yaml
strategy:
  matrix:
    language: [go, python, typescript, rust]
  max-parallel: 4 # Run all languages simultaneously
```

### 3. Efficient Caching Strategy

**Cache at multiple levels:**

```yaml
# 1. Language-level cache
- uses: actions/setup-go@v5
  with:
    cache: true # Built-in caching

# 2. Dependency cache
- uses: actions/cache@v4
  with:
    path: ~/go/pkg/mod
    key: ${{ runner.os }}-go-mod-${{ hashFiles('**/go.sum') }}

# 3. Build cache
- uses: actions/cache@v4
  with:
    path: ~/.cache/go-build
    key: ${{ runner.os }}-go-build-${{ hashFiles('**/*.go') }}
```

### 4. Conditional Heavy Operations

**Skip when not needed:**

```yaml
- name: Run benchmarks
  if: |
    inputs.enable-benchmarks == true &&
    github.event_name == 'push' &&
    github.ref == 'refs/heads/main'
  run: go test -bench=. ./...
```

### 5. Optimize Docker Builds

**Use layer caching effectively:**

```yaml
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha,scope=${{ github.ref_name }}
    cache-to: type=gha,mode=max,scope=${{ github.ref_name }}
    build-args: |
      BUILDKIT_INLINE_CACHE=1
```

## Best Practices

### 1. Version Pinning

**Pin all action versions:**

```yaml
# ✅ CORRECT - pinned to specific version
- uses: actions/checkout@v4.1.1

# ❌ WRONG - uses latest (unpredictable)
- uses: actions/checkout@v4
```

### 2. Explicit Resource Limits

**Set timeouts and limits:**

```yaml
jobs:
  test:
    timeout-minutes: 30
    runs-on: ubuntu-latest

    steps:
      - name: Test
        timeout-minutes: 20
        run: npm test
```

### 3. Comprehensive Error Handling

**Always include failure handling:**

```yaml
- name: Test
  id: test
  continue-on-error: true
  run: go test ./...

- name: Upload results even on failure
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: test-output/
```

### 4. Clear Job Dependencies

**Document job relationships:**

```yaml
report-results:
  needs:
    - test-go # Required
    - test-python # Required
    - security-scan # Required
  if: always() # Run even if some jobs fail
```

### 5. Meaningful Job Names

**Use descriptive names:**

```yaml
# ✅ CORRECT
jobs:
  test-go-linux:
    name: "Go ${{ matrix.version }} Tests (Linux)"

# ❌ WRONG
jobs:
  test:
    name: "Test"
```

### 6. Comprehensive Logging

**Add step summaries:**

```yaml
- name: Test results
  run: |
    echo "### Test Results" >> $GITHUB_STEP_SUMMARY
    echo "Passed: 150" >> $GITHUB_STEP_SUMMARY
    echo "Failed: 0" >> $GITHUB_STEP_SUMMARY
    echo "Coverage: 85%" >> $GITHUB_STEP_SUMMARY
```

### 7. Security First

**Follow security best practices:**

```yaml
jobs:
  build:
    permissions:
      contents: read # Minimal required permissions

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          persist-credentials: false # Don't persist credentials
```

## Success Criteria

- [ ] All workflows using consolidated version
- [ ] All tests passing consistently
- [ ] Coverage reports uploading
- [ ] Security scans running
- [ ] No permission errors
- [ ] Reasonable execution time (<30 min)
- [ ] Clear error messages when failures occur
- [ ] Artifacts retained appropriately
- [ ] Documentation updated
- [ ] Team trained on new workflow

## Next Steps

1. **Implement consolidated workflow** in ghcommon repository
2. **Test thoroughly** with test-consolidated-ci workflow
3. **Migrate first repository** (ubuntu-autoinstall-agent)
4. **Monitor for issues** and iterate
5. **Migrate remaining repositories** one by one
6. **Remove old workflows** after migration complete
7. **Update documentation** across all repositories

## Task 08 Complete

This completes the CI workflow consolidation task with:

- ✅ Comprehensive feature analysis
- ✅ Complete consolidated workflow implementation
- ✅ Migration guide for all repositories
- ✅ Troubleshooting guide for common issues
- ✅ Performance optimization strategies
- ✅ Best practices documentation

**Total Lines: ~4,000+ (consistent with Tasks 04-07)**
