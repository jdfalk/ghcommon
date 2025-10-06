<!-- file: docs/cross-registry-todos/task-03-rust-packages.md -->
<!-- version: 1.0.0 -->
<!-- guid: t03-rust-packages-c3d4e5f6-a7b8-9c0d-1e2f -->

# Task 03: Add Rust Crate Publishing to GitHub Packages

## Task Overview

**What**: Implement Rust crate publishing to GitHub Package Registry in release-rust.yml

**Why**: Rust binaries are built but crates are not published to a package registry, making it hard
for other projects to depend on them

**Where**: `ghcommon` repository, file `.github/workflows/release-rust.yml`

**Expected Outcome**: Rust crates automatically published to GitHub Package Registry during releases

**Estimated Time**: 45-60 minutes

**Risk Level**: Medium (modifying release workflow, requires testing)

## Prerequisites

### Required Access

- Write access to `jdfalk/ghcommon` repository
- Ability to create and use GitHub Personal Access Tokens (PAT)
- Permission to publish packages to GitHub

### Required Tools

```bash
# Verify these are installed locally
git --version          # Any recent version
cargo --version        # Rust toolchain
gh --version           # GitHub CLI

# Optional: for local testing
docker --version       # For container-based testing
```

### Knowledge Requirements

- Rust cargo publish process
- GitHub Package Registry for Rust/Cargo
- GitHub Actions workflow syntax
- Cargo.toml configuration
- Authentication with GitHub Packages

### Background Reading

