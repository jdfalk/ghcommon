<!-- file: docs/cross-registry-todos/task-09/t09-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t09-ci-migration-part3-c3d4e5f6-g7h8 -->
<!-- last-edited: 2026-01-19 -->

# Task 09 Part 3: Phase 2 Repository Migration

## Phase 2: ubuntu-autoinstall-agent Migration

After successfully migrating ghcommon, proceed with ubuntu-autoinstall-agent, which has more complex
requirements.

### Step 1: Analyze ubuntu-autoinstall-agent CI Workflow

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-agent

# Review current CI workflow
cat .github/workflows/ci.yml | less

# Extract job names
yq eval '.jobs | keys' .github/workflows/ci.yml

# Identify unique features not in ghcommon
diff <(yq eval '.jobs | keys' ../ghcommon/.github/workflows/ci.yml) \
     <(yq eval '.jobs | keys' .github/workflows/ci.yml)
```

**Key features to preserve:**

1. **Rust-Specific Jobs**
   - `test-rust` - Runs cargo test
   - `lint-rust` - Runs clippy
   - `format-rust` - Checks rustfmt

2. **Cross-Compilation**
   - Multiple target platforms
   - Docker-based cross builds
   - Musl libc builds

3. **QEMU Testing**
   - Tests run in QEMU environment
   - ARM64 emulation
   - Platform-specific validation

4. **Security Scanning**
   - Cargo audit for dependencies
   - SARIF report generation
   - Supply chain security

5. **Code Coverage**
   - llvm-cov integration
   - Coverage reports in different formats
   - Codecov integration

### Step 2: Create Migration Branch

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-agent

# Create feature branch
git checkout -b feat/migrate-to-reusable-ci

# Verify branch
git branch --show-current
```

### Step 3: Create Repository Configuration File

ubuntu-autoinstall-agent needs more configuration than ghcommon due to Rust-specific requirements:

```bash
# Create comprehensive config
cat > .github/repository-config.yml << 'EOF'
# file: .github/repository-config.yml
# version: 1.0.0
# guid: ubuntu-autoinstall-agent-config

# Repository Configuration for ubuntu-autoinstall-agent
# Used by reusable CI workflows for intelligent defaults

# Language Detection
languages:
  rust: true
  python: true
  shell: true
  markdown: true
  yaml: true

# Language-Specific Configuration
rust:
  toolchain: stable
  components:
    - rustfmt
    - clippy
  targets:
    - x86_64-unknown-linux-gnu
    - x86_64-unknown-linux-musl
    - aarch64-unknown-linux-gnu
    - aarch64-unknown-linux-musl
  features:
    - cross-compilation
    - qemu-testing
    - llvm-cov
  test_args: "--verbose --all-features"
  clippy_args: "-- -D warnings"

python:
  version: "3.11"
  test_command: "pytest tests/ -v --cov=. --cov-report=xml"
  lint_tools:
    - ruff
    - mypy
  format_check: "ruff format --check ."

# Testing Configuration
testing:
  unit_tests: true
  integration_tests: true
  qemu_tests: true
  platforms:
    - linux-amd64
    - linux-arm64
  coverage:
    enabled: true
    tool: llvm-cov
    format: lcov
    threshold: 80

# Linting Configuration
linting:
  super_linter: true
  language_specific: true
  config_file: .github/linters/super-linter-ci.env
  fail_on_error: true

# Security Configuration
security:
  cargo_audit: true
  dependency_scanning: true
  sarif_reports: true
  supply_chain: true

# Build Configuration
build:
  rust_release: true
  cross_compile: true
  platforms:
    - linux/amd64
    - linux/arm64
  output_dir: target/release
  artifacts:
    - ubuntu-autoinstall-agent
    - ubuntu-autoinstall-agent.exe

# Workflow Behavior
workflow:
  fail_fast: false
  cancel_in_progress: true
  timeout_minutes: 30
  retry_on_failure: false

# Environment Variables
env:
  CARGO_TERM_COLOR: always
  RUST_BACKTRACE: "1"
  RUSTFLAGS: "-D warnings"

# Caching Strategy
cache:
  enabled: true
  cargo: true
  python_pip: true
  key_prefix: v1

# Notification Settings
notifications:
  slack: false
  email: false
  github_issues: true  # Create issues on failure
EOF

git add .github/repository-config.yml
```

**Configuration explanation:**

- **Rust targets**: Four targets for comprehensive cross-compilation
- **QEMU testing**: Enabled for ARM64 platform validation
- **llvm-cov**: Rust code coverage tool integration
- **Cargo audit**: Dependency vulnerability scanning
- **Fail fast**: Disabled to see all job results
- **Cancel in progress**: Enabled to save CI minutes on new pushes

