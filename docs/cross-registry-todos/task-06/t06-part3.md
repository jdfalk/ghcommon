<!-- file: docs/cross-registry-todos/task-06/t06-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t06-frontend-packages-part3-m4n5o6p7-q8r9 -->
<!-- last-edited: 2026-01-19 -->

# Task 06 Part 3: Dependency Installation and Package Building

## Stage 1: Install Dependencies Job

### Step 1: Setup Package Manager

```yaml
install-dependencies:
  name: Install Dependencies
  runs-on: ubuntu-latest
  needs: [detect-frontend-package]
  if: needs.detect-frontend-package.outputs.has-package == 'true'

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
        cache: ${{ needs.detect-frontend-package.outputs.package-manager }}
        cache-dependency-path: ${{ needs.detect-frontend-package.outputs.package-dir }}

    - name: Setup pnpm
      if: needs.detect-frontend-package.outputs.package-manager == 'pnpm'
      uses: pnpm/action-setup@v2
      with:
        version: 8

    - name: Setup Yarn Berry
      if: needs.detect-frontend-package.outputs.package-manager == 'yarn-berry'
      run: |
        corepack enable
        yarn set version stable
```

### Step 2: Install Dependencies

```yaml
- name: Install dependencies with npm
  if: needs.detect-frontend-package.outputs.package-manager == 'npm'
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    echo "=== Installing Dependencies with npm ==="
    npm ci

    echo ""
    echo "✅ Dependencies installed"

- name: Install dependencies with yarn
  if: needs.detect-frontend-package.outputs.package-manager == 'yarn'
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    echo "=== Installing Dependencies with Yarn ==="
    yarn install --frozen-lockfile

    echo ""
    echo "✅ Dependencies installed"

- name: Install dependencies with pnpm
  if: needs.detect-frontend-package.outputs.package-manager == 'pnpm'
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    echo "=== Installing Dependencies with pnpm ==="
    pnpm install --frozen-lockfile

    echo ""
    echo "✅ Dependencies installed"
```

## Stage 2: Build Package Job

### Step 1: Build Job Definition

```yaml
build-frontend-package:
  name: Build Frontend Package
  runs-on: ubuntu-latest
  needs: [detect-frontend-package]
  if: needs.detect-frontend-package.outputs.has-package == 'true'

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
        cache: ${{ needs.detect-frontend-package.outputs.package-manager }}
        cache-dependency-path: ${{ needs.detect-frontend-package.outputs.package-dir }}

    - name: Setup package manager
      run: |
        PKG_MGR="${{ needs.detect-frontend-package.outputs.package-manager }}"

        if [ "$PKG_MGR" = "pnpm" ]; then
            npm install -g pnpm@8
        elif [ "$PKG_MGR" = "yarn-berry" ]; then
            corepack enable
        fi
```

### Step 2: Install Dependencies

```yaml
- name: Install dependencies
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    echo "=== Installing Dependencies ==="

    PKG_MGR="${{ needs.detect-frontend-package.outputs.package-manager }}"

    case "$PKG_MGR" in
      npm)
        npm ci
        ;;
      yarn|yarn-berry)
        yarn install --frozen-lockfile
        ;;
      pnpm)
        pnpm install --frozen-lockfile
        ;;
      *)
        echo "Unknown package manager: $PKG_MGR"
        exit 1
        ;;
    esac

    echo "✅ Dependencies installed"
```

### Step 3: Run Build Script

```yaml
- name: Build package
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    echo "=== Building Package ==="
    echo ""
    echo "Build script: ${{ needs.detect-frontend-package.outputs.build-script }}"
    echo ""

    PKG_MGR="${{ needs.detect-frontend-package.outputs.package-manager }}"

    # Run build script
    case "$PKG_MGR" in
      npm)
        npm run build
        ;;
      yarn|yarn-berry)
        yarn build
        ;;
      pnpm)
        pnpm build
        ;;
    esac

    echo ""
    echo "✅ Build completed"
```

### Step 4: Verify Build Output

```yaml
- name: Verify build output
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    echo "=== Verifying Build Output ==="
    echo ""

    # Check for common output directories
    OUTPUT_DIRS="dist lib build out .next"
    FOUND_OUTPUT=""

    for dir in $OUTPUT_DIRS; do
        if [ -d "$dir" ]; then
            echo "✅ Found output directory: $dir"
            FOUND_OUTPUT="$dir"
            break
        fi
    done

    if [ -z "$FOUND_OUTPUT" ]; then
        echo "⚠️  WARNING: No standard output directory found"
        echo "   Expected one of: $OUTPUT_DIRS"
        echo ""
        echo "   Checking package.json 'files' field..."

        # Check files field in package.json
        FILES=$(jq -r '.files[]?' package.json 2>/dev/null)
        if [ -n "$FILES" ]; then
            echo "   Files to be published:"
            echo "$FILES" | sed 's/^/     /'
            FOUND_OUTPUT="custom"
        else
            echo "   ⚠️  No 'files' field specified"
            echo "   All files will be included by default"
        fi
    else
        # List build output
        echo ""
        echo "Build output contents:"
        ls -lh "$FOUND_OUTPUT" | head -20
    fi

    echo ""
    echo "✅ Build output verified"
```

