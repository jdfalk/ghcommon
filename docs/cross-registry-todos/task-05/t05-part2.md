<!-- file: docs/cross-registry-todos/task-05/t05-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t05-python-packages-part2-e6f7a8b9-c0d1 -->

# Task 05 Part 2: Workflow Header and Package Detection

## Stage 1: Update Workflow Header and Environment

### Step 1: Open Workflow File

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon
code .github/workflows/release-python.yml
```

### Step 2: Update Version and Header

```yaml
# file: .github/workflows/release-python.yml
# version: 2.0.0  # Update this
# guid: [keep existing guid]
#
# Changes in 2.0.0:
# - Added Python package publishing to PyPI and GitHub Packages
# - Added build system auto-detection (Poetry, setuptools, Flit, Hatch)
# - Added package validation before publishing
# - Support for wheel and sdist distribution formats
# - Multi-registry publishing support

name: Release - Python
```

### Step 3: Update or Add Permissions

```yaml
permissions:
  contents: write # For creating releases and tags
  packages: write # For publishing to GitHub Packages
  id-token: write # For trusted publishing to PyPI
  pull-requests: read # For checking PR context
```

### Step 4: Add Environment Variables

```yaml
env:
  # Python configuration
  PYTHON_VERSION: '3.11' # Default Python version
  PYTHON_MIN_VERSION: '3.8' # Minimum supported version

  # Package registry configuration
  PYPI_REGISTRY: 'https://upload.pypi.org/legacy/'
  TEST_PYPI_REGISTRY: 'https://test.pypi.org/legacy/'
  GITHUB_PACKAGES_REGISTRY: 'https://pypi.pkg.github.com/'

  # Build configuration
  BUILD_ISOLATION: 'true'
  PIP_NO_CACHE_DIR: 'false'
  PIP_DISABLE_PIP_VERSION_CHECK: '1'

  # Publishing configuration
  PUBLISH_TO_PYPI: 'false' # Set to true when PyPI token configured
  PUBLISH_TO_TEST_PYPI: 'true' # Test publishing first
  PUBLISH_TO_GITHUB_PACKAGES: 'true'
  SKIP_EXISTING: 'true' # Don't fail if version exists
```

### Step 5: Verify Workflow Triggers

```yaml
on:
  push:
    tags:
      - 'v*.*.*' # Semantic version tags
  workflow_dispatch:
    inputs:
      tag:
        description: 'Release tag (e.g., v1.2.3)'
        required: true
        type: string
      publish_to_pypi:
        description: 'Publish to PyPI'
        required: false
        type: boolean
        default: false
