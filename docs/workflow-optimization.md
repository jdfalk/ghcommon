# Workflow Optimization Audit

This document captures the current state of the `ghcommon` workflows and reusable workflows, identifies the main inefficiencies, and proposes improvements aligned with the single source of truth in `.github/repository-config.yml`.

## Guiding Principles

- **Repository-config first:** Workflows should read defaults and toggles from `.github/repository-config.yml` instead of hardcoding matrices and feature flags. Dispatch inputs override, but automatic behaviour should come from config.
- **Reusable > bespoke:** Shared logic belongs in reusable workflows or helper scripts. Inline shell should be avoided when the logic is complex or needed in multiple jobs.
- **Single checkout of ghcommon:** Consumers should not need to re-checkout ghcommon when the workflow already ships the required scripts.
- **Test the helpers:** Every helper script should have direct unit-level coverage and a workflow that exercises the suite (`workflow-scripts-tests.yml`).

## Summary by Workflow

| Workflow | Current Role | Status | Inefficiencies | Recommendation |
| --- | --- | --- | --- | --- |
| `ci.yml` | Delegates to `reusable-ci.yml` | ✅ updated | – | Keep delegating; requires downstream adoption of new helper script flow |
| `ci-tests.yml` | Legacy full-matrix test runner | ⚠️ | Duplicates new reusable CI behaviour, manual path filters, hard-coded matrices | Deprecate in favour of `reusable-ci.yml` or refactor to call targeted reusable components driven by repository-config flags |
| `release.yml` | Calls `reusable-release.yml` | ⚠️ | Dispatch inputs mirror config, duplication for per-language jobs | Extend `reusable-release.yml` to inspect config for enabled languages and build matrices. Remove redundant per-language release workflows once consolidated |
| `release-go.yml`, `release-python.yml`, `release-rust.yml`, `release-frontend.yml`, `release-docker.yml`, `release-protobuf.yml` | Language-specific release orchestrators | ⚠️ | Near-identical scaffolding, manual environment configuration, inconsistent artefact handling | Fold into `reusable-release.yml` with modular jobs toggled by repository-config values. Expose hooks for language-specific steps via scripts |
| `reusable-ci.yml` | Shared CI pipeline | ✅ updated | – | Already converted to python helpers; next iteration should source matrices (versions, OS) from repository-config and expose skip flags via config |
| `reusable-release.yml` | Shared release/cut pipeline | ⚠️ | Heavy reliance on bash scripts, second checkout of ghcommon, duplicated detection logic | Replace shell helpers with python equivalents (mirroring `ci_workflow.py`), load repository-config once, and emit outputs consumed by language jobs |
| `reusable-maintenance.yml`, `reusable-security.yml`, `maintenance.yml`, `security.yml`, `performance-monitoring.yml` | Scheduled maintenance/security tasks | ⚠️ | Hard-coded schedules and behaviours, minimal config integration | Add parsing of repository-config maintenance/security sections for schedule, tooling, thresholds |
| `documentation.yml` | Docs verification | ⚠️ | Inline placeholder shell steps, not driven by config | Convert to python helper (e.g., docs_workflow.py) that reads doc tooling from config |
| `unified-automation.yml`, `issue-automation.yml`, `pr-automation.yml` | Labeling & automation | ⚠️ | Combination of inline scripts and Node entries that duplicate logic already present in scripts | Migrate to python helpers (existing `intelligent_labeling.py`, etc.) and ensure config-driven toggles |
| `auto-module-tagging.yml`, `manager-sync-dispatcher.yml` | Repo synchronisation | ❔ | Behaviour predates repository-config | Evaluate once initial CI/Release consolidation completes |
| `sync-receiver.yml` | Sync entry point | ✅ updated | – | Keep; new python helper already installed |

## High-impact Changes

1. **Repository-config driven matrices:**
   - Extend `ci_workflow.py` to consume `languages.versions` and `build.platforms` from config, eliminating hard-coded version lists.
   - Update `reusable-ci.yml` to request the parsed config and feed it into helper commands.

2. **Release consolidation:**
   - Introduce a `release_workflow.py` helper mirroring the CI helper style (language detection, versioning, artefact mapping based on config).
   - Rewire `reusable-release.yml` to call helper subcommands instead of bash scripts and to emit a structured build plan per language.
   - Replace per-language release workflows with thin wrappers around the new release helper (or integrate the jobs directly in the reusable workflow using dynamic matrices).

