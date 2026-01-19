<!-- file: docs/cross-registry-todos/task-01-fix-yaml-syntax.md -->
<!-- version: 1.1.0 -->
<!-- guid: t01-yaml-fix-a1b2c3d4-e5f6-7a8b-9c0d -->
<!-- last-edited: 2026-01-19 -->

# Task 01: Fix YAML Syntax in release-rust.yml

> **Status:** ✅ Completed  
> **Updated:** `.github/workflows/release-rust.yml` now v1.9.0 with cache `restore-keys` trimmed to
> prefix values (no trailing hyphen).  
> **Verification:** Manual inspection of the workflow confirms the fix across all cache blocks.

## Task Overview

**What**: Remove trailing hyphens from cache restore-keys in release-rust.yml

**Why**: YAML restore-keys with trailing hyphens are syntactically incorrect and can cause cache
restoration failures or warnings in GitHub Actions

**Where**: `ghcommon` repository, file `.github/workflows/release-rust.yml` lines 231-236, 241-246,
251-254

**Expected Outcome**: Clean YAML syntax with proper restore-keys formatting, no trailing hyphens

**Estimated Time**: 5-10 minutes

**Risk Level**: Low (fixing syntax, not changing logic)

## Prerequisites

### Required Access

- Write access to `jdfalk/ghcommon` repository
- Ability to commit and push to `main` branch

### Required Tools

```bash
# Verify these are installed
git --version          # Any recent version
code --version         # VS Code (or any text editor)
yamllint --version     # Optional but recommended
```

### Knowledge Requirements

- Basic YAML syntax understanding
- GitHub Actions cache action knowledge
- Git commit message conventions (conventional commits)

## Current State Analysis

### Check Current State

```bash
# Navigate to repository
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Verify you're on main branch
git branch --show-current

# Check current file state
head -260 .github/workflows/release-rust.yml | tail -35
```

### Expected Output

You should see three cache blocks with trailing hyphens in restore-keys:

```yaml
- name: Cache cargo registry
  uses: actions/cache@v4
  with:
    path: ~/.cargo/registry
    key: ${{ runner.os }}-cargo-registry-${{ matrix.target }}-${{ github.run_id }}
    restore-keys: |
      ${{ runner.os }}-cargo-registry-${{ matrix.target }}-
      ${{ runner.os }}-cargo-registry-

- name: Cache cargo index
  uses: actions/cache@v4
  with:
    path: ~/.cargo/git
    key: ${{ runner.os }}-cargo-index-${{ matrix.target }}-${{ github.run_id }}
    restore-keys: |
      ${{ runner.os }}-cargo-index-${{ matrix.target }}-
      ${{ runner.os }}-cargo-index-

- name: Cache cargo build
  uses: actions/cache@v4
  with:
    path: target
    key: ${{ runner.os }}-cargo-build-${{ matrix.target }}-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-cargo-build-${{ matrix.target }}-
      ${{ runner.os }}-cargo-build-
```

### Problem Identification

The issue is the trailing hyphens on lines like:

- `${{ runner.os }}-cargo-registry-${{ matrix.target }}-` ← trailing hyphen
- `${{ runner.os }}-cargo-registry-` ← trailing hyphen

These should NOT have trailing hyphens. The hyphen is used as a YAML list indicator, not part of the
key prefix.

### Decision Point

**Proceed if**: You see the exact pattern above with trailing hyphens

**Stop if**: The file already has correct syntax (no trailing hyphens after variables)

## Implementation Steps

### Step 1: Update File Header Version

First, update the version number in the file header (lines 1-3):

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon
```

Open `.github/workflows/release-rust.yml` and change line 2:

**Current:**

```yaml
# version: 1.8.1
```

**New:**

```yaml
# version: 1.8.2
```

**Rationale**: Patch version increment for bug fix

### Step 2: Fix Cache cargo registry Block

Locate lines 228-236 (the first cache block):

**Current:**

```yaml
- name: Cache cargo registry
  uses: actions/cache@v4
  with:
    path: ~/.cargo/registry
    key: ${{ runner.os }}-cargo-registry-${{ matrix.target }}-${{ github.run_id }}
    restore-keys: |
      ${{ runner.os }}-cargo-registry-${{ matrix.target }}-
      ${{ runner.os }}-cargo-registry-
```

**Replace with:**

```yaml
- name: Cache cargo registry
  uses: actions/cache@v4
  with:
    path: ~/.cargo/registry
    key: ${{ runner.os }}-cargo-registry-${{ matrix.target }}-${{ github.run_id }}
    restore-keys: |
      ${{ runner.os }}-cargo-registry-${{ matrix.target }}
      ${{ runner.os }}-cargo-registry
```

**Changes**: Removed trailing hyphens from both restore-keys lines

### Step 3: Fix Cache cargo index Block

Locate lines 238-246 (the second cache block):

**Current:**

```yaml
- name: Cache cargo index
  uses: actions/cache@v4
  with:
    path: ~/.cargo/git
    key: ${{ runner.os }}-cargo-index-${{ matrix.target }}-${{ github.run_id }}
    restore-keys: |
      ${{ runner.os }}-cargo-index-${{ matrix.target }}-
      ${{ runner.os }}-cargo-index-