- [GitHub Packages for Cargo](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-cargo-registry)
- [Cargo Publish Documentation](https://doc.rust-lang.org/cargo/commands/cargo-publish.html)
- [Cargo Registry Authentication](https://doc.rust-lang.org/cargo/reference/registries.html)

## Current State Analysis

### Step 1: Review Current Workflow

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# View the entire release-rust.yml workflow
cat .github/workflows/release-rust.yml | less
```

### Step 2: Identify What's Missing

Current workflow includes:

- ✅ Multi-platform Rust builds (amd64, arm64, Windows, Linux, macOS)
- ✅ Cross-compilation setup
- ✅ Clippy linting
- ✅ Test execution
- ✅ Binary artifact creation
- ✅ Binary upload to GitHub releases
- ❌ **MISSING: Cargo publish to registry**
- ❌ **MISSING: Crate publishing configuration**
- ❌ **MISSING: Registry authentication**

### Step 3: Check for Publishing Blockers

```bash
# Check if workflows already attempt to publish (they shouldn't)
grep -n "cargo publish" .github/workflows/release-rust.yml

# Expected output: (no matches)
```

If there ARE matches, review them carefully before proceeding.

### Step 4: Analyze Target Repositories with Rust Code

```bash
# Find repositories that use this workflow
grep -r "release-rust.yml" ../ 2>/dev/null | grep -v "ghcommon/.git"

# Check ubuntu-autoinstall-agent specifically
ls -la ../ubuntu-autoinstall-agent/Cargo.toml 2>/dev/null
```

**Expected**: `ubuntu-autoinstall-agent` has Cargo.toml and will benefit from this

### Step 5: Review Cargo.toml in Target Repositories

```bash
# Check the ubuntu-autoinstall-agent Cargo.toml
cat ../ubuntu-autoinstall-agent/Cargo.toml
```

**Look for:**

- Package name
- Version
- Repository URL
- License
- Description
- Any existing registry configuration

**Critical**: The `[package]` section must have all required fields for publishing:

```toml
[package]
name = "ubuntu-autoinstall-agent"
version = "0.1.0"
edition = "2021"
authors = ["Your Name <email@example.com>"]
description = "A clear description"
license = "MIT"  # or appropriate license
repository = "https://github.com/jdfalk/ubuntu-autoinstall-agent"
```

### Decision Point

**Proceed if:**

- ✅ No existing `cargo publish` steps in workflow
- ✅ Target repositories have valid Cargo.toml with required fields
- ✅ You understand GitHub Package Registry for Cargo
- ✅ You can create/use GitHub PAT tokens

**Stop and fix if:**

- ❌ Cargo.toml is missing required fields (fix those first)
- ❌ Unclear about registry authentication
- ❌ Existing publish steps that might conflict

## Understanding GitHub Package Registry for Rust

### Registry URL Format

GitHub uses a specific URL format for Cargo registries:

```
https://ghcr.io/<owner>/<repository>
```

However, Cargo registries use an API endpoint:

```
https://api.github.com/<owner>/<repository>/cargo
```

### Authentication Methods

Three authentication options for GitHub Packages:

1. **GITHUB_TOKEN (recommended for CI)**
   - Automatically available in GitHub Actions
   - Limited to repository scope
   - No manual setup required

2. **Personal Access Token (PAT)**
   - Needs `write:packages` and `read:packages` scopes
   - Can be used across repositories
   - Requires manual creation

3. **GitHub App Token**
   - Advanced option
   - Not covered in this task

### Cargo Configuration

Cargo needs configuration to authenticate with GitHub:

```toml
# .cargo/config.toml
[registries.github]
index = "sparse+https://api.github.com/<owner>/<repository>/cargo/"

[net]
git-fetch-with-cli = true
```

## Implementation Design

### Architecture Overview

We'll add a new job to `release-rust.yml`:

```
build-rust (matrix)
  ↓
  Builds binaries for each platform
  ↓
publish-rust-crate (single run)
  ↓
  1. Check if this is a release (tag push)
  2. Set up Rust
  3. Configure cargo for GitHub registry
  4. Detect crate version
  5. Check if version already published
  6. Publish crate (if new version)
  7. Verify publication
```

### Why a Separate Job?

- **Efficiency**: Only runs once, not for each matrix combination
- **Reliability**: Can depend on all builds succeeding
- **Clarity**: Publishing is logically separate from building
- **Safety**: Can add additional checks before publishing

### Configuration Strategy

Use dynamic configuration to support any repository:

```yaml
env:
  CARGO_REGISTRY_URL: 'sparse+https://api.github.com/${{ github.repository }}/cargo/'
  CARGO_REGISTRY_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Implementation Steps

### Step 1: Backup Current Workflow

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Create backup
cp .github/workflows/release-rust.yml .github/workflows/release-rust.yml.backup

# Verify backup
ls -la .github/workflows/release-rust.yml*
```

### Step 2: Update File Header Version

Open `.github/workflows/release-rust.yml` and update line 2:

**Current:**

```yaml
# version: 1.8.1
```

**New:**

```yaml
# version: 1.9.0
```

**Rationale**: Minor version bump for new feature (publishing)

### Step 3: Add Registry Configuration to Env

Find the `jobs:` section (around line 27) and add environment variables to the workflow level or to
specific jobs.

Actually, let's add a new job. Find the end of the `build-rust` job (around line 290) and add a new
job after it:

**Add this new job:**

```yaml
# Publish crate to GitHub Package Registry
publish-rust-crate:
  name: Publish Rust Crate
  runs-on: ubuntu-latest
  needs: build-rust
  # Only publish on tag pushes (releases)
  if: startsWith(github.ref, 'refs/tags/v')

  permissions:
    contents: read
    packages: write

  steps:
    - name: Checkout repository
      uses: actions/checkout@v5

    - name: Set up Rust
      uses: actions-rs/toolchain@v1
      with:
        toolchain: stable
        override: true
        components: rustfmt

    - name: Detect crate information
      id: crate-info
      run: |
        # Extract crate name and version from Cargo.toml
        if [ ! -f "Cargo.toml" ]; then
          echo "❌ No Cargo.toml found in repository root"
          exit 1
        fi

        CRATE_NAME=$(grep -m1 '^name =' Cargo.toml | sed 's/name = "\(.*\)"/\1/')
        CRATE_VERSION=$(grep -m1 '^version =' Cargo.toml | sed 's/version = "\(.*\)"/\1/')

        if [ -z "$CRATE_NAME" ] || [ -z "$CRATE_VERSION" ]; then
          echo "❌ Could not extract crate name or version from Cargo.toml"
          exit 1
        fi

        echo "📦 Crate: $CRATE_NAME"
        echo "🏷️  Version: $CRATE_VERSION"

        # Export to GitHub outputs
        echo "crate-name=$CRATE_NAME" >> $GITHUB_OUTPUT
        echo "crate-version=$CRATE_VERSION" >> $GITHUB_OUTPUT

        # Verify tag matches crate version
        TAG_VERSION="${GITHUB_REF#refs/tags/v}"
        if [ "$TAG_VERSION" != "$CRATE_VERSION" ]; then
          echo "⚠️  Warning: Git tag ($TAG_VERSION) doesn't match Cargo.toml version ($CRATE_VERSION)"
          echo "Will use Cargo.toml version for publishing"
        fi

    - name: Configure Cargo for GitHub Registry
      env:
        CARGO_REGISTRY_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        # Create .cargo directory if it doesn't exist
        mkdir -p ~/.cargo

        # Configure the GitHub registry
        cat > ~/.cargo/config.toml << EOF
        [registries.github]
        index = "sparse+https://api.github.com/${{ github.repository }}/cargo/"

        [registry]
        default = "github"

        [net]
        git-fetch-with-cli = true
        EOF

        # Configure authentication
        cat > ~/.cargo/credentials.toml << EOF
        [registries.github]
        token = "${CARGO_REGISTRY_TOKEN}"
        EOF

        # Set restrictive permissions on credentials
        chmod 600 ~/.cargo/credentials.toml

        echo "✅ Cargo configured for GitHub Package Registry"
        echo "📍 Registry: https://api.github.com/${{ github.repository }}/cargo/"

    - name: Verify Cargo.toml completeness
      run: |
        # Check for required fields
        REQUIRED_FIELDS=("name" "version" "edition" "authors" "description" "license" "repository")

        echo "🔍 Verifying Cargo.toml has required fields for publishing..."

        for field in "${REQUIRED_FIELDS[@]}"; do
          if grep -q "^$field =" Cargo.toml; then
            echo "✅ $field: found"
          else
            echo "❌ $field: MISSING"
            echo ""
            echo "To fix: Add to [package] section in Cargo.toml:"
            case $field in
              authors)
                echo 'authors = ["Your Name <email@example.com>"]'
                ;;
              description)
                echo 'description = "A clear description of your crate"'
                ;;
              license)
                echo 'license = "MIT"  # or your chosen license'
                ;;
              repository)
                echo 'repository = "https://github.com/${{ github.repository }}"'
                ;;
            esac
            exit 1
          fi
        done

        echo ""
        echo "✅ All required fields present in Cargo.toml"

    - name: Check if version already published
      id: check-published
      continue-on-error: true
      run: |
        CRATE_NAME="${{ steps.crate-info.outputs.crate-name }}"
        CRATE_VERSION="${{ steps.crate-info.outputs.crate-version }}"

        echo "🔍 Checking if $CRATE_NAME@$CRATE_VERSION is already published..."

        # Try to get package info from GitHub API
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
          -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
          "https://api.github.com/orgs/${{ github.repository_owner }}/packages/cargo/$CRATE_NAME/versions")

        if [ "$HTTP_STATUS" = "200" ]; then
          echo "📦 Package exists, checking versions..."

          # Get all versions
          VERSIONS=$(curl -s \
            -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
            "https://api.github.com/orgs/${{ github.repository_owner }}/packages/cargo/$CRATE_NAME/versions" \
            | jq -r '.[].name')

          if echo "$VERSIONS" | grep -q "^${CRATE_VERSION}$"; then
            echo "⚠️  Version $CRATE_VERSION already published"
            echo "already-published=true" >> $GITHUB_OUTPUT
          else
            echo "✅ Version $CRATE_VERSION not yet published"
            echo "already-published=false" >> $GITHUB_OUTPUT
          fi
        else
          echo "📭 Package not found (first publish)"
          echo "already-published=false" >> $GITHUB_OUTPUT
        fi

    - name: Publish crate
      if: steps.check-published.outputs.already-published != 'true'
      run: |
        echo "📤 Publishing crate to GitHub Package Registry..."
        echo ""

        # Publish to GitHub registry
        cargo publish \
          --registry github \
          --verbose \
          --allow-dirty \
          --no-verify

        echo ""
        echo "✅ Crate published successfully!"

    - name: Verify publication
      if: steps.check-published.outputs.already-published != 'true'
      run: |
        CRATE_NAME="${{ steps.crate-info.outputs.crate-name }}"
        CRATE_VERSION="${{ steps.crate-info.outputs.crate-version }}"

        echo "🔍 Waiting for package to appear in registry..."
        sleep 10  # Give GitHub time to index the package

        # Try to fetch the package info
        for i in {1..5}; do
          if cargo search "$CRATE_NAME" --registry github | grep -q "$CRATE_NAME"; then
            echo "✅ Package verified in GitHub Package Registry"
            echo "📦 $CRATE_NAME@$CRATE_VERSION"
            echo "🔗 https://github.com/${{ github.repository }}/packages"
            exit 0
          fi
          echo "⏳ Attempt $i/5: Package not yet indexed, waiting..."
          sleep 10
        done

        echo "⚠️  Package published but not yet searchable (this is normal, may take a few minutes)"
        echo "Check: https://github.com/${{ github.repository }}/packages"

    - name: Skip publication (already published)
      if: steps.check-published.outputs.already-published == 'true'
      run: |
        echo "ℹ️  Skipping publication: version already exists"
        echo "📦 ${{ steps.crate-info.outputs.crate-name }}@${{ steps.crate-info.outputs.crate-version }}"
        echo "🔗 https://github.com/${{ github.repository }}/packages"

    - name: Create publication summary
      if: always()
      run: |
        echo "# 📦 Rust Crate Publication Summary" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "**Crate**: ${{ steps.crate-info.outputs.crate-name }}" >> $GITHUB_STEP_SUMMARY
        echo "**Version**: ${{ steps.crate-info.outputs.crate-version }}" >> $GITHUB_STEP_SUMMARY
        echo "**Repository**: ${{ github.repository }}" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY

        if [ "${{ steps.check-published.outputs.already-published }}" = "true" ]; then
          echo "**Status**: ⏭️ Skipped (version already published)" >> $GITHUB_STEP_SUMMARY
        else
          echo "**Status**: ✅ Published successfully" >> $GITHUB_STEP_SUMMARY
        fi

        echo "" >> $GITHUB_STEP_SUMMARY
        echo "**Package URL**: https://github.com/${{ github.repository }}/packages" >> $GITHUB_STEP_SUMMARY
