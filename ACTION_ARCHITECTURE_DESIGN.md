<!-- file: ACTION_ARCHITECTURE_DESIGN.md -->
<!-- version: 1.0.0 -->
<!-- guid: 3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f -->
<!-- last-edited: 2026-01-19 -->

# GitHub Actions Architecture Design

**Date:** December 20, 2025 **Purpose:** Technical architecture and design
patterns for workflow script conversion **Status:** Phase 3 - Architecture
Design Complete

## Design Principles

### 1. Self-Contained Actions

- **No external script dependencies** - All code embedded in action.yml
- **Clear input/output contracts** - Formal parameter specifications
- **Idempotent operations** - Safe to run multiple times
- **Fast execution** - Minimal overhead (<5 seconds for simple actions)

### 2. Composability

- Actions can call other actions via `uses:`
- Outputs from one action feed inputs to another
- Matrix generation actions produce JSON for downstream jobs

### 3. Backward Compatibility

- Maintain same inputs/outputs as original scripts
- Support fallback to defaults
- Graceful degradation when config missing

### 4. Observability

- Rich step summaries using `$GITHUB_STEP_SUMMARY`
- Structured outputs (JSON where appropriate)
- Error messages with actionable guidance

---

## Action Repository Pattern

Based on analysis of existing `release-*-action` repositories:

```
action-name/
├── action.yml                    # Main action definition
├── README.md                     # Usage documentation
├── LICENSE                       # MIT License
├── TODO.md                       # Implementation tracking
├── CHANGELOG.md                  # Version history
├── .github/
│   ├── workflows/
│   │   ├── ci.yml               # Test action on push/PR
│   │   ├── release.yml          # Semantic release tagging
│   │   └── test-integration.yml # Integration tests (optional)
│   └── dependabot.yml           # Dependency updates (if using actions)
├── test-project/                # Test fixtures (optional)
│   ├── .github/
│   │   └── repository-config.yml
│   ├── go.mod                   # Language-specific test files
│   └── ...
└── .gitignore
```

### action.yml Structure

```yaml
# file: action.yml
# version: 1.0.0
# guid: <unique-uuid>

name: 'Action Display Name'
description: 'Clear, concise description of action purpose'
author: 'jdfalk'

branding:
  icon: 'icon-name' # From https://feathericons.com/
  color: 'blue' # blue, green, orange, red, purple, gray-dark

inputs:
  # Required inputs first
  required-input:
    description: 'Clear description'
    required: true

  # Optional inputs with defaults
  optional-input:
    description: 'Clear description'
    required: false
    default: 'default-value'

outputs:
  # All outputs defined upfront
  output-name:
    description: 'Clear description of output'
    value: ${{ steps.step-id.outputs.output-name }}

runs:
  using: 'composite'
  steps:
    # Implementation steps
```

---

## Priority 1 Actions (Critical Infrastructure)

### Action 1: load-config-action

**Repository:** `jdfalk/load-config-action` **Purpose:** Load and parse
`.github/repository-config.yml` **Replaces:** `load_repository_config.py` (43
lines)

#### Technical Specification

