<!-- file: docs/cross-registry-todos/task-04/t04-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t04-go-packages-part5-b8c9d0e1-f2a3 -->
<!-- last-edited: 2026-01-19 -->

# Task 04 Part 5: Testing and Validation

## Stage 4: Testing and Validation

### Overview

Before pushing the workflow changes to production, we need to thoroughly test:

1. ✅ Workflow syntax validation
2. ✅ Job dependency correctness
3. ✅ Conditional logic
4. ✅ Output variable propagation
5. ✅ Error handling
6. ✅ Local simulation of key steps

### Step 1: Comprehensive Syntax Validation

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Run multiple validation tools
echo "=== Validating Workflow Syntax ==="
echo ""

# 1. YAML syntax with yamllint
echo "1. YAML Syntax Check (yamllint)..."
if yamllint .github/workflows/release-go.yml; then
    echo "   ✅ YAML syntax valid"
else
    echo "   ❌ YAML syntax errors found"
    exit 1
fi
echo ""

# 2. GitHub Actions syntax with actionlint
echo "2. GitHub Actions Syntax Check (actionlint)..."
if actionlint .github/workflows/release-go.yml; then
    echo "   ✅ GitHub Actions syntax valid"
else
    echo "   ❌ GitHub Actions syntax errors found"
    exit 1
fi
echo ""

# 3. Check for common issues
echo "3. Common Issues Check..."

# Check for trailing whitespace
if grep -n " $" .github/workflows/release-go.yml; then
    echo "   ⚠️  Trailing whitespace found (see line numbers above)"
else
    echo "   ✅ No trailing whitespace"
fi

# Check for tabs (should use spaces)
if grep -n $'\t' .github/workflows/release-go.yml; then
    echo "   ⚠️  Tabs found (should use spaces)"
else
    echo "   ✅ No tabs (using spaces)"
fi

# Check for very long lines
if awk 'length > 150' .github/workflows/release-go.yml | head -5; then
    echo "   ⚠️  Some lines exceed 150 characters"
else
    echo "   ✅ Line lengths reasonable"
fi
echo ""

echo "=== Syntax Validation Complete ==="
```

### Step 2: Validate Job Dependencies

Create a script to analyze job dependencies:

```bash
#!/bin/bash
# validate-job-dependencies.sh

echo "=== Validating Job Dependencies ==="
echo ""

WORKFLOW_FILE=".github/workflows/release-go.yml"

# Extract all job names
echo "1. Extracting job names..."
JOBS=$(grep -E "^  [a-z][a-z0-9_-]*:" "$WORKFLOW_FILE" | sed 's/://' | sed 's/^  //')
echo "   Jobs found:"
for job in $JOBS; do
    echo "     - $job"
done
echo ""

# Check needs references
echo "2. Checking 'needs' references..."
ALL_NEEDS=$(grep -E "^\s+needs:" "$WORKFLOW_FILE" | grep -oE "\[[^]]*\]|[a-z][a-z0-9_-]*" | tr -d '[],' | sort -u)

for need in $ALL_NEEDS; do
    if echo "$JOBS" | grep -q "^$need$"; then
        echo "   ✅ $need - Valid reference"
    else
        echo "   ❌ $need - Invalid reference (job doesn't exist)"
        exit 1
    fi
done
echo ""

# Build dependency graph
echo "3. Job dependency graph:"
echo ""
for job in $JOBS; do
    echo "   $job"
    NEEDS=$(sed -n "/^  $job:/,/^  [a-z]/p" "$WORKFLOW_FILE" | \
            grep "needs:" | \
            grep -oE "\[[^]]*\]|[a-z][a-z0-9_-]*" | \
            tr -d '[],' | \
            tr ' ' '\n' | \
            grep -v "^$")

    if [ -n "$NEEDS" ]; then
        for need in $NEEDS; do
            echo "     ↑ depends on: $need"
        done
    else
        echo "     ↑ no dependencies"
    fi
    echo ""
done

echo "=== Dependency Validation Complete ==="
```

**Run it:**

```bash
chmod +x validate-job-dependencies.sh
./validate-job-dependencies.sh
```

**Expected output:**

```
build-go
  ↑ no dependencies