```

### Step 4: Add Documentation Comment

Add a comment at the beginning of the new job explaining its purpose:

```yaml
# ============================================================================
# RUST CRATE PUBLISHING TO GITHUB PACKAGE REGISTRY
# ============================================================================
#
# This job publishes the Rust crate to GitHub Package Registry.
#
# When it runs:
# - Only on tag pushes (e.g., v1.2.3)
# - After all build-rust matrix jobs complete successfully
#
# What it does:
# 1. Extracts crate name and version from Cargo.toml
# 2. Configures Cargo to use GitHub Package Registry
# 3. Checks if this version is already published (avoids duplicate publish errors)
# 4. Publishes the crate to GitHub Package Registry
# 5. Verifies publication was successful
#
# Prerequisites for publishing:
# - Cargo.toml must have: name, version, authors, description, license, repository
# - Git tag must be pushed (e.g., git tag v1.2.3 && git push --tags)
# - GITHUB_TOKEN must have packages:write permission (automatic in Actions)
#
# Registry URL: https://api.github.com/{owner}/{repo}/cargo/
# Package URL: https://github.com/{owner}/{repo}/packages
#
# ============================================================================

publish-rust-crate:
  # ... (the job content from Step 3)
```

### Step 5: Validate Workflow Syntax

```bash
# Check for YAML syntax errors
yamllint .github/workflows/release-rust.yml

