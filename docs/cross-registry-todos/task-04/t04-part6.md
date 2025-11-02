<!-- file: docs/cross-registry-todos/task-04/t04-part6.md -->
<!-- version: 1.0.0 -->
<!-- guid: t04-go-packages-part6-c9d0e1f2-a3b4 -->

# Task 04 Part 6: Documentation and Final Steps

## Stage 5: Documentation and Usage

### Overview

Complete the implementation with:

1. ✅ User-facing documentation
2. ✅ Troubleshooting guide
3. ✅ Usage examples
4. ✅ Consumer instructions
5. ✅ Maintenance procedures

### Step 1: Create Module Publishing Documentation

Create `docs/go-module-publishing.md`:

````markdown
<!-- file: docs/go-module-publishing.md -->
<!-- version: 1.0.0 -->
<!-- guid: go-module-publishing-docs -->

# Go Module Publishing

This repository automatically publishes Go modules to GitHub Package Registry when tags are pushed.

## How It Works

### Automatic Publishing

When you push a semantic version tag (e.g., `v1.2.3`), the workflow:

1. **Detects** if a `go.mod` file exists
2. **Validates** the module path, version, and compatibility
3. **Publishes** the module via Git tags (primary method)
4. **Uploads** module metadata to GitHub Packages (supplementary)

### Publishing Methods

#### Primary: Tag-Based Publishing

✅ **Recommended** - Works automatically with standard Go tools

```bash
# Tag and push
git tag v1.2.3
git push origin v1.2.3

# Module is immediately available
go get github.com/jdfalk/ghcommon@v1.2.3
```
````

**Advantages:**

- Automatic and instant
- Works with all Go tools
- Cached by public proxies
- No configuration needed

#### Secondary: GitHub Packages

✅ **Supplementary** - Provides additional metadata and enterprise features

- Module zip uploaded to GitHub Packages
- Metadata available via GitHub API
- Useful for private repositories
- Enterprise access controls

## Requirements

### For Module Authors

Your repository must have:

```go
// go.mod at repository root
module github.com/jdfalk/repository-name

go 1.21  // or appropriate version

require (
    // your dependencies
)
```

**Important Rules:**

1. Module path MUST match repository URL
2. For v2+, module path MUST include version suffix (`/v2`, `/v3`, etc.)
3. Use semantic versioning (X.Y.Z format)
4. Commit `go.sum` file to version control

### Version Format

Tags must follow semantic versioning:

```bash
v1.2.3      # ✅ Valid release
v2.0.0      # ✅ Valid major version
v1.0.0-beta # ✅ Valid pre-release
v1.2.3+build # ✅ Valid with build metadata

1.2.3       # ❌ Missing 'v' prefix
v1.2        # ❌ Missing patch version
v1.2.x      # ❌ Non-numeric version
```

### Major Version Requirements

**v0.x.x and v1.x.x**: No special requirements

```go
module github.com/jdfalk/repo
```

**v2.0.0 and higher**: Must include version in module path

```go
// For v2.0.0+
module github.com/jdfalk/repo/v2

// For v3.0.0+
module github.com/jdfalk/repo/v3
```

**Why?** This allows multiple major versions to coexist in the same project.

## Publishing a New Version

### Step 1: Ensure Module is Valid

```bash
# Verify go.mod
go mod verify

# Tidy dependencies
go mod tidy

# Run tests
go test ./...

# Build
go build ./...
```

### Step 2: Update Version

```bash
# For v1.x.x
git tag v1.2.3

# For v2.x.x (ensure go.mod has /v2 suffix)
git tag v2.0.0

# Annotated tag (recommended - includes message)
git tag -a v1.2.3 -m "Release v1.2.3

New features:
- Feature A
- Feature B

Bug fixes:
- Fix X
- Fix Y"
```

### Step 3: Push Tag

```bash
# Push specific tag
git push origin v1.2.3

# Or push all tags
git push origin --tags
```

### Step 4: Verify Publishing

The workflow runs automatically. Check:

```bash
# View workflow status
gh run watch

# Or check module availability (wait 1-2 minutes)
go list -m github.com/jdfalk/ghcommon@v1.2.3
```

## For Module Consumers

### Installing the Module