```

**Replace with:**

```yaml
- name: Cache cargo index
  uses: actions/cache@v4
  with:
    path: ~/.cargo/git
    key: ${{ runner.os }}-cargo-index-${{ matrix.target }}-${{ github.run_id }}
    restore-keys: |
      ${{ runner.os }}-cargo-index-${{ matrix.target }}
      ${{ runner.os }}-cargo-index
```

**Changes**: Removed trailing hyphens from both restore-keys lines

### Step 4: Fix Cache cargo build Block

Locate lines 248-254 (the third cache block):

**Current:**

```yaml
- name: Cache cargo build
  uses: actions/cache@v4
  with:
    path: target
    key: ${{ runner.os }}-cargo-build-${{ matrix.target }}-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-cargo-build-${{ matrix.target }}-
      ${{ runner.os }}-cargo-build-
```

**Replace with:**

```yaml
- name: Cache cargo build
  uses: actions/cache@v4
  with:
    path: target
    key: ${{ runner.os }}-cargo-build-${{ matrix.target }}-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-cargo-build-${{ matrix.target }}
      ${{ runner.os }}-cargo-build
```

**Changes**: Removed trailing hyphens from both restore-keys lines

### Step 5: Verify Changes

Check that all changes were applied correctly:

```bash
# View the modified sections
sed -n '228,254p' .github/workflows/release-rust.yml
```

**Expected output** (no trailing hyphens):

```yaml
- name: Cache cargo registry
  uses: actions/cache@v4
  with:
    path: ~/.cargo/registry
    key: ${{ runner.os }}-cargo-registry-${{ matrix.target }}-${{ github.run_id }}
    restore-keys: |
      ${{ runner.os }}-cargo-registry-${{ matrix.target }}
      ${{ runner.os }}-cargo-registry

- name: Cache cargo index
  uses: actions/cache@v4
  with:
    path: ~/.cargo/git
    key: ${{ runner.os }}-cargo-index-${{ matrix.target }}-${{ github.run_id }}
    restore-keys: |
      ${{ runner.os }}-cargo-index-${{ matrix.target }}
      ${{ runner.os }}-cargo-index

- name: Cache cargo build
  uses: actions/cache@v4
  with:
    path: target
    key: ${{ runner.os }}-cargo-build-${{ matrix.target }}-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-cargo-build-${{ matrix.target }}
      ${{ runner.os }}-cargo-build
```

### Step 6: Validate YAML Syntax

```bash
# Optional: Use yamllint if available
yamllint .github/workflows/release-rust.yml

# Check for actionlint errors
actionlint .github/workflows/release-rust.yml || echo "actionlint not installed, skipping"

# Verify no trailing hyphens remain
grep -n "restore-keys" .github/workflows/release-rust.yml -A 3
```

**Expected**: No syntax errors, no trailing hyphens after variable substitutions

## Validation

### Pre-Commit Validation

```bash
# Ensure we're in the right place
pwd
# Should output: /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Check git status
git status
# Should show: modified: .github/workflows/release-rust.yml

# View diff
git diff .github/workflows/release-rust.yml
```

**Expected diff output:**

```diff
@@ -2,7 +2,7 @@
-# version: 1.8.1
+# version: 1.8.2
 # guid: b5c6d7e8-f9a0-1b2c-3d4e-5f6a7b8c9d0e

@@ -233,8 +233,8 @@
           key: ${{ runner.os }}-cargo-registry-${{ matrix.target }}-${{ github.run_id }}
           restore-keys: |
-            ${{ runner.os }}-cargo-registry-${{ matrix.target }}-
-            ${{ runner.os }}-cargo-registry-
+            ${{ runner.os }}-cargo-registry-${{ matrix.target }}
+            ${{ runner.os }}-cargo-registry

@@ -244,8 +244,8 @@
           key: ${{ runner.os }}-cargo-index-${{ matrix.target }}-${{ github.run_id }}
           restore-keys: |
-            ${{ runner.os }}-cargo-index-${{ matrix.target }}-
-            ${{ runner.os }}-cargo-index-
+            ${{ runner.os }}-cargo-index-${{ matrix.target }}
+            ${{ runner.os }}-cargo-index

@@ -252,8 +252,8 @@
           key: ${{ runner.os }}-cargo-build-${{ matrix.target }}-${{ github.sha }}
           restore-keys: |
-            ${{ runner.os }}-cargo-build-${{ matrix.target }}-
-            ${{ runner.os }}-cargo-build-
+            ${{ runner.os }}-cargo-build-${{ matrix.target }}
+            ${{ runner.os }}-cargo-build
```

### Commit Changes

Use the VS Code task or conventional commit format:

```bash
# Using copilot-agent-util (preferred)
copilot-agent-util git add .github/workflows/release-rust.yml

copilot-agent-util git commit -m "fix(workflows): remove trailing hyphens from cache restore-keys