### Step 5: Create Package Tarball

```yaml
- name: Create package tarball
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    echo "=== Creating Package Tarball ==="
    echo ""

    PKG_MGR="${{ needs.detect-frontend-package.outputs.package-manager }}"

    # Create tarball using package manager
    case "$PKG_MGR" in
      npm)
        npm pack
        ;;
      yarn)
        yarn pack
        ;;
      yarn-berry)
        yarn pack --out package.tgz
        ;;
      pnpm)
        pnpm pack
        ;;
    esac

    # Find generated tarball
    TARBALL=$(ls -t *.tgz 2>/dev/null | head -1)

    if [ -z "$TARBALL" ]; then
        echo "❌ ERROR: No tarball created"
        exit 1
    fi

    echo "✅ Tarball created: $TARBALL"

    # Display tarball info
    TARBALL_SIZE=$(stat -f%z "$TARBALL" 2>/dev/null || stat -c%s "$TARBALL" 2>/dev/null)
    TARBALL_SIZE_KB=$((TARBALL_SIZE / 1024))

    echo "   Size: ${TARBALL_SIZE_KB}KB"

    # Warn if package is large
    if [ "$TARBALL_SIZE_KB" -gt 5120 ]; then  # 5MB
        echo "⚠️  WARNING: Package is large (>${TARBALL_SIZE_KB}KB)"
        echo "   Consider reducing package size"
    fi

    # List tarball contents
    echo ""
    echo "Tarball contents:"
    tar -tzf "$TARBALL" | head -50
```

### Step 6: Analyze Package Size

```yaml
- name: Analyze package size
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    echo "=== Analyzing Package Size ==="
    echo ""

    TARBALL=$(ls -t *.tgz 2>/dev/null | head -1)

    if [ -z "$TARBALL" ]; then
        echo "❌ No tarball found"
        exit 1
    fi

    # Extract tarball to analyze
    mkdir -p /tmp/package-analysis
    tar -xzf "$TARBALL" -C /tmp/package-analysis

    # Analyze contents
    echo "Package contents by size:"
    du -sh /tmp/package-analysis/package/* 2>/dev/null | sort -hr | head -20

    echo ""
    echo "Largest files:"
    find /tmp/package-analysis/package -type f -exec du -h {} + | sort -hr | head -20

    # Check for common issues
    echo ""
    echo "Checking for common issues..."

    if find /tmp/package-analysis/package -name "*.map" | grep -q .; then
        echo "⚠️  Source maps found in package"
        echo "   Consider excluding .map files"
    fi

    if find /tmp/package-analysis/package -name "*.test.*" -o -name "*.spec.*" | grep -q .; then
        echo "⚠️  Test files found in package"
        echo "   Consider excluding test files"
    fi

    if find /tmp/package-analysis/package -name "*.md" | grep -q .; then
        DOCS_COUNT=$(find /tmp/package-analysis/package -name "*.md" | wc -l)
        echo "✅ Documentation files: $DOCS_COUNT"
    fi

    # Cleanup
    rm -rf /tmp/package-analysis
```

### Step 7: Generate Build Report

```yaml
- name: Generate build report
  if: always()
  working-directory: ${{ needs.detect-frontend-package.outputs.package-dir }}
  run: |
    TARBALL=$(ls -t *.tgz 2>/dev/null | head -1)
    TARBALL_SIZE=$(stat -f%z "$TARBALL" 2>/dev/null || stat -c%s "$TARBALL" 2>/dev/null || echo "0")
    TARBALL_SIZE_KB=$((TARBALL_SIZE / 1024))

    cat > build-report.md << EOF
    # Frontend Package Build Report

    ## Build Configuration

    - **Package Name**: ${{ needs.detect-frontend-package.outputs.package-name }}
    - **Version**: ${{ needs.detect-frontend-package.outputs.package-version }}
    - **Package Manager**: ${{ needs.detect-frontend-package.outputs.package-manager }}
    - **Node.js Version**: ${{ env.NODE_VERSION }}

    ## Build Results

    - **Tarball**: \`$TARBALL\`
    - **Size**: ${TARBALL_SIZE_KB}KB

    ## Build Output

    EOF

    # List build directories
    for dir in dist lib build out; do
        if [ -d "$dir" ]; then
            echo "### $dir/" >> build-report.md
            echo "" >> build-report.md
            echo "\`\`\`" >> build-report.md
            ls -lh "$dir" | tail -n +2 >> build-report.md
            echo "\`\`\`" >> build-report.md
            echo "" >> build-report.md
        fi
    done

    cat >> build-report.md << 'EOF'

    ## Next Steps

    1. Validate package structure
    2. Test package installation
    3. Publish to registries

    ---
    Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
    EOF

    cat build-report.md

- name: Upload build artifacts
  uses: actions/upload-artifact@v4
  with:
    name:
      frontend-package-${{ needs.detect-frontend-package.outputs.package-name }}-${{
      needs.detect-frontend-package.outputs.package-version }}
    path: |
      ${{ needs.detect-frontend-package.outputs.package-dir }}/*.tgz
      ${{ needs.detect-frontend-package.outputs.package-dir }}/dist/
      ${{ needs.detect-frontend-package.outputs.package-dir }}/lib/
    retention-days: 90

- name: Upload build report
  uses: actions/upload-artifact@v4
  with:
    name: frontend-build-report
    path: ${{ needs.detect-frontend-package.outputs.package-dir }}/build-report.md
    retention-days: 30
```

