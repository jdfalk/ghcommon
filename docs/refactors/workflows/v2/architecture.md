<!-- file: docs/refactors/workflows/v2/architecture.md -->
<!-- version: 1.0.0 -->
<!-- guid: b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e -->

# Workflow Architecture V2

## Overview

This document defines the architectural principles and patterns for the refactored ghcommon workflow
system.

## Core Principles

### 1. Configuration-Driven Design

**Single Source of Truth**: `.github/repository-config.yml`

All workflow behavior is controlled by configuration, not hardcoded values. This enables:

- **Consistency**: Same behavior across all consumer repositories
- **Maintainability**: Changes in one place propagate everywhere
- **Testability**: Can test with different configs without changing code
- **Documentation**: Config serves as living documentation

**Config Structure**:

```yaml
languages:
  versions:
    go: ['1.23', '1.24'] # Latest 2 stable versions
    python: ['3.13', '3.14'] # Latest 2 stable versions
    node: ['20', '22'] # LTS versions only
    rust: ['stable', 'stable-1'] # Latest + previous stable

build:
  platforms:
    - ubuntu-latest
    - macos-latest

testing:
  coverage:
    threshold: 80
    format: 'lcov'
```

### 2. Python Helper Scripts

**Why Python Over Bash**:

- **Type Safety**: Type hints catch errors at development time
- **Error Handling**: Structured exceptions vs exit codes
- **Testing**: pytest ecosystem provides excellent test infrastructure
- **Maintainability**: Readable code that junior engineers can understand
- **Cross-Platform**: Works identically on Linux and macOS

**Helper Structure**:

```
.github/workflows/scripts/
├── workflow_common.py          # Shared utilities (config loading, I/O)
├── ci_workflow.py              # CI-specific helpers
├── release_workflow.py         # Release-specific helpers
├── maintenance_workflow.py     # Maintenance helpers
├── docs_workflow.py            # Documentation helpers
└── automation_workflow.py      # Issue/PR automation helpers
```

**Coding Standards**: All helpers MUST follow:

- `.github/instructions/python.instructions.md` - Python style guide
- `.github/instructions/general-coding.instructions.md` - Universal standards
- `.github/instructions/test-generation.instructions.md` - Testing requirements

### 3. Idempotent and Independent Tasks

**Idempotency**: Running a task multiple times produces the same result.

Examples:

```python
# ✅ IDEMPOTENT: Checks before creating
def ensure_config_file():
    if not Path(".github/repository-config.yml").exists():
        create_default_config()
    return load_config()

# ❌ NOT IDEMPOTENT: Always appends
def add_config_line():
    with open("config.yml", "a") as f:
        f.write("new_setting: true\n")
```

**Independence**: Tasks can be executed in any order without breaking.

Design patterns:

