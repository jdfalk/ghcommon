<!-- file: docs/cross-registry-todos/task-04/t04-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t04-go-packages-part2-e5f6a7b8-c9d0 -->

# Task 04 Part 2: Workflow Header and Environment Updates

## Stage 1: Update Workflow Header and Environment

### Step 1: Open Workflow File

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon
code .github/workflows/release-go.yml
```

### Step 2: Locate Current Header

The file should start with:

```yaml
# file: .github/workflows/release-go.yml
# version: X.X.X
# guid: some-guid-here

name: Release - Go
```

### Step 3: Update Version Number

**Current version**: Check the current version at the top of the file

**New version**: Increment minor version (adds new feature)

**Change:**

```yaml
# OLD:
# version: 2.1.0

# NEW:
# version: 2.2.0
```

**Rationale**: Adding module publishing is a new feature (minor version bump)

### Step 4: Add Go Module Publishing Comment

After the version header, add documentation:

```yaml
# file: .github/workflows/release-go.yml
# version: 2.2.0
# guid: [keep existing guid]
#
# Changes in 2.2.0:
# - Added Go module publishing to GitHub Packages
# - Added module validation job
# - Added version detection and validation
# - Support for both tag-based and GitHub Packages publishing

name: Release - Go
```

### Step 5: Review Current Permissions

Locate the `permissions:` block (should be near the top):

```yaml
permissions:
  contents: write
  packages: write
  id-token: write
```

**Verify these permissions exist:**

- ✅ `contents: write` - Required for tag operations and releases
- ✅ `packages: write` - Required for GitHub Packages publishing
- ✅ `id-token: write` - Required for OIDC authentication

**If any are missing, add them:**

```yaml
permissions:
  contents: write # For creating tags and releases
  packages: write # For publishing to GitHub Packages
  id-token: write # For OIDC authentication
  pull-requests: read # For checking PR context (if needed)
```

### Step 6: Add Environment Variables Section

Locate the `env:` section at the workflow level (after `permissions:`, before `on:`).

**If it doesn't exist, add it:**

```yaml
permissions:
  contents: write
  packages: write
  id-token: write

env:
  # Go module publishing configuration
  GO_MODULE_REGISTRY: 'github.com'
  GO_PROXY_URL: 'https://proxy.golang.org'
  GO_SUM_DB: 'sum.golang.org'
  GOPROXY: 'https://proxy.golang.org,direct'
  GOSUMDB: 'sum.golang.org'
  GOPRIVATE: '' # Set to repo path for private modules

  # Module validation settings
  GO_MODULE_VALIDATION_ENABLED: 'true'
  GO_MODULE_REQUIRE_SEMVER: 'true'
  GO_MODULE_CHECK_BREAKING_CHANGES: 'true'

on:
  # ... existing triggers
```

**If it exists, merge these variables:**

```yaml
env:
  # ... existing variables ...

  # Go module publishing configuration
  GO_MODULE_REGISTRY: 'github.com'
  GO_PROXY_URL: 'https://proxy.golang.org'
  GO_SUM_DB: 'sum.golang.org'
  GOPROXY: 'https://proxy.golang.org,direct'
  GOSUMDB: 'sum.golang.org'
  GOPRIVATE: ''

  # Module validation settings
  GO_MODULE_VALIDATION_ENABLED: 'true'
  GO_MODULE_REQUIRE_SEMVER: 'true'
  GO_MODULE_CHECK_BREAKING_CHANGES: 'true'
```

### Step 7: Verify Workflow Triggers

Ensure the workflow triggers on tags:

```yaml
on:
  push:
    tags:
      - 'v*.*.*' # Semantic version tags
  workflow_dispatch:
    inputs:
      tag:
        description: 'Release tag (e.g., v1.2.3)'
        required: true
        type: string
```

**Key points:**

- ✅ Triggers on semantic version tags (v1.2.3 format)
- ✅ Supports manual dispatch with tag input
- ✅ Tag format matches Go module version expectations

### Step 8: Review Existing Jobs Structure

Locate the `jobs:` section and review the current structure:

```yaml
jobs:
  build-go:
    name: Build Go Binary
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        # ... matrix configuration
    steps:
      # ... build steps

  aggregate-artifacts:
    name: Aggregate Build Artifacts
    needs: build-go
    runs-on: ubuntu-latest
    steps:
      # ... aggregation steps

  publish-release:
    name: Publish GitHub Release
    needs: aggregate-artifacts
    runs-on: ubuntu-latest
    steps:
      # ... release steps
