<!-- file: WORKFLOW_SCRIPT_AUDIT.md -->
<!-- version: 1.0.0 -->
<!-- guid: 1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d -->
<!-- last-edited: 2026-01-19 -->

# Workflow Scripts to Actions Conversion Audit

**Date:** December 20, 2025 **Purpose:** Comprehensive audit of workflow scripts
for conversion to GitHub Actions **Status:** Phase 1 - Full Audit Complete

## Executive Summary

This repository currently has **38 Python/Shell scripts** (6,232 total lines)
embedded in `.github/workflows/scripts/` that are referenced by reusable
workflows. These scripts fail when called from other repositories because:

1. Scripts are fetched via sparse checkout during workflow execution
2. External repos can't resolve the `$GHCOMMON_SCRIPTS_DIR` path properly
3. Scripts have inter-dependencies that break when paths are misconfigured

**Solution:** Convert scripts to **standalone GitHub Actions** following the
pattern established by the existing 6 release actions (release-go-action,
release-docker-action, etc.).

---

## Existing Actions (Reference Pattern)

These actions are in **separate repositories** and serve as the conversion
template:

| Action Repository                | Purpose                  | Key Pattern                                |
| -------------------------------- | ------------------------ | ------------------------------------------ |
| `jdfalk/release-go-action`       | Release Go modules       | Composite action with embedded Python/Bash |
| `jdfalk/release-docker-action`   | Build/push Docker images | Uses docker/\* actions + custom logic      |
| `jdfalk/release-python-action`   | Release Python packages  | PyPI publishing + artifact management      |
| `jdfalk/release-rust-action`     | Release Rust crates      | Cargo publish + cross-compilation          |
| `jdfalk/release-frontend-action` | Build frontend assets    | Node.js builds + npm/yarn                  |
| `jdfalk/release-protobuf-action` | Generate protobufs       | Buf + multi-language generation            |

### Common Action Pattern

```yaml
name: 'Action Name'
description: 'Brief description'
author: 'jdfalk'
branding:
  icon: 'icon-name'
  color: 'blue'

inputs:
  # Parameterized inputs
outputs:
  # Generated outputs

runs:
  using: 'composite'
  steps:
    - name: Step 1
      shell: bash
      run: |
        # Inline script logic OR
        # Call to another action
```

---

## Script Inventory & Prioritization

### Priority 1: Critical Infrastructure Scripts (Blocking Issues)

These scripts are called by **ALL** reusable workflows and cause immediate
failures:

| Script                      | Lines | Used By                  | Purpose                               | Complexity |
| --------------------------- | ----- | ------------------------ | ------------------------------------- | ---------- |
| `load_repository_config.py` | 43    | All reusable workflows   | Load `.github/repository-config.yml`  | **LOW**    |
| `workflow_common.py`        | 145   | 15+ scripts (dependency) | Shared utilities (outputs, summaries) | **LOW**    |

**Action Conversions Needed:**

- `jdfalk/load-config-action` - Standalone config loader
- `jdfalk/workflow-common-action` - Shared utility library (or embed in each
  action)

---

### Priority 2: CI Workflow Scripts (High Usage)

These scripts power the `reusable-ci.yml` workflow used by all repositories:

| Script                | Lines                     | Called By         | Purpose                                          | Complexity |
| --------------------- | ------------------------- | ----------------- | ------------------------------------------------ | ---------- |
| `ci_workflow.py`      | 867                       | `reusable-ci.yml` | Generate matrices, run linters, collect coverage | **HIGH**   |
| `detect_languages.py` | (embedded in ci_workflow) | CI job            | Detect project languages                         | **MEDIUM** |

**Workflow Calls:**

```bash
python3 "$GHCOMMON_SCRIPTS_DIR/ci_workflow.py" generate-matrices
python3 "$GHCOMMON_SCRIPTS_DIR/ci_workflow.py" detect-changes
python3 "$GHCOMMON_SCRIPTS_DIR/ci_workflow.py" run-linters
```

**Action Conversions Needed:**

- `jdfalk/ci-generate-matrices-action` - Language detection + matrix generation
- `jdfalk/ci-detect-changes-action` - File change detection (or use
  dorny/paths-filter)
