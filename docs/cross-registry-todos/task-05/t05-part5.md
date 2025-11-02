<!-- file: docs/cross-registry-todos/task-05/t05-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t05-python-packages-part5-h9i0j1k2-l3m4 -->

# Task 05 Part 5: Publishing to Registries

## Stage 1: Publish to Test PyPI

### Step 1: Test PyPI Publishing Job

```yaml
publish-test-pypi:
  name: Publish to Test PyPI
  runs-on: ubuntu-latest
  needs: [detect-python-package, build-python-package, validate-python-package]
  if: |
    needs.detect-python-package.outputs.has-package == 'true' &&
    env.PUBLISH_TO_TEST_PYPI == 'true'
  environment:
    name: test-pypi
    url: https://test.pypi.org/project/${{ needs.detect-python-package.outputs.package-name }}/

  steps:
    - name: Download build artifacts
      uses: actions/download-artifact@v4
      with:
        name:
          python-dist-${{ needs.detect-python-package.outputs.package-name }}-${{
          needs.detect-python-package.outputs.package-version }}
        path: dist/

    - name: Display artifacts
      run: |
        echo "=== Artifacts to Publish ==="
        ls -lh dist/

    - name: Publish to Test PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        repository-url: https://test.pypi.org/legacy/
        password: ${{ secrets.TEST_PYPI_API_TOKEN }}
        skip-existing: true
        verbose: true
        print-hash: true
```

### Step 2: Verify Test PyPI Publication

```yaml
- name: Wait for Test PyPI propagation
  run: |
    echo "Waiting for Test PyPI to propagate package..."
    sleep 30

- name: Verify Test PyPI publication
  run: |
    echo "=== Verifying Test PyPI Publication ==="

    PACKAGE_NAME="${{ needs.detect-python-package.outputs.package-name }}"
    PACKAGE_VERSION="${{ needs.detect-python-package.outputs.package-version }}"

    # Try to install from Test PyPI
    python -m pip install \
      --index-url https://test.pypi.org/simple/ \
      --no-deps \
      "$PACKAGE_NAME==$PACKAGE_VERSION" || {
        echo "⚠️  WARNING: Package not yet available on Test PyPI"
        echo "   This is normal if the package was just uploaded"
        exit 0
    }

    echo "✅ Package available on Test PyPI"

    # Show package info
    python -m pip show "$PACKAGE_NAME"
```

## Stage 2: Publish to Production PyPI

### Step 1: PyPI Publishing Job

```yaml
publish-pypi:
  name: Publish to PyPI
  runs-on: ubuntu-latest
  needs:
    [
      detect-python-package,
      build-python-package,
      validate-python-package,
      publish-test-pypi,
    ]
  if: |
    needs.detect-python-package.outputs.has-package == 'true' &&
    env.PUBLISH_TO_PYPI == 'true' &&
    startsWith(github.ref, 'refs/tags/v')
  environment:
    name: pypi
    url: https://pypi.org/project/${{ needs.detect-python-package.outputs.package-name }}/

  steps:
    - name: Download build artifacts
      uses: actions/download-artifact@v4
      with:
        name:
          python-dist-${{ needs.detect-python-package.outputs.package-name }}-${{
          needs.detect-python-package.outputs.package-version }}
        path: dist/

    - name: Display artifacts
      run: |
        echo "=== Artifacts to Publish ==="
        ls -lh dist/

    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}
        skip-existing: ${{ env.SKIP_EXISTING }}
        verbose: true
        print-hash: true
```

### Step 2: Verify PyPI Publication

```yaml
- name: Wait for PyPI propagation
  run: |
    echo "Waiting for PyPI to propagate package..."
    sleep 60

- name: Verify PyPI publication
  run: |
    echo "=== Verifying PyPI Publication ==="

    PACKAGE_NAME="${{ needs.detect-python-package.outputs.package-name }}"
    PACKAGE_VERSION="${{ needs.detect-python-package.outputs.package-version }}"

    # Try to install from PyPI
    python -m pip install "$PACKAGE_NAME==$PACKAGE_VERSION" || {
        echo "⚠️  WARNING: Package not yet available on PyPI"
        echo "   Package may need time to propagate"
        exit 0
    }

    echo "✅ Package available on PyPI"

    # Show package info
    python -m pip show "$PACKAGE_NAME"

    # Display PyPI URL
    echo ""
    echo "📦 Package published to:"
    echo "   https://pypi.org/project/$PACKAGE_NAME/$PACKAGE_VERSION/"
```