```

## Stage 2: Add Package Detection Job

### Step 1: Add Detection Job Definition

```yaml
jobs:
  # Existing jobs...

  detect-python-package:
    name: Detect Python Package
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    outputs:
      has-package: ${{ steps.detect.outputs.has-package }}
      build-system: ${{ steps.detect.outputs.build-system }}
      package-name: ${{ steps.detect.outputs.package-name }}
      package-version: ${{ steps.detect.outputs.package-version }}
      package-dir: ${{ steps.detect.outputs.package-dir }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      # Continue with detection steps...
```

### Step 2: Detect Build System

```yaml
- name: Detect build system
  id: detect
  run: |
    echo "=== Detecting Python Package Configuration ==="
    echo ""

    HAS_PACKAGE="false"
    BUILD_SYSTEM="none"
    PACKAGE_DIR="."

    # Function to find Python package directories
    find_package_dirs() {
        # Look for common package indicators
        find . -type f \( \
            -name "setup.py" -o \
            -name "setup.cfg" -o \
            -name "pyproject.toml" -o \
            -name "poetry.lock" \
        \) | sed 's|/[^/]*$||' | sort -u
    }

    # Search for package configurations
    PACKAGE_DIRS=$(find_package_dirs)

    if [ -z "$PACKAGE_DIRS" ]; then
        echo "⚠️  No Python package configuration found"
        echo "has-package=false" >> $GITHUB_OUTPUT
        exit 0
    fi

    # Use first package directory found
    PACKAGE_DIR=$(echo "$PACKAGE_DIRS" | head -1)
    cd "$PACKAGE_DIR"

    echo "📦 Package directory: $PACKAGE_DIR"
    echo "package-dir=$PACKAGE_DIR" >> $GITHUB_OUTPUT

    # Detect build system
    if [ -f "poetry.lock" ] || grep -q "^\[tool\.poetry\]" pyproject.toml 2>/dev/null; then
        BUILD_SYSTEM="poetry"
        echo "🔧 Build system: Poetry"

    elif grep -q "^\[tool\.flit" pyproject.toml 2>/dev/null; then
        BUILD_SYSTEM="flit"
        echo "🔧 Build system: Flit"

    elif grep -q "^\[tool\.hatch" pyproject.toml 2>/dev/null; then
        BUILD_SYSTEM="hatch"
        echo "🔧 Build system: Hatchling"

    elif [ -f "setup.py" ]; then
        BUILD_SYSTEM="setuptools"
        echo "🔧 Build system: setuptools (setup.py)"

    elif [ -f "pyproject.toml" ]; then
        BUILD_SYSTEM="setuptools"
        echo "🔧 Build system: setuptools (pyproject.toml)"

    else
        echo "❌ Unable to determine build system"
        echo "has-package=false" >> $GITHUB_OUTPUT
        exit 0
    fi

    HAS_PACKAGE="true"
    echo "has-package=true" >> $GITHUB_OUTPUT
    echo "build-system=$BUILD_SYSTEM" >> $GITHUB_OUTPUT
```

### Step 3: Extract Package Metadata

```yaml
- name: Extract package metadata
  id: metadata
  if: steps.detect.outputs.has-package == 'true'
  working-directory: ${{ steps.detect.outputs.package-dir }}
  run: |
    echo "=== Extracting Package Metadata ==="
    echo ""

    BUILD_SYSTEM="${{ steps.detect.outputs.build-system }}"
    PACKAGE_NAME=""
    PACKAGE_VERSION=""

    # Extract metadata based on build system
    if [ "$BUILD_SYSTEM" = "poetry" ]; then
        # Poetry uses pyproject.toml [tool.poetry]
        PACKAGE_NAME=$(grep -A 10 "^\[tool\.poetry\]" pyproject.toml | grep "^name" | cut -d'"' -f2)
        PACKAGE_VERSION=$(grep -A 10 "^\[tool\.poetry\]" pyproject.toml | grep "^version" | cut -d'"' -f2)

    elif [ "$BUILD_SYSTEM" = "setuptools" ] && [ -f "pyproject.toml" ]; then
        # Modern setuptools uses [project] section
        PACKAGE_NAME=$(grep -A 10 "^\[project\]" pyproject.toml | grep "^name" | cut -d'"' -f2)
        PACKAGE_VERSION=$(grep -A 10 "^\[project\]" pyproject.toml | grep "^version" | cut -d'"' -f2)

        # If no version in pyproject.toml, check setup.py
        if [ -z "$PACKAGE_VERSION" ] && [ -f "setup.py" ]; then
            PACKAGE_VERSION=$(python -c "import re; content=open('setup.py').read(); match=re.search(r'version=[\"']([^\"']+)[\"']', content); print(match.group(1) if match else '')")
        fi

    elif [ "$BUILD_SYSTEM" = "setuptools" ] && [ -f "setup.py" ]; then
        # Legacy setuptools with setup.py
        PACKAGE_NAME=$(python -c "import re; content=open('setup.py').read(); match=re.search(r'name=[\"']([^\"']+)[\"']', content); print(match.group(1) if match else '')")
        PACKAGE_VERSION=$(python -c "import re; content=open('setup.py').read(); match=re.search(r'version=[\"']([^\"']+)[\"']', content); print(match.group(1) if match else '')")

    elif [ "$BUILD_SYSTEM" = "flit" ] || [ "$BUILD_SYSTEM" = "hatch" ]; then
        # Flit and Hatch use [project] section
        PACKAGE_NAME=$(grep -A 10 "^\[project\]" pyproject.toml | grep "^name" | cut -d'"' -f2)
        PACKAGE_VERSION=$(grep -A 10 "^\[project\]" pyproject.toml | grep "^version" | cut -d'"' -f2)
    fi

    # If version not found in config, check for dynamic version
    if [ -z "$PACKAGE_VERSION" ]; then
        # Check for version file
        if [ -f "src/${PACKAGE_NAME}/__version__.py" ]; then
            PACKAGE_VERSION=$(grep -E "^__version__" "src/${PACKAGE_NAME}/__version__.py" | cut -d'"' -f2)
        elif [ -f "${PACKAGE_NAME}/__version__.py" ]; then
            PACKAGE_VERSION=$(grep -E "^__version__" "${PACKAGE_NAME}/__version__.py" | cut -d'"' -f2)
        elif [ -f "src/${PACKAGE_NAME}/_version.py" ]; then
            PACKAGE_VERSION=$(grep -E "^__version__" "src/${PACKAGE_NAME}/_version.py" | cut -d'"' -f2)
        fi
    fi

    # Use Git tag version if package version is dynamic or missing
    GIT_TAG_VERSION="${GITHUB_REF#refs/tags/v}"
    if [ -z "$PACKAGE_VERSION" ] || [ "$PACKAGE_VERSION" = "0.0.0" ]; then
        echo "ℹ️  Using Git tag version: $GIT_TAG_VERSION"
        PACKAGE_VERSION="$GIT_TAG_VERSION"
    fi

    # Validate extracted metadata
    if [ -z "$PACKAGE_NAME" ]; then
        echo "❌ ERROR: Could not determine package name"
        exit 1
    fi

    if [ -z "$PACKAGE_VERSION" ]; then
        echo "❌ ERROR: Could not determine package version"
        exit 1
    fi

    echo "📦 Package name: $PACKAGE_NAME"
    echo "🏷️  Package version: $PACKAGE_VERSION"

    echo "package-name=$PACKAGE_NAME" >> $GITHUB_OUTPUT
    echo "package-version=$PACKAGE_VERSION" >> $GITHUB_OUTPUT
```

### Step 4: Validate Package Name

```yaml
- name: Validate package name
  if: steps.detect.outputs.has-package == 'true'
  run: |
    echo "=== Validating Package Name ==="

    PACKAGE_NAME="${{ steps.metadata.outputs.package-name }}"

    # Check for valid Python package name
    # PEP 508: lowercase letters, numbers, hyphens, underscores
    if [[ ! "$PACKAGE_NAME" =~ ^[a-z0-9]([a-z0-9_-]*[a-z0-9])?$ ]]; then
        echo "❌ ERROR: Invalid package name: $PACKAGE_NAME"
        echo "   Package names must:"
        echo "   - Start and end with a letter or number"
        echo "   - Contain only lowercase letters, numbers, hyphens, underscores"
        echo "   - Not start or end with special characters"
        exit 1
    fi

    echo "✅ Package name is valid: $PACKAGE_NAME"
```

### Step 5: Validate Version Format

```yaml
- name: Validate version format
  if: steps.detect.outputs.has-package == 'true'
  run: |
    echo "=== Validating Version Format ==="

    VERSION="${{ steps.metadata.outputs.package-version }}"
    GIT_TAG_VERSION="${GITHUB_REF#refs/tags/v}"

    # Check PEP 440 version format
    # Basic pattern: N(.N)*[{a|b|rc}N][.postN][.devN]
    if [[ ! "$VERSION" =~ ^[0-9]+(\.[0-9]+)*((a|b|rc)[0-9]+)?(\.post[0-9]+)?(\.dev[0-9]+)?$ ]]; then
        echo "⚠️  WARNING: Version may not comply with PEP 440: $VERSION"
        echo "   Recommended format: X.Y.Z or X.Y.Z.devN"
    else
        echo "✅ Version format is valid: $VERSION"
    fi

    # Check if package version matches Git tag
    if [ "$VERSION" != "$GIT_TAG_VERSION" ]; then
        echo "⚠️  WARNING: Version mismatch"
        echo "   Git tag: $GIT_TAG_VERSION"
        echo "   Package: $VERSION"
        echo "   Consider synchronizing versions"
    else
        echo "✅ Version matches Git tag"
    fi
```

### Step 6: Display Detection Summary

```yaml
- name: Display detection summary
  if: always()
  run: |
    echo "=== Python Package Detection Summary ==="
    echo ""
    echo "Has Package: ${{ steps.detect.outputs.has-package }}"

    if [ "${{ steps.detect.outputs.has-package }}" = "true" ]; then
        echo "Build System: ${{ steps.detect.outputs.build-system }}"
        echo "Package Directory: ${{ steps.detect.outputs.package-dir }}"
        echo "Package Name: ${{ steps.metadata.outputs.package-name }}"
        echo "Package Version: ${{ steps.metadata.outputs.package-version }}"
        echo ""
        echo "✅ Python package detected and ready for building"
    else
        echo "⚠️  No Python package configuration found"
        echo "   Skipping package publishing"
    fi
```

### Step 7: Save Detection Report

```yaml
- name: Generate detection report
  if: steps.detect.outputs.has-package == 'true'
  working-directory: ${{ steps.detect.outputs.package-dir }}
  run: |
    cat > package-detection-report.md << EOF
    # Python Package Detection Report

    ## Package Information

    - **Package Name**: ${{ steps.metadata.outputs.package-name }}
    - **Version**: ${{ steps.metadata.outputs.package-version }}
    - **Build System**: ${{ steps.detect.outputs.build-system }}
    - **Package Directory**: ${{ steps.detect.outputs.package-dir }}

    ## Configuration Files

    $(if [ -f "setup.py" ]; then echo "- ✅ setup.py"; fi)
    $(if [ -f "setup.cfg" ]; then echo "- ✅ setup.cfg"; fi)
    $(if [ -f "pyproject.toml" ]; then echo "- ✅ pyproject.toml"; fi)
    $(if [ -f "poetry.lock" ]; then echo "- ✅ poetry.lock"; fi)
    $(if [ -f "requirements.txt" ]; then echo "- ✅ requirements.txt"; fi)
    $(if [ -f "README.md" ]; then echo "- ✅ README.md"; fi)
    $(if [ -f "LICENSE" ]; then echo "- ✅ LICENSE"; fi)

    ## Build System Details

    $(if [ "${{ steps.detect.outputs.build-system }}" = "poetry" ]; then
        echo "Using Poetry for dependency management and building."
        echo ""
        echo "Build command: \`poetry build\`"
    elif [ "${{ steps.detect.outputs.build-system }}" = "setuptools" ]; then
        echo "Using setuptools for building."
        echo ""
        echo "Build command: \`python -m build\`"
    elif [ "${{ steps.detect.outputs.build-system }}" = "flit" ]; then
        echo "Using Flit for building."
        echo ""
        echo "Build command: \`python -m build\`"
    elif [ "${{ steps.detect.outputs.build-system }}" = "hatch" ]; then
        echo "Using Hatchling for building."
        echo ""
        echo "Build command: \`python -m build\`"
    fi)

    ## Next Steps

    1. Build wheel and sdist distributions
    2. Validate package metadata
    3. Test installation
    4. Publish to registries

    ---
    Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
    EOF

    cat package-detection-report.md

- name: Upload detection report
  if: steps.detect.outputs.has-package == 'true'
  uses: actions/upload-artifact@v4
  with:
    name: python-package-detection-report
    path: ${{ steps.detect.outputs.package-dir }}/package-detection-report.md
    retention-days: 30
```

## Testing Package Detection Locally

### Test Script 1: Build System Detection

```bash
#!/bin/bash
# test-python-detection.sh

echo "=== Testing Python Package Detection ==="
echo ""

cd "$(dirname "$0")"

# Detect build system
if [ -f "poetry.lock" ] || grep -q "^\[tool\.poetry\]" pyproject.toml 2>/dev/null; then
    BUILD_SYSTEM="poetry"
elif grep -q "^\[tool\.flit" pyproject.toml 2>/dev/null; then
    BUILD_SYSTEM="flit"
elif grep -q "^\[tool\.hatch" pyproject.toml 2>/dev/null; then
    BUILD_SYSTEM="hatch"
elif [ -f "setup.py" ]; then
    BUILD_SYSTEM="setuptools"
elif [ -f "pyproject.toml" ]; then
    BUILD_SYSTEM="setuptools"
else
    echo "❌ No build system detected"
    exit 1
fi

echo "✅ Build system: $BUILD_SYSTEM"

# Extract package name based on build system
if [ "$BUILD_SYSTEM" = "poetry" ]; then
    PACKAGE_NAME=$(grep -A 10 "^\[tool\.poetry\]" pyproject.toml | grep "^name" | cut -d'"' -f2)
elif [ -f "pyproject.toml" ]; then
    PACKAGE_NAME=$(grep -A 10 "^\[project\]" pyproject.toml | grep "^name" | cut -d'"' -f2)
elif [ -f "setup.py" ]; then
    PACKAGE_NAME=$(python -c "import re; content=open('setup.py').read(); match=re.search(r'name=[\"']([^\"']+)[\"']', content); print(match.group(1) if match else '')")
fi

if [ -n "$PACKAGE_NAME" ]; then
    echo "✅ Package name: $PACKAGE_NAME"
else
    echo "❌ Could not determine package name"
    exit 1
fi

echo ""
echo "Detection successful!"
```

**Run it:**

```bash
chmod +x test-python-detection.sh
./test-python-detection.sh
```

### Test Script 2: Metadata Extraction

```bash
#!/bin/bash
# test-metadata-extraction.sh

echo "=== Testing Metadata Extraction ==="
echo ""

# Try to extract all metadata
echo "Checking for package configuration files:"
echo ""

if [ -f "setup.py" ]; then
    echo "✅ setup.py found"
    python -c "
import re
with open('setup.py') as f:
    content = f.read()
    name = re.search(r'name=[\"']([^\"']+)[\"']', content)
    version = re.search(r'version=[\"']([^\"']+)[\"']', content)
    print(f'  Name: {name.group(1) if name else \"NOT FOUND\"}')
    print(f'  Version: {version.group(1) if version else \"NOT FOUND\"}')
"
fi

if [ -f "pyproject.toml" ]; then
    echo "✅ pyproject.toml found"
    python -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
    # Try Poetry format
    if 'tool' in data and 'poetry' in data['tool']:
        print(f'  Name: {data[\"tool\"][\"poetry\"].get(\"name\", \"NOT FOUND\")}')
        print(f'  Version: {data[\"tool\"][\"poetry\"].get(\"version\", \"NOT FOUND\")}')
    # Try PEP 621 format
    elif 'project' in data:
        print(f'  Name: {data[\"project\"].get(\"name\", \"NOT FOUND\")}')
        print(f'  Version: {data[\"project\"].get(\"version\", \"NOT FOUND\")}')
"
fi

echo ""
echo "Metadata extraction complete!"
```

**Run it:**

```bash
chmod +x test-metadata-extraction.sh
python3 -m pip install tomli  # For Python < 3.11
./test-metadata-extraction.sh
```

## Commit Detection Job Changes

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage the workflow
git add .github/workflows/release-python.yml

# Commit with conventional format
git commit -m "feat(release-python): add package detection and build system identification

Added comprehensive Python package detection to release-python.yml:

Added Job:
- detect-python-package: Auto-detects build system, extracts metadata

Detection Features:
- Supports Poetry, setuptools, Flit, Hatchling build systems
- Extracts package name and version from configuration files
- Validates package name format (PEP 508)
- Validates version format (PEP 440)
- Checks version consistency with Git tags
- Generates detailed detection report

Outputs:
- has-package: Whether Python package exists
- build-system: Detected build system (poetry/setuptools/flit/hatch)
- package-name: Extracted package name
- package-version: Package version
- package-dir: Package directory location

Benefits:
- Automatic build system detection
- No manual configuration needed
- Supports multiple build tools
- Clear reporting and validation

Files changed:
- .github/workflows/release-python.yml - Added detection job"
```

## Next Steps

**Continue to Part 3:** Package building job implementation with support for all detected build
systems.