- `jdfalk/ci-run-linters-action` - Coordinated linter execution

**Dependencies:**

- `workflow_common.py` (outputs, summaries)
- `load_repository_config.py` (config access)

---

### Priority 3: Release Workflow Scripts (High Usage)

These scripts power the `reusable-release.yml` workflow:

| Script                      | Lines      | Called By              | Purpose                                                  | Complexity |
| --------------------------- | ---------- | ---------------------- | -------------------------------------------------------- | ---------- |
| `release_workflow.py`       | 425        | `reusable-release.yml` | Language detection, release strategy, version generation | **MEDIUM** |
| `generate-version.sh`       | 182        | `release_workflow.py`  | Semantic version generation                              | **MEDIUM** |
| `release-strategy.sh`       | (embedded) | `release_workflow.py`  | Branch-based release strategy                            | **LOW**    |
| `generate-changelog.sh`     | (embedded) | `release_workflow.py`  | Generate release notes                                   | **LOW**    |
| `package_release_assets.py` | 135        | Release finalization   | Package artifacts for GitHub release                     | **MEDIUM** |

**Workflow Calls:**

```bash
python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" detect-languages
python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" release-strategy
python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" generate-version
python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" generate-changelog
```

**Action Conversions Needed:**

- `jdfalk/detect-languages-action` - Detect Go/Python/Rust/Frontend/Docker
- `jdfalk/release-strategy-action` - Determine stable/prerelease/draft
- `jdfalk/generate-version-action` - Semantic versioning logic
- `jdfalk/package-assets-action` - Artifact bundling

**Dependencies:**

- `workflow_common.py`
- `load_repository_config.py`

---

### Priority 4: Language-Specific Build Scripts (Moderate Usage)

| Script                           | Lines   | Called By              | Purpose                          | Complexity  |
| -------------------------------- | ------- | ---------------------- | -------------------------------- | ----------- |
| `build_go_release.py`            | 308     | `release-go.yml`       | Go module builds (now in action) | **✅ DONE** |
| `detect_python_package.py`       | 113     | `release-python.yml`   | Detect Python package metadata   | **MEDIUM**  |
| `run_python_release_tests.py`    | (small) | `release-python.yml`   | Pre-release Python testing       | **LOW**     |
| `collect_rust_crate_metadata.py` | 85      | `release-rust.yml`     | Extract Rust crate metadata      | **LOW**     |
| `detect_frontend_package.py`     | (small) | `release-frontend.yml` | Detect Node.js package metadata  | **LOW**     |
| `get_frontend_working_dir.py`    | (small) | `release-frontend.yml` | Find frontend build directory    | **LOW**     |

**Status:** Most of this logic is **already embedded** in the separate
release-\*-action repositories. However, some scripts are still referenced:

**Action Conversions Needed:**

- `jdfalk/detect-package-metadata-action` - Generic package metadata detection
  (all languages)

---

### Priority 5: Protobuf Scripts (Specialized)

| Script                              | Lines   | Called By               | Purpose                    | Complexity |
| ----------------------------------- | ------- | ----------------------- | -------------------------- | ---------- |
| `parse_protobuf_config.py`          | 92      | `reusable-protobuf.yml` | Parse buf.yaml config      | **LOW**    |
| `check_protobuf_artifacts.py`       | (small) | `reusable-protobuf.yml` | Verify generated artifacts | **LOW**    |
| `verify_python_protobuf_plugins.py` | (small) | Python protobuf builds  | Check protoc plugins       | **LOW**    |

**Action Conversions Needed:**

- `jdfalk/protobuf-config-action` - Parse and validate buf.yaml
- `jdfalk/protobuf-verify-action` - Verify generated code

---

### Priority 6: Docker/Container Scripts

| Script                          | Lines   | Called By                  | Purpose                   | Complexity |
| ------------------------------- | ------- | -------------------------- | ------------------------- | ---------- |
| `detect_docker_config.py`       | (small) | `reusable-release.yml`     | Find Dockerfiles          | **LOW**    |
| `determine_docker_platforms.py` | 111     | `release-docker.yml`       | Determine build platforms | **LOW**    |
| `validate_docker_compose.py`    | (small) | `reusable-maintenance.yml` | Validate compose files    | **LOW**    |

