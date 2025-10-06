<!-- file: docs/cross-registry-todos/task-05/t05-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t05-python-packages-part3-f7g8h9i0-j1k2 -->

# Task 05 Part 3: Package Building Job

## Stage 1: Add Build Dependencies Job

### Step 1: Install Build Tools

```yaml
install-build-tools:
  name: Install Build Tools
  runs-on: ubuntu-latest
  needs: [detect-python-package]
  if: needs.detect-python-package.outputs.has-package == 'true'

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'

    - name: Install base build tools
      run: |
        echo "=== Installing Base Build Tools ==="
        python -m pip install --upgrade pip setuptools wheel

        # Install build tool based on detected system
        BUILD_SYSTEM="${{ needs.detect-python-package.outputs.build-system }}"

        if [ "$BUILD_SYSTEM" = "poetry" ]; then
            echo "Installing Poetry..."
            python -m pip install poetry
            poetry --version

        elif [ "$BUILD_SYSTEM" = "flit" ]; then
            echo "Installing Flit..."
            python -m pip install flit
            flit --version

        elif [ "$BUILD_SYSTEM" = "hatch" ]; then
            echo "Installing Hatch..."
            python -m pip install hatch
            hatch --version

        else
            echo "Using standard build tools..."
            python -m pip install build twine
        fi

        # Always install build and twine for compatibility
        python -m pip install build twine

        echo "✅ Build tools installed successfully"
```

## Stage 2: Add Package Building Job

### Step 1: Build Job Definition

```yaml
build-python-package:
  name: Build Python Package
  runs-on: ubuntu-latest
  needs: [detect-python-package]
  if: needs.detect-python-package.outputs.has-package == 'true'

  steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0 # Full history for setuptools_scm if used

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'

    - name: Install build dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install build twine wheel setuptools
```

### Step 2: Poetry Build

```yaml
- name: Build with Poetry
  if: needs.detect-python-package.outputs.build-system == 'poetry'
  working-directory: ${{ needs.detect-python-package.outputs.package-dir }}
  run: |
    echo "=== Building with Poetry ==="

    # Install Poetry
    python -m pip install poetry
    poetry --version

    # Configure Poetry for CI
    poetry config virtualenvs.create false
    poetry config virtualenvs.in-project false

    # Install dependencies (needed for build)
    echo "Installing dependencies..."
    poetry install --no-interaction --no-ansi

    # Build package
    echo "Building package..."
    poetry build --format wheel
    poetry build --format sdist

    # Display built artifacts
    echo "Built artifacts:"
    ls -lh dist/

    echo "✅ Poetry build completed"
```

### Step 3: Setuptools Build

```yaml
- name: Build with setuptools
  if: needs.detect-python-package.outputs.build-system == 'setuptools'
  working-directory: ${{ needs.detect-python-package.outputs.package-dir }}
  run: |
    echo "=== Building with setuptools ==="

    # Check if using pyproject.toml or setup.py
    if [ -f "pyproject.toml" ]; then
        echo "Using pyproject.toml build configuration"
        BUILD_BACKEND=$(grep -A 5 "^\[build-system\]" pyproject.toml | grep "^build-backend" | cut -d'"' -f2 || echo "setuptools.build_meta")
        echo "Build backend: $BUILD_BACKEND"
    else
        echo "Using setup.py build configuration"
    fi

    # Build using python -m build (PEP 517)
    echo "Building distributions..."
    python -m build --sdist --wheel --outdir dist/

    # Display built artifacts
    echo "Built artifacts:"
    ls -lh dist/

    echo "✅ setuptools build completed"
```

### Step 4: Flit Build

