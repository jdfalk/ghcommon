<!-- file: docs/cross-registry-todos/task-04/t04-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t04-go-packages-part3-f6a7b8c9-d0e1 -->

# Task 04 Part 3: Module Validation Job Implementation

## Stage 2: Add Module Validation Job

### Overview

The module validation job ensures:

- ✅ go.mod file is valid and well-formed
- ✅ Module path matches repository location
- ✅ Version tag follows semantic versioning
- ✅ Major version alignment (v2+ requires /v2 in module path)
- ✅ No breaking changes without version bump
- ✅ Dependencies are resolvable

### Step 1: Add Validation Job Definition

After the `detect-go-module` job, add:

```yaml
validate-go-module:
  name: Validate Go Module
  runs-on: ubuntu-latest
  needs: [build-go, detect-go-module]
  if: |
    startsWith(github.ref, 'refs/tags/v') &&
    needs.detect-go-module.outputs.has-module == 'true'
  outputs:
    is-valid: ${{ steps.validation-result.outputs.is-valid }}
    module-path: ${{ steps.extract-info.outputs.module-path }}
    module-version: ${{ steps.extract-info.outputs.module-version }}
    major-version: ${{ steps.extract-info.outputs.major-version }}
    validation-errors: ${{ steps.validation-result.outputs.errors }}

  steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0 # Need full history for version comparison

    - name: Set up Go
      uses: actions/setup-go@v5
      with:
        go-version-file: 'go.mod'
        cache: true

    # Continue with validation steps...
```

**Key configuration:**

- `needs: [build-go, detect-go-module]` - Depends on both jobs
- Conditional: Only runs for tag pushes when module exists
- Five outputs for downstream jobs
- Full Git history for version comparison
- Go version from go.mod file

### Step 2: Extract Module Information

Add this step after Go setup:

```yaml
- name: Extract module information
  id: extract-info
  run: |
    echo "=== Extracting Module Information ==="

    # Extract module path
    MODULE_PATH=$(grep "^module " go.mod | awk '{print $2}')
    echo "module-path=$MODULE_PATH" >> $GITHUB_OUTPUT
    echo "📦 Module path: $MODULE_PATH"

    # Extract version from tag
    TAG_VERSION="${GITHUB_REF#refs/tags/v}"
    echo "module-version=$TAG_VERSION" >> $GITHUB_OUTPUT
    echo "🏷️  Version: $TAG_VERSION"

    # Extract major version
    MAJOR_VERSION="${TAG_VERSION%%.*}"
    echo "major-version=$MAJOR_VERSION" >> $GITHUB_OUTPUT
    echo "🔢 Major version: $MAJOR_VERSION"

    # Display go.mod contents for reference
    echo ""
    echo "=== go.mod Contents ==="
    cat go.mod
    echo ""

    # Display Go version
    echo "=== Go Version ==="
    go version
```

**What this does:**

1. Reads module path from go.mod
2. Extracts version from Git tag
3. Calculates major version number
4. Stores all values in outputs
5. Displays information for debugging

### Step 3: Validate Module Path

Add path validation step:

```yaml
- name: Validate module path
  id: validate-path
  run: |
    echo "=== Validating Module Path ==="

    MODULE_PATH="${{ steps.extract-info.outputs.module-path }}"
    REPO_OWNER="${{ github.repository_owner }}"
    REPO_NAME="${{ github.event.repository.name }}"
    EXPECTED_PREFIX="github.com/${REPO_OWNER}/${REPO_NAME}"

    echo "Module path: $MODULE_PATH"
    echo "Expected prefix: $EXPECTED_PREFIX"

    # Check if module path starts with expected prefix
    if [[ "$MODULE_PATH" == "$EXPECTED_PREFIX"* ]]; then
      echo "✅ Module path matches repository location"
      echo "path-valid=true" >> $GITHUB_OUTPUT
    else
      echo "❌ ERROR: Module path does not match repository"
      echo "   Expected: $EXPECTED_PREFIX"
      echo "   Got: $MODULE_PATH"
      echo "path-valid=false" >> $GITHUB_OUTPUT
      exit 1
    fi

    # Check for uppercase characters (Go modules should be lowercase)
    if [[ "$MODULE_PATH" =~ [A-Z] ]]; then
      echo "⚠️  WARNING: Module path contains uppercase characters"
      echo "   Go module paths should be lowercase"
      echo "   Current: $MODULE_PATH"
      echo "   Suggested: ${MODULE_PATH,,}"  # Convert to lowercase
    fi

    # Check for invalid characters
    if [[ "$MODULE_PATH" =~ [^a-z0-9/.\-_] ]]; then
      echo "❌ ERROR: Module path contains invalid characters"
      echo "   Valid characters: a-z, 0-9, /, ., -, _"
      echo "   Current: $MODULE_PATH"
      exit 1
    fi

    echo "✅ Module path validation complete"
```

