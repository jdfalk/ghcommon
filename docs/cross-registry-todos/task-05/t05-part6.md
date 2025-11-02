<!-- file: docs/cross-registry-todos/task-05/t05-part6.md -->
<!-- version: 1.0.0 -->
<!-- guid: t05-python-packages-part6-i0j1k2l3-m4n5 -->

# Task 05 Part 6: Documentation and Final Steps

## Stage 1: Configure PyPI Credentials

### Step 1: Generate PyPI API Tokens

#### For Production PyPI

1. **Go to PyPI Account Settings:**
   - Visit: <https://pypi.org/manage/account/>
   - Login with your PyPI account

2. **Create API Token:**
   - Scroll to "API tokens" section
   - Click "Add API token"
   - Token name: `ghcommon-release-workflow`
   - Scope: Choose specific project after first upload, or "Entire account (all projects)"
   - Click "Add token"
   - **CRITICAL**: Copy the token immediately (starts with `pypi-`)

3. **Add to GitHub Secrets:**
   ```bash
   # In GitHub repository:
   # Settings → Secrets and variables → Actions → New repository secret
   # Name: PYPI_API_TOKEN
   # Value: [paste the token]
   ```

#### For Test PyPI

1. **Go to Test PyPI Account Settings:**
   - Visit: <https://test.pypi.org/manage/account/>
   - Create account if needed (separate from production PyPI)

2. **Create API Token:**
   - Scroll to "API tokens" section
   - Click "Add API token"
   - Token name: `ghcommon-test-workflow`
   - Scope: "Entire account (all projects)"
   - Click "Add token"
   - **CRITICAL**: Copy the token immediately

3. **Add to GitHub Secrets:**
   ```bash
   # Name: TEST_PYPI_API_TOKEN
   # Value: [paste the token]
   ```

### Step 2: Configure GitHub Environments

```bash
# In GitHub repository:
# Settings → Environments

# Create three environments:
# 1. test-pypi
#    - Add protection rules (optional)
#    - Add TEST_PYPI_API_TOKEN as environment secret
#
# 2. pypi
#    - Add protection rules: Require approval for production
#    - Add PYPI_API_TOKEN as environment secret
#    - Limit to protected branches: main, master
#
# 3. github-packages
#    - Uses GITHUB_TOKEN (automatic)
#    - No additional secrets needed
```

### Step 3: Enable Trusted Publishing (Recommended)

Trusted Publishing eliminates the need for API tokens by using OIDC.

#### For PyPI

1. **Register GitHub Actions Publisher:**
   - Visit: <https://pypi.org/manage/account/publishing/>
   - Click "Add a new publisher"
   - Fill in:
     - Repository owner: `jdfalk`
     - Repository name: `ghcommon`
     - Workflow name: `release-python.yml`
     - Environment name: `pypi`
   - Click "Add"

2. **Update Workflow (if using trusted publishing):**
   ```yaml
   # Remove password parameter, add trusted publishing
   - name: Publish to PyPI
     uses: pypa/gh-action-pypi-publish@release/v1
     # No password needed with trusted publishing!
   ```

## Stage 2: Update Repository Documentation

### Step 1: Create Python Package Documentation

````bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Create documentation file
cat > docs/python-package-publishing.md << 'EOF'
<!-- file: docs/python-package-publishing.md -->
<!-- version: 1.0.0 -->
<!-- guid: python-pkg-docs-j1k2l3m4-n5o6 -->

# Python Package Publishing Guide

## Overview

This repository automatically publishes Python packages to:
- PyPI (production)
- Test PyPI (testing)
- GitHub Packages
- GitHub Releases

## Requirements

### Package Configuration

Your Python package must have one of:
- `pyproject.toml` (recommended)
- `setup.py`
- `setup.cfg`

### Supported Build Systems

- **Poetry**: Dependency management and building
- **setuptools**: Traditional and modern (PEP 517/518)
- **Flit**: Simple building for pure-Python packages
- **Hatch**: Modern project management

### Version Management

Package version must match Git tag:
- Git tag: `v1.2.3`
- Package version: `1.2.3`

## Publishing Workflow

### Automatic Publishing

1. **Create Git Tag:**
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
````

2. **Workflow Runs Automatically:**
   - Detects Python package
   - Builds wheel and sdist
   - Validates on multiple platforms
   - Publishes to registries