### Step 4: Update CI Workflow to Use Reusable Workflow

```bash
# Backup current workflow
cp .github/workflows/ci.yml .github/workflows/ci.yml.backup

# Create new workflow that calls reusable workflow
cat > .github/workflows/ci.yml << 'EOF'
# file: .github/workflows/ci.yml
# version: 2.0.0
# guid: ubuntu-autoinstall-agent-ci

name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  workflow_dispatch:

# Permissions for the workflow
permissions:
  contents: read
  pull-requests: write
  security-events: write
  checks: write

jobs:
  # Use the reusable CI workflow from ghcommon
  ci:
    uses: jdfalk/ghcommon/.github/workflows/reusable-ci.yml@main
    with:
      # Repository identification
      repository: ${{ github.repository }}
      ref: ${{ github.ref }}

      # Language enablement
      enable_go: false
      enable_rust: true
      enable_python: true
      enable_frontend: false
      enable_docker: false

      # Rust-specific configuration
      rust_toolchain: stable
      rust_targets: "x86_64-unknown-linux-gnu,x86_64-unknown-linux-musl,aarch64-unknown-linux-gnu,aarch64-unknown-linux-musl"
      rust_features: "cross-compilation,qemu-testing,llvm-cov"

      # Testing configuration
      run_tests: true
      run_qemu_tests: true
      coverage_enabled: true
      coverage_tool: llvm-cov

      # Linting configuration
      run_linters: true
      super_linter_enabled: true
      super_linter_config: .github/linters/super-linter-ci.env

      # Security scanning
      security_scanning: true
      cargo_audit: true
      sarif_upload: true

      # Build configuration
      build_artifacts: true
      artifact_retention_days: 30

      # Workflow behavior
      fail_fast: false
      timeout_minutes: 30

    secrets:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

  # Post-CI summary job
  ci-summary:
    name: CI Summary
    runs-on: ubuntu-latest
    needs: ci
    if: always()

    steps:
      - name: CI Result Summary
        run: |
          echo "# CI Workflow Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Repository**: \`${{ github.repository }}\`" >> $GITHUB_STEP_SUMMARY
          echo "**Ref**: \`${{ github.ref }}\`" >> $GITHUB_STEP_SUMMARY
          echo "**SHA**: \`${{ github.sha }}\`" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          if [ "${{ needs.ci.result }}" = "success" ]; then
            echo "**Status**: ✅ All checks passed" >> $GITHUB_STEP_SUMMARY
          elif [ "${{ needs.ci.result }}" = "failure" ]; then
            echo "**Status**: ❌ Some checks failed" >> $GITHUB_STEP_SUMMARY
          elif [ "${{ needs.ci.result }}" = "cancelled" ]; then
            echo "**Status**: ⏭️ Workflow cancelled" >> $GITHUB_STEP_SUMMARY
          else
            echo "**Status**: ⚠️ Unknown status" >> $GITHUB_STEP_SUMMARY
          fi

          echo "" >> $GITHUB_STEP_SUMMARY
          echo "See the CI job for detailed results." >> $GITHUB_STEP_SUMMARY
EOF

git add .github/workflows/ci.yml
```

**Key migration points:**

1. **Simplified workflow**: Delegates to reusable workflow
2. **Explicit configuration**: All settings passed as inputs
3. **Rust features**: Cross-compilation, QEMU, llvm-cov enabled
4. **Security**: SARIF uploads, cargo audit enabled
5. **Summary job**: Provides high-level status

### Step 5: Test Migration Locally

Before pushing, validate the changes:

```bash
# Validate YAML syntax
yamllint .github/workflows/ci.yml
yamllint .github/repository-config.yml

# Check workflow with actionlint
actionlint .github/workflows/ci.yml

# Verify reusable workflow exists and is accessible
gh api repos/jdfalk/ghcommon/contents/.github/workflows/reusable-ci.yml \
  --jq '.download_url'

# Test loading repository config
cat > /tmp/test-config-loader.sh << 'EOF'
#!/bin/bash
set -e

CONFIG_FILE=".github/repository-config.yml"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ Config file not found: $CONFIG_FILE"
  exit 1
fi

# Test YAML parsing
if ! python3 -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))" 2>/dev/null; then
  echo "❌ Invalid YAML in $CONFIG_FILE"
  exit 1
fi

echo "✅ Config file valid"

# Extract and display key settings
echo ""
echo "Configuration Summary:"
python3 << 'PYTHON'
import yaml
with open('.github/repository-config.yml') as f:
    config = yaml.safe_load(f)

print(f"Languages: {', '.join([k for k, v in config.get('languages', {}).items() if v])}")
print(f"Rust toolchain: {config.get('rust', {}).get('toolchain', 'N/A')}")
print(f"Rust targets: {', '.join(config.get('rust', {}).get('targets', []))}")
print(f"Testing enabled: {config.get('testing', {}).get('unit_tests', False)}")
print(f"Coverage tool: {config.get('testing', {}).get('coverage', {}).get('tool', 'N/A')}")
PYTHON

echo ""
echo "✅ Configuration loaded successfully"
EOF

chmod +x /tmp/test-config-loader.sh
/tmp/test-config-loader.sh
```