**Validation checks:**

1. ✅ Path starts with `github.com/owner/repo`
2. ⚠️ Warns if uppercase characters present
3. ❌ Fails if invalid characters present
4. ✅ Stores validation result in output

### Step 4: Validate Version Format

Add version format validation:

```yaml
- name: Validate version format
  id: validate-version
  run: |
    echo "=== Validating Version Format ==="

    VERSION="${{ steps.extract-info.outputs.module-version }}"
    echo "Version: $VERSION"

    # Check semantic versioning format
    if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      if [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+-[a-zA-Z0-9.-]+$ ]]; then
        echo "⚠️  Pre-release version detected: $VERSION"
        echo "   Format: X.Y.Z-prerelease"
        echo "version-type=prerelease" >> $GITHUB_OUTPUT
      elif [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+\+[a-zA-Z0-9.-]+$ ]]; then
        echo "⚠️  Build metadata detected: $VERSION"
        echo "   Format: X.Y.Z+build"
        echo "version-type=build-metadata" >> $GITHUB_OUTPUT
      else
        echo "❌ ERROR: Invalid semantic version format"
        echo "   Expected: X.Y.Z (e.g., 1.2.3)"
        echo "   Got: $VERSION"
        exit 1
      fi
    else
      echo "✅ Valid semantic version: $VERSION"
      echo "version-type=release" >> $GITHUB_OUTPUT
    fi

    # Extract version components
    if [[ "$VERSION" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
      MAJOR="${BASH_REMATCH[1]}"
      MINOR="${BASH_REMATCH[2]}"
      PATCH="${BASH_REMATCH[3]}"

      echo "Components:"
      echo "  Major: $MAJOR"
      echo "  Minor: $MINOR"
      echo "  Patch: $PATCH"

      echo "version-major=$MAJOR" >> $GITHUB_OUTPUT
      echo "version-minor=$MINOR" >> $GITHUB_OUTPUT
      echo "version-patch=$PATCH" >> $GITHUB_OUTPUT
    fi

    echo "✅ Version format validation complete"
```

**Validation checks:**

1. ✅ Validates semantic versioning (X.Y.Z)
2. ⚠️ Detects pre-release versions (X.Y.Z-alpha)
3. ⚠️ Detects build metadata (X.Y.Z+build)
4. ✅ Extracts version components
5. ✅ Stores version type in output

### Step 5: Validate Major Version Alignment

Add major version path requirement check:

```yaml
- name: Validate major version alignment
  id: validate-major-version
  run: |
    echo "=== Validating Major Version Alignment ==="

    MAJOR_VERSION="${{ steps.extract-info.outputs.major-version }}"
    MODULE_PATH="${{ steps.extract-info.outputs.module-path }}"

    echo "Major version: $MAJOR_VERSION"
    echo "Module path: $MODULE_PATH"

    # For v2+, module path must include version suffix
    if [ "$MAJOR_VERSION" -ge 2 ]; then
      if [[ "$MODULE_PATH" =~ /v$MAJOR_VERSION$ ]]; then
        echo "✅ Module path correctly includes /v$MAJOR_VERSION suffix"
        echo "major-version-aligned=true" >> $GITHUB_OUTPUT
      else
        echo "❌ ERROR: Module path must end with /v$MAJOR_VERSION for version ${{ steps.extract-info.outputs.module-version }}"
        echo ""
        echo "Current module path: $MODULE_PATH"
        echo "Required suffix: /v$MAJOR_VERSION"
        echo ""
        echo "To fix, update go.mod:"
        echo "  module $MODULE_PATH/v$MAJOR_VERSION"
        echo ""
        echo "See: https://go.dev/doc/modules/major-version"
        exit 1
      fi
    else
      echo "✅ Version ${{ steps.extract-info.outputs.module-version }} (v0 or v1) - no version suffix required"
      echo "major-version-aligned=true" >> $GITHUB_OUTPUT
    fi
```