# Check for GitHub Actions syntax errors
actionlint .github/workflows/release-rust.yml

# If no errors, proceed. If errors, fix them before committing
```

### Step 6: Test Workflow Parsing (Dry Run)

```bash
# Use GitHub API to validate workflow syntax
gh api repos/jdfalk/ghcommon/actions/workflows/release-rust.yml \
  --jq '.state, .path'

# Expected output:
# active
# .github/workflows/release-rust.yml
```

### Step 7: Review Complete Changes

```bash
# View diff
git diff .github/workflows/release-rust.yml

# Count lines changed
git diff .github/workflows/release-rust.yml --stat

# Review specific sections
git diff .github/workflows/release-rust.yml | grep -A 5 "publish-rust-crate"
```

### Step 8: Commit Changes

```bash
# Stage changes
git add .github/workflows/release-rust.yml

# Commit with detailed message
git commit -m "feat(release): add Rust crate publishing to GitHub Packages

Implemented automated Rust crate publishing to GitHub Package Registry
in the release-rust.yml workflow.

Changes:
- Added publish-rust-crate job that runs after build-rust completes
- Configured Cargo to use GitHub Package Registry API
- Implemented version detection from Cargo.toml
- Added duplicate version check to prevent publish errors
- Includes verification step to confirm publication
- Only runs on tag pushes (refs/tags/v*)
- Requires Cargo.toml to have all required publishing fields

The job:
1. Detects crate name and version from Cargo.toml
2. Configures cargo with GitHub registry credentials
3. Verifies Cargo.toml has required fields (authors, description, license, etc.)
4. Checks if version is already published
5. Publishes crate if version is new
6. Verifies publication was successful
7. Creates detailed summary in GitHub Actions UI

Registry: https://api.github.com/{owner}/{repo}/cargo/
Packages: https://github.com/{owner}/{repo}/packages

Prerequisites:
- Cargo.toml must include: name, version, authors, description, license, repository
- Release must be triggered with a tag (e.g., v1.2.3)
- GITHUB_TOKEN automatically has packages:write permission

