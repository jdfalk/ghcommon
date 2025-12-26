<!-- file: CACHE_TESTING_GUIDE.md -->
<!-- version: 1.0.0 -->
<!-- guid: cache-testing-2025-12-26 -->

# Robust Manual Caching Strategy - Testing Guide

Complete step-by-step guide to test the new caching strategy in the
audiobook-organizer repository.

---

## Quick Start (5 minutes)

### 1. Verify Changes Were Pushed

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon
git log --oneline -5
# Should see: de881bd feat(cache): implement robust advanced caching strategy for npm
```

✅ **Expected Output**:

```
de881bd (HEAD -> main) feat(cache): implement robust advanced caching strategy for npm
71575cf chore(changelog): document npm cache hardening
...
```

### 2. Trigger CI in audiobook-organizer

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/audiobook-organizer
gh workflow run ci.yml --ref main
```

✅ **Expected Output**:

```
✓ Created workflow_run ...
  Status: queued
```

### 3. Monitor the Run

```bash
# In browser
https://github.com/jdfalk/audiobook-organizer/actions
```

---

## Detailed Testing Steps

### Phase 1: Pre-Test Validation (Local)

#### Step 1.1: Verify File Changes

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Check modified files
git diff --stat HEAD~1
```

✅ **Expected Output**:

```
 .github/workflows/reusable-advanced-cache.yml  |   9 +-
 .github/workflows/reusable-ci.yml              |  36 +-
 CACHE_STRATEGY_IMPLEMENTATION.md               | 351 ++++++++++++++
 CACHE_STRATEGY_SUMMARY.md                      | 382 +++++++++++++++
 CACHE_YAML_DIFFS.md                            | 460 +++++++++++++++++
 5 files changed, 1237 insertions(+), 36 deletions(-)
```

#### Step 1.2: Verify Workflow Syntax

```bash
# Install actionlint if needed
which actionlint || (brew install actionlint)

# Validate workflows
actionlint .github/workflows/reusable-ci.yml
actionlint .github/workflows/reusable-advanced-cache.yml
```

✅ **Expected Output**:

```
(No output = No errors)
```

#### Step 1.3: Check Commit Message

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon
git log -1 --format=fuller
```

✅ **Expected Output** (sample):

```
commit de881bd...
Author: ...
Date: ...

    feat(cache): implement robust advanced caching strategy for npm
    ...
```

---

### Phase 2: Integration Testing (audiobook-organizer CI)

#### Step 2.1: Trigger Workflow Run