### Manual Publishing

Trigger workflow manually:

```bash
# Using GitHub CLI
gh workflow run release-python.yml \
  -f tag=v1.2.3 \
  -f publish_to_pypi=true
```

## Configuration

### Enable/Disable Registries

In `.github/workflows/release-python.yml`:

```yaml
env:
  PUBLISH_TO_PYPI: 'true' # Publish to PyPI
  PUBLISH_TO_TEST_PYPI: 'true' # Publish to Test PyPI
  PUBLISH_TO_GITHUB_PACKAGES: 'true' # Publish to GitHub Packages
```

### Secrets Required

| Secret                | Purpose              | Where to Get                            |
| --------------------- | -------------------- | --------------------------------------- |
| `PYPI_API_TOKEN`      | PyPI publishing      | <https://pypi.org/manage/account/>      |
| `TEST_PYPI_API_TOKEN` | Test PyPI publishing | <https://test.pypi.org/manage/account/> |

## Installation

### From PyPI

```bash
pip install your-package-name
```

### From Test PyPI

```bash
pip install --index-url https://test.pypi.org/simple/ your-package-name
```

### From GitHub Packages

```bash
pip install --extra-index-url https://pypi.pkg.github.com/jdfalk your-package-name
```

### From GitHub Release

```bash
pip install https://github.com/jdfalk/ghcommon/releases/download/v1.2.3/your-package-1.2.3-py3-none-any.whl
```

## Troubleshooting