detect-go-module
  ↑ depends on: build-go

validate-go-module
  ↑ depends on: build-go
  ↑ depends on: detect-go-module

publish-go-module
  ↑ depends on: build-go
  ↑ depends on: validate-go-module

aggregate-artifacts
  ↑ depends on: build-go

publish-release
  ↑ depends on: aggregate-artifacts
```

### Step 3: Validate Conditional Logic

Test that conditionals are correct:

```bash
#!/bin/bash
# validate-conditionals.sh

echo "=== Validating Conditional Logic ==="
echo ""

WORKFLOW_FILE=".github/workflows/release-go.yml"

echo "1. Checking tag conditionals..."
TAG_CONDITIONS=$(grep -n "startsWith(github.ref, 'refs/tags/v')" "$WORKFLOW_FILE")
echo "   Tag conditions found at lines:"
echo "$TAG_CONDITIONS" | sed 's/^/     /'
echo ""

echo "2. Checking validation conditionals..."
VALIDATION_CONDITIONS=$(grep -n "needs.validate-go-module.outputs" "$WORKFLOW_FILE")
echo "   Validation output checks found at lines:"
echo "$VALIDATION_CONDITIONS" | sed 's/^/     /'
echo ""

echo "3. Checking module detection conditionals..."
DETECTION_CONDITIONS=$(grep -n "needs.detect-go-module.outputs" "$WORKFLOW_FILE")
echo "   Detection output checks found at lines:"
echo "$DETECTION_CONDITIONS" | sed 's/^/     /'
echo ""

# Simulate conditional evaluation
echo "4. Simulating conditionals..."
echo ""

# Test case 1: Tag push with valid module
echo "   Test Case 1: Tag push, valid module"
GITHUB_REF="refs/tags/v1.2.3"
HAS_MODULE="true"
IS_VALID="true"

if [[ "$GITHUB_REF" == refs/tags/v* ]] && [ "$HAS_MODULE" = "true" ] && [ "$IS_VALID" = "true" ]; then
    echo "     ✅ publish-go-module would run"
else
    echo "     ❌ publish-go-module would NOT run"
fi
echo ""

# Test case 2: Tag push with invalid module
echo "   Test Case 2: Tag push, invalid module"
GITHUB_REF="refs/tags/v1.2.3"
HAS_MODULE="true"
IS_VALID="false"

if [[ "$GITHUB_REF" == refs/tags/v* ]] && [ "$HAS_MODULE" = "true" ] && [ "$IS_VALID" = "true" ]; then
    echo "     ✅ publish-go-module would run"
else
    echo "     ❌ publish-go-module would NOT run (expected)"
fi
echo ""

# Test case 3: Non-tag push
echo "   Test Case 3: Non-tag push"
GITHUB_REF="refs/heads/main"
HAS_MODULE="true"
IS_VALID="true"

if [[ "$GITHUB_REF" == refs/tags/v* ]] && [ "$HAS_MODULE" = "true" ] && [ "$IS_VALID" = "true" ]; then
    echo "     ✅ publish-go-module would run"
else
    echo "     ❌ publish-go-module would NOT run (expected)"
fi
echo ""

echo "=== Conditional Validation Complete ==="
```

**Run it:**

```bash
chmod +x validate-conditionals.sh
./validate-conditionals.sh
```

### Step 4: Validate Output Variables

Check that all output variables are properly defined and used:

```bash
#!/bin/bash
# validate-outputs.sh

echo "=== Validating Output Variables ==="
echo ""

WORKFLOW_FILE=".github/workflows/release-go.yml"

echo "1. Extracting output definitions..."
echo ""

# Find all job outputs
grep -B 5 "outputs:" "$WORKFLOW_FILE" | grep -E "^  [a-z]" | sed 's/://' | while read job; do
    echo "   Job: $job"

    # Get outputs for this job
    sed -n "/^  $job:/,/^  [a-z]/p" "$WORKFLOW_FILE" | \
        grep -E "^\s+[a-z][a-z0-9_-]*:" | \
        sed 's/:.*//' | \
        sed 's/^[[:space:]]*//' | \
        while read output; do
            echo "     - $output"
        done
    echo ""