```yaml
- name: Build with Flit
  if: needs.detect-python-package.outputs.build-system == 'flit'
  working-directory: ${{ needs.detect-python-package.outputs.package-dir }}
  run: |
    echo "=== Building with Flit ==="

    # Install Flit
    python -m pip install flit
    flit --version

    # Flit uses pyproject.toml [project] section
    echo "Flit configuration:"
    grep -A 20 "^\[project\]" pyproject.toml || true

    # Build using python -m build (recommended for CI)
    echo "Building distributions..."
    python -m build --sdist --wheel --outdir dist/

    # Alternative: Use flit directly
    # flit build --format wheel
    # flit build --format sdist

    # Display built artifacts
    echo "Built artifacts:"
    ls -lh dist/

    echo "✅ Flit build completed"
```

### Step 5: Hatch Build

```yaml
- name: Build with Hatch
  if: needs.detect-python-package.outputs.build-system == 'hatch'
  working-directory: ${{ needs.detect-python-package.outputs.package-dir }}
  run: |
    echo "=== Building with Hatch ==="

    # Install Hatch
    python -m pip install hatch
    hatch --version

    # Hatch uses pyproject.toml [tool.hatch] section
    echo "Hatch configuration:"
    grep -A 20 "^\[tool\.hatch" pyproject.toml || true

    # Build using python -m build
    echo "Building distributions..."
    python -m build --sdist --wheel --outdir dist/

    # Alternative: Use hatch directly
    # hatch build --target wheel
    # hatch build --target sdist

    # Display built artifacts
    echo "Built artifacts:"
    ls -lh dist/

    echo "✅ Hatch build completed"
```

### Step 6: Verify Build Artifacts

```yaml
- name: Verify build artifacts
  working-directory: ${{ needs.detect-python-package.outputs.package-dir }}
  run: |
    echo "=== Verifying Build Artifacts ==="
    echo ""

    # Check dist directory exists
    if [ ! -d "dist" ]; then
        echo "❌ ERROR: dist/ directory not found"
        exit 1
    fi

    # Count artifacts
    WHEEL_COUNT=$(ls -1 dist/*.whl 2>/dev/null | wc -l)
    SDIST_COUNT=$(ls -1 dist/*.tar.gz 2>/dev/null | wc -l)

    echo "Artifacts found:"
    echo "  Wheels: $WHEEL_COUNT"
    echo "  Source distributions: $SDIST_COUNT"
    echo ""

    # Require at least one of each
    if [ "$WHEEL_COUNT" -lt 1 ]; then
        echo "❌ ERROR: No wheel (.whl) file found"
        exit 1
    fi

    if [ "$SDIST_COUNT" -lt 1 ]; then
        echo "❌ ERROR: No source distribution (.tar.gz) file found"
        exit 1
    fi

    # Display artifact details
    echo "Artifact details:"
    ls -lh dist/
    echo ""

    # Check artifact sizes
    for file in dist/*; do
        SIZE=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        if [ "$SIZE" -lt 1024 ]; then
            echo "⚠️  WARNING: Artifact seems too small: $file ($SIZE bytes)"
        fi
    done

    echo "✅ Build artifacts verified"
```

### Step 7: Check Package Metadata

```yaml
- name: Check package metadata
  working-directory: ${{ needs.detect-python-package.outputs.package-dir }}
  run: |
    echo "=== Checking Package Metadata ==="
    echo ""

    # Use twine to check metadata
    python -m pip install --upgrade twine

    echo "Running twine check..."
    python -m twine check dist/* || {
        echo "❌ ERROR: Package metadata check failed"
        echo "   Fix metadata issues before publishing"
        exit 1
    }

    echo "✅ Package metadata is valid"
```

### Step 8: Extract Wheel Metadata