**Status:** Most logic is in `release-docker-action`, but some detection logic
remains in scripts.

**Action Conversions Needed:**

- `jdfalk/docker-detect-config-action` - Find and validate Docker configs

---

### Priority 7: Automation & Maintenance Scripts

| Script                    | Lines | Called By                     | Purpose                       | Complexity |
| ------------------------- | ----- | ----------------------------- | ----------------------------- | ---------- |
| `automation_workflow.py`  | 921   | `reusable-advanced-cache.yml` | Cache strategy generation     | **HIGH**   |
| `maintenance_workflow.py` | 418   | `reusable-maintenance.yml`    | Dependency/security summaries | **MEDIUM** |
| `docs_workflow.py`        | 470   | `documentation.yml`           | Doc generation automation     | **MEDIUM** |
| `intelligent_labeling.py` | 98    | `issue-automation.yml`        | AI-based PR/issue labeling    | **MEDIUM** |
| `sync_receiver.py`        | 338   | `sync-receiver.yml`           | Cross-repo sync management    | **HIGH**   |

**Action Conversions Needed:**

- `jdfalk/cache-strategy-action` - Advanced caching logic
- `jdfalk/maintenance-summary-action` - Dependency/security summaries
- `jdfalk/docs-generator-action` - Documentation automation
- `jdfalk/intelligent-labeling-action` - AI label suggestions
- `jdfalk/sync-receiver-action` - Repo sync orchestration

---

### Priority 8: Utility Scripts (Low Priority)

| Script                                   | Lines   | Called By              | Purpose                    | Complexity |
| ---------------------------------------- | ------- | ---------------------- | -------------------------- | ---------- |
| `publish_to_github_packages.py`          | 187     | Release workflows      | Publish to GitHub Packages | **MEDIUM** |
| `write_go_module_metadata.py`            | (small) | Go releases            | Write metadata files       | **LOW**    |
| `write_pypirc.py`                        | (small) | Python releases        | Generate PyPI config       | **LOW**    |
| `configure_cargo_registry.py`            | (small) | Rust releases          | Configure cargo registry   | **LOW**    |
| `download_nltk_data.py`                  | (small) | ML workflows           | Download NLTK datasets     | **LOW**    |
| `capture_benchmark_metrics.py`           | (small) | Performance monitoring | Collect benchmark data     | **LOW**    |
| `generate_security_summary.py`           | (small) | Security workflows     | Security scan summaries    | **LOW**    |
| `generate_workflow_analytics_summary.py` | 89      | Analytics              | Workflow metrics           | **LOW**    |
| `generate_release_summary.py`            | (small) | Releases               | Release changelog          | **LOW**    |

**Action Conversions Needed:**

- Most of these can remain as scripts OR be embedded into the larger actions
  above
- `jdfalk/publish-packages-action` - Generic package publishing (all registries)

---

## Conversion Strategy

### Phase 1: Critical Infrastructure (Week 1) ✅ YOU ARE HERE

**Goal:** Unblock all reusable workflow calls

- [ ] Create `jdfalk/load-config-action`
  - Embed `load_repository_config.py` logic
  - Add YAML parsing (PyYAML dependency)
  - Output JSON config + has-config flag

- [ ] Create `jdfalk/workflow-common-action`
  - Embed `workflow_common.py` utilities
  - Provide reusable step outputs
  - **OR** embed this into every action (reduces external deps)

### Phase 2: CI Workflow Actions (Week 2)

**Goal:** Replace `ci_workflow.py` dependencies

- [ ] Create `jdfalk/ci-generate-matrices-action`
  - Language detection
  - Matrix JSON generation
  - Config-based fallbacks

- [ ] Create `jdfalk/ci-detect-changes-action`
  - File change detection
  - Pattern matching
  - **OR** use `dorny/paths-filter` directly

- [ ] Create `jdfalk/ci-run-linters-action`
  - Multi-language linter coordination
  - Super-linter integration
  - Error aggregation

### Phase 3: Release Workflow Actions (Week 3)

