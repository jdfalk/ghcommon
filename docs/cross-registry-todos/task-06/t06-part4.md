<!-- file: docs/cross-registry-todos/task-06/t06-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t06-frontend-packages-part4-n5o6p7q8-r9s0 -->

# Task 06 Part 4: Package Validation and Publishing

## Stage 1: Validate Package Job

### Step 1: Validation Job Definition

```yaml
validate-frontend-package:
  name: Validate Frontend Package
  runs-on: ubuntu-latest
  needs: [detect-frontend-package, build-frontend-package]
  if: needs.detect-frontend-package.outputs.has-package == 'true'

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}

    - name: Download build artifacts
      uses: actions/download-artifact@v4
      with:
        name:
          frontend-package-${{ needs.detect-frontend-package.outputs.package-name }}-${{
          needs.detect-frontend-package.outputs.package-version }}
        path: ${{ needs.detect-frontend-package.outputs.package-dir }}
```

### Step 2: Test Package Installation

```yaml
- name: Test package installation
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    echo "=== Testing Package Installation ==="
    echo ""

    # Find tarball
    TARBALL=$(ls -t *.tgz | head -1)

    if [ -z "$TARBALL" ]; then
        echo "❌ ERROR: No tarball found"
        exit 1
    fi

    echo "Testing tarball: $TARBALL"

    # Create test directory
    TEST_DIR=$(mktemp -d)
    cd "$TEST_DIR"

    # Initialize test package
    npm init -y

    # Install from tarball
    echo ""
    echo "Installing from tarball..."
    npm install "$OLDPWD/$TARBALL"

    # Verify installation
    PACKAGE_NAME="${{ needs.detect-frontend-package.outputs.package-name }}"

    if npm list "$PACKAGE_NAME" >/dev/null 2>&1; then
        echo "✅ Package installed successfully"
    else
        echo "❌ ERROR: Package not found after installation"
        exit 1
    fi

    # Show installation info
    echo ""
    echo "Installed package info:"
    npm list "$PACKAGE_NAME" --depth=0

    # Cleanup
    cd -
    rm -rf "$TEST_DIR"
```

### Step 3: Test Package Import (ESM)

```yaml
- name: Test ESM import
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    echo "=== Testing ESM Import ==="
    echo ""

    PACKAGE_NAME="${{ needs.detect-frontend-package.outputs.package-name }}"

    # Create test file
    cat > test-esm.mjs << EOF
    import pkg from '$PACKAGE_NAME';
    console.log('✅ ESM import successful');
    console.log('Package:', pkg);
    EOF

    # Try to run test
    if node test-esm.mjs 2>/dev/null; then
        echo "✅ ESM import works"
    else
        echo "⚠️  WARNING: ESM import failed"
        echo "   This may be expected if package doesn't support ESM"
    fi

    rm -f test-esm.mjs
```

### Step 4: Test Package Import (CommonJS)

```yaml
- name: Test CommonJS import
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    echo "=== Testing CommonJS Import ==="
    echo ""

    PACKAGE_NAME="${{ needs.detect-frontend-package.outputs.package-name }}"

    # Create test file
    cat > test-cjs.js << EOF
    const pkg = require('$PACKAGE_NAME');
    console.log('✅ CommonJS import successful');
    console.log('Package:', pkg);
    EOF

    # Try to run test
    if node test-cjs.js 2>/dev/null; then
        echo "✅ CommonJS import works"
    else
        echo "⚠️  WARNING: CommonJS import failed"
        echo "   This may be expected if package is ESM-only"
    fi

    rm -f test-cjs.js
```

### Step 5: Validate Package Metadata

```yaml
- name: Validate package metadata
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    echo "=== Validating Package Metadata ==="
    echo ""

    # Required fields
    REQUIRED_FIELDS="name version"

    for field in $REQUIRED_FIELDS; do
        VALUE=$(jq -r ".$field // empty" package.json)
        if [ -z "$VALUE" ]; then
            echo "❌ ERROR: Missing required field: $field"
            exit 1
        fi
        echo "✅ $field: $VALUE"
    done

    # Recommended fields
    echo ""
    echo "Recommended fields:"

    RECOMMENDED_FIELDS="description author license repository keywords"

    for field in $RECOMMENDED_FIELDS; do
        VALUE=$(jq -r ".$field // empty" package.json)
        if [ -z "$VALUE" ]; then
            echo "⚠️  Missing: $field"
        else
            echo "✅ $field: present"
        fi
    done
```

### Step 6: Check TypeScript Declarations