```

**Note the job names and dependencies** - we'll add new jobs after `build-go` and before
`publish-release`

### Step 9: Add Module Detection Job (Optional but Recommended)

Before the validation job, add a detection job to check if Go modules exist:

```yaml
jobs:
  build-go:
    # ... existing build job ...

  detect-go-module:
    name: Detect Go Module
    runs-on: ubuntu-latest
    needs: build-go
    if: startsWith(github.ref, 'refs/tags/v')
    outputs:
      has-module: ${{ steps.detect.outputs.has-module }}
      module-path: ${{ steps.detect.outputs.module-path }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Full history for version detection

      - name: Detect Go module
        id: detect
        run: |
          if [ -f "go.mod" ]; then
            echo "has-module=true" >> $GITHUB_OUTPUT
            MODULE_PATH=$(grep "^module " go.mod | awk '{print $2}')
            echo "module-path=$MODULE_PATH" >> $GITHUB_OUTPUT
            echo "✅ Go module detected: $MODULE_PATH"
          else
            echo "has-module=false" >> $GITHUB_OUTPUT
            echo "⚠️  No go.mod file found - skipping module publishing"
          fi

      - name: Display module information
        if: steps.detect.outputs.has-module == 'true'
        run: |
          echo "📦 Module Path: ${{ steps.detect.outputs.module-path }}"
          echo "🏷️  Version Tag: ${{ github.ref_name }}"
          echo ""
          echo "go.mod contents:"
          cat go.mod

  # ... other jobs continue ...
```

**Why add this job:**

- ✅ Prevents unnecessary validation when no module exists
- ✅ Provides early feedback about module presence
- ✅ Outputs can be used by subsequent jobs
- ✅ Fast execution (just checks file existence)

### Step 10: Validate Syntax So Far

```bash
# Check YAML syntax
yamllint .github/workflows/release-go.yml

# If you don't have yamllint installed:
brew install yamllint

# Check with actionlint
actionlint .github/workflows/release-go.yml

# If you don't have actionlint installed:
brew install actionlint
```

**Fix any syntax errors before proceeding.**

### Step 11: Commit Header and Environment Changes

```bash
# Stage the workflow file
git add .github/workflows/release-go.yml

# Commit with conventional commit format
git commit -m "feat(release-go): add module publishing environment and detection

Added Go module publishing configuration to release-go.yml workflow:

- Updated version to 2.2.0
- Added Go module environment variables (GOPROXY, GOSUMDB, etc.)
- Added detect-go-module job to check for go.mod presence
- Verified permissions include packages:write for publishing
- Added module validation configuration flags

This prepares the workflow for Go module publishing implementation.

Files changed:
- .github/workflows/release-go.yml - Added env vars and detection job"
```

**Do NOT push yet** - we'll complete all changes first

### Step 12: Verify Changes in VS Code

Open the file and verify:

1. **Header updated**: Version bumped, change notes added
2. **Permissions present**: `contents: write`, `packages: write`, `id-token: write`
3. **Environment variables added**: All Go module config variables
4. **Detection job added**: `detect-go-module` job present
5. **Syntax valid**: No YAML errors in editor

### Step 13: Test Workflow Syntax with GitHub CLI

```bash
# Validate workflow syntax with GitHub API
gh workflow view "Release - Go" --repo jdfalk/ghcommon

# If this succeeds, syntax is valid
```

**Expected output:**

```
Release - Go - release-go.yml
ID: [some ID]
```

**If you get errors:**

- Review YAML indentation
- Check for missing colons or invalid characters
- Verify all quotes are properly closed
- Ensure all job names are unique

## Environment Configuration Deep Dive

### Understanding Go Environment Variables

#### GOPROXY

**Purpose**: Specifies Go module proxy servers

**Format**: Comma-separated list with fallback options

**Options:**

```bash
# Public proxy only (fastest, most reliable)
GOPROXY="https://proxy.golang.org"

# Public proxy with direct VCS fallback
GOPROXY="https://proxy.golang.org,direct"

# Private proxy first, then public, then direct
GOPROXY="https://your-private-proxy.com,https://proxy.golang.org,direct"

# Direct VCS only (no proxy)
GOPROXY="direct"

# Off (fail if not cached locally)
GOPROXY="off"
```

**What we're using:**

```yaml
GOPROXY: 'https://proxy.golang.org,direct'
```

**Why:**

- First tries public proxy (fast, cached)
- Falls back to direct VCS if not in proxy
- Supports both public and private modules

#### GOSUMDB

**Purpose**: Specifies checksum database for verification

**Format**: Database URL or "off"

**Options:**

```bash
# Public checksum database (default, recommended)
GOSUMDB="sum.golang.org"

# Custom checksum database
GOSUMDB="your-sumdb.com"

# Disable checksum verification (not recommended)
GOSUMDB="off"
```

**What we're using:**

```yaml
GOSUMDB: 'sum.golang.org'
```

**Why:**

- Verifies module checksums for security
- Prevents tampering with module sources
- Standard and recommended for public modules

#### GOPRIVATE

**Purpose**: Specifies module paths that should bypass proxies and checksum databases

**Format**: Comma-separated glob patterns

**Examples:**

```bash
# No private modules (public only)
GOPRIVATE=""

# Single private module
GOPRIVATE="github.com/myorg/private-repo"

# All modules from an organization
GOPRIVATE="github.com/myorg/*"

# Multiple organizations
GOPRIVATE="github.com/myorg/*,gitlab.com/another-org/*"

# All modules from a domain
GOPRIVATE="*.mycompany.com"
```

**What we're using:**

```yaml
GOPRIVATE: ''
```

**Why:**

- Default assumes public modules
- Can be overridden for private module publishing
- Empty string means use proxy for all modules

**For private modules, change to:**

```yaml
GOPRIVATE: 'github.com/${{ github.repository_owner }}/*'
```

### Custom Environment Variables Explained

#### GO_MODULE_REGISTRY

**Purpose**: Identifier for which registry to publish to

**Value:** `"github.com"`

**Usage:**

- Used in scripts to determine publishing destination
- Could be extended for other registries in future

#### GO_PROXY_URL

**Purpose**: Base URL for module proxy

**Value:** `"https://proxy.golang.org"`

**Usage:**

- Documentation and verification
- Could be used to test module availability

#### GO_SUM_DB

**Purpose**: Checksum database URL (duplicates GOSUMDB for clarity)

**Value:** `"sum.golang.org"`

**Usage:**

- Documentation
- Validation scripts

#### GO_MODULE_VALIDATION_ENABLED

**Purpose**: Feature flag to enable/disable module validation

**Value:** `"true"`

**Usage:**

```yaml
if: env.GO_MODULE_VALIDATION_ENABLED == 'true'
```

**Benefits:**

- Can disable validation for testing
- Can skip validation for non-module releases

#### GO_MODULE_REQUIRE_SEMVER

**Purpose**: Enforce semantic versioning format

**Value:** `"true"`

**Usage:**

```bash
if [ "$GO_MODULE_REQUIRE_SEMVER" = "true" ]; then
  # Validate semver format
fi
```

**Benefits:**

- Ensures tags follow v1.2.3 format
- Catches version format errors early

#### GO_MODULE_CHECK_BREAKING_CHANGES

**Purpose**: Enable breaking change detection

**Value:** `"true"`

**Usage:**

```bash
if [ "$GO_MODULE_CHECK_BREAKING_CHANGES" = "true" ]; then
  # Run API compatibility checks
fi
```

**Benefits:**

- Warns on major version bumps
- Validates v2+ module path requirements

## Testing the Environment Setup

### Test 1: Validate Workflow Syntax

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Test with actionlint
actionlint .github/workflows/release-go.yml

# Test with yamllint
yamllint .github/workflows/release-go.yml
```

**Expected**: No errors

### Test 2: Check Detection Job Logic

Create a test script to simulate the detection logic:

```bash
#!/bin/bash
# test-go-module-detection.sh

cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

echo "Testing Go module detection..."

if [ -f "go.mod" ]; then
    echo "✅ go.mod found"
    MODULE_PATH=$(grep "^module " go.mod | awk '{print $2}')
    echo "📦 Module path: $MODULE_PATH"
    echo "Has module: true"
else
    echo "⚠️  go.mod not found"
    echo "Has module: false"
fi
```

**Run it:**

```bash
chmod +x test-go-module-detection.sh
./test-go-module-detection.sh
```

**Expected output (if go.mod exists):**

```
Testing Go module detection...
✅ go.mod found
📦 Module path: github.com/jdfalk/ghcommon
Has module: true
```

**Expected output (if go.mod doesn't exist):**

```
Testing Go module detection...
⚠️  go.mod not found
Has module: false
```

### Test 3: Verify Environment Variables Are Accessible

```bash
# In a local shell, set the variables
export GOPROXY="https://proxy.golang.org,direct"
export GOSUMDB="sum.golang.org"
export GOPRIVATE=""

# Test that Go recognizes them
go env | grep -E "GOPROXY|GOSUMDB|GOPRIVATE"
```

**Expected:**

```
GOPROXY="https://proxy.golang.org,direct"
GOSUMDB="sum.golang.org"
GOPRIVATE=""
```

### Test 4: Validate Module Path Format

Create a validation script:

```bash
#!/bin/bash
# validate-module-path.sh

MODULE_PATH="${1:-github.com/jdfalk/ghcommon}"
REPO_OWNER="jdfalk"
REPO_NAME="ghcommon"

echo "Validating module path: $MODULE_PATH"

# Check if module path starts with github.com
if [[ ! "$MODULE_PATH" =~ ^github\.com/ ]]; then
    echo "❌ Module path must start with github.com/"
    exit 1
fi

# Check if module path contains repo owner and name
EXPECTED_PREFIX="github.com/${REPO_OWNER}/${REPO_NAME}"
if [[ ! "$MODULE_PATH" == "$EXPECTED_PREFIX"* ]]; then
    echo "❌ Module path must start with: $EXPECTED_PREFIX"
    echo "   Got: $MODULE_PATH"
    exit 1
fi

echo "✅ Module path is valid"
```

**Run it:**

```bash
chmod +x validate-module-path.sh

# Test with valid path
./validate-module-path.sh "github.com/jdfalk/ghcommon"

# Test with invalid path
./validate-module-path.sh "example.com/wrong/path"
```

## Troubleshooting Environment Setup

### Issue: YAML Syntax Errors

**Symptoms:**

```
Error: Unable to process file command 'env' successfully.
```

**Causes:**

1. Incorrect indentation
2. Missing colons
3. Unquoted special characters

**Solutions:**

```yaml
# ❌ WRONG: No colon after key
env
  GO_MODULE_REGISTRY "github.com"

# ✅ CORRECT: Colon after key
env:
  GO_MODULE_REGISTRY: "github.com"

# ❌ WRONG: Missing quotes around URL with special characters
env:
  GOPROXY: https://proxy.golang.org,direct

# ✅ CORRECT: Quoted value
env:
  GOPROXY: "https://proxy.golang.org,direct"

# ❌ WRONG: Inconsistent indentation
env:
  GO_MODULE_REGISTRY: "github.com"
    GOPROXY: "https://proxy.golang.org"

# ✅ CORRECT: Consistent 2-space indentation
env:
  GO_MODULE_REGISTRY: "github.com"
  GOPROXY: "https://proxy.golang.org"
```

### Issue: Permission Denied on Packages

**Symptoms:**

```
Error: Resource not accessible by integration
```

**Cause:** Missing `packages: write` permission

**Solution:**

```yaml
# Add to permissions block
permissions:
  contents: write
  packages: write # ← ADD THIS
  id-token: write
```

### Issue: Environment Variables Not Available in Jobs

**Symptoms:**

```bash
echo $GOPROXY
# (empty output)
```

**Cause:** Environment variables defined at workflow level aren't automatically inherited by all
jobs

**Solution 1 - Job-level inheritance (current approach):**

```yaml
env:
  GOPROXY: 'https://proxy.golang.org,direct' # Workflow level

jobs:
  my-job:
    runs-on: ubuntu-latest
    # Variables automatically inherited
    steps:
      - run: echo $GOPROXY # Works!
```

**Solution 2 - Explicit job environment (if needed):**

```yaml
jobs:
  my-job:
    runs-on: ubuntu-latest
    env:
      GOPROXY: ${{ env.GOPROXY }} # Explicit reference
    steps:
      - run: echo $GOPROXY
```

### Issue: Module Detection Job Always Shows No Module

**Symptoms:**

```
⚠️  No go.mod file found - skipping module publishing
```

**Possible causes:**

1. `go.mod` is in a subdirectory, not repository root
2. Checkout step missing or incomplete
3. Wrong working directory

**Solution:**

```yaml
steps:
  - name: Checkout code
    uses: actions/checkout@v4 # ← Make sure this is present

  - name: Detect Go module
    run: |
      # Debug: Show current directory
      echo "Current directory: $(pwd)"
      echo "Files in directory:"
      ls -la

      # Check for go.mod
      if [ -f "go.mod" ]; then
        echo "✅ go.mod found"
      else
        echo "⚠️  go.mod not found"

        # Check subdirectories
        echo "Checking subdirectories..."
        find . -name "go.mod" -type f
      fi
```

**If go.mod is in a subdirectory:**

```yaml
- name: Detect Go module
  working-directory: ./path/to/module # ← Add this
  run: |
    if [ -f "go.mod" ]; then
      echo "✅ go.mod found"
    fi
```

## Next Steps

**Completed in this part:**

- ✅ Updated workflow header and version
- ✅ Added environment variables for module publishing
- ✅ Added module detection job
- ✅ Validated syntax
- ✅ Created test scripts
- ✅ Documented troubleshooting

**Continue to Part 3:** Module validation job implementation

**In Part 3, we'll add:**

- Complete module path validation
- Version format validation
- Breaking change detection
- Module compatibility checks
- Validation output variables for downstream jobs