**Goal:** Replace `release_workflow.py` dependencies

- [ ] Create `jdfalk/detect-languages-action`
  - Detect all project languages
  - Generate build matrices
  - Output boolean flags

- [ ] Create `jdfalk/release-strategy-action`
  - Branch-based strategy (main=stable, develop=prerelease)
  - Manual override support
  - Output strategy metadata

- [ ] Create `jdfalk/generate-version-action`
  - Semantic versioning
  - Tag generation
  - Changelog integration

- [ ] Create `jdfalk/package-assets-action`
  - Bundle artifacts
  - Generate checksums
  - Prepare release archives

### Phase 4: Specialized Actions (Week 4+)

**Goal:** Convert remaining high-value scripts

- [ ] Protobuf actions (config, verify)
- [ ] Docker detection action
- [ ] Maintenance/automation actions
- [ ] Documentation generator action
- [ ] Intelligent labeling action

### Phase 5: Cleanup & Deprecation

- [ ] Update all reusable workflows to use new actions
- [ ] Mark `.github/workflows/scripts/` as deprecated
- [ ] Create migration guide for external repos
- [ ] Archive script directory after 1 release cycle

---

## Migration Impact Assessment

### Repositories Affected

Based on grep search, these repositories call the reusable workflows:

- `jdfalk/audiobook-organizer` - Uses reusable-ci.yml, reusable-release.yml
- `jdfalk/ghcommon` (self) - Self-referential workflows
- `jdfalk/project-template` - Template for new repos
- **Estimate:** 10-50 additional repositories (not in current workspace)

### Breaking Changes

- **None (if done correctly)** - Actions should be drop-in replacements
- Workflows will change from:

  ```yaml
  - name: Checkout scripts
    uses: actions/checkout@v6
    with:
      repository: jdfalk/ghcommon
      path: ghcommon-scripts
  - run: python3 $GHCOMMON_SCRIPTS_DIR/script.py
  ```

  To:

  ```yaml
  - uses: jdfalk/action-name@v1
    with:
      input1: value1
  ```

### Testing Strategy

1. Create actions with same inputs/outputs as scripts
2. Test in `ghcommon` repository first (self-test)
3. Deploy to `audiobook-organizer` (production test)
4. Deploy to `project-template` (template test)
5. Gradual rollout to other repos
6. Monitor workflow run logs for errors

---

## Action Architecture Decisions

### Decision 1: Monorepo vs. Multi-Repo for Actions

**Current:** 6 release actions are in **separate repositories**

**Options:**

- A) Continue separate repos (1 action = 1 repo)
- B) Create `jdfalk/ghcommon-actions` monorepo with multiple actions
- C) Embed actions in `jdfalk/ghcommon/.github/actions/`

**Recommendation:** **Option A (Separate Repos)** for consistency

- Pros: Independent versioning, clear boundaries, follows existing pattern
- Cons: More repos to manage
- Mitigation: Use action templates for consistency

### Decision 2: Dependency Management

**Challenge:** Scripts like `workflow_common.py` are shared dependencies

**Options:**

- A) Embed shared code in every action (duplication)
- B) Create `jdfalk/workflow-common-action` as a dependency
- C) Use GitHub Action's built-in `uses:` composition

**Recommendation:** **Option A (Embed)** for simplicity

- Pros: No external dependencies, actions are self-contained
- Cons: Code duplication
- Rationale: Shared code is only ~150 lines, benefits outweigh duplication

### Decision 3: Language Choice for Actions

**Current:** Scripts are Python + Shell

**Options:**

- A) Keep Python (requires `python` in composite action steps)
- B) Convert to pure Shell/Bash
- C) Use TypeScript (GitHub Actions native runtime)
- D) Mix: Simple actions = Shell, Complex = Python

**Recommendation:** **Option D (Mixed)**

- Simple logic → Shell (generate-version, release-strategy)
- Complex logic → Python (ci_workflow, automation_workflow)
- Rationale: Leverage existing code, Python is available on all runners

### Decision 4: Action Versioning Strategy

**Current:** Release actions use semantic versioning tags

**Options:**

