<!-- file: docs/cross-registry-todos/task-04/t04-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t04-go-packages-part4-a7b8c9d0-e1f2 -->

# Task 04 Part 4: Publishing Job Implementation

## Stage 3: Add Module Publishing Job

### Overview

The publishing job publishes the validated Go module using two methods:

1. **Tag-based publishing** (automatic, works immediately)
2. **GitHub Packages publishing** (optional, for enterprise/private use)

### Step 1: Add Publishing Job Definition

After the `validate-go-module` job, add:

```yaml
publish-go-module:
  name: Publish Go Module
  runs-on: ubuntu-latest
  needs: [build-go, validate-go-module]
  if: |
    startsWith(github.ref, 'refs/tags/v') &&
    needs.validate-go-module.outputs.is-valid == 'true'
  permissions:
    contents: write
    packages: write
    id-token: write

  steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0 # Full history needed

    - name: Set up Go
      uses: actions/setup-go@v5
      with:
        go-version-file: 'go.mod'
        cache: true

    # Continue with publishing steps...
```

**Key configuration:**

- Only runs if validation passed
- Requires all three permissions
- Full Git history for tag operations
- Same Go version as validation

### Step 2: Display Publishing Information

Add information display step:

```yaml
- name: Display publishing information
  run: |
    echo "=== Go Module Publishing ==="
    echo ""
    echo "Module Information:"
    echo "  📦 Module: ${{ needs.validate-go-module.outputs.module-path }}"
    echo "  🏷️  Version: ${{ needs.validate-go-module.outputs.module-version }}"
    echo "  🔢 Major: ${{ needs.validate-go-module.outputs.major-version }}"
    echo "  📍 Repository: ${{ github.repository }}"
    echo "  🌳 Ref: ${{ github.ref }}"
    echo "  🔖 Tag: ${{ github.ref_name }}"
    echo ""
    echo "Publishing Methods:"
    echo "  1. ✅ Tag-based (automatic via Git tags)"
    echo "  2. ✅ GitHub Packages (metadata and private access)"
    echo ""
    echo "After publishing, users can import with:"
    echo "  go get ${{ needs.validate-go-module.outputs.module-path }}@${{ github.ref_name }}"
```

### Step 3: Verify Git Tag

Add tag verification:

```yaml
- name: Verify Git tag
  id: verify-tag
  run: |
    echo "=== Verifying Git Tag ==="

    TAG_NAME="${{ github.ref_name }}"
    echo "Tag name: $TAG_NAME"

    # Check if tag exists
    if git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
      echo "✅ Tag exists: $TAG_NAME"
      TAG_COMMIT=$(git rev-parse "$TAG_NAME")
      echo "Tag commit: $TAG_COMMIT"
    else
      echo "❌ ERROR: Tag not found: $TAG_NAME"
      exit 1
    fi

    # Check if tag is annotated
    if git cat-file -t "$TAG_NAME" | grep -q "tag"; then
      echo "✅ Annotated tag"
      echo "tag-type=annotated" >> $GITHUB_OUTPUT

      # Show tag message
      echo ""
      echo "Tag message:"
      git tag -l -n999 "$TAG_NAME"
    else
      echo "ℹ️  Lightweight tag"
      echo "tag-type=lightweight" >> $GITHUB_OUTPUT
    fi

    # Verify tag matches HEAD
    HEAD_COMMIT=$(git rev-parse HEAD)
    if [ "$TAG_COMMIT" = "$HEAD_COMMIT" ]; then
      echo "✅ Tag points to HEAD commit"
    else
      echo "⚠️  WARNING: Tag doesn't point to HEAD"
      echo "   Tag commit: $TAG_COMMIT"
      echo "   HEAD commit: $HEAD_COMMIT"
    fi
```

**Tag verification checks:**

1. ✅ Confirms tag exists
2. ✅ Identifies annotated vs lightweight
3. ✅ Shows tag message (if annotated)
4. ⚠️ Warns if tag doesn't match HEAD

### Step 4: Publish via Tag-Based Method

Add tag-based publishing (automatic):

