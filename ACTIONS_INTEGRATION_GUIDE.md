# Integration Guide: Using New Actions in Workflows

<!-- file: ACTIONS_INTEGRATION_GUIDE.md -->
<!-- version: 1.0.0 -->
<!-- guid: 6e7f8a9b-0c1d-2e3f-4a5b-6c7d8e9f0a1b -->

## Overview

This guide shows how to refactor `reusable-ci.yml` and `reusable-release.yml` to
use the new GitHub Actions instead of inline scripts.

## Problem Being Solved

**Old Pattern** (sparse-checkout + scripts):

```yaml
# This fails when called from external repos
- run: |
    git sparse-checkout add .github/workflows/scripts
    python .github/workflows/scripts/load_repository_config.py
```

**New Pattern** (GitHub Actions):

```yaml
# This works everywhere
- uses: jdfalk/load-config-action@v1.0.0
```

## Integration Examples

### Example 1: Load Configuration

**Before:**

```yaml
- name: Load repository config
  id: config
  run: |
    python .github/workflows/scripts/load_repository_config.py
```

**After:**

```yaml
- name: Load repository config
  id: config
  uses: jdfalk/load-config-action@v1.0.0
  with:
    config-file: .github/repository-config.yml
    fail-on-missing: false
```

### Example 2: Generate CI Matrices

**Before:**

```yaml
- name: Generate CI matrices
  id: matrices
  run: |
    python .github/workflows/scripts/ci_workflow.py generate-matrices \
      --config "$CONFIG_JSON" \
      --fallback-go-version "1.23"
```

**After:**

```yaml
- name: Generate CI matrices
  id: matrices
  uses: jdfalk/ci-generate-matrices-action@v1.0.0
  with:
    repository-config: ${{ steps.config.outputs.config }}
    fallback-go-version: '1.23'
```

### Example 3: Detect Languages

**Before:**

```yaml
- name: Detect languages
  id: detect
  run: |
    python .github/workflows/scripts/release_workflow.py detect-languages
```

**After:**

```yaml
- name: Detect languages
  id: detect
  uses: jdfalk/detect-languages-action@v1.0.0
  with:
    skip-detection: false
```

### Example 4: Release Strategy

**Before:**

```yaml
- name: Determine release strategy
  id: strategy
  run: |
    bash .github/workflows/scripts/release_strategy.sh "${{ github.ref_name }}"
```

**After:**

```yaml
- name: Determine release strategy
  id: strategy
  uses: jdfalk/release-strategy-action@v1.0.0
  with:
    branch-name: ${{ github.ref_name }}
```

### Example 5: Generate Version

**Before:**

```yaml
- name: Generate semantic version
  id: version
  run: |
    bash .github/workflows/scripts/generate-version.sh \
      --release-type auto \
      --branch "${{ github.ref_name }}"
```

**After:**

```yaml
- name: Generate semantic version
  id: version
  uses: jdfalk/generate-version-action@v1.0.0
  with:
    release-type: auto
    branch-name: ${{ github.ref_name }}
```

### Example 6: Package Assets

**Before:**

```yaml
- name: Package release assets
  id: package
  run: |
    python .github/workflows/scripts/package_release_assets.py \
      --artifacts-dir dist
```

**After:**

```yaml
- name: Package assets
  id: package
  uses: jdfalk/package-assets-action@v1.0.0
  with:
    artifacts-dir: dist
```

## Complete Workflow Example

### Refactored `reusable-ci.yml`

```yaml
name: 'Reusable CI Workflow'

on:
  workflow_call:
    inputs:
      config-file:
        type: string
        default: .github/repository-config.yml

jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      config: ${{ steps.config.outputs.config }}
      has-go: ${{ steps.detect.outputs.has-go }}
      has-python: ${{ steps.detect.outputs.has-python }}
      go-matrix: ${{ steps.matrices.outputs.go-matrix }}
      python-matrix: ${{ steps.matrices.outputs.python-matrix }}

    steps:
      # NEW: Use action instead of script
      - name: Checkout
        uses: actions/checkout@v4

      - name: Load config
        id: config
        uses: jdfalk/load-config-action@v1.0.0
        with:
          config-file: ${{ inputs.config-file }}

      - name: Detect languages
        id: detect
        uses: jdfalk/detect-languages-action@v1.0.0

      - name: Generate matrices
        id: matrices
        uses: jdfalk/ci-generate-matrices-action@v1.0.0
        with:
          repository-config: ${{ steps.config.outputs.config }}

  test-go:
    needs: detect
    if: ${{ needs.detect.outputs.has-go == 'true' }}
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJson(needs.detect.outputs.go-matrix) }}

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go-version }}
      - run: go test ./...

  test-python:
    needs: detect
    if: ${{ needs.detect.outputs.has-python == 'true' }}
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJson(needs.detect.outputs.python-matrix) }}

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pytest
```