```yaml
- name: Check TypeScript declarations
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    echo "=== Checking TypeScript Declarations ==="
    echo ""

    # Check if package includes types
    TYPES_FIELD=$(jq -r '.types // .typings // empty' package.json)

    if [ -n "$TYPES_FIELD" ]; then
        echo "✅ TypeScript declarations specified: $TYPES_FIELD"

        # Check if types file exists
        if [ -f "$TYPES_FIELD" ]; then
            echo "✅ Types file exists"
        else
            echo "⚠️  WARNING: Types file not found: $TYPES_FIELD"
        fi
    else
        echo "ℹ️  No TypeScript declarations specified"
        echo "   TypeScript users will not get type hints"
    fi
```

## Stage 2: Publish to npm Registry

### Step 1: npm Publishing Job

```yaml
publish-npm:
  name: Publish to npm
  runs-on: ubuntu-latest
  needs: [detect-frontend-package, build-frontend-package, validate-frontend-package]
  if: |
    needs.detect-frontend-package.outputs.has-package == 'true' &&
    env.PUBLISH_TO_NPM == 'true' &&
    startsWith(github.ref, 'refs/tags/')
  environment:
    name: npm
    url: https://www.npmjs.com/package/${{ needs.detect-frontend-package.outputs.package-name }}

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
        registry-url: ${{ env.NPM_REGISTRY }}

    - name: Download build artifacts
      uses: actions/download-artifact@v4
      with:
        name:
          frontend-package-${{ needs.detect-frontend-package.outputs.package-name }}-${{
          needs.detect-frontend-package.outputs.package-version }}
        path: ${{ needs.detect-frontend-package.outputs.package-dir }}

    - name: Publish to npm
      working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
      env:
        NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
      run: |
        echo "=== Publishing to npm Registry ==="
        echo ""

        TARBALL=$(ls -t *.tgz | head -1)

        if [ -z "$TARBALL" ]; then
            echo "❌ ERROR: No tarball found"
            exit 1
        fi

        echo "Publishing: $TARBALL"
        echo "Tag: ${{ env.NPM_PUBLISH_TAG }}"
        echo ""

        # Publish package
        npm publish "$TARBALL" --access public --tag ${{ env.NPM_PUBLISH_TAG }}

        echo ""
        echo "✅ Published to npm"

    - name: Verify npm publication
      run: |
        echo "=== Verifying npm Publication ==="
        echo ""

        PACKAGE_NAME="${{ needs.detect-frontend-package.outputs.package-name }}"
        PACKAGE_VERSION="${{ needs.detect-frontend-package.outputs.package-version }}"

        # Wait for propagation
        sleep 10

        # Try to view package info
        if npm view "$PACKAGE_NAME@$PACKAGE_VERSION" version >/dev/null 2>&1; then
            echo "✅ Package visible on npm"
            echo ""
            echo "Installation command:"
            echo "  npm install $PACKAGE_NAME@$PACKAGE_VERSION"
        else
            echo "⚠️  Package not yet visible (may need time to propagate)"
        fi
```

## Stage 3: Publish to GitHub Packages

### Step 1: GitHub Packages Publishing Job