```yaml
# file: action.yml
# version: 1.0.0
# guid: 4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a

name: 'Load Repository Config'
description:
  'Load and parse .github/repository-config.yml with fallback handling'
author: 'jdfalk'

branding:
  icon: 'file-text'
  color: 'blue'

inputs:
  config-file:
    description: 'Path to repository config YAML file'
    required: false
    default: '.github/repository-config.yml'

  fail-on-missing:
    description: 'Fail if config file is missing'
    required: false
    default: 'false'

outputs:
  config:
    description: 'Parsed configuration as JSON string'
    value: ${{ steps.load.outputs.config }}

  has-config:
    description: 'Whether config file exists and was parsed successfully'
    value: ${{ steps.load.outputs.has-config }}

  raw-yaml:
    description: 'Raw YAML content (if exists)'
    value: ${{ steps.load.outputs.raw-yaml }}

runs:
  using: 'composite'
  steps:
    - name: Load and parse configuration
      id: load
      shell: python
      env:
        CONFIG_FILE: ${{ inputs.config-file }}
        FAIL_ON_MISSING: ${{ inputs.fail-on-missing }}
      run: |
        import json
        import os
        import sys
        from pathlib import Path

        try:
            import yaml
        except ImportError:
            print("::error::PyYAML not available - installing...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "PyYAML"])
            import yaml

        def write_output(name, value):
            """Write to GITHUB_OUTPUT."""
            output_file = os.environ.get("GITHUB_OUTPUT")
            if output_file:
                with open(output_file, "a", encoding="utf-8") as f:
                    # Handle multiline outputs
                    if "\n" in value:
                        delimiter = "EOF"
                        f.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")
                    else:
                        f.write(f"{name}={value}\n")

        def write_summary(text):
            """Write to GITHUB_STEP_SUMMARY."""
            summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
            if summary_file:
                with open(summary_file, "a", encoding="utf-8") as f:
                    f.write(text + "\n")

        config_file = Path(os.environ.get("CONFIG_FILE", ".github/repository-config.yml"))
        fail_on_missing = os.environ.get("FAIL_ON_MISSING", "false").lower() == "true"

        # Check if file exists
        if not config_file.exists():
            write_output("has-config", "false")
            write_output("config", "{}")
            write_output("raw-yaml", "")

            if fail_on_missing:
                print(f"::error::Config file not found: {config_file}")
                sys.exit(1)
            else:
                write_summary(f"⚠️ Config file not found: `{config_file}` (using defaults)")
                sys.exit(0)

        # Read and parse YAML
        try:
            raw_content = config_file.read_text(encoding="utf-8")
            data = yaml.safe_load(raw_content) or {}

            write_output("has-config", "true")
            write_output("config", json.dumps(data, separators=(",", ":")))
            write_output("raw-yaml", raw_content)

            write_summary(f"✅ Loaded config from `{config_file}`")
            write_summary(f"\n**Config keys:** {', '.join(f'`{k}`' for k in data.keys())}")

        except yaml.YAMLError as e:
            write_output("has-config", "false")
            write_output("config", "{}")
            write_output("raw-yaml", "")

            print(f"::error::Failed to parse YAML: {e}")
            if fail_on_missing:
                sys.exit(1)
            else:
                write_summary(f"⚠️ Failed to parse `{config_file}`: {e}")
```

#### Usage Example

```yaml
jobs:
  load-config:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: jdfalk/load-config-action@v1
        id: config
        with:
          config-file: .github/repository-config.yml
          fail-on-missing: false

      - name: Use config
        run: |
          echo "Has config: ${{ steps.config.outputs.has-config }}"
          echo "Config: ${{ steps.config.outputs.config }}"
```

#### Testing Strategy

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test-with-config:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: ./ # Test action itself
        id: config
        with:
          config-file: test-project/.github/repository-config.yml
      - name: Validate outputs
        run: |
          if [ "${{ steps.config.outputs.has-config }}" != "true" ]; then
            echo "Expected has-config=true"
            exit 1
          fi

  test-without-config:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: ./
        id: config
        with:
          config-file: nonexistent.yml
          fail-on-missing: false
      - name: Validate fallback
        run: |
          if [ "${{ steps.config.outputs.has-config }}" != "false" ]; then
            echo "Expected has-config=false"
            exit 1
          fi
          if [ "${{ steps.config.outputs.config }}" != "{}" ]; then
            echo "Expected empty config"
            exit 1
          fi
```

---

### Action 2: workflow-common-action (Decision: EMBED, Don't Create)

**Analysis:** The `workflow_common.py` (145 lines) provides utility functions:

- `write_output()` - Write to GITHUB_OUTPUT
- `append_summary()` - Write to GITHUB_STEP_SUMMARY
- `get_repository_config()` - Parse config JSON from environment

**Decision:** **DO NOT create a separate action.** Instead, **embed** these
utilities into each action that needs them. Reasoning:

1. Functions are only ~10-20 lines each
2. Creating a dependency action adds complexity
3. Duplication is acceptable for this level of simplicity
4. Actions remain self-contained

**Embedded Utility Template:**

```python
# Standard utilities (embed at top of Python blocks)
def write_output(name, value):
    """Write to GITHUB_OUTPUT."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            if "\n" in value:
                delimiter = "EOF"
                f.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                f.write(f"{name}={value}\n")

def write_summary(text):
    """Write to GITHUB_STEP_SUMMARY."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(text + "\n")

