<!-- file: docs/cross-registry-todos/task-04/t04-part1.md -->
<!-- version: 1.1.0 -->
<!-- guid: t04-go-packages-part1-d4e5f6a7-b8c9 -->
<!-- last-edited: 2026-01-19 -->

# Task 04: Add Go Module Publishing to GitHub Packages

> **Status:** ✅ Completed  
> **Updated:** `.github/workflows/release-go.yml` v2.2.0 now detects Go modules, validates tag
> alignment, builds metadata, and publishes artifacts to GitHub Packages.  
> **Verification:** Validation and publishing jobs confirm module readiness before execution and
> upload build outputs for review.

## Task Overview

**What**: Implement Go module/binary publishing to GitHub Package Registry in release-go.yml

**Why**: Go binaries are built and released, but Go modules are not published to a package registry,
making it difficult for other Go projects to import and depend on this code as a library

**Where**: `ghcommon` repository, file `.github/workflows/release-go.yml`

**Expected Outcome**:

- Go modules automatically published to GitHub Package Registry
- Binaries continue to be built and attached to releases
- Module versions properly tagged and discoverable
- go.mod proxy configuration for easy consumption

**Estimated Time**: 60-90 minutes

**Risk Level**: Medium (modifying release workflow, affects Go module consumers)

## Prerequisites

### Required Access

- Write access to `jdfalk/ghcommon` repository
- Ability to create and push Git tags
- Permission to publish packages to GitHub
- Understanding of Go module versioning and semantic versioning

### Required Tools

```bash
# Verify these are installed locally
git --version          # Any recent version
go version             # Go 1.21 or later recommended
gh --version           # GitHub CLI
curl --version         # For API testing

# Optional: for local testing
docker --version       # For container-based testing
```

### Knowledge Requirements

- **Go Module System**: Understanding of go.mod, go.sum, module paths
- **Semantic Versioning**: Major.Minor.Patch versioning scheme
- **GitHub Package Registry**: How Go modules work with GitHub Packages
- **Go Module Proxy**: How GOPROXY works and module discovery
- **GitHub Actions**: Workflow syntax and job dependencies
- **Git Tagging**: How tags relate to Go module versions

### Background Reading

Essential reading before starting:

1. **Go Modules**
   - [Go Modules Reference](https://go.dev/ref/mod)
   - [Module version numbering](https://go.dev/doc/modules/version-numbers)
   - [Publishing modules](https://go.dev/doc/modules/publishing)

2. **GitHub Packages for Go**
   - [Working with the Go registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-go-registry)
   - [Publishing a package](https://docs.github.com/en/packages/learn-github-packages/publishing-a-package)
   - [Installing a package](https://docs.github.com/en/packages/learn-github-packages/installing-a-package)

3. **Go Module Proxy Protocol**
   - [Module proxy protocol](https://go.dev/ref/mod#module-proxy)
   - [GOPROXY environment variable](https://go.dev/ref/mod#goproxy-protocol)
   - [Module index](https://go.dev/ref/mod#goproxy-protocol)

### Understanding Go Module Publishing

Go module publishing is different from other package systems:

**Key Differences:**

1. **No Central Registry**: Unlike npm, PyPI, or crates.io, Go doesn't have a single central
   registry
2. **VCS-Based**: Go modules are primarily fetched directly from version control (Git)
3. **Module Proxy**: Go uses proxies (like proxy.golang.org) to cache and serve modules
4. **GitHub Packages Support**: GitHub can act as a Go module proxy for private/enterprise modules

**Publishing Methods:**

1. **Direct VCS (Recommended for Public Modules)**
   - Tag repository with semantic version (v1.2.3)
   - Push tag to GitHub
   - Go tools fetch directly from GitHub
   - Cached by public proxies automatically

2. **GitHub Package Registry (For Private/Enterprise)**
   - Push module metadata to GitHub Packages
   - Configure GOPROXY to use GitHub
   - Requires authentication
   - Useful for private modules or enterprise environments

3. **Custom Module Proxy**
   - Run your own proxy server
   - Advanced setup, not covered here

**For This Task:**

We'll implement BOTH methods:

- ✅ Tag-based publishing (primary method, always works)
- ✅ GitHub Packages publishing (secondary method, for private/enterprise use)

## Current State Analysis

### Step 1: Review Current release-go.yml Workflow

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# View the entire workflow
cat .github/workflows/release-go.yml | less

# Count lines
wc -l .github/workflows/release-go.yml
```

**Expected**: ~380-400 lines

### Step 2: Identify Current Capabilities

```bash
# Check what the workflow currently does
grep -n "^  [a-z-]*:" .github/workflows/release-go.yml
```

**Current jobs should include:**

```
build-go:           # Matrix build job
aggregate-artifacts: # Combines all build artifacts
publish-release:    # Creates GitHub release
```

### Step 3: Check for Existing Publishing Steps

```bash
# Search for any existing module publishing
grep -i "go.*publish\|goproxy\|module.*publish" .github/workflows/release-go.yml

# Expected output: (no matches or minimal matches)
```

### Step 4: Analyze What's Missing

Current workflow includes:

- ✅ Multi-platform Go builds (Linux, macOS, Windows)
- ✅ Multi-architecture support (amd64, arm64)
- ✅ Test execution
- ✅ Coverage reporting
- ✅ Binary artifact creation
- ✅ Tarball/zip packaging
- ✅ Checksum generation
- ✅ SBOM generation
- ✅ Cosign signing
- ✅ GitHub release creation
- ❌ **MISSING: Go module publishing**
- ❌ **MISSING: Module proxy configuration**
- ❌ **MISSING: go.mod validation for publishing**
- ❌ **MISSING: Module version verification**

### Step 5: Check Target Repositories for Go Modules

```bash
# Check if any repositories have Go modules
find /Users/jdfalk/repos/github.com/jdfalk -name "go.mod" -type f 2>/dev/null

# For each repository with go.mod, check the module path
for dir in $(find /Users/jdfalk/repos/github.com/jdfalk -name "go.mod" -type f -exec dirname {} \;); do
    echo "=== $dir ==="
    grep "^module " "$dir/go.mod"
    echo ""
done
```

**Expected**: Some repositories have Go modules that could benefit from this

### Step 6: Understand Go Module Path Requirements

A valid Go module must have:

```go
// In go.mod
module github.com/jdfalk/repository-name

go 1.21  // or appropriate version

require (
    // dependencies
)
```

**Critical**: The module path MUST match the repository URL for public modules

### Step 7: Check Current Tagging Strategy

```bash
# List recent tags in repositories
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon
git tag -l | tail -10

# Check tag format
git tag -l | grep -E "^v[0-9]+\.[0-9]+\.[0-9]+$" | tail -5
```

**Expected**: Some repositories use semantic versioning tags (v1.2.3)

**If no semantic version tags exist**: Will need to start with v0.1.0 or v1.0.0

### Step 8: Test Go Module Discoverability

For any existing Go module, test if it's discoverable:

```bash
# Test if a module can be fetched (replace with actual module)
GOPROXY=direct go list -m github.com/jdfalk/repository-name@latest

# Expected: Either succeeds (module found) or fails with clear error
```

### Decision Point

**Proceed if:**

- ✅ You understand Go module system and versioning
- ✅ At least one repository has a valid go.mod file
- ✅ You can create and push Git tags
- ✅ You understand the difference between public and private module distribution

**Stop and prepare if:**

- ❌ No repositories have go.mod files (create them first)
- ❌ Module paths don't match repository URLs (fix go.mod first)
- ❌ Unclear about Go module versioning (read background material)
- ❌ Don't have permissions to publish packages

## Go Module Publishing Architecture

### Publishing Strategy Overview

We'll implement a dual-strategy approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    Release Workflow                          │
│                                                              │
│  1. Build binaries (existing)                               │
│  2. Run tests (existing)                                    │
│  3. Package artifacts (existing)                            │
│  4. ┌─────────────────────────────────────┐                │
│     │  NEW: Validate Go Module            │                │
│     │  - Check go.mod exists              │                │
│     │  - Verify module path               │                │
│     │  - Validate version format          │                │
│     │  - Check for breaking changes       │                │
│     └─────────────────────────────────────┘                │
│  5. ┌─────────────────────────────────────┐                │
│     │  NEW: Tag-Based Publishing          │                │
│     │  - Verify tag matches version       │                │
│     │  - Push tag to GitHub               │                │
│     │  - Module auto-discoverable         │                │
│     └─────────────────────────────────────┘                │
│  6. ┌─────────────────────────────────────┐                │
│     │  NEW: GitHub Packages Publishing    │                │
│     │  (Optional, for private modules)    │                │
│     │  - Upload module zip                │                │
│     │  - Create module index              │                │
│     │  - Configure GOPROXY endpoint       │                │
│     └─────────────────────────────────────┘                │
│  7. Create GitHub Release (existing)                        │
│  8. Upload release assets (existing)                        │
└─────────────────────────────────────────────────────────────┘
```

### Method 1: Tag-Based Publishing (Primary)

**How it works:**

1. **Tag Creation**: Push a semantic version tag (e.g., v1.2.3)
2. **Go Discovery**: Go tools use the tag to fetch the module
3. **Proxy Caching**: Public proxies (proxy.golang.org) cache the module
4. **Client Fetch**: Other projects can `go get github.com/owner/repo@v1.2.3`

**Advantages:**

- ✅ Simple and standard
- ✅ Works automatically with public proxies
- ✅ No additional configuration needed
- ✅ Free and unlimited
- ✅ Works for public modules

**Limitations:**

- ❌ Requires repository to be public (or VCS credentials for private)
- ❌ No additional metadata or artifacts
- ❌ Limited to Git-based distribution

**Implementation:**

```yaml
- name: Publish Go Module (Tag-Based)
  run: |
    # Tag already created by release process
    # Go tools will automatically discover module via Git tags
    echo "✅ Module published via Git tag: ${{ github.ref_name }}"
    echo "📦 Importable as: github.com/${{ github.repository }}@${{ github.ref_name }}"
    echo "🔍 Discoverable via: go list -m github.com/${{ github.repository }}@${{ github.ref_name }}"
```

### Method 2: GitHub Packages Publishing (Secondary)

**How it works:**

1. **Module Zip**: Create a zip file of the module source
2. **Upload**: Upload to GitHub Packages Go registry
3. **Index**: Create module index metadata
4. **GOPROXY**: Configure clients to use GitHub as module proxy

**Advantages:**

- ✅ Works for private repositories
- ✅ Additional metadata and analytics
- ✅ Enterprise access controls
- ✅ Audit logs

**Limitations:**

- ❌ Requires authentication setup
- ❌ Extra configuration on client side
- ❌ More complex setup
- ❌ May have storage limits

**Implementation:**

```yaml
- name: Publish Go Module (GitHub Packages)
  run: |
    # Create module zip
    go mod vendor
    zip -r module.zip . -x ".git/*"

    # Upload to GitHub Packages
    curl -X POST \
      -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
      -H "Content-Type: application/zip" \
      --data-binary @module.zip \
      "https://api.github.com/repos/${{ github.repository }}/packages/go"
```

### Version Detection Strategy

**Source Priority:**

1. **Git Tag** (highest priority)
   - If workflow triggered by tag push: Use tag version
   - Format: `v1.2.3` → version `1.2.3`

2. **go.mod File**
   - Extract version from go.mod comments or embedded version
   - Fallback if no tag

3. **Commit SHA**
   - Use pseudo-version format: `v0.0.0-20231005123456-abcdef123456`
   - Last resort for development builds

**Version Validation:**

```bash
# Extract version from tag
TAG_VERSION="${GITHUB_REF#refs/tags/v}"

# Validate semver format
if [[ $TAG_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "✅ Valid semantic version: $TAG_VERSION"
else
    echo "❌ Invalid version format: $TAG_VERSION"
    exit 1
fi

# Check for v2+ major version module path requirement
MAJOR_VERSION="${TAG_VERSION%%.*}"
if [ "$MAJOR_VERSION" -ge 2 ]; then
    MODULE_PATH=$(grep "^module " go.mod | awk '{print $2}')
    if [[ ! "$MODULE_PATH" =~ /v$MAJOR_VERSION$ ]]; then
        echo "❌ Module path must end with /v$MAJOR_VERSION for version $TAG_VERSION"
        exit 1
    fi
fi
```

### Module Path Validation

**Requirements:**

1. Module path must match repository URL
2. Module path must be lowercase
3. For v2+, must include version suffix

**Examples:**

```
✅ module github.com/jdfalk/repository-name
✅ module github.com/jdfalk/repository-name/v2
✅ module github.com/jdfalk/repository-name/subpackage

❌ module github.com/JDFalk/Repository-Name  (case mismatch)
❌ module example.com/custom-domain          (doesn't match GitHub)
❌ module github.com/jdfalk/repository-name/v2  (but tagging v1.x.x)
```

**Validation Script:**

```bash
# Extract module path
MODULE_PATH=$(grep "^module " go.mod | awk '{print $2}')

# Extract expected path from repository
EXPECTED_PREFIX="github.com/${{ github.repository }}"

# Check if module path starts with expected prefix
if [[ "$MODULE_PATH" == "$EXPECTED_PREFIX"* ]]; then
    echo "✅ Module path matches repository"
else
    echo "❌ Module path mismatch:"
    echo "   Found: $MODULE_PATH"
    echo "   Expected: $EXPECTED_PREFIX[/subpath][/vN]"
    exit 1
fi
```

### Breaking Change Detection

**Major Version Rules:**

- `v0.x.x`: Anything can change (development)
- `v1.0.0+`: Breaking changes require major version bump
- `v2.0.0+`: Requires `/v2` suffix in module path

**Breaking Change Types:**

1. **API Changes**: Removing or changing public functions/types
2. **Behavior Changes**: Changing function behavior
3. **Dependency Changes**: Major version updates of dependencies
4. **Module Path Changes**: Changing the import path

**Detection Strategy:**

```bash
# Get previous version
PREVIOUS_VERSION=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "v0.0.0")

# Extract major versions
CURRENT_MAJOR=$(echo "$TAG_VERSION" | cut -d. -f1)
PREVIOUS_MAJOR=$(echo "$PREVIOUS_VERSION" | sed 's/^v//' | cut -d. -f1)

# Check if major version increased
if [ "$CURRENT_MAJOR" -gt "$PREVIOUS_MAJOR" ]; then
    echo "⚠️  Major version bump detected: $PREVIOUS_VERSION → v$TAG_VERSION"
    echo "   This indicates breaking changes"

    # For v2+, verify module path has version suffix
    if [ "$CURRENT_MAJOR" -ge 2 ]; then
        MODULE_PATH=$(grep "^module " go.mod | awk '{print $2}')
        if [[ ! "$MODULE_PATH" =~ /v$CURRENT_MAJOR$ ]]; then
            echo "❌ ERROR: Module path must end with /v$CURRENT_MAJOR"
            echo "   Current module path: $MODULE_PATH"
            echo "   Required suffix: /v$CURRENT_MAJOR"
            exit 1
        fi
    fi
fi
```

## Implementation Design

### New Jobs to Add

We'll add two new jobs to `release-go.yml`:

```yaml
validate-go-module:
  name: Validate Go Module
  runs-on: ubuntu-latest
  needs: build-go
  if: startsWith(github.ref, 'refs/tags/v')
  outputs:
    module-path: ${{ steps.validation.outputs.module-path }}
    module-version: ${{ steps.validation.outputs.module-version }}
    is-valid: ${{ steps.validation.outputs.is-valid }}
  steps:
    # Validation steps...

publish-go-module:
  name: Publish Go Module
  runs-on: ubuntu-latest
  needs: [build-go, validate-go-module]
  if: |
    startsWith(github.ref, 'refs/tags/v') &&
    needs.validate-go-module.outputs.is-valid == 'true'
  steps:
    # Publishing steps...
```

### Job Dependency Flow

```
build-go (matrix)
    ↓
    ├─→ aggregate-artifacts
    │       ↓
    │   publish-release
    │
    └─→ validate-go-module
            ↓
        publish-go-module
            ↓
        (module available)
```

### Environment Variables Strategy

```yaml
env:
  # Module publishing configuration
  GO_MODULE_REGISTRY: 'github.com'
  GO_PROXY_URL: 'https://proxy.golang.org'
  GO_SUM_DB: 'sum.golang.org'
  GOPROXY: 'https://proxy.golang.org,direct'
  GOSUMDB: 'sum.golang.org'
  GOPRIVATE: '' # Set to repo path for private modules
```

### Permissions Required

```yaml
permissions:
  contents: write # For creating tags and releases
  packages: write # For publishing to GitHub Packages
  id-token: write # For OIDC authentication
```

## Implementation Steps Overview

We'll implement this in several stages:

### Stage 1: Update Workflow Header and Environment (Part 2)

- Update version number
- Add environment variables
- Update permissions

### Stage 2: Add Module Validation Job (Part 3)

- Create validate-go-module job
- Implement validation steps
- Add output variables

### Stage 3: Add Module Publishing Job (Part 4)

- Create publish-go-module job
- Implement tag-based publishing
- Implement GitHub Packages publishing
- Add verification steps

### Stage 4: Testing and Validation (Part 5)

- Test workflow syntax
- Test with actual Go module
- Verify module discoverability
- Test consumption from another project

### Stage 5: Documentation and Troubleshooting (Part 6)

- Document usage for consumers
- Add troubleshooting guide
- Create examples

Each stage is detailed in the subsequent parts of this task.