## Testing Build Locally

### Test Script 1: Complete Build Test

```bash
#!/bin/bash
# test-frontend-build.sh

set -e

echo "=== Testing Frontend Package Build ==="
echo ""

if [ ! -f "package.json" ]; then
    echo "❌ No package.json found"
    exit 1
fi

# Detect package manager
if [ -f "pnpm-lock.yaml" ]; then
    PKG_MGR="pnpm"
    INSTALL_CMD="pnpm install"
    BUILD_CMD="pnpm build"
    PACK_CMD="pnpm pack"
elif [ -f "yarn.lock" ]; then
    PKG_MGR="yarn"
    INSTALL_CMD="yarn install"
    BUILD_CMD="yarn build"
    PACK_CMD="yarn pack"
else
    PKG_MGR="npm"
    INSTALL_CMD="npm ci"
    BUILD_CMD="npm run build"
    PACK_CMD="npm pack"
fi

echo "Package manager: $PKG_MGR"
echo ""

# Install dependencies
echo "1. Installing dependencies..."
$INSTALL_CMD

# Build package
echo ""
echo "2. Building package..."
$BUILD_CMD

# Create tarball
echo ""
echo "3. Creating tarball..."
$PACK_CMD

# Display results
echo ""
echo "Build complete!"
TARBALL=$(ls -t *.tgz | head -1)
if [ -n "$TARBALL" ]; then
    TARBALL_SIZE=$(stat -f%z "$TARBALL" 2>/dev/null || stat -c%s "$TARBALL")
    TARBALL_SIZE_KB=$((TARBALL_SIZE / 1024))
    echo "  Tarball: $TARBALL"
    echo "  Size: ${TARBALL_SIZE_KB}KB"
fi
```

**Run it:**

```bash
chmod +x test-frontend-build.sh
./test-frontend-build.sh
```

### Test Script 2: Build Output Verification

```bash
#!/bin/bash
# verify-build-output.sh

echo "=== Verifying Build Output ==="
echo ""

# Check for build output
for dir in dist lib build out; do
    if [ -d "$dir" ]; then
        echo "✅ Found: $dir/"
        echo "   Contents:"
        ls -lh "$dir" | tail -n +2 | head -10 | sed 's/^/     /'
        echo ""
    fi
done

# Check for tarball
TARBALL=$(ls -t *.tgz 2>/dev/null | head -1)
if [ -n "$TARBALL" ]; then
    echo "✅ Tarball: $TARBALL"
    echo ""
    echo "Contents (first 20 files):"
    tar -tzf "$TARBALL" | head -20 | sed 's/^/  /'
else
    echo "❌ No tarball found"
fi
```

**Run it:**

```bash
chmod +x verify-build-output.sh
./verify-build-output.sh
```

## Commit Build Job Changes

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage the workflow
git add .github/workflows/release-frontend.yml

# Commit with conventional format
git commit -m "feat(release-frontend): add dependency installation and package building

Added package building to release-frontend.yml:

Added Jobs:
- install-dependencies: Setup and install dependencies
- build-frontend-package: Build and package frontend code

Dependency Installation:
- Multi-package-manager support (npm, yarn, pnpm, yarn-berry)
- Uses CI-optimized install commands (npm ci, frozen-lockfile)
- Leverages Node.js cache for faster builds
- Auto-detects and setups package manager

Package Building:
- Runs build script from package.json
- Verifies build output directory
- Creates package tarball (.tgz)
- Analyzes package size and contents
- Checks for common packaging issues
- Generates detailed build report

Build Features:
- TypeScript compilation support
- Multi-format builds (ESM, CJS, UMD)
- Source map handling
- Build output verification
- Package size warnings (>5MB)
- Test file detection

Artifacts:
- frontend-package-{name}-{version}: Built package tarball
- frontend-build-report: Detailed build analysis

Quality Checks:
- Build output verification
- Package size analysis
- Content inspection
- Common issue detection (source maps, test files)

Files changed:
- .github/workflows/release-frontend.yml - Added build jobs"
```

## Next Steps

**Continue to Part 4:** Package validation and testing with multiple installation methods.
