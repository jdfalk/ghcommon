<!-- file: docs/cross-registry-todos/task-05/t05-part1.md -->
<!-- version: 1.0.0 -->
<!-- guid: t05-python-packages-part1-d5e6f7a8-b9c0 -->

# Task 05: Add Python Package Publishing to GitHub Packages

## Task Overview

**What**: Implement Python package publishing to PyPI and GitHub Package Registry in
release-python.yml

**Why**: Python packages are currently built but not published to any package registry, making it
difficult for users to install and use the Python code via pip

**Where**: `ghcommon` repository, file `.github/workflows/release-python.yml`

**Expected Outcome**:

- Python packages automatically published to PyPI and/or GitHub Packages
- Support for multiple build systems (Poetry, setuptools, pyproject.toml)
- Wheel and source distributions (sdist) generated
- Package metadata validated before publishing
- Version tags properly synchronized

**Estimated Time**: 90-120 minutes

**Risk Level**: Medium (modifying release workflow, affects package consumers)

## Prerequisites

### Required Access

- Write access to `jdfalk/ghcommon` repository
- Ability to create and push Git tags
- Permission to publish packages to GitHub Packages
- (Optional) PyPI API token for publishing to PyPI

### Required Tools

```bash
# Verify these are installed locally
python3 --version     # Python 3.8 or later
pip --version         # Package installer
git --version         # Any recent version
gh --version          # GitHub CLI

# Python packaging tools
pip install --upgrade pip setuptools wheel
pip install --upgrade build twine poetry

# Optional: for testing
docker --version      # For container-based testing
```

### Knowledge Requirements

- **Python Packaging**: Understanding of setup.py, pyproject.toml, wheel, sdist
- **Semantic Versioning**: Major.Minor.Patch versioning scheme
- **PyPI and GitHub Packages**: How Python package registries work
- **Build Systems**: Poetry, setuptools, flit, hatchling
- **GitHub Actions**: Workflow syntax and job dependencies
- **Virtual Environments**: venv, virtualenv concepts

### Background Reading

Essential reading before starting:

