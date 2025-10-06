<!-- file: docs/cross-registry-todos/task-08/t08-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t08-ci-consolidation-part5-f1g2h3i4-j5k6 -->

# Task 08 Part 5: Result Aggregation & Migration Guide

## Completing reusable-ci-consolidated.yml - Final Job

```yaml
  # ============================================================================
  # Job 11: Aggregate Results and Report
  # ============================================================================
  report-results:
    name: Aggregate Results
    if: always()
    needs:
      - load-config
      - detect-changes
      - super-lint
      - test-go
      - test-python
      - test-typescript
      - test-rust
      - build-docker
      - security-scan
      - build-protobuf
    runs-on: ubuntu-latest
    outputs:
      all-tests-passed: ${{ steps.aggregate.outputs.all-passed }}
      coverage-percentage: ${{ steps.aggregate.outputs.coverage }}
      security-issues: ${{ steps.aggregate.outputs.security-issues }}

    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: artifacts/

      - name: Aggregate test results
        id: aggregate
        run: |
          echo "### 📊 CI Results Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          # Check job statuses
          all_passed=true

          # Go results
          if [ "${{ needs.test-go.result }}" != "skipped" ]; then
            echo "**Go Tests:** ${{ needs.test-go.result }}" >> $GITHUB_STEP_SUMMARY
            if [ "${{ needs.test-go.result }}" != "success" ]; then
              all_passed=false
            fi
          fi

          # Python results
          if [ "${{ needs.test-python.result }}" != "skipped" ]; then
            echo "**Python Tests:** ${{ needs.test-python.result }}" >> $GITHUB_STEP_SUMMARY
            if [ "${{ needs.test-python.result }}" != "success" ]; then
              all_passed=false
            fi
          fi

          # TypeScript results
          if [ "${{ needs.test-typescript.result }}" != "skipped" ]; then
            echo "**TypeScript Tests:** ${{ needs.test-typescript.result }}" >> $GITHUB_STEP_SUMMARY
            if [ "${{ needs.test-typescript.result }}" != "success" ]; then
              all_passed=false
            fi
          fi

          # Rust results
          if [ "${{ needs.test-rust.result }}" != "skipped" ]; then
            echo "**Rust Tests:** ${{ needs.test-rust.result }}" >> $GITHUB_STEP_SUMMARY
            if [ "${{ needs.test-rust.result }}" != "success" ]; then
              all_passed=false
            fi
          fi

          # Docker results
          if [ "${{ needs.build-docker.result }}" != "skipped" ]; then
            echo "**Docker Build:** ${{ needs.build-docker.result }}" >> $GITHUB_STEP_SUMMARY
            if [ "${{ needs.build-docker.result }}" != "success" ]; then
              all_passed=false
            fi
          fi

          # Security scan results
          if [ "${{ needs.security-scan.result }}" != "skipped" ]; then
            echo "**Security Scan:** ${{ needs.security-scan.result }}" >> $GITHUB_STEP_SUMMARY
            if [ "${{ needs.security-scan.result }}" != "success" ]; then
              all_passed=false
            fi
          fi

          # Super-linter results
          if [ "${{ needs.super-lint.result }}" != "skipped" ]; then
            echo "**Super-Linter:** ${{ needs.super-lint.result }}" >> $GITHUB_STEP_SUMMARY
            if [ "${{ needs.super-lint.result }}" != "success" ]; then
              all_passed=false
            fi
          fi

          echo "all-passed=$all_passed" >> $GITHUB_OUTPUT

          echo "" >> $GITHUB_STEP_SUMMARY
          if [ "$all_passed" = "true" ]; then
            echo "✅ **All Tests Passed!**" >> $GITHUB_STEP_SUMMARY
          else
            echo "❌ **Some Tests Failed**" >> $GITHUB_STEP_SUMMARY
          fi

      - name: Calculate combined coverage
        id: coverage
        run: |
          total_coverage=0
          count=0

          # Aggregate coverage from all languages
          if [ -d "artifacts/go-test-results"* ]; then
            for dir in artifacts/go-test-results-*; do
              if [ -f "$dir/coverage.out" ]; then
                cov=$(go tool cover -func="$dir/coverage.out" 2>/dev/null | tail -1 | awk '{print $3}' | sed 's/%//' || echo "0")
                total_coverage=$(echo "$total_coverage + $cov" | bc)
                count=$((count + 1))
              fi
            done
          fi

          if [ -d "artifacts/python-test-results"* ]; then
            for dir in artifacts/python-test-results-*; do
              if [ -f "$dir/coverage.xml" ]; then
                cov=$(python3 -c "import xml.etree.ElementTree as ET; tree = ET.parse('$dir/coverage.xml'); print(float(tree.getroot().attrib.get('line-rate', 0)) * 100)" 2>/dev/null || echo "0")
                total_coverage=$(echo "$total_coverage + $cov" | bc)
                count=$((count + 1))
              fi
            done
          fi

          if [ -d "artifacts/rust-test-results"* ]; then
            for dir in artifacts/rust-test-results-*; do
              if [ -f "$dir/lcov.info" ]; then
                total=$(grep -o "LF:[0-9]*" "$dir/lcov.info" | cut -d: -f2 | awk '{s+=$1} END {print s}')
                covered=$(grep -o "LH:[0-9]*" "$dir/lcov.info" | cut -d: -f2 | awk '{s+=$1} END {print s}')
                if [ "$total" -gt 0 ]; then
                  cov=$(echo "scale=2; $covered * 100 / $total" | bc)
                  total_coverage=$(echo "$total_coverage + $cov" | bc)
                  count=$((count + 1))
                fi
              fi
            done
          fi

          if [ "$count" -gt 0 ]; then
            avg_coverage=$(echo "scale=2; $total_coverage / $count" | bc)
          else
            avg_coverage=0
          fi

          echo "coverage=$avg_coverage" >> $GITHUB_OUTPUT
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Overall Coverage:** ${avg_coverage}%" >> $GITHUB_STEP_SUMMARY

      - name: Count security issues
        id: security
        run: |
          security_issues=0

          # Count Trivy issues
          if [ -f "artifacts/docker-security-results/trivy-results.sarif" ]; then
            trivy_count=$(jq '.runs[0].results | length' artifacts/docker-security-results/trivy-results.sarif)
            security_issues=$((security_issues + trivy_count))
          fi

          # Count Grype issues
          if [ -f "artifacts/docker-security-results/grype-results.json" ]; then
            grype_count=$(jq '.matches | length' artifacts/docker-security-results/grype-results.json)
            security_issues=$((security_issues + grype_count))
          fi

          echo "security-issues=$security_issues" >> $GITHUB_OUTPUT
          echo "**Security Issues Found:** $security_issues" >> $GITHUB_STEP_SUMMARY

      - name: Generate final report
        run: |
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "---" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "### 📋 Detailed Results" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          # List all artifacts
          echo "**Artifacts Generated:**" >> $GITHUB_STEP_SUMMARY
          find artifacts/ -type f | sort | while read file; do
            size=$(du -h "$file" | cut -f1)
            echo "- \`${file#artifacts/}\` ($size)" >> $GITHUB_STEP_SUMMARY
          done

          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Workflow Configuration:**" >> $GITHUB_STEP_SUMMARY
          echo "- Coverage enabled: ${{ inputs.enable-coverage }}" >> $GITHUB_STEP_SUMMARY
          echo "- Security scan enabled: ${{ inputs.enable-security-scan }}" >> $GITHUB_STEP_SUMMARY
          echo "- Super-linter enabled: ${{ inputs.enable-super-linter }}" >> $GITHUB_STEP_SUMMARY
          echo "- Benchmarks enabled: ${{ inputs.enable-benchmarks }}" >> $GITHUB_STEP_SUMMARY

      - name: Upload combined report
        uses: actions/upload-artifact@v4
        with:
          name: ci-summary-report
          path: |
            ${{ github.step_summary }}
          retention-days: 90
```