### Refactored `reusable-release.yml`

````yaml
name: 'Reusable Release Workflow'

on:
  workflow_call:
    inputs:
      release-type:
        type: string
        default: auto

jobs:
  release:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
      tag: ${{ steps.version.outputs.tag }}
      strategy: ${{ steps.strategy.outputs.strategy }}

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      # NEW: Use action for version generation
      - name: Generate version
        id: version
        uses: jdfalk/generate-version-action@v1.0.0
        with:
          release-type: ${{ inputs.release-type }}
          branch-name: ${{ github.ref_name }}

      # NEW: Use action for strategy detection
      - name: Determine strategy
        id: strategy
        uses: jdfalk/release-strategy-action@v1.0.0
        with:
          branch-name: ${{ github.ref_name }}

      # NEW: Use action for asset packaging
      - name: Package assets
        id: package
        uses: jdfalk/package-assets-action@v1.0.0
        with:
          artifacts-dir: dist

      - name: Create release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: ${{ steps.version.outputs.tag }}
          name: Release ${{ steps.version.outputs.version }}
          draft: ${{ steps.strategy.outputs.is-draft }}
          prerelease: ${{ steps.strategy.outputs.is-prerelease }}
          files: |
            dist/*
          body: |
            ## Checksums
            ```
            ${{ steps.package.outputs.checksums }}
            ```
````

## Migration Checklist

- [ ] Update `reusable-ci.yml` to use new actions
- [ ] Update `reusable-release.yml` to use new actions
- [ ] Remove sparse-checkout from workflows
- [ ] Remove `.github/workflows/scripts/` directory (or archive)
- [ ] Test with audiobook-organizer repository
- [ ] Verify Go, Python, Docker detection works
- [ ] Verify version generation works
- [ ] Verify release creation works
- [ ] Update documentation in ghcommon README
- [ ] Create migration guide for external repositories
- [ ] Tag ghcommon release (v2.0.0 or similar)

## Benefits of New Approach

✅ **No script copying** - Actions work anywhere ✅ **Centralized updates** -
Fix scripts in one place ✅ **Better auditing** - External scripts are
reviewable ✅ **No sparse-checkout** - Simpler, more reliable workflows ✅
**Easier to test** - Actions have isolated test workflows ✅ **Version
control** - Each action has own version tags ✅ **Faster CI/CD** - No git
operations needed ✅ **Reusable** - External repos can use actions directly

## Action Documentation

Each action has comprehensive README:

- `jdfalk/load-config-action` - Load config files
- `jdfalk/ci-generate-matrices-action` - Generate test matrices
- `jdfalk/detect-languages-action` - Detect languages
- `jdfalk/release-strategy-action` - Determine strategy
- `jdfalk/generate-version-action` - Generate versions
- `jdfalk/package-assets-action` - Package artifacts

Visit action repositories for detailed usage examples.

## Troubleshooting

### Action not found

Ensure you're using the correct GitHub org and action name:

```yaml
# Correct
uses: jdfalk/detect-languages-action@v1.0.0

# Incorrect
uses: detect-languages-action@v1.0.0  # Missing org
uses: jdfalk/detect-language-action@v1.0.0  # Wrong name
```

### Output not available

Check action documentation for correct output names:

```yaml
# Load config outputs: config, has-config, raw-yaml
steps.config.outputs.config

# Detect languages outputs: has-go, has-python, primary-language
steps.detect.outputs.has-go
```

### Version compatibility

All actions use semantic versioning:

- `v1.0.0` - Specific version
- `v1` - Latest v1.x version
- `main` - Latest development version (not recommended)

## Next Steps

1. **In ghcommon**: Update `reusable-ci.yml` and `reusable-release.yml`
2. **Test locally**: Create test workflow using new actions
3. **Test in audiobook-organizer**: Use refactored workflows
4. **Document**: Update ghcommon README with action references
5. **Release**: Tag ghcommon with new version
6. **Communicate**: Notify repos about migration path

---

**Integration Ready**: ✅ YES **Actions Available**: ✅ v1.0.0 **Documentation
Complete**: ✅ YES