Fixed YAML syntax in release-rust.yml where cache restore-keys had
trailing hyphens. These hyphens were syntactically incorrect and could
cause cache restoration issues.

Changes:
- Cache cargo registry: removed trailing hyphens from restore-keys
- Cache cargo index: removed trailing hyphens from restore-keys
- Cache cargo build: removed trailing hyphens from restore-keys
- Bumped version from 1.8.1 to 1.8.2

Related to task: task-01-fix-yaml-syntax"

# Push changes
copilot-agent-util git push
```

**Or using raw git** (if copilot-agent-util unavailable):

```bash
git add .github/workflows/release-rust.yml
git commit -m "fix(workflows): remove trailing hyphens from cache restore-keys

Fixed YAML syntax in release-rust.yml where cache restore-keys had
trailing hyphens. These hyphens were syntactically incorrect and could
cause cache restoration issues.

Changes:
- Cache cargo registry: removed trailing hyphens from restore-keys
- Cache cargo index: removed trailing hyphens from restore-keys
- Cache cargo build: removed trailing hyphens from restore-keys
- Bumped version from 1.8.1 to 1.8.2

Related to task: task-01-fix-yaml-syntax"

git push
```

### Post-Commit Validation

```bash
# Verify commit was created
git log -1 --oneline
# Should show: fix(workflows): remove trailing hyphens from cache restore-keys

# Verify pushed successfully
git status
# Should show: On branch main, Your branch is up to date with 'origin/main'

# View the committed changes
git show HEAD
```

### Workflow Validation (Optional)

Trigger the workflow to ensure it runs without errors:

```bash
# Trigger release workflow manually (if you have gh CLI)
gh workflow run release.yml

# Monitor workflow
gh run list --workflow=release.yml --limit 5

# View specific run (replace RUN_ID with actual ID from above)
gh run view <RUN_ID> --log
```

**Expected**: Workflow should start, cache restoration should work without warnings

## Common Issues and Solutions

### Issue 1: Git Conflicts

**Symptom**: Git reports conflicts when trying to commit

**Solution**:

```bash
# Stash changes
git stash

# Pull latest
git pull origin main

# Reapply changes
git stash pop

# Resolve conflicts if any, then commit
```

### Issue 2: Permission Denied on Push

**Symptom**: `remote: Permission to jdfalk/ghcommon.git denied`

**Solution**:

```bash
# Check remote URL
git remote -v

# Should use SSH: git@github.com:jdfalk/ghcommon.git
# If using HTTPS, switch to SSH:
git remote set-url origin git@github.com:jdfalk/ghcommon.git

# Verify SSH keys
ssh -T git@github.com
```

### Issue 3: Changes Look Different

**Symptom**: Diff doesn't match expected output

**Solution**:

```bash
# Revert and start over
git checkout -- .github/workflows/release-rust.yml

# Re-read task instructions carefully
# Make changes again, one block at a time
```

### Issue 4: YAML Validation Errors

**Symptom**: `yamllint` or `actionlint` reports errors

**Solution**:

```bash
# Check exact error message
yamllint .github/workflows/release-rust.yml

# Common issues:
# - Indentation problems: ensure 2-space indents
# - Missing newline at EOF: add blank line at end of file
# - Tab characters: replace with spaces

# Fix indentation
# Open in VS Code and use Format Document (Shift+Alt+F)
```

## Rollback Procedure

If something goes wrong after pushing:

```bash
# Find the commit hash
git log --oneline -5

# Revert the commit (creates new commit that undoes changes)
git revert <commit-hash>

# Push the revert
git push

# Or, if not yet pushed to main, hard reset
git reset --hard HEAD~1
```

## Integration Notes

### Affected Systems

- **release-rust.yml workflow**: Cache behavior improved
- **Other workflows**: No impact (change is isolated)
- **Downstream repos**: No impact (change is in ghcommon only)

### Communication

- No notification needed for this fix (internal improvement)
- Document in next release notes as "Fixed cache restore-keys syntax"

### Follow-up Tasks

- None required
- This task is complete and independent

## Success Criteria Checklist

- [x] File header version updated (1.8.1 → 1.8.2)
- [x] Cache cargo registry restore-keys: trailing hyphens removed
- [x] Cache cargo index restore-keys: trailing hyphens removed
- [x] Cache cargo build restore-keys: trailing hyphens removed
- [x] YAML syntax validated (no errors)
- [x] Changes committed with conventional commit message
- [x] Changes pushed to origin/main
- [x] No workflow errors introduced

## Completion Verification

Run this final check:

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Verify changes are in main branch
git log --oneline -1 --grep="trailing hyphens"

# Verify file contains correct syntax (no trailing hyphens)
grep -A 2 "restore-keys" .github/workflows/release-rust.yml | grep -v "^--$"

# Expected: All restore-keys lines end with variable names, no trailing hyphens
```

**Task Complete!** ✅

The YAML syntax is now correct and cache restoration will work optimally.

---

**Next Suggested Task**: `task-02-docker-packages.md` (verification task)