## Complete Workflow Footer

```yaml
# End of reusable-ci-consolidated.yml
```

## Migration Guide

### Step 1: Test Consolidated Workflow

**Create test workflow in your repository:**

```yaml
# file: .github/workflows/test-consolidated-ci.yml
name: Test Consolidated CI

on:
  workflow_dispatch:

jobs:
  test:
    uses: jdfalk/ghcommon/.github/workflows/reusable-ci-consolidated.yml@main
    with:
      enable-go: true
      enable-python: true
      enable-coverage: true
      enable-security-scan: true
      go-versions: '["1.21", "1.22"]'
      python-versions: '["3.10", "3.11", "3.12"]'
    secrets: inherit
```

**Run test:**

```bash
gh workflow run test-consolidated-ci.yml
gh run watch
```

### Step 2: Create Repository Config

**Create `.github/repository-config.yml`:**

```yaml
# file: .github/repository-config.yml
# version: 1.0.0
# guid: repo-config-example

ci:
  languages:
    go:
      enabled: true
      versions: ["1.21", "1.22"]
      test-command: "go test -v -race -coverprofile=coverage.out ./..."
      coverage-threshold: 80

    python:
      enabled: true
      versions: ["3.11", "3.12"]
      test-command: "pytest -v --cov --cov-report=xml"
      coverage-threshold: 85

    typescript:
      enabled: false

    rust:
      enabled: false

  features:
    super-linter: false
    security-scan: true
    code-coverage: true
    benchmarks: false

  docker:
    platforms: ["linux/amd64", "linux/arm64"]
    scan-security: true
```