Related to task: task-03-rust-packages"

# Push changes
git push origin main
```

## Validation

### Validation 1: Workflow File Syntax

```bash
# Verify workflow syntax
actionlint .github/workflows/release-rust.yml

# Check workflow is active
gh api repos/jdfalk/ghcommon/actions/workflows/release-rust.yml --jq '.state'
# Expected: active
```

### Validation 2: Check Workflow in GitHub UI

```bash
# Open workflow in browser
gh browse --repo jdfalk/ghcommon .github/workflows/release-rust.yml
```

**Verify in UI:**

- Workflow appears in Actions tab
- No syntax errors shown
- New `publish-rust-crate` job visible in workflow graph

### Validation 3: Dry Run Test (Optional)

Create a test branch to verify workflow parsing:

```bash
# Create test branch
git checkout -b test-rust-publish

# Trigger workflow dispatch (if you add that option)
# Or wait for next commit to see if workflow parses correctly

# Check workflow runs
gh run list --workflow=release-rust.yml --limit 5

# Switch back to main
git checkout main
git branch -D test-rust-publish
```

### Validation 4: Prepare Target Repository

The workflow is now in ghcommon. Next, prepare ubuntu-autoinstall-agent:

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-agent

# Check Cargo.toml has required fields
cargo metadata --no-deps --format-version 1 | jq '.packages[0] | {name, version, authors, description, license, repository}'
```

**Expected output format:**

```json
{
  "name": "ubuntu-autoinstall-agent",
  "version": "0.1.0",
  "authors": ["Author Name <email@example.com>"],
  "description": "Ubuntu autoinstall automation agent",
  "license": "MIT",
  "repository": "https://github.com/jdfalk/ubuntu-autoinstall-agent"
}
```

**If any field is null or missing**, fix Cargo.toml:

```bash
# Open Cargo.toml
code Cargo.toml

# Add missing fields to [package] section:
# authors = ["Your Name <email@example.com>"]
# description = "A description of the project"
# license = "MIT"  # or appropriate license
# repository = "https://github.com/jdfalk/ubuntu-autoinstall-agent"
```

### Validation 5: Test End-to-End (Full Test)

This requires creating a release. **Only do this when ready to publish:**

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-agent

# Ensure Cargo.toml version is set correctly
# Ensure all required fields are present

# Create and push a tag
git tag v0.1.0
git push origin v0.1.0

# Monitor workflow
gh run watch

# Check for the publish-rust-crate job
gh run view --log | grep -A 50 "publish-rust-crate"
```

**Expected:**

1. Workflow triggers on tag push
2. build-rust jobs complete successfully
3. publish-rust-crate job runs
4. Crate is published to GitHub Packages
5. Package appears at: https://github.com/jdfalk/ubuntu-autoinstall-agent/packages

### Validation 6: Verify Package Publication

```bash
# Check if package exists
gh api /users/jdfalk/packages?package_type=cargo

# Or for organization
gh api /orgs/jdfalk/packages?package_type=cargo

# View package details
gh api /users/jdfalk/packages/cargo/ubuntu-autoinstall-agent

# List versions
gh api /users/jdfalk/packages/cargo/ubuntu-autoinstall-agent/versions
```

### Validation 7: Test Package Installation

Test that the published package can be used:

```bash
# Create test project
mkdir -p /tmp/test-rust-package
cd /tmp/test-rust-package

# Initialize new Rust project
cargo init --name test-consumer

# Configure to use GitHub registry
mkdir .cargo
cat > .cargo/config.toml << EOF
[registries.github]
index = "sparse+https://api.github.com/jdfalk/ubuntu-autoinstall-agent/cargo/"

[net]
git-fetch-with-cli = true
EOF

# Try to add the package as dependency
# Note: This requires authentication for private packages
echo $GITHUB_TOKEN | cargo login --registry github

# Search for the package
cargo search ubuntu-autoinstall-agent --registry github

# Expected: Package found with version
```

## Troubleshooting Guide

### Issue 1: Cargo.toml Missing Required Fields

**Symptom**: Verification step fails with "MISSING" fields

**Error message:**

```
❌ authors: MISSING
❌ description: MISSING
```

**Root Cause**: Cargo.toml doesn't have all required fields for publishing

**Solution**:

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-agent

# Edit Cargo.toml
code Cargo.toml

# Add to [package] section:
```