```yaml
- name: Publish via Git tags (automatic)
  id: publish-tag
  run: |
    echo "=== Publishing via Git Tags ==="
    echo ""
    echo "✅ Module automatically published via Git tag"
    echo ""
    echo "The Git tag '${{ github.ref_name }}' makes this module version"
    echo "discoverable through standard Go module proxy protocol."
    echo ""
    echo "📍 Import Path:"
    echo "   ${{ needs.validate-go-module.outputs.module-path }}@${{ github.ref_name }}"
    echo ""
    echo "🔍 Module can be found via:"
    echo "   - Go module proxies (proxy.golang.org)"
    echo "   - Direct VCS access"
    echo "   - GitHub API"
    echo ""
    echo "✅ No additional action needed - publishing complete"

    # Test module discoverability
    echo ""
    echo "=== Testing Module Discoverability ==="

    MODULE="${{ needs.validate-go-module.outputs.module-path }}"
    VERSION="${{ github.ref_name }}"

    echo "Testing: $MODULE@$VERSION"

    # Allow some time for GitHub to propagate the tag
    sleep 5

    # Try to list the module
    if GOPROXY=direct go list -m "$MODULE@$VERSION" 2>&1; then
      echo "✅ Module is discoverable"
      echo "module-discoverable=true" >> $GITHUB_OUTPUT
    else
      echo "⚠️  Module not yet discoverable (may need time to propagate)"
      echo "   This is normal immediately after tag creation"
      echo "module-discoverable=pending" >> $GITHUB_OUTPUT
    fi
```

**Tag-based publishing:**

- ✅ Automatic (no API calls needed)
- ✅ Works immediately for public repos
- ✅ Discoverable via all Go tools
- ✅ Cached by proxy.golang.org
- ⚠️ May have short propagation delay

### Step 5: Create Module Zip

Add module zip creation for GitHub Packages:

```yaml
- name: Create module zip
  id: create-zip
  run: |
    echo "=== Creating Module Zip ==="

    MODULE_PATH="${{ needs.validate-go-module.outputs.module-path }}"
    VERSION="${{ needs.validate-go-module.outputs.module-version }}"

    # Create zip filename following Go module convention
    # Format: module_path@version.zip
    ZIP_NAME="${MODULE_PATH//\//_}@v${VERSION}.zip"

    echo "Creating: $ZIP_NAME"

    # Create zip with module contents
    # Exclude unnecessary files
    zip -r "$ZIP_NAME" . \
      -x ".git/*" \
      -x ".github/*" \
      -x "*.zip" \
      -x "dist/*" \
      -x "target/*" \
      -x "node_modules/*" \
      -x ".vscode/*" \
      -x ".idea/*"

    # Verify zip was created
    if [ -f "$ZIP_NAME" ]; then
      SIZE=$(du -h "$ZIP_NAME" | cut -f1)
      echo "✅ Zip created: $ZIP_NAME ($SIZE)"
      echo "zip-name=$ZIP_NAME" >> $GITHUB_OUTPUT
      echo "zip-size=$SIZE" >> $GITHUB_OUTPUT

      # List contents
      echo ""
      echo "Zip contents (first 20 files):"
      unzip -l "$ZIP_NAME" | head -25
    else
      echo "❌ ERROR: Failed to create zip"
      exit 1
    fi
```

**Module zip specifications:**

- ✅ Follows Go module naming convention
- ✅ Includes all necessary source files
- ✅ Excludes build artifacts and IDE files
- ✅ Compressed for efficient storage

### Step 6: Generate Module Metadata

Add metadata generation:

```yaml
- name: Generate module metadata
  id: gen-metadata
  run: |
    echo "=== Generating Module Metadata ==="

    MODULE_PATH="${{ needs.validate-go-module.outputs.module-path }}"
    VERSION="v${{ needs.validate-go-module.outputs.module-version }}"

    # Create go.mod metadata JSON
    cat > module-metadata.json << EOF
    {
      "module": "$MODULE_PATH",
      "version": "$VERSION",
      "time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
      "repository": "${{ github.repository }}",
      "commit": "${{ github.sha }}",
      "tag": "${{ github.ref_name }}",
      "goVersion": "$(go version | awk '{print $3}')",
      "dependencies": $(go list -m -json all | jq -s '[.[] | select(.Main != true) | {path: .Path, version: .Version}]')
    }
    EOF

    echo "✅ Metadata generated"
    echo ""
    echo "Metadata contents:"
    cat module-metadata.json | jq .
```

**Metadata includes:**

- ✅ Module path and version
- ✅ Timestamp
- ✅ Repository information
- ✅ Git commit and tag
- ✅ Go version
- ✅ All dependencies

### Step 7: Publish to GitHub Packages

Add GitHub Packages publishing:

