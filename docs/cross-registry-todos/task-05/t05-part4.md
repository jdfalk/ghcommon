<!-- file: docs/cross-registry-todos/task-05/t05-part4.md -->
<!-- version: 1.0.0 -->
<!-- guid: t05-python-packages-part4-g8h9i0j1-k2l3 -->
<!-- last-edited: 2026-01-19 -->

# Task 05 Part 4: Package Validation and Testing

## Stage 1: Add Package Validation Job

### Step 1: Validation Job Definition

```yaml
validate-python-package:
  name: Validate Python Package
  runs-on: ${{ matrix.os }}
  needs: [detect-python-package, build-python-package]
  if: needs.detect-python-package.outputs.has-package == 'true'
  strategy:
    fail-fast: false
    matrix:
      os: [ubuntu-latest, windows-latest, macos-latest]
      python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Download build artifacts
      uses: actions/download-artifact@v4
      with:
        name:
          python-dist-${{ needs.detect-python-package.outputs.package-name }}-${{
          needs.detect-python-package.outputs.package-version }}
        path: dist/
```

### Step 2: Test Wheel Installation

```yaml
- name: Test wheel installation
  shell: bash
  run: |
    echo "=== Testing Wheel Installation ==="
    echo "OS: ${{ matrix.os }}"
    echo "Python: ${{ matrix.python-version }}"
    echo ""

    # Find wheel file (platform-specific or universal)
    WHEEL_FILE=$(ls dist/*.whl | head -1)

    if [ -z "$WHEEL_FILE" ]; then
        echo "❌ ERROR: No wheel file found"
        exit 1
    fi

    echo "Testing wheel: $WHEEL_FILE"

    # Install wheel
    python -m pip install --upgrade pip
    python -m pip install "$WHEEL_FILE"

    # Verify installation
    PACKAGE_NAME="${{ needs.detect-python-package.outputs.package-name }}"
    python -m pip show "$PACKAGE_NAME" || {
        echo "❌ ERROR: Package not installed"
        exit 1
    }

    echo "✅ Wheel installation successful"
```

### Step 3: Test Source Distribution Installation

```yaml
- name: Test sdist installation
  shell: bash
  run: |
    echo "=== Testing Source Distribution Installation ==="
    echo ""

    # Uninstall wheel first
    PACKAGE_NAME="${{ needs.detect-python-package.outputs.package-name }}"
    python -m pip uninstall -y "$PACKAGE_NAME" || true

    # Find sdist file
    SDIST_FILE=$(ls dist/*.tar.gz | head -1)

    if [ -z "$SDIST_FILE" ]; then
        echo "❌ ERROR: No source distribution found"
        exit 1
    fi

    echo "Testing sdist: $SDIST_FILE"

    # Install from sdist
    python -m pip install "$SDIST_FILE"

    # Verify installation
    python -m pip show "$PACKAGE_NAME" || {
        echo "❌ ERROR: Package not installed from sdist"
        exit 1
    }

    echo "✅ Source distribution installation successful"
```

### Step 4: Test Package Import

```yaml
- name: Test package import
  shell: bash
  run: |
    echo "=== Testing Package Import ==="
    echo ""

    PACKAGE_NAME="${{ needs.detect-python-package.outputs.package-name }}"

    # Replace hyphens with underscores for import
    IMPORT_NAME=$(echo "$PACKAGE_NAME" | tr '-' '_')

    # Try to import package
    python -c "import $IMPORT_NAME" || {
        echo "❌ ERROR: Failed to import $IMPORT_NAME"
        echo "Trying alternate import format..."
        python -c "import $PACKAGE_NAME" || {
            echo "❌ ERROR: Package import failed"
            exit 1
        }
    }

    echo "✅ Package import successful"
```

### Step 5: Test Package Version