- A) Use branch-based refs (`@main`, `@develop`)
- B) Use semantic version tags (`@v1`, `@v1.2.3`)
- C) Use commit SHAs (`@abc123...`)

**Recommendation:** **Option B (Semantic Tags)**

- Align with existing release-\*-action pattern
- Use major version tags (`@v1`) for stability
- Cut new versions on breaking changes

---

## Technical Specifications

### Action Input/Output Contracts

#### `load-config-action`

```yaml
inputs:
  config-file:
    description: 'Path to repository-config.yml'
    default: '.github/repository-config.yml'
outputs:
  config:
    description: 'Parsed config as JSON'
  has-config:
    description: 'Whether config file exists'
```

#### `ci-generate-matrices-action`

```yaml
inputs:
  repository-config:
    description: 'Repository config JSON'
  fallback-go-version:
    default: '1.24'
  fallback-python-version:
    default: '3.13'
  # ... other fallbacks
outputs:
  go-matrix:
    description: 'Go version/OS matrix JSON'
  python-matrix:
    description: 'Python version/OS matrix JSON'
  # ... other matrices
```

#### `detect-languages-action`

```yaml
inputs:
  skip-detection:
    description: 'Skip auto-detection'
    default: 'false'
  build-target:
    description: 'Targets to build (all, go, python, etc.)'
    default: 'all'
  # ... language overrides
outputs:
  has-go: 'true/false'
  has-python: 'true/false'
  has-rust: 'true/false'
  # ... other languages
  go-matrix: 'JSON matrix'
  # ... other matrices
```

#### `release-strategy-action`

```yaml
inputs:
  branch-name:
    description: 'Git branch name'
  prerelease:
    description: 'Force prerelease'
    default: 'false'
  draft:
    description: 'Force draft'
    default: 'false'
outputs:
  strategy:
    description: 'stable/prerelease/draft'
  auto-prerelease:
    description: 'Whether auto-detected prerelease'
  auto-draft:
    description: 'Whether auto-detected draft'
```

#### `generate-version-action`

```yaml
inputs:
  release-type:
    description: 'auto/major/minor/patch'
    default: 'auto'
  branch-name:
    description: 'Git branch name'
  base-version:
    description: 'Existing version to increment from'
outputs:
  tag:
    description: 'Generated semantic version tag'
  version:
    description: "Version without 'v' prefix"
  changelog:
    description: 'Generated changelog since last tag'
```

---

## Development Guidelines

### Action Repository Template Structure

```
action-name/
├── action.yml              # Action metadata + composite steps
├── README.md               # Usage documentation
├── LICENSE                 # MIT or Apache 2.0
├── TODO.md                 # Implementation todos
├── .github/
│   └── workflows/
│       ├── ci.yml          # Test action in CI
│       ├── release.yml     # Semantic release tagging
│       └── test-integration.yml  # Integration tests (optional)
└── test-project/           # Optional test fixtures
```

### Action.yml Header Template

```yaml
# file: action.yml
# version: 1.0.0
# guid: <generate-new-uuid>

name: 'Action Name'
description: 'Brief description of action purpose'
author: 'jdfalk'

branding:
  icon: 'icon-name' # https://feathericons.com/
  color: 'blue' # blue, green, orange, red, purple, gray-dark

inputs:
  # Define inputs here
outputs:
  # Define outputs here

runs:
  using: 'composite'
  steps:
    # Implementation steps
```

### Embedding Python Scripts

```yaml
- name: Run Python logic
  shell: python
  run: |
    import os
    import json
    from pathlib import Path

    # Embed Python code here (no external file needed)
    # Use GitHub Actions env vars: os.environ["GITHUB_OUTPUT"]

    def write_output(name, value):
        output_file = os.environ.get("GITHUB_OUTPUT")
        if output_file:
            with open(output_file, "a") as f:
                f.write(f"{name}={value}\n")

    # Main logic here
    write_output("result", "success")
```

### Embedding Shell Scripts

```yaml
- name: Run Shell logic
  shell: bash
  run: |
    set -euo pipefail

    # Embed bash code here
    echo "result=success" >> "$GITHUB_OUTPUT"
```

---

## Next Steps (Immediate Actions)