def get_repository_config():
    """Get config JSON from environment."""
    import json
    raw = os.environ.get("REPOSITORY_CONFIG", "{}")
    return json.loads(raw)
```

---

## Priority 2 Actions (CI Workflow)

### Action 3: ci-generate-matrices-action

**Repository:** `jdfalk/ci-generate-matrices-action` **Purpose:** Generate
language version matrices for CI testing **Replaces:**
`ci_workflow.py generate-matrices` (partial, ~200 lines)

#### Technical Specification

```yaml
name: 'Generate CI Matrices'
description:
  'Generate test matrices for Go, Python, Rust, and Node.js based on repository
  config'
author: 'jdfalk'

branding:
  icon: 'grid'
  color: 'blue'

inputs:
  repository-config:
    description: 'Repository configuration JSON (from load-config-action)'
    required: false
    default: '{}'

  # Fallback versions
  fallback-go-version:
    description: 'Default Go version if not in config'
    required: false
    default: '1.23'

  fallback-python-version:
    description: 'Default Python version if not in config'
    required: false
    default: '3.12'

  fallback-rust-version:
    description: 'Default Rust version if not in config'
    required: false
    default: '1.75'

  fallback-node-version:
    description: 'Default Node.js version if not in config'
    required: false
    default: '22'

  fallback-coverage-threshold:
    description: 'Default coverage threshold percentage'
    required: false
    default: '80'

  # OS options
  include-linux:
    description: 'Include Linux in OS matrix'
    required: false
    default: 'true'

  include-macos:
    description: 'Include macOS in OS matrix'
    required: false
    default: 'false'

  include-windows:
    description: 'Include Windows in OS matrix'
    required: false
    default: 'false'

outputs:
  go-matrix:
    description: 'Go version/OS matrix as JSON'
    value: ${{ steps.generate.outputs.go-matrix }}

  python-matrix:
    description: 'Python version/OS matrix as JSON'
    value: ${{ steps.generate.outputs.python-matrix }}

  rust-matrix:
    description: 'Rust version/OS matrix as JSON'
    value: ${{ steps.generate.outputs.rust-matrix }}

  frontend-matrix:
    description: 'Node.js version/OS matrix as JSON'
    value: ${{ steps.generate.outputs.frontend-matrix }}

  coverage-threshold:
    description: 'Effective coverage threshold'
    value: ${{ steps.generate.outputs.coverage-threshold }}