3. **Maintenance/Security integration:**
   - Create a `maintenance_workflow.py` helper that reads the `maintenance` and `security` sections of repository-config to determine schedule, tooling, and thresholds.
   - Update `reusable-maintenance.yml` and `reusable-security.yml` to run scripted steps using this helper instead of inline bash.

4. **Documentation validation:**
   - Replace placeholder echo steps in `documentation.yml` with calls to a new helper that can optionally run vale, markdownlint, or other tooling defined in config.

5. **Automation workflows:**
   - Consolidate issue/PR automation under a single reusable workflow that reads `automation.issues` and `automation.pull_requests` sections from config.
   - The existing Python scripts (`intelligent_labeling.py`, etc.) should be invoked from that reusable workflow with inputs derived from config (auto-merge toggles, label rules, etc.).

## Roadmap

1. **Phase 1 (current work)**
   - ✅ CI workflow scripted helpers and tests (`ci_workflow.py`).
   - ✅ Sync receiver helper conversion.
   - ☐ Repository-config parsing for CI matrices.

2. **Phase 2**
   - Implement `release_workflow.py` helper and migrate `reusable-release.yml`.
   - Merge per-language release workflows into reusable release (deprecate single-language ones after confirmation).
   - Add unit tests mirroring the CI helper suite.

3. **Phase 3**
   - Build maintenance/security helper and retrofit reusable workflows.
   - Expand documentation workflow to honour config toggles.
   - Rationalise `ci-tests.yml` (either remove or wire into reusable CI).

4. **Phase 4**
   - Reassess automation workflows, consolidating scripts and enabling config-driven behaviour.
   - Document the new workflow architecture in `docs/` with examples for consumer repositories.

## Implementation Notes

- Helpers should live under `.github/workflows/scripts/` with pytest coverage in `tests/workflow_scripts/`.
- Each reusable workflow should have a matching entry in `.github/workflows/workflow-scripts-tests.yml` once new helpers land.
- When deprecating legacy workflows (e.g., per-language release ones), keep them temporarily but emit warnings pointing maintainers to the consolidated workflow.
- Promote the helper scripts as versioned assets if we want external repos to pin specific revisions instead of fetching `main`.

## Next Actions

1. Add repository-config parsing to `ci_workflow.py` for matrices and pass config JSON through reusable CI.
2. Draft `release_workflow.py` and start migrating bash helpers.
3. Schedule follow-up issues for maintenance/security/doc automation updates using this audit as the spec.

---

# Detailed Implementation Guide

The remainder of this document is a step-by-step playbook aimed at a junior engineer. It spells out **what to change**, **why the change matters**, and **how to verify** each step with concrete commands, sample code, and expected outputs.

---

## Phase 1 – CI Pipeline Modernisation (Status: ✅ In-progress)

### Goal
Move the reusable CI workflow (`.github/workflows/reusable-ci.yml`) and its helper (`ci_workflow.py`) to be fully driven by `.github/repository-config.yml`.

### Step-by-step
1. **Load config once**
   ```yaml
   jobs:
     load-config:
       name: Load Repository Configuration
       runs-on: ubuntu-latest
       outputs:
         config: ${{ steps.load.outputs.config }}
         has-config: ${{ steps.load.outputs.has-config }}
       steps:
         - uses: actions/checkout@v5
         - id: load
           env:
             CONFIG_FILE: .github/repository-config.yml
           run: python3 .github/workflows/scripts/load_repository_config.py
   ```
   *Expected output*: `config` (JSON string) and `has-config` booleans written to `GITHUB_OUTPUT`.

2. **Generate language matrices**
   ```yaml
       - id: matrices
         env:
           REPOSITORY_CONFIG: ${{ steps.load.outputs.config }}
           FALLBACK_GO_VERSION: ${{ inputs.go-version }}
           FALLBACK_PYTHON_VERSION: ${{ inputs.python-version }}
           FALLBACK_RUST_VERSION: ${{ inputs.rust-version }}
           FALLBACK_NODE_VERSION: ${{ inputs.node-version }}
           FALLBACK_COVERAGE_THRESHOLD: ${{ inputs.coverage-threshold }}
         run: python3 .github/workflows/scripts/ci_workflow.py generate-matrices
   ```
   This populates matrix JSON for Go/Python/Rust/Frontend and a fallback coverage threshold.