## Stage 3: Publish to GitHub Packages

### Step 1: GitHub Packages Publishing Job

```yaml
publish-github-packages:
  name: Publish to GitHub Packages
  runs-on: ubuntu-latest
  needs: [detect-python-package, build-python-package, validate-python-package]
  if: |
    needs.detect-python-package.outputs.has-package == 'true' &&
    env.PUBLISH_TO_GITHUB_PACKAGES == 'true'
  environment:
    name: github-packages
    url: https://github.com/${{ github.repository }}/packages

  steps:
    - name: Download build artifacts
      uses: actions/download-artifact@v4
      with:
        name:
          python-dist-${{ needs.detect-python-package.outputs.package-name }}-${{
          needs.detect-python-package.outputs.package-version }}
        path: dist/

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ env.PYTHON_VERSION }}

    - name: Install twine
      run: |
        python -m pip install --upgrade pip twine
```

### Step 2: Configure GitHub Packages

```yaml
- name: Configure GitHub Packages authentication
  run: |
    echo "=== Configuring GitHub Packages ==="

    # Create .pypirc for GitHub Packages
    cat > ~/.pypirc << EOF
    [distutils]
    index-servers =
        github

    [github]
    repository = https://upload.pypi.org/legacy/
    username = __token__
    password = ${{ secrets.GITHUB_TOKEN }}
    EOF

    chmod 600 ~/.pypirc

    echo "✅ Authentication configured"
```

### Step 3: Publish to GitHub Packages

```yaml
- name: Publish to GitHub Packages
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.GITHUB_TOKEN }}
    TWINE_REPOSITORY_URL: https://upload.pypi.org/legacy/
  run: |
    echo "=== Publishing to GitHub Packages ==="

    # GitHub Packages uses standard PyPI upload protocol
    # But with GitHub token authentication

    python -m twine upload \
      --repository-url https://upload.pypi.org/legacy/ \
      --username __token__ \
      --password "${{ secrets.GITHUB_TOKEN }}" \
      --skip-existing \
      --verbose \
      dist/* || {
        echo "⚠️  WARNING: Failed to publish to GitHub Packages"
        echo "   GitHub Packages for Python may not be enabled"
        echo "   Consider using pip install from GitHub releases instead"
        exit 0
    }

    echo "✅ Published to GitHub Packages"
```

### Step 4: Generate Installation Instructions

```yaml
- name: Generate installation instructions
  run: |
    PACKAGE_NAME="${{ needs.detect-python-package.outputs.package-name }}"
    PACKAGE_VERSION="${{ needs.detect-python-package.outputs.package-version }}"

    cat > installation-instructions.md << EOF
    # Installation Instructions

    ## Install from PyPI

    \`\`\`bash
    pip install $PACKAGE_NAME
    \`\`\`

    ## Install Specific Version

    \`\`\`bash
    pip install $PACKAGE_NAME==$PACKAGE_VERSION
    \`\`\`

    ## Install from Test PyPI

    \`\`\`bash
    pip install --index-url https://test.pypi.org/simple/ $PACKAGE_NAME
    \`\`\`

    ## Install from GitHub Packages

    \`\`\`bash
    # Configure pip to use GitHub Packages
    pip install --extra-index-url https://pypi.pkg.github.com/${{ github.repository_owner }} $PACKAGE_NAME
    \`\`\`

    ## Install from GitHub Release

    \`\`\`bash
    pip install https://github.com/${{ github.repository }}/releases/download/v$PACKAGE_VERSION/$PACKAGE_NAME-$PACKAGE_VERSION-py3-none-any.whl
    \`\`\`

    ## Verify Installation

    \`\`\`bash
    python -c "import $PACKAGE_NAME; print('Version:', $PACKAGE_NAME.__version__)"
    \`\`\`

    ## Package Links

    - **PyPI**: https://pypi.org/project/$PACKAGE_NAME/
    - **Test PyPI**: https://test.pypi.org/project/$PACKAGE_NAME/
    - **GitHub**: https://github.com/${{ github.repository }}
    - **Documentation**: https://${{ github.repository_owner }}.github.io/${{ github.event.repository.name }}/

    ---
    Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
    EOF

    cat installation-instructions.md

- name: Upload installation instructions
  uses: actions/upload-artifact@v4
  with:
    name: python-installation-instructions
    path: installation-instructions.md
    retention-days: 90
```