### Step 6: Create Pull Request

```bash
# Commit changes
git add .github/workflows/ci.yml .github/repository-config.yml

git commit -m "feat(ci): migrate to reusable CI workflow

Migrated ubuntu-autoinstall-agent CI workflow to use the centralized
reusable workflow from ghcommon.

Changes:
- Created .github/repository-config.yml with Rust-specific settings
- Updated .github/workflows/ci.yml to call reusable workflow
- Preserved all existing functionality:
  * Rust testing with multiple targets
  * Cross-compilation support
  * QEMU testing for ARM64
  * llvm-cov code coverage
  * Cargo audit security scanning
  * Super-linter integration
- Added CI summary job for high-level status

Configuration highlights:
- Rust targets: x86_64 (gnu/musl), aarch64 (gnu/musl)
- Testing: unit, integration, QEMU
- Coverage: llvm-cov with 80% threshold
- Security: cargo audit, SARIF reports
- Build: cross-compilation enabled

Benefits:
- Centralized workflow management
- Consistent CI behavior across repos
- Easier maintenance and updates
- Reduced code duplication

Testing:
- Validated YAML syntax
- Checked actionlint
- Verified config file parsing
- Confirmed reusable workflow accessibility

Version: CI workflow 1.1.0 → 2.0.0 (major refactor)"

# Push to remote
git push origin feat/migrate-to-reusable-ci
```

### Step 7: Create Pull Request via GitHub CLI

```bash
# Create PR
gh pr create \
  --title "feat(ci): migrate to reusable CI workflow" \
  --body "## Migration to Reusable CI Workflow

This PR migrates the CI workflow to use the centralized reusable workflow from ghcommon.

### Changes

- ✅ Created \`.github/repository-config.yml\` with comprehensive Rust configuration
- ✅ Updated \`.github/workflows/ci.yml\` to call reusable workflow
- ✅ Preserved all existing CI functionality
- ✅ Added CI summary job for better visibility

### Configuration

The new config file defines:

- **Languages**: Rust (primary), Python, Shell
- **Rust**: 4 targets (x86_64/aarch64, gnu/musl)
- **Testing**: Unit, integration, QEMU tests
- **Coverage**: llvm-cov with 80% threshold
- **Security**: Cargo audit, SARIF reports
- **Build**: Cross-compilation, release artifacts

### Testing Plan

1. **Automated Checks** (will run on this PR):
   - Rust tests on all platforms
   - Clippy linting
   - Rustfmt validation
   - Python tests (if any)
   - Super-linter checks
   - Security scanning

2. **Manual Verification**:
   - Compare CI job output with previous runs
   - Verify all tests execute
   - Check code coverage reports
   - Review security scan results
   - Confirm artifacts are built

3. **Regression Testing**:
   - Ensure no tests are skipped
   - Verify cross-compilation works
   - Check QEMU tests execute
   - Confirm coverage thresholds met

### Rollback Plan

If issues are found:

1. Revert this PR
2. Workflow automatically reverts to previous version
3. File issues for any missing functionality
4. Address issues and re-submit

### Benefits

- **Consistency**: Same CI behavior as ghcommon
- **Maintainability**: Update once in ghcommon, affects all repos
- **Simplicity**: Less code in this repo, easier to understand
- **Features**: Access to new features added to reusable workflow

### Checklist

- [x] YAML syntax validated
- [x] Actionlint checks passed
- [x] Config file parsing tested
- [x] Reusable workflow accessible
- [x] Commit message follows conventional commits
- [x] Documentation updated (this PR description)

### Related

- Depends on: ghcommon reusable-ci.yml workflow
- Related PR: ghcommon #XX (if applicable)
- Issue: #XX (if tracking migration)" \
  --base main \
  --head feat/migrate-to-reusable-ci \
  --label ci,enhancement \
  --draft
```

**Note**: Created as draft PR to allow initial review before marking ready.

### Step 8: Monitor PR Checks