3. **Update language jobs to consume matrices**

   Example (Go):
   ```yaml
   go-ci:
     needs: [load-config, detect-changes]
     if: needs.detect-changes.outputs.go-files == 'true'
     strategy:
       fail-fast: false
       matrix: ${{ fromJSON(needs.load-config.outputs.go-matrix) }}
     runs-on: ${{ matrix.os }}
     env:
       REPOSITORY_CONFIG: ${{ needs.load-config.outputs.config }}
   ```

4. **Helper updates (`ci_workflow.py`)**
   - Add `generate_matrices`, `go_setup`, `go_test`, `_config_path`, etc.
   - Use repository-config to determine coverage threshold if `COVERAGE_THRESHOLD` env var not set.

5. **Unit tests**
   ```bash
   python -m pytest tests/workflow_scripts/test_ci_workflow.py -vv
   ```
   *Expected*: All tests including `test_generate_matrices_uses_repository_config` pass.

6. **Integration test**
   ```bash
   python -m pytest tests/workflow_scripts -vv
   ```

7. **Document in `docs/workflow-optimization.md`** (this file) and update changelog if needed.

### Example config snippet
```yaml
languages:
  versions:
    go: ["1.22", "1.23", "1.24"]
    python: ["3.11", "3.12", "3.13"]
build:
  platforms:
    os: ["ubuntu-latest", "macos-latest"]
testing:
  coverage:
    threshold: 85
```

### Checklist
- [x] `load-config` job exists.
- [x] Matrices produced via helper.
- [x] Language jobs use generated matrix.
- [x] All helper tests pass.
- [x] `workflow-scripts-tests.yml` runs green in CI.

---

## Phase 2 – Release Pipeline Consolidation (Status: ☐ Not started)

### Goal
Replace shell-based release helpers with a Python module (`release_workflow.py`) and merge single-language release workflows into `reusable-release.yml`.

### Deliverables
- `release_workflow.py` with commands:
  - `detect-languages`
  - `release-strategy`
  - `generate-version`
  - `generate-changelog`
- Updated `reusable-release.yml` that invokes those commands.
- New tests in `tests/workflow_scripts/test_release_workflow.py`.
- Documentation updates explaining how to migrate consumers.

### Step-by-step
1. **Create helper skeleton**
   ```python
   # .github/workflows/scripts/release_workflow.py
   def detect_languages(args): ...
   def release_strategy(args): ...
   def generate_version(args): ...
   def generate_changelog(args): ...

   def build_parser():
       parser = argparse.ArgumentParser(...)
       ...
   ```

2. **Language detection logic**
   - Mirror `ci_workflow.generate_matrices`.
   - Respect overrides from workflow inputs.
   - Emit outputs used by job fan-out (Go, Python, Rust, Frontend, Docker, Protobuf).

3. **Versioning logic**
   - Use GitHub API (`/releases/latest`) with fallback to git tags.
   - Support `release-type` (auto/major/minor/patch) and branch-specific behaviour.
   - Auto-increment when tag already exists (avoid collisions).
   - Support manual re-run via `workflow_dispatch`.

4. **Changelog generation**
   - Use `git log` to collect commits since last tag.
   - Output Markdown summary with metadata.

5. **Update reusable workflow**
   ```yaml
   - id: detect
     env:
       REPOSITORY_CONFIG: ${{ needs.load-config.outputs.config }}
       SKIP_LANGUAGE_DETECTION: ${{ inputs.skip-language-detection }}
       ...
     run: python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" detect-languages
   ```
   Replace `bash` invocations for release strategy, version, changelog with equivalent Python commands.

6. **Merge per-language workflows**
   - Move build logic from `release-go.yml`, `release-python.yml`, etc. into conditional jobs inside `reusable-release.yml`.
   - Example snippet for Go:
     ```yaml
     build-go:
       needs: [detect-languages, build-protobuf]
       if: needs.detect-languages.outputs.has-go == 'true'
       strategy:
         matrix: ${{ fromJSON(needs.detect-languages.outputs.go-matrix) }}
       steps:
         - uses: actions/checkout@v5
         - uses: actions/setup-go@v6
           with:
             go-version: ${{ matrix["go-version"] }}
         - run: go build -v ./...
         - run: go test -v ./...
         - uses: actions/upload-artifact@v4
           with:
             name: go-build-${{ matrix.os }}-${{ matrix["go-version"] }}
             path: dist/
     ```
   - Repeat for Python, Rust, Frontend, Docker, Protobuf (reuse step templates from existing workflows).
   - Retain any language-specific publishing or packaging steps.