done

echo "2. Checking output usage..."
echo ""

# Check detect-go-module outputs
echo "   detect-go-module outputs:"
echo "     - has-module (used by: validate-go-module, publish-go-module)"
grep -n "needs.detect-go-module.outputs.has-module" "$WORKFLOW_FILE" | \
    sed 's/^/       Line /'
echo ""

# Check validate-go-module outputs
echo "   validate-go-module outputs:"
for output in is-valid module-path module-version major-version; do
    echo "     - $output"
    COUNT=$(grep -c "needs.validate-go-module.outputs.$output" "$WORKFLOW_FILE")
    echo "       Used $COUNT times"
done
echo ""

# Check for orphaned outputs (defined but not used)
echo "3. Checking for unused outputs..."
ALL_OUTPUTS=$(sed -n '/outputs:/,/^  [a-z]/p' "$WORKFLOW_FILE" | \
              grep -E "^\s+[a-z][a-z0-9_-]*:" | \
              sed 's/:.*//' | \
              sed 's/^[[:space:]]*//')

for output in $ALL_OUTPUTS; do
    # Find which job defines this output
    JOB=$(grep -B 20 "^    $output:" "$WORKFLOW_FILE" | \
          grep -E "^  [a-z][a-z0-9_-]*:" | \
          tail -1 | \
          sed 's/://' | \
          sed 's/^  //')

    # Check if used
    if grep -q "needs.$JOB.outputs.$output" "$WORKFLOW_FILE"; then
        echo "   ✅ $JOB.$output - used"
    else
        echo "   ⚠️  $JOB.$output - defined but not used"
    fi
done
echo ""

echo "=== Output Validation Complete ==="
```

**Run it:**

```bash
chmod +x validate-outputs.sh
./validate-outputs.sh
```

### Step 5: Test Error Handling

Verify error handling in critical steps:

```bash
#!/bin/bash
# test-error-handling.sh

echo "=== Testing Error Handling ==="
echo ""

cd "$(dirname "$0")"

# Test 1: Invalid module path
echo "1. Testing invalid module path detection..."
cat > test-go.mod << 'EOF'
module example.com/wrong/path

go 1.21
EOF

MODULE_PATH=$(grep "^module " test-go.mod | awk '{print $2}')
EXPECTED_PREFIX="github.com/jdfalk/ghcommon"

if [[ "$MODULE_PATH" == "$EXPECTED_PREFIX"* ]]; then
    echo "   ❌ Should have detected invalid path"
    rm test-go.mod
    exit 1
else
    echo "   ✅ Correctly detected invalid path"
fi
rm test-go.mod
echo ""

# Test 2: Invalid version format
echo "2. Testing invalid version format detection..."
TEST_VERSIONS=("1.2" "v1.2.3" "1.2.3.4" "abc" "")