**Go module versioning rules:**

- v0.x.x and v1.x.x: No version suffix in module path
- v2.0.0+: Must include `/v2` in module path
- v3.0.0+: Must include `/v3` in module path
- And so on...

**Example:**

```go
// For v1.5.2:
module github.com/jdfalk/repo  // ✅ Correct

// For v2.0.0:
module github.com/jdfalk/repo/v2  // ✅ Correct
module github.com/jdfalk/repo      // ❌ Wrong - missing /v2

// For v3.1.0:
module github.com/jdfalk/repo/v3  // ✅ Correct
```

### Step 6: Check for Breaking Changes

Add breaking change detection:

```yaml
- name: Check for breaking changes
  id: check-breaking
  if: env.GO_MODULE_CHECK_BREAKING_CHANGES == 'true'
  continue-on-error: true # Don't fail build, just warn
  run: |
    echo "=== Checking for Breaking Changes ==="

    # Get previous version
    PREVIOUS_VERSION=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "")
    CURRENT_VERSION="v${{ steps.extract-info.outputs.module-version }}"

    if [ -z "$PREVIOUS_VERSION" ]; then
      echo "ℹ️  No previous version found - this is the first release"
      echo "has-previous=false" >> $GITHUB_OUTPUT
      exit 0
    fi

    echo "Previous version: $PREVIOUS_VERSION"
    echo "Current version: $CURRENT_VERSION"
    echo "has-previous=true" >> $GITHUB_OUTPUT

    # Extract major versions
    PREV_MAJOR=$(echo "$PREVIOUS_VERSION" | sed 's/^v//' | cut -d. -f1)
    CURR_MAJOR="${{ steps.extract-info.outputs.major-version }}"

    echo "Previous major: $PREV_MAJOR"
    echo "Current major: $CURR_MAJOR"

    # Check if major version increased
    if [ "$CURR_MAJOR" -gt "$PREV_MAJOR" ]; then
      echo "⚠️  MAJOR VERSION BUMP DETECTED"
      echo "   $PREVIOUS_VERSION → $CURRENT_VERSION"
      echo "   This indicates BREAKING CHANGES"
      echo ""
      echo "Breaking changes should include:"
      echo "  - Updated CHANGELOG.md with breaking changes section"
      echo "  - Migration guide for users"
      echo "  - Updated documentation"
      echo ""
      echo "is-breaking=true" >> $GITHUB_OUTPUT
    else
      echo "✅ No major version change - backward compatible update"
      echo "is-breaking=false" >> $GITHUB_OUTPUT
    fi

    # Show commits since previous version
    echo ""
    echo "=== Commits Since $PREVIOUS_VERSION ==="
    git log --oneline "$PREVIOUS_VERSION..HEAD" | head -20
```

**Breaking change detection logic:**

1. ✅ Finds previous Git tag
2. ✅ Compares major versions
3. ⚠️ Warns if major version increased
4. ✅ Shows commits since last version
5. ✅ Provides guidance on breaking changes

### Step 7: Validate go.mod File

Add go.mod validation:

```yaml
- name: Validate go.mod file
  id: validate-gomod
  run: |
    echo "=== Validating go.mod File ==="

    # Check if go.mod is valid
    if ! go mod verify; then
      echo "❌ ERROR: go.mod verification failed"
      echo "   Run 'go mod verify' locally to see details"
      exit 1
    fi

    echo "✅ go.mod verification passed"

    # Check if go.sum exists
    if [ ! -f "go.sum" ]; then
      echo "⚠️  WARNING: go.sum file not found"
      echo "   This file should be committed to version control"
      echo "   Run 'go mod download' to generate it"
    else
      echo "✅ go.sum file exists"
    fi

    # Try to download dependencies
    echo ""
    echo "=== Downloading Dependencies ==="
    if ! go mod download; then
      echo "❌ ERROR: Failed to download dependencies"
      echo "   Check go.mod for invalid or unavailable dependencies"
      exit 1
    fi

    echo "✅ All dependencies downloaded successfully"

    # Check for tidy go.mod
    echo ""
    echo "=== Checking go.mod Tidiness ==="
    go mod tidy

    if git diff --exit-code go.mod go.sum; then
      echo "✅ go.mod and go.sum are tidy"
    else
      echo "⚠️  WARNING: go.mod or go.sum are not tidy"
      echo "   Run 'go mod tidy' and commit the changes"
      echo ""
      echo "Changes needed:"
      git diff go.mod go.sum
    fi
```

