<!-- file: docs/cross-registry-todos/task-09/t09-part1.md -->
<!-- version: 1.0.0 -->
<!-- guid: t09-ci-migration-testing-part1-h3i4j5k6-l7m8 -->

# Task 09 Part 1: CI Workflow Migration & Testing - Overview

## Task Overview

**Priority:** 3 (High) **Estimated Lines:** ~3,500 lines (6 parts) **Complexity:** High
**Dependencies:** Task 08 (Consolidated CI Workflow)

## Objective

Complete the migration of all repositories from legacy CI workflows to the consolidated reusable
workflow. Ensure thorough testing at each step, validate functionality, and verify that all features
work correctly across different repository types.

## What This Task Accomplishes

### Primary Goals

1. **Phase Migration**: Systematic rollout of consolidated workflow
2. **Repository Testing**: Comprehensive test coverage for each repo type
3. **Validation Framework**: Automated verification of migrations
4. **Rollback Procedures**: Safety mechanisms for failed migrations
5. **Documentation**: Complete migration records and lessons learned
6. **Team Training**: Knowledge transfer and onboarding

### Migration Phases

#### Phase 1: ghcommon (Self-Migration)

**Repository:** `jdfalk/ghcommon` **Rationale:** Test consolidated workflow in its home repository
first **Risk:** Low (can iterate quickly)

**Steps:**

1. Create consolidated workflow file
2. Test with workflow_dispatch
3. Update existing CI to call consolidated workflow
4. Verify all features working
5. Monitor for 1 week
6. Remove old workflow

#### Phase 2: ubuntu-autoinstall-agent (Complex Migration)

**Repository:** `jdfalk/ubuntu-autoinstall-agent` **Rationale:** Most complex CI implementation,
best test case **Risk:** Medium (has advanced features)

**Steps:**

1. Create repository-config.yml
2. Test consolidated workflow with workflow_dispatch
3. Run both workflows in parallel
4. Compare results
5. Switch to consolidated workflow
6. Monitor for 2 weeks
7. Remove old workflow

#### Phase 3: Remaining Repositories

**Repositories:** All other repos using ghcommon workflows **Rationale:** Apply lessons learned from
Phases 1-2 **Risk:** Low (proven pattern)

**Steps:**

1. Batch migrate similar repositories
2. Use standardized repository-config.yml templates
3. Automated testing with migration scripts
4. Coordinated switchover
5. Monitoring period
6. Cleanup old workflows

## Repository Inventory

### High-Priority Repositories (Complex CI)

| Repository               | Languages     | Current CI       | Features           | Migration Priority |
| ------------------------ | ------------- | ---------------- | ------------------ | ------------------ |
| ghcommon                 | Python, Shell | reusable-ci.yml  | Workflows, Scripts | 1 (First)          |
| ubuntu-autoinstall-agent | Rust, Python  | ci.yml (complex) | Coverage, Security | 2 (Second)         |

### Medium-Priority Repositories (Standard CI)

| Repository | Languages  | Current CI      | Migration Complexity |
| ---------- | ---------- | --------------- | -------------------- |
| repo-3     | Go         | reusable-ci.yml | Low                  |
| repo-4     | Python     | reusable-ci.yml | Low                  |
| repo-5     | TypeScript | reusable-ci.yml | Medium               |

### Low-Priority Repositories (Simple CI)

| Repository | Languages | Current CI   | Migration Complexity |
| ---------- | --------- | ------------ | -------------------- |
| repo-6     | Go        | basic-ci.yml | Very Low             |
| repo-7     | Python    | basic-ci.yml | Very Low             |

## Pre-Migration Checklist

### 1. Consolidated Workflow Ready

- [ ] reusable-ci-consolidated.yml created in ghcommon
- [ ] All features implemented (from Task 08)
- [ ] Workflow syntax validated
- [ ] Inputs/outputs documented
- [ ] Job dependencies correct

### 2. Testing Infrastructure

- [ ] Test workflows created
- [ ] Validation scripts ready
- [ ] Comparison tools installed
- [ ] Monitoring dashboards configured

### 3. Documentation