7. **Add unit tests**
   ```python
   def test_release_strategy_branch_defaults(...):
       ...
   def test_generate_version_from_tag(...):
       ...
   def test_generate_changelog(...):
       ...
   ```
   Run:
   ```bash
   python -m pytest tests/workflow_scripts/test_release_workflow.py -vv
   ```

8. **Integration tests**
   - Local smoke test (optional):
     ```bash
     act workflow_dispatch -W .github/workflows/release.yml -j release
     ```
   - Ensure YAML still validates:
     ```bash
     python -m yamlcheck .github/workflows/reusable-release.yml
     ```

9. **Deprecation plan**
   - Add comments to old per-language workflows (e.g., `release-go.yml`) stating they are superseded.
   - Update docs to point consumers at new reusable release.

### Example configuration-driven flow
```yaml
release:
  versioning:
    triggers:
      major: ["breaking", "feat!"]
  artifacts:
    types: ["binary", "archive"]
  changelog:
    enabled: true
    categories: ["Features", "Bug Fixes"]
```

### Checklist
- [ ] `release_workflow.py` exists with all commands.
- [ ] `reusable-release.yml` uses helper commands.
- [ ] Language jobs migrated or removed.
- [ ] Tests pass.
- [ ] Documentation updated (README, workflow guide, release guide).

---

## Phase 3 – Maintenance, Security, and Documentation Automation (Status: ☐ Backlog)

### Goal
Introduce config-driven maintenance/security/doc workflows using Python helpers and remove redundant workflows (`ci-tests.yml`, etc.).

### Tasks
1. **Create `maintenance_workflow.py`**
   - Expose commands: `maintenance-plan`, `dependency-update`, `cleanup`, `security-scan`.
   - Read sections `maintenance`, `security`, `notifications` from repository-config.
2. **Refactor `reusable-maintenance.yml` & `reusable-security.yml`**
   - Use helper commands for schedule and tooling (e.g., `pip-audit`, `cargo audit`, `npm audit`).
   - Generate a maintenance summary.
3. **Documentation workflow**
   - Add `docs_workflow.py`.
   - Support linters (`markdownlint`, `vale`), broken link checkers, custom commands.
4. **Retire `ci-tests.yml`**
   - Migrate necessary coverage/benchmark tasks into `reusable-ci.yml`.
5. **Tests**
   - Add `test_maintenance_workflow.py`, `test_docs_workflow.py`.
   - Expand `workflow-scripts-tests.yml` to run new suites.

### Example Implementation Blueprint
```python
# maintenance_workflow.py
def maintenance_plan(args):
    config = get_repository_config()
    schedule = _config_path("weekly", "maintenance", "dependencies", "schedule")
    updates_enabled = _config_path(True, "maintenance", "dependencies", "auto_update")
    write_output("schedule", schedule)
    write_output("updates-enabled", str(updates_enabled).lower())
```

### Verification
```bash
python -m pytest tests/workflow_scripts/test_maintenance_workflow.py -vv
python -m pytest tests/workflow_scripts/test_docs_workflow.py -vv
```

---

## Phase 4 – Automation & Long-tail Cleanup (Status: ☐ Backlog)

### Focus areas
- Rework issue/PR automation to be configuration-driven.
- Simplify sync/manager workflows after Phase 2 and 3 are stable.
- Clean up documentation to reflect new architecture.

### Concrete steps
1. **Automation helper**
   - Build `automation_workflow.py` handling label rules, auto-merge criteria, stale issues, etc.
   - Invoke from `reusable-issue-automation.yml` and `reusable-security.yml`.
2. **Sync workflows**
   - Re-evaluate `auto-module-tagging.yml`, `manager-sync-dispatcher.yml`.
   - Use config to determine target files/repos.
3. **Documentation**
   - Update `docs/README.md`, `docs/workflow-optimization.md`, project wiki.
   - Provide migration guide for consumer repositories.

### Long-term tasks
- Publish ghcommon workflow releases (e.g., `v1.0.0`) so consumers can pin versions.
- Improve developer onboarding with a “How to adopt ghcommon workflows” tutorial.
- Consider packaging helpers as a Python module if we need dependency management later.

---

# Appendix A – Sample Commands

| Purpose | Command |
| --- | --- |
| Run unit tests | `python -m pytest tests/workflow_scripts -vv` |
| Validate YAML | `pip install yamllint && yamllint .github/workflows/` |
| Run local workflow (optional) | `act workflow_dispatch -W .github/workflows/reusable-ci.yml` |
| Format Python (if needed) | `pip install black && black .github/workflows/scripts` |

---