### Step 3: Update Main CI Workflow

**Update `.github/workflows/ci.yml`:**

```yaml
# file: .github/workflows/ci.yml
# version: 2.0.0
# guid: main-ci-workflow

name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
  workflow_dispatch:

jobs:
  ci:
    name: Continuous Integration
    uses: jdfalk/ghcommon/.github/workflows/reusable-ci-consolidated.yml@main
    with:
      # Load configuration from repository-config.yml
      config-file: '.github/repository-config.yml'

      # Enable languages
      enable-go: true
      enable-python: true
      enable-typescript: false
      enable-rust: false
      enable-docker: true

      # Enable features
      enable-coverage: true
      enable-security-scan: true
      enable-super-linter: false
      enable-benchmarks: false

      # Version matrices
      go-versions: '["1.21", "1.22"]'
      python-versions: '["3.11", "3.12"]'

      # Coverage threshold
      coverage-threshold: 80

      # Test timeout
      test-timeout: 30

    secrets: inherit
```

### Step 4: Verify Migration

**Run migration verification script:**

```bash
#!/bin/bash
# file: scripts/verify-ci-migration.sh
# version: 1.0.0
# guid: verify-migration-script

echo "=== Verifying CI Migration ==="

# 1. Check workflow file exists
if [ ! -f ".github/workflows/ci.yml" ]; then
  echo "❌ CI workflow not found"
  exit 1
fi

echo "✅ CI workflow found"

# 2. Check it uses consolidated workflow
if grep -q "reusable-ci-consolidated.yml" .github/workflows/ci.yml; then
  echo "✅ Using consolidated workflow"
else
  echo "❌ Not using consolidated workflow"
  exit 1
fi

# 3. Check repository config
if [ -f ".github/repository-config.yml" ]; then
  echo "✅ Repository config found"
else
  echo "⚠️  Repository config not found (optional)"
fi

# 4. Validate workflow syntax
if command -v yamllint &> /dev/null; then
  yamllint .github/workflows/ci.yml
  echo "✅ Workflow syntax valid"
else
  echo "⚠️  yamllint not installed, skipping syntax check"
fi

# 5. Check for old workflow
if [ -f ".github/workflows/old-ci.yml" ] || [ -f ".github/workflows/ci.yml.bak" ]; then
  echo "⚠️  Old workflow files still present - consider removing"
fi

echo ""
echo "✅ Migration verification complete!"
```