- [ ] Migration guide written
- [ ] Repository-config.yml templates created
- [ ] Troubleshooting guide available
- [ ] Team communication plan ready

### 4. Rollback Plan

- [ ] Old workflows backed up
- [ ] Rollback procedure documented
- [ ] Emergency contacts identified
- [ ] Incident response plan ready

### 5. Team Readiness

- [ ] Team notified of migration schedule
- [ ] Training materials distributed
- [ ] Q&A session held
- [ ] Support channel established

## Migration Testing Strategy

### Test Categories

#### 1. Smoke Tests (Quick Validation)

**Purpose:** Verify basic functionality **Duration:** 5-10 minutes **Frequency:** After every change

**Tests:**

- Workflow triggers correctly
- Change detection works
- Jobs execute in correct order
- Basic build/test passes
- Artifacts uploaded

**Script:**

```bash
#!/bin/bash
# file: scripts/smoke-test-migration.sh
# version: 1.0.0
# guid: smoke-test-migration-script

echo "=== Running Smoke Tests ==="

# 1. Trigger workflow
gh workflow run ci.yml --ref migration-test

# 2. Wait for completion
run_id=$(gh run list --workflow=ci.yml --limit 1 --json databaseId -q '.[0].databaseId')
gh run watch $run_id

# 3. Check status
status=$(gh run view $run_id --json conclusion -q '.conclusion')

if [ "$status" = "success" ]; then
  echo "✅ Smoke test passed"
  exit 0
else
  echo "❌ Smoke test failed"
  exit 1
fi
```

#### 2. Integration Tests (Feature Validation)

**Purpose:** Verify all features work together **Duration:** 20-30 minutes **Frequency:** After
significant changes

**Tests:**

- All language jobs execute
- Coverage reports generated
- Security scans complete
- Docker builds succeed
- All artifacts present

**Script:**

```bash
#!/bin/bash
# file: scripts/integration-test-migration.sh
# version: 1.0.0
# guid: integration-test-migration-script

echo "=== Running Integration Tests ==="

# Test all features enabled
gh workflow run test-all-features.yml

run_id=$(gh run list --workflow=test-all-features.yml --limit 1 --json databaseId -q '.[0].databaseId')
gh run watch $run_id

# Verify artifacts
artifacts=$(gh run view $run_id --json artifacts -q '.artifacts | length')

if [ "$artifacts" -ge 5 ]; then
  echo "✅ Integration tests passed ($artifacts artifacts)"
  exit 0
else
  echo "❌ Integration tests failed (only $artifacts artifacts)"
  exit 1
fi
```

#### 3. Comparison Tests (Feature Parity)

**Purpose:** Ensure new workflow matches old workflow behavior **Duration:** 30-60 minutes
**Frequency:** Before migration

**Tests:**

- Run both workflows simultaneously
- Compare test results
- Compare coverage numbers
- Compare artifact contents
- Compare execution time

**Script:**

```bash
#!/bin/bash
# file: scripts/compare-workflows.sh
# version: 1.0.0
# guid: compare-workflows-script

echo "=== Comparing Old vs New Workflows ==="

# Run old workflow
gh workflow run old-ci.yml
old_run=$(gh run list --workflow=old-ci.yml --limit 1 --json databaseId -q '.[0].databaseId')

# Run new workflow
gh workflow run ci.yml
new_run=$(gh run list --workflow=ci.yml --limit 1 --json databaseId -q '.[0].databaseId')

# Wait for both
gh run watch $old_run &
gh run watch $new_run &
wait

# Compare results
echo "Old workflow: $(gh run view $old_run --json conclusion -q '.conclusion')"
echo "New workflow: $(gh run view $new_run --json conclusion -q '.conclusion')"

# Compare artifacts
echo "Old artifacts: $(gh run view $old_run --json artifacts -q '.artifacts | length')"
echo "New artifacts: $(gh run view $new_run --json artifacts -q '.artifacts | length')"

# Compare timing
old_time=$(gh run view $old_run --json timing -q '.timing.run_duration_ms')
new_time=$(gh run view $new_run --json timing -q '.timing.run_duration_ms')

echo "Old duration: $((old_time / 60000)) minutes"
echo "New duration: $((new_time / 60000)) minutes"
```