1. **Mark current todo complete** ✅

   ```
   - [✅] Audit all workflow scripts and dependencies
   ```

2. **Move to next phase:**
   - [ ] Map script usage across reusable workflows (detailed call graph)
   - [ ] Design action architecture and conversion pattern (technical spec)
   - [ ] Create conversion roadmap with priorities (project plan)
   - [ ] Document action development guidelines (developer guide)

3. **Create first action (validation):**
   - Start with `load-config-action` as proof-of-concept
   - Test in ghcommon repository
   - Validate pattern before mass conversion

---

## Appendix A: Complete Script List

```
__pycache__/                           (ignored)
automation_workflow.py                 921 lines - Priority 7
build_go_release.py                    308 lines - ✅ IN ACTION
capture_benchmark_metrics.py           (small) - Priority 8
check_protobuf_artifacts.py            (small) - Priority 5
ci_workflow.py                         867 lines - Priority 2
collect_rust_crate_metadata.py         85 lines - Priority 4
configure_cargo_registry.py            (small) - Priority 8
detect-languages.sh                    165 lines - Priority 3
detect_docker_config.py                (small) - Priority 6
detect_frontend_package.py             (small) - Priority 4
detect_languages.py                    (embedded in ci_workflow) - Priority 2
detect_python_package.py               113 lines - Priority 4
determine_docker_platforms.py          111 lines - Priority 6
docs_workflow.py                       470 lines - Priority 7
download_nltk_data.py                  (small) - Priority 8
generate-changelog.sh                  (embedded) - Priority 3
generate-version.sh                    182 lines - Priority 3
generate_release_summary.py            (small) - Priority 8
generate_security_summary.py           (small) - Priority 8
generate_workflow_analytics_summary.py 89 lines - Priority 8
get_frontend_working_dir.py            (small) - Priority 4
intelligent_labeling.py                98 lines - Priority 7
load_repository_config.py              43 lines - Priority 1 🔥
maintenance_workflow.py                418 lines - Priority 7
package_release_assets.py              135 lines - Priority 3
parse_protobuf_config.py               92 lines - Priority 5
publish_to_github_packages.py          187 lines - Priority 8
release-strategy.sh                    (embedded) - Priority 3
release_workflow.py                    425 lines - Priority 3
run_python_release_tests.py            (small) - Priority 4
sync_receiver.py                       338 lines - Priority 7
test-scripts.sh                        156 lines - Testing/Dev only
validate_docker_compose.py             (small) - Priority 6
verify_python_protobuf_plugins.py      (small) - Priority 5
workflow_common.py                     145 lines - Priority 1 🔥
write_go_module_metadata.py            (small) - Priority 8
write_pypirc.py                        (small) - Priority 8
README.md                              Documentation
```

**Legend:**

- 🔥 = Critical path blocker
- ✅ = Already in action
- (small) = Less than 50 lines
- (embedded) = Logic is inside another script

---

## Appendix B: Workflow Dependency Graph

```
reusable-ci.yml
├── load_repository_config.py (Priority 1)
├── ci_workflow.py (Priority 2)
│   ├── workflow_common.py (Priority 1)
│   └── load_repository_config.py
└── dorny/paths-filter (external action)

reusable-release.yml
├── load_repository_config.py (Priority 1)
├── release_workflow.py (Priority 3)
│   ├── workflow_common.py (Priority 1)
│   ├── detect-languages.sh
│   ├── generate-version.sh
│   └── release-strategy.sh
└── package_release_assets.py (Priority 3)

reusable-protobuf.yml
├── parse_protobuf_config.py (Priority 5)
└── check_protobuf_artifacts.py (Priority 5)

reusable-maintenance.yml
├── maintenance_workflow.py (Priority 7)
├── workflow_common.py
└── validate_docker_compose.py

reusable-advanced-cache.yml
├── automation_workflow.py (Priority 7)
└── workflow_common.py

documentation.yml
└── docs_workflow.py (Priority 7)

issue-automation.yml
└── intelligent_labeling.py (Priority 7)

sync-receiver.yml
└── sync_receiver.py (Priority 7)
```

---

**End of Audit Document**