runs:
  using: 'composite'
  steps:
    - name: Generate matrices
      id: generate
      shell: python
      env:
        REPOSITORY_CONFIG: ${{ inputs.repository-config }}
        FALLBACK_GO_VERSION: ${{ inputs.fallback-go-version }}
        FALLBACK_PYTHON_VERSION: ${{ inputs.fallback-python-version }}
        FALLBACK_RUST_VERSION: ${{ inputs.fallback-rust-version }}
        FALLBACK_NODE_VERSION: ${{ inputs.fallback-node-version }}
        FALLBACK_COVERAGE_THRESHOLD: ${{ inputs.fallback-coverage-threshold }}
        INCLUDE_LINUX: ${{ inputs.include-linux }}
        INCLUDE_MACOS: ${{ inputs.include-macos }}
        INCLUDE_WINDOWS: ${{ inputs.include-windows }}
      run: |
        import json
        import os

        # [Embed utility functions here]

        # Parse config
        config = json.loads(os.environ.get("REPOSITORY_CONFIG", "{}"))
        ci_config = config.get("ci", {})

        # Build OS list
        oses = []
        if os.environ.get("INCLUDE_LINUX", "true").lower() == "true":
            oses.append("ubuntu-latest")
        if os.environ.get("INCLUDE_MACOS", "false").lower() == "true":
            oses.append("macos-latest")
        if os.environ.get("INCLUDE_WINDOWS", "false").lower() == "true":
            oses.append("windows-latest")

        # Generate Go matrix
        go_versions = ci_config.get("go", {}).get("versions", [os.environ["FALLBACK_GO_VERSION"]])
        go_matrix = {
            "go-version": go_versions,
            "os": oses
        }
        write_output("go-matrix", json.dumps(go_matrix, separators=(",", ":")))

        # Generate Python matrix
        python_versions = ci_config.get("python", {}).get("versions", [os.environ["FALLBACK_PYTHON_VERSION"]])
        python_matrix = {
            "python-version": python_versions,
            "os": oses
        }
        write_output("python-matrix", json.dumps(python_matrix, separators=(",", ":")))

        # Generate Rust matrix
        rust_versions = ci_config.get("rust", {}).get("versions", [os.environ["FALLBACK_RUST_VERSION"]])
        rust_matrix = {
            "rust-version": rust_versions,
            "os": oses
        }
        write_output("rust-matrix", json.dumps(rust_matrix, separators=(",", ":")))

        # Generate Node.js matrix
        node_versions = ci_config.get("frontend", {}).get("node-versions", [os.environ["FALLBACK_NODE_VERSION"]])
        frontend_matrix = {
            "node-version": node_versions,
            "os": oses
        }
        write_output("frontend-matrix", json.dumps(frontend_matrix, separators=(",", ":")))

        # Coverage threshold
        coverage_threshold = ci_config.get("coverage", {}).get("threshold", os.environ["FALLBACK_COVERAGE_THRESHOLD"])
        write_output("coverage-threshold", str(coverage_threshold))

        # Summary
        write_summary("## 🔧 Generated CI Matrices")
        write_summary(f"- **Go versions:** {', '.join(go_versions)}")
        write_summary(f"- **Python versions:** {', '.join(python_versions)}")
        write_summary(f"- **Rust versions:** {', '.join(rust_versions)}")
        write_summary(f"- **Node.js versions:** {', '.join(node_versions)}")
        write_summary(f"- **Operating systems:** {', '.join(oses)}")
        write_summary(f"- **Coverage threshold:** {coverage_threshold}%")
```

#### Usage Example

```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      go-matrix: ${{ steps.matrices.outputs.go-matrix }}
      python-matrix: ${{ steps.matrices.outputs.python-matrix }}
    steps:
      - uses: actions/checkout@v6
      - uses: jdfalk/load-config-action@v1
        id: config
      - uses: jdfalk/ci-generate-matrices-action@v1
        id: matrices
        with:
          repository-config: ${{ steps.config.outputs.config }}
          fallback-go-version: '1.23'

  test-go:
    needs: setup
    strategy:
      matrix: ${{ fromJSON(needs.setup.outputs.go-matrix) }}
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go-version }}
      - run: go test ./...
```

---

## Priority 3 Actions (Release Workflow)

### Action 4: detect-languages-action

**Repository:** `jdfalk/detect-languages-action` **Purpose:** Detect project
languages and technologies **Replaces:** `release_workflow.py detect-languages`
(~150 lines)

#### Technical Specification

```yaml
name: 'Detect Project Languages'
description:
  'Automatically detect Go, Python, Rust, Frontend, Docker, and Protobuf in
  repository'
author: 'jdfalk'

branding:
  icon: 'search'
  color: 'purple'

inputs:
  skip-detection:
    description: 'Skip file-based detection and use manual overrides'
    required: false
    default: 'false'

  build-target:
    description:
      'Comma-separated build targets (all, go, python, rust, frontend, docker,
      protobuf)'
    required: false
    default: 'all'

  # Manual overrides
  go-enabled:
    description: 'Force enable/disable Go (true/false/auto)'
    required: false
    default: 'auto'

  python-enabled:
    description: 'Force enable/disable Python (true/false/auto)'
    required: false
    default: 'auto'

  rust-enabled:
    description: 'Force enable/disable Rust (true/false/auto)'
    required: false
    default: 'auto'

  frontend-enabled:
    description: 'Force enable/disable Frontend (true/false/auto)'
    required: false
    default: 'auto'

  docker-enabled:
    description: 'Force enable/disable Docker (true/false/auto)'
    required: false
    default: 'auto'

  protobuf-enabled:
    description: 'Force enable/disable Protobuf (true/false/auto)'
    required: false
    default: 'auto'

  repository-config:
    description: 'Repository config JSON for version matrices'
    required: false
    default: '{}'