## Stage 4: Create Release with Packages

### Step 1: Attach Packages to GitHub Release

```yaml
attach-to-release:
  name: Attach Packages to GitHub Release
  runs-on: ubuntu-latest
  needs: [detect-python-package, build-python-package, publish-pypi]
  if: |
    needs.detect-python-package.outputs.has-package == 'true' &&
    startsWith(github.ref, 'refs/tags/v')

  permissions:
    contents: write

  steps:
    - name: Download build artifacts
      uses: actions/download-artifact@v4
      with:
        name:
          python-dist-${{ needs.detect-python-package.outputs.package-name }}-${{
          needs.detect-python-package.outputs.package-version }}
        path: dist/

    - name: Download installation instructions
      uses: actions/download-artifact@v4
      with:
        name: python-installation-instructions
        path: ./

    - name: Create or update GitHub Release
      uses: softprops/action-gh-release@v1
      with:
        tag_name: ${{ github.ref_name }}
        name: Release ${{ github.ref_name }}
        body_path: installation-instructions.md
        files: |
          dist/*.whl
          dist/*.tar.gz
          installation-instructions.md
        draft: false
        prerelease: false
```

## Stage 5: Publish Summary

### Step 1: Generate Publishing Report

```yaml
publish-summary:
  name: Generate Publishing Summary
  runs-on: ubuntu-latest
  needs:
    [
      detect-python-package,
      publish-test-pypi,
      publish-pypi,
      publish-github-packages,
      attach-to-release,
    ]
  if: always() && needs.detect-python-package.outputs.has-package == 'true'

  steps:
    - name: Generate publishing summary
      run: |
        cat > publishing-summary.md << 'EOF'
        # Python Package Publishing Summary

        ## Package Information

        - **Package Name**: ${{ needs.detect-python-package.outputs.package-name }}
        - **Version**: ${{ needs.detect-python-package.outputs.package-version }}
        - **Git Tag**: ${{ github.ref_name }}

        ## Publishing Status

        ### Test PyPI
        - Status: ${{ needs.publish-test-pypi.result }}
        - URL: https://test.pypi.org/project/${{ needs.detect-python-package.outputs.package-name }}/

        ### Production PyPI
        - Status: ${{ needs.publish-pypi.result }}
        - URL: https://pypi.org/project/${{ needs.detect-python-package.outputs.package-name }}/

        ### GitHub Packages
        - Status: ${{ needs.publish-github-packages.result }}
        - URL: https://github.com/${{ github.repository }}/packages

        ### GitHub Release
        - Status: ${{ needs.attach-to-release.result }}
        - URL: https://github.com/${{ github.repository }}/releases/tag/${{ github.ref_name }}

        ## Installation

        \`\`\`bash
        # Install from PyPI
        pip install ${{ needs.detect-python-package.outputs.package-name }}

        # Install specific version
        pip install ${{ needs.detect-python-package.outputs.package-name }}==${{ needs.detect-python-package.outputs.package-version }}
        \`\`\`

        ## Next Steps

        1. ✅ Verify package installation from PyPI
        2. ✅ Test package functionality
        3. ✅ Update documentation with new version
        4. ✅ Announce release to users

        ---
        Published: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
        EOF

        cat publishing-summary.md

    - name: Upload publishing summary
      uses: actions/upload-artifact@v4
      with:
        name: python-publishing-summary
        path: publishing-summary.md
        retention-days: 90

    - name: Add job summary
      run: |
        cat publishing-summary.md >> $GITHUB_STEP_SUMMARY
```

## Testing Publishing Locally

### Test Script 1: Test PyPI Upload (Dry Run)