# Appendix B – Sample Commit Messages and Tags

- **Commit**: `chore(ci): generate matrices from repository config`
- **Commit**: `refactor(release): use release_workflow helper`
- **Tag**: `v0.2.0` – first release after workflow consolidation
- **Release notes**:
  ```
  ## Highlights
  - Config-driven CI matrices (ghcommon#123)
  - Unified release pipeline with Python helper (ghcommon#145)
  ## Upgrade Notes
  - Update reusable workflow reference to ghcommon@v0.2.0
  ```

---

# Appendix C – Troubleshooting Cheat Sheet

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError` when running tests | Helper script not on `sys.path` | Ensure `tests/workflow_scripts/__init__.py` injects `.github/workflows/scripts` into `sys.path` |
| Matrices empty in CI | `REPOSITORY_CONFIG` not passed to helper | Check `load-config` job outputs and env propagation |
| Release tag conflict | Existing tag on branch | `workflow_dispatch` allows auto-delete; otherwise version increments automatically |
| Docker build skipped unexpectedly | `detect_docker_config.py` found no Dockerfile | Override with `dockerfile` input or ensure file exists |

---

# Appendix D – Suggested Timeline

| Week | Milestone | Artifacts |
| --- | --- | --- |
| Week 1 | Phase 1 completion | Updated CI workflow, helper tests |
| Week 2 | Phase 2 implementation | New release helper, consolidated release workflow, docs |
| Week 3 | Phase 3 work | Maintenance/doc helpers and tests |
| Week 4+ | Phase 4 & adoption support | Automation helper, onboarding docs, versioned tags |

---

## Final Notes for Implementers

- **Work incrementally**: each phase should result in a passing test suite and updated documentation.
- **Communicate**: share the workflow updates with downstream repositories and provide guidance on pinning new tags.
- **Automate validation**: ensure `workflow-scripts-tests.yml` runs as part of CI to catch regressions.
- **Document everything**: this file should evolve with each phase to keep instructions accurate for new contributors.

---

# Appendix E – Step-by-step Recipes (Copy/Paste Friendly)

This appendix contains exhaustive instructions that an AI or junior engineer can follow without additional guidance.

## E.1 Phase 1 – CI Modernisation

1. **Update `.github/workflows/scripts/ci_workflow.py`**
   - Replace the file contents with the canonical version below (copy all lines):

     ```python
     {{CI_WORKFLOW_CANONICAL}}
     ```

2. **Update `.github/workflows/reusable-ci.yml`**
   - Apply the diff (can be pasted into `git apply`):

     ```diff
     diff --git a/.github/workflows/reusable-ci.yml b/.github/workflows/reusable-ci.yml
     --- a/.github/workflows/reusable-ci.yml
     +++ b/.github/workflows/reusable-ci.yml
     @@
      jobs:
     +  load-config:
     +    name: Load Repository Configuration
     +    runs-on: ubuntu-latest
     +    outputs:
     +      config: ${{ steps.load.outputs.config }}
     +      has-config: ${{ steps.load.outputs.has-config }}
     +      go-matrix: ${{ steps.matrices.outputs.go-matrix }}
     +      python-matrix: ${{ steps.matrices.outputs.python-matrix }}
     +      rust-matrix: ${{ steps.matrices.outputs.rust-matrix }}
     +      frontend-matrix: ${{ steps.matrices.outputs.frontend-matrix }}
     +      coverage-threshold: ${{ steps.matrices.outputs.coverage-threshold }}
     +    steps:
     +      - uses: actions/checkout@v5
     +      - id: load
     +        env:
     +          CONFIG_FILE: .github/repository-config.yml
     +        run: python3 .github/workflows/scripts/load_repository_config.py
     +      - id: matrices
     +        env:
     +          REPOSITORY_CONFIG: ${{ steps.load.outputs.config }}
     +          FALLBACK_GO_VERSION: ${{ inputs.go-version }}
     +          FALLBACK_PYTHON_VERSION: ${{ inputs.python-version }}
     +          FALLBACK_RUST_VERSION: ${{ inputs.rust-version }}
     +          FALLBACK_NODE_VERSION: ${{ inputs.node-version }}
     +          FALLBACK_COVERAGE_THRESHOLD: ${{ inputs.coverage-threshold }}
     +        run: python3 .github/workflows/scripts/ci_workflow.py generate-matrices
     @@
      go-ci:
-    needs: detect-changes
-    runs-on: ubuntu-latest
+    needs: [load-config, detect-changes]
+    strategy:
+      fail-fast: false
+      matrix: ${{ fromJSON(needs.load-config.outputs.go-matrix) }}
+    runs-on: ${{ matrix.os }}
+    env:
+      REPOSITORY_CONFIG: ${{ needs.load-config.outputs.config }}
     @@
-      - uses: actions/setup-go@v6
-        with:
-          go-version: ${{ inputs.go-version }}
+      - uses: actions/setup-go@v6
+        with:
+          go-version: ${{ matrix.go-version }}
     ```
     *(Repeat matrix substitution blocks for Python, Rust, and Frontend jobs.)*

3. **Run tests**
   ```bash
   python -m pytest tests/workflow_scripts/test_ci_workflow.py -vv
   python -m pytest tests/workflow_scripts -vv
   ```

## E.2 Phase 2 – Release Consolidation

1. **Create/replace `.github/workflows/scripts/release_workflow.py`**
   ```python
   {{RELEASE_WORKFLOW_CANONICAL}}
   ```

2. **Update `.github/workflows/reusable-release.yml`**
   ```diff
   diff --git a/.github/workflows/reusable-release.yml b/.github/workflows/reusable-release.yml
   --- a/.github/workflows/reusable-release.yml
   +++ b/.github/workflows/reusable-release.yml
   @@
    - run: bash "$GHCOMMON_SCRIPTS_DIR/detect-languages.sh"
    + run: python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" detect-languages
   @@
    - run: bash "$GHCOMMON_SCRIPTS_DIR/release-strategy.sh"
    + run: python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" release-strategy
   @@
    - run: bash "$GHCOMMON_SCRIPTS_DIR/generate-version.sh"
    + run: python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" generate-version
   @@
    - run: bash "$GHCOMMON_SCRIPTS_DIR/generate-changelog.sh"
    + run: python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" generate-changelog
   ```

3. **Inline language build jobs** – copy the job templates from Section 3.2 of this doc and replace each `uses: ./.github/workflows/release-*.yml` invocation.

4. **Add tests**
   ```bash
   python -m pytest tests/workflow_scripts/test_release_workflow.py -vv
   python -m pytest tests/workflow_scripts -vv
   ```

5. **Mark old workflows deprecated**
   ```yaml
   # ⚠️ DEPRECATED - use reusable-release.yml instead.
   ```

## E.3 Phase 3 – Helper Stubs

1. **Create `.github/workflows/scripts/maintenance_workflow.py`**
   ```python
   {{MAINTENANCE_HELPER_STUB}}
   ```
2. **Add tests**
   ```bash
   python -m pytest tests/workflow_scripts/test_maintenance_workflow.py -vv
   ```

## E.4 Phase 4 – Automation Helper

1. **Create `.github/workflows/scripts/automation_workflow.py`** (skeleton)
   ```python
   {{AUTOMATION_HELPER_STUB}}
   ```
2. **Add `tests/workflow_scripts/test_automation_workflow.py`** with fixtures verifying label rules and auto-merge toggles.

---

# Appendix F – Canonical Code Blocks

> Keep these snippets aligned with `main`. When they diverge, update both the source files and this appendix.

## F.1 `ci_workflow.py`

```python
{{CI_WORKFLOW_CANONICAL}}
```

## F.2 `release_workflow.py`

```python
{{RELEASE_WORKFLOW_CANONICAL}}
```

## F.3 Helper Stubs

### Maintenance Helper Stub

```python
{{MAINTENANCE_HELPER_STUB}}
```

### Documentation Helper Stub

```python
{{DOCS_HELPER_STUB}}
```

### Automation Helper Stub

```python
{{AUTOMATION_HELPER_STUB}}
```

---

# Appendix G – Sample `.github/repository-config.yml`

```yaml
{{REPOSITORY_CONFIG_SAMPLE}}
```

---

# Appendix H – Verification Matrix

| Step | Command | Expected Result |
| --- | --- | --- |
| Phase 1 unit tests | `python -m pytest tests/workflow_scripts/test_ci_workflow.py -vv` | `11 passed` |
| Phase 1 integration | `python -m pytest tests/workflow_scripts -vv` | `23 passed` |
| Phase 2 unit tests | `python -m pytest tests/workflow_scripts/test_release_workflow.py -vv` | `4 passed` |
| YAML validation | `python -m yamlcheck .github/workflows/reusable-release.yml` | `OK` |
| Optional smoke test | `act workflow_dispatch -W .github/workflows/release.yml -j release` | Workflow completes |