outputs:
  has-go:
    description: 'Whether Go is detected'
    value: ${{ steps.detect.outputs.has-go }}

  has-python:
    description: 'Whether Python is detected'
    value: ${{ steps.detect.outputs.has-python }}

  has-rust:
    description: 'Whether Rust is detected'
    value: ${{ steps.detect.outputs.has-rust }}

  has-frontend:
    description: 'Whether Frontend is detected'
    value: ${{ steps.detect.outputs.has-frontend }}

  has-docker:
    description: 'Whether Docker is detected'
    value: ${{ steps.detect.outputs.has-docker }}

  protobuf-needed:
    description: 'Whether Protobuf is needed'
    value: ${{ steps.detect.outputs.protobuf-needed }}

  primary-language:
    description: 'Primary language (go, python, rust, frontend, docker)'
    value: ${{ steps.detect.outputs.primary-language }}

  go-matrix:
    description: 'Go build matrix JSON'
    value: ${{ steps.detect.outputs.go-matrix }}

  python-matrix:
    description: 'Python build matrix JSON'
    value: ${{ steps.detect.outputs.python-matrix }}

  rust-matrix:
    description: 'Rust build matrix JSON'
    value: ${{ steps.detect.outputs.rust-matrix }}

  frontend-matrix:
    description: 'Frontend build matrix JSON'
    value: ${{ steps.detect.outputs.frontend-matrix }}

  docker-matrix:
    description: 'Docker build matrix JSON'
    value: ${{ steps.detect.outputs.docker-matrix }}