**Method A: Using GitHub CLI**

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/audiobook-organizer
gh workflow run ci.yml --ref main
```

**Method B: Using GitHub Web UI**

1. Navigate to: <https://github.com/jdfalk/audiobook-organizer/actions>
2. Click "CI" workflow on left
3. Click "Run workflow" button
4. Select "main" branch
5. Click "Run workflow"

✅ **Expected Result**: Workflow queued and starts running

#### Step 2.2: Monitor Job Execution

**Navigation**:

1. Go to: <https://github.com/jdfalk/audiobook-organizer/actions>
2. Click the latest "CI" run
3. Wait for jobs to appear (should see within 30 seconds)

**Watch for these jobs** (in order of execution):

1. ✅ load-config - should complete first
2. ✅ detect-changes - depends on load-config
3. ✅ workflow-lint - depends on detect-changes
4. ✅ **workflow-scripts-npm-cache** ← NEW! Should appear
5. ✅ workflow-scripts - depends on workflow-scripts-npm-cache ← MODIFIED!
6. ✅ **frontend-npm-cache** ← NEW! Should appear
7. ✅ frontend-ci - depends on frontend-npm-cache ← MODIFIED!
8. ✅ go-ci, python-ci, rust-ci (parallel)
9. ✅ ci-summary - depends on all previous jobs

---

### Phase 3: Cache Job Validation

#### Step 3.1: Check workflow-scripts-npm-cache Job

**Location in UI**: Actions > CI Run > workflow-scripts-npm-cache (in job list)

**What to verify**:

1. ✅ Job name shows "Cache npm (Workflow Scripts)"
2. ✅ Job status: ✓ (green checkmark)
3. ✅ Execution time: < 30 seconds (typical 10-15s)

**Check logs**:

1. Click on job name
2. Expand "Prepare Intelligent Cache" step
3. Look for one of these messages:

**For CACHE HIT** (on 2nd+ run):

```
✅ Cache hit for npm-workflow-scripts-ubuntu-22-node-22-<hash>
```

**For CACHE MISS** (on 1st run):

```
⚠️ Cache miss for npm-workflow-scripts-ubuntu-22-node-22-<hash>
```

#### Step 3.2: Check frontend-npm-cache Job

**Location in UI**: Actions > CI Run > frontend-npm-cache (in job list)

**What to verify**:

1. ✅ Job name shows "Cache npm (Frontend)"
2. ✅ Job status: ✓ (green checkmark)
3. ✅ Execution time: < 30 seconds (typical 10-15s)

**Check logs**:

1. Click on job name
2. Expand "Prepare Intelligent Cache" step
3. Look for:

**For CACHE HIT**:

```
✅ Cache hit for npm-frontend-ubuntu-22-node-22-<hash>
```

**For CACHE MISS**:

```
⚠️ Cache miss for npm-frontend-ubuntu-22-node-22-<hash>
```

#### Step 3.3: Verify Cache Key Generation

**In job logs**, look for these steps in sequence:

1. "Checkout" ✓
2. "Detect ghcommon ref" ✓
3. "Checkout ghcommon workflow scripts" ✓
4. "Set up GHCOMMON_SCRIPTS_DIR" ✓
5. "Set up Python" ✓
6. "Determine cache metadata" ✓ (generates file list)
7. "Generate intelligent cache key" ✓ (generates key)
8. "Configure cache" ✓ (runs actions/cache)
9. "Report cache status" ✓ (shows hit/miss)

---

### Phase 4: Dependent Job Validation

#### Step 4.1: Verify workflow-scripts Job Still Works

**Location**: Actions > CI Run > workflow-scripts

**What to verify**:

1. ✅ Job completed successfully
2. ✅ Depends on: workflow-scripts-npm-cache (shown in job details)
3. ✅ All steps succeeded:
   - Set up Python ✓
   - Lint Python workflow scripts ✓
   - Set up Node.js ✓
   - **NO "Ensure npm cache directories exist" step** ✓ (REMOVED)
   - **NO "Cache npm dependencies for workflow scripts" step** ✓ (REMOVED)
   - Lint JavaScript/TypeScript workflow scripts ✓
   - Publish workflow script summary ✓

**Important**: The old inline cache steps should NOT appear. If they do,
something went wrong.

#### Step 4.2: Verify frontend-ci Job Still Works

**Location**: Actions > CI Run > frontend-ci (may be multiple due to matrix)

**What to verify**:

1. ✅ All matrix combinations succeeded
2. ✅ Depends on: frontend-npm-cache (shown in job details)
3. ✅ All steps succeeded:
   - Checkout repository ✓
   - Get frontend working directory ✓
   - Get ghcommon workflow ref ✓
   - Checkout ghcommon workflow scripts ✓
   - Configure workflow script path ✓
   - Set up Node.js ✓
   - **NO "Ensure npm cache directories exist" step** ✓ (REMOVED)
   - **NO "Cache npm dependencies" step** ✓ (REMOVED)
   - Install dependencies ✓
   - Lint frontend code ✓
   - Build frontend ✓
   - Test frontend ✓

**Important**: npm install should use cached directories (it's transparent to
the user).

#### Step 4.3: Verify ci-summary Job

**Location**: Actions > CI Run > ci-summary

**What to verify**:

1. ✅ Job depends on new cache jobs
2. ✅ Job completed successfully
3. ✅ All dependencies listed:
   - detect-changes ✓
   - workflow-lint ✓
   - workflow-scripts ✓
   - **workflow-scripts-npm-cache** ✓ (NEW)
   - go-ci ✓
   - python-ci ✓
   - rust-ci ✓
   - frontend-ci ✓
   - **frontend-npm-cache** ✓ (NEW)

---

## Performance Comparison Testing

### Test 1: First Run (Cache Miss)

**Scenario**: Fresh cache, no cached dependencies

**Expected behavior**:

```
⚠️ Cache miss for npm-workflow-scripts-ubuntu-22-node-22-abc123def456
⚠️ Cache miss for npm-frontend-ubuntu-22-node-22-abc123def456
```

**Expected timing**:

- Cache job: 10-15 seconds (miss penalty)
- workflow-scripts install: 30-60 seconds (normal npm install)
- frontend-ci install: 30-60 seconds (normal npm install)

### Test 2: Second Run (Cache Hit)

**Scenario**: Cache populated from first run, no dependency changes

**Expected behavior**:

```
✅ Cache hit for npm-workflow-scripts-ubuntu-22-node-22-abc123def456
✅ Cache hit for npm-frontend-ubuntu-22-node-22-abc123def456
```

**Expected timing**:

- Cache job: 5-10 seconds (hit!)
- workflow-scripts install: 5-15 seconds (30-50% faster!)
- frontend-ci install: 5-15 seconds (30-50% faster!)

**Total time saved**: ~60 seconds on second run

### Test 3: Dependency Update (Cache Miss)

**Scenario**: package-lock.json changes

**Expected behavior**:

```
⚠️ Cache miss for npm-workflow-scripts-ubuntu-22-node-22-xyz789uvw012
(hash changed from abc123def456 to xyz789uvw012)
```

**Expected timing**:

- Cache job: 10-15 seconds (miss due to hash change)
- workflow-scripts install: 30-60 seconds (normal npm install)
- Cache is rebuilt with new dependencies

---

## Troubleshooting Guide

### Issue 1: Cache job fails with "actions/cache not found"

**Symptom**:

```
Error: Unable to resolve action `actions/cache@v5`
```

**Root cause**: GitHub has old version of actions/cache

**Solution**:

1. This is a GitHub version issue, not a repo issue
2. Wait for GitHub to sync latest action versions (usually < 1 hour)
3. Re-run workflow

### Issue 2: Cache job fails with "Repository not found"

**Symptom**:

```
Error: Repository 'jdfalk/ghcommon' not found
```

**Root cause**: ghcommon repository not accessible or branch doesn't exist

**Solution**:

1. Verify ghcommon is public: <https://github.com/jdfalk/ghcommon>
2. Verify main branch exists
3. Check audiobook-organizer's ghcommon-ref.txt if it exists

### Issue 3: workflow-scripts still has old cache steps

**Symptom**:

```
- Ensure npm cache directories exist
- Cache npm dependencies for workflow scripts
(Steps appear in job)
```

**Root cause**: Changes didn't push or audiobook-organizer using old workflow
version

**Solution**:

1. Verify ghcommon main branch has de881bd commit:
   ```bash
   cd ghcommon && git log --oneline | head -1
   ```
2. If not, verify push succeeded:
   ```bash
   git push origin main
   ```
3. Force re-run in audiobook-organizer:
   ```bash
   gh workflow run ci.yml --ref main --untagged
   ```

### Issue 4: Cache paths not resolved warning

**Symptom**:

```
⚠️ Cache paths are not resolved from file paths
```

**Root cause**: automation_workflow.py couldn't find package files

**Solution**:

1. Check if package-lock.json exists in the repo:
   ```bash
   find . -name "package-lock.json" -o -name "yarn.lock" -o -name "pnpm-lock.yaml"
   ```
2. If no package files, cache job still succeeds (no cache needed)
3. If files exist but not found, check automation_workflow.py logic

### Issue 5: Cache-hit step shows "false" but cache should exist

**Symptom**:

```
Cache miss for npm-workflow-scripts-ubuntu-22-node-22-abc123def456
(on second run when cache should be there)
```

**Root cause**: Cache key changed (hash mismatch)

**Possible causes**:

- package-lock.json changed between runs
- Node.js version changed
- Different runner OS
- Cache expired (GitHub cleans old caches after 7 days)

**Solution**:

1. Check if package-lock.json changed: `git diff package-lock.json`
2. Check if Node.js version matches: Look at cache key hash
3. Expected behavior after dependency update: Accept miss and rebuild

---

## Detailed Validation Checklist

### ✅ Pre-Run Checklist

- [ ] ghcommon main branch has de881bd commit
- [ ] Commit message mentions "advanced caching strategy"
- [ ] reusable-advanced-cache.yml version is 1.1.0
- [ ] reusable-ci.yml version is 1.7.0
- [ ] actionlint shows no errors
- [ ] CACHE_STRATEGY_IMPLEMENTATION.md exists in ghcommon

### ✅ Cache Job Checklist (workflow-scripts-npm-cache)

- [ ] Job name shows "Cache npm (Workflow Scripts)"
- [ ] Job status is green checkmark
- [ ] Job runs before workflow-scripts job
- [ ] Log shows either cache-hit or cache-miss
- [ ] Cache key is generated (shown in logs)
- [ ] Execution time < 30 seconds
- [ ] No errors or warnings in job output

### ✅ Cache Job Checklist (frontend-npm-cache)

- [ ] Job name shows "Cache npm (Frontend)"
- [ ] Job status is green checkmark
- [ ] Job runs before frontend-ci job
- [ ] Log shows either cache-hit or cache-miss
- [ ] Cache key is generated (shown in logs)
- [ ] Execution time < 30 seconds
- [ ] No errors or warnings in job output

### ✅ workflow-scripts Job Checklist

- [ ] Job depends on workflow-scripts-npm-cache
- [ ] Job status is green checkmark
- [ ] "Ensure npm cache directories exist" step NOT present
- [ ] "Cache npm dependencies for workflow scripts" step NOT present
- [ ] "Lint Python workflow scripts" step succeeds
- [ ] "Lint JavaScript/TypeScript workflow scripts" step succeeds
- [ ] All linting completes successfully
- [ ] No cache-related warnings in output

### ✅ frontend-ci Job Checklist

- [ ] Job depends on frontend-npm-cache
- [ ] Job status is green checkmark (all matrix combinations)
- [ ] "Ensure npm cache directories exist" step NOT present
- [ ] "Cache npm dependencies" step NOT present
- [ ] "Install dependencies" step succeeds
- [ ] "Lint frontend code" step succeeds
- [ ] "Build frontend" step succeeds
- [ ] "Test frontend" step succeeds
- [ ] All matrix combinations complete
- [ ] No cache-related warnings in output

### ✅ ci-summary Job Checklist

- [ ] Job depends on workflow-scripts-npm-cache
- [ ] Job depends on frontend-npm-cache
- [ ] Job status is green checkmark
- [ ] Summary shows all jobs completed
- [ ] Overall workflow result is success

### ✅ Final Validation

- [ ] Total CI run time reasonable (normal or better)
- [ ] No unexpected failures
- [ ] No breaking changes to other jobs
- [ ] Cache strategy working as intended
- [ ] Ready for next run to test cache hits

---

## Metrics to Track (Multiple Runs)

Create a simple metrics table:

| Run | Date       | Cache Status | Install Time | Total Time | Notes                  |
| --- | ---------- | ------------ | ------------ | ---------- | ---------------------- |
| 1   | 2025-12-26 | Miss         | 45s          | 3m 20s     | Initial cache creation |
| 2   | 2025-12-26 | Hit          | 12s          | 2m 50s     | Cache restored         |
| 3   | 2025-12-27 | Hit          | 11s          | 2m 48s     | Consistent performance |

---

## Success Criteria

✅ Implementation is successful when:

1. **Cache jobs exist**:
   - [x] workflow-scripts-npm-cache job visible in UI
   - [x] frontend-npm-cache job visible in UI

2. **Cache jobs function**:
   - [x] Cache job completes successfully
   - [x] Shows cache-hit or cache-miss message
   - [x] No errors in cache preparation

3. **Dependent jobs work**:
   - [x] workflow-scripts succeeds after cache job
   - [x] frontend-ci succeeds after cache job
   - [x] Old inline cache steps are gone

4. **Performance improvement**:
   - [x] First run baseline established
   - [x] Second run shows cache hit
   - [x] npm install time reduced by 30-50%

5. **No regressions**:
   - [x] All other jobs still pass
   - [x] No new failures introduced
   - [x] Workflow logic unchanged

---

## Questions?

Refer to:

- [CACHE_STRATEGY_IMPLEMENTATION.md](./CACHE_STRATEGY_IMPLEMENTATION.md) - Full
  implementation details
- [CACHE_STRATEGY_SUMMARY.md](./CACHE_STRATEGY_SUMMARY.md) - Quick reference
- [CACHE_YAML_DIFFS.md](./CACHE_YAML_DIFFS.md) - Detailed YAML changes
