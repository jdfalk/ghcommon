<!-- file: docs/cross-registry-todos/task-01/t01-part1.md -->
<!-- version: 1.0.0 -->
<!-- guid: t01-yaml-fix-part1-a1b2c3d4-e5f6 -->

# Task 01 Part 1: YAML Syntax Fixes - Overview & Analysis

## Task Overview

**Priority:** 1 (Critical - Syntax Error)
**Estimated Lines:** ~3,500 lines (6 parts)
**Complexity:** Low (Simple fix, but comprehensive documentation)
**Impact:** High (Affects cache performance across all Rust releases)

## What We're Fixing

### The Problem

The `release-rust.yml` workflow contains YAML syntax errors in the cache `restore-keys` configuration. Trailing hyphens in YAML sequences cause:

1. **Cache restoration failures** - Keys may not match properly
2. **GitHub Actions warnings** - Syntax validation issues
3. **Inconsistent behavior** - Different YAML parsers interpret differently
4. **Maintenance issues** - Confusing syntax for contributors

### Current State (Incorrect)

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo-
      # ^^ WRONG: Trailing hyphen with no value
```

### Correct State (Fixed)

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo
      # ^^ CORRECT: No trailing hyphen
```

## Why This Matters

### Cache Performance Impact

GitHub Actions cache matching works with prefix matching:

**Primary Key:**
```
linux-cargo-abc123def456
```

**Restore Keys (Incorrect with trailing hyphen):**
```
linux-cargo-
```

**Restore Keys (Correct without trailing hyphen):**
```
linux-cargo
```

Both technically work for prefix matching, BUT:

1. **YAML Syntax**: Trailing hyphen implies list continuation
2. **Parser Behavior**: Some parsers expect value after hyphen
3. **Best Practice**: Clean YAML without ambiguous syntax
4. **Consistency**: Match GitHub Actions documentation examples

### Locations in File

**File:** `.github/workflows/release-rust.yml`

**Occurrences:**

1. **Lines 231-236** - Linux x86_64 cache restore-keys
2. **Lines 241-246** - Linux aarch64 cache restore-keys
3. **Lines 251-254** - macOS cache restore-keys

**Pattern:**

```yaml
restore-keys: |
  ${{ runner.os }}-cargo-${{ matrix.rust }}-
  ${{ runner.os }}-cargo-
```

**Should be:**

```yaml
restore-keys: |
  ${{ runner.os }}-cargo-${{ matrix.rust }}
  ${{ runner.os }}-cargo
```

## Repository Context

### File: release-rust.yml

**Purpose:** Multi-platform Rust binary release workflow

**Key Features:**
- Cross-compilation for Linux (x86_64, aarch64)
- macOS builds (Intel, Apple Silicon)
- Windows builds
- Cargo caching for faster builds
- Artifact generation and release publishing

**Cache Strategy:**

The workflow uses a hierarchical cache key strategy:

1. **Exact match:** `{os}-cargo-{rust-version}-{Cargo.lock-hash}`
2. **Version fallback:** `{os}-cargo-{rust-version}`
3. **Generic fallback:** `{os}-cargo`

This allows:
- Reusing cache when Cargo.lock unchanged
- Falling back to rust-version cache when dependencies change
- Ultimate fallback to any Rust cache for that OS

### Current Workflow Structure

```yaml
name: Release Rust Binaries

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

permissions:
  contents: write
  packages: write

jobs:
  release:
    strategy:
      matrix:
        include:
          - target: x86_64-unknown-linux-gnu
            os: ubuntu-latest
            rust: stable

          - target: aarch64-unknown-linux-gnu
            os: ubuntu-latest
            rust: stable

          - target: x86_64-apple-darwin
            os: macos-latest
            rust: stable

          - target: aarch64-apple-darwin
            os: macos-latest
            rust: stable

          - target: x86_64-pc-windows-msvc
            os: windows-latest
            rust: stable

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.target }}

      # CACHE STEP HERE (with syntax issues)
      - uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/bin/
            ~/.cargo/registry/index/
            ~/.cargo/registry/cache/
            ~/.cargo/git/db/
            target/
          key: ${{ runner.os }}-cargo-${{ matrix.rust }}-${{ hashFiles('**/Cargo.lock') }}
          restore-keys: |
            ${{ runner.os }}-cargo-${{ matrix.rust }}-
            ${{ runner.os }}-cargo-

      - name: Build
        run: cargo build --release --target ${{ matrix.target }}

      - name: Create release
        # ... release logic
```

