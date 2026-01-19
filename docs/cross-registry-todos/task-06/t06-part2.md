<!-- file: docs/cross-registry-todos/task-06/t06-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t06-frontend-packages-part2-k2l3m4n5-o6p7 -->
<!-- last-edited: 2026-01-19 -->

# Task 06 Part 2: Workflow Header and Package Detection

## Stage 1: Create/Update Workflow File

### Step 1: Create Workflow File

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Create workflow file if it doesn't exist
touch .github/workflows/release-frontend.yml

# Open in editor
code .github/workflows/release-frontend.yml
```

### Step 2: Add Workflow Header

```yaml
# file: .github/workflows/release-frontend.yml
# version: 1.0.0
# guid: release-frontend-workflow-l3m4n5o6-p7q8
#
# Frontend Package Publishing Workflow
#
# This workflow automatically publishes frontend (npm) packages to:
# - npm Registry (production)
# - GitHub Packages (npm)
# - GitHub Releases
#
# Supports:
# - TypeScript and JavaScript packages
# - Multiple package managers (npm, yarn, pnpm)
# - ESM and CommonJS builds
# - Scoped and unscoped packages
# - Multi-framework support (React, Vue, Angular, Svelte, vanilla JS)

name: Release - Frontend
```

### Step 3: Configure Permissions

```yaml
permissions:
  contents: write # For creating releases and tags
  packages: write # For publishing to GitHub Packages
  id-token: write # For provenance (npm)
  pull-requests: read # For checking PR context
```

### Step 4: Add Environment Variables

```yaml
env:
  # Node.js configuration
  NODE_VERSION: '20' # LTS version
  NODE_MIN_VERSION: '18'

  # Package registry configuration
  NPM_REGISTRY: 'https://registry.npmjs.org/'
  GITHUB_PACKAGES_REGISTRY: 'https://npm.pkg.github.com/'

  # Publishing configuration
  PUBLISH_TO_NPM: 'false' # Set true when NPM_TOKEN configured
  PUBLISH_TO_GITHUB_PACKAGES: 'true' # Default enabled
  NPM_PUBLISH_TAG: 'latest' # npm dist-tag

  # Build configuration
  NPM_CONFIG_LOGLEVEL: 'info'
  NODE_ENV: 'production'
```

### Step 5: Configure Workflow Triggers

```yaml
on:
  push:
    tags:
      - 'v*.*.*' # Semantic version tags
      - 'frontend-v*' # Frontend-specific tags
  workflow_dispatch:
    inputs:
      tag:
        description: 'Release tag (e.g., v1.2.3)'
        required: true
        type: string
      publish_to_npm:
        description: 'Publish to npm registry'
        required: false
        type: boolean
        default: false
      npm_tag:
        description: 'npm dist-tag (latest, next, beta)'
        required: false
        type: string
        default: 'latest'