```yaml
- name: Extract wheel metadata
  working-directory: ${{ needs.detect-python-package.outputs.package-dir }}
  run: |
    echo "=== Extracting Wheel Metadata ==="
    echo ""

    # Find wheel file
    WHEEL_FILE=$(ls dist/*.whl | head -1)

    if [ -z "$WHEEL_FILE" ]; then
        echo "❌ ERROR: No wheel file found"
        exit 1
    fi

    echo "Examining wheel: $WHEEL_FILE"
    echo ""

    # Extract wheel filename components
    WHEEL_FILENAME=$(basename "$WHEEL_FILE")

    # Parse wheel filename (PEP 427)
    # Format: {distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl
    IFS='-' read -ra PARTS <<< "${WHEEL_FILENAME%.whl}"

    echo "Wheel filename components:"
    echo "  Distribution: ${PARTS[0]}"
    echo "  Version: ${PARTS[1]}"

    # Use wheel command to inspect (if available)
    if command -v wheel &> /dev/null; then
        echo ""
        echo "Wheel contents:"
        wheel unpack "$WHEEL_FILE" --dest /tmp/wheel-inspect
        echo "Files in wheel:"
        find "/tmp/wheel-inspect" -type f | head -20
    else
        # Use unzip as fallback
        echo ""
        echo "Wheel contents (using unzip):"
        unzip -l "$WHEEL_FILE" | head -30
    fi

    echo ""
    echo "✅ Wheel metadata extracted"
```

### Step 9: Generate Build Report

```yaml
- name: Generate build report
  if: always()
  working-directory: ${{ needs.detect-python-package.outputs.package-dir }}
  run: |
    cat > build-report.md << 'EOF'
    # Python Package Build Report

    ## Build Configuration

    - **Build System**: ${{ needs.detect-python-package.outputs.build-system }}
    - **Package Name**: ${{ needs.detect-python-package.outputs.package-name }}
    - **Package Version**: ${{ needs.detect-python-package.outputs.package-version }}
    - **Python Version**: ${{ env.PYTHON_VERSION }}
    - **Package Directory**: ${{ needs.detect-python-package.outputs.package-dir }}

    ## Build Artifacts

    EOF

    if [ -d "dist" ]; then
        echo "### Wheel Files" >> build-report.md
        echo "" >> build-report.md
        ls -lh dist/*.whl 2>/dev/null | awk '{print "- " $9 " (" $5 ")"}' >> build-report.md || echo "No wheel files" >> build-report.md
        echo "" >> build-report.md

        echo "### Source Distributions" >> build-report.md
        echo "" >> build-report.md
        ls -lh dist/*.tar.gz 2>/dev/null | awk '{print "- " $9 " (" $5 ")"}' >> build-report.md || echo "No sdist files" >> build-report.md
        echo "" >> build-report.md
    fi

    cat >> build-report.md << 'EOF'

    ## Build Status

    - ✅ Build completed successfully
    - ✅ Metadata validated
    - ✅ Ready for testing and publishing

    ## Next Steps

    1. Test package installation
    2. Run package validation tests
    3. Publish to Test PyPI
    4. Publish to PyPI
    5. Publish to GitHub Packages

    ---
    Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
    EOF

    cat build-report.md

- name: Upload build artifacts
  uses: actions/upload-artifact@v4
  with:
    name:
      python-dist-${{ needs.detect-python-package.outputs.package-name }}-${{
      needs.detect-python-package.outputs.package-version }}
    path: ${{ needs.detect-python-package.outputs.package-dir }}/dist/
    retention-days: 90

- name: Upload build report
  uses: actions/upload-artifact@v4
  with:
    name: python-build-report
    path: ${{ needs.detect-python-package.outputs.package-dir }}/build-report.md
    retention-days: 30
```

## Testing Build Locally

### Test Script 1: Complete Build Test