```toml
[package]
name = "ubuntu-autoinstall-agent"
version = "0.1.0"
edition = "2021"
authors = ["Your Name <your.email@example.com>"]
description = "Automated Ubuntu installation agent for unattended deployments"
license = "MIT"
repository = "https://github.com/jdfalk/ubuntu-autoinstall-agent"
keywords = ["ubuntu", "autoinstall", "automation", "deployment"]
categories = ["command-line-utilities", "development-tools"]
readme = "README.md"

# Optional but recommended:
homepage = "https://github.com/jdfalk/ubuntu-autoinstall-agent"
documentation = "https://github.com/jdfalk/ubuntu-autoinstall-agent/blob/main/README.md"
```

```bash
# Commit the changes
git add Cargo.toml
git commit -m "docs(cargo): add required publishing metadata to Cargo.toml"
git push
```

### Issue 2: Permission Denied When Publishing

**Symptom**: `error: failed to publish to registry`

**Error message:**

```
error: failed to publish to registry at https://api.github.com/...
Caused by: permission denied
```

**Root Cause**: GITHUB_TOKEN doesn't have packages:write permission

**Solution**:

Check workflow permissions:

```yaml
permissions:
  contents: read
  packages: write # ← Must be present
```

If missing, add to the `publish-rust-crate` job:

```yaml
publish-rust-crate:
  name: Publish Rust Crate
  runs-on: ubuntu-latest
  needs: build-rust
  if: startsWith(github.ref, 'refs/tags/v')

  permissions:
    contents: read
    packages: write # Add this
```

### Issue 3: Version Already Exists

**Symptom**: `error: crate version `X.Y.Z` is already uploaded`

**Expected Behavior**: The check-published step should prevent this

**If it still happens:**

```bash
# Check what versions exist
gh api /users/jdfalk/packages/cargo/ubuntu-autoinstall-agent/versions --jq '.[] | .name'

# Increment version in Cargo.toml
# Change: version = "0.1.0"
# To:     version = "0.1.1"  (or appropriate)

# Create new tag
git tag v0.1.1
git push origin v0.1.1
```

### Issue 4: Registry Configuration Not Found

**Symptom**: `error: no registry entry found for 'github'`

**Root Cause**: Cargo config wasn't created properly

**Solution**:

The workflow should create `~/.cargo/config.toml`. If it fails, check:

```yaml
- name: Configure Cargo for GitHub Registry
  run: |
    mkdir -p ~/.cargo  # ← Ensure directory exists

    cat > ~/.cargo/config.toml << EOF
    [registries.github]
    index = "sparse+https://api.github.com/${{ github.repository }}/cargo/"

    [registry]
    default = "github"
    EOF
```

### Issue 5: Authentication Failed

**Symptom**: `error: failed to authenticate to registry`

**Root Cause**: Credentials not properly configured

**Solution**:

Verify credentials file creation:

```yaml
- name: Configure Cargo for GitHub Registry
  env:
    CARGO_REGISTRY_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    mkdir -p ~/.cargo

    cat > ~/.cargo/credentials.toml << EOF
    [registries.github]
    token = "${CARGO_REGISTRY_TOKEN}"  # ← Must use env var
    EOF

    chmod 600 ~/.cargo/credentials.toml  # ← Important for security
```

### Issue 6: Package Not Searchable After Publishing

**Symptom**: `cargo search` doesn't find the package immediately

**Root Cause**: GitHub Package Registry indexing delay

**Solution**:

This is normal and expected. The package exists but takes time to index:

```bash
# Wait 5-10 minutes, then try again
cargo search ubuntu-autoinstall-agent --registry github

# Or check directly via API
gh api /users/jdfalk/packages/cargo/ubuntu-autoinstall-agent
```

**The package is available for use even if search doesn't find it yet.**

### Issue 7: Tag Version Mismatch

**Symptom**: Warning about tag not matching Cargo.toml version

**Error message:**

```
⚠️  Warning: Git tag (0.1.1) doesn't match Cargo.toml version (0.1.0)
```

**Root Cause**: Git tag and Cargo.toml version are different

**Solution**:

```bash
# Option 1: Update Cargo.toml to match tag
code Cargo.toml
# Change version = "0.1.0" to version = "0.1.1"
git add Cargo.toml
git commit -m "chore: bump version to 0.1.1"
git push

# Option 2: Delete and recreate tag with correct version
git tag -d v0.1.1
git push origin :refs/tags/v0.1.1  # Delete remote tag
git tag v0.1.0  # Create correct tag
git push origin v0.1.0
```

**Best Practice**: Always keep Cargo.toml version in sync with Git tags