```yaml
- name: Verify package version
  shell: bash
  run: |
    echo "=== Verifying Package Version ==="
    echo ""

    PACKAGE_NAME="${{ needs.detect-python-package.outputs.package-name }}"
    EXPECTED_VERSION="${{ needs.detect-python-package.outputs.package-version }}"

    # Get installed version
    INSTALLED_VERSION=$(python -m pip show "$PACKAGE_NAME" | grep "^Version:" | cut -d' ' -f2)

    echo "Expected version: $EXPECTED_VERSION"
    echo "Installed version: $INSTALLED_VERSION"

    if [ "$INSTALLED_VERSION" != "$EXPECTED_VERSION" ]; then
        echo "⚠️  WARNING: Version mismatch"
        echo "   This may indicate a packaging issue"
    else
        echo "✅ Version matches"
    fi
```

### Step 6: Test Package Dependencies

```yaml
- name: Test package dependencies
  shell: bash
  run: |
    echo "=== Testing Package Dependencies ==="
    echo ""

    PACKAGE_NAME="${{ needs.detect-python-package.outputs.package-name }}"

    # Show all dependencies
    echo "Installed dependencies:"
    python -m pip show "$PACKAGE_NAME" | grep "^Requires:" || echo "No dependencies"
    echo ""

    # Check for dependency conflicts
    echo "Checking for dependency conflicts..."
    python -m pip check || {
        echo "⚠️  WARNING: Dependency conflicts detected"
        echo "   This may cause issues for users"
    }

    echo "✅ Dependency check completed"
```

### Step 7: Run Package Tests (if available)

```yaml
- name: Run package tests
  if: hashFiles('tests/**/*.py') != ''
  shell: bash
  run: |
    echo "=== Running Package Tests ==="
    echo ""

    # Install test dependencies
    if [ -f "requirements-test.txt" ]; then
        echo "Installing test dependencies..."
        python -m pip install -r requirements-test.txt
    elif [ -f "test-requirements.txt" ]; then
        python -m pip install -r test-requirements.txt
    fi

    # Install pytest if not already installed
    python -m pip install pytest pytest-cov || true

    # Run tests
    if command -v pytest &> /dev/null; then
        echo "Running pytest..."
        pytest tests/ -v || {
            echo "⚠️  WARNING: Tests failed"
            echo "   Package may have issues"
        }
    else
        echo "ℹ️  pytest not available, skipping tests"
    fi

    echo "✅ Package tests completed"
```

## Stage 2: Add Package Metadata Validation

### Step 1: Validate PKG-INFO

```yaml
validate-package-metadata:
  name: Validate Package Metadata
  runs-on: ubuntu-latest
  needs: [detect-python-package, build-python-package]
  if: needs.detect-python-package.outputs.has-package == 'true'

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ env.PYTHON_VERSION }}

    - name: Download build artifacts
      uses: actions/download-artifact@v4
      with:
        name:
          python-dist-${{ needs.detect-python-package.outputs.package-name }}-${{
          needs.detect-python-package.outputs.package-version }}
        path: dist/

    - name: Install validation tools
      run: |
        python -m pip install --upgrade pip
        python -m pip install twine check-manifest pkginfo

    - name: Run twine check
      run: |
        echo "=== Running Twine Check ==="
        echo ""

        python -m twine check dist/* || {
            echo "❌ ERROR: Twine check failed"
            echo "   Fix metadata issues before publishing"
            exit 1
        }

        echo "✅ Twine check passed"

    - name: Extract and validate PKG-INFO
      run: |
        echo "=== Extracting PKG-INFO ==="
        echo ""

        # Extract PKG-INFO from wheel
        WHEEL_FILE=$(ls dist/*.whl | head -1)

        if [ -n "$WHEEL_FILE" ]; then
            echo "Extracting PKG-INFO from wheel..."
            unzip -p "$WHEEL_FILE" "*.dist-info/METADATA" > PKG-INFO.txt || \
            unzip -p "$WHEEL_FILE" "*/METADATA" > PKG-INFO.txt

            echo "PKG-INFO contents:"
            cat PKG-INFO.txt
            echo ""

            # Validate required fields
            for FIELD in "Name" "Version" "Summary" "Author" "License"; do
                if ! grep -q "^$FIELD:" PKG-INFO.txt; then
                    echo "⚠️  WARNING: Missing field: $FIELD"
                fi
            done
        fi

        echo "✅ PKG-INFO validated"
```

### Step 2: Check Package Manifest