#### 4. Load Tests (Scalability)

**Purpose:** Verify performance under load **Duration:** 1-2 hours **Frequency:** Before production
deployment

**Tests:**

- Multiple concurrent runs
- Large file sets
- Maximum matrix sizes
- Artifact size limits
- Cache performance

**Script:**

```python
#!/usr/bin/env python3
# file: scripts/load-test-migration.py
# version: 1.0.0
# guid: load-test-migration-script

"""
Load testing for CI workflow migration.
Tests concurrent execution and resource limits.
"""

import subprocess
import time
import concurrent.futures

def trigger_workflow():
    """Trigger a workflow run."""
    result = subprocess.run(
        ["gh", "workflow", "run", "ci.yml"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def main():
    print("=== Running Load Tests ===")

    # Trigger 10 concurrent workflow runs
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(trigger_workflow) for _ in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_count = sum(results)
    print(f"✅ {success_count}/10 workflows triggered successfully")

    # Monitor execution
    time.sleep(60)  # Wait for workflows to start

    # Check running workflows
    result = subprocess.run(
        ["gh", "run", "list", "--limit", "20", "--json", "status"],
        capture_output=True,
        text=True
    )

    import json
    runs = json.loads(result.stdout)
    in_progress = sum(1 for run in runs if run['status'] == 'in_progress')

    print(f"Workflows in progress: {in_progress}")

    if in_progress >= 5:
        print("✅ Load test passed (multiple workflows running)")
    else:
        print("⚠️  Load test warning (low concurrency)")

if __name__ == "__main__":
    main()
```

#### 5. Regression Tests (No Breaking Changes)

**Purpose:** Ensure no functionality lost **Duration:** 30-45 minutes **Frequency:** Before each
migration

**Tests:**

- All previous tests still pass
- No new failures introduced
- Coverage not decreased
- Build times not increased significantly
- All features still accessible

## Success Criteria

### Technical Criteria

- [ ] All tests passing in consolidated workflow
- [ ] Coverage equivalent or better than old workflow
- [ ] No security regressions
- [ ] Execution time within 20% of old workflow
- [ ] All artifacts generated correctly
- [ ] No permission issues
- [ ] Documentation complete

### Business Criteria

- [ ] Zero downtime during migration
- [ ] No impact on development velocity
- [ ] Team comfortable with new workflow
- [ ] Support requests minimal
- [ ] Rollback not required

## Risk Assessment

### High Risk Scenarios

| Risk                                  | Probability | Impact | Mitigation                       |
| ------------------------------------- | ----------- | ------ | -------------------------------- |
| Breaking changes in reusable workflow | Medium      | High   | Extensive testing, parallel runs |
| Permission issues                     | Low         | Medium | Test with minimal permissions    |
| Performance degradation               | Low         | Medium | Load testing, monitoring         |
| Feature gaps                          | Medium      | High   | Comprehensive feature comparison |

### Mitigation Strategies

1. **Parallel Execution**: Run both workflows simultaneously during transition
2. **Staged Rollout**: Migrate one repository at a time
3. **Monitoring**: Watch key metrics closely
4. **Quick Rollback**: Keep old workflows for easy reversion
5. **Team Communication**: Regular updates and Q&A sessions

## Timeline

### Phase 1: ghcommon (Week 1-2)

- **Week 1**: Implementation and testing
- **Week 2**: Monitoring and validation

### Phase 2: ubuntu-autoinstall-agent (Week 3-5)

- **Week 3**: Configuration and testing
- **Week 4**: Parallel execution
- **Week 5**: Switchover and monitoring

### Phase 3: Remaining Repositories (Week 6-8)

- **Week 6**: Batch configuration
- **Week 7**: Batch migration
- **Week 8**: Monitoring and cleanup

### Phase 4: Cleanup and Documentation (Week 9-10)

- **Week 9**: Remove old workflows
- **Week 10**: Final documentation and retrospective

## Next Steps

**Continue to Part 2:** Detailed migration procedure for ghcommon repository (Phase 1).