See [Troubleshooting Guide](#troubleshooting-guide) below.

---

For more information, see:

- [PyPI Documentation](https://packaging.python.org/)
- [Python Packaging Guide](https://packaging.python.org/guides/)
- [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) EOF

````

### Step 2: Update Main README

```bash
# Add Python package section to README.md
cat >> README.md << 'EOF'

## Python Package Publishing

This repository includes automated Python package publishing to PyPI and GitHub Packages.

For details, see:
- [Python Package Publishing Guide](docs/python-package-publishing.md)
- [Release Workflow](.github/workflows/release-python.yml)

### Quick Start

1. Tag a release:
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
````

2. Workflow automatically:
   - Builds wheel and sdist
   - Validates on multiple platforms (Linux, Windows, macOS)
   - Tests with Python 3.8-3.12
   - Publishes to PyPI
   - Creates GitHub Release

### Installation

```bash
pip install your-package-name
```

EOF

````

## Stage 3: Troubleshooting Guide

### Problem 1: Package Not Detected

**Symptom:** Workflow shows "No Python package configuration found"

**Solutions:**

1. **Check for configuration files:**
   ```bash
   # Must have one of these
   ls -la setup.py setup.cfg pyproject.toml
````

2. **Verify pyproject.toml format:**

   ```toml
   # For Poetry
   [tool.poetry]
   name = "your-package"
   version = "1.2.3"

   # For modern setuptools
   [project]
   name = "your-package"
   version = "1.2.3"

   # For Flit/Hatch
   [project]
   name = "your-package"
   version = "1.2.3"
   ```

3. **Check setup.py format:**

   ```python
   from setuptools import setup

   setup(
       name="your-package",
       version="1.2.3",
       # ... other config
   )
   ```

### Problem 2: Build Fails

**Symptom:** "ERROR: Could not build wheels for your-package"

**Solutions:**

1. **Missing dependencies:**

   ```bash
   # Add build dependencies to pyproject.toml
   [build-system]
   requires = ["setuptools>=61.0", "wheel"]
   build-backend = "setuptools.build_meta"
   ```

2. **Test build locally:**

   ```bash
   python -m pip install build
   python -m build
   ```

3. **Check for C extensions:**
   ```python
   # If you have C extensions, ensure build tools are available
   # May need to add setup-python action with build dependencies
   ```

### Problem 3: Version Mismatch

**Symptom:** "WARNING: Version mismatch"

**Solutions:**

1. **Synchronize versions:**

   ```bash
   # Git tag: v1.2.3
   # Package version must be: 1.2.3 (without 'v')
   ```

2. **Use dynamic versioning:**

   ```toml
   # pyproject.toml
   [project]
   name = "your-package"
   dynamic = ["version"]

   [tool.setuptools.dynamic]
   version = {attr = "your_package.__version__"}
   ```

3. **Use setuptools_scm:**

   ```toml
   [build-system]
   requires = ["setuptools>=64", "setuptools-scm>=8"]

   [tool.setuptools_scm]
   # Version from git tags automatically
   ```

### Problem 4: PyPI Upload Fails

**Symptom:** "HTTPError: 403 Forbidden"

**Solutions:**

1. **Check API token:**

   ```bash
   # Verify secret is set correctly
   # GitHub Settings → Secrets → PYPI_API_TOKEN
   # Token should start with: pypi-
   ```

2. **Check token scope:**
   - Token must have "upload" permission
   - For first upload, use "Entire account" scope
   - After first upload, can limit to specific project

3. **Version already exists:**
   ```yaml
   # Workflow uses skip-existing by default
   # To force new version, update version number
   ```

### Problem 5: Test PyPI Works, Production Fails

**Symptom:** Publishes to Test PyPI but fails on PyPI

**Solutions:**

1. **Register project on PyPI first:**

   ```bash
   # Do manual first upload
   twine upload dist/*
   ```

2. **Check package name availability:**
   - Visit <https://pypi.org/project/your-package-name/>
   - Name may be taken
   - Choose unique name

3. **Enable production publishing:**
   ```yaml
   # In workflow file
   env:
     PUBLISH_TO_PYPI: 'true' # Must be "true" string
   ```

### Problem 6: Metadata Validation Fails

**Symptom:** "twine check failed"

**Solutions:**

1. **Add required metadata:**

   ```toml
   [project]
   name = "your-package"
   version = "1.2.3"
   description = "Short description"
   authors = [{name = "Your Name", email = "you@example.com"}]
   license = {text = "MIT"}
   readme = "README.md"
   requires-python = ">=3.8"
   ```

2. **Fix README rendering:**

   ```bash
   # Test README rendering locally
   pip install readme-renderer
   python -c "from readme_renderer.markdown import render; \
              print(render(open('README.md').read()))"
   ```

3. **Check long_description:**

   ```python
   # In setup.py
   with open("README.md", "r") as fh:
       long_description = fh.read()

   setup(
       long_description=long_description,
       long_description_content_type="text/markdown",
   )
   ```

### Problem 7: Multi-Platform Build Issues

**Symptom:** Build works on Linux, fails on Windows/macOS

**Solutions:**

1. **Use pure Python when possible:**

   ```toml
   # Avoid platform-specific dependencies
   # Or provide wheels for each platform
   ```

2. **Test locally on each platform:**

   ```bash
   # Use GitHub Actions matrix locally
   # Or use docker/VM for testing
   ```

3. **Add platform-specific dependencies:**

   ```toml
   [project]
   dependencies = [
       "universal-package",
   ]

   [project.optional-dependencies]
   windows = ["windows-specific-package ; sys_platform=='win32'"]
   ```

## Stage 4: Testing the Complete Workflow

### Test Plan

```bash
#!/bin/bash
# complete-workflow-test.sh

set -e

echo "=== Complete Python Package Publishing Test ==="
echo ""

# 1. Clean workspace
echo "1. Cleaning workspace..."
rm -rf dist/ build/ *.egg-info

# 2. Run detection
echo ""
echo "2. Testing package detection..."
./test-python-detection.sh

# 3. Build package
echo ""
echo "3. Testing package build..."
./test-python-build.sh

# 4. Validate package
echo ""
echo "4. Testing package validation..."
./test-package-validation.sh

# 5. Test installation
echo ""
echo "5. Testing local installation..."
./test-local-install.sh

# 6. Test PyPI upload (dry run)
echo ""
echo "6. Testing PyPI upload configuration..."
./test-pypi-upload-dry-run.sh

echo ""
echo "✅ All tests passed!"
echo ""
echo "Ready to publish:"
echo "  git tag v1.2.3"
echo "  git push origin v1.2.3"
```

**Run it:**

```bash
chmod +x complete-workflow-test.sh
./complete-workflow-test.sh
```

## Stage 5: Completion Checklist

### Pre-Publishing Checklist

- [ ] Package configuration file exists (`pyproject.toml` or `setup.py`)
- [ ] Package metadata is complete (name, version, description, author, license)
- [ ] README.md exists and renders correctly
- [ ] LICENSE file exists
- [ ] Package builds successfully locally
- [ ] Package installs successfully from wheel
- [ ] Package installs successfully from sdist
- [ ] Package imports successfully
- [ ] Tests pass (if any)
- [ ] Version in code matches Git tag
- [ ] PyPI API token is configured in GitHub Secrets
- [ ] Test PyPI API token is configured (optional but recommended)

### Publishing Checklist

- [ ] Create and push Git tag: `v1.2.3`
- [ ] Workflow runs successfully
- [ ] Package detected correctly
- [ ] Build artifacts generated (wheel + sdist)
- [ ] Validation passes on all platforms
- [ ] Published to Test PyPI (optional)
- [ ] Published to PyPI
- [ ] Published to GitHub Packages (optional)
- [ ] GitHub Release created with packages attached
- [ ] Package installable from PyPI

### Post-Publishing Checklist

- [ ] Verify package on PyPI: <https://pypi.org/project/your-package/>
- [ ] Test installation: `pip install your-package`
- [ ] Verify package version: `pip show your-package`
- [ ] Test package functionality
- [ ] Update documentation with new version
- [ ] Announce release (if appropriate)
- [ ] Monitor PyPI download stats
- [ ] Monitor GitHub issue tracker for bug reports

## Stage 6: Maintenance and Updates

### Updating the Package

1. **Make changes to code**
2. **Update version number:**
   - In `pyproject.toml` or `setup.py`
   - Update CHANGELOG.md
3. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```
4. **Create new tag:**
   ```bash
   git tag v1.2.4
   git push origin v1.2.4
   ```
5. **Workflow runs automatically**

### Yanking a Release

If you published a broken version:

```bash
# On PyPI web interface:
# 1. Go to https://pypi.org/project/your-package/
# 2. Click on the version
# 3. Click "Options" → "Yank release"
# 4. Provide reason for yanking

# Then publish fixed version:
git tag v1.2.5
git push origin v1.2.5
```

### Deleting Old Distributions

PyPI keeps all versions indefinitely. To manage:

```bash
# PyPI policy: Cannot delete versions
# Can only "yank" (hide but keep downloadable by version)
# Best practice: Publish new version instead
```

## Reference Materials

### Useful Commands

```bash
# Check package metadata
python -m pip show your-package

# List package files
python -m pip show -f your-package

# Search PyPI
pip search your-package  # Note: Currently disabled by PyPI

# List installed packages
pip list

# Show package info without installing
pip index versions your-package

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ your-package

# Uninstall package
pip uninstall your-package

# Build package locally
python -m build

# Check distribution files
twine check dist/*

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

### Additional Resources

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [setuptools Documentation](https://setuptools.pypa.io/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Flit Documentation](https://flit.pypa.io/)
- [Hatch Documentation](https://hatch.pypa.io/)
- [PEP 517 - Build System Interface](https://peps.python.org/pep-0517/)
- [PEP 518 - Dependency Specification](https://peps.python.org/pep-0518/)
- [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)
- [PEP 440 - Version Identification](https://peps.python.org/pep-0440/)
- [Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)

## Summary

You have now completed Task 05: Python Package Publishing to PyPI and GitHub Packages!

**What was accomplished:**

1. ✅ Added Python package detection with build system identification
2. ✅ Implemented multi-build-system support (Poetry, setuptools, Flit, Hatch)
3. ✅ Added package building with wheel and sdist generation
4. ✅ Implemented comprehensive validation across platforms and Python versions
5. ✅ Added publishing to Test PyPI, PyPI, and GitHub Packages
6. ✅ Created GitHub Releases with packages attached
7. ✅ Generated installation instructions and publishing summaries
8. ✅ Documented complete workflow with troubleshooting guide

**Files modified:**

- `.github/workflows/release-python.yml` - Complete Python package publishing workflow

**New capabilities:**

- Automatic Python package detection
- Multi-build-system support
- Cross-platform validation
- Multi-registry publishing
- Comprehensive reporting and documentation

**Ready for:**

- Publishing Python packages from this repository
- Testing package publishing workflow
- Distributing packages to users via PyPI

**Next task:** Task 06 - Frontend Package Publishing to npm and GitHub Packages