for version in "${TEST_VERSIONS[@]}"; do
    if [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "   Version '$version': Valid"
    else
        echo "   Version '$version': Invalid (expected)"
    fi
done
echo ""

# Test 3: Major version misalignment
echo "3. Testing major version alignment..."

# v2.0.0 with /v2 suffix
MODULE_PATH="github.com/jdfalk/ghcommon/v2"
MAJOR_VERSION="2"
if [[ "$MODULE_PATH" =~ /v$MAJOR_VERSION$ ]]; then
    echo "   ✅ v2.0.0 with /v2 suffix: Valid"
else
    echo "   ❌ Should be valid"
fi

# v2.0.0 without /v2 suffix
MODULE_PATH="github.com/jdfalk/ghcommon"
MAJOR_VERSION="2"
if [[ "$MODULE_PATH" =~ /v$MAJOR_VERSION$ ]]; then
    echo "   ❌ Should detect missing /v2"
else
    echo "   ✅ v2.0.0 without /v2 suffix: Invalid (expected)"
fi

# v1.0.0 without suffix (valid)
MODULE_PATH="github.com/jdfalk/ghcommon"
MAJOR_VERSION="1"
if [ "$MAJOR_VERSION" -lt 2 ]; then
    echo "   ✅ v1.0.0 without suffix: Valid"
fi
echo ""

echo "=== Error Handling Test Complete ==="
```

**Run it:**

```bash
chmod +x test-error-handling.sh
./test-error-handling.sh
```

### Step 6: Dry Run Test

Create a comprehensive dry-run script that simulates the entire workflow:

```bash
#!/bin/bash
# workflow-dry-run.sh

set -e

echo "========================================="
echo "  Go Module Publishing Workflow Dry Run"
echo "========================================="
echo ""

cd "$(dirname "$0")"

# Configuration (simulate workflow inputs)
GITHUB_REF="refs/tags/v1.2.3"
GITHUB_REF_NAME="v1.2.3"
GITHUB_REPOSITORY="jdfalk/ghcommon"
GITHUB_SHA="abc123def456"

echo "Simulated Inputs:"
echo "  GITHUB_REF: $GITHUB_REF"
echo "  GITHUB_REF_NAME: $GITHUB_REF_NAME"
echo "  GITHUB_REPOSITORY: $GITHUB_REPOSITORY"
echo "  GITHUB_SHA: $GITHUB_SHA"
echo ""

# Check if this is a tag push
if [[ ! "$GITHUB_REF" == refs/tags/v* ]]; then
    echo "❌ Not a tag push - workflow would not run module publishing"
    exit 0
fi
echo "✅ Tag push detected - continuing"
echo ""

# ===== JOB: detect-go-module =====
echo "===== JOB: detect-go-module ====="
echo ""

if [ -f "go.mod" ]; then
    HAS_MODULE="true"
    MODULE_PATH=$(grep "^module " go.mod | awk '{print $2}')
    echo "✅ go.mod found"
    echo "   Module path: $MODULE_PATH"
else
    HAS_MODULE="false"
    echo "⚠️  No go.mod found - would skip module publishing"
    exit 0
fi
echo ""

# ===== JOB: validate-go-module =====
echo "===== JOB: validate-go-module ====="
echo ""

IS_VALID="true"
VALIDATION_ERRORS=""

# Extract version
VERSION="${GITHUB_REF_NAME#v}"
MAJOR_VERSION="${VERSION%%.*}"
echo "1. Extracting module information..."
echo "   Module: $MODULE_PATH"
echo "   Version: $VERSION"
echo "   Major: $MAJOR_VERSION"
echo ""

# Validate module path
echo "2. Validating module path..."
REPO_OWNER="$(echo $GITHUB_REPOSITORY | cut -d'/' -f1)"
REPO_NAME="$(echo $GITHUB_REPOSITORY | cut -d'/' -f2)"
EXPECTED_PREFIX="github.com/${REPO_OWNER}/${REPO_NAME}"

if [[ "$MODULE_PATH" == "$EXPECTED_PREFIX"* ]]; then
    echo "   ✅ Module path matches repository"
else
    echo "   ❌ Module path mismatch"
    IS_VALID="false"
    VALIDATION_ERRORS="${VALIDATION_ERRORS}Invalid module path. "
fi
echo ""

# Validate version format
echo "3. Validating version format..."
if [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "   ✅ Valid semantic version"
else
    echo "   ❌ Invalid version format"
    IS_VALID="false"
    VALIDATION_ERRORS="${VALIDATION_ERRORS}Invalid version format. "
fi
echo ""

# Validate major version alignment
echo "4. Validating major version alignment..."
if [ "$MAJOR_VERSION" -ge 2 ]; then
    if [[ "$MODULE_PATH" =~ /v$MAJOR_VERSION$ ]]; then
        echo "   ✅ Module path includes /v$MAJOR_VERSION"
    else
        echo "   ❌ Module path missing /v$MAJOR_VERSION"
        IS_VALID="false"
        VALIDATION_ERRORS="${VALIDATION_ERRORS}Major version misalignment. "
    fi
else
    echo "   ✅ v0 or v1 - no version suffix required"
fi
echo ""

# Validate go.mod
echo "5. Validating go.mod..."
if go mod verify >/dev/null 2>&1; then
    echo "   ✅ go.mod verification passed"
else
    echo "   ❌ go.mod verification failed"
    IS_VALID="false"
    VALIDATION_ERRORS="${VALIDATION_ERRORS}go.mod verification failed. "
fi
echo ""

# Check go.sum
echo "6. Checking go.sum..."
if [ -f "go.sum" ]; then
    echo "   ✅ go.sum exists"
else
    echo "   ⚠️  go.sum not found"
fi
echo ""

# Try to build
echo "7. Building module..."
if go build ./... >/dev/null 2>&1; then
    echo "   ✅ Module builds successfully"
else
    echo "   ❌ Module build failed"
    IS_VALID="false"
    VALIDATION_ERRORS="${VALIDATION_ERRORS}Build failed. "
fi
echo ""

# Validation summary
echo "Validation Result: "
if [ "$IS_VALID" = "true" ]; then
    echo "   ✅ VALID - Ready for publishing"
else
    echo "   ❌ INVALID - Errors: $VALIDATION_ERRORS"
    exit 1
fi
echo ""

# ===== JOB: publish-go-module =====
echo "===== JOB: publish-go-module ====="
echo ""

if [ "$IS_VALID" != "true" ]; then
    echo "⚠️  Validation failed - would skip publishing"
    exit 1
fi

echo "1. Publishing via Git tags..."
echo "   ✅ Tag $GITHUB_REF_NAME makes module discoverable"
echo "   Import: go get $MODULE_PATH@$GITHUB_REF_NAME"
echo ""

echo "2. Creating module zip..."
ZIP_NAME="${MODULE_PATH//\//_}@v${VERSION}.zip"
echo "   Would create: $ZIP_NAME"
echo ""

echo "3. Generating metadata..."
echo "   Would create: module-metadata.json"
echo ""

echo "4. Publishing to GitHub Packages..."
echo "   Would upload module zip and metadata"
echo ""

echo "========================================="
echo "  Dry Run Complete - All Checks Passed"
echo "========================================="
echo ""
echo "Summary:"
echo "  ✅ Tag push detected"
echo "  ✅ Module detected: $MODULE_PATH"
echo "  ✅ Validation passed"
echo "  ✅ Ready for publishing"
echo ""
echo "Next steps:"
echo "  1. Review workflow changes"
echo "  2. Commit workflow updates"
echo "  3. Push to repository"
echo "  4. Create a test tag to trigger workflow"
```

**Run it:**

```bash
chmod +x workflow-dry-run.sh
./workflow-dry-run.sh
```

### Step 7: Validate Workflow with GitHub API

Test workflow file validity using GitHub API:

```bash
#!/bin/bash
# validate-with-github-api.sh

echo "=== Validating Workflow with GitHub API ==="
echo ""

WORKFLOW_FILE=".github/workflows/release-go.yml"
REPO="jdfalk/ghcommon"

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not found"
    echo "   Install: brew install gh"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub"
    echo "   Run: gh auth login"
    exit 1
fi

echo "1. Checking workflow file exists..."
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "   ❌ Workflow file not found: $WORKFLOW_FILE"
    exit 1
fi
echo "   ✅ File exists"
echo ""

echo "2. Listing existing workflows..."
gh workflow list --repo "$REPO"
echo ""

echo "3. Checking if 'Release - Go' workflow exists..."
if gh workflow view "Release - Go" --repo "$REPO" &> /dev/null; then
    echo "   ✅ Workflow found"
    gh workflow view "Release - Go" --repo "$REPO"
else
    echo "   ⚠️  Workflow not found (will be created on push)"
fi
echo ""

echo "=== GitHub API Validation Complete ==="
```

**Run it:**

```bash
chmod +x validate-with-github-api.sh
./validate-with-github-api.sh
```

### Step 8: Final Pre-Push Checklist

Run through this checklist before pushing:

```bash
#!/bin/bash
# pre-push-checklist.sh

echo "========================================="
echo "  Pre-Push Checklist"
echo "========================================="
echo ""

PASSED=0
FAILED=0

check_pass() {
    echo "   ✅ $1"
    ((PASSED++))
}

check_fail() {
    echo "   ❌ $1"
    ((FAILED++))
}

# 1. Syntax validation
echo "1. Syntax Validation"
if actionlint .github/workflows/release-go.yml &> /dev/null && \
   yamllint .github/workflows/release-go.yml &> /dev/null; then
    check_pass "Workflow syntax valid"
else
    check_fail "Workflow syntax errors"
fi
echo ""

# 2. Git status
echo "2. Git Status"
if git diff --quiet .github/workflows/release-go.yml; then
    check_fail "No changes to commit"
else
    check_pass "Changes staged"
fi
echo ""

# 3. Commit message
echo "3. Commit Message"
if git log -1 --pretty=%B | grep -q "^feat(release-go):"; then
    check_pass "Conventional commit format"
else
    check_fail "Non-conventional commit message"
fi
echo ""

# 4. Version updated
echo "4. Version Number"
if grep -q "# version: 2.2.0" .github/workflows/release-go.yml; then
    check_pass "Version number updated"
else
    check_fail "Version number not updated"
fi
echo ""

# 5. New jobs present
echo "5. Required Jobs"
for job in detect-go-module validate-go-module publish-go-module; do
    if grep -q "^  $job:" .github/workflows/release-go.yml; then
        check_pass "Job exists: $job"
    else
        check_fail "Job missing: $job"
    fi
done
echo ""

# 6. Environment variables
echo "6. Environment Variables"
for var in GO_MODULE_REGISTRY GOPROXY GOSUMDB; do
    if grep -q "$var:" .github/workflows/release-go.yml; then
        check_pass "Variable defined: $var"
    else
        check_fail "Variable missing: $var"
    fi
done
echo ""

# 7. Local tests passed
echo "7. Local Tests"
if [ -f "test-go-module-validation.sh" ]; then
    if ./test-go-module-validation.sh &> /dev/null; then
        check_pass "Validation test passed"
    else
        check_fail "Validation test failed"
    fi
else
    echo "   ⚠️  Test script not found"
fi
echo ""

# Summary
echo "========================================="
echo "  Checklist Summary"
echo "========================================="
echo "  ✅ Passed: $PASSED"
if [ $FAILED -gt 0 ]; then
    echo "  ❌ Failed: $FAILED"
    echo ""
    echo "⚠️  RECOMMENDATION: Fix failures before pushing"
    exit 1
else
    echo ""
    echo "✅ ALL CHECKS PASSED"
    echo ""
    echo "Ready to push!"
    echo "Run: git push origin main"
fi
```

**Run it:**

```bash
chmod +x pre-push-checklist.sh
./pre-push-checklist.sh
```

## Testing After Push

After pushing the changes, create a test tag to trigger the workflow:

### Step 1: Create Test Tag

```bash
# Create a lightweight test tag
git tag v0.0.1-test
git push origin v0.0.1-test

# Or create an annotated tag (recommended)
git tag -a v0.0.1-test -m "Test tag for Go module publishing workflow"
git push origin v0.0.1-test
```

### Step 2: Monitor Workflow Execution

```bash
# Watch workflow run
gh run watch --repo jdfalk/ghcommon

# Or list recent runs
gh run list --workflow="Release - Go" --repo jdfalk/ghcommon --limit 5
```

### Step 3: Review Workflow Logs

```bash
# Get the latest run ID
RUN_ID=$(gh run list --workflow="Release - Go" --repo jdfalk/ghcommon --limit 1 --json databaseId --jq '.[0].databaseId')

# View logs
gh run view $RUN_ID --log --repo jdfalk/ghcommon
```

### Step 4: Verify Module Publishing

```bash
# Test module installation
go get github.com/jdfalk/ghcommon@v0.0.1-test

# Check module info
go list -m -json github.com/jdfalk/ghcommon@v0.0.1-test | jq .
```

### Step 5: Clean Up Test Tag

```bash
# Delete local tag
git tag -d v0.0.1-test

# Delete remote tag
git push origin :refs/tags/v0.0.1-test
```

## Next Steps

**Continue to Part 6:** Documentation, troubleshooting guide, and usage examples for the completed
Go module publishing feature.
