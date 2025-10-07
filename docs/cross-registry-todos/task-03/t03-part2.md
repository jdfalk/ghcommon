<!-- file: docs/cross-registry-todos/task-03/t03-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t03-rust-part2-b2c3d4e5-f6g7 -->

# Task 03 Part 2: Workflow Configuration and Implementation

## Implementation Design

### Architecture Overview

We'll add a new job to `release-rust.yml` that publishes the crate to GitHub Package Registry:

```
Workflow Execution Flow:
========================

1. Tag Push (v1.2.3)
   ↓
2. build-rust (matrix job)
   ├─ linux/amd64 build
   ├─ linux/arm64 build
   ├─ windows/amd64 build
   └─ macos/amd64 build
   ↓
3. All builds complete successfully
   ↓
4. publish-rust-crate (single job)
   ├─ Extract crate info from Cargo.toml
   ├─ Configure Cargo for GitHub registry
   ├─ Verify Cargo.toml completeness
   ├─ Check if version already published
   ├─ Publish crate (if new version)
   ├─ Verify publication successful
   └─ Create summary report
```

### Why a Separate Job?

**Rationale for creating a dedicated publishing job:**

1. **Efficiency**: Only runs once, not for each matrix combination
   - Matrix builds create 4+ jobs (amd64, arm64, Windows, macOS)
   - Publishing only needs to happen once per release
   - Saves GitHub Actions minutes

2. **Reliability**: Can depend on all builds succeeding
   - Uses `needs: build-rust` to wait for all matrix jobs
   - Won't publish if any platform build fails
   - Ensures quality control

3. **Clarity**: Publishing is logically separate from building
   - Binaries vs library publication are different concerns
   - Easier to debug if publishing fails
   - Clear separation of responsibilities

4. **Safety**: Can add additional checks before publishing
   - Version verification
   - Duplicate check
   - Cargo.toml validation
   - Dry-run capability

5. **Maintainability**: Easier to modify publishing logic
   - Changes don't affect build jobs
   - Can add/remove checks independently
   - Clear audit trail

### Configuration Strategy

Use dynamic configuration to support any repository calling this reusable workflow:

```yaml
env:
  # Dynamic registry URL based on current repository
  CARGO_REGISTRY_URL: 'sparse+https://api.github.com/${{ github.repository }}/cargo/'
  
  # Use GitHub's automatic token (requires packages:write permission)
  CARGO_REGISTRY_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  
  # Extract repository information
  REPO_OWNER: ${{ github.repository_owner }}
  REPO_NAME: ${{ github.event.repository.name }}
```

**Benefits:**

- No hardcoded repository names
- Works for any repository using this workflow
- Automatic credential management
- No manual token configuration needed

### Job Design Principles

**publish-rust-crate job:**

```yaml
publish-rust-crate:
  name: Publish Rust Crate  # Human-readable name in UI
  runs-on: ubuntu-latest    # Linux for cargo publish
  needs: build-rust         # Wait for all builds
  
  # Only publish on tag pushes (releases)
  if: startsWith(github.ref, 'refs/tags/v')
  
  permissions:
    contents: read    # Read repository code
    packages: write   # Write to GitHub Packages
  
  steps:
    # ... (implementation steps)
```

**Key design elements:**

1. **Conditional execution**: `if: startsWith(github.ref, 'refs/tags/v')`
   - Only runs on version tags (v1.2.3)
   - Prevents accidental publishes on pushes to main
   - Requires explicit version tagging

2. **Explicit permissions**: Principle of least privilege
   - `contents: read` - Checkout code
   - `packages: write` - Publish packages
   - No write access to contents or other resources

3. **Dependency on builds**: `needs: build-rust`
   - Waits for all matrix build jobs to complete
   - Only runs if ALL builds succeed
   - Ensures quality before publishing

4. **Linux runner**: `runs-on: ubuntu-latest`
   - Cargo publish is platform-independent
   - Linux is fastest and cheapest
   - Consistent environment

## Implementation Steps

### Step 1: Backup Current Workflow

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Create timestamped backup
BACKUP_NAME="release-rust.yml.backup-$(date +%Y%m%d-%H%M%S)"
cp .github/workflows/release-rust.yml .github/workflows/$BACKUP_NAME

# Verify backup created
ls -lh .github/workflows/release-rust.yml*