- Each task includes dependency check at start
- Use file existence checks before creating
- Load config fresh in each task (don't rely on state)
- Clean up temporary files at task end

**Benefits for Parallel Agents**:

- Multiple copilot agents can work simultaneously
- Failed tasks can be retried safely
- No need for complex coordination logic
- Easy to parallelize in CI/CD

### 4. Version Support Policy

**Latest 2 Versions Only**:

| Language | Current Versions | Next Update              | Removal Date |
| -------- | ---------------- | ------------------------ | ------------ |
| Go       | 1.23, 1.24       | When 1.25 releases       | Drop 1.23    |
| Python   | 3.13, 3.14       | When 3.15 releases       | Drop 3.13    |
| Node.js  | 20 LTS, 22 LTS   | When 24 LTS releases     | Drop 20      |
| Rust     | stable, stable-1 | Monthly (stable updates) | Auto-managed |

**Rationale**:

- **Security**: Older versions miss critical patches
- **Maintenance Burden**: Testing N versions costs N times resources
- **Modern Features**: Can use latest language features
- **Industry Standard**: Most orgs support 2 versions max

See [Version Policy](version-policy.md) for complete details.

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Consumer Repository                                         │
│                                                             │
│  ┌────────────────────────────────────┐                   │
│  │ .github/repository-config.yml      │                   │
│  │  - Languages & versions            │                   │
│  │  - Build platforms                 │                   │
│  │  - Testing config                  │                   │
│  │  - Feature flags                   │                   │
│  └─────────────┬──────────────────────┘                   │
│                │                                           │
│                ▼                                           │
│  ┌────────────────────────────────────┐                   │
│  │ .github/workflows/ci.yml           │                   │
│  │  (delegates to ghcommon)           │                   │
│  └─────────────┬──────────────────────┘                   │
└────────────────┼──────────────────────────────────────────┘
                 │
                 │ uses: ghcommon/.github/workflows/reusable-ci.yml
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ ghcommon Repository                                         │
│                                                             │
│  ┌────────────────────────────────────┐                   │
│  │ .github/workflows/reusable-ci.yml  │                   │
│  │  - Load consumer config            │                   │
│  │  - Generate matrices               │                   │
│  │  - Execute test jobs               │                   │
│  └─────────────┬──────────────────────┘                   │
│                │                                           │
│                ▼                                           │
│  ┌────────────────────────────────────┐                   │
│  │ scripts/workflow_common.py         │                   │
│  │  - get_repository_config()         │                   │
│  │  - write_output()                  │                   │
│  │  - timed_operation()               │                   │
│  └────────────────────────────────────┘                   │
│                │                                           │
│                ▼                                           │
│  ┌────────────────────────────────────┐                   │
│  │ scripts/ci_workflow.py             │                   │
│  │  - generate_matrices()             │                   │
│  │  - go_setup() / go_test()          │                   │
│  │  - python_run_tests()              │                   │
│  │  - generate_ci_summary()           │                   │
│  └────────────────────────────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Config Loading**:

   ```
   Consumer Repo Config → GitHub Actions Context → Helper Script → Cache
   ```

2. **Matrix Generation**:

   ```
   Config Versions → Helper → JSON Matrix → Workflow Job Strategy
   ```

3. **Test Execution**:

   ```
   Job Matrix → Language-Specific Helper → Test Runner → Results → Summary
   ```

4. **Output Propagation**:
   ```
   Helper write_output() → GITHUB_OUTPUT → Job Outputs → Dependent Jobs
   ```

## Design Patterns

### Pattern 1: Config-First Defaults

Always check config first, fall back to sensible defaults:

```python
def get_coverage_threshold() -> int:
    """Get coverage threshold from config or environment, with fallback."""
    # Priority: env var > config > default
    if threshold := os.getenv("COVERAGE_THRESHOLD"):
        return int(threshold)

    config = get_repository_config()
    return config.get("testing", {}).get("coverage", {}).get("threshold", 80)
```

### Pattern 2: Structured Error Handling

Use custom exceptions with actionable messages:

```python
class WorkflowError(Exception):
    """Base exception with recovery hints."""
    def __init__(self, message: str, hint: str = "", docs_url: str = ""):
        self.message = message
        self.hint = hint
        self.docs_url = docs_url
        super().__init__(message)

# Usage
if not Path("go.mod").exists():
    raise WorkflowError(
        "No go.mod found",
        hint="Run: go mod init github.com/user/repo",
        docs_url="https://go.dev/doc/modules/gomod-ref"
    )
```

### Pattern 3: Idempotent File Operations

Always check before modifying:

```python
def ensure_file(path: Path, content: str) -> bool:
    """Create file if missing. Returns True if created, False if existed."""
    if path.exists():
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True
```

### Pattern 4: Timed Operations

Track performance for optimization:

```python
from contextlib import contextmanager
import time

@contextmanager
def timed_operation(name: str):
    """Time and report operation duration."""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        print(f"⏱️  {name} took {duration:.2f}s")
        append_summary(f"| {name} | {duration:.2f}s |\n")
```

### Pattern 5: Graceful Degradation

Continue with warnings vs failing:

```python
def load_optional_config(key: str, default: Any) -> Any:
    """Load config with fallback, warn but don't fail."""
    try:
        return get_config_value(key)
    except KeyError:
        print(f"⚠️  Config key '{key}' not found, using default: {default}")
        return default
```

## Testing Strategy

### Test Pyramid

```
    ┌─────────────────┐
    │   Integration   │  (10% of tests)
    │   Test Suites   │  - Full workflow runs
    └─────────────────┘  - Multi-language projects
          ▲
          │
    ┌─────────────────┐
    │  Helper Tests   │  (30% of tests)
    │  (pytest suite) │  - Mock GitHub env
    └─────────────────┘  - Test each command
          ▲
          │
    ┌─────────────────┐
    │   Unit Tests    │  (60% of tests)
    │  (pure Python)  │  - Config parsing
    └─────────────────┘  - Utility functions
```

### Test Independence

Each test must:

- Set up its own fixtures
- Clean up after itself
- Not rely on test execution order
- Use temporary directories

Example:

```python
def test_generate_matrices(tmp_path, monkeypatch):
    # Arrange: Create isolated environment
    config_file = tmp_path / "repository-config.yml"
    config_file.write_text("languages:\n  versions:\n    go: ['1.24']\n")
    monkeypatch.setenv("REPOSITORY_CONFIG", str(config_file))
    monkeypatch.chdir(tmp_path)

    # Act: Run helper
    result = generate_matrices()

    # Assert: Verify output
    assert "1.24" in result["go"]

    # Cleanup: Automatic via tmp_path
```

See [Testing Guide](implementation/testing-guide.md) for complete details.

## Security Considerations

### Secret Handling

**Never log secrets**:

```python
import re

def sanitize_log(message: str) -> str:
    """Remove potential secrets from log output."""
    # Mask tokens
    message = re.sub(r'ghp_[a-zA-Z0-9]{36}', '***GITHUB_TOKEN***', message)
    # Mask other patterns...
    return message

print(sanitize_log(output))
```

### Least Privilege

Workflows request minimal permissions:

```yaml
permissions:
  contents: read # Only what's needed
  pull-requests: write # For PR comments
  # NOT: write: all
```

### Dependency Pinning

Pin third-party actions to commit SHA:

```yaml
- uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab # v4.1.1
  # NOT: @v4 (mutable tag)
```

## Performance Optimization

### Config Caching

Load config once per workflow run:

```python
_CONFIG_CACHE: dict[str, Any] | None = None

def get_repository_config() -> dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    # Load and cache
    _CONFIG_CACHE = load_config_from_file()
    return _CONFIG_CACHE
```

### Matrix Optimization

Generate minimal matrices:

```python
# ❌ BAD: Every combination (4 jobs)
platforms = ["ubuntu", "macos"]
versions = ["1.23", "1.24"]
# Result: 2 × 2 = 4 jobs

# ✅ GOOD: Strategic subset (3 jobs)
matrix = [
    {"os": "ubuntu-latest", "go": "1.24"},    # Latest on Linux
    {"os": "ubuntu-latest", "go": "1.23"},    # Prev on Linux
    {"os": "macos-latest", "go": "1.24"},     # Latest on macOS
]
```

### Early Exit

Skip unnecessary work:

```python
def should_run_tests(language: str) -> bool:
    """Check if language files changed."""
    changed_files = os.getenv("CHANGED_FILES", "")
    patterns = {
        "go": [".go", "go.mod", "go.sum"],
        "python": [".py", "requirements.txt", "pyproject.toml"],
    }
    return any(pattern in changed_files for pattern in patterns[language])
```

## Migration Strategy

### Phase Rollout

Each phase is gated by feature flags:

```yaml
# In repository-config.yml
workflows:
  experimental:
    use_new_ci: false # Stable: old workflow
    use_new_release: false # Stable: old workflow
    use_config_matrices: false # Stable: hardcoded
```

Enable progressively:

1. **Alpha**: Enable in 1-2 test repos
2. **Beta**: Enable in 5-10 diverse repos
3. **GA**: Enable by default, opt-out available
4. **Deprecation**: Remove old workflows after 3 months

### Rollback Plan

Every phase includes rollback procedures:

1. **Immediate**: Revert commits
2. **Short-term**: Pin to previous workflow version
3. **Config**: Disable feature flags
4. **Communication**: Alert affected teams

See [Rollback Procedures](operations/rollback-procedures.md) for details.

## Monitoring and Observability

### Metrics to Track

1. **Performance**:
   - Workflow duration (p50, p95, p99)
   - Helper execution time
   - Queue time

2. **Reliability**:
   - Success rate by language/platform
   - Flaky test rate
   - Timeout frequency

3. **Adoption**:
   - Repos using new workflows
   - Feature flag enablement rate
   - Old workflow usage decline

### Alerting

Set up alerts for:

- Workflow failure rate > 5%
- Average duration increase > 20%
- Config validation errors
- Deprecated workflow usage after sunset date

See [Monitoring Guide](operations/monitoring.md) for implementation.

## Code Style Compliance

All code in this refactoring MUST comply with:

- **General**: `.github/instructions/general-coding.instructions.md`
  - File headers with path/version/GUID
  - Semantic versioning for changes
  - Idempotent operations
  - Check before doing

- **Python**: `.github/instructions/python.instructions.md`
  - Type hints on all functions
  - Docstrings with examples
  - pytest for testing
  - Black formatting

- **GitHub Actions**: `.github/instructions/github-actions.instructions.md`
  - Workflow naming conventions
  - Permission scoping
  - Action pinning

- **Testing**: `.github/instructions/test-generation.instructions.md`
  - Arrange-Act-Assert pattern
  - Test independence
  - Edge case coverage

## References

- [Original Audit](../workflow-optimization.md) - Initial analysis
- [Helper API Reference](reference/helper-api.md) - Function documentation
- [Config Schema](reference/config-schema.md) - Configuration specification
- [Workflow Catalog](reference/workflow-catalog.md) - All available workflows

---

**Last Updated**: 2025-10-12 **Document Owner**: Workflow Refactoring Team **Status**: Living
Document - Update as architecture evolves
