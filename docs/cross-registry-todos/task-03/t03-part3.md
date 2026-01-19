<!-- file: docs/cross-registry-todos/task-03/t03-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t03-rust-part3-c3d4e5f6-g7h8 -->
<!-- last-edited: 2026-01-19 -->

# Task 03 Part 3: Publishing, Verification, and Testing

## Publishing Steps

### Step 1: Implement Cargo Publish

Add the publishing step to the workflow (continuing from Part 2):

```yaml
- name: Publish crate
  if: steps.check-published.outputs.already-published != 'true'
  env:
    CARGO_REGISTRY_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    echo "📤 Publishing crate to GitHub Package Registry..."
    echo ""
    echo "Crate: ${{ steps.crate-info.outputs.crate-name }}"
    echo "Version: ${{ steps.crate-info.outputs.crate-version }}"
    echo "Registry: https://api.github.com/${{ github.repository }}/cargo/"
    echo ""

    # Publish to GitHub registry
    cargo publish \
      --registry github \
      --verbose \
      --allow-dirty \
      --no-verify

    echo ""
    echo "✅ Crate published successfully!"
    echo "📦 Package: https://github.com/${{ github.repository }}/packages"
```

**Key flags explained:**

- `--registry github`: Use the GitHub registry we configured
- `--verbose`: Show detailed output for debugging
- `--allow-dirty`: Allow uncommitted changes (CI environment)
- `--no-verify`: Skip building/testing (already done in build-rust job)

**Why `--no-verify`:**

The `build-rust` job already:

- Built all platforms successfully
- Ran tests
- Ran clippy
- Verified the code works

Running verification again during publish would:

- Duplicate work
- Waste CI time
- Potentially fail on cross-compilation edge cases

### Step 2: Add Post-Publish Verification

Verify the package is accessible after publishing:

```yaml
- name: Verify publication
  if: steps.check-published.outputs.already-published != 'true'
  run: |
    CRATE_NAME="${{ steps.crate-info.outputs.crate-name }}"
    CRATE_VERSION="${{ steps.crate-info.outputs.crate-version }}"

    echo "🔍 Verifying package is accessible in registry..."
    echo ""

    # Wait for package to be indexed
    echo "⏳ Waiting 10 seconds for package indexing..."
    sleep 10

    # Try to fetch package metadata via API
    for i in {1..5}; do
      echo "Attempt $i/5: Checking package availability..."

      HTTP_STATUS=$(curl -s -o /tmp/package-info.json -w "%{http_code}" \
        -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/orgs/${{ github.repository_owner }}/packages/cargo/$CRATE_NAME")

      if [ "$HTTP_STATUS" = "200" ]; then
        echo ""
        echo "✅ Package verified in GitHub Package Registry"
        echo ""
        echo "📦 Package Details:"
        cat /tmp/package-info.json | jq -r '
          "  Name: \(.name)",
          "  Package Type: \(.package_type)",
          "  Visibility: \(.visibility)",
          "  URL: \(.html_url)",
          "  Total Downloads: \(.download_count // 0)"
        '

        echo ""
        echo "🏷️  Available Versions:"
        curl -s \
          -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
          -H "Accept: application/vnd.github.v3+json" \
          "https://api.github.com/orgs/${{ github.repository_owner }}/packages/cargo/$CRATE_NAME/versions" \
          | jq -r '.[] | "  - \(.name) (published \(.created_at))"' | head -10

        echo ""
        echo "✅ Verification complete"
        exit 0
      fi

      if [ $i -lt 5 ]; then
        echo "Package not yet available, waiting 10 seconds..."
        sleep 10
      fi
    done

    echo ""
    echo "⚠️  Package published but not yet searchable (this can take a few minutes)"
    echo "🔗 Check: https://github.com/${{ github.repository }}/packages"
    echo ""
    echo "This is normal for new packages. The package will appear shortly."
```

**Verification approach:**

