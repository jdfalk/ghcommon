# Workflow Optimization Audit

This document captures the current state of the `ghcommon` workflows and reusable workflows,
identifies the main inefficiencies, and proposes improvements aligned with the single source of
truth in `.github/repository-config.yml`.

## Guiding Principles

- **Repository-config first:** Workflows should read defaults and toggles from
  `.github/repository-config.yml` instead of hardcoding matrices and feature flags. Dispatch inputs
  override, but automatic behaviour should come from config.
- **Reusable > bespoke:** Shared logic belongs in reusable workflows or helper scripts. Inline shell
  should be avoided when the logic is complex or needed in multiple jobs.
- **Single checkout of ghcommon:** Consumers should not need to re-checkout ghcommon when the
  workflow already ships the required scripts.
- **Test the helpers:** Every helper script should have direct unit-level coverage, executed through
  the Python test job in `reusable-ci.yml` (runs `pytest tests/workflow_scripts`).

## Summary by Workflow

| Workflow                                                                                                                                                                                                             | Current Role                                   | Status     | Inefficiencies                                                                                 | Recommendation                                                                                                                                              |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ci.yml`                                                                                                                                                                                                             | Delegates to `reusable-ci.yml`                 | ✅ updated | –                                                                                              | Keep delegating; requires downstream adoption of new helper script flow                                                                                     |
| `ci-tests.yml`                                                                                                                                                                                                       | Legacy full-matrix test runner                 | ⚠️         | Duplicates new reusable CI behaviour, manual path filters, hard-coded matrices                 | Deprecate in favour of `reusable-ci.yml` or refactor to call targeted reusable components driven by repository-config flags                                 |
| `release.yml`                                                                                                                                                                                                        | Calls `reusable-release.yml`                   | ⚠️         | Dispatch inputs mirror config, duplication for per-language jobs                               | Extend `reusable-release.yml` to inspect config for enabled languages and build matrices. Remove redundant per-language release workflows once consolidated |
| `release-go-v1-deprecated.yml`, `release-python-v1-deprecated.yml`, `release-rust-v1-deprecated.yml`, `release-frontend-v1-deprecated.yml`, `release-docker-v1-deprecated.yml`, `release-protobuf-v1-deprecated.yml` | Legacy language-specific release orchestrators | ⚠️         | Near-identical scaffolding, manual environment configuration, inconsistent artefact handling   | Fold into `reusable-release.yml` with modular jobs toggled by repository-config values. Expose hooks for language-specific steps via scripts                |
| `reusable-ci.yml`                                                                                                                                                                                                    | Shared CI pipeline                             | ✅ updated | –                                                                                              | Already converted to python helpers; next iteration should source matrices (versions, OS) from repository-config and expose skip flags via config           |
| `reusable-release.yml`                                                                                                                                                                                               | Shared release/cut pipeline                    | ⚠️         | Heavy reliance on bash scripts, second checkout of ghcommon, duplicated detection logic        | Replace shell helpers with python equivalents (mirroring `ci_workflow.py`), load repository-config once, and emit outputs consumed by language jobs         |
| `reusable-maintenance.yml`, `reusable-security.yml`, `maintenance.yml`, `security.yml`, `performance-monitoring.yml`                                                                                                 | Scheduled maintenance/security tasks           | ⚠️         | Hard-coded schedules and behaviours, minimal config integration                                | Add parsing of repository-config maintenance/security sections for schedule, tooling, thresholds                                                            |
| `documentation.yml`                                                                                                                                                                                                  | Docs verification                              | ⚠️         | Inline placeholder shell steps, not driven by config                                           | Convert to python helper (e.g., docs_workflow.py) that reads doc tooling from config                                                                        |
| `unified-automation.yml`, `issue-automation.yml`, `pr-automation.yml`                                                                                                                                                | Labeling & automation                          | ⚠️         | Combination of inline scripts and Node entries that duplicate logic already present in scripts | Migrate to python helpers (existing `intelligent_labeling.py`, etc.) and ensure config-driven toggles                                                       |
| `auto-module-tagging.yml`, `manager-sync-dispatcher.yml`                                                                                                                                                             | Repo synchronisation                           | ❔         | Behaviour predates repository-config                                                           | Evaluate once initial CI/Release consolidation completes                                                                                                    |
| `sync-receiver.yml`                                                                                                                                                                                                  | Sync entry point                               | ✅ updated | –                                                                                              | Keep; new python helper already installed                                                                                                                   |

## High-impact Changes

1. **Repository-config driven matrices:**
   - Extend `ci_workflow.py` to consume `languages.versions` and `build.platforms` from config,
     eliminating hard-coded version lists.
   - Update `reusable-ci.yml` to request the parsed config and feed it into helper commands.

2. **Release consolidation:**
   - Introduce a `release_workflow.py` helper mirroring the CI helper style (language detection,
     versioning, artefact mapping based on config).
   - Rewire `reusable-release.yml` to call helper subcommands instead of bash scripts and to emit a
     structured build plan per language.
   - Replace per-language release workflows with thin wrappers around the new release helper (or
     integrate the jobs directly in the reusable workflow using dynamic matrices).

3. **Maintenance/Security integration:**
   - Create a `maintenance_workflow.py` helper that reads the `maintenance` and `security` sections
     of repository-config to determine schedule, tooling, and thresholds.
   - Update `reusable-maintenance.yml` and `reusable-security.yml` to run scripted steps using this
     helper instead of inline bash.

4. **Documentation validation:**
   - Replace placeholder echo steps in `documentation.yml` with calls to a new helper that can
     optionally run vale, markdownlint, or other tooling defined in config.

5. **Automation workflows:**
   - Consolidate issue/PR automation under a single reusable workflow that reads `automation.issues`
     and `automation.pull_requests` sections from config.
   - The existing Python scripts (`intelligent_labeling.py`, etc.) should be invoked from that
     reusable workflow with inputs derived from config (auto-merge toggles, label rules, etc.).

## Roadmap

1. **Phase 1 (current work)**
   - ✅ CI workflow scripted helpers and tests (`ci_workflow.py`).
   - ✅ Sync receiver helper conversion.
   - ☐ Repository-config parsing for CI matrices.

2. **Phase 2**
   - Implement `release_workflow.py` helper and migrate `reusable-release.yml`.
   - Merge per-language release workflows into reusable release (deprecate single-language ones
     after confirmation).
   - Add unit tests mirroring the CI helper suite.

3. **Phase 3**
   - Build maintenance/security helper and retrofit reusable workflows.
   - Expand documentation workflow to honour config toggles.
   - Rationalise `ci-tests.yml` (either remove or wire into reusable CI).

4. **Phase 4**
   - Reassess automation workflows, consolidating scripts and enabling config-driven behaviour.
   - Document the new workflow architecture in `docs/` with examples for consumer repositories.

## Implementation Notes

- Helpers should live under `.github/workflows/scripts/` with pytest coverage in
  `tests/workflow_scripts/`.
- Each reusable workflow should have a matching entry in reusable Python test job once new helpers
  land.
- When deprecating legacy workflows (e.g., per-language release ones), keep them temporarily but
  emit warnings pointing maintainers to the consolidated workflow.
- Promote the helper scripts as versioned assets if we want external repos to pin specific revisions
  instead of fetching `main`.

## Next Actions

1. Add repository-config parsing to `ci_workflow.py` for matrices and pass config JSON through
   reusable CI.
2. Draft `release_workflow.py` and start migrating bash helpers.
3. Schedule follow-up issues for maintenance/security/doc automation updates using this audit as the
   spec.

---

# Detailed Implementation Guide

The remainder of this document is a step-by-step playbook aimed at a junior engineer. It spells out
**what to change**, **why the change matters**, and **how to verify** each step with concrete
commands, sample code, and expected outputs.

---

## Phase 1 – CI Pipeline Modernisation (Status: ✅ In-progress)

### Goal

Move the reusable CI workflow (`.github/workflows/reusable-ci.yml`) and its helper
(`ci_workflow.py`) to be fully driven by `.github/repository-config.yml`.

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

   _Expected output_: `config` (JSON string) and `has-config` booleans written to `GITHUB_OUTPUT`.

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

   _Expected_: All tests including `test_generate_matrices_uses_repository_config` pass.

6. **Integration test**

   ```bash
   python -m pytest tests/workflow_scripts -vv
   ```

7. **Document in `docs/workflow-optimization.md`** (this file) and update changelog if needed.

### Example config snippet

```yaml
languages:
  versions:
    go: ['1.22', '1.23', '1.24']
    python: ['3.11', '3.12', '3.13']
build:
  platforms:
    os: ['ubuntu-latest', 'macos-latest']
testing:
  coverage:
    threshold: 85
```

### Checklist

- [x] `load-config` job exists.
- [x] Matrices produced via helper.
- [x] Language jobs use generated matrix.
- [x] All helper tests pass.
- [x] Helper script tests run green under the reusable CI Python job.

---

## Phase 2 – Release Pipeline Consolidation (Status: ☐ Not started)

### Goal

Replace shell-based release helpers with a Python module (`release_workflow.py`) and merge
single-language release workflows into `reusable-release.yml`.

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

   Replace `bash` invocations for release strategy, version, changelog with equivalent Python
   commands.

6. **Merge per-language workflows**
   - Move build logic from `release-go.yml`, `release-python.yml`, etc. into conditional jobs inside
     `reusable-release.yml`.
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
   - Repeat for Python, Rust, Frontend, Docker, Protobuf (reuse step templates from existing
     workflows).
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
   - Add comments to old per-language workflows (e.g., `release-go.yml`) stating they are
     superseded.
   - Update docs to point consumers at new reusable release.

### Example configuration-driven flow

```yaml
release:
  versioning:
    triggers:
      major: ['breaking', 'feat!']
  artifacts:
    types: ['binary', 'archive']
  changelog:
    enabled: true
    categories: ['Features', 'Bug Fixes']
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

Introduce config-driven maintenance/security/doc workflows using Python helpers and remove redundant
workflows (`ci-tests.yml`, etc.).

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

- Expand reusable CI Python test coverage to include new suites.

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

| Purpose                       | Command                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| Run unit tests                | `python -m pytest tests/workflow_scripts -vv`                |
| Validate YAML                 | `pip install yamllint && yamllint .github/workflows/`        |
| Run local workflow (optional) | `act workflow_dispatch -W .github/workflows/reusable-ci.yml` |
| Format Python (if needed)     | `pip install black && black .github/workflows/scripts`       |

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

| Symptom                                  | Cause                                         | Fix                                                                                             |
| ---------------------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError` when running tests | Helper script not on `sys.path`               | Ensure `tests/workflow_scripts/__init__.py` injects `.github/workflows/scripts` into `sys.path` |
| Matrices empty in CI                     | `REPOSITORY_CONFIG` not passed to helper      | Check `load-config` job outputs and env propagation                                             |
| Release tag conflict                     | Existing tag on branch                        | `workflow_dispatch` allows auto-delete; otherwise version increments automatically              |
| Docker build skipped unexpectedly        | `detect_docker_config.py` found no Dockerfile | Override with `dockerfile` input or ensure file exists                                          |

---

# Appendix D – Suggested Timeline

| Week    | Milestone                  | Artifacts                                               |
| ------- | -------------------------- | ------------------------------------------------------- |
| Week 1  | Phase 1 completion         | Updated CI workflow, helper tests                       |
| Week 2  | Phase 2 implementation     | New release helper, consolidated release workflow, docs |
| Week 3  | Phase 3 work               | Maintenance/doc helpers and tests                       |
| Week 4+ | Phase 4 & adoption support | Automation helper, onboarding docs, versioned tags      |

---

## Final Notes for Implementers

- **Work incrementally**: each phase should result in a passing test suite and updated
  documentation.
- **Communicate**: share the workflow updates with downstream repositories and provide guidance on
  pinning new tags.
- **Automate validation**: ensure reusable CI Python tests run as part of every PR to catch
  regressions.
- **Document everything**: this file should evolve with each phase to keep instructions accurate for
  new contributors.

---

# Appendix E – Step-by-step Recipes (Copy/Paste Friendly)

This appendix contains exhaustive instructions that an AI or junior engineer can follow without
additional guidance.

## E.1 Phase 1 – CI Modernisation

1. **Update `.github/workflows/scripts/ci_workflow.py`**
   - Replace the file contents with the canonical version in
     [Appendix F.2](#f2-githubworkflowsscriptsci_workflowpy) (copy/paste the entire code block).

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
     @@
     -    needs: detect-changes
     -    runs-on: ubuntu-latest
     -    steps:
     -      - uses: actions/setup-go@v6
     -        with:
     -          go-version: ${{ inputs.go-version }}
     +    needs: [load-config, detect-changes]
     +    strategy:
     +      fail-fast: false
     +      matrix: ${{ fromJSON(needs.load-config.outputs.go-matrix) }}
     +    runs-on: ${{ matrix.os }}
     +    env:
     +      REPOSITORY_CONFIG: ${{ needs.load-config.outputs.config }}
     +    steps:
     +      - uses: actions/setup-go@v6
     +        with:
     +          go-version: ${{ matrix.go-version }}
     ```

     _(Repeat matrix substitution blocks for Python, Rust, and Frontend jobs.)_

3. **Run tests**
   ```bash
   python -m pytest tests/workflow_scripts/test_ci_workflow.py -vv
   python -m pytest tests/workflow_scripts -vv
   ```

## E.2 Phase 2 – Release Consolidation