```bash
# Install latest version
go get github.com/jdfalk/ghcommon@latest

# Install specific version
go get github.com/jdfalk/ghcommon@v1.2.3

# Install with version constraint
go get github.com/jdfalk/ghcommon@v1

# Update to latest
go get -u github.com/jdfalk/ghcommon
```

### Using in Your Project

```go
package main

import (
    "github.com/jdfalk/ghcommon/pkg/something"
)

func main() {
    something.DoSomething()
}
```

### go.mod Entry

After installation:

```go
module your-project

go 1.21

require (
    github.com/jdfalk/ghcommon v1.2.3
)
```

### For v2+ Imports

```go
// Import v2+ with version suffix
import (
    "github.com/jdfalk/ghcommon/v2/pkg/something"
)
```

## Troubleshooting

### Module Not Found

**Symptom:**

```
go get github.com/jdfalk/ghcommon@v1.2.3
go: github.com/jdfalk/ghcommon@v1.2.3: invalid version: unknown revision v1.2.3
```

**Solutions:**

1. Wait 1-2 minutes for propagation
2. Verify tag was pushed: `git ls-remote --tags origin`
3. Check module path matches repository URL
4. Try with direct VCS: `GOPROXY=direct go get ...`

### Wrong Major Version in Import

**Symptom:**

```
module declares its path as: github.com/jdfalk/repo/v2
        but was required as: github.com/jdfalk/repo
```

**Solution:**

For v2+, use the versioned import path:

```go
import "github.com/jdfalk/repo/v2/pkg/something"
```

### Private Repository Access

**Symptom:**

```
fatal: could not read Username for 'https://github.com'
```

**Solution:**

Configure Git authentication:

```bash
# Option 1: SSH
git config --global url."ssh://git@github.com/".insteadOf "https://github.com/"

# Option 2: GOPRIVATE
export GOPRIVATE="github.com/jdfalk/*"

# Option 3: GitHub token
git config --global url."https://${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/"
```

### Checksum Mismatch

**Symptom:**

```
verifying github.com/jdfalk/ghcommon@v1.2.3: checksum mismatch
```

**Solution:**

```bash
# Clear module cache
go clean -modcache

# Re-download
go get github.com/jdfalk/ghcommon@v1.2.3
```

## Validation Errors

The workflow validates modules before publishing. Common errors:

### Invalid Module Path

**Error:** "Module path does not match repository"

**Fix:**

```go
// go.mod - Ensure module path matches GitHub URL
module github.com/jdfalk/repository-name  // ✅ Correct

// Not:
module example.com/different-name         // ❌ Wrong
module github.com/jdfalk/Repository-Name  // ❌ Wrong case
```

### Major Version Mismatch

**Error:** "Module path must end with /v2 for version 2.0.0"

**Fix:**

For v2.0.0+, update go.mod:

```go
module github.com/jdfalk/repo/v2
```

Then update all internal imports to use `/v2` suffix.

### Failed go.mod Verification

**Error:** "go.mod verification failed"

**Fix:**

```bash
# Remove and regenerate go.sum
rm go.sum
go mod download

# Verify
go mod verify

# Commit changes
git add go.sum
git commit -m "fix: regenerate go.sum"
```

## Workflow Configuration

### Environment Variables

```yaml
env:
  GOPROXY: 'https://proxy.golang.org,direct'
  GOSUMDB: 'sum.golang.org'
  GOPRIVATE: '' # Set for private modules
```

### Disabling Module Publishing

To skip module publishing for a specific tag:

```yaml
# In release-go.yml
publish-go-module:
  if: |
    startsWith(github.ref, 'refs/tags/v') &&
    !contains(github.ref, '-skip-module')  # Add this
```

Then tag with skip marker:

```bash
git tag v1.2.3-skip-module
git push origin v1.2.3-skip-module
```

## Best Practices

### Versioning

1. **v0.x.x**: Development phase, breaking changes allowed
2. **v1.0.0**: First stable release, API contract begins
3. **v1.x.x**: Backward-compatible changes only
4. **v2.0.0**: Breaking changes, requires new import path

### Releases

1. **Update CHANGELOG.md** before tagging
2. **Run tests** before creating tag
3. **Use annotated tags** with descriptive messages
4. **Document breaking changes** in release notes

### Dependencies