```bash
#!/bin/bash
# test-python-build.sh

set -e

echo "=== Testing Python Package Build ==="
echo ""

# Detect build system
if [ -f "poetry.lock" ] || grep -q "^\[tool\.poetry\]" pyproject.toml 2>/dev/null; then
    BUILD_SYSTEM="poetry"
elif grep -q "^\[tool\.flit" pyproject.toml 2>/dev/null; then
    BUILD_SYSTEM="flit"
elif grep -q "^\[tool\.hatch" pyproject.toml 2>/dev/null; then
    BUILD_SYSTEM="hatch"
else
    BUILD_SYSTEM="setuptools"
fi

echo "Build system: $BUILD_SYSTEM"
echo ""

# Clean previous builds
if [ -d "dist" ]; then
    echo "Cleaning previous build artifacts..."
    rm -rf dist/
fi

# Install build tools
echo "Installing build tools..."
python -m pip install --upgrade pip build twine

if [ "$BUILD_SYSTEM" = "poetry" ]; then
    python -m pip install poetry
    poetry build
elif [ "$BUILD_SYSTEM" = "flit" ]; then
    python -m pip install flit
    python -m build
elif [ "$BUILD_SYSTEM" = "hatch" ]; then
    python -m pip install hatch
    python -m build
else
    python -m build
fi

echo ""
echo "Build artifacts:"
ls -lh dist/

echo ""
echo "Checking package metadata..."
python -m twine check dist/*

echo ""
echo "✅ Build test completed successfully!"
```

**Run it:**

```bash
chmod +x test-python-build.sh
./test-python-build.sh
```

### Test Script 2: Local Installation Test

```bash
#!/bin/bash
# test-local-install.sh

set -e

echo "=== Testing Local Package Installation ==="
echo ""

if [ ! -d "dist" ]; then
    echo "❌ ERROR: No dist/ directory found"
    echo "   Run build first"
    exit 1
fi

# Find wheel file
WHEEL_FILE=$(ls dist/*.whl | head -1)

if [ -z "$WHEEL_FILE" ]; then
    echo "❌ ERROR: No wheel file found"
    exit 1
fi

echo "Testing wheel: $WHEEL_FILE"
echo ""

# Create temporary virtual environment
VENV_DIR=$(mktemp -d)
echo "Creating temporary venv at: $VENV_DIR"
python -m venv "$VENV_DIR"

# Activate venv
source "$VENV_DIR/bin/activate"

# Install wheel
echo "Installing wheel..."
pip install "$WHEEL_FILE"

# Try to import package
PACKAGE_NAME=$(echo "$WHEEL_FILE" | sed 's|dist/||' | cut -d'-' -f1)
echo ""
echo "Testing import..."
python -c "import $PACKAGE_NAME; print('✅ Import successful')" || {
    echo "❌ Import failed"
    deactivate
    rm -rf "$VENV_DIR"
    exit 1
}

# Show installed package info
echo ""
echo "Package info:"
pip show "$PACKAGE_NAME"

# Cleanup
deactivate
rm -rf "$VENV_DIR"

echo ""
echo "✅ Local installation test passed!"
```

**Run it:**

```bash
chmod +x test-local-install.sh
./test-local-install.sh
```

## Commit Build Job Changes

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage the workflow
git add .github/workflows/release-python.yml

# Commit with conventional format
git commit -m "feat(release-python): add package building with multi-system support

Added comprehensive package building to release-python.yml:

Added Job:
- build-python-package: Builds wheel and sdist distributions

Build System Support:
- Poetry: Uses poetry build
- setuptools: Uses python -m build (PEP 517)
- Flit: Uses python -m build
- Hatch: Uses python -m build

Build Features:
- Automatic build tool installation based on detected system
- Generates both wheel (.whl) and source distribution (.tar.gz)
- Validates build artifacts existence and size
- Checks package metadata with twine
- Extracts and displays wheel contents
- Generates detailed build report

Artifacts:
- python-dist-{name}-{version}: Built distributions
- python-build-report: Build status and details

Quality Checks:
- Verifies both wheel and sdist are created
- Validates artifact sizes
- Checks metadata compliance
- Supports PEP 517 builds

Files changed:
- .github/workflows/release-python.yml - Added build job"
```

## Next Steps

**Continue to Part 4:** Package validation and testing before publishing.