runs:
  using: 'composite'
  steps:
    - name: Detect languages
      id: detect
      shell: python
      env:
        SKIP_DETECTION: ${{ inputs.skip-detection }}
        BUILD_TARGET: ${{ inputs.build-target }}
        GO_ENABLED: ${{ inputs.go-enabled }}
        PYTHON_ENABLED: ${{ inputs.python-enabled }}
        RUST_ENABLED: ${{ inputs.rust-enabled }}
        FRONTEND_ENABLED: ${{ inputs.frontend-enabled }}
        DOCKER_ENABLED: ${{ inputs.docker-enabled }}
        PROTOBUF_ENABLED: ${{ inputs.protobuf-enabled }}
        REPOSITORY_CONFIG: ${{ inputs.repository-config }}
      run: |
        import json
        import os
        from pathlib import Path

        # [Embed utility functions]

        # Parse inputs
        skip_detection = os.environ.get("SKIP_DETECTION", "false").lower() == "true"
        build_target = os.environ.get("BUILD_TARGET", "all").lower()
        targets = set(t.strip() for t in build_target.split(",") if t.strip())

        def normalize_override(value):
            value = str(value).lower()
            return value if value in ("true", "false") else "auto"

        def derive_flag(override, key, default):
            if override == "true":
                return True
            if override == "false":
                return False
            if "all" in targets or not targets:
                return default
            return key in targets or default

        overrides = {
            "go": normalize_override(os.environ.get("GO_ENABLED", "auto")),
            "python": normalize_override(os.environ.get("PYTHON_ENABLED", "auto")),
            "rust": normalize_override(os.environ.get("RUST_ENABLED", "auto")),
            "frontend": normalize_override(os.environ.get("FRONTEND_ENABLED", "auto")),
            "docker": normalize_override(os.environ.get("DOCKER_ENABLED", "auto")),
            "protobuf": normalize_override(os.environ.get("PROTOBUF_ENABLED", "auto")),
        }

        # Detect languages
        if skip_detection:
            has_go = derive_flag(overrides["go"], "go", False)
            has_python = derive_flag(overrides["python"], "python", False)
            has_rust = derive_flag(overrides["rust"], "rust", False)
            has_frontend = derive_flag(overrides["frontend"], "frontend", False)
            has_docker = derive_flag(overrides["docker"], "docker", False)
            protobuf_needed = derive_flag(overrides["protobuf"], "protobuf", False)
        else:
            # File-based detection
            has_go = Path("go.mod").exists() or Path("main.go").exists() or Path("cmd").exists()
            has_python = any(Path(p).exists() for p in ["setup.py", "pyproject.toml", "requirements.txt"])
            has_rust = Path("Cargo.toml").exists()
            has_frontend = Path("package.json").exists()
            has_docker = Path("Dockerfile").exists() or Path("docker-compose.yml").exists()
            protobuf_needed = any(Path(".").rglob("*.proto"))

            # Apply overrides
            if overrides["go"] != "auto":
                has_go = overrides["go"] == "true"
            if overrides["python"] != "auto":
                has_python = overrides["python"] == "true"
            if overrides["rust"] != "auto":
                has_rust = overrides["rust"] == "true"
            if overrides["frontend"] != "auto":
                has_frontend = overrides["frontend"] == "true"
            if overrides["docker"] != "auto":
                has_docker = overrides["docker"] == "true"
            if overrides["protobuf"] != "auto":
                protobuf_needed = overrides["protobuf"] == "true"

        # Determine primary language
        if has_go:
            primary = "go"
        elif has_python:
            primary = "python"
        elif has_rust:
            primary = "rust"
        elif has_frontend:
            primary = "frontend"
        elif has_docker:
            primary = "docker"
        else:
            primary = "unknown"

        # Generate matrices (simplified - use ci-generate-matrices-action for full logic)
        config = json.loads(os.environ.get("REPOSITORY_CONFIG", "{}"))
        go_matrix = {"os": ["ubuntu-latest"]} if has_go else {}
        python_matrix = {"os": ["ubuntu-latest"]} if has_python else {}
        rust_matrix = {"os": ["ubuntu-latest"]} if has_rust else {}
        frontend_matrix = {"os": ["ubuntu-latest"]} if has_frontend else {}
        docker_matrix = {"platform": ["linux/amd64"]} if has_docker else {}

        # Write outputs
        write_output("has-go", "true" if has_go else "false")
        write_output("has-python", "true" if has_python else "false")
        write_output("has-rust", "true" if has_rust else "false")
        write_output("has-frontend", "true" if has_frontend else "false")
        write_output("has-docker", "true" if has_docker else "false")
        write_output("protobuf-needed", "true" if protobuf_needed else "false")
        write_output("primary-language", primary)
        write_output("go-matrix", json.dumps(go_matrix, separators=(",", ":")))
        write_output("python-matrix", json.dumps(python_matrix, separators=(",", ":")))
        write_output("rust-matrix", json.dumps(rust_matrix, separators=(",", ":")))
        write_output("frontend-matrix", json.dumps(frontend_matrix, separators=(",", ":")))
        write_output("docker-matrix", json.dumps(docker_matrix, separators=(",", ":")))

        # Summary
        languages = [
            ("Go", has_go),
            ("Python", has_python),
            ("Rust", has_rust),
            ("Frontend", has_frontend),
            ("Docker", has_docker),
            ("Protobuf", protobuf_needed),
        ]
        write_summary("## 🔍 Detected Languages")
        for lang, detected in languages:
            icon = "✅" if detected else "❌"
            write_summary(f"- {icon} **{lang}**")
        write_summary(f"\n**Primary language:** `{primary}`")
```

---

### Action 5: release-strategy-action

**Repository:** `jdfalk/release-strategy-action` **Purpose:** Determine release
strategy (stable/prerelease/draft) based on branch **Replaces:**
`release_workflow.py release-strategy` (~50 lines)

#### Technical Specification

```yaml
name: 'Release Strategy'
description:
  'Determine release strategy (stable/prerelease/draft) based on Git branch'
author: 'jdfalk'

branding:
  icon: 'git-branch'
  color: 'green'

inputs:
  branch-name:
    description: 'Git branch name'
    required: true

  prerelease:
    description: 'Force prerelease (overrides auto-detection)'
    required: false
    default: 'false'

  draft:
    description: 'Force draft (overrides auto-detection)'
    required: false
    default: 'false'