# Example output:
# -rw-r--r--  1 user  staff  15K Jan 15 10:30 release-rust.yml
# -rw-r--r--  1 user  staff  15K Jan 15 10:30 release-rust.yml.backup-20250115-103000
```

**Why backup:**

- Safe rollback if something goes wrong
- Compare changes easily
- Preserve working version
- No risk of losing tested configuration

**Recovery command (if needed):**

```bash
# Restore from backup
cp .github/workflows/release-rust.yml.backup-20250115-103000 \
   .github/workflows/release-rust.yml
```

### Step 2: Update File Header Version

Open `.github/workflows/release-rust.yml` and update the version on line 2:

**Current:**

```yaml
# file: .github/workflows/release-rust.yml
# version: 1.8.1
# guid: a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6
```

**New:**

```yaml
# file: .github/workflows/release-rust.yml
# version: 1.9.0
# guid: a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6
```

**Rationale**: Minor version bump (1.8.1 → 1.9.0) for new feature

- **Patch** (x.y.Z): Bug fixes, typos
- **Minor** (x.Y.z): New features, backward compatible ← This change
- **Major** (X.y.z): Breaking changes

**Our change**: Adding crate publishing is a new feature, backward compatible (doesn't affect existing binary builds), so it's a minor version bump.

### Step 3: Locate Insertion Point

Find the end of the `build-rust` job to add the new job after it:

```bash
# Find the build-rust job end
grep -n "^  build-rust:" .github/workflows/release-rust.yml
# Example output: 28:  build-rust:

# Find where it ends (next job or end of file)
grep -n "^  [a-z]" .github/workflows/release-rust.yml | grep -A1 "build-rust"
# Look for the line number where the next job starts or file ends

# Or use awk to find the line count
awk '/^  build-rust:/,/^[^ ]/ {print NR": "$0}' \
  .github/workflows/release-rust.yml | tail -20
```

**Typical structure:**

```yaml
Line 28:  build-rust:
Line 29:    name: Build Rust Binary
...
Line 285:    - name: Upload release assets
Line 286:      if: startsWith(github.ref, 'refs/tags/')
...
Line 290:      # (end of build-rust job)
Line 291:
Line 292:  # INSERT NEW JOB HERE
```

**Find exact insertion point:**

```bash
# Show last 10 lines of build-rust job
awk '/^  build-rust:/,/^[^ ]/' .github/workflows/release-rust.yml | tail -15
```

### Step 4: Add Publishing Job Documentation

Add a comprehensive documentation comment before the new job:

```yaml
  # ==========================================================================
  # RUST CRATE PUBLISHING TO GITHUB PACKAGE REGISTRY
  # ==========================================================================
  #
  # This job publishes the Rust crate to GitHub Package Registry after all
  # build jobs complete successfully.
  #
  # WHEN IT RUNS:
  # - Only on tag pushes (e.g., git push --tags v1.2.3)
  # - After ALL build-rust matrix jobs complete successfully
  # - Skipped on regular pushes, PRs, and untagged commits
  #
  # WHAT IT DOES:
  # 1. Extracts crate name and version from Cargo.toml
  # 2. Verifies Git tag matches Cargo.toml version (warning if mismatch)
  # 3. Configures Cargo to use GitHub Package Registry
  # 4. Creates credentials file with GITHUB_TOKEN
  # 5. Validates Cargo.toml has all required publishing fields
  # 6. Checks if this version is already published (avoids duplicate errors)
  # 7. Publishes crate to GitHub Package Registry (if new version)
  # 8. Verifies publication was successful
  # 9. Creates detailed summary in GitHub Actions UI
  #
  # PREREQUISITES FOR PUBLISHING:
  # - Cargo.toml must have these fields in [package] section:
  #   * name         - Crate identifier
  #   * version      - Semantic version (e.g., 1.2.3)
  #   * edition      - Rust edition (2021)
  #   * authors      - List of maintainers with emails
  #   * description  - One-line description (max 100 chars)
  #   * license      - SPDX identifier (e.g., "MIT", "Apache-2.0")
  #   * repository   - GitHub repository URL
  #
  # - Git tag must be pushed:
  #   git tag v1.2.3
  #   git push origin v1.2.3
  #
  # - GITHUB_TOKEN automatically has packages:write permission
  #
  # REGISTRY URLs:
  # - Index:   sparse+https://api.github.com/{owner}/{repo}/cargo/
  # - Packages: https://github.com/{owner}/{repo}/packages
  # - Crate:    https://github.com/{owner}/{repo}/packages?type=cargo
  #
  # AUTHENTICATION:
  # Uses GITHUB_TOKEN (automatic, no configuration needed)
  # Token has packages:write permission by default in Actions
  #
  # ERROR HANDLING:
  # - Skips publishing if version already exists (not an error)
  # - Fails if Cargo.toml is missing required fields
  # - Fails if crate name/version cannot be detected
  # - Creates summary even on failure for debugging
  #
  # TROUBLESHOOTING:
  # - Check: https://github.com/{owner}/{repo}/packages
  # - View logs: Expand "Publish Rust Crate" job in Actions UI
  # - Verify Cargo.toml: Run validation locally with cargo package --list
  # - Test locally: cargo publish --dry-run --allow-dirty
  #
  # ==========================================================================

  publish-rust-crate:
```

**Why such detailed documentation:**

- Complex job with many steps
- Helps future maintainers understand intent
- Documents prerequisites clearly
- Provides troubleshooting guidance
- Explains authentication mechanism
- Lists all required Cargo.toml fields

### Step 5: Implement Job Structure

Add the complete job after the documentation comment:

```yaml
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
          
          # Use toml-cli if available, otherwise use grep/sed
          if command -v toml >/dev/null 2>&1; then
            CRATE_NAME=$(toml get Cargo.toml package.name -r)
            CRATE_VERSION=$(toml get Cargo.toml package.version -r)
          else
            CRATE_NAME=$(grep -m1 '^name =' Cargo.toml | sed 's/name = "\(.*\)"/\1/')
            CRATE_VERSION=$(grep -m1 '^version =' Cargo.toml | sed 's/version = "\(.*\)"/\1/')
          fi
          
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
          else
            echo "✅ Git tag matches Cargo.toml version"
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
```

### Step 6: Add Validation Steps

Continue the job with validation steps:

```yaml
      - name: Verify Cargo.toml completeness
        run: |
          # Check for required fields
          REQUIRED_FIELDS=("name" "version" "edition" "authors" "description" "license" "repository")
          
          echo "🔍 Verifying Cargo.toml has required fields for publishing..."
          echo ""
          
          MISSING_COUNT=0
          for field in "${REQUIRED_FIELDS[@]}"; do
            if grep -q "^$field =" Cargo.toml; then
              VALUE=$(grep "^$field =" Cargo.toml | head -1)
              echo "✅ $field: $VALUE"
            else
              echo "❌ $field: MISSING"
              MISSING_COUNT=$((MISSING_COUNT + 1))
              
              # Provide fix instructions
              case $field in
                authors)
                  echo "   Fix: authors = [\"Your Name <email@example.com>\"]"
                  ;;
                description)
                  echo "   Fix: description = \"A clear description of your crate\""
                  ;;
                license)
                  echo "   Fix: license = \"MIT\"  # or your chosen license"
                  ;;
                repository)
                  echo "   Fix: repository = \"https://github.com/${{ github.repository }}\""
                  ;;
              esac
            fi
          done
          
          echo ""
          if [ $MISSING_COUNT -eq 0 ]; then
            echo "✅ All required fields present in Cargo.toml"
          else
            echo "❌ $MISSING_COUNT required fields missing from Cargo.toml"
            echo ""
            echo "Add the missing fields to the [package] section and try again."
            exit 1
          fi
      
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
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/orgs/${{ github.repository_owner }}/packages/cargo/$CRATE_NAME/versions")
          
          if [ "$HTTP_STATUS" = "200" ]; then
            echo "📦 Package exists, checking versions..."
            
            # Get all versions
            VERSIONS=$(curl -s \
              -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
              -H "Accept: application/vnd.github.v3+json" \
              "https://api.github.com/orgs/${{ github.repository_owner }}/packages/cargo/$CRATE_NAME/versions" \
              | jq -r '.[].name // empty' 2>/dev/null)
            
            if [ -n "$VERSIONS" ]; then
              echo "Found versions:"
              echo "$VERSIONS" | head -5
              
              if echo "$VERSIONS" | grep -q "^${CRATE_VERSION}$"; then
                echo ""
                echo "⚠️  Version $CRATE_VERSION already published"
                echo "already-published=true" >> $GITHUB_OUTPUT
                exit 0
              fi
            fi
            
            echo "✅ Version $CRATE_VERSION not yet published"
            echo "already-published=false" >> $GITHUB_OUTPUT
          else
            echo "📭 Package not found (first publish for this crate)"
            echo "already-published=false" >> $GITHUB_OUTPUT
          fi
```

**Next**: Part 3 will cover publishing steps, verification, and error handling.

---

**Part 2 Complete**: Implementation design, workflow configuration, job structure, and validation steps. ✅

**Continue to Part 3** for publishing execution, verification, and summary generation.