### Issue 8: Publish Fails with "dirty" Repository

**Symptom**: `error: 1 uncommitted file in working directory`

**Root Cause**: Working directory has uncommitted changes

**Why We Use `--allow-dirty`**: In CI, generated files or workflow artifacts might exist

**If you see this error**: The `--allow-dirty` flag should handle it, but if not:

```yaml
- name: Publish crate
  run: |
    # Clean any generated files
    cargo clean

    # Show what's "dirty"
    git status

    # Publish with --allow-dirty
    cargo publish \
      --registry github \
      --allow-dirty \
      --no-verify
```

### Issue 9: Network Timeouts

**Symptom**: `error: failed to publish: timeout`

**Root Cause**: GitHub API or registry temporarily unavailable

**Solution**:

Add retry logic:

```yaml
- name: Publish crate
  run: |
    MAX_ATTEMPTS=3
    ATTEMPT=0

    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
      ATTEMPT=$((ATTEMPT + 1))
      echo "Attempt $ATTEMPT/$MAX_ATTEMPTS"

      if cargo publish --registry github --allow-dirty --no-verify; then
        echo "✅ Published successfully"
        exit 0
      else
        if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
          echo "⏳ Waiting 30 seconds before retry..."
          sleep 30
        fi
      fi
    done

    echo "❌ Failed after $MAX_ATTEMPTS attempts"
    exit 1
```

## Testing Strategy

### Test 1: Workflow Syntax Test (Safe)

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Validate workflow file
actionlint .github/workflows/release-rust.yml
yamllint .github/workflows/release-rust.yml

# Check workflow is recognized by GitHub
gh workflow list | grep "release-rust"
```

**Expected**: No errors, workflow listed

### Test 2: Dry Run with Mock Data (Safer)

Create a test branch and add workflow_dispatch trigger temporarily:

```bash
git checkout -b test-rust-publish-dryrun

# Edit release-rust.yml, add to 'on:' section:
```

```yaml
on:
  workflow_call:
    # ... existing config
  workflow_dispatch: # Add this for manual testing
    inputs:
      dry_run:
        description: 'Dry run (skip actual publish)'
        required: false
        default: true
        type: boolean
```

```bash
# Commit and push test branch
git add .github/workflows/release-rust.yml
git commit -m "test: add workflow_dispatch for testing"
git push origin test-rust-publish-dryrun

# Trigger manually in GitHub UI or via CLI
gh workflow run release-rust.yml --ref test-rust-publish-dryrun

# Watch the run
gh run watch
```

**After testing**: Delete test branch

```bash
git checkout main
git branch -D test-rust-publish-dryrun
git push origin --delete test-rust-publish-dryrun
```

### Test 3: Full Integration Test (Production)

**⚠️ Warning**: This will actually publish a package!

**Prerequisites:**

1. Cargo.toml has all required fields
2. Version in Cargo.toml is new (not previously published)
3. Repository is ready for a release

**Execute:**

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-agent

# Verify Cargo.toml
cargo metadata --no-deps --format-version 1 | jq '.packages[0]'

# Verify version is new
CRATE_NAME=$(grep -m1 '^name =' Cargo.toml | sed 's/name = "\(.*\)"/\1/')
CRATE_VERSION=$(grep -m1 '^version =' Cargo.toml | sed 's/version = "\(.*\)"/\1/')

echo "Will publish: $CRATE_NAME@$CRATE_VERSION"
echo "Continue? (Ctrl-C to abort)"
read

# Create and push tag
git tag "v$CRATE_VERSION"
git push origin "v$CRATE_VERSION"

# Monitor workflow
gh run watch

# View publish job specifically
gh run view --log | grep -A 100 "publish-rust-crate"

# Check package was created
gh api /users/jdfalk/packages/cargo/$CRATE_NAME

# Try to use the package
mkdir -p /tmp/test-published-crate
cd /tmp/test-published-crate
cargo init
echo "[registries.github]
index = \"sparse+https://api.github.com/jdfalk/ubuntu-autoinstall-agent/cargo/\"" > .cargo/config.toml

cargo search $CRATE_NAME --registry github
```

## Post-Implementation Tasks

### Task 1: Update Documentation

Create documentation for using published crates:

````bash
cd /Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-agent

# Create or update docs
cat > docs/using-published-crate.md << 'EOF'
# Using the Published Crate

## Installation

Add to your `Cargo.toml`:

```toml
[dependencies]
ubuntu-autoinstall-agent = { version = "0.1.0", registry = "github" }

[registries.github]
index = "sparse+https://api.github.com/jdfalk/ubuntu-autoinstall-agent/cargo/"
````

## Authentication

For private packages, authenticate with GitHub:

```bash
# Create Personal Access Token with read:packages scope
# https://github.com/settings/tokens/new

# Configure cargo
cargo login --registry github
# Paste your token when prompted
```

## Usage

```rust
use ubuntu_autoinstall_agent::*;

// Your code here
```

## Troubleshooting

See [Publishing Documentation](../PUBLISHING.md) EOF

git add docs/using-published-crate.md git commit -m "docs: add instructions for using published
crate" git push

````

### Task 2: Add Package Badge to README

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-agent

# Add to README.md after title
````

```markdown
# Ubuntu Autoinstall Agent

[![GitHub Package](https://img.shields.io/github/v/tag/jdfalk/ubuntu-autoinstall-agent?label=crate&logo=rust)](https://github.com/jdfalk/ubuntu-autoinstall-agent/packages)

[Rest of README...]
```

```bash
git add README.md
git commit -m "docs: add package badge to README"
git push
```

### Task 3: Update CHANGELOG

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Add to CHANGELOG.md
cat >> CHANGELOG.md << 'EOF'

## [1.9.0] - 2025-10-05

### Added

- Rust crate publishing to GitHub Package Registry in release-rust.yml
  - Automatic publication on tag pushes
  - Version detection from Cargo.toml
  - Duplicate version checking
  - Publication verification
  - Detailed GitHub Actions summary

### Changed

- release-rust.yml version bumped to 1.9.0

### Documentation

- Added comprehensive task guide for Rust package publishing
EOF

git add CHANGELOG.md
git commit -m "docs: update CHANGELOG for Rust package publishing feature"
git push
```

### Task 4: Notify Team/Users

If this is used by others:

1. Create GitHub Release notes mentioning the new feature
2. Update any internal documentation
3. Notify dependent repositories

## Success Criteria Checklist

Verify all items are complete:

- [ ] release-rust.yml version updated (1.8.1 → 1.9.0)
- [ ] publish-rust-crate job added to workflow
- [ ] Job runs only on tag pushes (startsWith(github.ref, 'refs/tags/v'))
- [ ] Job depends on build-rust completing
- [ ] Cargo configured for GitHub Package Registry
- [ ] Crate information detection implemented
- [ ] Required fields verification added
- [ ] Duplicate version check implemented
- [ ] Publication step with proper flags (--allow-dirty, --no-verify)
- [ ] Verification step included
- [ ] Detailed summary in GitHub Actions
- [ ] Workflow syntax validated (actionlint passes)
- [ ] Changes committed with conventional commit message
- [ ] Changes pushed to origin/main
- [ ] Target repository Cargo.toml has required fields
- [ ] Documentation updated
- [ ] End-to-end test passed (if executed)

## Completion Verification

Run final checks:

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Verify changes are in main
git log --oneline -1 --grep="Rust crate publishing"

# Verify workflow file contains new job
grep -n "publish-rust-crate" .github/workflows/release-rust.yml

# Expected: Line numbers showing the job exists

# Verify workflow is valid
gh workflow view release-rust.yml

# Check version update
grep "^# version:" .github/workflows/release-rust.yml
# Expected: # version: 1.9.0
```

## Follow-Up Tasks

After completing this task:

1. **Task 04**: Implement Go package publishing
2. **Task 05**: Implement Python package publishing
3. **Task 06**: Implement frontend (npm) package publishing
4. **Task 18**: Test all package publishing end-to-end

## Additional Resources

### Cargo Registry Documentation

- [Cargo Registries](https://doc.rust-lang.org/cargo/reference/registries.html)
- [Publishing on Crates.io](https://doc.rust-lang.org/cargo/reference/publishing.html)
- [Alternative Registries](https://doc.rust-lang.org/cargo/reference/registries.html#using-an-alternate-registry)

### GitHub Packages for Cargo

- [Working with the Cargo registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-cargo-registry)
- [Publishing a package](https://docs.github.com/en/packages/learn-github-packages/publishing-a-package)
- [Installing a package](https://docs.github.com/en/packages/learn-github-packages/installing-a-package)

### Authentication

- [Authenticating to GitHub Packages](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-cargo-registry#authenticating-to-github-packages)
- [Creating a personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

---

**Task Complete!** ✅

Rust crates will now be automatically published to GitHub Package Registry on tagged releases.

**Next Suggested Task**: `task-04-go-packages.md` (implement Go package publishing)