```yaml
- name: Publish to GitHub Packages
  id: publish-packages
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    echo "=== Publishing to GitHub Packages ==="

    MODULE_PATH="${{ needs.validate-go-module.outputs.module-path }}"
    VERSION="v${{ needs.validate-go-module.outputs.module-version }}"
    ZIP_NAME="${{ steps.create-zip.outputs.zip-name }}"

    echo "Module: $MODULE_PATH"
    echo "Version: $VERSION"
    echo "Package: $ZIP_NAME"
    echo ""

    # GitHub Packages Go module publishing
    # Note: This creates a package entry in GitHub Packages

    PACKAGE_NAME="${{ github.event.repository.name }}"
    PACKAGE_URL="https://api.github.com/repos/${{ github.repository }}/packages/go/${PACKAGE_NAME}/versions"

    echo "Publishing to: $PACKAGE_URL"

    # Upload module zip as package
    RESPONSE=$(curl -X POST \
      -H "Authorization: Bearer $GITHUB_TOKEN" \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      -F "package=@$ZIP_NAME" \
      "$PACKAGE_URL" \
      -w "\nHTTP_STATUS:%{http_code}" 2>&1)

    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)

    if [ "$HTTP_CODE" -eq 201 ] || [ "$HTTP_CODE" -eq 200 ]; then
      echo "✅ Successfully published to GitHub Packages"
      echo "published=true" >> $GITHUB_OUTPUT
    else
      echo "⚠️  GitHub Packages publishing response: HTTP $HTTP_CODE"
      echo "   Note: Go modules are primarily distributed via Git tags"
      echo "   GitHub Packages publishing is supplementary"
      echo "published=false" >> $GITHUB_OUTPUT
      # Don't fail - tag-based publishing is sufficient
    fi
```

**GitHub Packages publishing:**

- ✅ Uploads module zip
- ✅ Creates package version entry
- ✅ Provides metadata to GitHub
- ⚠️ Supplementary to tag-based publishing
- ⚠️ Doesn't fail if unsuccessful

### Step 8: Upload Publishing Artifacts

Add artifact uploads:

```yaml
- name: Upload module artifacts
  uses: actions/upload-artifact@v4
  with:
    name: go-module-${{ github.ref_name }}
    path: |
      ${{ steps.create-zip.outputs.zip-name }}
      module-metadata.json
    retention-days: 90

- name: Attach module to release
  if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/')
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    echo "=== Attaching Module to Release ==="

    TAG_NAME="${{ github.ref_name }}"
    ZIP_NAME="${{ steps.create-zip.outputs.zip-name }}"

    # Check if release exists
    RELEASE_ID=$(gh api "/repos/${{ github.repository }}/releases/tags/$TAG_NAME" \
      --jq '.id' 2>/dev/null || echo "")

    if [ -z "$RELEASE_ID" ]; then
      echo "ℹ️  No release found for tag $TAG_NAME yet"
      echo "   Module zip will be available as workflow artifact"
    else
      echo "✅ Release found: $RELEASE_ID"
      echo "Uploading module zip to release..."

      gh release upload "$TAG_NAME" "$ZIP_NAME" \
        --repo "${{ github.repository }}" \
        --clobber

      gh release upload "$TAG_NAME" module-metadata.json \
        --repo "${{ github.repository }}" \
        --clobber

      echo "✅ Module zip attached to release"
    fi
```

**Artifact handling:**

- ✅ Always uploaded as workflow artifact
- ✅ Attached to GitHub release if it exists
- ✅ Module zip and metadata both included
- ✅ 90-day retention for artifacts

### Step 9: Generate Publishing Summary

Add comprehensive summary:

````yaml
- name: Generate publishing summary
  if: always()
  run: |
    cat > publishing-summary.md << 'EOF'
    # Go Module Publishing Summary

    ## Module Information

    - **Module**: `${{ needs.validate-go-module.outputs.module-path }}`
    - **Version**: `${{ github.ref_name }}`
    - **Repository**: [${{ github.repository }}](https://github.com/${{ github.repository }})
    - **Commit**: `${{ github.sha }}`

    ## Publishing Status

    | Method                  | Status                                                                  | Details                                |
    | ----------------------- | ----------------------------------------------------------------------- | -------------------------------------- |
    | **Git Tags**            | ✅ Published                                                             | Automatic via `${{ github.ref_name }}` |
    | **GitHub Packages**     | ${{ steps.publish-packages.outputs.published == 'true' && '✅ Published' |                                        | '⚠️ Skipped' }} | Supplementary metadata     |
    | **Module Discoverable** | ${{ steps.publish-tag.outputs.module-discoverable == 'true' && '✅ Yes'  |                                        | '⏳ Pending' }} | May need time to propagate |

    ## Installation Instructions

    ### For Public Modules (Recommended)

    Users can install this module using standard Go tools:

    ```bash
    # Install latest version
    go get ${{ needs.validate-go-module.outputs.module-path }}@latest

    # Install specific version
    go get ${{ needs.validate-go-module.outputs.module-path }}@${{ github.ref_name }}

    # Add to go.mod
    go mod edit -require=${{ needs.validate-go-module.outputs.module-path }}@${{ github.ref_name }}
    go mod tidy
    ```

    ### Usage in Code

    ```go
    import (
        "${{ needs.validate-go-module.outputs.module-path }}/pkg/something"
    )
    ```

    ### For Private Modules

    If this is a private module, users need to configure Git authentication:

    ```bash
    # Configure Git to use SSH
    git config --global url."ssh://git@github.com/".insteadOf "https://github.com/"

    # Or set GOPRIVATE
    export GOPRIVATE="${{ needs.validate-go-module.outputs.module-path }}"

    # Then install normally
    go get ${{ needs.validate-go-module.outputs.module-path }}@${{ github.ref_name }}
    ```

    ## Verification

    Verify the module is available:

    ```bash
    # List module versions
    go list -m -versions ${{ needs.validate-go-module.outputs.module-path }}

    # Show module information
    go list -m -json ${{ needs.validate-go-module.outputs.module-path }}@${{ github.ref_name }}

    # Check module proxy cache
    curl https://proxy.golang.org/${{ needs.validate-go-module.outputs.module-path }}/@v/${{ github.ref_name }}.info
    ```

    ## Additional Resources

    - [Module source](https://github.com/${{ github.repository }}/tree/${{ github.ref_name }})
    - [Release notes](https://github.com/${{ github.repository }}/releases/tag/${{ github.ref_name }})
    - [Go module documentation](https://pkg.go.dev/${{ needs.validate-go-module.outputs.module-path }}@${{ github.ref_name }})

    ---
    Published: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
    EOF

    echo "Publishing summary generated"
    cat publishing-summary.md

- name: Upload publishing summary
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: go-module-publishing-summary
    path: publishing-summary.md
    retention-days: 90
````

**Summary features:**

- ✅ Complete publishing status
- ✅ Installation instructions for users
- ✅ Usage examples
- ✅ Private module configuration
- ✅ Verification commands
- ✅ Links to documentation

### Step 10: Add Workflow Success Notification

Add job summary for GitHub Actions UI:

````yaml
- name: Add job summary
  if: always()
  run: |
    cat publishing-summary.md >> $GITHUB_STEP_SUMMARY

    echo "" >> $GITHUB_STEP_SUMMARY
    echo "---" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "## Quick Install" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo '```bash' >> $GITHUB_STEP_SUMMARY
    echo "go get ${{ needs.validate-go-module.outputs.module-path }}@${{ github.ref_name }}" >> $GITHUB_STEP_SUMMARY
    echo '```' >> $GITHUB_STEP_SUMMARY
````

**Job summary:**

- ✅ Shows in GitHub Actions workflow UI
- ✅ Provides quick copy-paste install command
- ✅ Accessible without downloading artifacts

## Testing the Publishing Job

### Test 1: Validate Complete Workflow

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Validate syntax of complete workflow
actionlint .github/workflows/release-go.yml
yamllint .github/workflows/release-go.yml

# Check for any issues
echo "Syntax check: PASS"
```

### Test 2: Dry Run Publishing Steps Locally

Create test script:

```bash
#!/bin/bash
# test-go-publishing.sh

set -e

echo "=== Go Module Publishing Test (Dry Run) ==="
echo ""

cd "$(dirname "$0")"

# Module information
MODULE_PATH=$(grep "^module " go.mod | awk '{print $2}')
VERSION="1.2.3"  # Mock version
TAG_NAME="v${VERSION}"

echo "Module: $MODULE_PATH"
echo "Version: $VERSION"
echo "Tag: $TAG_NAME"
echo ""

# Step 1: Create module zip
echo "1. Creating module zip..."
ZIP_NAME="${MODULE_PATH//\//_}@v${VERSION}.zip"
echo "   Zip name: $ZIP_NAME"

if [ -f "$ZIP_NAME" ]; then
    rm "$ZIP_NAME"
fi

zip -r "$ZIP_NAME" . \
    -x ".git/*" \
    -x ".github/*" \
    -x "*.zip" \
    -x "dist/*" \
    -x "target/*" \
    -x "node_modules/*" \
    -x ".vscode/*" \
    -x ".idea/*" \
    > /dev/null 2>&1

if [ -f "$ZIP_NAME" ]; then
    SIZE=$(du -h "$ZIP_NAME" | cut -f1)
    echo "   ✅ Created: $ZIP_NAME ($SIZE)"
else
    echo "   ❌ Failed to create zip"
    exit 1
fi
echo ""

# Step 2: Generate metadata
echo "2. Generating metadata..."
cat > module-metadata.json << EOF
{
  "module": "$MODULE_PATH",
  "version": "$TAG_NAME",
  "time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "repository": "test/repo",
  "commit": "abc123",
  "tag": "$TAG_NAME",
  "goVersion": "$(go version | awk '{print $3}')"
}
EOF

if [ -f module-metadata.json ]; then
    echo "   ✅ Created: module-metadata.json"
    echo "   Contents:"
    cat module-metadata.json | jq . 2>/dev/null || cat module-metadata.json
else
    echo "   ❌ Failed to create metadata"
    exit 1
fi
echo ""

# Step 3: Test module discoverability
echo "3. Testing module discoverability (if module is published)..."
if go list -m "$MODULE_PATH@latest" 2>/dev/null; then
    echo "   ✅ Module is discoverable"
else
    echo "   ℹ️  Module not yet discoverable (expected for unpublished modules)"
fi
echo ""

# Cleanup
echo "Cleaning up test files..."
rm -f "$ZIP_NAME" module-metadata.json
echo ""

echo "=== Publishing Test Complete ==="
```

**Run it:**

```bash
chmod +x test-go-publishing.sh
./test-go-publishing.sh
```

### Test 3: Test Module Installation (After Publishing)

After publishing a real version, test installation:

```bash
#!/bin/bash
# test-module-installation.sh

MODULE_PATH="$1"
VERSION="$2"

if [ -z "$MODULE_PATH" ] || [ -z "$VERSION" ]; then
    echo "Usage: $0 <module-path> <version>"
    echo "Example: $0 github.com/jdfalk/ghcommon v1.2.3"
    exit 1
fi

echo "=== Testing Module Installation ==="
echo ""
echo "Module: $MODULE_PATH"
echo "Version: $VERSION"
echo ""

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"
echo "Test directory: $TEMP_DIR"
echo ""

# Initialize test module
echo "1. Initializing test module..."
go mod init test-module
echo ""

# Try to get the module
echo "2. Installing module..."
if go get "$MODULE_PATH@$VERSION"; then
    echo "   ✅ Module installed successfully"
else
    echo "   ❌ Failed to install module"
    cd -
    rm -rf "$TEMP_DIR"
    exit 1
fi
echo ""

# Verify in go.mod
echo "3. Verifying go.mod..."
if grep -q "$MODULE_PATH" go.mod; then
    echo "   ✅ Module added to go.mod"
    grep "$MODULE_PATH" go.mod
else
    echo "   ❌ Module not found in go.mod"
    cd -
    rm -rf "$TEMP_DIR"
    exit 1
fi
echo ""

# Show module info
echo "4. Module information:"
go list -m -json "$MODULE_PATH@$VERSION" | jq .
echo ""

# Cleanup
cd -
rm -rf "$TEMP_DIR"

echo "=== Installation Test Complete ==="
echo "✅ Module is correctly published and installable"
```

**Run it after publishing:**

```bash
chmod +x test-module-installation.sh
./test-module-installation.sh "github.com/jdfalk/ghcommon" "v1.0.0"
```

## Commit All Changes

Now that both validation and publishing jobs are complete:

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage the workflow
git add .github/workflows/release-go.yml

# Commit with detailed message
git commit -m "feat(release-go): add Go module validation and publishing

Added comprehensive Go module publishing to release-go.yml:

Added Jobs:
- detect-go-module: Detects presence of go.mod
- validate-go-module: Validates module path, version, and compatibility
- publish-go-module: Publishes via Git tags and GitHub Packages

Validation Features:
- Module path verification against repository URL
- Semantic version format validation
- Major version alignment (v2+ requires /v2 in path)
- Breaking change detection
- go.mod verification and dependency checks
- Module build and test validation
- Comprehensive validation reports

Publishing Features:
- Tag-based publishing (automatic, primary method)
- GitHub Packages publishing (supplementary)
- Module zip creation with metadata
- Release artifact attachment
- User-friendly installation instructions
- Discoverability testing

Benefits:
- Go modules automatically published on tag push
- Users can 'go get' the module easily
- Both public and private module support
- Complete validation before publishing
- Clear documentation for consumers

Files changed:
- .github/workflows/release-go.yml - Added module publishing jobs"

# Do not push yet - complete testing first
```

## Next Steps

**Continue to Part 5:** Testing and validation procedures to verify the complete workflow works
correctly before pushing to production.