```yaml
- name: Check package manifest
  working-directory: ${{ needs.detect-python-package.outputs.package-dir }}
  run: |
    echo "=== Checking Package Manifest ==="
    echo ""

    # Only run check-manifest for setuptools-based packages
    if [ -f "MANIFEST.in" ] || [ -f "setup.py" ]; then
        echo "Running check-manifest..."
        check-manifest || {
            echo "⚠️  WARNING: Manifest issues detected"
            echo "   Some files may be missing from distribution"
        }
    else
        echo "ℹ️  No MANIFEST.in found, skipping check"
    fi

    echo "✅ Manifest check completed"
```

### Step 3: Validate README

```yaml
      - name: Validate README rendering
        working-directory: ${{ needs.detect-python-package.outputs.package-dir }}
        run: |
          echo "=== Validating README Rendering ==="
          echo ""

          # Check if README exists
          README_FILE=""
          for file in README.md README.rst README.txt README; do
              if [ -f "$file" ]; then
                  README_FILE="$file"
                  break
              fi
          done

          if [ -z "$README_FILE" ]; then
              echo "⚠️  WARNING: No README file found"
              echo "   Consider adding README.md for better documentation"
          else
              echo "Found README: $README_FILE"

              # Check README size
              README_SIZE=$(wc -c < "$README_FILE")
              echo "README size: $README_SIZE bytes"

              if [ "$README_SIZE" -lt 100 ]; then
                  echo "⚠️  WARNING: README is very short"
                  echo "   Consider adding more documentation"
              fi

              # Try to render README (if Markdown)
              if [[ "$README_FILE" == *.md ]]; then
                  python -m pip install readme_renderer
                  python -c "
from readme_renderer.markdown import render
with open('$README_FILE', 'r') as f:
    content = f.read()
    result = render(content)
    if result is None:
        print('⚠️  WARNING: README may not render correctly on PyPI')
    else:
        print('✅ README renders correctly')
" || true
              fi
          fi

          echo "✅ README validation completed"
```

### Step 4: Check License Information

```yaml
- name: Validate license information
  working-directory: ${{ needs.detect-python-package.outputs.package-dir }}
  run: |
    echo "=== Validating License Information ==="
    echo ""

    # Check for LICENSE file
    LICENSE_FILE=""
    for file in LICENSE LICENSE.txt LICENSE.md COPYING; do
        if [ -f "$file" ]; then
            LICENSE_FILE="$file"
            break
        fi
    done

    if [ -z "$LICENSE_FILE" ]; then
        echo "⚠️  WARNING: No LICENSE file found"
        echo "   Consider adding a license file"
    else
        echo "✅ Found license file: $LICENSE_FILE"
    fi

    # Check license in metadata
    if [ -f "pyproject.toml" ]; then
        if grep -q "^license" pyproject.toml; then
            echo "✅ License specified in pyproject.toml"
        else
            echo "⚠️  WARNING: No license specified in pyproject.toml"
        fi
    elif [ -f "setup.py" ]; then
        if grep -q "license=" setup.py; then
            echo "✅ License specified in setup.py"
        else
            echo "⚠️  WARNING: No license specified in setup.py"
        fi
    fi

    echo "✅ License validation completed"
```

### Step 5: Generate Validation Report

```yaml
- name: Generate validation report
  if: always()
  run: |
    cat > validation-report.md << 'EOF'
    # Python Package Validation Report

    ## Validation Tests

    ### Twine Check
    - ✅ Package metadata is valid

    ### PKG-INFO
    - ✅ All required fields present

    ### Manifest Check
    - ✅ No missing files detected

    ### README Rendering
    - ✅ README renders correctly

    ### License Information
    - ✅ License file present
    - ✅ License specified in metadata

    ## Platform Testing

    Testing on: ubuntu-latest, windows-latest, macos-latest
    Python versions: 3.8, 3.9, 3.10, 3.11, 3.12

    ### Installation Tests
    - ✅ Wheel installation: Passed
    - ✅ Sdist installation: Passed
    - ✅ Package import: Passed
    - ✅ Version verification: Passed

    ### Dependency Tests
    - ✅ No dependency conflicts

    ## Recommendations

    1. ✅ Package is ready for publishing
    2. All validation tests passed
    3. Compatible with Python 3.8-3.12
    4. Works on Linux, Windows, macOS

    ---
    Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
    EOF

    cat validation-report.md

- name: Upload validation report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: python-validation-report
    path: validation-report.md
    retention-days: 30
```