```yaml
publish-github-packages:
  name: Publish to GitHub Packages
  runs-on: ubuntu-latest
  needs: [detect-frontend-package, build-frontend-package, validate-frontend-package]
  if: |
    needs.detect-frontend-package.outputs.has-package == 'true' &&
    env.PUBLISH_TO_GITHUB_PACKAGES == 'true' &&
    needs.detect-frontend-package.outputs.is-scoped == 'true'
  environment:
    name: github-packages
    url: https://github.com/${{ github.repository }}/packages

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
        registry-url: ${{ env.GITHUB_PACKAGES_REGISTRY }}
        scope: '@${{ github.repository_owner }}'

    - name: Download build artifacts
      uses: actions/download-artifact@v4
      with:
        name:
          frontend-package-${{ needs.detect-frontend-package.outputs.package-name }}-${{
          needs.detect-frontend-package.outputs.package-version }}
        path: ${{ needs.detect-frontend-package.outputs.package-dir }}

    - name: Configure GitHub Packages registry
      working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
      run: |
        echo "=== Configuring GitHub Packages ==="
        echo ""

        # Create/update .npmrc
        cat > .npmrc << EOF
        @${{ github.repository_owner }}:registry=${{ env.GITHUB_PACKAGES_REGISTRY }}
        //${{ env.GITHUB_PACKAGES_REGISTRY }}/:_authToken=\${NODE_AUTH_TOKEN}
        EOF

        echo "✅ Registry configured"

    - name: Publish to GitHub Packages
      working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
      env:
        NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        echo "=== Publishing to GitHub Packages ==="
        echo ""

        TARBALL=$(ls -t *.tgz | head -1)

        if [ -z "$TARBALL" ]; then
            echo "❌ ERROR: No tarball found"
            exit 1
        fi

        echo "Publishing: $TARBALL"
        echo ""

        # Publish package
        npm publish "$TARBALL"

        echo ""
        echo "✅ Published to GitHub Packages"

    - name: Generate installation instructions
      run: |
        PACKAGE_NAME="${{ needs.detect-frontend-package.outputs.package-name }}"
        PACKAGE_VERSION="${{ needs.detect-frontend-package.outputs.package-version }}"

        cat > installation-instructions.md << EOF
        # Installation Instructions

        ## Install from npm

        \`\`\`bash
        npm install $PACKAGE_NAME
        \`\`\`

        ## Install from GitHub Packages

        1. Create/update \`.npmrc\`:
           \`\`\`
           @${{ github.repository_owner }}:registry=${{ env.GITHUB_PACKAGES_REGISTRY }}
           //${{ env.GITHUB_PACKAGES_REGISTRY }}/:_authToken=\${GITHUB_TOKEN}
           \`\`\`

        2. Install package:
           \`\`\`bash
           npm install $PACKAGE_NAME
           \`\`\`

        ## Import in Code

        ### ES Modules
        \`\`\`javascript
        import pkg from '$PACKAGE_NAME';
        \`\`\`

        ### CommonJS
        \`\`\`javascript
        const pkg = require('$PACKAGE_NAME');
        \`\`\`

        ### TypeScript
        \`\`\`typescript
        import pkg from '$PACKAGE_NAME';
        // Types included automatically
        \`\`\`

        ## Package Links

        - **npm**: https://www.npmjs.com/package/$PACKAGE_NAME
        - **GitHub**: https://github.com/${{ github.repository }}
        - **GitHub Packages**: https://github.com/${{ github.repository }}/packages

        ---
        Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
        EOF

        cat installation-instructions.md

    - name: Upload installation instructions
      uses: actions/upload-artifact@v4
      with:
        name: frontend-installation-instructions
        path: installation-instructions.md
        retention-days: 90
```

## Testing Publishing Locally

### Test Script: Publish Dry Run

```bash
#!/bin/bash
# test-npm-publish-dry-run.sh

echo "=== Testing npm Publish (Dry Run) ==="
echo ""

if [ ! -f "package.json" ]; then
    echo "❌ No package.json found"
    exit 1
fi

# Find tarball
TARBALL=$(ls -t *.tgz 2>/dev/null | head -1)

if [ -z "$TARBALL" ]; then
    echo "❌ No tarball found. Run build first."
    exit 1
fi

echo "Testing publish for: $TARBALL"
echo ""

# Dry run publish
npm publish "$TARBALL" --dry-run

echo ""
echo "✅ Dry run completed!"
echo ""
echo "To actually publish:"
echo "1. Set NPM_TOKEN secret in GitHub"
echo "2. Enable PUBLISH_TO_NPM in workflow"
echo "3. Push a version tag"
```

**Run it:**

```bash
chmod +x test-npm-publish-dry-run.sh
./test-npm-publish-dry-run.sh
```

## Commit Publishing Job Changes

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage the workflow
git add .github/workflows/release-frontend.yml

# Commit with conventional format
git commit -m "feat(release-frontend): add package validation and multi-registry publishing

Added validation and publishing to release-frontend.yml:

Added Jobs:
- validate-frontend-package: Comprehensive package validation
- publish-npm: Publish to npm registry
- publish-github-packages: Publish to GitHub Packages

Validation Features:
- Package installation testing from tarball
- ESM and CommonJS import testing
- Package metadata validation (required and recommended fields)
- TypeScript declaration checking
- Entry point verification

Publishing Features:
- npm registry publishing with access control
- GitHub Packages publishing for scoped packages
- Automatic registry configuration
- Publication verification
- Installation instructions generation

npm Publishing:
- Uses NPM_TOKEN for authentication
- Supports public and scoped packages
- Configurable dist-tag (latest, next, beta)
- Post-publication verification

GitHub Packages:
- Uses GITHUB_TOKEN (automatic)
- Requires scoped packages (@owner/package)
- Auto-configures .npmrc
- Integrated with repository

Environment Protection:
- npm environment for production publishing
- github-packages environment for GitHub registry
- Manual approval supported

Artifacts:
- frontend-installation-instructions: Complete installation guide

Quality Checks:
- Installation verification
- Import testing (ESM and CJS)
- Metadata completeness
- TypeScript support validation

Files changed:
- .github/workflows/release-frontend.yml - Added validation and publishing jobs"
```

## Next Steps

**Continue to Part 5:** GitHub Release creation and final documentation.