**Validation checks:**

1. ✅ Verifies go.mod integrity
2. ✅ Checks go.sum exists
3. ✅ Downloads all dependencies
4. ✅ Checks if go.mod is tidy
5. ⚠️ Warns if tidying is needed

### Step 8: Run Module Compatibility Check

Add compatibility validation:

```yaml
- name: Check module compatibility
  id: check-compat
  run: |
    echo "=== Checking Module Compatibility ==="

    # Get Go version from go.mod
    GO_VERSION=$(grep "^go " go.mod | awk '{print $2}')
    echo "Declared Go version: $GO_VERSION"

    # Get installed Go version
    INSTALLED_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
    echo "Installed Go version: $INSTALLED_VERSION"

    # Try to build the module
    echo ""
    echo "=== Building Module ==="
    if go build ./...; then
      echo "✅ Module builds successfully"
      echo "build-success=true" >> $GITHUB_OUTPUT
    else
      echo "❌ ERROR: Module build failed"
      echo "   Fix build errors before publishing"
      echo "build-success=false" >> $GITHUB_OUTPUT
      exit 1
    fi

    # Run tests
    echo ""
    echo "=== Running Tests ==="
    if go test ./... -short; then
      echo "✅ Tests pass"
      echo "tests-pass=true" >> $GITHUB_OUTPUT
    else
      echo "⚠️  WARNING: Some tests failed"
      echo "   Consider fixing tests before publishing"
      echo "tests-pass=false" >> $GITHUB_OUTPUT
      # Don't fail here - tests might be flaky
    fi

    # Run vet
    echo ""
    echo "=== Running go vet ==="
    if go vet ./...; then
      echo "✅ go vet passed"
    else
      echo "⚠️  WARNING: go vet found issues"
      echo "   Consider fixing these before publishing"
    fi
```

**Compatibility checks:**

1. ✅ Verifies Go version
2. ✅ Builds the entire module
3. ✅ Runs tests (warning only)
4. ✅ Runs go vet (warning only)
5. ❌ Fails only if build fails

### Step 9: Aggregate Validation Results

Add final validation summary:

```yaml
- name: Validation summary
  id: validation-result
  if: always()
  run: |
    echo "=== Validation Summary ==="
    echo ""

    ERRORS=""
    WARNINGS=""

    # Check all validation steps
    if [ "${{ steps.validate-path.outputs.path-valid }}" != "true" ]; then
      ERRORS="${ERRORS}Module path validation failed. "
    fi

    if [ "${{ steps.validate-major-version.outputs.major-version-aligned }}" != "true" ]; then
      ERRORS="${ERRORS}Major version alignment failed. "
    fi

    if [ "${{ steps.check-compat.outputs.build-success }}" != "true" ]; then
      ERRORS="${ERRORS}Module build failed. "
    fi

    if [ "${{ steps.check-breaking.outputs.is-breaking }}" == "true" ]; then
      WARNINGS="${WARNINGS}Breaking changes detected. "
    fi

    if [ "${{ steps.check-compat.outputs.tests-pass }}" != "true" ]; then
      WARNINGS="${WARNINGS}Some tests failed. "
    fi

    # Display results
    if [ -n "$ERRORS" ]; then
      echo "❌ Validation FAILED"
      echo ""
      echo "Errors:"
      echo "$ERRORS"
      echo ""
      echo "errors=$ERRORS" >> $GITHUB_OUTPUT
      echo "is-valid=false" >> $GITHUB_OUTPUT
      exit 1
    fi

    echo "✅ Validation PASSED"

    if [ -n "$WARNINGS" ]; then
      echo ""
      echo "⚠️  Warnings:"
      echo "$WARNINGS"
      echo "warnings=$WARNINGS" >> $GITHUB_OUTPUT
    fi

    echo ""
    echo "Module is ready for publishing:"
    echo "  📦 Module: ${{ steps.extract-info.outputs.module-path }}"
    echo "  🏷️  Version: ${{ steps.extract-info.outputs.module-version }}"
    echo "  🔢 Major: ${{ steps.extract-info.outputs.major-version }}"

    echo "is-valid=true" >> $GITHUB_OUTPUT
```

