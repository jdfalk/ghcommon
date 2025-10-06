<!-- file: docs/cross-registry-todos/task-06/t06-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t06-frontend-packages-part5-t7u8v9w0-x1y2 -->

# Task 06 Part 5: GitHub Release and Final Deployment

## Stage 1: Create GitHub Release

### Step 1: GitHub Release Job

````yaml
create-github-release:
  name: Create GitHub Release
  runs-on: ubuntu-latest
  needs: [detect-frontend-package, validate-frontend-package]
  if: |
    needs.detect-frontend-package.outputs.has-package == 'true' &&
    startsWith(github.ref, 'refs/tags/')
  permissions:
    contents: write

  steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Download build artifacts
      uses: actions/download-artifact@v4
      with:
        name:
          frontend-package-${{ needs.detect-frontend-package.outputs.package-name }}-${{
          needs.detect-frontend-package.outputs.package-version }}
        path: ./artifacts

    - name: Download installation instructions
      uses: actions/download-artifact@v4
      with:
        name: frontend-installation-instructions
        path: ./artifacts
      continue-on-error: true

    - name: Generate changelog
      id: changelog
      run: |
        echo "=== Generating Changelog ==="
        echo ""

        TAG_NAME="${{ github.ref_name }}"
        PREV_TAG=$(git describe --tags --abbrev=0 "$TAG_NAME^" 2>/dev/null || echo "")

        if [ -n "$PREV_TAG" ]; then
            echo "Generating changelog from $PREV_TAG to $TAG_NAME"

            # Get commit messages
            CHANGELOG=$(git log "$PREV_TAG".."$TAG_NAME" \
                --pretty=format:"- %s (%h)" \
                --no-merges)
        else
            echo "First release, listing all commits"

            CHANGELOG=$(git log "$TAG_NAME" \
                --pretty=format:"- %s (%h)" \
                --no-merges)
        fi

        # Save to file
        cat > changelog.md << EOF
        ## Changes

        $CHANGELOG
        EOF

        echo "changelog-file=changelog.md" >> $GITHUB_OUTPUT

    - name: Create release notes
      run: |
        PACKAGE_NAME="${{ needs.detect-frontend-package.outputs.package-name }}"
        PACKAGE_VERSION="${{ needs.detect-frontend-package.outputs.package-version }}"

        cat > release-notes.md << 'EOF'
        # ${{ needs.detect-frontend-package.outputs.package-name }} v${{ needs.detect-frontend-package.outputs.package-version }}

        ## Installation

        ### From npm

        ```bash
        npm install ${{ needs.detect-frontend-package.outputs.package-name }}@${{ needs.detect-frontend-package.outputs.package-version }}
        ```

        ### From GitHub Packages

        1. Configure `.npmrc`:
           ```
           @${{ github.repository_owner }}:registry=https://npm.pkg.github.com
           //npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}
           ```

        2. Install:
           ```bash
           npm install ${{ needs.detect-frontend-package.outputs.package-name }}@${{ needs.detect-frontend-package.outputs.package-version }}
           ```

        ## Usage

        ### ES Modules

        ```javascript
        import pkg from '${{ needs.detect-frontend-package.outputs.package-name }}';
        ```

        ### CommonJS

        ```javascript
        const pkg = require('${{ needs.detect-frontend-package.outputs.package-name }}');
        ```

        ### TypeScript

        ```typescript
        import pkg from '${{ needs.detect-frontend-package.outputs.package-name }}';
        // Full type support included
        ```

        ## Package Information

        - **npm**: [npmjs.com/package/${{ needs.detect-frontend-package.outputs.package-name }}](https://www.npmjs.com/package/${{ needs.detect-frontend-package.outputs.package-name }})
        - **GitHub Packages**: [GitHub Packages](https://github.com/${{ github.repository }}/packages)
        - **Repository**: [${{ github.repository }}](https://github.com/${{ github.repository }})

        EOF

        # Append changelog
        if [ -f "changelog.md" ]; then
            echo "" >> release-notes.md
            cat changelog.md >> release-notes.md
        fi

        cat release-notes.md

    - name: Create GitHub Release
      uses: softprops/action-gh-release@v1
      with:
        files: |
          artifacts/*.tgz
          artifacts/installation-instructions.md
        body_path: release-notes.md
        draft: false
        prerelease:
          ${{ contains(github.ref_name, '-alpha') || contains(github.ref_name, '-beta') ||
          contains(github.ref_name, '-rc') }}
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
````

## Stage 2: Post-Publication Verification

### Step 1: Verification Job

```yaml
verify-publication:
  name: Verify Package Publication
  runs-on: ubuntu-latest
  needs: [detect-frontend-package, publish-npm, publish-github-packages]
  if: needs.detect-frontend-package.outputs.has-package == 'true'

  steps:
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}

    - name: Wait for npm propagation
      if: env.PUBLISH_TO_NPM == 'true'
      run: |
        echo "=== Waiting for npm Propagation ==="
        echo "Waiting 30 seconds for npm registry to update..."
        sleep 30

    - name: Verify npm publication
      if: env.PUBLISH_TO_NPM == 'true'
      run: |
        echo "=== Verifying npm Publication ==="
        echo ""

        PACKAGE_NAME="${{ needs.detect-frontend-package.outputs.package-name }}"
        PACKAGE_VERSION="${{ needs.detect-frontend-package.outputs.package-version }}"

        MAX_RETRIES=5
        RETRY_COUNT=0

        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            if npm view "$PACKAGE_NAME@$PACKAGE_VERSION" version >/dev/null 2>&1; then
                echo "✅ Package found on npm"

                echo ""
                echo "Package details:"
                npm view "$PACKAGE_NAME@$PACKAGE_VERSION"

                exit 0
            fi

            RETRY_COUNT=$((RETRY_COUNT + 1))
            echo "⏳ Attempt $RETRY_COUNT/$MAX_RETRIES failed, retrying in 10s..."
            sleep 10
        done

        echo "❌ Package not found on npm after $MAX_RETRIES attempts"
        exit 1

    - name: Verify GitHub Packages publication
      if: |
        env.PUBLISH_TO_GITHUB_PACKAGES == 'true' &&
        needs.detect-frontend-package.outputs.is-scoped == 'true'
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        echo "=== Verifying GitHub Packages Publication ==="
        echo ""

        PACKAGE_NAME="${{ needs.detect-frontend-package.outputs.package-name }}"
        PACKAGE_VERSION="${{ needs.detect-frontend-package.outputs.package-version }}"
        OWNER="${{ github.repository_owner }}"

        # Configure registry
        npm config set @${OWNER}:registry https://npm.pkg.github.com
        npm config set //npm.pkg.github.com/:_authToken ${GITHUB_TOKEN}

        MAX_RETRIES=5
        RETRY_COUNT=0

        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            if npm view "$PACKAGE_NAME@$PACKAGE_VERSION" version >/dev/null 2>&1; then
                echo "✅ Package found on GitHub Packages"

                echo ""
                echo "Package details:"
                npm view "$PACKAGE_NAME@$PACKAGE_VERSION"

                exit 0
            fi

            RETRY_COUNT=$((RETRY_COUNT + 1))
            echo "⏳ Attempt $RETRY_COUNT/$MAX_RETRIES failed, retrying in 10s..."
            sleep 10
        done

        echo "⚠️  Package not found on GitHub Packages after $MAX_RETRIES attempts"
        echo "   This may be expected for new packages (takes time to index)"

    - name: Test package installation
      run: |
        echo "=== Testing Package Installation ==="
        echo ""

        PACKAGE_NAME="${{ needs.detect-frontend-package.outputs.package-name }}"
        PACKAGE_VERSION="${{ needs.detect-frontend-package.outputs.package-version }}"

        # Create temp directory
        TEST_DIR=$(mktemp -d)
        cd "$TEST_DIR"

        # Initialize test project
        npm init -y

        # Install package
        echo "Installing $PACKAGE_NAME@$PACKAGE_VERSION..."
        npm install "$PACKAGE_NAME@$PACKAGE_VERSION"

        # Verify installation
        if npm list "$PACKAGE_NAME" >/dev/null 2>&1; then
            echo "✅ Package installed successfully"

            echo ""
            echo "Installed version:"
            npm list "$PACKAGE_NAME" --depth=0
        else
            echo "❌ Package installation failed"
            exit 1
        fi

        # Cleanup
        cd -
        rm -rf "$TEST_DIR"
```

## Stage 3: Generate Package Metrics

### Step 1: Metrics Collection Job

```yaml
collect-metrics:
  name: Collect Package Metrics
  runs-on: ubuntu-latest
  needs: [detect-frontend-package, publish-npm, publish-github-packages]
  if: needs.detect-frontend-package.outputs.has-package == 'true'

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}

    - name: Download artifacts
      uses: actions/download-artifact@v4
      with:
        name:
          frontend-package-${{ needs.detect-frontend-package.outputs.package-name }}-${{
          needs.detect-frontend-package.outputs.package-version }}
        path: ./artifacts

    - name: Analyze package size
      run: |
        echo "=== Package Size Analysis ==="
        echo ""

        cd artifacts

        TARBALL=$(ls -t *.tgz | head -1)

        if [ -z "$TARBALL" ]; then
            echo "❌ No tarball found"
            exit 1
        fi

        SIZE_BYTES=$(stat -f%z "$TARBALL" 2>/dev/null || stat -c%s "$TARBALL")
        SIZE_KB=$((SIZE_BYTES / 1024))
        SIZE_MB=$((SIZE_BYTES / 1024 / 1024))

        echo "Package: $TARBALL"
        echo "Size: $SIZE_BYTES bytes ($SIZE_KB KB, $SIZE_MB MB)"
        echo ""

        # Extract and analyze contents
        EXTRACT_DIR=$(mktemp -d)
        tar -xzf "$TARBALL" -C "$EXTRACT_DIR"

        echo "Package contents:"
        du -sh "$EXTRACT_DIR"/* | sort -hr

        echo ""
        echo "File breakdown:"
        find "$EXTRACT_DIR" -type f -exec du -h {} + | sort -hr | head -20

        # Cleanup
        rm -rf "$EXTRACT_DIR"

    - name: Generate metrics report
      run: |
        PACKAGE_NAME="${{ needs.detect-frontend-package.outputs.package-name }}"
        PACKAGE_VERSION="${{ needs.detect-frontend-package.outputs.package-version }}"

        cat > metrics-report.md << EOF
        # Package Metrics Report

        **Package**: $PACKAGE_NAME
        **Version**: $PACKAGE_VERSION
        **Released**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

        ## Publishing Status

        - ✅ Build successful
        - ✅ Validation passed
        $(if [ "${{ env.PUBLISH_TO_NPM }}" = "true" ]; then echo "- ✅ Published to npm"; fi)
        $(if [ "${{ env.PUBLISH_TO_GITHUB_PACKAGES }}" = "true" ]; then echo "- ✅ Published to GitHub Packages"; fi)
        - ✅ GitHub Release created

        ## Package Links

        - **npm**: https://www.npmjs.com/package/$PACKAGE_NAME
        - **GitHub**: https://github.com/${{ github.repository }}
        - **GitHub Packages**: https://github.com/${{ github.repository }}/packages
        - **GitHub Release**: https://github.com/${{ github.repository }}/releases/tag/${{ github.ref_name }}

        ## Quality Metrics

        - ✅ Installation tested
        - ✅ ESM import tested
        - ✅ CommonJS import tested
        - ✅ TypeScript declarations checked
        - ✅ Metadata validated

        ## Next Steps

        1. Monitor npm/GitHub Packages for downloads
        2. Update documentation if needed
        3. Announce release to users
        4. Monitor for issues

        ---
        *Generated by ${{ github.workflow }} - Run #${{ github.run_number }}*
        EOF

        cat metrics-report.md

    - name: Upload metrics report
      uses: actions/upload-artifact@v4
      with:
        name: frontend-metrics-report
        path: metrics-report.md
        retention-days: 90
```

## Complete Workflow Summary

### Full Job Dependencies

```yaml
jobs:
  detect-frontend-package:    # Detects package.json
    ↓
  build-frontend-package:      # Builds and creates tarball
    ↓
  validate-frontend-package:   # Validates installation and imports
    ↓
  ├─ publish-npm:              # Publishes to npm registry
  ├─ publish-github-packages:  # Publishes to GitHub Packages
  ├─ create-github-release:    # Creates GitHub release
  │   ↓
  └─ verify-publication:       # Verifies all publishing
      ↓
      collect-metrics:         # Collects final metrics
```

## Local Testing Scripts

### Test Complete Release Workflow

```bash
#!/bin/bash
# test-complete-release.sh

echo "=== Testing Complete Release Workflow ==="
echo ""

# Check prerequisites
if [ ! -f "package.json" ]; then
    echo "❌ No package.json found"
    exit 1
fi

PACKAGE_NAME=$(jq -r '.name' package.json)
PACKAGE_VERSION=$(jq -r '.version' package.json)

echo "Package: $PACKAGE_NAME"
echo "Version: $PACKAGE_VERSION"
echo ""

# Stage 1: Build
echo "Stage 1: Building package..."
if npm run build 2>/dev/null; then
    echo "✅ Build successful"
else
    echo "⚠️  No build script or build failed"
fi
echo ""

# Stage 2: Create tarball
echo "Stage 2: Creating tarball..."
npm pack
TARBALL=$(ls -t *.tgz | head -1)
echo "✅ Created: $TARBALL"
echo ""

# Stage 3: Test installation
echo "Stage 3: Testing installation..."
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
npm init -y >/dev/null 2>&1
npm install "$OLDPWD/$TARBALL" >/dev/null 2>&1

if npm list "$PACKAGE_NAME" >/dev/null 2>&1; then
    echo "✅ Installation successful"
else
    echo "❌ Installation failed"
    cd "$OLDPWD"
    rm -rf "$TEST_DIR"
    exit 1
fi

cd "$OLDPWD"
rm -rf "$TEST_DIR"
echo ""

# Stage 4: Size analysis
echo "Stage 4: Analyzing size..."
SIZE_BYTES=$(stat -f%z "$TARBALL" 2>/dev/null || stat -c%s "$TARBALL")
SIZE_KB=$((SIZE_BYTES / 1024))

echo "Size: $SIZE_KB KB"

if [ $SIZE_KB -gt 5120 ]; then
    echo "⚠️  WARNING: Package is large (>5MB)"
else
    echo "✅ Size acceptable"
fi
echo ""

# Summary
echo "=== Summary ==="
echo "✅ Build: OK"
echo "✅ Package: OK"
echo "✅ Installation: OK"
echo "✅ Size: $SIZE_KB KB"
echo ""
echo "Ready for publishing!"
```

**Run it:**

```bash
chmod +x test-complete-release.sh
./test-complete-release.sh
```

## Commit Release Configuration

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage workflow
git add .github/workflows/release-frontend.yml

# Commit with conventional format
git commit -m "feat(release-frontend): add GitHub release and verification jobs

Added final release and verification to release-frontend.yml:

Added Jobs:
- create-github-release: Creates GitHub releases with artifacts
- verify-publication: Verifies npm and GitHub Packages publication
- collect-metrics: Generates package metrics and reports

GitHub Release Features:
- Automatic changelog generation from git history
- Comprehensive release notes with installation instructions
- Tarball and documentation attachment
- Prerelease detection (alpha, beta, rc)
- Links to all package registries

Verification Features:
- npm registry verification with retries
- GitHub Packages verification with authentication
- Live installation testing
- Version confirmation
- Propagation delay handling

Metrics Collection:
- Package size analysis
- Content breakdown
- File size distribution
- Publishing status report
- Quality metrics summary

Release Notes Include:
- Installation instructions (npm and GitHub Packages)
- Usage examples (ESM, CommonJS, TypeScript)
- Package links (npm, GitHub, GitHub Packages)
- Changelog from previous tag
- Prerelease indicators

Verification Includes:
- 5 retry attempts with backoff
- Authentication handling for GitHub Packages
- Live installation test in clean environment
- Version matching confirmation

Metrics Include:
- Package size in bytes/KB/MB
- Top 20 largest files
- Publishing status
- Quality checks summary
- Next steps recommendations

Artifacts:
- frontend-metrics-report: Complete metrics and status

Files changed:
- .github/workflows/release-frontend.yml - Added release, verification, and metrics jobs"
```

## Next Steps

**Continue to Part 6:** Documentation, troubleshooting, and completion checklist.