```

## Stage 2: Add Package Detection Job

### Step 1: Detection Job Definition

```yaml
jobs:
  detect-frontend-package:
    name: Detect Frontend Package
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v') || startsWith(github.ref, 'refs/tags/frontend-v')
    outputs:
      has-package: ${{ steps.detect.outputs.has-package }}
      package-name: ${{ steps.detect.outputs.package-name }}
      package-version: ${{ steps.detect.outputs.package-version }}
      package-manager: ${{ steps.detect.outputs.package-manager }}
      package-dir: ${{ steps.detect.outputs.package-dir }}
      is-scoped: ${{ steps.detect.outputs.is-scoped }}
      build-script: ${{ steps.detect.outputs.build-script }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
```

### Step 2: Detect Package.json Files

```yaml
- name: Find package.json files
  id: find-packages
  run: |
    echo "=== Finding Frontend Package Configurations ==="
    echo ""

    # Find all package.json files (exclude node_modules)
    PACKAGE_FILES=$(find . -name "package.json" \
      -not -path "*/node_modules/*" \
      -not -path "*/dist/*" \
      -not -path "*/build/*" \
      -not -path "*/.next/*" \
      -type f)

    if [ -z "$PACKAGE_FILES" ]; then
        echo "⚠️  No package.json files found"
        echo "has-packages=false" >> $GITHUB_OUTPUT
        exit 0
    fi

    echo "Found package.json files:"
    echo "$PACKAGE_FILES" | sed 's/^/  /'
    echo ""

    # Filter out private packages and workspace roots
    PUBLISHABLE_PACKAGES=""

    for PKG_FILE in $PACKAGE_FILES; do
        PKG_DIR=$(dirname "$PKG_FILE")

        # Check if package is marked private
        IS_PRIVATE=$(jq -r '.private // false' "$PKG_FILE")
        if [ "$IS_PRIVATE" = "true" ]; then
            echo "⏭️  Skipping private package: $PKG_DIR"
            continue
        fi

        # Check if package has a name
        PKG_NAME=$(jq -r '.name // empty' "$PKG_FILE")
        if [ -z "$PKG_NAME" ]; then
            echo "⏭️  Skipping package without name: $PKG_DIR"
            continue
        fi

        # Check if package has a version
        PKG_VERSION=$(jq -r '.version // empty' "$PKG_FILE")
        if [ -z "$PKG_VERSION" ]; then
            echo "⏭️  Skipping package without version: $PKG_DIR"
            continue
        fi

        # Check if package is a workspace root (has workspaces field)
        HAS_WORKSPACES=$(jq -r '.workspaces // empty' "$PKG_FILE")
        if [ -n "$HAS_WORKSPACES" ]; then
            echo "⏭️  Skipping workspace root: $PKG_DIR"
            continue
        fi

        echo "✅ Publishable package found: $PKG_NAME ($PKG_DIR)"
        PUBLISHABLE_PACKAGES="$PUBLISHABLE_PACKAGES$PKG_FILE "
    done

    if [ -z "$PUBLISHABLE_PACKAGES" ]; then
        echo ""
        echo "⚠️  No publishable packages found"
        echo "has-packages=false" >> $GITHUB_OUTPUT
        exit 0
    fi

    # Use first publishable package found
    SELECTED_PACKAGE=$(echo "$PUBLISHABLE_PACKAGES" | awk '{print $1}')
    echo ""
    echo "📦 Selected package: $SELECTED_PACKAGE"
    echo "selected-package=$SELECTED_PACKAGE" >> $GITHUB_OUTPUT
    echo "has-packages=true" >> $GITHUB_OUTPUT
```

### Step 3: Detect Package Manager

```yaml
- name: Detect package manager
  id: detect-pm
  if: steps.find-packages.outputs.has-packages == 'true'
  run: |
    echo "=== Detecting Package Manager ==="
    echo ""

    PKG_FILE="${{ steps.find-packages.outputs.selected-package }}"
    PKG_DIR=$(dirname "$PKG_FILE")

    cd "$PKG_DIR"

    PACKAGE_MANAGER="npm"  # Default

    # Check for lock files
    if [ -f "pnpm-lock.yaml" ]; then
        PACKAGE_MANAGER="pnpm"
        echo "📦 Detected: pnpm (pnpm-lock.yaml found)"

    elif [ -f "yarn.lock" ]; then
        # Distinguish between Yarn 1.x and Yarn 2+
        if [ -f ".yarnrc.yml" ]; then
            PACKAGE_MANAGER="yarn-berry"
            echo "📦 Detected: Yarn Berry (yarn.lock + .yarnrc.yml found)"
        else
            PACKAGE_MANAGER="yarn"
            echo "📦 Detected: Yarn Classic (yarn.lock found)"
        fi

    elif [ -f "package-lock.json" ]; then
        PACKAGE_MANAGER="npm"
        echo "📦 Detected: npm (package-lock.json found)"

    else
        echo "⚠️  No lock file found, using npm as default"
        PACKAGE_MANAGER="npm"
    fi

    echo "package-manager=$PACKAGE_MANAGER" >> $GITHUB_OUTPUT
```

### Step 4: Extract Package Metadata

```yaml
- name: Extract package metadata
  id: detect
  if: steps.find-packages.outputs.has-packages == 'true'
  run: |
    echo "=== Extracting Package Metadata ==="
    echo ""

    PKG_FILE="${{ steps.find-packages.outputs.selected-package }}"
    PKG_DIR=$(dirname "$PKG_FILE")

    cd "$PKG_DIR"

    # Extract metadata using jq
    PACKAGE_NAME=$(jq -r '.name' package.json)
    PACKAGE_VERSION=$(jq -r '.version' package.json)
    PACKAGE_DESCRIPTION=$(jq -r '.description // ""' package.json)

    echo "Package Information:"
    echo "  Name: $PACKAGE_NAME"
    echo "  Version: $PACKAGE_VERSION"
    echo "  Description: $PACKAGE_DESCRIPTION"
    echo "  Directory: $PKG_DIR"
    echo ""

    # Check if package is scoped
    IS_SCOPED="false"
    if [[ "$PACKAGE_NAME" == @*/* ]]; then
        IS_SCOPED="true"
        SCOPE=$(echo "$PACKAGE_NAME" | cut -d'/' -f1)
        PACKAGE_BASE=$(echo "$PACKAGE_NAME" | cut -d'/' -f2)
        echo "✅ Scoped package: $SCOPE/$PACKAGE_BASE"
    else
        echo "⚠️  Unscoped package: $PACKAGE_NAME"
        echo "   GitHub Packages requires scoped packages"
    fi

    # Check build script
    BUILD_SCRIPT=$(jq -r '.scripts.build // empty' package.json)
    if [ -z "$BUILD_SCRIPT" ]; then
        echo "⚠️  WARNING: No build script defined"
        echo "   Package may need manual build configuration"
        BUILD_SCRIPT="echo 'No build script defined'"
    else
        echo "✅ Build script: $BUILD_SCRIPT"
    fi

    # Check entry points
    echo ""
    echo "Entry Points:"
    jq -r '.main // "Not specified"' package.json | sed 's/^/  main: /'
    jq -r '.module // "Not specified"' package.json | sed 's/^/  module: /'
    jq -r '.types // "Not specified"' package.json | sed 's/^/  types: /'
    jq -r '.exports // "Not specified"' package.json | sed 's/^/  exports: /'

    # Output values
    echo "has-package=true" >> $GITHUB_OUTPUT
    echo "package-name=$PACKAGE_NAME" >> $GITHUB_OUTPUT
    echo "package-version=$PACKAGE_VERSION" >> $GITHUB_OUTPUT
    echo "package-manager=${{ steps.detect-pm.outputs.package-manager }}" >> $GITHUB_OUTPUT
    echo "package-dir=$PKG_DIR" >> $GITHUB_OUTPUT
    echo "is-scoped=$IS_SCOPED" >> $GITHUB_OUTPUT
    echo "build-script=$BUILD_SCRIPT" >> $GITHUB_OUTPUT
```

### Step 5: Validate Package Name

```yaml
- name: Validate package name
  if: steps.detect.outputs.has-package == 'true'
  run: |
    echo "=== Validating Package Name ==="

    PACKAGE_NAME="${{ steps.detect.outputs.package-name }}"

    # npm package name rules:
    # - All lowercase
    # - No leading dots or underscores
    # - No uppercase letters
    # - Can contain hyphens and underscores
    # - Can be scoped (@scope/name)

    # Remove scope if present for validation
    NAME_TO_VALIDATE="$PACKAGE_NAME"
    if [[ "$PACKAGE_NAME" == @*/* ]]; then
        NAME_TO_VALIDATE=$(echo "$PACKAGE_NAME" | cut -d'/' -f2)
    fi

    # Check for valid characters
    if [[ ! "$NAME_TO_VALIDATE" =~ ^[a-z0-9][a-z0-9._-]*$ ]]; then
        echo "❌ ERROR: Invalid package name: $PACKAGE_NAME"
        echo "   npm package names must:"
        echo "   - Be lowercase"
        echo "   - Start with a letter or number"
        echo "   - Contain only lowercase letters, numbers, hyphens, underscores, dots"
        exit 1
    fi

    # Check length
    if [ ${#NAME_TO_VALIDATE} -gt 214 ]; then
        echo "❌ ERROR: Package name too long (>214 characters)"
        exit 1
    fi

    echo "✅ Package name is valid: $PACKAGE_NAME"
```

### Step 6: Validate Version Format

```yaml
- name: Validate version format
  if: steps.detect.outputs.has-package == 'true'
  run: |
    echo "=== Validating Version Format ==="

    VERSION="${{ steps.detect.outputs.package-version }}"
    GIT_TAG="${GITHUB_REF#refs/tags/}"
    GIT_TAG_VERSION="${GIT_TAG#v}"
    GIT_TAG_VERSION="${GIT_TAG_VERSION#frontend-v}"

    echo "Package version: $VERSION"
    echo "Git tag: $GIT_TAG"
    echo "Git tag version: $GIT_TAG_VERSION"
    echo ""

    # Validate semver format
    if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$ ]]; then
        echo "⚠️  WARNING: Version may not be valid semver: $VERSION"
        echo "   Recommended format: X.Y.Z or X.Y.Z-prerelease+build"
    else
        echo "✅ Version format is valid semver"
    fi

    # Check version match with Git tag
    if [ "$VERSION" != "$GIT_TAG_VERSION" ]; then
        echo "⚠️  WARNING: Version mismatch"
        echo "   Git tag: $GIT_TAG_VERSION"
        echo "   package.json: $VERSION"
        echo ""
        echo "   Consider synchronizing versions before publishing"
    else
        echo "✅ Version matches Git tag"
    fi
```

### Step 7: Check Dependencies

```yaml
- name: Analyze dependencies
  if: steps.detect.outputs.has-package == 'true'
  working-directory: ${{ steps.detect.outputs.package-dir }}
  run: |
    echo "=== Analyzing Package Dependencies ==="
    echo ""

    # Count dependencies
    DEPS_COUNT=$(jq '.dependencies // {} | length' package.json)
    DEV_DEPS_COUNT=$(jq '.devDependencies // {} | length' package.json)
    PEER_DEPS_COUNT=$(jq '.peerDependencies // {} | length' package.json)

    echo "Dependency Counts:"
    echo "  dependencies: $DEPS_COUNT"
    echo "  devDependencies: $DEV_DEPS_COUNT"
    echo "  peerDependencies: $PEER_DEPS_COUNT"
    echo ""

    # List production dependencies
    if [ "$DEPS_COUNT" -gt 0 ]; then
        echo "Production Dependencies:"
        jq -r '.dependencies | to_entries[] | "  \(.key): \(.value)"' package.json
        echo ""
    fi

    # Check for peer dependencies
    if [ "$PEER_DEPS_COUNT" -gt 0 ]; then
        echo "Peer Dependencies (users must install):"
        jq -r '.peerDependencies | to_entries[] | "  \(.key): \(.value)"' package.json
        echo ""
    fi

    # Warn about large dependency trees
    if [ "$DEPS_COUNT" -gt 20 ]; then
        echo "⚠️  WARNING: Large number of dependencies ($DEPS_COUNT)"
        echo "   Consider reducing dependencies for better package size"
    fi
```

### Step 8: Generate Detection Report

```yaml
- name: Generate detection report
  if: steps.detect.outputs.has-package == 'true'
  working-directory: ${{ steps.detect.outputs.package-dir }}
  run: |
    cat > frontend-detection-report.md << 'EOF'
    # Frontend Package Detection Report

    ## Package Information

    - **Package Name**: ${{ steps.detect.outputs.package-name }}
    - **Version**: ${{ steps.detect.outputs.package-version }}
    - **Package Manager**: ${{ steps.detect.outputs.package-manager }}
    - **Package Directory**: ${{ steps.detect.outputs.package-dir }}
    - **Scoped**: ${{ steps.detect.outputs.is-scoped }}

    ## Configuration Files

    EOF

    # Check for configuration files
    for file in package.json package-lock.json yarn.lock pnpm-lock.yaml \
                tsconfig.json .npmrc .npmignore README.md LICENSE; do
        if [ -f "$file" ]; then
            echo "- ✅ $file" >> frontend-detection-report.md
        fi
    done

    cat >> frontend-detection-report.md << 'EOF'

    ## Build Configuration

    - **Build Script**: ${{ steps.detect.outputs.build-script }}

    EOF

    # Add entry points
    echo "## Entry Points" >> frontend-detection-report.md
    echo "" >> frontend-detection-report.md

    for field in main module types exports; do
        VALUE=$(jq -r ".$field // \"Not specified\"" package.json)
        echo "- **$field**: \`$VALUE\`" >> frontend-detection-report.md
    done

    cat >> frontend-detection-report.md << 'EOF'

    ## Next Steps

    1. Install dependencies
    2. Run build script
    3. Validate package structure
    4. Publish to registries

    ---
    Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
    EOF

    cat frontend-detection-report.md

- name: Upload detection report
  if: steps.detect.outputs.has-package == 'true'
  uses: actions/upload-artifact@v4
  with:
    name: frontend-detection-report
    path: ${{ steps.detect.outputs.package-dir }}/frontend-detection-report.md
    retention-days: 30
```

## Testing Detection Locally

### Test Script 1: Package Detection

```bash
#!/bin/bash
# test-frontend-detection.sh

echo "=== Testing Frontend Package Detection ==="
echo ""

# Find package.json files
echo "1. Finding package.json files..."
PACKAGE_FILES=$(find . -name "package.json" \
  -not -path "*/node_modules/*" \
  -not -path "*/dist/*" \
  -type f)

if [ -z "$PACKAGE_FILES" ]; then
    echo "❌ No package.json files found"
    exit 1
fi

echo "✅ Found package.json files:"
echo "$PACKAGE_FILES" | sed 's/^/  /'
echo ""

# Check first package
FIRST_PKG=$(echo "$PACKAGE_FILES" | head -1)
echo "2. Analyzing: $FIRST_PKG"
echo ""

# Extract metadata
PKG_NAME=$(jq -r '.name' "$FIRST_PKG")
PKG_VERSION=$(jq -r '.version' "$FIRST_PKG")
IS_PRIVATE=$(jq -r '.private // false' "$FIRST_PKG")

echo "  Name: $PKG_NAME"
echo "  Version: $PKG_VERSION"
echo "  Private: $IS_PRIVATE"

# Check if scoped
if [[ "$PKG_NAME" == @*/* ]]; then
    echo "  ✅ Scoped package"
else
    echo "  ⚠️  Unscoped package"
fi

# Detect package manager
echo ""
echo "3. Detecting package manager..."
PKG_DIR=$(dirname "$FIRST_PKG")
cd "$PKG_DIR"

if [ -f "pnpm-lock.yaml" ]; then
    echo "  ✅ pnpm"
elif [ -f "yarn.lock" ]; then
    echo "  ✅ yarn"
elif [ -f "package-lock.json" ]; then
    echo "  ✅ npm"
else
    echo "  ⚠️  No lock file (using npm)"
fi

echo ""
echo "✅ Detection test completed!"
```

**Run it:**

```bash
chmod +x test-frontend-detection.sh
./test-frontend-detection.sh
```

### Test Script 2: Package Manager Detection

```bash
#!/bin/bash
# test-package-manager.sh

echo "=== Testing Package Manager Detection ==="
echo ""

# Check current directory
if [ ! -f "package.json" ]; then
    echo "❌ No package.json in current directory"
    exit 1
fi

echo "Checking for lock files..."
echo ""

if [ -f "pnpm-lock.yaml" ]; then
    echo "✅ pnpm detected (pnpm-lock.yaml)"
    INSTALL_CMD="pnpm install"
    BUILD_CMD="pnpm build"
    PUBLISH_CMD="pnpm publish"

elif [ -f "yarn.lock" ]; then
    if [ -f ".yarnrc.yml" ]; then
        echo "✅ Yarn Berry detected (yarn.lock + .yarnrc.yml)"
    else
        echo "✅ Yarn Classic detected (yarn.lock)"
    fi
    INSTALL_CMD="yarn install"
    BUILD_CMD="yarn build"
    PUBLISH_CMD="yarn publish"

elif [ -f "package-lock.json" ]; then
    echo "✅ npm detected (package-lock.json)"
    INSTALL_CMD="npm install"
    BUILD_CMD="npm run build"
    PUBLISH_CMD="npm publish"

else
    echo "⚠️  No lock file found, defaulting to npm"
    INSTALL_CMD="npm install"
    BUILD_CMD="npm run build"
    PUBLISH_CMD="npm publish"
fi

echo ""
echo "Recommended commands:"
echo "  Install: $INSTALL_CMD"
echo "  Build: $BUILD_CMD"
echo "  Publish: $PUBLISH_CMD"
```

**Run it:**

```bash
chmod +x test-package-manager.sh
./test-package-manager.sh
```

## Commit Detection Job Changes

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage the workflow
git add .github/workflows/release-frontend.yml

# Commit with conventional format
git commit -m "feat(release-frontend): add frontend package detection and validation

Added comprehensive frontend package detection to release-frontend.yml:

Added Job:
- detect-frontend-package: Auto-detects npm packages and metadata

Detection Features:
- Finds all package.json files (excludes node_modules, dist, build)
- Filters out private packages and workspace roots
- Auto-detects package manager (npm, yarn, pnpm, yarn-berry)
- Extracts package metadata (name, version, description)
- Validates package name format (npm rules)
- Validates version format (semver)
- Checks version consistency with Git tags
- Analyzes dependencies and counts
- Generates detailed detection report

Package Manager Support:
- npm: package-lock.json detection
- Yarn Classic: yarn.lock detection
- Yarn Berry: yarn.lock + .yarnrc.yml detection
- pnpm: pnpm-lock.yaml detection

Outputs:
- has-package: Whether frontend package exists
- package-name: Package name from package.json
- package-version: Package version
- package-manager: Detected package manager
- package-dir: Package directory location
- is-scoped: Whether package is scoped (@scope/name)
- build-script: Build script from package.json

Validation:
- npm package name rules enforcement
- Semantic versioning validation
- Git tag version matching
- Dependency analysis
- Large dependency tree warnings

Benefits:
- Automatic package detection
- Multi-package-manager support
- Robust validation
- Clear reporting

Files changed:
- .github/workflows/release-frontend.yml - Added detection job"
```

## Next Steps

**Continue to Part 3:** Dependency installation and package building with multi-package-manager
support.