**Summary logic:**

1. ✅ Collects all validation results
2. ✅ Categorizes errors vs warnings
3. ❌ Fails if any errors
4. ⚠️ Shows warnings but continues
5. ✅ Sets final validation output

### Step 10: Save Validation Report

Add artifact upload for validation report:

```yaml
- name: Generate validation report
  if: always()
  run: |
    cat > validation-report.md << 'EOF'
    # Go Module Validation Report

    ## Module Information

    - **Module Path**: ${{ steps.extract-info.outputs.module-path }}
    - **Version**: ${{ steps.extract-info.outputs.module-version }}
    - **Major Version**: ${{ steps.extract-info.outputs.major-version }}
    - **Version Type**: ${{ steps.validate-version.outputs.version-type }}

    ## Validation Results

    | Check                   | Result                                                                                  |
    | ----------------------- | --------------------------------------------------------------------------------------- |
    | Module Path             | ${{ steps.validate-path.outputs.path-valid == 'true' && '✅ Valid'                       |  | '❌ Invalid' }}    |
    | Version Format          | ${{ steps.validate-version.outcome == 'success' && '✅ Valid'                            |  | '❌ Invalid' }}    |
    | Major Version Alignment | ${{ steps.validate-major-version.outputs.major-version-aligned == 'true' && '✅ Aligned' |  | '❌ Misaligned' }} |
    | go.mod Valid            | ${{ steps.validate-gomod.outcome == 'success' && '✅ Valid'                              |  | '❌ Invalid' }}    |
    | Module Builds           | ${{ steps.check-compat.outputs.build-success == 'true' && '✅ Success'                   |  | '❌ Failed' }}     |
    | Tests Pass              | ${{ steps.check-compat.outputs.tests-pass == 'true' && '✅ Pass'                         |  | '⚠️ Warnings' }}   |

    ## Breaking Changes

    ${{ steps.check-breaking.outputs.is-breaking == 'true' && '⚠️ Breaking changes detected - major version bump' || '✅ No breaking changes detected' }}

    ## Overall Status

    ${{ steps.validation-result.outputs.is-valid == 'true' && '✅ **VALID** - Ready for publishing' || '❌ **INVALID** - Fix errors before publishing' }}

    ---
    Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
    Workflow: ${{ github.workflow }}
    Run: ${{ github.run_number }}
    EOF

    echo "Validation report generated"
    cat validation-report.md

- name: Upload validation report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: go-module-validation-report
    path: validation-report.md
    retention-days: 30
```

**Report features:**

- ✅ Comprehensive validation summary
- ✅ Table of all checks with results
- ✅ Breaking change analysis
- ✅ Overall status indicator
- ✅ Available as downloadable artifact

## Testing the Validation Job

### Test 1: Validate Job Syntax

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Validate syntax
actionlint .github/workflows/release-go.yml
yamllint .github/workflows/release-go.yml
```

### Test 2: Simulate Validation Locally

Create a test script to simulate all validation checks:

```bash
#!/bin/bash
# test-go-module-validation.sh

set -e

echo "=== Go Module Validation Test ==="
echo ""

cd "$(dirname "$0")"

# Extract module information
echo "1. Extracting module information..."
MODULE_PATH=$(grep "^module " go.mod | awk '{print $2}')
echo "   Module path: $MODULE_PATH"

# Mock version (would come from Git tag in workflow)
VERSION="1.2.3"
MAJOR_VERSION="1"
echo "   Version: $VERSION"
echo "   Major: $MAJOR_VERSION"
echo ""

# Validate module path
echo "2. Validating module path..."
if [[ "$MODULE_PATH" == "github.com/"* ]]; then
    echo "   ✅ Valid GitHub module path"