1. **Python Packaging**
   - [Python Packaging User Guide](https://packaging.python.org/)
   - [Building and Distributing Packages](https://packaging.python.org/tutorials/packaging-projects/)
   - [pyproject.toml specification](https://peps.python.org/pep-0621/)

2. **GitHub Packages for Python**
   - [Working with Python registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-python-registry)
   - [Publishing a package](https://docs.github.com/en/packages/learn-github-packages/publishing-a-package)

3. **PyPI Publishing**
   - [Uploading to PyPI](https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives)
   - [Using TestPyPI](https://packaging.python.org/guides/using-testpypi/)
   - [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)

### Understanding Python Package Publishing

Python has evolved through several packaging systems:

**Build Systems (Choose One):**

1. **setuptools** (traditional, widely supported)
   - Uses setup.py or pyproject.toml
   - Most compatible with legacy projects
   - Well-documented and stable

2. **Poetry** (modern, dependency management)
   - Uses pyproject.toml exclusively
   - Integrated dependency resolver
   - Lock file for reproducible builds

3. **Flit** (simple, PEP 517 compliant)
   - Minimal configuration
   - Uses pyproject.toml
   - Good for pure Python packages

4. **Hatchling** (modern, extensible)
   - Part of Hatch project management tool
   - PEP 517 compliant
   - Plugin system

**For This Task:**

We'll implement support for ALL major build systems:

- ✅ Auto-detect build system from project files
- ✅ Use appropriate build commands
- ✅ Generate both wheel and sdist
- ✅ Validate package before publishing

## Current State Analysis

### Step 1: Review Current release-python.yml Workflow

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# View the workflow
cat .github/workflows/release-python.yml | less

# Count lines
wc -l .github/workflows/release-python.yml
```

**Expected**: ~300-400 lines

### Step 2: Identify Current Capabilities

```bash
# Check what the workflow currently does
grep -n "^  [a-z-]*:" .github/workflows/release-python.yml
```

**Current jobs should include:**

```text
test-python:          # Run tests
build-python:         # Build package (maybe)
```

### Step 3: Check for Existing Publishing Steps

```bash
# Search for any existing publishing
grep -i "publish\|twine\|pypi\|upload.*package" .github/workflows/release-python.yml

# Expected: minimal or no matches
```

### Step 4: Analyze What's Missing

Current workflow likely includes:

- ✅ Python environment setup
- ✅ Dependency installation
- ✅ Test execution
- ✅ Coverage reporting
- ❌ **MISSING: Package building**
- ❌ **MISSING: Build system detection**
- ❌ **MISSING: Package validation**
- ❌ **MISSING: PyPI publishing**
- ❌ **MISSING: GitHub Packages publishing**
- ❌ **MISSING: Version synchronization**

### Step 5: Check Repository for Python Packages

```bash
# Find Python package configurations
find /Users/jdfalk/repos/github.com/jdfalk -name "setup.py" -o -name "pyproject.toml" 2>/dev/null

# For each Python project, check configuration
for dir in $(find /Users/jdfalk/repos/github.com/jdfalk -name "setup.py" -exec dirname {} \;); do
    echo "=== $dir ==="
    if [ -f "$dir/setup.py" ]; then
        echo "Build system: setuptools (setup.py)"
    fi
    if [ -f "$dir/pyproject.toml" ]; then
        echo "Has pyproject.toml"
        grep -E "^\[tool\.(poetry|flit|hatch)" "$dir/pyproject.toml" || echo "Uses setuptools"
    fi
    echo ""
done
```

### Step 6: Understand Python Package Structure

A valid Python package needs:

**Option 1: setuptools with setup.py**

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="package-name",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'dependency>=1.0',
    ],
)
```

**Option 2: setuptools with pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "package-name"
version = "1.0.0"
dependencies = [
    "dependency>=1.0",
]
```

**Option 3: Poetry**

```toml
[tool.poetry]
name = "package-name"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.8"
dependency = "^1.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### Step 7: Check Current Versioning Strategy

```bash
# List recent tags
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon
git tag -l | tail -10

# Check for Python version files
find . -name "__version__.py" -o -name "_version.py" -o -name "version.py" 2>/dev/null
```

### Step 8: Test Local Package Building

If a Python package exists:

```bash
# Navigate to Python package directory
cd path/to/python/package

# Try building with python -m build
python -m build

# Check if dist/ directory created
ls -la dist/

# Expected: .whl and .tar.gz files
```

**If build fails**: Note the error - we'll handle it in validation

### Decision Point

**Proceed if:**

- ✅ You understand Python packaging ecosystem
- ✅ At least one repository has Python package configuration
- ✅ You can create and push Git tags
- ✅ You understand wheel vs sdist distributions

**Stop and prepare if:**

- ❌ No Python packages found (create setup.py/pyproject.toml first)
- ❌ Unclear about build systems (read background material)
- ❌ Don't have permissions to publish packages
- ❌ Version management strategy unclear

## Python Package Publishing Architecture

### Publishing Strategy Overview

We'll implement a multi-registry strategy:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Release Workflow                          │
│                                                              │
│  1. Test Python code (existing)                             │
│  2. ┌─────────────────────────────────────┐                │
│     │  NEW: Detect Build System           │                │
│     │  - Check for Poetry                 │                │
│     │  - Check for setuptools             │                │
│     │  - Check for Flit/Hatch             │                │
│     │  - Determine build commands         │                │
│     └─────────────────────────────────────┘                │
│  3. ┌─────────────────────────────────────┐                │
│     │  NEW: Build Package                 │                │
│     │  - Run appropriate build command    │                │
│     │  - Generate wheel (.whl)            │                │
│     │  - Generate source dist (.tar.gz)   │                │
│     │  - Validate distributions           │                │
│     └─────────────────────────────────────┘                │
│  4. ┌─────────────────────────────────────┐                │
│     │  NEW: Validate Package              │                │
│     │  - Check metadata                   │                │
│     │  - Verify version format            │                │
│     │  - Test installation                │                │
│     │  - Run package checks               │                │
│     └─────────────────────────────────────┘                │
│  5. ┌─────────────────────────────────────┐                │
│     │  NEW: Publish to PyPI               │                │
│     │  (Optional - requires token)        │                │
│     │  - Upload to TestPyPI first         │                │
│     │  - Validate TestPyPI installation   │                │
│     │  - Upload to production PyPI        │                │
│     └─────────────────────────────────────┘                │
│  6. ┌─────────────────────────────────────┐                │
│     │  NEW: Publish to GitHub Packages    │                │
│     │  - Upload distributions             │                │
│     │  - Create package version           │                │
│     │  - Update package metadata          │                │
│     └─────────────────────────────────────┘                │
│  7. Create GitHub Release (existing)                        │
│  8. Attach distributions to release (new)                   │
└─────────────────────────────────────────────────────────────┘
```

### Publishing Targets

#### Target 1: PyPI (Python Package Index)

**Purpose**: Public Python package repository

**Advantages:**

- ✅ Default pip install source
- ✅ Widest reach for public packages
- ✅ Automatic package discovery
- ✅ Free for open source

**Requirements:**

- PyPI account and API token
- Package name must be unique globally
- Metadata must be valid

**Installation:**

```bash
pip install package-name
```

#### Target 2: TestPyPI

**Purpose**: Testing environment for PyPI

**Advantages:**

- ✅ Test publishing without affecting production
- ✅ Validate package metadata
- ✅ Practice release process
- ✅ Free and isolated

**Usage:**

```bash
pip install --index-url https://test.pypi.org/simple/ package-name
```

#### Target 3: GitHub Packages

**Purpose**: GitHub-hosted package registry

**Advantages:**

- ✅ Integrated with GitHub
- ✅ Private package support
- ✅ Same authentication as GitHub
- ✅ Enterprise-friendly

**Requirements:**

- GitHub authentication
- Package name scoped to repository

**Installation:**

```bash
pip install --index-url https://pypi.pkg.github.com/jdfalk/simple/ package-name
```

### Build System Detection Strategy

**Detection Order:**

1. **Poetry** (if `poetry.lock` exists or `[tool.poetry]` in pyproject.toml)
2. **Flit** (if `[tool.flit]` in pyproject.toml)
3. **Hatchling** (if `[tool.hatch]` in pyproject.toml)
4. **Setuptools** (if `setup.py` exists or default in pyproject.toml)

**Detection Logic:**

```bash
# Check for Poetry
if [ -f "poetry.lock" ] || grep -q "^\[tool\.poetry\]" pyproject.toml 2>/dev/null; then
    BUILD_SYSTEM="poetry"
    BUILD_CMD="poetry build"

# Check for Flit
elif grep -q "^\[tool\.flit" pyproject.toml 2>/dev/null; then
    BUILD_SYSTEM="flit"
    BUILD_CMD="python -m build"

# Check for Hatch
elif grep -q "^\[tool\.hatch" pyproject.toml 2>/dev/null; then
    BUILD_SYSTEM="hatch"
    BUILD_CMD="python -m build"

# Check for setuptools with setup.py
elif [ -f "setup.py" ]; then
    BUILD_SYSTEM="setuptools"
    BUILD_CMD="python -m build"

# Check for setuptools with pyproject.toml
elif [ -f "pyproject.toml" ]; then
    BUILD_SYSTEM="setuptools"
    BUILD_CMD="python -m build"

else
    echo "No Python package configuration found"
    exit 1
fi
```

### Version Detection Strategy

**Source Priority:**

1. **Git Tag** (highest priority)
   - Extract from `refs/tags/v1.2.3` → version `1.2.3`

2. **pyproject.toml** or **setup.py**
   - Read version from package configuration

3. ****version**.py**
   - Read from version module

**Version Synchronization:**

```python
# Option 1: Dynamic versioning (recommended)
# Read version from Git tag at build time

# Option 2: Static versioning
# Update version in source files before tagging
```

### Package Validation Strategy

**Pre-Publishing Checks:**

1. **Metadata Validation**
   - Check package name, version, author
   - Verify dependencies are valid
   - Ensure README exists

2. **Distribution Validation**
   - Verify wheel is valid
   - Check sdist completeness
   - Test installation in clean environment

3. **Content Validation**
   - Check all required files included
   - Verify no sensitive data included
   - Ensure license file present

4. **Version Validation**
   - Confirm version not already published
   - Check version format (PEP 440)
   - Verify version tag matches package version

## Implementation Design

### New Jobs to Add

We'll add three new jobs to `release-python.yml`:

```yaml
detect-python-package:
  name: Detect Python Package
  runs-on: ubuntu-latest
  outputs:
    has-package: ${{ steps.detect.outputs.has-package }}
    build-system: ${{ steps.detect.outputs.build-system }}
    package-name: ${{ steps.detect.outputs.package-name }}
    package-version: ${{ steps.detect.outputs.package-version }}

build-python-package:
  name: Build Python Package
  needs: detect-python-package
  runs-on: ubuntu-latest
  outputs:
    wheel-name: ${{ steps.build.outputs.wheel-name }}
    sdist-name: ${{ steps.build.outputs.sdist-name }}

validate-python-package:
  name: Validate Python Package
  needs: build-python-package
  runs-on: ubuntu-latest
  outputs:
    is-valid: ${{ steps.validation.outputs.is-valid }}

publish-python-package:
  name: Publish Python Package
  needs: [build-python-package, validate-python-package]
  runs-on: ubuntu-latest
  # Publishing steps...
```

### Job Dependency Flow

```text
test-python (existing)
    ↓
detect-python-package
    ↓
build-python-package
    ↓
validate-python-package
    ↓
publish-python-package
    ├─→ PyPI (optional)
    └─→ GitHub Packages
```

### Environment Variables Strategy

```yaml
env:
  # Package registry configuration
  PYPI_REGISTRY: 'https://upload.pypi.org/legacy/'
  TEST_PYPI_REGISTRY: 'https://test.pypi.org/legacy/'
  GITHUB_PACKAGES_REGISTRY: 'https://pypi.pkg.github.com/'

  # Build configuration
  PYTHON_VERSION: '3.11'
  BUILD_ISOLATION: 'true'

  # Publishing configuration
  PUBLISH_TO_PYPI: 'false' # Set to true when ready
  PUBLISH_TO_TEST_PYPI: 'true' # Test first
  PUBLISH_TO_GITHUB_PACKAGES: 'true'
```

### Permissions Required

```yaml
permissions:
  contents: write # For creating releases
  packages: write # For publishing to GitHub Packages
  id-token: write # For trusted publishing (PyPI)
```

## Implementation Steps Overview

We'll implement this in several stages:

### Stage 1: Update Workflow Header and Environment (Part 2)

- Update version number
- Add environment variables
- Update permissions
- Configure registries

### Stage 2: Add Package Detection Job (Part 3)

- Detect build system
- Extract package metadata
- Determine build commands
- Output package information

### Stage 3: Add Package Building Job (Part 4)

- Install build dependencies
- Run build commands
- Generate wheel and sdist
- Upload build artifacts

### Stage 4: Add Package Validation Job (Part 5)

- Validate package metadata
- Test installation
- Check package contents
- Verify version consistency

### Stage 5: Add Publishing Jobs (Part 6)

- Publish to TestPyPI (optional)
- Publish to PyPI (optional)
- Publish to GitHub Packages
- Attach to GitHub Release

### Stage 6: Testing and Documentation (Part 6)

- Local testing procedures
- Integration testing
- User documentation
- Troubleshooting guide

Each stage is detailed in the subsequent parts of this task.