### Step 5: Test All Jobs

**Create comprehensive test:**

```yaml
# file: .github/workflows/test-all-features.yml
name: Test All Features

on:
  workflow_dispatch:

jobs:
  test-full:
    uses: jdfalk/ghcommon/.github/workflows/reusable-ci-consolidated.yml@main
    with:
      # Enable everything
      enable-go: true
      enable-python: true
      enable-typescript: true
      enable-rust: true
      enable-docker: true
      enable-coverage: true
      enable-security-scan: true
      enable-super-linter: true
      enable-benchmarks: true

      # Test all versions
      go-versions: '["1.20", "1.21", "1.22"]'
      python-versions: '["3.9", "3.10", "3.11", "3.12"]'
      node-versions: '["18", "20", "21"]'
      rust-versions: '["stable", "beta", "nightly"]'

      # Coverage threshold
      coverage-threshold: 75

    secrets: inherit
```

### Step 6: Update Documentation

**Update repository README.md:**

```markdown
## CI/CD Pipeline

This repository uses the consolidated CI workflow from `jdfalk/ghcommon`.

### Configuration

CI configuration is defined in `.github/repository-config.yml`.

### Running Tests Locally

**Go:**
```bash
go test -v -race -coverprofile=coverage.out ./...
```

**Python:**
```bash
pytest -v --cov --cov-report=xml
```

### Coverage Reports

Coverage reports are uploaded to Codecov automatically on each push.

Current coverage: [![codecov](https://codecov.io/gh/ORG/REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/ORG/REPO)

### Security Scanning

Security scanning includes:
- CodeQL for code analysis
- Trivy for container vulnerabilities
- Grype for dependency vulnerabilities
- Dependency review on pull requests
```

### Step 7: Remove Old Workflows

**After verification, remove old workflows:**

```bash
#!/bin/bash
# file: scripts/cleanup-old-workflows.sh
# version: 1.0.0
# guid: cleanup-old-workflows-script

echo "=== Cleaning Up Old Workflows ==="

# Backup old workflows
mkdir -p .github/workflows-archive
mv .github/workflows/reusable-ci.yml .github/workflows-archive/ 2>/dev/null || true
mv .github/workflows/old-*.yml .github/workflows-archive/ 2>/dev/null || true

echo "✅ Old workflows archived to .github/workflows-archive/"

# Update .gitignore
if ! grep -q "workflows-archive" .gitignore; then
  echo ".github/workflows-archive/" >> .gitignore
  echo "✅ Added workflows-archive to .gitignore"
fi

echo "✅ Cleanup complete!"
```

## Comparison: Before vs After

### Before (Multiple Workflows)

**File Structure:**
```
.github/
  workflows/
    ci.yml                    # Repository-specific CI
    reusable-ci.yml          # Basic reusable workflow
```

**Problems:**
- Duplication between repositories
- Missing features in reusable workflow
- Inconsistent coverage reporting
- No security scanning in reusable workflow
- Hard to maintain across repositories

### After (Consolidated Workflow)

**File Structure:**
```
.github/
  workflows/
    ci.yml                              # Simple caller workflow
  repository-config.yml                 # Repository-specific config

ghcommon/
  .github/workflows/
    reusable-ci-consolidated.yml        # Feature-complete reusable workflow
```

**Benefits:**
- Single source of truth
- All features available everywhere
- Consistent coverage/security across repos
- Easy to maintain (update once, apply everywhere)
- Repository-specific customization via config
- Backward compatible with existing workflows

## Testing Checklist

- [ ] Workflow syntax validated
- [ ] All language jobs tested
- [ ] Coverage reporting working
- [ ] Security scanning operational
- [ ] Artifacts uploaded correctly
- [ ] Job conditionals working
- [ ] Change detection accurate
- [ ] Repository config loaded
- [ ] Output variables correct
- [ ] Summary report generated

## Continue to Part 6

Final part will cover:
- Troubleshooting guide
- Performance optimization
- Advanced configuration
- Best practices