else
    echo "   ❌ Invalid module path"
    exit 1
fi
echo ""

# Validate version format
echo "3. Validating version format..."
if [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "   ✅ Valid semantic version"
else
    echo "   ❌ Invalid version format"
    exit 1
fi
echo ""

# Validate major version alignment
echo "4. Validating major version alignment..."
if [ "$MAJOR_VERSION" -ge 2 ]; then
    if [[ "$MODULE_PATH" =~ /v$MAJOR_VERSION$ ]]; then
        echo "   ✅ Module path includes /v$MAJOR_VERSION"
    else
        echo "   ❌ Module path missing /v$MAJOR_VERSION"
        exit 1
    fi
else
    echo "   ✅ v0 or v1 - no version suffix required"
fi
echo ""

# Validate go.mod
echo "5. Validating go.mod..."
if go mod verify; then
    echo "   ✅ go.mod verification passed"
else
    echo "   ❌ go.mod verification failed"
    exit 1
fi
echo ""

# Check if go.sum exists
echo "6. Checking go.sum..."
if [ -f "go.sum" ]; then
    echo "   ✅ go.sum exists"
else
    echo "   ⚠️  go.sum not found"
fi
echo ""

# Download dependencies
echo "7. Downloading dependencies..."
if go mod download; then
    echo "   ✅ Dependencies downloaded"
else
    echo "   ❌ Failed to download dependencies"
    exit 1
fi
echo ""

# Build module
echo "8. Building module..."
if go build ./...; then
    echo "   ✅ Build successful"
else
    echo "   ❌ Build failed"
    exit 1
fi
echo ""

# Run tests
echo "9. Running tests..."
if go test ./... -short; then
    echo "   ✅ Tests passed"
else
    echo "   ⚠️  Tests failed"
fi
echo ""

# Run vet
echo "10. Running go vet..."
if go vet ./...; then
    echo "   ✅ go vet passed"
else
    echo "   ⚠️  go vet found issues"
fi
echo ""

echo "=== Validation Complete ==="
echo "✅ Module is valid and ready for publishing"
```

**Run it:**

```bash
chmod +x test-go-module-validation.sh
./test-go-module-validation.sh
```

### Test 3: Test with Different Version Scenarios

```bash
# Test v1.x.x version (no path suffix needed)
./test-go-module-validation.sh "1.5.2"

# Test v2.x.x version (requires /v2 path suffix)
./test-go-module-validation.sh "2.0.0"

# Test pre-release version
./test-go-module-validation.sh "1.5.3-beta.1"
```

## Troubleshooting

### Issue: Module Path Validation Fails

**Symptom:**

```
❌ ERROR: Module path does not match repository
```

**Cause:** go.mod module path doesn't match GitHub repository URL

**Fix:**

```go
// In go.mod, change:
module example.com/wrong/path

// To:
module github.com/jdfalk/repository-name
```

### Issue: Major Version Alignment Fails

**Symptom:**

```
❌ ERROR: Module path must end with /v2 for version 2.0.0
```

**Cause:** Tagging v2.0.0 but module path doesn't include /v2

**Fix:**

```go
// In go.mod, for v2.0.0 or higher:
module github.com/jdfalk/repository-name/v2

// Update all imports in your code:
import "github.com/jdfalk/repository-name/v2/pkg/something"
```

### Issue: go.mod Verification Fails

**Symptom:**

```
❌ ERROR: go.mod verification failed
```

**Cause:** Corrupted go.sum or mismatched dependencies

**Fix:**

```bash
# Remove go.sum and regenerate
rm go.sum
go mod download
go mod verify

# If still failing, try:
go clean -modcache
go mod download
```

### Issue: Dependencies Download Fails

**Symptom:**

```
❌ ERROR: Failed to download dependencies
```

**Cause:** Unavailable or invalid dependencies

**Fix:**

```bash
# Check which dependency fails
go mod download -x

# Update dependencies to latest versions
go get -u ./...
go mod tidy

# Or remove problematic dependency
go mod edit -droprequire=github.com/problematic/package
```

## Next Steps

**Continue to Part 4:** Publishing job implementation where we'll add the actual module publishing
steps using the validation results.