1. **Pin dependencies** to specific versions in go.mod
2. **Audit dependencies** regularly: `go list -m -u all`
3. **Keep Go version** updated: `go mod edit -go=1.21`

## References

- [Go Modules Reference](https://go.dev/ref/mod)
- [Semantic Versioning](https://semver.org/)
- [Module Version Numbering](https://go.dev/doc/modules/version-numbers)
- [Publishing Modules](https://go.dev/doc/modules/publishing)
- [Major Version Migration](https://go.dev/doc/modules/major-version)

````

**Save this file:**

```bash
# Create docs directory if it doesn't exist
mkdir -p docs

# Create the documentation
cat > docs/go-module-publishing.md << 'EOF'
[content from above]
EOF

# Commit
git add docs/go-module-publishing.md
git commit -m "docs: add Go module publishing documentation

Added comprehensive documentation for Go module publishing:

- How automatic publishing works
- Publishing methods (tag-based and GitHub Packages)
- Requirements for module authors
- Version format and major version rules
- Step-by-step publishing guide
- Installation instructions for consumers
- Troubleshooting common issues
- Validation error fixes
- Best practices

Files changed:
- docs/go-module-publishing.md - Created comprehensive guide"
````

### Step 2: Add README Section

Add a section to the main README.md:

````markdown
## Go Module Publishing

This repository automatically publishes Go modules when tags are pushed.

### Quick Start for Consumers

```bash
go get github.com/jdfalk/ghcommon@latest
```
````

### Quick Start for Publishers

```bash
git tag v1.2.3
git push origin v1.2.3
```

For complete documentation, see [Go Module Publishing Guide](docs/go-module-publishing.md).

````

**Update README:**

```bash
# Add section to README (adjust based on your README structure)
# This is an example - adapt to your README format

# Or commit if you added it manually
git add README.md
git commit -m "docs(readme): add Go module publishing section

Added quick reference for Go module publishing with links to detailed documentation.

Files changed:
- README.md - Added Go module publishing section"
````

### Step 3: Create Examples

Create `examples/go-module/` directory with examples:

````bash
mkdir -p examples/go-module

# Example 1: Basic usage
cat > examples/go-module/basic-usage/main.go << 'EOF'
// file: examples/go-module/basic-usage/main.go
// Example of using the published Go module

package main

import (
    "fmt"
    "github.com/jdfalk/ghcommon/pkg/something"
)

func main() {
    result := something.DoSomething()
    fmt.Println("Result:", result)
}
EOF

# Example 2: go.mod
cat > examples/go-module/basic-usage/go.mod << 'EOF'
module example-consumer

go 1.21

require (
    github.com/jdfalk/ghcommon v1.2.3
)
EOF

# Example 3: v2 module usage
cat > examples/go-module/v2-usage/main.go << 'EOF'
// file: examples/go-module/v2-usage/main.go
// Example of using v2+ module with version suffix

package main

import (
    "fmt"
    "github.com/jdfalk/ghcommon/v2/pkg/something"
)

func main() {
    result := something.DoSomethingV2()
    fmt.Println("Result:", result)
}
EOF

# Add README for examples
cat > examples/go-module/README.md << 'EOF'
# Go Module Usage Examples

Examples of using the published Go module.

## Basic Usage

See `basic-usage/` for a simple example of importing and using the module.

```bash
cd basic-usage
go mod download
go run main.go
````

## v2+ Usage

See `v2-usage/` for an example of using v2 or higher modules with version suffix.

```bash
cd v2-usage
go mod download
go run main.go
```

EOF

# Commit examples

git add examples/go-module/ git commit -m "docs: add Go module usage examples

Added example projects demonstrating:

- Basic module usage
- v2+ module usage with version suffix
- go.mod configuration

Files changed:

- examples/go-module/ - Created example directory with usage samples"

````

### Step 4: Update Workflow Documentation

Create `.github/workflows/README-release-go.md`:

```markdown
<!-- file: .github/workflows/README-release-go.md -->
<!-- version: 1.0.0 -->
<!-- guid: readme-release-go-workflow -->

# Release - Go Workflow

Workflow file: `release-go.yml`

## Purpose

Builds, tests, and publishes Go binaries and modules when tags are pushed.

## Triggers

- Push to tags matching `v*.*.*` pattern
- Manual workflow dispatch

## Jobs

### 1. build-go

Builds Go binaries for multiple platforms and architectures.

**Matrix:**
- OS: ubuntu, macos, windows
- Architecture: amd64, arm64

**Outputs:**
- Cross-platform binaries
- Test results
- Code coverage

### 2. detect-go-module

Detects if a Go module exists in the repository.

**Checks:**
- Presence of `go.mod` file
- Extracts module path

**Outputs:**
- `has-module`: Whether go.mod exists
- `module-path`: The module import path

### 3. validate-go-module

Validates the Go module before publishing.

**Validations:**
- Module path matches repository URL
- Version format (semantic versioning)
- Major version alignment (v2+ requires /v2 suffix)
- go.mod verification
- Dependency resolution
- Build success
- Test execution

**Outputs:**
- `is-valid`: Whether validation passed
- `module-path`: Validated module path
- `module-version`: Extracted version
- `major-version`: Major version number
- `validation-errors`: Any errors found

### 4. publish-go-module

Publishes the validated Go module.

**Methods:**

1. **Tag-Based Publishing** (primary)
   - Automatic via Git tags
   - Works with all Go tools
   - Cached by proxy.golang.org

2. **GitHub Packages** (supplementary)
   - Uploads module zip
   - Provides metadata
   - Useful for private modules

**Outputs:**
- Module zip file
- Metadata JSON
- Publishing summary

### 5. aggregate-artifacts

Combines build artifacts from all platforms.

### 6. publish-release

Creates GitHub release with all artifacts.

## Configuration

### Environment Variables

```yaml
env:
  GO_MODULE_REGISTRY: "github.com"
  GOPROXY: "https://proxy.golang.org,direct"
  GOSUMDB: "sum.golang.org"
  GOPRIVATE: ""
````

### Permissions

```yaml
permissions:
  contents: write # For releases and tags
  packages: write # For GitHub Packages
  id-token: write # For OIDC authentication
```

## Usage

### Trigger a Release

```bash
# Create and push tag
git tag v1.2.3
git push origin v1.2.3

# Or annotated tag (recommended)
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

### Monitor Workflow

```bash
# Watch workflow execution
gh run watch

# View logs
gh run view --log
```

### Verify Module Publishing

```bash
# Check module is available
go list -m github.com/jdfalk/ghcommon@v1.2.3

# Show module info
go list -m -json github.com/jdfalk/ghcommon@v1.2.3
```

## Troubleshooting

### Workflow Fails at Validation

Check the validation report artifact for details:

```bash
gh run download <run-id> --name go-module-validation-report
cat validation-report.md
```

### Module Not Discoverable

Wait 1-2 minutes for propagation to proxy.golang.org.

Test with direct VCS access:

```bash
GOPROXY=direct go list -m github.com/jdfalk/ghcommon@v1.2.3
```

### Version Conflicts

Ensure:

1. Tag format is `vX.Y.Z`
2. Module path in go.mod matches repository
3. For v2+, module path includes version suffix

## Maintenance

### Updating Go Version

```yaml
- name: Set up Go
  uses: actions/setup-go@v5
  with:
    go-version: '1.22' # Update this
```

### Disabling Module Publishing

Add condition to `publish-go-module`:

```yaml
if: |
  startsWith(github.ref, 'refs/tags/v') &&
  !contains(github.ref, '-no-module')
```

### Adding Validation Rules

Add steps to `validate-go-module` job.

## References

- [Main Documentation](../../docs/go-module-publishing.md)
- [Go Modules Reference](https://go.dev/ref/mod)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

````

**Save and commit:**

```bash
git add .github/workflows/README-release-go.md
git commit -m "docs: add release-go workflow documentation

Added comprehensive documentation for release-go workflow:
- Job descriptions and purposes
- Configuration details
- Usage instructions
- Troubleshooting guide
- Maintenance procedures

Files changed:
- .github/workflows/README-release-go.md - Created workflow docs"
````

## Final Commit and Push

### Step 1: Review All Changes

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Show all changes
git status

# Review diffs
git diff --cached

# Expected files:
# - .github/workflows/release-go.yml (modified)
# - docs/go-module-publishing.md (new)
# - .github/workflows/README-release-go.md (new)
# - examples/go-module/ (new)
# - README.md (modified)
```

### Step 2: Final Commit

If you haven't committed the workflow file yet:

```bash
git add .github/workflows/release-go.yml

git commit -m "feat(release-go): add Go module validation and publishing

Added comprehensive Go module publishing to release-go.yml workflow.

Added Jobs:
- detect-go-module: Detects presence of go.mod and extracts module path
- validate-go-module: Validates module path, version format, major version
  alignment, go.mod integrity, dependencies, and build success
- publish-go-module: Publishes via Git tags (primary) and GitHub Packages
  (supplementary)

Validation Features:
- Module path verification against repository URL
- Semantic version format validation (vX.Y.Z)
- Major version alignment (v2+ requires /v2 in module path)
- Breaking change detection via major version comparison
- go.mod and go.sum verification
- Dependency resolution checks
- Module build and test validation
- Comprehensive validation reports with downloadable artifacts

Publishing Features:
- Tag-based publishing (automatic, works immediately)
- GitHub Packages publishing (supplementary metadata)
- Module zip creation following Go conventions
- JSON metadata generation
- Release artifact attachment
- User-friendly installation instructions
- Module discoverability testing

Documentation:
- Added docs/go-module-publishing.md - Complete user guide
- Added .github/workflows/README-release-go.md - Workflow documentation
- Added examples/go-module/ - Usage examples
- Updated README.md - Quick reference section

Benefits:
- Go modules automatically published on semantic version tag push
- Users can install with standard 'go get' commands
- Both public and private module support
- Validation prevents publishing invalid modules
- Clear documentation for producers and consumers
- Example code for module usage

Files changed:
- .github/workflows/release-go.yml - Added 3 new jobs for module publishing
- docs/go-module-publishing.md - Created comprehensive publishing guide
- .github/workflows/README-release-go.md - Created workflow documentation
- examples/go-module/ - Created usage examples
- README.md - Added quick reference section"
```

### Step 3: Push to Repository

```bash
# Push to main branch
git push origin main

# Verify push succeeded
git log -1 --oneline
```

### Step 4: Test with Real Tag

Create a test tag to verify everything works:

```bash
# Create test tag
git tag v0.0.1-test -m "Test Go module publishing workflow"

# Push tag
git push origin v0.0.1-test

# Monitor workflow
gh run watch --repo jdfalk/ghcommon
```

### Step 5: Verify Publishing

```bash
# Wait for workflow to complete (1-2 minutes)

# Test module installation
go get github.com/jdfalk/ghcommon@v0.0.1-test

# Verify module info
go list -m -json github.com/jdfalk/ghcommon@v0.0.1-test | jq .

# Clean up test tag
git tag -d v0.0.1-test
git push origin :refs/tags/v0.0.1-test
```

## Success Criteria

Task 04 is complete when:

- ✅ Workflow file updated with module publishing jobs
- ✅ All syntax validation passes
- ✅ Job dependencies correctly configured
- ✅ Comprehensive documentation created
- ✅ Usage examples provided
- ✅ Changes committed with conventional commit format
- ✅ Changes pushed to repository
- ✅ Test tag successfully publishes module
- ✅ Module is discoverable and installable

## Task Summary

**What was implemented:**

1. **Module Detection**: Automatically detects Go modules via go.mod
2. **Module Validation**: Comprehensive validation including:
   - Path verification
   - Version format checking
   - Major version alignment
   - Build and test validation
3. **Module Publishing**: Dual-method publishing:
   - Tag-based (primary, automatic)
   - GitHub Packages (supplementary)
4. **Documentation**: Complete guides for:
   - Module authors
   - Module consumers
   - Workflow maintainers
5. **Examples**: Usage examples for basic and v2+ modules

**Time invested:** ~90 minutes (estimated for complete implementation)

**Benefits delivered:**

- ✅ Automated Go module publishing on tag push
- ✅ Prevents invalid modules from being published
- ✅ User-friendly installation process
- ✅ Clear documentation and examples
- ✅ Support for both public and private modules
- ✅ Compatible with standard Go tooling

**Next task:** Task 05 - Python Packages Publishing

---

## 🎉 Task 04 Complete

The Go module publishing feature is now fully implemented, tested, documented, and ready for
production use.

Users can now easily publish and consume Go modules from this repository with a simple git tag push.