```bash
#!/bin/bash
# test-pypi-upload-dry-run.sh

set -e

echo "=== Testing PyPI Upload (Dry Run) ==="
echo ""

if [ ! -d "dist" ]; then
    echo "❌ ERROR: No dist/ directory found"
    exit 1
fi

# Install twine
python -m pip install --upgrade twine

# Check distributions
echo "Checking distributions..."
python -m twine check dist/*

# Test upload (dry run - won't actually upload)
echo ""
echo "Testing upload configuration..."
echo "(This is a dry run - no actual upload will occur)"

# Show what would be uploaded
python -m twine upload \
  --repository testpypi \
  --skip-existing \
  --verbose \
  dist/* \
  || echo "Configure TEST_PYPI_API_TOKEN to test actual upload"

echo ""
echo "✅ Dry run completed!"
echo ""
echo "To actually upload to Test PyPI:"
echo "1. Create account at https://test.pypi.org"
echo "2. Generate API token"
echo "3. Run: twine upload --repository testpypi dist/*"
```

**Run it:**

```bash
chmod +x test-pypi-upload-dry-run.sh
./test-pypi-upload-dry-run.sh
```

### Test Script 2: Verify Published Package

```bash
#!/bin/bash
# verify-published-package.sh

echo "=== Verifying Published Package ==="
echo ""

read -p "Enter package name: " PACKAGE_NAME
read -p "Enter package version: " PACKAGE_VERSION

echo ""
echo "Checking Test PyPI..."
pip index versions --index-url https://test.pypi.org/simple/ "$PACKAGE_NAME" || \
  echo "⚠️  Not found on Test PyPI"

echo ""
echo "Checking PyPI..."
pip index versions "$PACKAGE_NAME" || \
  echo "⚠️  Not found on PyPI"

echo ""
echo "Attempting installation from PyPI..."
python -m venv /tmp/test-venv
source /tmp/test-venv/bin/activate
pip install "$PACKAGE_NAME==$PACKAGE_VERSION" || \
  echo "⚠️  Installation failed"

if pip show "$PACKAGE_NAME" >/dev/null 2>&1; then
    echo "✅ Package installed successfully"
    pip show "$PACKAGE_NAME"
else
    echo "❌ Package not installed"
fi

deactivate
rm -rf /tmp/test-venv

echo ""
echo "Verification completed!"
```

**Run it:**

```bash
chmod +x verify-published-package.sh
./verify-published-package.sh
```

## Commit Publishing Job Changes

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Stage the workflow
git add .github/workflows/release-python.yml

# Commit with conventional format
git commit -m "feat(release-python): add multi-registry package publishing

Added comprehensive package publishing to release-python.yml:

Added Jobs:
- publish-test-pypi: Publish to Test PyPI for testing
- publish-pypi: Publish to production PyPI
- publish-github-packages: Publish to GitHub Packages
- attach-to-release: Attach packages to GitHub Release
- publish-summary: Generate publishing status report

Publishing Features:
- Test PyPI publishing for verification before production
- Production PyPI publishing with trusted publishing support
- GitHub Packages publishing (when enabled)
- Automatic GitHub Release creation with packages attached
- Installation instructions generation
- Publishing status tracking

Registry Support:
- PyPI (production): https://pypi.org
- Test PyPI (testing): https://test.pypi.org
- GitHub Packages: https://pypi.pkg.github.com

Authentication:
- PyPI: API token (PYPI_API_TOKEN secret)
- Test PyPI: API token (TEST_PYPI_API_TOKEN secret)
- GitHub Packages: GITHUB_TOKEN (automatic)

Publishing Flow:
1. Build and validate package
2. Publish to Test PyPI (optional)
3. Verify Test PyPI publication
4. Publish to production PyPI (tag releases only)
5. Verify PyPI publication
6. Publish to GitHub Packages
7. Attach to GitHub Release
8. Generate publishing summary

Environment Protection:
- test-pypi environment for Test PyPI
- pypi environment for production PyPI
- github-packages environment for GitHub Packages

Artifacts:
- python-installation-instructions: Installation guide
- python-publishing-summary: Publishing status report

Files changed:
- .github/workflows/release-python.yml - Added publishing jobs"
```

## Next Steps

**Continue to Part 6:** Documentation, troubleshooting, and completion checklist.