outputs:
  strategy:
    description: 'Release strategy: stable, prerelease, or draft'
    value: ${{ steps.strategy.outputs.strategy }}

  auto-prerelease:
    description: 'Whether prerelease was auto-detected'
    value: ${{ steps.strategy.outputs.auto-prerelease }}

  auto-draft:
    description: 'Whether draft was auto-detected'
    value: ${{ steps.strategy.outputs.auto-draft }}

  is-stable:
    description: 'Whether this is a stable release'
    value: ${{ steps.strategy.outputs.is-stable }}

  is-prerelease:
    description: 'Whether this is a prerelease'
    value: ${{ steps.strategy.outputs.is-prerelease }}

  is-draft:
    description: 'Whether this is a draft'
    value: ${{ steps.strategy.outputs.is-draft }}

runs:
  using: 'composite'
  steps:
    - name: Determine strategy
      id: strategy
      shell: bash
      env:
        BRANCH_NAME: ${{ inputs.branch-name }}
        FORCE_PRERELEASE: ${{ inputs.prerelease }}
        FORCE_DRAFT: ${{ inputs.draft }}
      run: |
        # [Embed utility functions if needed, or use pure bash]

        branch="${BRANCH_NAME}"
        force_prerelease="${FORCE_PRERELEASE,,}"
        force_draft="${FORCE_DRAFT,,}"

        # Default flags
        auto_prerelease="false"
        auto_draft="false"
        strategy="stable"

        # Strategy logic
        if [[ "$force_prerelease" == "true" ]]; then
          strategy="prerelease"
        elif [[ "$force_draft" == "true" ]]; then
          strategy="draft"
        elif [[ "$branch" == "main" ]]; then
          strategy="stable"
          auto_draft="true"  # Main releases start as drafts for review
        elif [[ "$branch" == "develop" ]]; then
          strategy="prerelease"
          auto_prerelease="true"
        else
          # Feature branches = prerelease
          strategy="prerelease"
          auto_prerelease="true"
        fi

        # Set boolean flags
        is_stable="false"
        is_prerelease="false"
        is_draft="false"

        case "$strategy" in
          stable)
            is_stable="true"
            ;;
          prerelease)
            is_prerelease="true"
            ;;
          draft)
            is_draft="true"
            ;;
        esac

        # Write outputs
        echo "strategy=$strategy" >> "$GITHUB_OUTPUT"
        echo "auto-prerelease=$auto_prerelease" >> "$GITHUB_OUTPUT"
        echo "auto-draft=$auto_draft" >> "$GITHUB_OUTPUT"
        echo "is-stable=$is_stable" >> "$GITHUB_OUTPUT"
        echo "is-prerelease=$is_prerelease" >> "$GITHUB_OUTPUT"
        echo "is-draft=$is_draft" >> "$GITHUB_OUTPUT"

        # Summary
        cat >> "$GITHUB_STEP_SUMMARY" <<EOF
        ## 📦 Release Strategy
        - **Branch:** \`$branch\`
        - **Strategy:** \`$strategy\`
        - **Auto-prerelease:** $auto_prerelease
        - **Auto-draft:** $auto_draft

        ### Strategy Logic
        - \`main\` branch → Stable release (created as DRAFT for review)
        - \`develop\` branch → Pre-release (published DIRECTLY)
        - Feature branches → Pre-release (published DIRECTLY)
        EOF
```

---

### Action 6: generate-version-action

**Repository:** `jdfalk/generate-version-action` **Purpose:** Generate semantic
version tags **Replaces:** `release_workflow.py generate-version` +
`generate-version.sh` (~200 lines)

#### Technical Specification