```bash
# Get PR number
PR_NUMBER=$(gh pr view feat/migrate-to-reusable-ci --json number --jq '.number')

echo "PR created: #$PR_NUMBER"

# Watch PR checks
gh pr checks $PR_NUMBER --watch

# View PR status
gh pr view $PR_NUMBER

# Get workflow run ID
RUN_ID=$(gh run list --branch feat/migrate-to-reusable-ci --limit 1 --json databaseId --jq '.[0].databaseId')

# Watch workflow
gh run watch $RUN_ID
```

### Step 9: Compare CI Behavior

After CI completes, compare with previous runs:

```bash
# Get latest main branch run
MAIN_RUN=$(gh run list --branch main --workflow ci.yml --limit 1 --json databaseId --jq '.[0].databaseId')

# Get this PR's run
PR_RUN=$(gh run list --branch feat/migrate-to-reusable-ci --workflow ci.yml --limit 1 --json databaseId --jq '.[0].databaseId')

# Compare job structure
echo "Main branch jobs:"
gh run view $MAIN_RUN --json jobs --jq '.jobs[] | {name, conclusion}'

echo ""
echo "PR branch jobs:"
gh run view $PR_RUN --json jobs --jq '.jobs[] | {name, conclusion}'

# Compare duration
echo ""
echo "Main branch duration:"
gh run view $MAIN_RUN --json updatedAt,createdAt --jq '
  (.updatedAt | fromdateiso8601) - (.createdAt | fromdateiso8601) |
  . / 60 | floor | tostring + " minutes"
'

echo "PR branch duration:"
gh run view $PR_RUN --json updatedAt,createdAt --jq '
  (.updatedAt | fromdateiso8601) - (.createdAt | fromdateiso8601) |
  . / 60 | floor | tostring + " minutes"
'

# Download and compare logs
mkdir -p /tmp/ci-comparison
gh run view $MAIN_RUN --log > /tmp/ci-comparison/main-run.log
gh run view $PR_RUN --log > /tmp/ci-comparison/pr-run.log

# Compare test counts
echo ""
echo "Main branch test summary:"
grep -i "test result:" /tmp/ci-comparison/main-run.log | tail -1

echo "PR branch test summary:"
grep -i "test result:" /tmp/ci-comparison/pr-run.log | tail -1
```

**What to verify:**

1. **All jobs execute**: No jobs missing vs main branch
2. **Tests pass**: Same number of tests passing
3. **Coverage maintained**: Coverage % similar to main
4. **Duration acceptable**: Within 10-20% of previous runs
5. **Artifacts created**: Build outputs present
6. **No new failures**: All checks that passed before still pass

### Step 10: Address Issues (if any)

If CI fails or behaves differently:

**Issue: Missing job or test**

```bash
# Check if job is disabled in reusable workflow
gh api repos/jdfalk/ghcommon/contents/.github/workflows/reusable-ci.yml \
  --jq '.content' | base64 -d | grep -A 10 "job-name"

# Verify input is passed correctly
grep "enable_" .github/workflows/ci.yml
```

**Issue: Wrong Rust target**

```bash
# Check target list in repository-config.yml
yq eval '.rust.targets' .github/repository-config.yml

# Compare with previous workflow
grep "target:" .github/workflows/ci.yml.backup
```

**Issue: Coverage not uploaded**

```bash
# Verify CODECOV_TOKEN is set
gh secret list | grep CODECOV_TOKEN

# Check coverage step in logs
grep -i "coverage" /tmp/ci-comparison/pr-run.log
```

**Issue: Build artifacts missing**

```bash
# List artifacts from run
gh run view $PR_RUN --json artifacts --jq '.artifacts[] | {name, size_in_bytes}'

# Compare with main branch
gh run view $MAIN_RUN --json artifacts --jq '.artifacts[] | {name, size_in_bytes}'
```

### Step 11: Mark PR Ready and Merge

Once all checks pass and comparison looks good:

```bash
# Mark PR as ready for review
gh pr ready $PR_NUMBER

# Request review (optional)
gh pr edit $PR_NUMBER --add-reviewer username

# If approved, merge
gh pr merge $PR_NUMBER --squash --delete-branch
```

**Post-merge verification:**

```bash
# Switch to main
git checkout main
git pull origin main

# Verify workflow file updated
cat .github/workflows/ci.yml | head -20

# Trigger a CI run
git commit --allow-empty -m "ci: trigger CI test after reusable workflow migration"
git push origin main

# Watch the run
gh run watch
```

---

**Part 3 Complete**: Phase 2 ubuntu-autoinstall-agent migration with Rust-specific configuration, PR
creation, comparison testing, and issue resolution. ✅

**Continue to Part 4** for batch repository migration strategies, template generation, and automated
migration tools.