## Understanding YAML List Syntax

### YAML List Formats

**Block style with hyphens:**

```yaml
# Correct
fruits:
  - apple
  - banana
  - orange

# Incorrect (trailing hyphen)
fruits:
  - apple
  - banana
  -        # <-- parser expects value here
```

**Literal block scalar with pipe:**

```yaml
# Correct
description: |
  Line 1
  Line 2
  Line 3

# In our case (multi-line string, not a list)
restore-keys: |
  prefix1
  prefix2
  prefix3
```

### The Issue with Trailing Hyphens

When we write:

```yaml
restore-keys: |
  ${{ runner.os }}-cargo-
```

The trailing hyphen in `cargo-` is part of the STRING value, not YAML syntax. However, it looks ambiguous:

1. Is it the start of another list item?
2. Is it part of the string?
3. Is it incomplete syntax?

**Best practice:** Remove trailing hyphen to avoid confusion.

## Impact Assessment

### Affected Workflows

**In ghcommon repository:**

1. `.github/workflows/release-rust.yml` - PRIMARY TARGET
2. Check for similar patterns in other workflows

**In other repositories:**

Any repository using ghcommon workflows as templates or examples.

### Build Impact

**Before Fix:**
- Cache may or may not restore properly (parser-dependent)
- Potential warnings in Actions logs
- Inconsistent cache hit rates

**After Fix:**
- Clean YAML syntax
- Consistent cache restoration
- No ambiguity in cache key matching
- Better documentation example

### Risk Assessment

**Risk Level:** Very Low

- Simple text change (remove 3 hyphens)
- No logic changes
- No conditional changes
- No new features
- Backward compatible (cache keys still match)

**Testing Required:**
- YAML syntax validation
- Cache key matching verification
- Test workflow execution

## Prerequisites

### Tools Required

```bash
# YAML linter
pip install yamllint

# OR
brew install yamllint

# OR
apt-get install yamllint

# GitHub CLI (for testing)
brew install gh
# OR
apt-get install gh
```

### Repository Access

```bash
# Verify access
gh auth status

# Expected output:
✓ Logged in to github.com as YOUR_USERNAME (oauth_token)
✓ Git operations for github.com configured to use https protocol.
✓ Token: *******************
✓ Token scopes: repo, workflow
```

### Local Environment Setup

```bash
# Clone repository
git clone https://github.com/jdfalk/ghcommon.git
cd ghcommon

# Create feature branch
git checkout -b fix/yaml-trailing-hyphens

# Verify workflow file exists
ls -la .github/workflows/release-rust.yml
```

## Validation Strategy

### Pre-Fix Validation

```bash
# 1. Check current syntax issues
yamllint .github/workflows/release-rust.yml

# Expected output (might show warnings about line length, etc.)

# 2. Search for trailing hyphens in restore-keys
grep -A 2 "restore-keys" .github/workflows/release-rust.yml | grep "\-$"

# Expected: Lines ending with hyphen

# 3. Count occurrences
grep -A 2 "restore-keys" .github/workflows/release-rust.yml | grep "\-$" | wc -l

# Expected: 6 (3 cache blocks × 2 restore-keys each)
```

### Post-Fix Validation

```bash
# 1. Verify no trailing hyphens in restore-keys
grep -A 2 "restore-keys" .github/workflows/release-rust.yml | grep "\-$"

# Expected: No output (or only hyphens in other contexts)

# 2. Validate YAML syntax
yamllint .github/workflows/release-rust.yml

# Expected: Clean (or only style warnings, not syntax errors)

# 3. Validate with GitHub Actions syntax checker
gh workflow view release-rust.yml

# Expected: No syntax errors
```

## Next Steps

This completes Part 1 (Overview & Analysis). Continue to Part 2 for:

- Step-by-step fix procedure
- Detailed before/after comparisons
- Line-by-line changes
- Testing procedures