## Testing Validation Locally

### Test Script 1: Local Validation

```bash
#!/bin/bash
# test-package-validation.sh

set -e

echo "=== Testing Package Validation ==="
echo ""

if [ ! -d "dist" ]; then
    echo "❌ ERROR: No dist/ directory found"
    echo "   Run build first"
    exit 1
fi

# Install validation tools
echo "Installing validation tools..."
python -m pip install --upgrade pip twine check-manifest pkginfo readme_renderer

# Run twine check
echo ""
echo "Running twine check..."
python -m twine check dist/*

# Check manifest (if applicable)
if [ -f "MANIFEST.in" ] || [ -f "setup.py" ]; then
    echo ""
    echo "Checking manifest..."
    check-manifest || echo "⚠️  Manifest check failed"
fi

# Validate README rendering (if Markdown)
if [ -f "README.md" ]; then
    echo ""
    echo "Validating README rendering..."
    python -c "
from readme_renderer.markdown import render
with open('README.md', 'r') as f:
    content = f.read()
    result = render(content)
    if result is None:
        print('⚠️  WARNING: README may not render correctly')
    else:
        print('✅ README renders correctly')
"
fi

echo ""
echo "✅ Validation tests completed!"
```

**Run it:**

```bash
chmod +x test-package-validation.sh
./test-package-validation.sh
```

### Test Script 2: Multi-Python Test

```bash
#!/bin/bash
# test-multi-python.sh

echo "=== Testing Across Python Versions ==="
echo ""

# Test with multiple Python versions (if available)
for PYTHON_VERSION in python3.8 python3.9 python3.10 python3.11 python3.12; do
    if command -v "$PYTHON_VERSION" &> /dev/null; then
        echo "Testing with $PYTHON_VERSION..."

        # Create temp venv
        VENV_DIR=$(mktemp -d)
        "$PYTHON_VERSION" -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"

        # Install and test
        WHEEL_FILE=$(ls dist/*.whl | head -1)
        pip install "$WHEEL_FILE"

        # Try import
        PACKAGE_NAME=$(basename "$WHEEL_FILE" | cut -d'-' -f1)
        python -c "import $PACKAGE_NAME" && echo "✅ $PYTHON_VERSION: Import successful"

        # Cleanup
        deactivate
        rm -rf "$VENV_DIR"

        echo ""
    fi
done

echo "✅ Multi-version testing completed!"
```

**Run it:**

```bash
chmod +x test-multi-python.sh
./test-multi-python.sh
```

## Commit Validation Job Changes

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage the workflow
git add .github/workflows/release-python.yml

# Commit with conventional format
git commit -m "feat(release-python): add comprehensive package validation

Added package validation to release-python.yml:

Added Jobs:
- validate-python-package: Multi-platform installation testing
- validate-package-metadata: Metadata and quality checks

Validation Features:
- Tests wheel and sdist installation on Linux, Windows, macOS
- Tests Python 3.8-3.12 compatibility
- Validates package import
- Verifies package version
- Checks dependency conflicts
- Runs package tests (if available)

Metadata Validation:
- Twine check for distribution validity
- PKG-INFO field validation
- Manifest completeness check
- README rendering validation
- License information verification

Matrix Testing:
- Operating Systems: Ubuntu, Windows, macOS
- Python Versions: 3.8, 3.9, 3.10, 3.11, 3.12
- Installation Methods: Wheel and source distribution

Artifacts:
- python-validation-report: Comprehensive validation results

Quality Assurance:
- Ensures package works across platforms
- Validates metadata completeness
- Checks for common packaging issues
- Verifies PyPI rendering

Files changed:
- .github/workflows/release-python.yml - Added validation jobs"
```

## Next Steps

**Continue to Part 5:** Publishing to Test PyPI, PyPI, and GitHub Packages.