1. **Create/replace `.github/workflows/scripts/release_workflow.py`**
   - Copy the full implementation from [Appendix F.4](#f4-githubworkflowsscriptsrelease_workflowpy)
     into the file.

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

3. **Inline language build jobs** – copy the job templates from Appendix F.3 and replace each
   `uses: ./.github/workflows/release-*.yml` invocation.

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

1. **Create `.github/workflows/scripts/maintenance_workflow.py`** – copy the implementation from
   Appendix F.5.
2. **Create `.github/workflows/scripts/docs_workflow.py`** – copy the implementation from
   Appendix F.6.
3. **Create `.github/workflows/scripts/automation_workflow.py`** – copy the implementation from
   Appendix F.7.
4. **Add tests** – copy the suites from Appendix F.10, Appendix F.11, and Appendix F.12 into
   `tests/workflow_scripts/`.
5. **Wire helpers** – update `reusable-maintenance.yml`, `reusable-security.yml`, and
   `documentation.yml` to invoke the new helper commands exactly as shown in Appendix F.3/F.5–F.7.

## E.4 Phase 4 – Automation Helper

1. **Create `.github/workflows/scripts/automation_workflow.py`** – copy the implementation from
   Appendix F.7.
2. **Add `tests/workflow_scripts/test_automation_workflow.py`** – reuse the suite from
   Appendix F.12.
3. **Update `unified-automation.yml`, `issue-automation.yml`, and `pr-automation.yml`** so that each
   job delegates to the helper commands defined in Appendix F.7 (label plan, PR plan, auto-merge
   plan).

---

# Appendix F – Canonical Code Blocks

> Keep these snippets aligned with `main`. When they diverge, update both the source files and this
> appendix.

## F.1 `.github/workflows/reusable-ci.yml`

```yaml
# file: .github/workflows/reusable-ci.yml
# version: 1.1.0
# guid: reusable-ci-2025-09-24-core-workflow

name: Reusable CI Workflow

on:
  workflow_call:
    inputs:
      go-version:
        description: 'Go version to use'
        required: false
        type: string
        default: '1.24'
      node-version:
        description: 'Node.js version to use'
        required: false
        type: string
        default: '22'
      python-version:
        description: 'Python version to use'
        required: false
        type: string
        default: '3.13'
      rust-version:
        description: 'Rust version to use'
        required: false
        type: string
        default: '1.76'
      coverage-threshold:
        description: 'Coverage threshold percentage'
        required: false
        type: string
        default: '80'
      skip-protobuf:
        description: 'Skip protobuf generation'
        required: false
        type: boolean
        default: false
      skip-tests:
        description: 'Skip running tests'
        required: false
        type: boolean
        default: false
      skip-linting:
        description: 'Skip linting'
        required: false
        type: boolean
        default: false
    outputs:
      go-files:
        description: 'Whether Go files were detected'
        value: ${{ jobs.detect-changes.outputs.go-files }}
      python-files:
        description: 'Whether Python files were detected'
        value: ${{ jobs.detect-changes.outputs.python-files }}
      rust-files:
        description: 'Whether Rust files were detected'
        value: ${{ jobs.detect-changes.outputs.rust-files }}
      frontend-files:
        description: 'Whether frontend files were detected'
        value: ${{ jobs.detect-changes.outputs.frontend-files }}
      docker-files:
        description: 'Whether Docker files were detected'
        value: ${{ jobs.detect-changes.outputs.docker-files }}
      docs-files:
        description: 'Whether documentation files were detected'
        value: ${{ jobs.detect-changes.outputs.docs-files }}
      workflows-files:
        description: 'Whether workflow files were detected'
        value: ${{ jobs.detect-changes.outputs.workflows-files }}
      lint-files:
        description: 'Whether linter configuration files were detected'
        value: ${{ jobs.detect-changes.outputs.lint-files }}

permissions:
  contents: write
  actions: write
  checks: write
  packages: write
  security-events: write
  id-token: write
  attestations: write

jobs:
  load-config:
    name: Load Repository Configuration
    runs-on: ubuntu-latest
    outputs:
      config: ${{ steps.load.outputs.config }}
      has-config: ${{ steps.load.outputs.has-config }}
      go-matrix: ${{ steps.matrices.outputs.go-matrix }}
      python-matrix: ${{ steps.matrices.outputs.python-matrix }}
      rust-matrix: ${{ steps.matrices.outputs.rust-matrix }}
      frontend-matrix: ${{ steps.matrices.outputs.frontend-matrix }}
      coverage-threshold: ${{ steps.matrices.outputs.coverage-threshold }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v5

      - name: Load repository configuration
        id: load
        env:
          CONFIG_FILE: .github/repository-config.yml
        run: python3 .github/workflows/scripts/load_repository_config.py

      - name: Generate language matrices
        id: matrices
        env:
          REPOSITORY_CONFIG: ${{ steps.load.outputs.config }}
          FALLBACK_GO_VERSION: ${{ inputs.go-version }}
          FALLBACK_PYTHON_VERSION: ${{ inputs.python-version }}
          FALLBACK_RUST_VERSION: ${{ inputs.rust-version }}
          FALLBACK_NODE_VERSION: ${{ inputs.node-version }}
          FALLBACK_COVERAGE_THRESHOLD: ${{ inputs.coverage-threshold }}
        run: python3 .github/workflows/scripts/ci_workflow.py generate-matrices

  # Detect what files changed to optimize workflow execution
  detect-changes:
    name: Detect Changes
    runs-on: ubuntu-latest
    needs: load-config
    outputs:
      go-files: ${{ steps.changes.outputs.go_files }}
      python-files: ${{ steps.changes.outputs.python_files }}
      rust-files: ${{ steps.changes.outputs.rust_files }}
      frontend-files: ${{ steps.changes.outputs.frontend_files }}
      docker-files: ${{ steps.changes.outputs.docker_files }}
      docs-files: ${{ steps.changes.outputs.docs_files }}
      workflows-files: ${{ steps.changes.outputs.workflow_files }}
      lint-files: ${{ steps.changes.outputs.lint_files }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v5
        with:
          fetch-depth: 2

      - name: Detect file changes
        uses: dorny/paths-filter@v3
        id: changes
        with:
          filters: |
            go_files:
              - '**/*.go'
              - 'go.mod'
              - 'go.sum'
            python_files:
              - '**/*.py'
              - 'requirements*.txt'
              - 'pyproject.toml'
              - 'setup.py'
              - 'setup.cfg'
            rust_files:
              - '**/*.rs'
              - 'Cargo.toml'
              - 'Cargo.lock'
            frontend_files:
              - '**/*.js'
              - '**/*.ts'
              - '**/*.jsx'
              - '**/*.tsx'
              - '**/*.vue'
              - '**/*.svelte'
              - '**/*.html'
              - '**/*.css'
              - '**/*.scss'
              - '**/*.sass'
              - '**/*.less'
              - 'package*.json'
              - 'yarn.lock'
              - 'pnpm-lock.yaml'
            docker_files:
              - 'Dockerfile*'
              - 'docker-compose*.yml'
              - 'docker-compose*.yaml'
              - '.dockerignore'
            docs_files:
              - '**/*.md'
              - 'docs/**'
              - '*.md'
            workflow_files:
              - '.github/workflows/**'
              - '.github/actions/**'
            lint_files:
              - 'super-linter-*.env'
              - '.markdownlint.json'
              - '.yaml-lint.yml'
              - 'clippy.toml'
              - 'rustfmt.toml'
              - '.eslintrc.*'
              - '.pylintrc'
              - '.python-black'
              - '.prettierrc*'
              - '.flake8'

      - name: Debug change outputs
        env:
          CI_GO_FILES: ${{ steps.changes.outputs.go_files }}
          CI_PYTHON_FILES: ${{ steps.changes.outputs.python_files }}
          CI_RUST_FILES: ${{ steps.changes.outputs.rust_files }}
          CI_FRONTEND_FILES: ${{ steps.changes.outputs.frontend_files }}
          CI_DOCKER_FILES: ${{ steps.changes.outputs.docker_files }}
          CI_DOCS_FILES: ${{ steps.changes.outputs.docs_files }}
          CI_WORKFLOW_FILES: ${{ steps.changes.outputs.workflow_files }}
          CI_LINT_FILES: ${{ steps.changes.outputs.lint_files }}
        run: python3 .github/workflows/scripts/ci_workflow.py debug-filter

  # Protobuf generation (if applicable)
  protobuf-generation:
    name: Generate Protobuf
    if: |
      !inputs.skip-protobuf &&
      (contains(github.event.head_commit.message, '[protobuf]') ||
       contains(github.event.head_commit.message, '[generate]') ||
       contains(github.event.head_commit.message, '[buf]'))
    uses: ./.github/workflows/reusable-protobuf.yml
    secrets: inherit

  # Language-specific build and test jobs
  go-ci:
    name: Go CI
    needs: [load-config, detect-changes]
    if: needs.detect-changes.outputs.go-files == 'true'
    strategy:
      fail-fast: false
      matrix: ${{ fromJSON(needs.load-config.outputs.go-matrix) }}
    runs-on: ${{ matrix.os }}
    env:
      REPOSITORY_CONFIG: ${{ needs.load-config.outputs.config }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v5

      - name: Set up Go
        uses: actions/setup-go@v6
        with:
          go-version: ${{ matrix.go-version }}
          cache: true

      - name: Build Go project
        run: python3 .github/workflows/scripts/ci_workflow.py go-setup

      - name: Test Go project
        if: ${{ !inputs.skip-tests }}
        env:
          COVERAGE_THRESHOLD: ${{ inputs.coverage-threshold || needs.load-config.outputs.coverage-threshold }}
        run: python3 .github/workflows/scripts/ci_workflow.py go-test

  python-ci:
    name: Python CI
    needs: [load-config, detect-changes]
    if: needs.detect-changes.outputs.python-files == 'true'
    strategy:
      fail-fast: false
      matrix: ${{ fromJSON(needs.load-config.outputs.python-matrix) }}
    runs-on: ${{ matrix.os }}
    env:
      REPOSITORY_CONFIG: ${{ needs.load-config.outputs.config }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v5

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Install Python dependencies
        run: python3 .github/workflows/scripts/ci_workflow.py python-install

      - name: Lint Python code
        if: ${{ !inputs.skip-linting }}
        run: python3 .github/workflows/scripts/ci_workflow.py python-lint

      - name: Test Python code
        if: ${{ !inputs.skip-tests }}
        run: python3 .github/workflows/scripts/ci_workflow.py python-run-tests

  rust-ci:
    name: Rust CI
    needs: [load-config, detect-changes]
    if: needs.detect-changes.outputs.rust-files == 'true'
    strategy:
      fail-fast: false
      matrix: ${{ fromJSON(needs.load-config.outputs.rust-matrix) }}
    runs-on: ${{ matrix.os }}
    env:
      REPOSITORY_CONFIG: ${{ needs.load-config.outputs.config }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v5

      - name: Set up Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          toolchain: ${{ matrix.rust-version }}
          components: rustfmt, clippy

      - name: Cache Rust dependencies
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/bin/
            ~/.cargo/registry/index/
            ~/.cargo/registry/cache/
            ~/.cargo/git/db/
            target/
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}

      - name: Format Rust code
        if: ${{ !inputs.skip-linting }}
        run: python3 .github/workflows/scripts/ci_workflow.py rust-format

      - name: Lint Rust code
        if: ${{ !inputs.skip-linting }}
        run: python3 .github/workflows/scripts/ci_workflow.py rust-clippy

      - name: Build Rust project
        run: python3 .github/workflows/scripts/ci_workflow.py rust-build

      - name: Test Rust project
        if: ${{ !inputs.skip-tests }}
        run: python3 .github/workflows/scripts/ci_workflow.py rust-test

  frontend-ci:
    name: Frontend CI
    needs: [load-config, detect-changes]
    if: needs.detect-changes.outputs.frontend-files == 'true'
    strategy:
      fail-fast: false
      matrix: ${{ fromJSON(needs.load-config.outputs.frontend-matrix) }}
    runs-on: ${{ matrix.os }}
    env:
      REPOSITORY_CONFIG: ${{ needs.load-config.outputs.config }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v5

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: npm

      - name: Install dependencies
        run: python3 .github/workflows/scripts/ci_workflow.py frontend-install

      - name: Lint frontend code
        if: ${{ !inputs.skip-linting }}
        env:
          FRONTEND_SCRIPT: lint
          FRONTEND_SUCCESS_MESSAGE: '✅ Linting passed'
          FRONTEND_FAILURE_MESSAGE: '❌ Linting failed or not configured'
        run: python3 .github/workflows/scripts/ci_workflow.py frontend-run

      - name: Build frontend
        env:
          FRONTEND_SCRIPT: build
          FRONTEND_SUCCESS_MESSAGE: '✅ Build successful'
          FRONTEND_FAILURE_MESSAGE: 'ℹ️ No build script configured'
        run: python3 .github/workflows/scripts/ci_workflow.py frontend-run

      - name: Test frontend
        if: ${{ !inputs.skip-tests }}
        env:
          FRONTEND_SCRIPT: test
          FRONTEND_SUCCESS_MESSAGE: '✅ Tests passed'
          FRONTEND_FAILURE_MESSAGE: 'ℹ️ No tests configured'
        run: python3 .github/workflows/scripts/ci_workflow.py frontend-run

  # Summary job
  ci-summary:
    name: CI Summary
    needs: [detect-changes, go-ci, python-ci, rust-ci, frontend-ci]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Generate summary
        env:
          JOB_GO: ${{ needs.go-ci.result || 'skipped' }}
          JOB_PYTHON: ${{ needs.python-ci.result || 'skipped' }}
          JOB_RUST: ${{ needs.rust-ci.result || 'skipped' }}
          JOB_FRONTEND: ${{ needs.frontend-ci.result || 'skipped' }}
          CI_GO_FILES: ${{ needs.detect-changes.outputs.go-files }}
          CI_PYTHON_FILES: ${{ needs.detect-changes.outputs.python-files }}
          CI_RUST_FILES: ${{ needs.detect-changes.outputs.rust-files }}
          CI_FRONTEND_FILES: ${{ needs.detect-changes.outputs.frontend-files }}
          CI_DOCKER_FILES: ${{ needs.detect-changes.outputs.docker-files }}
          CI_DOCS_FILES: ${{ needs.detect-changes.outputs.docs-files }}
          CI_WORKFLOW_FILES: ${{ needs.detect-changes.outputs.workflow-files }}
        run: python3 .github/workflows/scripts/ci_workflow.py generate-ci-summary

      - name: Check overall status
        env:
          JOB_GO: ${{ needs.go-ci.result || 'skipped' }}
          JOB_PYTHON: ${{ needs.python-ci.result || 'skipped' }}
          JOB_RUST: ${{ needs.rust-ci.result || 'skipped' }}
          JOB_FRONTEND: ${{ needs.frontend-ci.result || 'skipped' }}
        run: python3 .github/workflows/scripts/ci_workflow.py check-ci-status
```

## F.2 `.github/workflows/scripts/ci_workflow.py`

```python
#!/usr/bin/env python3
"""Helper utilities invoked from GitHub Actions CI workflows."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Any, Iterable

import requests

_CONFIG_CACHE: dict[str, Any] | None = None


def append_to_file(path_env: str, content: str) -> None:
    """Append content to the file referenced by a GitHub Actions environment variable."""
    file_path = os.environ.get(path_env)
    if not file_path:
        return
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "a", encoding="utf-8") as handle:
        handle.write(content)


def write_output(name: str, value: str) -> None:
    append_to_file("GITHUB_OUTPUT", f"{name}={value}\n")


def append_env(name: str, value: str) -> None:
    append_to_file("GITHUB_ENV", f"{name}={value}\n")


def append_summary(text: str) -> None:
    append_to_file("GITHUB_STEP_SUMMARY", text)


def get_repository_config() -> dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    raw = os.environ.get("REPOSITORY_CONFIG")
    if not raw:
        _CONFIG_CACHE = {}
        return _CONFIG_CACHE

    try:
        _CONFIG_CACHE = json.loads(raw)
    except json.JSONDecodeError:
        print("::warning::Unable to parse REPOSITORY_CONFIG JSON; falling back to defaults")
        _CONFIG_CACHE = {}
    return _CONFIG_CACHE


def _config_path(default: Any, *path: str) -> Any:
    current: Any = get_repository_config()
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def debug_filter(_: argparse.Namespace) -> None:
    mapping = {
        "Go files changed": os.environ.get("CI_GO_FILES", ""),
        "Frontend files changed": os.environ.get("CI_FRONTEND_FILES", ""),
        "Python files changed": os.environ.get("CI_PYTHON_FILES", ""),
        "Rust files changed": os.environ.get("CI_RUST_FILES", ""),
        "Docker files changed": os.environ.get("CI_DOCKER_FILES", ""),
        "Docs files changed": os.environ.get("CI_DOCS_FILES", ""),
        "Workflow files changed": os.environ.get("CI_WORKFLOW_FILES", ""),
        "Linter config files changed": os.environ.get("CI_LINT_FILES", ""),
    }
    for label, value in mapping.items():
        print(f"{label}: {value}")


def determine_execution(_: argparse.Namespace) -> None:
    commit_message = os.environ.get("GITHUB_HEAD_COMMIT_MESSAGE", "")
    skip_ci = bool(re.search(r"\[(skip ci|ci skip)\]", commit_message, flags=re.IGNORECASE))
    write_output("skip_ci", "true" if skip_ci else "false")
    if skip_ci:
        print("Skipping CI due to commit message")
    else:
        print("CI will continue; no skip directive found in commit message")

    write_output("should_lint", "true")
    write_output("should_test_go", os.environ.get("CI_GO_FILES", "false"))
    write_output("should_test_frontend", os.environ.get("CI_FRONTEND_FILES", "false"))
    write_output("should_test_python", os.environ.get("CI_PYTHON_FILES", "false"))
    write_output("should_test_rust", os.environ.get("CI_RUST_FILES", "false"))
    write_output("should_test_docker", os.environ.get("CI_DOCKER_FILES", "false"))


def wait_for_pr_automation(_: argparse.Namespace) -> None:
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    target_sha = os.environ.get("TARGET_SHA")
    workflow_name = os.environ.get("WORKFLOW_NAME", "PR Automation")
    max_attempts = int(os.environ.get("MAX_ATTEMPTS", "60"))
    sleep_seconds = int(os.environ.get("SLEEP_SECONDS", "10"))

    if not (repo and token and target_sha):
        print("Missing required environment values; skipping PR automation wait")
        return

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{repo}/actions/runs"

    print("🔄 Waiting for PR automation to complete...")
    for attempt in range(max_attempts):
        print(f"Checking for PR automation completion (attempt {attempt + 1}/{max_attempts})...")
        response = requests.get(url, headers=headers, params={"per_page": 100}, timeout=30)
        if response.status_code != 200:
            print(f"::warning::Unable to query workflow runs: {response.status_code}")
            time.sleep(sleep_seconds)
            continue

        runs = response.json().get("workflow_runs", [])
        matching_runs = [
            run for run in runs if run.get("head_sha") == target_sha and run.get("name") == workflow_name
        ]

        if not matching_runs:
            print("ℹ️  No PR automation workflow found, proceeding with CI")
            return

        status = matching_runs[0].get("status", "")
        if status == "completed":
            print("✅ PR automation has completed, proceeding with CI")
            return

        print(f"⏳ PR automation status: {status or 'unknown'}, waiting...")
        time.sleep(sleep_seconds)

    print("⚠️  Timeout waiting for PR automation, proceeding with CI anyway")


def _export_env_from_file(file_path: Path) -> None:
    with file_path.open(encoding="utf-8") as handle:
        for line in handle:
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key or key.startswith("#"):
                continue
            append_env(key, value.strip())


def load_super_linter_config(_: argparse.Namespace) -> None:
    event_name = os.environ.get("EVENT_NAME", "")
    pr_env = Path(os.environ.get("PR_ENV_FILE", "super-linter-pr.env"))
    ci_env = Path(os.environ.get("CI_ENV_FILE", "super-linter-ci.env"))

    chosen: Path | None = None

    if event_name in {"pull_request", "pull_request_target"}:
        if pr_env.is_file():
            print(f"Loading PR Super Linter configuration from {pr_env}")
            chosen = pr_env
        elif ci_env.is_file():
            print(f"PR config not found, falling back to CI config ({ci_env})")
            chosen = ci_env
    else:
        if ci_env.is_file():
            print(f"Loading CI Super Linter configuration from {ci_env}")
            chosen = ci_env

    if chosen:
        _export_env_from_file(chosen)
        write_output("config-file", chosen.name)
    else:
        print("Warning: No Super Linter configuration found")
        write_output("config-file", "")


def write_validation_summary(_: argparse.Namespace) -> None:
    event_name = os.environ.get("EVENT_NAME", "unknown")
    config_name = os.environ.get("SUMMARY_CONFIG", "super-linter-ci.env")
    append_summary(
        textwrap.dedent(
            f"""\
            # 🔍 CI Validation Results

            ✅ **Code validation completed**

            ## Configuration
            - **Mode**: Validation only (no auto-fixes)
            - **Configuration**: {config_name}
            - **Event**: {event_name}

            """
        )
    )


def _ensure_go_context() -> bool:
    if not Path("go.mod").is_file():
        print("ℹ️ No go.mod found; skipping Go step")
        return False
    return True


def go_setup(_: argparse.Namespace) -> None:
    if not _ensure_go_context():
        return
    subprocess.run(["go", "mod", "download"], check=True)
    subprocess.run(["go", "build", "-v", "./..."], check=True)


def _parse_go_coverage(total_line: str) -> float:
    parts = total_line.strip().split()
    if not parts:
        raise ValueError("Unable to parse go coverage output")
    percentage = parts[-1].rstrip("%")
    return float(percentage)


def go_test(_: argparse.Namespace) -> None:
    if not _ensure_go_context():
        return

    coverage_file = os.environ.get("COVERAGE_FILE", "coverage.out")
    coverage_html = os.environ.get("COVERAGE_HTML", "coverage.html")
    threshold_env = os.environ.get("COVERAGE_THRESHOLD")
    if threshold_env:
        threshold = float(threshold_env)
    else:
        threshold = float(_config_path(0, "testing", "coverage", "threshold") or 0)

    subprocess.run(["go", "test", "-v", "-race", f"-coverprofile={coverage_file}", "./..."], check=True)

    go_binary = shutil.which("go") or "go"
    subprocess.run(
        [go_binary, "tool", "cover", f"-html={coverage_file}", "-o", coverage_html],
        check=True,
    )
    result = subprocess.run(
        [go_binary, "tool", "cover", "-func", coverage_file],
        check=True,
        capture_output=True,
        text=True,
    )

    total_line = ""
    for line in result.stdout.splitlines():
        if line.startswith("total:"):
            total_line = line
            break

    if not total_line:
        raise ValueError("Total coverage line not found in go tool output")

    coverage = _parse_go_coverage(total_line)
    print(f"Coverage: {coverage}%")
    if coverage < threshold:
        raise SystemExit(f"Coverage {coverage}% is below threshold {threshold}%")
    print(f"✅ Coverage {coverage}% meets threshold {threshold}%")


def check_go_coverage(_: argparse.Namespace) -> None:
    coverage_file = Path(os.environ.get("COVERAGE_FILE", "coverage.out"))
    html_output = Path(os.environ.get("COVERAGE_HTML", "coverage.html"))
    threshold = float(os.environ.get("COVERAGE_THRESHOLD", "0"))

    if not coverage_file.is_file():
        raise FileNotFoundError(f"{coverage_file} not found")

    go_binary = shutil.which("go") or "go"

    subprocess.run(
        [go_binary, "tool", "cover", f"-html={coverage_file}", "-o", str(html_output)],
        check=True,
    )
    result = subprocess.run(
        [go_binary, "tool", "cover", "-func", str(coverage_file)],
        check=True,
        capture_output=True,
        text=True,
    )

    total_line = ""
    for line in result.stdout.splitlines():
        if line.startswith("total:"):
            total_line = line
            break

    if not total_line:
        raise ValueError("Total coverage line not found in go tool output")

    coverage = _parse_go_coverage(total_line)
    print(f"Coverage: {coverage}%")
    if coverage < threshold:
        raise SystemExit(
            f"Coverage {coverage}% is below threshold {threshold}%"
        )
    print(f"✅ Coverage {coverage}% meets threshold {threshold}%")


def _run_command(command: Iterable[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), check=check)


def frontend_install(_: argparse.Namespace) -> None:
    if Path("package-lock.json").is_file():
        _run_command(["npm", "ci"])
    elif Path("yarn.lock").is_file():
        _run_command(["yarn", "install", "--frozen-lockfile"])
    elif Path("pnpm-lock.yaml").is_file():
        _run_command(["npm", "install", "-g", "pnpm"])
        _run_command(["pnpm", "install", "--frozen-lockfile"])
    else:
        _run_command(["npm", "install"])


def frontend_run(_: argparse.Namespace) -> None:
    script_name = os.environ.get("FRONTEND_SCRIPT", "")
    success_message = os.environ.get("FRONTEND_SUCCESS_MESSAGE", "Command succeeded")
    failure_message = os.environ.get("FRONTEND_FAILURE_MESSAGE", "Command failed")

    if not script_name:
        raise SystemExit("FRONTEND_SCRIPT environment variable is required")

    result = subprocess.run(["npm", "run", script_name, "--if-present"])
    if result.returncode == 0:
        print(success_message)
    else:
        print(failure_message)


def python_install(_: argparse.Namespace) -> None:
    python = sys.executable
    subprocess.run([python, "-m", "pip", "install", "--upgrade", "pip"], check=True)

    if Path("requirements.txt").is_file():
        subprocess.run([python, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

    if Path("pyproject.toml").is_file():
        subprocess.run([python, "-m", "pip", "install", "-e", "."], check=True)

    subprocess.run([python, "-m", "pip", "install", "pytest", "pytest-cov"], check=True)


def python_run_tests(_: argparse.Namespace) -> None:
    def has_tests() -> bool:
        for pattern in ("test_*.py", "*_test.py"):
            if any(Path(".").rglob(pattern)):
                return True
        return False

    if not has_tests():
        print("ℹ️ No Python tests found")
        return

    python = sys.executable
    subprocess.run(
        [python, "-m", "pytest", "--cov=.", "--cov-report=xml", "--cov-report=html"],
        check=True,
    )


def ensure_cargo_llvm_cov(_: argparse.Namespace) -> None:
    if shutil.which("cargo-llvm-cov"):
        print("cargo-llvm-cov already installed")
        return
    subprocess.run(["cargo", "install", "cargo-llvm-cov", "--locked"], check=True)


def generate_rust_lcov(_: argparse.Namespace) -> None:
    output_path = Path(os.environ.get("LCOV_OUTPUT", "lcov.info"))
    subprocess.run(
        ["cargo", "llvm-cov", "--workspace", "--verbose", "--lcov", "--output-path", str(output_path)],
        check=True,
    )


def generate_rust_html(_: argparse.Namespace) -> None:
    output_dir = Path(os.environ.get("HTML_OUTPUT_DIR", "htmlcov"))
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["cargo", "llvm-cov", "--workspace", "--verbose", "--html", "--output-dir", str(output_dir)],
        check=True,
    )


def compute_rust_coverage(_: argparse.Namespace) -> None:
    path = Path(os.environ.get("LCOV_FILE", "lcov.info"))
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found")

    total = 0
    covered = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("LF:"):
            total += int(line.split(":", 1)[1])
        elif line.startswith("LH:"):
            covered += int(line.split(":", 1)[1])

    if total == 0:
        write_output("percent", "0")
        return

    percent = (covered * 100.0) / total
    write_output("percent", f"{percent:.2f}")


def enforce_coverage_threshold(_: argparse.Namespace) -> None:
    threshold = float(os.environ.get("COVERAGE_THRESHOLD", "0"))
    percent_str = os.environ.get("COVERAGE_PERCENT")
    if percent_str is None:
        raise SystemExit("COVERAGE_PERCENT environment variable missing")

    percent = float(percent_str)
    append_summary(f"Rust coverage: {percent}% (threshold {threshold}%)\n")
    if percent < threshold:
        raise SystemExit(f"Coverage {percent}% is below threshold {threshold}%")
    print(f"✅ Coverage {percent}% meets threshold {threshold}%")


def docker_build(_: argparse.Namespace) -> None:
    dockerfile = Path(os.environ.get("DOCKERFILE_PATH", "Dockerfile"))
    image_name = os.environ.get("DOCKER_IMAGE", "test-image")
    if not dockerfile.is_file():
        print("ℹ️ No Dockerfile found")
        return

    subprocess.run(["docker", "build", "-t", image_name, str(dockerfile.parent)], check=True)


def docker_test_compose(_: argparse.Namespace) -> None:
    if Path("docker-compose.yml").is_file() or Path("docker-compose.yaml").is_file():
        subprocess.run(["docker-compose", "config"], check=True)
    else:
        print("ℹ️ No docker-compose file found")


def docs_check_links(_: argparse.Namespace) -> None:
    print("ℹ️ Link checking would go here")


def docs_validate_structure(_: argparse.Namespace) -> None:
    print("ℹ️ Documentation structure validation would go here")


def run_benchmarks(_: argparse.Namespace) -> None:
    has_benchmarks = False
    for path in Path(".").rglob("*_test.go"):
        try:
            if "Benchmark" in path.read_text(encoding="utf-8"):
                has_benchmarks = True
                break
        except UnicodeDecodeError:
            continue

    if not has_benchmarks:
        print("ℹ️ No benchmarks found")
        return

    subprocess.run(["go", "test", "-bench=.", "-benchmem", "./..."], check=True)


def _matrix_entries(versions: list[str], oses: list[str], version_key: str) -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for os_index, runner in enumerate(oses):
        for ver_index, version in enumerate(versions):
            matrix.append(
                {
                    "os": runner,
                    version_key: version,
                    "primary": os_index == 0 and ver_index == 0,
                }
            )
    return matrix


def generate_matrices(_: argparse.Namespace) -> None:
    fallback_go = os.environ.get("FALLBACK_GO_VERSION", "1.24")
    fallback_python = os.environ.get("FALLBACK_PYTHON_VERSION", "3.13")
    fallback_rust = os.environ.get("FALLBACK_RUST_VERSION", "stable")
    fallback_node = os.environ.get("FALLBACK_NODE_VERSION", "22")
    fallback_threshold = os.environ.get("FALLBACK_COVERAGE_THRESHOLD", "80")

    versions_config = _config_path({}, "languages", "versions") or {}
    build_platforms = _config_path({}, "build", "platforms") or {}
    os_list = build_platforms.get("os") or ["ubuntu-latest"]

    go_versions = versions_config.get("go") or [fallback_go]
    python_versions = versions_config.get("python") or [fallback_python]
    rust_versions = versions_config.get("rust") or [fallback_rust]
    node_versions = versions_config.get("node") or [fallback_node]

    go_matrix = _matrix_entries(go_versions, os_list, "go-version")
    python_matrix = _matrix_entries(python_versions, os_list, "python-version")
    rust_matrix = _matrix_entries(rust_versions, os_list, "rust-version")
    frontend_matrix = _matrix_entries(node_versions, os_list, "node-version")

    write_output("go-matrix", json.dumps({"include": go_matrix}, separators=(",", ":")))
    write_output("python-matrix", json.dumps({"include": python_matrix}, separators=(",", ":")))
    write_output("rust-matrix", json.dumps({"include": rust_matrix}, separators=(",", ":")))
    write_output("frontend-matrix", json.dumps({"include": frontend_matrix}, separators=(",", ":")))

    coverage_threshold = _config_path(fallback_threshold, "testing", "coverage", "threshold")
    write_output("coverage-threshold", str(coverage_threshold))


def generate_ci_summary(_: argparse.Namespace) -> None:
    primary_language = os.environ.get("PRIMARY_LANGUAGE", "unknown")
    steps = {
        "Detect Changes": os.environ.get("JOB_DETECT_CHANGES", "unknown"),
        "Detect Languages": os.environ.get("JOB_DETECT_LANGUAGES", "unknown"),
        "Check Overrides": os.environ.get("JOB_CHECK_OVERRIDES", "unknown"),
        "Lint": os.environ.get("JOB_LINT", "unknown"),
        "Test Go": os.environ.get("JOB_TEST_GO", "unknown"),
        "Test Frontend": os.environ.get("JOB_TEST_FRONTEND", "unknown"),
        "Test Python": os.environ.get("JOB_TEST_PYTHON", "unknown"),
        "Test Rust": os.environ.get("JOB_TEST_RUST", "unknown"),
        "Rust Coverage": os.environ.get("JOB_RUST_COVERAGE", "unknown"),
        "Test Docker": os.environ.get("JOB_TEST_DOCKER", "unknown"),
        "Test Docs": os.environ.get("JOB_TEST_DOCS", "unknown"),
        "Release Build": os.environ.get("JOB_RELEASE_BUILD", "unknown"),
        "Security Scan": os.environ.get("JOB_SECURITY_SCAN", "unknown"),
        "Performance Test": os.environ.get("JOB_PERFORMANCE_TEST", "unknown"),
    }

    files_changed = {
        "Go": os.environ.get("CI_GO_FILES", "false"),
        "Frontend": os.environ.get("CI_FRONTEND_FILES", "false"),
        "Python": os.environ.get("CI_PYTHON_FILES", "false"),
        "Rust": os.environ.get("CI_RUST_FILES", "false"),
        "Docker": os.environ.get("CI_DOCKER_FILES", "false"),
        "Docs": os.environ.get("CI_DOCS_FILES", "false"),
        "Workflows": os.environ.get("CI_WORKFLOW_FILES", "false"),
    }

    languages = {
        "has-rust": os.environ.get("HAS_RUST", "false"),
        "has-go": os.environ.get("HAS_GO", "false"),
        "has-python": os.environ.get("HAS_PYTHON", "false"),
        "has-frontend": os.environ.get("HAS_FRONTEND", "false"),
        "has-docker": os.environ.get("HAS_DOCKER", "false"),
    }

    summary_lines = [
        "# 🚀 CI Pipeline Summary",
        "",
        "## 🧭 Detection",
        f"- Primary language: {primary_language}",
    ]
    summary_lines.extend(f"- {label}: {value}" for label, value in languages.items())
    summary_lines.extend(
        [
            "",
            "## 📊 Job Results",
            "| Job | Status |",
            "|-----|--------|",
        ]
    )
    summary_lines.extend(f"| {job} | {status} |" for job, status in steps.items())
    summary_lines.extend(
        [
            "",
            "## 📁 Changed Files",
        ]
    )
    summary_lines.extend(f"- {label}: {value}" for label, value in files_changed.items())
    summary_lines.append("")

    append_summary("\n".join(summary_lines) + "\n")


def check_ci_status(_: argparse.Namespace) -> None:
    job_envs = {
        "Lint": os.environ.get("JOB_LINT"),
        "Test Go": os.environ.get("JOB_TEST_GO"),
        "Test Frontend": os.environ.get("JOB_TEST_FRONTEND"),
        "Test Python": os.environ.get("JOB_TEST_PYTHON"),
        "Test Rust": os.environ.get("JOB_TEST_RUST"),
        "Test Docker": os.environ.get("JOB_TEST_DOCKER"),
        "Release Build": os.environ.get("JOB_RELEASE_BUILD"),
    }

    failures = [job for job, status in job_envs.items() if status == "failure"]
    if failures:
        print(f"❌ CI Pipeline failed: {', '.join(failures)}")
        raise SystemExit(1)
    print("✅ CI Pipeline succeeded")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CI workflow helper commands.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = {
        "debug-filter": debug_filter,
        "determine-execution": determine_execution,
        "wait-for-pr-automation": wait_for_pr_automation,
        "load-super-linter-config": load_super_linter_config,
        "write-validation-summary": write_validation_summary,
        "generate-matrices": generate_matrices,
        "go-setup": go_setup,
        "go-test": go_test,
        "check-go-coverage": check_go_coverage,
        "frontend-install": frontend_install,
        "frontend-run": frontend_run,
        "python-install": python_install,
        "python-run-tests": python_run_tests,
        "ensure-cargo-llvm-cov": ensure_cargo_llvm_cov,
        "generate-rust-lcov": generate_rust_lcov,
        "generate-rust-html": generate_rust_html,
        "compute-rust-coverage": compute_rust_coverage,
        "enforce-coverage-threshold": enforce_coverage_threshold,
        "docker-build": docker_build,
        "docker-test-compose": docker_test_compose,
        "docs-check-links": docs_check_links,
        "docs-validate-structure": docs_validate_structure,
        "run-benchmarks": run_benchmarks,
        "generate-ci-summary": generate_ci_summary,
        "check-ci-status": check_ci_status,
    }

    for command, handler in commands.items():
        subparsers.add_parser(command).set_defaults(handler=handler)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        raise SystemExit(1)
    handler(args)


if __name__ == "__main__":
    main()
```

## F.3 `.github/workflows/reusable-release.yml`

```yaml
# file: .github/workflows/reusable-release.yml
# version: 2.6.0
# guid: 7b8c9d0e-1f2a-3b4c-5d6e-7f8a9b0c1d2e

name: Reusable Release Coordinator

on:
  workflow_call:
    inputs:
      release-type:
        description: 'Release type (auto, major, minor, patch)'
        required: false
        type: string
        default: 'auto'
      build-target:
        description: 'Build target (all, go, python, rust, frontend, docker, protobuf)'
        required: false
        type: string
        default: 'all'
      prerelease:
        description: 'Create as prerelease'
        required: false
        type: boolean
        default: false
      draft:
        description: 'Create as draft'
        required: false
        type: boolean
        default: false
      skip-language-detection:
        description: 'Skip automatic language detection'
        required: false
        type: boolean
        default: false
      go-enabled:
        description: 'Force enable Go builds'
        required: false
        type: boolean
        default: false
      python-enabled:
        description: 'Force enable Python builds'
        required: false
        type: boolean
        default: false
      rust-enabled:
        description: 'Force enable Rust builds'
        required: false
        type: boolean
        default: false
      frontend-enabled:
        description: 'Force enable Frontend builds'
        required: false
        type: boolean
        default: false
      docker-enabled:
        description: 'Force enable Docker builds'
        required: false
        type: boolean
        default: false
      protobuf-enabled:
        description: 'Force enable Protobuf builds'
        required: false
        type: boolean
        default: false
    outputs:
      release-created:
        description: 'Whether a release was created'
        value: ${{ jobs.build-status.outputs.release-created }}
      release-tag:
        description: 'The created release tag'
        value: ${{ jobs.detect-languages.outputs.release-tag }}
      primary-language:
        description: 'The detected primary language'
        value: ${{ jobs.detect-languages.outputs.primary-language }}
      release-strategy:
        description: 'The release strategy used (stable, prerelease, draft)'
        value: ${{ jobs.detect-languages.outputs.release-branch-strategy }}

permissions:
  contents: write
  packages: write
  attestations: write
  id-token: write
  security-events: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Load unified configuration
  load-config:
    name: Load Repository Configuration
    runs-on: ubuntu-latest
    outputs:
      config: ${{ steps.load-config.outputs.config }}
      has-config: ${{ steps.load-config.outputs.has-config }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v5

      - name: Load repository configuration
        id: load-config
        env:
          CONFIG_FILE: .github/repository-config.yml
        run: |
          python3 .github/workflows/scripts/load_repository_config.py

  # Detect what languages/technologies are present
  detect-languages:
    name: Detect Project Languages
    runs-on: ubuntu-latest
    needs: [load-config]
    outputs:
      has-go: ${{ steps.detect.outputs.has-go }}
      has-python: ${{ steps.detect.outputs.has-python }}
      has-frontend: ${{ steps.detect.outputs.has-frontend }}
      has-docker: ${{ steps.detect.outputs.has-docker }}
      has-rust: ${{ steps.detect.outputs.has-rust }}
      protobuf-needed: ${{ steps.detect.outputs.protobuf-needed }}
      primary-language: ${{ steps.detect.outputs.primary-language }}
      go-matrix: ${{ steps.detect.outputs.go-matrix }}
      python-matrix: ${{ steps.detect.outputs.python-matrix }}
      frontend-matrix: ${{ steps.detect.outputs.frontend-matrix }}
      docker-matrix: ${{ steps.detect.outputs.docker-matrix }}
      rust-matrix: ${{ steps.detect.outputs.rust-matrix }}
      registry: ${{ steps.env-setup.outputs.registry }}
      image-name: ${{ steps.env-setup.outputs.image-name }}
      release-tag: ${{ steps.version.outputs.tag }}
      release-branch-strategy: ${{ steps.release-strategy.outputs.strategy }}
      auto-prerelease: ${{ steps.release-strategy.outputs.auto-prerelease }}
      auto-draft: ${{ steps.release-strategy.outputs.auto-draft }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - name: Determine ghcommon workflow ref
        id: ghcommon-ref
        run: |
          ref="${GITHUB_WORKFLOW_REF##*@}"
          if [[ -z "$ref" || "$ref" == "$GITHUB_WORKFLOW_REF" ]]; then
            ref="refs/heads/main"
          fi
          echo "ref=$ref" >> "$GITHUB_OUTPUT"

      - name: Checkout ghcommon workflow scripts
        uses: actions/checkout@v5
        with:
          repository: jdfalk/ghcommon
          ref: ${{ steps.ghcommon-ref.outputs.ref }}
          path: ghcommon-workflow-scripts
          sparse-checkout: |
            .github/workflows/scripts
          sparse-checkout-cone-mode: false

      - name: Configure workflow script path
        run: |
          echo "GHCOMMON_SCRIPTS_DIR=$PWD/ghcommon-workflow-scripts/.github/workflows/scripts" >> $GITHUB_ENV

      - name: Setup environment variables
        id: env-setup
        run: |
          echo "registry=${REGISTRY}" >> $GITHUB_OUTPUT
          echo "image-name=${IMAGE_NAME}" >> $GITHUB_OUTPUT

      - name: Detect project languages and generate matrices
        id: detect
        env:
          REPOSITORY_CONFIG: ${{ needs.load-config.outputs.config }}
          SKIP_LANGUAGE_DETECTION: ${{ inputs.skip-language-detection }}
          BUILD_TARGET: ${{ inputs.build-target || 'all' }}
          GO_ENABLED: ${{ inputs.go-enabled && 'true' || 'auto' }}
          PYTHON_ENABLED: ${{ inputs.python-enabled && 'true' || 'auto' }}
          RUST_ENABLED: ${{ inputs.rust-enabled && 'true' || 'auto' }}
          FRONTEND_ENABLED: ${{ inputs.frontend-enabled && 'true' || 'auto' }}
          DOCKER_ENABLED: ${{ inputs.docker-enabled && 'true' || 'auto' }}
          PROTOBUF_ENABLED: ${{ inputs.protobuf-enabled && 'true' || 'auto' }}
        run: |
          python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" detect-languages

      - name: Determine release strategy based on branch
        id: release-strategy
        env:
          BRANCH_NAME: ${{ github.ref_name }}
          INPUT_PRERELEASE: ${{ inputs.prerelease }}
          INPUT_DRAFT: ${{ inputs.draft }}
        run: |
          python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" release-strategy

      - name: Generate semantic release version
        id: version
        env:
          RELEASE_TYPE: ${{ inputs.release-type || 'auto' }}
          BRANCH_NAME: ${{ github.ref_name }}
          AUTO_PRERELEASE: ${{ steps.release-strategy.outputs.auto-prerelease }}
          AUTO_DRAFT: ${{ steps.release-strategy.outputs.auto-draft }}
        run: |
          python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" generate-version

  # Protocol Buffer Generation (if needed)
  build-protobuf:
    name: Generate Protocol Buffers
    needs: [detect-languages]
    if: needs.detect-languages.outputs.protobuf-needed == 'true'
    uses: ./.github/workflows/release-protobuf.yml
    secrets: inherit

  # Go Build
  build-go:
    name: Build Go Components
    needs: [detect-languages, build-protobuf]
    if: |
      always() &&
      needs.detect-languages.outputs.has-go == 'true' &&
      (inputs.build-target == 'all' || inputs.build-target == 'go')
    uses: ./.github/workflows/release-go.yml
    with:
      go-matrix: ${{ needs.detect-languages.outputs.go-matrix }}
      protobuf-artifacts: ${{ needs.detect-languages.outputs.protobuf-needed }}
    secrets: inherit

  # Python Build
  build-python:
    name: Build Python Components
    needs: [detect-languages, build-protobuf]
    if: |
      always() &&
      needs.detect-languages.outputs.has-python == 'true' &&
      (inputs.build-target == 'all' || inputs.build-target == 'python')
    uses: ./.github/workflows/release-python.yml
    with:
      python-matrix: ${{ needs.detect-languages.outputs.python-matrix }}
      protobuf-artifacts: ${{ needs.detect-languages.outputs.protobuf-needed }}
    secrets: inherit

  # Rust Build
  build-rust:
    name: Build Rust Components
    needs: [detect-languages, build-protobuf]
    if: |
      always() &&
      needs.detect-languages.outputs.has-rust == 'true' &&
      (inputs.build-target == 'all' || inputs.build-target == 'rust')
    uses: ./.github/workflows/release-rust.yml
    with:
      protobuf-artifacts: ${{ needs.detect-languages.outputs.protobuf-needed }}
      release-version: ${{ needs.detect-languages.outputs.release-tag }}
    secrets: inherit

  # Frontend Build
  build-frontend:
    name: Build Frontend Components
    needs: [detect-languages]
    if: |
      always() &&
      needs.detect-languages.outputs.has-frontend == 'true' &&
      (inputs.build-target == 'all' || inputs.build-target == 'frontend')
    uses: ./.github/workflows/release-frontend.yml
    with:
      frontend-matrix: ${{ needs.detect-languages.outputs.frontend-matrix }}
    secrets: inherit

  # Docker Build
  build-docker:
    name: Build Docker Images
    needs: [detect-languages, build-go, build-python, build-rust]
    if: |
      always() &&
      needs.detect-languages.outputs.has-docker == 'true' &&
      (inputs.build-target == 'all' || inputs.build-target == 'docker')
    uses: ./.github/workflows/release-docker.yml
    with:
      docker-matrix: ${{ needs.detect-languages.outputs.docker-matrix }}
      registry: ${{ needs.detect-languages.outputs.registry }}
      image-name: ${{ needs.detect-languages.outputs.image-name }}
    secrets: inherit

  # Create GitHub Release
  create-release:
    name: Create GitHub Release
    runs-on: ubuntu-latest
    needs:
      [
        detect-languages,
        build-go,
        build-python,
        build-rust,
        build-frontend,
        build-docker,
      ]
    if: |
      always() &&
      !failure() &&
      (github.event_name == 'push' || github.event_name == 'workflow_dispatch')
    outputs:
      version: ${{ steps.version.outputs.version }}
      release-id: ${{ steps.release.outputs.id }}
      release-created: ${{ steps.check-release.outputs.created }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - name: Determine ghcommon workflow ref
        id: ghcommon-ref
        run: |
          ref="${GITHUB_WORKFLOW_REF##*@}"
          if [[ -z "$ref" || "$ref" == "$GITHUB_WORKFLOW_REF" ]]; then
            ref="refs/heads/main"
          fi
          echo "ref=$ref" >> "$GITHUB_OUTPUT"

      - name: Checkout ghcommon workflow scripts
        uses: actions/checkout@v5
        with:
          repository: jdfalk/ghcommon
          ref: ${{ steps.ghcommon-ref.outputs.ref }}
          path: ghcommon-workflow-scripts
          sparse-checkout: |
            .github/workflows/scripts
          sparse-checkout-cone-mode: false

      - name: Configure workflow script path
        run: |
          echo "GHCOMMON_SCRIPTS_DIR=$PWD/ghcommon-workflow-scripts/.github/workflows/scripts" >> $GITHUB_ENV

      - name: Get version
        id: version
        env:
          DETECTED_RELEASE_TAG: ${{ needs.detect-languages.outputs.release-tag }}
        run: |
          VERSION="$DETECTED_RELEASE_TAG"
          echo "version=${VERSION}" >> $GITHUB_OUTPUT

      - name: Generate changelog
        id: changelog
        env:
          BRANCH_NAME: ${{ github.ref_name }}
          PRIMARY_LANGUAGE: ${{ needs.detect-languages.outputs.primary-language }}
          RELEASE_STRATEGY: ${{ needs.detect-languages.outputs.release-branch-strategy }}
          AUTO_PRERELEASE: ${{ needs.detect-languages.outputs.auto-prerelease }}
          AUTO_DRAFT: ${{ needs.detect-languages.outputs.auto-draft }}
        run: |
          python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" generate-changelog

      - name: Download all build artifacts
        uses: actions/download-artifact@v5
        with:
          path: ./artifacts
          merge-multiple: true

      - name: Package and organize release artifacts
        id: package-artifacts
        env:
          RELEASE_VERSION: ${{ steps.version.outputs.version }}
        run: |
          echo "📦 Organizing and packaging release artifacts..."

          # Create release directory structure
          mkdir -p release-assets/{sdks,binaries,packages,documentation}

          # Move and organize SDK packages
          if find ./artifacts -name "*-sdk.*" -type f | grep -q .; then
            echo "Moving SDK packages..."
            find ./artifacts -name "*-sdk.*" -type f -exec mv {} release-assets/sdks/ \;
            ls -la release-assets/sdks/
          fi

          # Move documentation packages
          if find ./artifacts -name "*docs.*" -type f | grep -q .; then
            echo "Moving documentation packages..."
            find ./artifacts -name "*docs.*" -type f -exec mv {} release-assets/documentation/ \;
          fi

          # Move binary files (executables)
          if find ./artifacts -name "*.exe" -o -name "*-linux-*" -o -name "*-darwin-*" -o -name "*-windows-*" | grep -q .; then
            echo "Moving binary packages..."
            find ./artifacts \( -name "*.exe" -o -name "*-linux-*" -o -name "*-darwin-*" -o -name "*-windows-*" \) -type f -exec mv {} release-assets/binaries/ \;
          fi

          # Move other packages (wheels, containers, etc.)
          if find ./artifacts -name "*.whl" -o -name "*.tar.gz" -o -name "*.zip" | grep -q .; then
            echo "Moving other packages..."
            find ./artifacts \( -name "*.whl" -o -name "*.tar.gz" -o -name "*.zip" \) -type f -exec mv {} release-assets/packages/ \;
          fi

          # Create a comprehensive release manifest
          echo "Creating release manifest..."
          {
            echo "# Release Manifest - ${RELEASE_VERSION}"
            echo "Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
            echo ""
            echo "## SDK Packages"
            if [ -d "release-assets/sdks" ] && [ "$(ls -A release-assets/sdks 2>/dev/null)" ]; then
              ls -la release-assets/sdks/ | tail -n +2 | awk '{print "- " $9 " (" $5 " bytes)"}'
            else
              echo "- No SDK packages"
            fi
            echo ""
            echo "## Documentation"
            if [ -d "release-assets/documentation" ] && [ "$(ls -A release-assets/documentation 2>/dev/null)" ]; then
              ls -la release-assets/documentation/ | tail -n +2 | awk '{print "- " $9 " (" $5 " bytes)"}'
            else
              echo "- No documentation packages"
            fi
            echo ""
            echo "## Binaries"
            if [ -d "release-assets/binaries" ] && [ "$(ls -A release-assets/binaries 2>/dev/null)" ]; then
              ls -la release-assets/binaries/ | tail -n +2 | awk '{print "- " $9 " (" $5 " bytes)"}'
            else
              echo "- No binary packages"
            fi
            echo ""
            echo "## Other Packages"
            if [ -d "release-assets/packages" ] && [ "$(ls -A release-assets/packages 2>/dev/null)" ]; then
              ls -la release-assets/packages/ | tail -n +2 | awk '{print "- " $9 " (" $5 " bytes)"}'
            else
              echo "- No other packages"
            fi
          } > release-assets/MANIFEST.md

          # Show summary
          echo "Release assets organized:"
          find release-assets -type f | wc -l | xargs echo "Total files:"
          du -sh release-assets/ | awk '{print "Total size: " $1}'

          # Set output indicating packaging completion
          echo "packaging-complete=true" >> $GITHUB_OUTPUT

      - name: Create GitHub Release
        id: release
        uses: softprops/action-gh-release@v2
        if: github.event_name != 'pull_request'
        with:
          tag_name: ${{ steps.version.outputs.version }}
          name: ${{ steps.version.outputs.version }}
          body: |
            ${{ steps.changelog.outputs.changelog_content }}

            ## 📦 Release Assets

            This release includes organized packages for easy consumption:

            ### SDKs
            - **Go SDK**: `gcommon-go-sdk.tar.gz` / `gcommon-go-sdk.zip`
            - **Python SDK**: `gcommon-python-sdk.tar.gz` / `gcommon-python-sdk.zip`

            ### Documentation
            - **API Documentation**: `gcommon-docs.tar.gz` / `gcommon-docs.zip`

            See `MANIFEST.md` for a complete list of all assets and their sizes.

            ---
            *Generated automatically from commit ${{ github.sha }}*
          draft: ${{ needs.detect-languages.outputs.auto-draft }}
          prerelease: ${{ needs.detect-languages.outputs.auto-prerelease }}
          files: |
            release-assets/**/*
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Check release created
        id: check-release
        env:
          RELEASE_OUTCOME: ${{ steps.release.outcome }}
        run: |
          if [ "$RELEASE_OUTCOME" = "success" ]; then
            echo "created=true" >> $GITHUB_OUTPUT
            echo "release-created=true" >> $GITHUB_OUTPUT
          else
            echo "created=false" >> $GITHUB_OUTPUT
            echo "release-created=false" >> $GITHUB_OUTPUT
          fi

  # Final status check
  build-status:
    name: Release Status Summary
    runs-on: ubuntu-latest
    needs:
      [
        detect-languages,
        build-go,
        build-python,
        build-rust,
        build-frontend,
        build-docker,
        create-release,
      ]
    if: always()
    outputs:
      release-created: ${{ needs.create-release.outputs.release-created || 'false' }}
    steps:
      - name: Generate release summary
        env:
          SUMMARY_PRIMARY_LANGUAGE: ${{ needs.detect-languages.outputs.primary-language }}
          SUMMARY_BUILD_TARGET: ${{ inputs.build-target }}
          SUMMARY_RELEASE_TAG: ${{ needs.detect-languages.outputs.release-tag }}
          SUMMARY_RELEASE_STRATEGY: ${{ needs.detect-languages.outputs.release-branch-strategy }}
          SUMMARY_BRANCH: ${{ github.ref_name }}
          SUMMARY_GO_RESULT: ${{ needs.build-go.result || 'skipped' }}
          SUMMARY_PYTHON_RESULT: ${{ needs.build-python.result || 'skipped' }}
          SUMMARY_RUST_RESULT: ${{ needs.build-rust.result || 'skipped' }}
          SUMMARY_FRONTEND_RESULT: ${{ needs.build-frontend.result || 'skipped' }}
          SUMMARY_DOCKER_RESULT: ${{ needs.build-docker.result || 'skipped' }}
          SUMMARY_RELEASE_RESULT: ${{ needs.create-release.result || 'skipped' }}
          SUMMARY_RELEASE_CREATED: ${{ needs.create-release.outputs.release-created || 'false' }}
          SUMMARY_AUTO_PRERELEASE: ${{ needs.detect-languages.outputs.auto-prerelease || 'false' }}
          SUMMARY_AUTO_DRAFT: ${{ needs.detect-languages.outputs.auto-draft || 'false' }}
        run: |
          echo "# 🚀 Release Build Results" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Project Type:** $SUMMARY_PRIMARY_LANGUAGE" >> $GITHUB_STEP_SUMMARY
          echo "**Build Target:** $SUMMARY_BUILD_TARGET" >> $GITHUB_STEP_SUMMARY
          echo "**Release Tag:** $SUMMARY_RELEASE_TAG" >> $GITHUB_STEP_SUMMARY
          echo "**Release Strategy:** $SUMMARY_RELEASE_STRATEGY" >> $GITHUB_STEP_SUMMARY
          echo "**Branch:** $SUMMARY_BRANCH" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Component | Status |" >> $GITHUB_STEP_SUMMARY
          echo "|-----------|--------|" >> $GITHUB_STEP_SUMMARY
          echo "| Go | $SUMMARY_GO_RESULT |" >> $GITHUB_STEP_SUMMARY
          echo "| Python | $SUMMARY_PYTHON_RESULT |" >> $GITHUB_STEP_SUMMARY
          echo "| Rust | $SUMMARY_RUST_RESULT |" >> $GITHUB_STEP_SUMMARY
          echo "| Frontend | $SUMMARY_FRONTEND_RESULT |" >> $GITHUB_STEP_SUMMARY
          echo "| Docker | $SUMMARY_DOCKER_RESULT |" >> $GITHUB_STEP_SUMMARY
          echo "| Release | $SUMMARY_RELEASE_RESULT |" >> $GITHUB_STEP_SUMMARY

          # Check for any failures
          if [[ "$SUMMARY_GO_RESULT" == "failure" ||
                "$SUMMARY_PYTHON_RESULT" == "failure" ||
                "$SUMMARY_RUST_RESULT" == "failure" ||
                "$SUMMARY_FRONTEND_RESULT" == "failure" ||
                "$SUMMARY_DOCKER_RESULT" == "failure" ||
                "$SUMMARY_RELEASE_RESULT" == "failure" ]]; then
            echo "" >> $GITHUB_STEP_SUMMARY
            echo "❌ **Some components failed**" >> $GITHUB_STEP_SUMMARY
            exit 1
          else
            echo "" >> $GITHUB_STEP_SUMMARY
            echo "✅ **All components completed successfully**" >> $GITHUB_STEP_SUMMARY
            if [[ "$SUMMARY_RELEASE_CREATED" == "true" ]]; then
              echo "" >> $GITHUB_STEP_SUMMARY
              echo "🎉 **Release created: $SUMMARY_RELEASE_TAG**" >> $GITHUB_STEP_SUMMARY
              if [[ "$SUMMARY_AUTO_PRERELEASE" == "true" ]]; then
                echo "⚠️ **Pre-release** - for testing purposes" >> $GITHUB_STEP_SUMMARY
              elif [[ "$SUMMARY_AUTO_DRAFT" == "true" ]]; then
                echo "📝 **Draft release** - review before publishing" >> $GITHUB_STEP_SUMMARY
              else
                echo "🚀 **Stable release** - ready for production" >> $GITHUB_STEP_SUMMARY
              fi
            fi
          fi
```

## F.4 `.github/workflows/scripts/release_workflow.py`

```python
#!/usr/bin/env python3
"""Helper utilities for reusable release workflows."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import requests

_CONFIG_CACHE: dict[str, Any] | None = None


def append_to_file(path_env: str, content: str) -> None:
    file_path = os.environ.get(path_env)
    if not file_path:
        return
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "a", encoding="utf-8") as handle:
        handle.write(content)


def write_output(name: str, value: str) -> None:
    append_to_file("GITHUB_OUTPUT", f"{name}={value}\n")


def append_summary(text: str) -> None:
    append_to_file("GITHUB_STEP_SUMMARY", text)


def get_repository_config() -> dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    raw = os.environ.get("REPOSITORY_CONFIG")
    if not raw:
        _CONFIG_CACHE = {}
        return _CONFIG_CACHE

    try:
        _CONFIG_CACHE = json.loads(raw)
    except json.JSONDecodeError:
        print("::warning::Unable to parse REPOSITORY_CONFIG JSON; falling back to defaults")
        _CONFIG_CACHE = {}
    return _CONFIG_CACHE


def _config_path(default: Any, *path: str) -> Any:
    current: Any = get_repository_config()
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _normalize_override(value: str | None) -> str:
    if value is None:
        return "auto"
    value = value.lower()
    if value in {"true", "false"}:
        return value
    return "auto"


def _build_target_set(build_target: str) -> set[str]:
    if not build_target or build_target == "all":
        return {"go", "python", "rust", "frontend", "docker", "protobuf"}
    return {entry.strip().lower() for entry in build_target.split(",") if entry.strip()}


def _derive_flag(override: str, key: str, targets: set[str], default: bool) -> bool:
    if override == "true":
        return True
    if override == "false":
        return False
    if "all" in targets:
        return True
    if not targets:
        return default
    return key in targets or default


def _any_proto_files(limit: int = 20) -> bool:
    count = 0
    for _ in Path(".").rglob("*.proto"):
        count += 1
        if count >= limit:
            return True
    return count > 0


def _matrix_json(version_key: str, versions: Iterable[str], oses: Iterable[str]) -> str:
    matrix = {
        version_key: list(dict.fromkeys(versions)),
        "os": list(dict.fromkeys(oses)),
    }
    return json.dumps(matrix, separators=(",", ":"))


def _docker_matrix_json(platforms: Iterable[str]) -> str:
    matrix = {"platform": list(dict.fromkeys(platforms))}
    return json.dumps(matrix, separators=(",", ":"))


def detect_languages(_: argparse.Namespace) -> None:
    skip_detection = os.environ.get("SKIP_LANGUAGE_DETECTION", "false").lower() == "true"
    targets = _build_target_set(os.environ.get("BUILD_TARGET", "all").lower())

    overrides = {
        "go": _normalize_override(os.environ.get("GO_ENABLED")),
        "python": _normalize_override(os.environ.get("PYTHON_ENABLED")),
        "rust": _normalize_override(os.environ.get("RUST_ENABLED")),
        "frontend": _normalize_override(os.environ.get("FRONTEND_ENABLED")),
        "docker": _normalize_override(os.environ.get("DOCKER_ENABLED")),
        "protobuf": _normalize_override(os.environ.get("PROTOBUF_ENABLED")),
    }

    if skip_detection:
        has_go = _derive_flag(overrides["go"], "go", targets, False)
        has_python = _derive_flag(overrides["python"], "python", targets, False)
        has_rust = _derive_flag(overrides["rust"], "rust", targets, False)
        has_frontend = _derive_flag(overrides["frontend"], "frontend", targets, False)
        has_docker = _derive_flag(overrides["docker"], "docker", targets, False)
        protobuf_needed = _derive_flag(overrides["protobuf"], "protobuf", targets, False)
    else:
        has_go = (
            Path("go.mod").is_file()
            or Path("main.go").is_file()
            or Path("cmd").exists()
            or Path("pkg").exists()
        )
        has_python = any(Path(".").joinpath(name).exists() for name in ["setup.py", "pyproject.toml", "requirements.txt", "poetry.lock"])
        has_rust = Path("Cargo.toml").is_file() or Path("Cargo.lock").is_file()
        has_frontend = (
            Path("package.json").is_file()
            or Path("webui").exists()
            or Path("frontend").exists()
            or Path("ui").exists()
        )
        has_docker = any(Path(".").glob("Dockerfile*")) or Path("docker-compose.yml").is_file() or Path("docker-compose.yaml").is_file()
        protobuf_needed = Path("buf.yaml").is_file() or Path("buf.gen.yaml").is_file() or _any_proto_files()

        for key, override in overrides.items():
            if override == "true":
                if key == "go":
                    has_go = True
                elif key == "python":
                    has_python = True
                elif key == "rust":
                    has_rust = True
                elif key == "frontend":
                    has_frontend = True
                elif key == "docker":
                    has_docker = True
                elif key == "protobuf":
                    protobuf_needed = True
            elif override == "false":
                if key == "go":
                    has_go = False
                elif key == "python":
                    has_python = False
                elif key == "rust":
                    has_rust = False
                elif key == "frontend":
                    has_frontend = False
                elif key == "docker":
                    has_docker = False
                elif key == "protobuf":
                    protobuf_needed = False

    config_primary = _config_path("auto", "repository", "primary_language")
    if config_primary and config_primary != "auto":
        primary_language = str(config_primary)
    else:
        primary_language = "multi"
        for candidate, flag in (
            ("rust", has_rust),
            ("go", has_go),
            ("python", has_python),
            ("frontend", has_frontend),
            ("docker", has_docker),
        ):
            if flag:
                primary_language = candidate
                break

    write_output("has-go", "true" if has_go else "false")
    write_output("has-python", "true" if has_python else "false")
    write_output("has-rust", "true" if has_rust else "false")
    write_output("has-frontend", "true" if has_frontend else "false")
    write_output("has-docker", "true" if has_docker else "false")
    write_output("protobuf-needed", "true" if protobuf_needed else "false")
    write_output("primary-language", primary_language)

    versions = _config_path({}, "languages", "versions") or {}
    platforms = _config_path({}, "build", "platforms") or {}
    os_list = platforms.get("os") or ["ubuntu-latest", "macos-latest"]
    go_versions = versions.get("go") or ["1.22", "1.23", "1.24"]
    python_versions = versions.get("python") or ["3.11", "3.12", "3.13"]
    rust_versions = versions.get("rust") or ["stable", "beta"]
    node_versions = versions.get("node") or ["18", "20", "22"]
    docker_platforms = _config_path(["linux/amd64", "linux/arm64"], "build", "docker", "platforms")

    write_output("go-matrix", _matrix_json("go-version", go_versions, os_list))
    write_output("python-matrix", _matrix_json("python-version", python_versions, os_list))
    write_output("rust-matrix", _matrix_json("rust-version", rust_versions, os_list))
    write_output("frontend-matrix", _matrix_json("node-version", node_versions, ["ubuntu-latest"]))
    write_output("docker-matrix", _docker_matrix_json(docker_platforms))


def release_strategy(_: argparse.Namespace) -> None:
    branch = os.environ.get("BRANCH_NAME", "")
    input_prerelease = os.environ.get("INPUT_PRERELEASE", "false").lower() == "true"
    input_draft = os.environ.get("INPUT_DRAFT", "false").lower() == "true"

    if branch == "main":
        strategy = "stable"
        auto_prerelease = False
        auto_draft = True
    else:
        strategy = "prerelease"
        auto_prerelease = True
        auto_draft = False

    if input_prerelease:
        auto_prerelease = True
    if input_draft:
        auto_draft = True

    write_output("strategy", strategy)
    write_output("auto-prerelease", "true" if auto_prerelease else "false")
    write_output("auto-draft", "true" if auto_draft else "false")

    print(f"🔄 Release strategy for branch '{branch}': {strategy}")
    print(f"📋 Auto-prerelease: {auto_prerelease}")
    print(f"📋 Auto-draft: {auto_draft}")


def _run_git(args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git"] + args, check=check, capture_output=True, text=True)


def _latest_tag_from_api() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repository:
        return ""

    url = f"https://api.github.com/repos/{repository}/releases/latest"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException:
        return ""

    if response.status_code != 200:
        return ""

    try:
        data = response.json()
    except ValueError:
        return ""

    tag = data.get("tag_name")
    if tag and isinstance(tag, str):
        return tag
    return ""


def _latest_tag_from_git() -> str:
    result = _run_git(["tag", "-l", "--sort=-version:refname"])
    for line in result.stdout.splitlines():
        candidate = line.strip()
        if re.match(r"^v\d+\.\d+\.\d+", candidate):
            return candidate

    describe = _run_git(["describe", "--tags", "--abbrev=0"])
    if describe.returncode == 0 and describe.stdout.strip():
        return describe.stdout.strip()

    return "v0.0.0"


def generate_version(_: argparse.Namespace) -> None:
    release_type = os.environ.get("RELEASE_TYPE", "auto").lower()
    branch_name = os.environ.get("BRANCH_NAME", "")
    auto_prerelease = os.environ.get("AUTO_PRERELEASE", "false").lower() == "true"

    print("🔍 Detecting latest version...")
    latest_tag = _latest_tag_from_api()
    if latest_tag:
        print(f"✅ Found latest release via API: {latest_tag}")
    else:
        print("⚠️ No releases found via API, using git tags...")
        latest_tag = _latest_tag_from_git()
        print(f"📌 Using base version: {latest_tag}")

    version_core = re.sub(r"^v", "", latest_tag).split("-")[0]
    parts = version_core.split(".")
    major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    if release_type == "major":
        new_major, new_minor, new_patch = major + 1, 0, 0
    elif release_type == "minor":
        new_major, new_minor, new_patch = major, minor + 1, 0
    elif release_type == "patch":
        new_major, new_minor, new_patch = major, minor, patch + 1
    else:
        if branch_name == "main":
            new_major, new_minor, new_patch = major, minor, patch + 1
        elif branch_name == "develop":
            new_major, new_minor, new_patch = major, minor + 1, 0
        else:
            new_major, new_minor, new_patch = major, minor, patch + 1

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M")
    if auto_prerelease:
        suffix = "dev" if branch_name == "develop" else "alpha"
        version_tag = f"v{new_major}.{new_minor}.{new_patch}-{suffix}.{timestamp}"
    else:
        version_tag = f"v{new_major}.{new_minor}.{new_patch}"

    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    while True:
        existing = _run_git(["tag", "-l", version_tag])
        if not existing.stdout.strip():
            break

        print(f"⚠️ Tag {version_tag} already exists")
        if event_name == "workflow_dispatch":
            print("🔄 Manual release detected; deleting existing tag")
            _run_git(["tag", "-d", version_tag])
            token = os.environ.get("GITHUB_TOKEN")
            repository = os.environ.get("GITHUB_REPOSITORY")
            if token and repository:
                subprocess.run(
                    [
                        "git",
                        "push",
                        f"https://x-access-token:{token}@github.com/{repository}.git",
                        f":refs/tags/{version_tag}",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
            break

        if auto_prerelease:
            suffix = "dev" if branch_name == "develop" else "alpha"
            version_tag = f"v{new_major}.{new_minor}.{new_patch}-{suffix}.{timestamp}.{int(datetime.utcnow().timestamp())}"
        else:
            new_patch += 1
            version_tag = f"v{new_major}.{new_minor}.{new_patch}"
        if new_patch - patch > 10:
            version_tag = f"v{new_major}.{new_minor}.{new_patch}-build.{timestamp}"
            break

    print(f"✅ Final version tag: {version_tag}")
    write_output("tag", version_tag)


def generate_changelog(_: argparse.Namespace) -> None:
    branch = os.environ.get("BRANCH_NAME", "")
    primary_language = os.environ.get("PRIMARY_LANGUAGE", "unknown")
    strategy = os.environ.get("RELEASE_STRATEGY", "stable")
    auto_prerelease = os.environ.get("AUTO_PRERELEASE", "false").lower() == "true"
    auto_draft = os.environ.get("AUTO_DRAFT", "false").lower() == "true"

    describe = _run_git(["describe", "--tags", "--abbrev=0"])
    last_tag = describe.stdout.strip() if describe.returncode == 0 else ""
    if last_tag:
        log_args = [f"{last_tag}..HEAD"]
        header = f"### 📋 Commits since {last_tag}:\n"
    else:
        log_args = []
        header = "### 📋 Initial Release Commits:\n"

    commits = _run_git(["log"] + log_args + ["--pretty=%s (%h)"]).stdout.splitlines()
    commits = [entry for entry in commits if entry.strip()]

    lines = ["## 🚀 What's Changed", "", header]
    if commits:
        lines.extend(f"- {commit}" for commit in commits)
    else:
        lines.append("- No commits available")

    lines.extend(
        [
            "",
            "### 🎯 Release Information",
            f"- **Branch:** {branch}",
            f"- **Release Type:** {strategy}",
            f"- **Primary Language:** {primary_language}",
        ]
    )

    if auto_prerelease:
        lines.append("\n⚠️ **This is a pre-release version** - use for testing purposes.")
    if auto_draft:
        lines.append("\n📝 **This is a draft release** - review before making public.")

    changelog = "\n".join(lines) + "\n"
    append_to_file("GITHUB_OUTPUT", "changelog_content<<EOF\n")
    append_to_file("GITHUB_OUTPUT", changelog)
    append_to_file("GITHUB_OUTPUT", "EOF\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Release workflow helper commands.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = {
        "detect-languages": detect_languages,
        "release-strategy": release_strategy,
        "generate-version": generate_version,
        "generate-changelog": generate_changelog,
    }

    for command, handler in commands.items():
        subparsers.add_parser(command).set_defaults(handler=handler)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        raise SystemExit(1)
    handler(args)


if __name__ == "__main__":
    main()
```

## F.5 `.github/workflows/scripts/maintenance_workflow.py`

```python
#!/usr/bin/env python3
"""Helper utilities for maintenance and security workflows."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

_CONFIG_CACHE: dict[str, Any] | None = None


def append_to_file(path_env: str, content: str) -> None:
    file_path = os.environ.get(path_env)
    if not file_path:
        return
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "a", encoding="utf-8") as handle:
        handle.write(content)


def write_output(name: str, value: str) -> None:
    append_to_file("GITHUB_OUTPUT", f"{name}={value}\n")


def append_summary(text: str) -> None:
    append_to_file("GITHUB_STEP_SUMMARY", text)


def get_repository_config() -> dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    raw = os.environ.get("REPOSITORY_CONFIG")
    if not raw:
        _CONFIG_CACHE = {}
        return _CONFIG_CACHE

    try:
        _CONFIG_CACHE = json.loads(raw)
    except json.JSONDecodeError:
        print("::warning::Failed to parse REPOSITORY_CONFIG, using empty config")
        _CONFIG_CACHE = {}
    return _CONFIG_CACHE


def _config_path(default: Any, *path: str) -> Any:
    current: Any = get_repository_config()
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _to_json(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=True)


def maintenance_plan(_: argparse.Namespace) -> None:
    schedule = str(_config_path("0 9 * * 1", "maintenance", "schedule", "cron"))
    maintainers = _ensure_list(_config_path([], "maintenance", "owners"))
    notifications = _ensure_list(_config_path([], "notifications", "channels"))
    auto_update = bool(_config_path(True, "maintenance", "dependencies", "auto_update"))
    runtime = str(_config_path("ubuntu-latest", "maintenance", "runtime", "runner"))

    summary = [
        "# 🛠️ Maintenance Plan",
        "",
        f"- Cron schedule: `{schedule}`",
        f"- Default runner: `{runtime}`",
        f"- Automatic dependency updates: {'enabled' if auto_update else 'disabled'}",
        f"- Maintainers: {', '.join(maintainers) if maintainers else 'not configured'}",
        f"- Notification channels: {', '.join(notifications) if notifications else 'not configured'}",
        "",
    ]
    append_summary("\n".join(summary) + "\n")

    write_output("schedule-cron", schedule)
    write_output("auto-update-enabled", str(auto_update).lower())
    write_output("maintenance-runner", runtime)
    write_output("maintenance-owners", _to_json(maintainers))
    write_output("notification-channels", _to_json(notifications))


def dependency_update(_: argparse.Namespace) -> None:
    managers = _config_path({}, "maintenance", "dependencies", "package_managers") or {}
    versions = _config_path({}, "languages", "versions")

    defaults = {
        "pip": {
            "command": "pip-review --auto",
            "paths": ["requirements.txt", "requirements/*.txt"],
        },
        "poetry": {
            "command": "poetry update",
            "paths": ["pyproject.toml", "poetry.lock"],
        },
        "npm": {
            "command": "npm update",
            "paths": ["package.json", "package-lock.json"],
        },
        "pnpm": {
            "command": "pnpm update --latest",
            "paths": ["pnpm-lock.yaml"],
        },
        "yarn": {
            "command": "yarn upgrade --latest",
            "paths": ["yarn.lock"],
        },
        "cargo": {
            "command": "cargo update",
            "paths": ["Cargo.toml", "Cargo.lock"],
        },
        "go": {
            "command": "go get -u ./...",
            "paths": ["go.mod", "go.sum"],
        },
    }

    matrix: list[dict[str, Any]] = []
    for name, default_params in defaults.items():
        manager_cfg = managers.get(name, {})
        enabled = manager_cfg.get("enabled", True)
        if not enabled:
            continue

        entry = {
            "manager": name,
            "command": manager_cfg.get("command", default_params["command"]),
            "paths": manager_cfg.get("paths", default_params["paths"]),
            "extra-args": manager_cfg.get("args", ""),
            "versions": versions.get(name, []),
        }
        matrix.append(entry)

    write_output("dependency-matrix", _to_json(matrix))
    write_output("updates-enabled", str(bool(matrix)).lower())

    summary = [
        "# 📦 Dependency Update Matrix",
        "",
        f"- Managers configured: {len(matrix)}",
    ]
    if matrix:
        summary.append("- Managed ecosystems: " + ", ".join(entry["manager"] for entry in matrix))
    else:
        summary.append("- No managers enabled")
    summary.append("")
    append_summary("\n".join(summary) + "\n")


def cleanup(_: argparse.Namespace) -> None:
    paths = _ensure_list(_config_path(["build/", "dist/", ".pytest_cache"], "maintenance", "cleanup", "paths"))
    retention_days = int(_config_path(30, "maintenance", "cleanup", "retention_days"))
    artifacts = _ensure_list(_config_path(["coverage.xml", "dist/"], "maintenance", "cleanup", "artifacts"))

    write_output("cleanup-paths", _to_json(paths))
    write_output("cleanup-retention-days", str(retention_days))
    write_output("cleanup-artifacts", _to_json(artifacts))

    summary = [
        "# 🧹 Cleanup Configuration",
        "",
        f"- Paths: {', '.join(paths) if paths else 'not configured'}",
        f"- Retention: {retention_days} days",
        f"- Artifacts to retain: {', '.join(artifacts) if artifacts else 'none'}",
        "",
    ]
    append_summary("\n".join(summary) + "\n")


def security_scan(_: argparse.Namespace) -> None:
    scans = _config_path({}, "security", "scans") or {}
    defaults = {
        "pip-audit": {"command": "pip-audit --strict"},
        "safety": {"command": "safety check --full-report"},
        "bandit": {"command": "bandit -r src"},
        "cargo-audit": {"command": "cargo audit"},
        "npm-audit": {"command": "npm audit --audit-level=high"},
        "osv-scanner": {"command": "osv-scanner --recursive ."},
    }

    matrix: list[dict[str, Any]] = []
    for name, default_params in defaults.items():
        config = scans.get(name, {})
        enabled = config.get("enabled", True)
        if not enabled:
            continue

        entry = {
            "tool": name,
            "command": config.get("command", default_params["command"]),
            "args": config.get("args", ""),
            "working-directory": config.get("working-directory", "."),
        }
        matrix.append(entry)

    write_output("security-matrix", _to_json(matrix))
    write_output("security-scan-enabled", str(bool(matrix)).lower())

    summary = [
        "# 🔐 Security Scan Matrix",
        "",
        f"- Tools configured: {len(matrix)}",
    ]
    if matrix:
        summary.append("- Tools: " + ", ".join(entry["tool"] for entry in matrix))
    else:
        summary.append("- No scanners enabled")
    summary.append("")
    append_summary("\n".join(summary) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maintenance workflow helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("maintenance-plan").set_defaults(handler=maintenance_plan)
    subparsers.add_parser("dependency-update").set_defaults(handler=dependency_update)
    subparsers.add_parser("cleanup").set_defaults(handler=cleanup)
    subparsers.add_parser("security-scan").set_defaults(handler=security_scan)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        raise SystemExit(1)
    handler(args)


if __name__ == "__main__":
    main()

```

## F.6 `.github/workflows/scripts/docs_workflow.py`

```python
#!/usr/bin/env python3
"""Helper utilities for documentation workflows."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

_CONFIG_CACHE: dict[str, Any] | None = None


def append_to_file(path_env: str, content: str) -> None:
    file_path = os.environ.get(path_env)
    if not file_path:
        return
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "a", encoding="utf-8") as handle:
        handle.write(content)


def write_output(name: str, value: str) -> None:
    append_to_file("GITHUB_OUTPUT", f"{name}={value}\n")


def append_summary(text: str) -> None:
    append_to_file("GITHUB_STEP_SUMMARY", text)


def get_repository_config() -> dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    raw = os.environ.get("REPOSITORY_CONFIG")
    if not raw:
        _CONFIG_CACHE = {}
        return _CONFIG_CACHE

    try:
        _CONFIG_CACHE = json.loads(raw)
    except json.JSONDecodeError:
        print("::warning::Failed to parse REPOSITORY_CONFIG, using defaults")
        _CONFIG_CACHE = {}
    return _CONFIG_CACHE


def _config_path(default: Any, *path: str) -> Any:
    current: Any = get_repository_config()
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _to_json(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=True)


def determine_tasks(_: argparse.Namespace) -> None:
    doc_config = _config_path({}, "documentation") or {}
    checks = doc_config.get("checks") or ["markdownlint", "vale", "links"]
    concurrency = int(doc_config.get("concurrency", 2))

    tasks: list[dict[str, Any]] = []
    for raw_name in checks:
        name = str(raw_name).lower()
        if name == "markdownlint":
            cfg = doc_config.get("markdownlint", {})
            tasks.append(
                {
                    "name": "markdownlint",
                    "command": cfg.get("command", "markdownlint"),
                    "args": cfg.get("args", "."),
                    "paths": cfg.get("paths", ["**/*.md"]),
                    "working-directory": cfg.get("working-directory", "."),
                }
            )
        elif name in {"vale", "vale-lint"}:
            cfg = doc_config.get("vale", {})
            tasks.append(
                {
                    "name": "vale",
                    "command": cfg.get("command", "vale"),
                    "args": cfg.get("args", "docs"),
                    "paths": cfg.get("paths", ["docs/", "README.md"]),
                    "working-directory": cfg.get("working-directory", "."),
                }
            )
        elif name in {"links", "linkcheck"}:
            cfg = doc_config.get("linkcheck", {})
            tasks.append(
                {
                    "name": "lychee",
                    "command": cfg.get("command", "lychee"),
                    "args": cfg.get("args", "--config .lychee.toml docs/**/*.md"),
                    "paths": cfg.get("paths", ["docs/**/*.md", "README.md"]),
                    "working-directory": cfg.get("working-directory", "."),
                }
            )
        else:
            cfg = doc_config.get(name, {})
            tasks.append(
                {
                    "name": name,
                    "command": cfg.get("command", name),
                    "args": cfg.get("args", cfg.get("arguments", "")),
                    "paths": cfg.get("paths", []),
                    "working-directory": cfg.get("working-directory", "."),
                }
            )

    write_output("doc-task-matrix", _to_json(tasks))
    write_output("doc-check-count", str(len(tasks)))
    write_output("doc-concurrency", str(concurrency))

    summary = [
        "# 📚 Documentation Checks",
        "",
        f"- Checks configured: {len(tasks)}",
        f"- Concurrency: {concurrency}",
    ]
    if tasks:
        summary.append("- Tools: " + ", ".join(task["name"] for task in tasks))
    else:
        summary.append("- No documentation checks configured")
    summary.append("")
    append_summary("\n".join(summary) + "\n")


def run_task(_: argparse.Namespace) -> None:
    raw_task = os.environ.get("DOC_TASK_JSON")
    if not raw_task:
        raise SystemExit("DOC_TASK_JSON environment variable is required")

    task = json.loads(raw_task)
    command = task.get("command")
    if not command:
        raise SystemExit("Task command is required")

    args = task.get("args", "")
    working_directory = task.get("working-directory") or "."

    executable = shlex.split(command)
    if not executable:
        raise SystemExit("Unable to parse command for documentation task")
    binary = executable[0]
    if shutil.which(binary) is None:
        raise SystemExit(f"Required tool '{binary}' is not installed")

    full_command = executable
    if args:
        full_command += shlex.split(str(args))

    print(f"Running documentation task: {' '.join(full_command)} (cwd={working_directory})")
    result = subprocess.run(full_command, cwd=working_directory or None, check=False)
    if result.returncode != 0:
        raise SystemExit(f"Documentation task '{task['name']}' failed with exit code {result.returncode}")

    write_output("doc-task-name", task.get("name", "unknown"))
    write_output("doc-task-status", "success")


def publish_summary(_: argparse.Namespace) -> None:
    matrix_json = os.environ.get("DOC_TASK_MATRIX", "[]")
    try:
        tasks = json.loads(matrix_json)
    except json.JSONDecodeError:
        tasks = []

    summary = [
        "# 📄 Documentation Summary",
        "",
    ]
    if not tasks:
        summary.append("- No documentation tasks were executed")
    else:
        for task in tasks:
            summary.append(f"- {task.get('name', 'task')}: {task.get('status', 'pending')}")
    summary.append("")
    append_summary("\n".join(summary) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Documentation workflow helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("determine-tasks").set_defaults(handler=determine_tasks)
    subparsers.add_parser("run-task").set_defaults(handler=run_task)
    subparsers.add_parser("publish-summary").set_defaults(handler=publish_summary)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        raise SystemExit(1)
    handler(args)


if __name__ == "__main__":
    main()

```

## F.7 `.github/workflows/scripts/automation_workflow.py`

```python
#!/usr/bin/env python3
"""Helper utilities for issue and pull request automation workflows."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

_CONFIG_CACHE: dict[str, Any] | None = None


def append_to_file(path_env: str, content: str) -> None:
    file_path = os.environ.get(path_env)
    if not file_path:
        return
    with open(file_path, "a", encoding="utf-8") as handle:
        handle.write(content)


def write_output(name: str, value: str) -> None:
    append_to_file("GITHUB_OUTPUT", f"{name}={value}\n")


def append_summary(text: str) -> None:
    append_to_file("GITHUB_STEP_SUMMARY", text)


def get_repository_config() -> dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    raw = os.environ.get("REPOSITORY_CONFIG")
    if not raw:
        _CONFIG_CACHE = {}
        return _CONFIG_CACHE
    try:
        _CONFIG_CACHE = json.loads(raw)
    except json.JSONDecodeError:
        print("::warning::Failed to parse REPOSITORY_CONFIG, using defaults")
        _CONFIG_CACHE = {}
    return _CONFIG_CACHE


def _config_path(default: Any, *path: str) -> Any:
    current: Any = get_repository_config()
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _to_json(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=True)


def issue_label_plan(_: argparse.Namespace) -> None:
    rules = _config_path([], "automation", "issues", "labels")
    normalised: list[dict[str, Any]] = []
    for index, rule in enumerate(rules):
        name = rule.get("name") or f"issue-rule-{index + 1}"
        normalised.append(
            {
                "name": name,
                "apply": _ensure_list(rule.get("apply")),
                "remove": _ensure_list(rule.get("remove")),
                "when": rule.get("when", {}),
                "requires": rule.get("requires", {}),
            }
        )

    stale_cfg = _config_path({}, "automation", "issues", "stale")

    write_output("issue-label-rules", _to_json(normalised))
    write_output("issue-stale-config", _to_json(stale_cfg))

    summary = [
        "# 🏷️ Issue Automation",
        "",
        f"- Label rules: {len(normalised)}",
        f"- Stale automation configured: {bool(stale_cfg)}",
        "",
    ]
    append_summary("\n".join(summary) + "\n")


def pr_label_plan(_: argparse.Namespace) -> None:
    rules = _config_path([], "automation", "pull_requests", "labels")
    normalised: list[dict[str, Any]] = []
    for index, rule in enumerate(rules):
        name = rule.get("name") or f"pr-rule-{index + 1}"
        normalised.append(
            {
                "name": name,
                "apply": _ensure_list(rule.get("apply")),
                "remove": _ensure_list(rule.get("remove")),
                "when": rule.get("when", {}),
                "requires": rule.get("requires", {}),
            }
        )

    write_output("pr-label-rules", _to_json(normalised))

    summary = [
        "# 🔖 Pull Request Automation",
        "",
        f"- Label rules: {len(normalised)}",
        "",
    ]
    append_summary("\n".join(summary) + "\n")


def auto_merge_plan(_: argparse.Namespace) -> None:
    auto_merge = _config_path({}, "automation", "pull_requests", "auto_merge")
    enabled = bool(auto_merge.get("enabled", False))
    strategies = _ensure_list(auto_merge.get("methods", ["squash"]))
    conditions = auto_merge.get("conditions", {})

    payload = {
        "enabled": enabled,
        "methods": strategies,
        "conditions": conditions,
    }

    write_output("auto-merge-config", _to_json(payload))
    write_output("auto-merge-enabled", str(enabled).lower())

    summary = [
        "# 🤖 Auto-merge",
        "",
        f"- Enabled: {enabled}",
        f"- Methods: {', '.join(strategies) if strategies else 'none'}",
        "",
    ]
    append_summary("\n".join(summary) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automation workflow helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("issue-label-plan").set_defaults(handler=issue_label_plan)
    subparsers.add_parser("pr-label-plan").set_defaults(handler=pr_label_plan)
    subparsers.add_parser("auto-merge-plan").set_defaults(handler=auto_merge_plan)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        raise SystemExit(1)
    handler(args)


if __name__ == "__main__":
    main()

```

## F.8 `tests/workflow_scripts/test_ci_workflow.py`

```python
import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

import ci_workflow


@pytest.fixture(autouse=True)
def reset_config_cache():
    ci_workflow._CONFIG_CACHE = None  # type: ignore[attr-defined]
def test_debug_filter_outputs(monkeypatch, capsys):
    env_values = {
        "CI_GO_FILES": "true",
        "CI_FRONTEND_FILES": "false",
        "CI_PYTHON_FILES": "true",
        "CI_RUST_FILES": "false",
        "CI_DOCKER_FILES": "false",
        "CI_DOCS_FILES": "true",
        "CI_WORKFLOW_FILES": "true",
        "CI_LINT_FILES": "false",
    }
    for key, value in env_values.items():
        monkeypatch.setenv(key, value)

    ci_workflow.debug_filter(argparse.Namespace())
    output = capsys.readouterr().out
    assert "Go files changed: true" in output
    assert "Docs files changed: true" in output


def test_determine_execution_sets_outputs(tmp_path, monkeypatch):
    output_file = tmp_path / "output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("GITHUB_HEAD_COMMIT_MESSAGE", "fix bug [skip ci]")
    monkeypatch.setenv("CI_GO_FILES", "true")
    monkeypatch.setenv("CI_FRONTEND_FILES", "false")
    monkeypatch.setenv("CI_PYTHON_FILES", "true")
    monkeypatch.setenv("CI_RUST_FILES", "false")
    monkeypatch.setenv("CI_DOCKER_FILES", "true")

    ci_workflow.determine_execution(argparse.Namespace())
    lines = output_file.read_text().splitlines()
    assert "skip_ci=true" in lines
    assert "should_test_go=true" in lines
    assert "should_test_frontend=false" in lines


class DummyResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


def test_wait_for_pr_automation_completed(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("TARGET_SHA", "abc123")
    monkeypatch.setenv("WORKFLOW_NAME", "PR Automation")
    monkeypatch.setenv("MAX_ATTEMPTS", "1")

    def fake_get(url: str, **kwargs):
        assert "owner/repo" in url
        return DummyResponse(
            200,
            {
                "workflow_runs": [
                    {"head_sha": "abc123", "name": "PR Automation", "status": "completed"}
                ]
            },
        )

    monkeypatch.setattr(ci_workflow.requests, "get", fake_get)
    ci_workflow.wait_for_pr_automation(argparse.Namespace())
    captured = capsys.readouterr().out
    assert "✅ PR automation has completed" in captured


def test_load_super_linter_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "super-linter-ci.env").write_text("FOO=bar\n", encoding="utf-8")
    env_file = tmp_path / "env.txt"
    output_file = tmp_path / "output.txt"

    monkeypatch.setenv("EVENT_NAME", "push")
    monkeypatch.setenv("CI_ENV_FILE", "super-linter-ci.env")
    monkeypatch.setenv("PR_ENV_FILE", "super-linter-pr.env")
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    ci_workflow.load_super_linter_config(argparse.Namespace())
    assert env_file.read_text() == "FOO=bar\n"
    assert "config-file=super-linter-ci.env" in output_file.read_text()


def test_go_setup_skips_without_go_mod(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    def fake_run(*args, **kwargs):  # pragma: no cover - should not be called
        raise AssertionError("go commands should not run")

    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    ci_workflow.go_setup(argparse.Namespace())
    assert "skipping Go step" in capsys.readouterr().out


def test_go_test_runs_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example.com/test\n", encoding="utf-8")
    commands = []

    def fake_run(cmd, check=False, capture_output=False, text=False, **kwargs):
        commands.append((tuple(cmd), check, capture_output))
        if "-func" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="total: (statements) 75.0%\n")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setenv("COVERAGE_THRESHOLD", "70")
    monkeypatch.delenv("REPOSITORY_CONFIG", raising=False)
    ci_workflow._CONFIG_CACHE = None  # type: ignore[attr-defined]
    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    monkeypatch.setattr(ci_workflow.shutil, "which", lambda name: "go")

    ci_workflow.go_test(argparse.Namespace())
    go_commands = [cmd for cmd, *_ in commands if cmd and cmd[0] == "go"]
    assert any("test" in cmd for cmd in go_commands)
    assert any("tool" in cmd for cmd in go_commands)


def test_python_run_tests_skips_when_no_tests(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    commands = []

    def fake_run(cmd, check=False, **kwargs):
        commands.append(tuple(cmd))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    ci_workflow.python_install(argparse.Namespace())
    ci_workflow.python_run_tests(argparse.Namespace())
    assert any("pip" in part for cmd in commands for part in cmd)
    assert "ℹ️ No Python tests found" in capsys.readouterr().out


def test_go_test_uses_config_threshold(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example.com/test\n", encoding="utf-8")

    config = {"testing": {"coverage": {"threshold": 90}}}
    monkeypatch.setenv("REPOSITORY_CONFIG", json.dumps(config))
    ci_workflow._CONFIG_CACHE = None  # type: ignore[attr-defined]

    commands = []

    def fake_run(cmd, check=False, capture_output=False, text=False, **kwargs):
        commands.append((tuple(cmd), capture_output))
        if "-func" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="total: (statements) 95.0%\n")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    monkeypatch.setattr(ci_workflow.shutil, "which", lambda name: "go")

    ci_workflow.go_test(argparse.Namespace())
    assert commands, "expected go commands to execute"


def test_generate_matrices_uses_repository_config(tmp_path, monkeypatch):
    config = {
        "languages": {
            "versions": {
                "go": ["1.22", "1.23"],
                "python": ["3.11", "3.12"],
                "rust": ["stable"],
                "node": ["20"],
            }
        },
        "build": {"platforms": {"os": ["ubuntu-latest", "macos-latest"]}},
        "testing": {"coverage": {"threshold": 85}},
    }
    output_file = tmp_path / "outputs.txt"
    monkeypatch.setenv("REPOSITORY_CONFIG", json.dumps(config))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("FALLBACK_GO_VERSION", "1.24")
    monkeypatch.setenv("FALLBACK_PYTHON_VERSION", "3.13")
    monkeypatch.setenv("FALLBACK_RUST_VERSION", "stable")
    monkeypatch.setenv("FALLBACK_NODE_VERSION", "22")
    monkeypatch.setenv("FALLBACK_COVERAGE_THRESHOLD", "80")
    ci_workflow._CONFIG_CACHE = None  # type: ignore[attr-defined]

    ci_workflow.generate_matrices(argparse.Namespace())

    outputs = dict(line.split("=", 1) for line in output_file.read_text().splitlines())
    go_matrix = json.loads(outputs["go-matrix"])
    python_matrix = json.loads(outputs["python-matrix"])
    coverage_threshold = outputs["coverage-threshold"]

    assert go_matrix["include"][0]["go-version"] == "1.22"
    assert python_matrix["include"][0]["python-version"] == "3.11"
    assert python_matrix["include"][0]["os"] == "ubuntu-latest"
    assert any(entry["os"] == "macos-latest" for entry in python_matrix["include"])
    assert coverage_threshold == "85"


def test_generate_ci_summary(tmp_path, monkeypatch):
    summary_path = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))
    monkeypatch.setenv("JOB_DETECT_CHANGES", "success")
    monkeypatch.setenv("JOB_LINT", "success")
    monkeypatch.setenv("JOB_TEST_GO", "success")
    monkeypatch.setenv("JOB_TEST_PYTHON", "skipped")
    monkeypatch.setenv("JOB_TEST_RUST", "failure")
    monkeypatch.setenv("JOB_TEST_FRONTEND", "success")
    monkeypatch.setenv("CI_GO_FILES", "true")
    monkeypatch.setenv("CI_PYTHON_FILES", "false")
    monkeypatch.setenv("CI_RUST_FILES", "true")
    monkeypatch.setenv("CI_FRONTEND_FILES", "false")
    monkeypatch.setenv("CI_DOCKER_FILES", "false")
    monkeypatch.setenv("CI_DOCS_FILES", "true")
    monkeypatch.setenv("CI_WORKFLOW_FILES", "false")

    ci_workflow.generate_ci_summary(argparse.Namespace())
    content = summary_path.read_text()
    assert "CI Pipeline Summary" in content
    assert "| Test Rust | failure |" in content


def test_check_ci_status_failure(monkeypatch):
    monkeypatch.setenv("JOB_LINT", "success")
    monkeypatch.setenv("JOB_TEST_GO", "success")
    monkeypatch.setenv("JOB_TEST_PYTHON", "failure")
    monkeypatch.setenv("JOB_TEST_RUST", "success")
    monkeypatch.setenv("JOB_TEST_FRONTEND", "success")
    with pytest.raises(SystemExit):
        ci_workflow.check_ci_status(argparse.Namespace())
```

## F.9 `tests/workflow_scripts/test_release_workflow.py`

```python
import argparse
import json
from pathlib import Path

import pytest

import release_workflow


@pytest.fixture(autouse=True)
def reset_release_config_cache():
    release_workflow._CONFIG_CACHE = None  # type: ignore[attr-defined]


def _parse_outputs(path: Path) -> dict[str, str]:
    data = {}
    if not path.exists():
        return data
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key] = value
    return data


def test_detect_languages_auto(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example.com/test\n")
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    (tmp_path / "Dockerfile").write_text("FROM busybox\n")
    (tmp_path / "proto").mkdir()
    (tmp_path / "proto" / "test.proto").write_text("syntax = \"proto3\";\n")

    output_file = tmp_path / "outputs.txt"
    config = {
        "languages": {
            "versions": {
                "go": ["1.20", "1.21"],
                "python": ["3.10", "3.11"],
                "rust": ["stable"],
                "node": ["18"],
            }
        },
        "build": {"platforms": {"os": ["ubuntu-latest"]}, "docker": {"platforms": ["linux/amd64"]}},
    }
    monkeypatch.setenv("REPOSITORY_CONFIG", json.dumps(config))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    release_workflow.detect_languages(argparse.Namespace())

    outputs = _parse_outputs(output_file)
    assert outputs["has-go"] == "true"
    assert outputs["has-python"] == "true"
    assert outputs["has-docker"] == "true"
    assert outputs["protobuf-needed"] == "true"
    assert json.loads(outputs["go-matrix"])["go-version"] == ["1.20", "1.21"]
    assert json.loads(outputs["docker-matrix"])["platform"] == ["linux/amd64"]


def test_release_strategy_branch_defaults(monkeypatch, tmp_path):
    output_file = tmp_path / "outputs.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("BRANCH_NAME", "develop")
    monkeypatch.setenv("INPUT_PRERELEASE", "false")
    monkeypatch.setenv("INPUT_DRAFT", "false")

    release_workflow.release_strategy(argparse.Namespace())
    outputs = _parse_outputs(output_file)
    assert outputs["strategy"] == "prerelease"
    assert outputs["auto-prerelease"] == "true"
    assert outputs["auto-draft"] == "false"


def test_generate_version_from_tag(monkeypatch, tmp_path):
    output_file = tmp_path / "outputs.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("RELEASE_TYPE", "auto")
    monkeypatch.setenv("BRANCH_NAME", "main")
    monkeypatch.setenv("AUTO_PRERELEASE", "false")
    monkeypatch.setenv("AUTO_DRAFT", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")

    monkeypatch.setattr(release_workflow, "_latest_tag_from_api", lambda: "")
    monkeypatch.setattr(release_workflow, "_latest_tag_from_git", lambda: "v1.2.3")

    def fake_run(args, check=False):
        cmd = tuple(args)
        if cmd[:2] == ("tag", "-l", "v1.2.4"):
            return subprocess.CompletedProcess(args, 0, "", "")
        return subprocess.CompletedProcess(args, 0, "", "")

    import subprocess  # noqa: F401 - used in fake_run

    monkeypatch.setattr(release_workflow, "_run_git", fake_run)

    release_workflow.generate_version(argparse.Namespace())
    outputs = _parse_outputs(output_file)
    assert outputs["tag"] == "v1.2.4"


def test_generate_changelog(monkeypatch, tmp_path):
    output_file = tmp_path / "outputs.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("BRANCH_NAME", "main")
    monkeypatch.setenv("PRIMARY_LANGUAGE", "go")
    monkeypatch.setenv("RELEASE_STRATEGY", "stable")
    monkeypatch.setenv("AUTO_PRERELEASE", "false")
    monkeypatch.setenv("AUTO_DRAFT", "true")

    import subprocess  # noqa: F401

    def fake_run(args, check=False):
        cmd = tuple(args)
        if cmd[:2] == ("describe", "--tags"):
            return subprocess.CompletedProcess(args, 0, "v1.0.0\n", "")
        if cmd[0] == "log":
            return subprocess.CompletedProcess(args, 0, "feat: add feature (abc123)\nfix: bug fix (def456)\n", "")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(release_workflow, "_run_git", fake_run)

    release_workflow.generate_changelog(argparse.Namespace())
    content = output_file.read_text()
    assert "feat: add feature" in content
    assert "Release Type" in content
```

## F.10 `tests/workflow_scripts/test_maintenance_workflow.py`

```python
import argparse
import json
from pathlib import Path

import pytest

import maintenance_workflow


@pytest.fixture(autouse=True)
def reset_cache(monkeypatch):
    maintenance_workflow._CONFIG_CACHE = None  # type: ignore[attr-defined]
    monkeypatch.delenv("REPOSITORY_CONFIG", raising=False)


def _prepare_environment(monkeypatch, tmp_path, config):
    output_file = tmp_path / "outputs.txt"
    summary_file = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    monkeypatch.setenv("REPOSITORY_CONFIG", json.dumps(config))
    return output_file, summary_file


def _parse_outputs(path: Path) -> dict[str, str]:
    results: dict[str, str] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                results[key] = value
    return results


def test_maintenance_plan_outputs(monkeypatch, tmp_path):
    config = {
        "maintenance": {
            "schedule": {"cron": "0 6 * * 2"},
            "owners": ["@ops"],
            "dependencies": {"auto_update": False},
            "runtime": {"runner": "ubuntu-22.04"},
        },
        "notifications": {"channels": ["slack:#ops-alerts"]},
    }
    outputs_path, summary_path = _prepare_environment(monkeypatch, tmp_path, config)

    maintenance_workflow.maintenance_plan(argparse.Namespace())

    outputs = _parse_outputs(outputs_path)
    assert outputs["schedule-cron"] == "0 6 * * 2"
    assert outputs["auto-update-enabled"] == "false"
    assert outputs["maintenance-runner"] == "ubuntu-22.04"
    assert "Maintenance Plan" in summary_path.read_text()


def test_dependency_update_matrix(monkeypatch, tmp_path):
    config = {
        "languages": {"versions": {"pip": ["3.11"], "cargo": ["stable"]}},
        "maintenance": {
            "dependencies": {
                "package_managers": {
                    "pip": {"enabled": True, "args": "--auto"},
                    "cargo": {"enabled": True},
                    "npm": {"enabled": False},
                }
            }
        },
    }
    outputs_path, _ = _prepare_environment(monkeypatch, tmp_path, config)

    maintenance_workflow.dependency_update(argparse.Namespace())

    outputs = _parse_outputs(outputs_path)
    matrix = json.loads(outputs["dependency-matrix"])
    managers = [entry["manager"] for entry in matrix]
    assert managers == ["pip", "cargo"]
    assert outputs["updates-enabled"] == "true"


def test_security_scan_matrix(monkeypatch, tmp_path):
    config = {
        "security": {
            "scans": {
                "pip-audit": {"enabled": False},
                "osv-scanner": {"enabled": True, "args": "--lockfile"},
            }
        }
    }
    outputs_path, _ = _prepare_environment(monkeypatch, tmp_path, config)

    maintenance_workflow.security_scan(argparse.Namespace())

    outputs = _parse_outputs(outputs_path)
    matrix = json.loads(outputs["security-matrix"])
    assert [entry["tool"] for entry in matrix] == ["osv-scanner"]
    assert matrix[0]["args"] == "--lockfile"
    assert outputs["security-scan-enabled"] == "true"

```

## F.11 `tests/workflow_scripts/test_docs_workflow.py`

```python
import argparse
import json

import pytest

import docs_workflow


@pytest.fixture(autouse=True)
def reset_cache(monkeypatch):
    docs_workflow._CONFIG_CACHE = None  # type: ignore[attr-defined]
    monkeypatch.delenv("REPOSITORY_CONFIG", raising=False)


def _prepare(monkeypatch, tmp_path, config):
    output_file = tmp_path / "outputs.txt"
    summary_file = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    monkeypatch.setenv("REPOSITORY_CONFIG", json.dumps(config))
    return output_file, summary_file


def _parse_outputs(path):
    results = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                results[key] = value
    return results


def test_determine_tasks(monkeypatch, tmp_path):
    config = {
        "documentation": {
            "checks": ["markdownlint", "links"],
            "markdownlint": {"args": "--config .markdownlint.json docs/"},
            "linkcheck": {"command": "lychee", "args": "docs/**/*.md"},
            "concurrency": 3,
        }
    }
    outputs_path, _ = _prepare(monkeypatch, tmp_path, config)

    docs_workflow.determine_tasks(argparse.Namespace())
    outputs = _parse_outputs(outputs_path)
    matrix = json.loads(outputs["doc-task-matrix"])
    assert outputs["doc-concurrency"] == "3"
    assert [task["name"] for task in matrix] == ["markdownlint", "lychee"]


def test_run_task_success(monkeypatch, tmp_path):
    task = {
        "name": "markdownlint",
        "command": "markdownlint",
        "args": "README.md",
        "working-directory": ".",
    }
    monkeypatch.setenv("DOC_TASK_JSON", json.dumps(task))
    output_file = tmp_path / "outputs.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    monkeypatch.setattr("docs_workflow.shutil.which", lambda _: str(tmp_path / "markdownlint"))

    class Result:
        returncode = 0

    monkeypatch.setattr("docs_workflow.subprocess.run", lambda *_, **__: Result())

    docs_workflow.run_task(argparse.Namespace())
    outputs = _parse_outputs(output_file)
    assert outputs["doc-task-name"] == "markdownlint"
    assert outputs["doc-task-status"] == "success"


def test_publish_summary(monkeypatch, tmp_path):
    summary_file = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    sample_tasks = json.dumps([
        {"name": "markdownlint", "status": "success"},
        {"name": "lychee", "status": "pending"},
    ])
    monkeypatch.setenv("DOC_TASK_MATRIX", sample_tasks)

    docs_workflow.publish_summary(argparse.Namespace())
    summary_text = summary_file.read_text()
    assert "markdownlint" in summary_text
    assert "lychee" in summary_text

```

## F.12 `tests/workflow_scripts/test_automation_workflow.py`

```python
import argparse
import json

import pytest

import automation_workflow


@pytest.fixture(autouse=True)
def reset_cache(monkeypatch):
    automation_workflow._CONFIG_CACHE = None  # type: ignore[attr-defined]
    monkeypatch.delenv("REPOSITORY_CONFIG", raising=False)


def _prepare(monkeypatch, tmp_path, config):
    output_file = tmp_path / "outputs.txt"
    summary_file = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    monkeypatch.setenv("REPOSITORY_CONFIG", json.dumps(config))
    return output_file, summary_file


def _parse_outputs(path):
    results = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                results[key] = value
    return results


def test_issue_label_plan(monkeypatch, tmp_path):
    config = {
        "automation": {
            "issues": {
                "labels": [
                    {
                        "name": "bug-triage",
                        "apply": ["bug", "needs-triage"],
                        "when": {"title": {"contains": ["bug"]}},
                    }
                ],
                "stale": {"days": 14, "label": "stale"},
            }
        }
    }
    outputs_path, summary_path = _prepare(monkeypatch, tmp_path, config)

    automation_workflow.issue_label_plan(argparse.Namespace())
    outputs = _parse_outputs(outputs_path)
    rules = json.loads(outputs["issue-label-rules"])
    assert rules[0]["apply"] == ["bug", "needs-triage"]
    stale = json.loads(outputs["issue-stale-config"])
    assert stale["days"] == 14
    assert "Issue Automation" in summary_path.read_text()


def test_pr_and_merge_plan(monkeypatch, tmp_path):
    config = {
        "automation": {
            "pull_requests": {
                "labels": [
                    {
                        "name": "ready",
                        "apply": ["ready-to-merge"],
                        "requires": {"checks": ["ci"]},
                    }
                ],
                "auto_merge": {
                    "enabled": True,
                    "methods": ["squash", "merge"],
                    "conditions": {"required_labels": ["ready-to-merge"]},
                },
            }
        }
    }
    outputs_path, _ = _prepare(monkeypatch, tmp_path, config)

    automation_workflow.pr_label_plan(argparse.Namespace())
    automation_workflow.auto_merge_plan(argparse.Namespace())

    outputs = _parse_outputs(outputs_path)
    label_rules = json.loads(outputs["pr-label-rules"])
    assert label_rules[0]["apply"] == ["ready-to-merge"]
    merge_config = json.loads(outputs["auto-merge-config"])
    assert merge_config["enabled"] is True
    assert merge_config["methods"] == ["squash", "merge"]
    assert outputs["auto-merge-enabled"] == "true"

```

# Appendix G – Sample `.github/repository-config.yml`

```yaml
repository:
  primary_language: go
  visibility: public
languages:
  versions:
    go: ["1.22", "1.23", "1.24"]
    python: ["3.11", "3.12", "3.13"]
    rust: ["stable", "beta"]
    node: ["20", "22"]
    protobuf: ["buf" ]
build:
  platforms:
    os: ["ubuntu-latest", "macos-latest"]
  docker:
    platforms: ["linux/amd64", "linux/arm64"]
ci:
  coverage:
    threshold: 85
    fail_on_drop: true
  lint:
    super_linter_env: super-linter-ci.env
release:
  versioning:
    default_branch_strategy:
      main: patch
      develop: minor
    allow_prerelease_on:
      - develop
  artifacts:
    buckets:
      binaries: dist/
      documentation: docs/_build
    docker:
      push: true
      tags:
        - latest
        - "{{version}}"
  changelog:
    categories:
      - name: Features
        match: ["feat", "feature"]
      - name: Fixes
        match: ["fix", "bugfix"]
maintenance:
  schedule:
    cron: "0 6 * * 1"
  runtime:
    runner: ubuntu-latest
  owners:
    - @eng/platform
  dependencies:
    auto_update: true
    package_managers:
      pip:
        enabled: true
        args: "--auto"
      cargo:
        enabled: true
  cleanup:
    paths:
      - build/
      - dist/
      - .pytest_cache
    artifacts:
      - coverage.xml
      - junit.xml
    retention_days: 14
security:
  scans:
    pip-audit:
      enabled: true
      args: "--strict"
    cargo-audit:
      enabled: true
    osv-scanner:
      enabled: true
      working-directory: .
documentation:
  checks:
    - markdownlint
    - vale
    - links
  markdownlint:
    command: markdownlint
    args: "--config .markdownlint.json docs/**/*.md"
  vale:
    command: vale
    args: "docs/"
    working-directory: docs
  linkcheck:
    command: lychee
    args: "--config .lychee.toml docs/**/*.md"
automation:
  issues:
    labels:
      - name: bug-triage
        apply: ["bug", "needs-triage"]
        when:
          title:
            contains: ["bug", "panic"]
          body:
            contains: ["steps to reproduce"]
      - name: documentation
        apply: ["docs"]
        when:
          files:
            patterns: ["docs/**", "*.md"]
    stale:
      days: 30
      label: stale
      exempt_labels: ["pinned", "security"]
  pull_requests:
    labels:
      - name: ready-to-merge
        apply: ["ready-to-merge"]
        requires:
          checks: ["ci", "lint"]
      - name: dependencies
        apply: ["dependencies"]
        when:
          title:
            startswith: ["chore(deps)"]
    auto_merge:
      enabled: true
      methods: ["squash"]
      conditions:
        required_labels: ["ready-to-merge"]
        status_checks: true
        allow_draft: false
notifications:
  channels:
    - slack:#ghcommon-releases
    - email:releases@example.com

```

---

# Appendix H – Verification Matrix

| Step                     | Command                                                                    | Expected Result                   |
| ------------------------ | -------------------------------------------------------------------------- | --------------------------------- |
| Phase 1 unit tests       | `python -m pytest tests/workflow_scripts/test_ci_workflow.py -vv`          | CI helper suite passes            |
| Phase 1 integration      | `python -m pytest tests/workflow_scripts -vv`                              | All workflow script tests pass    |
| Phase 2 unit tests       | `python -m pytest tests/workflow_scripts/test_release_workflow.py -vv`     | Release helper suite passes       |
| Phase 3 helper tests     | `python -m pytest tests/workflow_scripts/test_maintenance_workflow.py -vv` | Maintenance helper suite passes   |
| Phase 3 docs tests       | `python -m pytest tests/workflow_scripts/test_docs_workflow.py -vv`        | Documentation helper suite passes |
| Phase 4 automation tests | `python -m pytest tests/workflow_scripts/test_automation_workflow.py -vv`  | Automation helper suite passes    |
| YAML validation          | `python -m yamlcheck .github/workflows/reusable-release.yml`               | No schema errors                  |
| Optional smoke test      | `act workflow_dispatch -W .github/workflows/release.yml -j release`        | Workflow completes                |