1. **Wait period**: Give GitHub time to index (10 seconds)
2. **Retry logic**: Try 5 times with 10-second intervals
3. **API verification**: Use GitHub Packages API to check existence
4. **Metadata display**: Show package details if found
5. **Graceful handling**: Warn but don't fail if not immediately visible

### Step 3: Handle Already-Published Scenario

Add a skip message for duplicate versions:

```yaml
- name: Skip publication (already published)
  if: steps.check-published.outputs.already-published == 'true'
  run: |
    echo "ℹ️  Skipping publication: version already exists"
    echo ""
    echo "📦 Crate: ${{ steps.crate-info.outputs.crate-name }}"
    echo "🏷️  Version: ${{ steps.crate-info.outputs.crate-version }}"
    echo "🔗 Package: https://github.com/${{ github.repository }}/packages"
    echo ""
    echo "To publish a new version:"
    echo "1. Update version in Cargo.toml"
    echo "2. Commit the change"
    echo "3. Create and push a new tag: git tag v<new-version> && git push --tags"
```

**Why this step:**

- Prevents confusion when version already exists
- Provides clear guidance on what to do next
- Avoids treating duplicate as an error (it's expected behavior)
- Shows package URL for verification

### Step 4: Create Execution Summary

Add a summary that appears in the GitHub Actions UI:

```yaml
- name: Create publication summary
  if: always()
  run: |
    echo "# 📦 Rust Crate Publication Summary" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "**Crate**: \`${{ steps.crate-info.outputs.crate-name }}\`" >> $GITHUB_STEP_SUMMARY
    echo "**Version**: \`${{ steps.crate-info.outputs.crate-version }}\`" >> $GITHUB_STEP_SUMMARY
    echo "**Repository**: \`${{ github.repository }}\`" >> $GITHUB_STEP_SUMMARY
    echo "**Tag**: \`${GITHUB_REF#refs/tags/}\`" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY

    if [ "${{ steps.check-published.outputs.already-published }}" = "true" ]; then
      echo "**Status**: ⏭️ **Skipped** (version already published)" >> $GITHUB_STEP_SUMMARY
      echo "" >> $GITHUB_STEP_SUMMARY
      echo "This version already exists in the package registry." >> $GITHUB_STEP_SUMMARY
    elif [ "${{ job.status }}" = "success" ]; then
      echo "**Status**: ✅ **Published successfully**" >> $GITHUB_STEP_SUMMARY
      echo "" >> $GITHUB_STEP_SUMMARY
      echo "The crate has been published to GitHub Package Registry." >> $GITHUB_STEP_SUMMARY
    else
      echo "**Status**: ❌ **Publication failed**" >> $GITHUB_STEP_SUMMARY
      echo "" >> $GITHUB_STEP_SUMMARY
      echo "Check the job logs for error details." >> $GITHUB_STEP_SUMMARY
    fi

    echo "" >> $GITHUB_STEP_SUMMARY
    echo "## 📍 Package Links" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "- **Packages**: https://github.com/${{ github.repository }}/packages" >> $GITHUB_STEP_SUMMARY
    echo "- **Registry Index**: https://api.github.com/${{ github.repository }}/cargo/" >> $GITHUB_STEP_SUMMARY
    echo "- **This Release**: https://github.com/${{ github.repository }}/releases/tag/${GITHUB_REF#refs/tags/}" >> $GITHUB_STEP_SUMMARY

    echo "" >> $GITHUB_STEP_SUMMARY
    echo "## 📚 Using This Crate" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "Add to your \`Cargo.toml\`:" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "\`\`\`toml" >> $GITHUB_STEP_SUMMARY
    echo "${{ steps.crate-info.outputs.crate-name }} = \"${{ steps.crate-info.outputs.crate-version }}\"" >> $GITHUB_STEP_SUMMARY
    echo "\`\`\`" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "Configure the registry in \`.cargo/config.toml\`:" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "\`\`\`toml" >> $GITHUB_STEP_SUMMARY
    echo "[registries.github]" >> $GITHUB_STEP_SUMMARY
    echo "index = \"sparse+https://api.github.com/${{ github.repository }}/cargo/\"" >> $GITHUB_STEP_SUMMARY
    echo "\`\`\`" >> $GITHUB_STEP_SUMMARY
```

**Summary features:**

- Shows at top of Actions run page
- Includes status (published/skipped/failed)
- Provides package URLs
- Shows usage instructions
- Appears even if job fails (`if: always()`)

## Local Testing

Before pushing changes, test locally to catch issues:

### Test 1: Validate Cargo.toml

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-agent

# Dry run publish (doesn't actually publish)
cargo publish --dry-run --allow-dirty

# Expected output:
#     Updating crates.io index
#    Packaging ubuntu-autoinstall-agent v0.1.0 (/path/to/project)
#    Verifying ubuntu-autoinstall-agent v0.1.0 (/path/to/project)
#     Compiling ubuntu-autoinstall-agent v0.1.0 (/path/to/project)
#     Finished dev [unoptimized + debuginfo] target(s) in 5.23s
#     Packaged 123 files, 456.7KB (234.5KB compressed)
#    Uploading ubuntu-autoinstall-agent v0.1.0 (/path/to/project)
# [DRY RUN] not uploading crate to registry
```

**What this tests:**

- Cargo.toml has all required fields
- Project builds successfully
- No files are excluded that shouldn't be
- Package size is reasonable

**Common errors and fixes:**

Error: `missing field 'license'`

```bash
# Add to Cargo.toml [package] section:
license = "MIT"
```

Error: `missing field 'description'`

```bash
# Add to Cargo.toml [package] section:
description = "Ubuntu autoinstall agent for automated provisioning"
```

Error: `missing field 'repository'`

```bash
# Add to Cargo.toml [package] section:
repository = "https://github.com/jdfalk/ubuntu-autoinstall-agent"
```

### Test 2: Package Contents

```bash
# List what will be included in the package
cargo package --list

# Expected: source files, Cargo.toml, README, LICENSE
# NOT expected: target/, .git/, node_modules/, etc.
```

**Check for issues:**

- ❌ Includes compiled binaries (target/)
- ❌ Includes Git history (.git/)
- ❌ Includes secrets or config files
- ✅ Includes source code (src/)
- ✅ Includes Cargo.toml and Cargo.lock
- ✅ Includes README.md and LICENSE

**Fix exclusions with `.cargo/package.include` or `.cargo/package.exclude` in Cargo.toml:**

```toml
[package]
exclude = [
    "target/",
    ".github/",
    "*.log",
    ".env",
]
```

### Test 3: Local Build Verification

```bash
# Build in release mode
cargo build --release

# Run tests
cargo test

# Run clippy
cargo clippy -- -D warnings

# Expected: All pass with no errors
```

### Test 4: Simulate CI Environment

Create a test script that mimics the CI workflow:

```bash
#!/bin/bash
# file: test-publish-workflow.sh
# version: 1.0.0
# guid: test-publish-workflow

set -e

echo "=== Simulating CI Publish Workflow ==="
echo ""

# Step 1: Extract crate info
echo "Step 1: Extracting crate information..."
CRATE_NAME=$(grep -m1 '^name =' Cargo.toml | sed 's/name = "\(.*\)"/\1/')
CRATE_VERSION=$(grep -m1 '^version =' Cargo.toml | sed 's/version = "\(.*\)"/\1/')
echo "✅ Crate: $CRATE_NAME"
echo "✅ Version: $CRATE_VERSION"
echo ""

# Step 2: Verify required fields
echo "Step 2: Verifying Cargo.toml completeness..."
REQUIRED_FIELDS=("name" "version" "edition" "authors" "description" "license" "repository")
for field in "${REQUIRED_FIELDS[@]}"; do
  if grep -q "^$field =" Cargo.toml; then
    echo "✅ $field: present"
  else
    echo "❌ $field: MISSING"
    exit 1
  fi
done
echo ""

# Step 3: Dry-run publish
echo "Step 3: Testing publish (dry-run)..."
cargo publish --dry-run --allow-dirty --no-verify
echo "✅ Dry-run successful"
echo ""

# Step 4: Check package contents
echo "Step 4: Checking package contents..."
FILE_COUNT=$(cargo package --list | wc -l)
echo "✅ Package contains $FILE_COUNT files"
echo ""

echo "=== All checks passed! ==="
echo "Ready to commit workflow changes."
```

**Run the test:**

```bash
chmod +x test-publish-workflow.sh
./test-publish-workflow.sh
```

## Workflow Validation

### Validate YAML Syntax

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Check for YAML syntax errors
yamllint .github/workflows/release-rust.yml

# Expected: No errors
# If errors, fix indentation/structure before proceeding
```

**Common YAML errors:**

- Inconsistent indentation (mix of tabs/spaces)
- Missing colons after keys
- Incorrect list formatting
- Trailing spaces
- Missing quotes around special characters

### Validate GitHub Actions Syntax

```bash
# Check for Actions-specific errors
actionlint .github/workflows/release-rust.yml

# Expected: No errors
# If errors, fix before committing
```

**Common Actions errors:**

- Undefined job dependencies in `needs:`
- Invalid conditional expressions in `if:`
- Typos in action names
- Missing required inputs
- Invalid outputs references

### Test Workflow Parsing

```bash
# Verify GitHub can parse the workflow
gh api repos/jdfalk/ghcommon/actions/workflows/release-rust.yml \
  --jq '.state, .path, .name'

# Expected output:
# active
# .github/workflows/release-rust.yml
# Release Rust Binaries and Crates
```

**If workflow not found:**

```bash
# List all workflows
gh api repos/jdfalk/ghcommon/actions/workflows --jq '.workflows[] | .name, .path'

# Find the correct workflow file
ls -la .github/workflows/
```

## Review Changes

### View Complete Diff

```bash
# Show all changes
git diff .github/workflows/release-rust.yml

# Or use a better diff viewer
git diff --color-words .github/workflows/release-rust.yml

# Or use VS Code
code --diff .github/workflows/release-rust.yml.backup-* .github/workflows/release-rust.yml
```

### Count Lines Changed

```bash
# Summary of changes
git diff .github/workflows/release-rust.yml --stat

# Expected output example:
# .github/workflows/release-rust.yml | 250 ++++++++++++++++++++++++++++++
# 1 file changed, 250 insertions(+)
```

### Review Specific Sections

```bash
# Show only the new job
git diff .github/workflows/release-rust.yml | grep -A 200 "publish-rust-crate"

# Show changes to job structure
git diff .github/workflows/release-rust.yml | grep "^[+-]  [a-z]"
```

## Commit Changes

### Stage and Commit

```bash
# Stage the modified workflow
git add .github/workflows/release-rust.yml

# Verify what's staged
git status

# Create detailed commit
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

Registry URL: sparse+https://api.github.com/\$REPO/cargo/
Packages: https://github.com/\$REPO/packages

Prerequisites for repositories using this workflow:
- Cargo.toml must have: name, version, edition, authors, description, license, repository
- Must push version tags (git tag v1.2.3 && git push --tags)
- GITHUB_TOKEN automatically has packages:write permission

Version bump: 1.8.1 → 1.9.0 (new feature, backward compatible)"
```

### Push Changes

```bash
# Push to remote
git push origin main

# Verify push succeeded
git log --oneline -1
```

---

**Part 3 Complete**: Publishing implementation, verification steps, local testing procedures,
workflow validation, and commit process. ✅

**Continue to Part 4** for post-merge verification, testing with actual releases, and monitoring.