```yaml
name: 'Generate Semantic Version'
description:
  'Generate semantic version tag based on release type and existing tags'
author: 'jdfalk'

branding:
  icon: 'tag'
  color: 'orange'

inputs:
  release-type:
    description: 'Release type: auto, major, minor, patch'
    required: false
    default: 'auto'

  branch-name:
    description: 'Git branch name'
    required: true

  prerelease-suffix:
    description: 'Prerelease suffix (alpha, beta, rc)'
    required: false
    default: ''

  base-version:
    description: 'Base version to increment from (if not using git tags)'
    required: false
    default: ''

outputs:
  tag:
    description: 'Generated semantic version tag (e.g., v1.2.3)'
    value: ${{ steps.version.outputs.tag }}

  version:
    description: "Version without 'v' prefix (e.g., 1.2.3)"
    value: ${{ steps.version.outputs.version }}

  major:
    description: 'Major version number'
    value: ${{ steps.version.outputs.major }}

  minor:
    description: 'Minor version number'
    value: ${{ steps.version.outputs.minor }}

  patch:
    description: 'Patch version number'
    value: ${{ steps.version.outputs.patch }}

  prerelease:
    description: 'Prerelease suffix (if any)'
    value: ${{ steps.version.outputs.prerelease }}

runs:
  using: 'composite'
  steps:
    - name: Generate version
      id: version
      shell: bash
      env:
        RELEASE_TYPE: ${{ inputs.release-type }}
        BRANCH_NAME: ${{ inputs.branch-name }}
        PRERELEASE_SUFFIX: ${{ inputs.prerelease-suffix }}
        BASE_VERSION: ${{ inputs.base-version }}
      run: |
        set -euo pipefail

        # Get latest tag
        latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
        echo "Latest tag: $latest_tag"

        # Parse version (strip 'v' prefix)
        version="${latest_tag#v}"
        IFS='.' read -r major minor patch_full <<< "$version"
        patch="${patch_full%%-*}"  # Strip prerelease suffix

        # Increment based on release type
        release_type="${RELEASE_TYPE,,}"
        case "$release_type" in
          major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
          minor)
            minor=$((minor + 1))
            patch=0
            ;;
          patch)
            patch=$((patch + 1))
            ;;
          auto)
            # Auto-detect from commit messages
            if git log "$latest_tag..HEAD" --oneline | grep -qE '^[a-f0-9]+ (feat|feature)'; then
              minor=$((minor + 1))
              patch=0
            else
              patch=$((patch + 1))
            fi
            ;;
        esac

        # Build version string
        new_version="$major.$minor.$patch"

        # Add prerelease suffix if provided
        if [[ -n "$PRERELEASE_SUFFIX" ]]; then
          # Count existing prereleases
          prerelease_count=$(git tag -l "v$new_version-$PRERELEASE_SUFFIX.*" | wc -l)
          prerelease_num=$((prerelease_count + 1))
          new_version="$new_version-$PRERELEASE_SUFFIX.$prerelease_num"
        fi

        # Write outputs
        echo "tag=v$new_version" >> "$GITHUB_OUTPUT"
        echo "version=$new_version" >> "$GITHUB_OUTPUT"
        echo "major=$major" >> "$GITHUB_OUTPUT"
        echo "minor=$minor" >> "$GITHUB_OUTPUT"
        echo "patch=$patch" >> "$GITHUB_OUTPUT"
        echo "prerelease=${PRERELEASE_SUFFIX}" >> "$GITHUB_OUTPUT"

        # Summary
        cat >> "$GITHUB_STEP_SUMMARY" <<EOF
        ## 🏷️ Generated Version
        - **Previous:** \`$latest_tag\`
        - **New:** \`v$new_version\`
        - **Release type:** \`$release_type\`
        - **Branch:** \`$BRANCH_NAME\`
        EOF
```

---

## Summary of Design Decisions

### 1. Embed Utilities (Don't Create workflow-common-action)

- ✅ Keeps actions self-contained
- ✅ Reduces external dependencies
- ✅ ~20 lines of code duplication is acceptable

### 2. Use Python for Complex Logic, Bash for Simple Logic

- ✅ Python available on all runners
- ✅ Leverage existing code
- ✅ Bash for simple file checks and git operations

### 3. Separate Repositories for Each Action

- ✅ Independent versioning
- ✅ Clear boundaries
- ✅ Follows existing pattern (release-\*-action)

### 4. Composite Actions (not Docker or JavaScript)

- ✅ Fastest execution
- ✅ No build step required
- ✅ Portable across runner OSes

### 5. Rich Summaries and Observability

- ✅ Every action writes to `$GITHUB_STEP_SUMMARY`
- ✅ Clear visual feedback in GitHub UI
- ✅ Actionable error messages

---

## Next: Conversion Roadmap

Now that architecture is defined, we can create:

1. **Conversion roadmap** - Implementation schedule with priorities
2. **Development guidelines** - Step-by-step action creation process
3. **Migration plan** - How to update workflows without breaking changes

---

**End of Architecture Design Document**
