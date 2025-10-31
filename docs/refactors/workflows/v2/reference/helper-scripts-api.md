# Helper Scripts API Reference

**Version**: 1.0.0 **Last Updated**: 2025-10-15 **Status**: Complete

## Overview

This document provides comprehensive API documentation for all helper modules in the workflow v2
system. These modules provide the core functionality for CI/CD automation, release management,
documentation generation, maintenance tasks, and advanced automation features.

### Module Organization

The helper scripts are organized into 6 main modules:

1. **workflow_common.py**: Core utilities, validation, configuration loading
2. **ci_workflow.py**: CI automation, matrix generation, change detection
3. **release_workflow.py**: Release automation, version management, branch-aware releases
4. **docs_workflow.py**: Documentation generation, AST parsing, GitHub Pages
5. **maintenance_workflow.py**: Dependency updates, security scanning, stale detection
6. **automation_workflow.py**: GitHub Apps, caching, metrics, self-healing


## docs_workflow.py

### generate_api_docs(source_dirs, output_dir)

Generates Markdown documentation for helper modules and returns the generated file paths.

### generate_workflow_docs(workflows_dir, output)

Parses GitHub Actions workflow YAML definitions and writes a catalog in Markdown format.

### build_documentation(source_dirs, workflows_dir, output_root, version=None)

Builds a versioned documentation tree with API docs, workflow reference, search index, and versions manifest.

### CLI entrypoints

The script exposes `generate-api`, `generate-workflows`, and `build` subcommands for integration with GitHub workflows.


## maintenance_workflow.py

### collect_dependency_updates(pip_path, npm_path, cargo_path, go_path)

Parses dependency reports (pip, npm, cargo, go) and returns a list of `DependencyUpdate` instances.

### summarize_dependency_updates(updates)

Formats dependency updates into Markdown and appends them to the step summary.

### parse_stale_items(data, days)

Filters issue/PR data for items exceeding the stale threshold and returns structured `StaleItem` records.

### CLI commands

- `summarize-dependencies` — summarise JSON reports into Markdown and artifacts.
- `summarize-stale` — produce a summary table for stale issues or PRs.

### Design Principles

- **Type Safety**: All functions use type hints with Python 3.13+ syntax
- **Error Handling**: Comprehensive exception handling with custom error types
- **Logging**: Structured logging with configurable levels
- **Testing**: 100% test coverage requirement
- **Documentation**: Google Style Guide docstrings
- **Security**: Input validation, secrets handling, rate limiting

---

## 1. workflow_common.py

Core utilities shared across all workflow modules.

### 1.1 Configuration Management

#### load_config()

Load and validate workflow configuration from .github/workflow-versions.yml.

```python
def load_config(
    config_path: str = ".github/workflow-versions.yml"
) -> dict[str, Any]:
    """Load and validate workflow configuration.

    Args:
        config_path: Path to workflow-versions.yml file.
            Defaults to .github/workflow-versions.yml.

    Returns:
        Validated configuration dictionary with all required fields.

    Raises:
        ConfigError: If config file missing or invalid schema.
        ValidationError: If config values fail validation.

    Example:
        >>> config = load_config()
        >>> print(config['version'])
        '1.0.0'
        >>> print(config['use_workflow_v2'])
        True
    """
```

**Implementation Notes**:

- Validates against JSON Schema (see config-schema.md)
- Caches config for performance
- Supports environment variable overrides
- Logs validation errors with helpful messages

#### validate_config()

Validate configuration dictionary against schema.

```python
def validate_config(config: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate configuration against schema.

    Args:
        config: Configuration dictionary to validate.

    Returns:
        Tuple of (is_valid, error_messages).
        is_valid is True if config passes all validation.
        error_messages is list of human-readable error descriptions.

    Example:
        >>> config = {'version': '1.0.0'}
        >>> is_valid, errors = validate_config(config)
        >>> if not is_valid:
        ...     for error in errors:
        ...         print(f"Error: {error}")
    """
```

**Validation Rules**:

- Required fields: version, use_workflow_v2
- Version format: Semantic versioning (X.Y.Z)
- Language versions: Match supported patterns
- Feature flags: Boolean values only
- Branch policies: Valid date formats (YYYY-MM-DD)

#### get_branch_config()

Get branch-specific configuration.

```python
def get_branch_config(
    config: dict[str, Any],
    branch_name: str
) -> dict[str, Any]:
    """Get configuration for specific branch.

    Args:
        config: Full workflow configuration.
        branch_name: Branch name (e.g., 'main', 'stable-1-go-1.23').

    Returns:
        Branch-specific configuration with version overrides.
        Falls back to main branch config if branch not found.

    Example:
        >>> config = load_config()
        >>> branch_config = get_branch_config(config, 'stable-1-go-1.23')
        >>> print(branch_config['go_version'])
        '1.23'
    """
```

**Branch Resolution**:

1. Check branch_policies for exact match
2. Parse branch name for pattern matching
3. Fall back to main branch versions
4. Apply locked/EOL/work_stopped status

### 1.2 Version Management

#### parse_version()

Parse semantic version string.

```python
def parse_version(version_str: str) -> tuple[int, int, int]:
    """Parse semantic version string into components.

    Args:
        version_str: Version string (e.g., '1.2.3', 'v1.2.3').

    Returns:
        Tuple of (major, minor, patch) integers.

    Raises:
        ValueError: If version string format invalid.

    Example:
        >>> major, minor, patch = parse_version('1.23.5')
        >>> print(f"{major}.{minor}.{patch}")
        1.23.5
    """
```

#### bump_version()

Bump version number by specified level.

```python
def bump_version(
    version_str: str,
    level: Literal["major", "minor", "patch"]
) -> str:
    """Bump version by specified level.

    Args:
        version_str: Current version string.
        level: Version level to bump ('major', 'minor', or 'patch').

    Returns:
        New version string with bumped component.

    Example:
        >>> new_version = bump_version('1.2.3', 'minor')
        >>> print(new_version)
        '1.3.0'
    """
```

**Bump Rules**:

- major: X.0.0 (resets minor and patch)
- minor: X.Y.0 (resets patch)
- patch: X.Y.Z (increments patch)

#### compare_versions()

Compare two semantic versions.

```python
def compare_versions(v1: str, v2: str) -> int:
    """Compare two semantic versions.

    Args:
        v1: First version string.
        v2: Second version string.

    Returns:
        -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2.

    Example:
        >>> result = compare_versions('1.2.3', '1.3.0')
        >>> print(result)
        -1
    """
```

### 1.3 Git Operations

#### get_current_branch()

Get current Git branch name.

```python
def get_current_branch() -> str:
    """Get current Git branch name.

    Returns:
        Current branch name (e.g., 'main', 'stable-1-go-1.23').

    Raises:
        GitError: If not in Git repository or Git command fails.

    Example:
        >>> branch = get_current_branch()
        >>> print(f"On branch: {branch}")
    """
```

#### get_latest_tag()

Get most recent Git tag.

```python
def get_latest_tag(prefix: str = "") -> str | None:
    """Get most recent Git tag with optional prefix.

    Args:
        prefix: Tag prefix filter (e.g., 'v', 'release-').
            Empty string returns all tags.

    Returns:
        Latest tag name, or None if no tags found.

    Example:
        >>> tag = get_latest_tag(prefix='v')
        >>> print(f"Latest version: {tag}")
    """
```

#### create_tag()

Create and push Git tag.

```python
def create_tag(
    tag_name: str,
    message: str,
    push: bool = True
) -> bool:
    """Create and optionally push Git tag.

    Args:
        tag_name: Tag name to create.
        message: Tag annotation message.
        push: Whether to push tag to remote. Defaults to True.

    Returns:
        True if tag created successfully.

    Raises:
        GitError: If tag creation fails.

    Example:
        >>> success = create_tag('v1.2.3', 'Release version 1.2.3')
        >>> if success:
        ...     print("Tag created and pushed")
    """
```

### 1.4 Error Handling

#### Custom Exceptions

```python
class WorkflowError(Exception):
    """Base exception for workflow errors."""
    pass

class ConfigError(WorkflowError):
    """Configuration file errors."""
    pass

class ValidationError(WorkflowError):
    """Configuration validation errors."""
    pass

class GitError(WorkflowError):
    """Git operation errors."""
    pass

class NetworkError(WorkflowError):
    """Network/API call errors."""
    pass
```

#### error_handler()

Decorator for consistent error handling.

```python
def error_handler(func: Callable) -> Callable:
    """Decorator for consistent error handling.

    Wraps functions to catch exceptions, log errors,
    and provide consistent error reporting.

    Example:
        >>> @error_handler
        ... def risky_operation():
        ...     # Operation that might fail
        ...     pass
    """
```

### 1.5 Logging

#### setup_logging()

Configure logging for workflow scripts.

```python
def setup_logging(
    level: str = "INFO",
    log_file: str | None = None
) -> logging.Logger:
    """Setup structured logging.

    Args:
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR').
        log_file: Optional log file path. If None, logs to console.

    Returns:
        Configured logger instance.

    Example:
        >>> logger = setup_logging(level='DEBUG')
        >>> logger.info("Operation started")
    """
```

**Log Format**:

```text
[2025-10-15 10:30:45] INFO [module.function:42] Message here
```

---

## 2. ci_workflow.py

CI automation utilities for matrix generation and change detection.

### 2.1 Matrix Generation

#### generate_test_matrix()

Generate test matrix for CI workflow.

```python
def generate_test_matrix(
    config: dict[str, Any],
    branch_name: str,
    changed_files: list[str]
) -> dict[str, list[dict[str, str]]]:
    """Generate test matrix based on configuration and changes.

    Args:
        config: Workflow configuration from load_config().
        branch_name: Current branch name.
        changed_files: List of changed file paths.

    Returns:
        Dictionary with language keys and matrix configurations.
        Format: {'go': [{'version': '1.23', 'os': 'ubuntu-latest'}, ...]}

    Example:
        >>> config = load_config()
        >>> changed = ['main.go', 'internal/auth/handler.go']
        >>> matrix = generate_test_matrix(config, 'main', changed)
        >>> for lang, configs in matrix.items():
        ...     print(f"{lang}: {len(configs)} configurations")
    """
```

**Matrix Structure**:

- **Languages**: Go, Python, Node.js, Rust
- **Versions**: From config (branch-aware)
- **Platforms**: ubuntu-latest, macos-latest (NO WINDOWS)
- **Optimization**: Skip if no relevant file changes

#### get_language_matrix()

Get matrix for specific language.

```python
def get_language_matrix(
    config: dict[str, Any],
    language: Literal["go", "python", "node", "rust"]
) -> list[dict[str, str]]:
    """Get test matrix for specific language.

    Args:
        config: Workflow configuration.
        language: Language identifier.

    Returns:
        List of test configurations for the language.

    Example:
        >>> config = load_config()
        >>> go_matrix = get_language_matrix(config, 'go')
        >>> for item in go_matrix:
        ...     print(f"Go {item['version']} on {item['os']}")
    """
```

### 2.2 Change Detection

#### detect_changes()

Detect changed files since last commit.

```python
def detect_changes(
    base_ref: str = "HEAD^",
    head_ref: str = "HEAD"
) -> list[str]:
    """Detect changed files between Git refs.

    Args:
        base_ref: Base reference (default: previous commit).
        head_ref: Head reference (default: current commit).

    Returns:
        List of changed file paths relative to repo root.

    Example:
        >>> changed = detect_changes('origin/main', 'HEAD')
        >>> print(f"Changed files: {len(changed)}")
        >>> for file in changed:
        ...     print(f"  - {file}")
    """
```

#### categorize_changes()

Categorize changes by type.

```python
def categorize_changes(
    file_paths: list[str]
) -> dict[str, list[str]]:
    """Categorize file changes by type.

    Args:
        file_paths: List of changed file paths.

    Returns:
        Dictionary mapping categories to file lists.
        Categories: 'go', 'python', 'node', 'rust', 'docker',
                   'workflows', 'docs', 'config', 'other'.

    Example:
        >>> changed = detect_changes()
        >>> categories = categorize_changes(changed)
        >>> if categories['go']:
        ...     print(f"Go files changed: {len(categories['go'])}")
    """
```

**Category Rules**:

- **go**: `*.go`, `go.mod`, `go.sum`
- **python**: `*.py`, `requirements.txt`, `pyproject.toml`
- **node**: `*.js`, `*.ts`, `package.json`, `package-lock.json`
- **rust**: `*.rs`, `Cargo.toml`, `Cargo.lock`
- **docker**: `Dockerfile`, `docker-compose.yml`, `.dockerignore`
- **workflows**: `.github/workflows/*.yml`
- **docs**: `*.md`, `docs/**/*`
- **config**: `*.json`, `*.yaml`, `*.toml`, `.github/**/*`

#### should_run_tests()

Determine if tests should run for language.

```python
def should_run_tests(
    language: str,
    changed_files: list[str],
    force_run: bool = False
) -> bool:
    """Determine if tests should run for language.

    Args:
        language: Language identifier.
        changed_files: List of changed file paths.
        force_run: Force tests to run regardless of changes.

    Returns:
        True if tests should run for this language.

    Example:
        >>> changed = detect_changes()
        >>> if should_run_tests('go', changed):
        ...     print("Running Go tests")
    """
```

### 2.3 Linting Integration

#### run_super_linter()

Run Super Linter with workflow v2 configuration.

```python
def run_super_linter(
    config: dict[str, Any],
    changed_files: list[str] | None = None,
    fix: bool = False
) -> tuple[bool, list[str]]:
    """Run Super Linter with v2 configuration.

    Args:
        config: Workflow configuration.
        changed_files: Optional list of files to lint. If None, lints all.
        fix: Whether to auto-fix issues (PR mode).

    Returns:
        Tuple of (success, error_messages).

    Example:
        >>> config = load_config()
        >>> success, errors = run_super_linter(config, fix=True)
        >>> if not success:
        ...     for error in errors:
        ...         print(f"Lint error: {error}")
    """
```

---

## 3. release_workflow.py

Release automation with branch-aware version targeting.

### 3.1 Version Detection

#### detect_version_bump()

Detect version bump type from commits.

```python
def detect_version_bump(
    commits: list[str] | None = None
) -> Literal["major", "minor", "patch"]:
    """Detect version bump type from commit messages.

    Analyzes commit messages using Conventional Commits format
    to determine appropriate version bump.

    Args:
        commits: List of commit messages. If None, uses git log
                since last tag.

    Returns:
        Version bump type: 'major', 'minor', or 'patch'.

    Example:
        >>> bump_type = detect_version_bump()
        >>> print(f"Next version bump: {bump_type}")
    """
```

**Detection Rules**:

- **major**: `BREAKING CHANGE:` in commit body or footer
- **minor**: `feat:` or `feat(scope):` commit type
- **patch**: `fix:`, `chore:`, `docs:`, etc.

#### get_next_version()

Calculate next version number.

```python
def get_next_version(
    current_version: str,
    bump_type: Literal["major", "minor", "patch"]
) -> str:
    """Calculate next version based on bump type.

    Args:
        current_version: Current version string.
        bump_type: Type of version bump.

    Returns:
        Next version string.

    Example:
        >>> current = get_latest_tag(prefix='v').lstrip('v')
        >>> bump = detect_version_bump()
        >>> next_ver = get_next_version(current, bump)
        >>> print(f"Release version: {next_ver}")
    """
```

### 3.2 Branch-Aware Releases

#### get_release_config()

Get branch-specific release configuration.

```python
def get_release_config(
    config: dict[str, Any],
    branch_name: str
) -> dict[str, Any]:
    """Get release configuration for branch.

    Args:
        config: Workflow configuration.
        branch_name: Branch name to release from.

    Returns:
        Release configuration with version targets and policies.

    Example:
        >>> config = load_config()
        >>> release_config = get_release_config(config, 'stable-1-go-1.23')
        >>> print(f"Go version: {release_config['go_version']}")
        >>> print(f"Locked: {release_config.get('locked', False)}")
    """
```

**Release Configuration**:

- Language versions for build
- Branch policy status (locked, EOL, work_stopped)
- Tag prefix (e.g., 'v', 'stable-1-')
- Release notes template

#### create_release()

Create GitHub release.

```python
def create_release(
    tag_name: str,
    release_name: str,
    body: str,
    draft: bool = False,
    prerelease: bool = False,
    assets: list[str] | None = None
) -> dict[str, Any]:
    """Create GitHub release.

    Args:
        tag_name: Git tag for release.
        release_name: Human-readable release name.
        body: Release notes in Markdown format.
        draft: Create as draft release.
        prerelease: Mark as prerelease.
        assets: List of file paths to upload as assets.

    Returns:
        Release information dictionary.

    Raises:
        NetworkError: If GitHub API call fails.

    Example:
        >>> tag = 'v1.2.3'
        >>> notes = generate_release_notes(tag)
        >>> release = create_release(
        ...     tag,
        ...     'Version 1.2.3',
        ...     notes,
        ...     assets=['dist/binary']
        ... )
        >>> print(f"Release URL: {release['html_url']}")
    """
```

### 3.3 Release Notes Generation

#### generate_release_notes()

Generate release notes from commits.

```python
def generate_release_notes(
    from_ref: str,
    to_ref: str = "HEAD",
    format: Literal["markdown", "json"] = "markdown"
) -> str | dict[str, Any]:
    """Generate release notes from commit history.

    Args:
        from_ref: Starting reference (previous release tag).
        to_ref: Ending reference (default: HEAD).
        format: Output format ('markdown' or 'json').

    Returns:
        Formatted release notes string or structured dict.

    Example:
        >>> last_tag = get_latest_tag(prefix='v')
        >>> notes = generate_release_notes(last_tag)
        >>> print(notes)
    """
```

**Release Notes Format**:

```markdown
## 🚀 Features

- feat(api): Add new endpoint (#123)
- feat(ui): Improve dashboard layout (#124)

## 🐛 Bug Fixes

- fix(auth): Resolve token expiration issue (#125)
- fix(db): Fix connection pool leak (#126)

## 📚 Documentation

- docs: Update API reference (#127)

## 🔧 Chores

- chore(deps): Update dependencies (#128)
```

### 3.4 Asset Building

#### build_release_assets()

Build release assets for all platforms.

```python
def build_release_assets(
    config: dict[str, Any],
    language: str,
    output_dir: str = "dist"
) -> list[str]:
    """Build release assets for language.

    Args:
        config: Workflow configuration.
        language: Language to build ('go', 'rust', etc.).
        output_dir: Output directory for built assets.

    Returns:
        List of built asset file paths.

    Example:
        >>> config = load_config()
        >>> assets = build_release_assets(config, 'go')
        >>> for asset in assets:
        ...     print(f"Built: {asset}")
    """
```

**Build Matrix**:

- **Go**: linux/amd64, linux/arm64, darwin/amd64, darwin/arm64
- **Rust**: x86_64-unknown-linux-gnu, aarch64-unknown-linux-gnu, x86_64-apple-darwin,
  aarch64-apple-darwin
- **NO WINDOWS**: No Windows builds

---

## 4. docs_workflow.py

Documentation automation with AST-based generation.

### 4.1 AST Parsing

#### parse_go_file()

Parse Go source file into AST.

```python
def parse_go_file(file_path: str) -> dict[str, Any]:
    """Parse Go file and extract documentation.

    Args:
        file_path: Path to Go source file.

    Returns:
        Dictionary with parsed structures:
        - 'package': Package name
        - 'imports': List of imports
        - 'types': List of type definitions
        - 'functions': List of function definitions
        - 'methods': List of method definitions

    Raises:
        FileNotFoundError: If file doesn't exist.
        ParseError: If Go syntax invalid.

    Example:
        >>> doc = parse_go_file('internal/auth/handler.go')
        >>> print(f"Package: {doc['package']}")
        >>> for func in doc['functions']:
        ...     print(f"Function: {func['name']}")
    """
```

**Extracted Information**:

- Function signatures with parameters and returns
- Type definitions (structs, interfaces, aliases)
- Method receivers and signatures
- Doc comments in Markdown format
- Source code locations (file, line numbers)

#### extract_doc_comments()

Extract documentation comments.

```python
def extract_doc_comments(
    ast_node: dict[str, Any]
) -> str:
    """Extract and format doc comments from AST node.

    Args:
        ast_node: AST node dictionary from parse_go_file().

    Returns:
        Formatted documentation string in Markdown.

    Example:
        >>> doc = parse_go_file('handler.go')
        >>> for func in doc['functions']:
        ...     comment = extract_doc_comments(func)
        ...     print(f"# {func['name']}\n{comment}")
    """
```

### 4.2 Documentation Generation

#### generate_api_docs()

Generate API documentation for package.

```python
def generate_api_docs(
    package_path: str,
    output_file: str,
    include_private: bool = False
) -> bool:
    """Generate API documentation for Go package.

    Args:
        package_path: Path to Go package directory.
        output_file: Output Markdown file path.
        include_private: Include unexported symbols.

    Returns:
        True if documentation generated successfully.

    Example:
        >>> success = generate_api_docs(
        ...     'internal/auth',
        ...     'docs/api/auth.md'
        ... )
        >>> if success:
        ...     print("API docs generated")
    """
```

**Generated Documentation Structure**:

1. Package overview
2. Table of contents
3. Constants and variables
4. Type definitions
5. Function documentation
6. Method documentation
7. Examples (if found in tests)

#### generate_module_docs()

Generate documentation for entire module.

```python
def generate_module_docs(
    module_path: str,
    output_dir: str,
    exclude_patterns: list[str] | None = None
) -> dict[str, str]:
    """Generate documentation for entire module.

    Args:
        module_path: Root path of Go module.
        output_dir: Output directory for generated docs.
        exclude_patterns: Glob patterns to exclude.

    Returns:
        Dictionary mapping package paths to output files.

    Example:
        >>> docs = generate_module_docs('.', 'docs/api')
        >>> for pkg, doc_file in docs.items():
        ...     print(f"{pkg} -> {doc_file}")
    """
```

### 4.3 Cross-Reference Detection

#### detect_cross_references()

Detect cross-references between packages.

```python
def detect_cross_references(
    module_path: str
) -> dict[str, list[str]]:
    """Detect package cross-references.

    Args:
        module_path: Root path of Go module.

    Returns:
        Dictionary mapping packages to their dependencies.

    Example:
        >>> refs = detect_cross_references('.')
        >>> for pkg, deps in refs.items():
        ...     print(f"{pkg} depends on: {', '.join(deps)}")
    """
```

#### generate_dependency_graph()

Generate dependency graph visualization.

```python
def generate_dependency_graph(
    module_path: str,
    output_file: str,
    format: Literal["mermaid", "dot", "svg"] = "mermaid"
) -> bool:
    """Generate package dependency graph.

    Args:
        module_path: Root path of Go module.
        output_file: Output file path.
        format: Output format (mermaid, dot, or svg).

    Returns:
        True if graph generated successfully.

    Example:
        >>> success = generate_dependency_graph(
        ...     '.',
        ...     'docs/architecture/dependencies.md',
        ...     format='mermaid'
        ... )
    """
```

### 4.4 GitHub Pages Deployment

#### build_docs_site()

Build documentation website.

```python
def build_docs_site(
    docs_dir: str,
    output_dir: str,
    config: dict[str, Any]
) -> bool:
    """Build documentation website for GitHub Pages.

    Args:
        docs_dir: Source documentation directory.
        output_dir: Output directory (usually _site).
        config: Site configuration (title, versions, theme).

    Returns:
        True if site built successfully.

    Example:
        >>> site_config = {
        ...     'title': 'Project Documentation',
        ...     'versions': ['1.23', '1.24'],
        ...     'theme': 'just-the-docs'
        ... }
        >>> success = build_docs_site('docs', '_site', site_config)
    """
```

---

## 5. maintenance_workflow.py

Automated maintenance tasks for dependency updates and security.

### 5.1 Dependency Management

#### check_outdated_dependencies()

Check for outdated dependencies.

```python
def check_outdated_dependencies(
    language: str,
    project_path: str = "."
) -> dict[str, dict[str, str]]:
    """Check for outdated dependencies.

    Args:
        language: Language identifier ('go', 'python', 'node', 'rust').
        project_path: Path to project root.

    Returns:
        Dictionary mapping package names to version info:
        {'package': {'current': '1.0.0', 'latest': '1.2.0'}}

    Example:
        >>> outdated = check_outdated_dependencies('go')
        >>> for pkg, versions in outdated.items():
        ...     print(f"{pkg}: {versions['current']} -> {versions['latest']}")
    """
```

**Language-Specific Commands**:

- **Go**: `go list -u -m all`
- **Python**: `pip list --outdated`
- **Node**: `npm outdated`
- **Rust**: `cargo outdated`

#### update_dependencies()

Update dependencies to latest versions.

```python
def update_dependencies(
    language: str,
    packages: list[str] | None = None,
    major_updates: bool = False,
    create_pr: bool = True
) -> dict[str, Any]:
    """Update dependencies.

    Args:
        language: Language identifier.
        packages: Specific packages to update. If None, updates all.
        major_updates: Allow major version updates.
        create_pr: Create pull request for updates.

    Returns:
        Update summary with changed packages and PR URL.

    Example:
        >>> result = update_dependencies(
        ...     'go',
        ...     packages=['github.com/pkg/errors'],
        ...     create_pr=True
        ... )
        >>> print(f"PR created: {result['pr_url']}")
    """
```

### 5.2 Security Scanning

#### run_security_scan()

Run security vulnerability scan.

```python
def run_security_scan(
    language: str,
    project_path: str = ".",
    severity_threshold: Literal["low", "medium", "high", "critical"] = "medium"
) -> dict[str, Any]:
    """Run security vulnerability scan.

    Args:
        language: Language identifier.
        project_path: Path to project root.
        severity_threshold: Minimum severity to report.

    Returns:
        Scan results with vulnerabilities found.

    Example:
        >>> results = run_security_scan('go', severity_threshold='high')
        >>> if results['vulnerabilities']:
        ...     print(f"Found {len(results['vulnerabilities'])} issues")
    """
```

**Scanning Tools**:

- **Go**: `govulncheck`
- **Python**: `pip-audit` or `safety`
- **Node**: `npm audit`
- **Rust**: `cargo audit`

#### create_security_issue()

Create GitHub issue for vulnerability.

```python
def create_security_issue(
    vulnerability: dict[str, Any],
    assign_to: str | None = None
) -> dict[str, Any]:
    """Create GitHub issue for security vulnerability.

    Args:
        vulnerability: Vulnerability information from scan.
        assign_to: GitHub username to assign issue to.

    Returns:
        Created issue information.

    Example:
        >>> vuln = {
        ...     'package': 'github.com/pkg/errors',
        ...     'severity': 'high',
        ...     'description': 'CVE-2024-1234'
        ... }
        >>> issue = create_security_issue(vuln, assign_to='security-team')
    """
```

### 5.3 Stale Detection

#### find_stale_issues()

Find stale issues and PRs.

```python
def find_stale_issues(
    days_inactive: int = 30,
    exempt_labels: list[str] | None = None
) -> dict[str, list[dict[str, Any]]]:
    """Find stale issues and pull requests.

    Args:
        days_inactive: Number of days without activity to consider stale.
        exempt_labels: Labels that exempt from stale detection.

    Returns:
        Dictionary with 'issues' and 'pull_requests' lists.

    Example:
        >>> stale = find_stale_issues(
        ...     days_inactive=60,
        ...     exempt_labels=['keep-open', 'in-progress']
        ... )
        >>> print(f"Stale issues: {len(stale['issues'])}")
    """
```

#### mark_as_stale()

Mark issue or PR as stale.

```python
def mark_as_stale(
    item_type: Literal["issue", "pull_request"],
    item_number: int,
    message: str | None = None
) -> bool:
    """Mark issue or PR as stale.

    Args:
        item_type: Type of item to mark.
        item_number: Issue or PR number.
        message: Optional custom stale message.

    Returns:
        True if marked successfully.

    Example:
        >>> success = mark_as_stale(
        ...     'issue',
        ...     123,
        ...     message='This issue has been inactive for 30 days.'
        ... )
    """
```

---

## 6. automation_workflow.py

Advanced automation features: GitHub Apps, caching, metrics.

### 6.1 GitHub Apps Integration

#### authenticate_github_app()

Authenticate as GitHub App.

```python
def authenticate_github_app(
    app_id: str,
    private_key: str,
    installation_id: str
) -> str:
    """Authenticate as GitHub App and get installation token.

    Args:
        app_id: GitHub App ID.
        private_key: App private key (PEM format).
        installation_id: Installation ID for repository.

    Returns:
        Installation access token.

    Raises:
        AuthenticationError: If authentication fails.

    Example:
        >>> token = authenticate_github_app(
        ...     os.getenv('GITHUB_APP_ID'),
        ...     os.getenv('GITHUB_APP_PRIVATE_KEY'),
        ...     os.getenv('GITHUB_APP_INSTALLATION_ID')
        ... )
        >>> # Use token for API calls
    """
```

#### get_app_permissions()

Get GitHub App permissions.

```python
def get_app_permissions(app_id: str) -> dict[str, str]:
    """Get GitHub App permissions configuration.

    Args:
        app_id: GitHub App ID.

    Returns:
        Dictionary of permissions and access levels.

    Example:
        >>> perms = get_app_permissions(app_id)
        >>> print(f"Issues: {perms.get('issues', 'none')}")
    """
```

### 6.2 Intelligent Caching

#### get_cache_key()

Generate cache key for workflow.

```python
def get_cache_key(
    language: str,
    version: str,
    dependency_files: list[str]
) -> str:
    """Generate cache key for dependency cache.

    Args:
        language: Language identifier.
        version: Language version.
        dependency_files: Paths to dependency lock files.

    Returns:
        Cache key string.

    Example:
        >>> key = get_cache_key(
        ...     'go',
        ...     '1.23',
        ...     ['go.mod', 'go.sum']
        ... )
        >>> print(f"Cache key: {key}")
    """
```

#### should_invalidate_cache()

Determine if cache should be invalidated.

```python
def should_invalidate_cache(
    cache_key: str,
    changed_files: list[str]
) -> bool:
    """Determine if cache should be invalidated.

    Args:
        cache_key: Current cache key.
        changed_files: List of changed files.

    Returns:
        True if cache should be invalidated.

    Example:
        >>> if should_invalidate_cache(key, changed):
        ...     print("Cache will be refreshed")
    """
```

### 6.3 Workflow Metrics

#### collect_workflow_metrics()

Collect workflow execution metrics.

```python
def collect_workflow_metrics(
    workflow_name: str,
    run_id: str
) -> dict[str, Any]:
    """Collect metrics for workflow run.

    Args:
        workflow_name: Name of workflow.
        run_id: Workflow run ID.

    Returns:
        Dictionary with metrics:
        - duration: Total execution time in seconds
        - jobs: List of job metrics
        - status: Workflow status
        - cost: Estimated compute cost

    Example:
        >>> metrics = collect_workflow_metrics('CI', '123456')
        >>> print(f"Duration: {metrics['duration']}s")
        >>> print(f"Cost: ${metrics['cost']:.2f}")
    """
```

#### generate_metrics_report()

Generate metrics report.

```python
def generate_metrics_report(
    start_date: str,
    end_date: str,
    output_format: Literal["json", "html", "markdown"] = "markdown"
) -> str:
    """Generate workflow metrics report.

    Args:
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        output_format: Report format.

    Returns:
        Formatted metrics report.

    Example:
        >>> report = generate_metrics_report(
        ...     '2025-10-01',
        ...     '2025-10-15',
        ...     format='markdown'
        ... )
        >>> with open('metrics.md', 'w') as f:
        ...     f.write(report)
    """
```

### 6.4 Self-Healing

#### detect_workflow_failures()

Detect recurring workflow failures.

```python
def detect_workflow_failures(
    workflow_name: str,
    lookback_days: int = 7,
    failure_threshold: int = 3
) -> list[dict[str, Any]]:
    """Detect recurring workflow failures.

    Args:
        workflow_name: Name of workflow to analyze.
        lookback_days: Number of days to analyze.
        failure_threshold: Minimum failures to trigger detection.

    Returns:
        List of detected failure patterns.

    Example:
        >>> failures = detect_workflow_failures('CI', lookback_days=7)
        >>> for failure in failures:
        ...     print(f"Pattern: {failure['pattern']}")
        ...     print(f"Count: {failure['count']}")
    """
```

#### suggest_fixes()

Suggest fixes for workflow failures.

```python
def suggest_fixes(
    failure_pattern: dict[str, Any]
) -> list[dict[str, str]]:
    """Suggest fixes for workflow failure pattern.

    Args:
        failure_pattern: Failure pattern from detect_workflow_failures().

    Returns:
        List of suggested fixes with descriptions and actions.

    Example:
        >>> failures = detect_workflow_failures('CI')
        >>> for failure in failures:
        ...     fixes = suggest_fixes(failure)
        ...     for fix in fixes:
        ...         print(f"Fix: {fix['description']}")
        ...         print(f"Action: {fix['action']}")
    """
```

---

## Error Handling Patterns

### Standard Error Response

All functions follow consistent error handling:

```python
try:
    result = operation()
    return result
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise WorkflowError(f"Detailed message: {e}") from e
```

### Validation Pattern

```python
def validate_input(value: Any, rules: dict[str, Any]) -> bool:
    """Validate input against rules.

    Args:
        value: Value to validate.
        rules: Validation rules dictionary.

    Returns:
        True if valid.

    Raises:
        ValidationError: If validation fails.
    """
    if not meets_requirements(value, rules):
        raise ValidationError(
            f"Validation failed: {get_error_message(value, rules)}"
        )
    return True
```

---

## Integration Examples

### Example 1: Complete CI Workflow

```python
#!/usr/bin/env python3
"""Complete CI workflow automation."""

import sys
from pathlib import Path

from workflow_common import load_config, setup_logging
from ci_workflow import (
    detect_changes,
    categorize_changes,
    generate_test_matrix,
    should_run_tests,
)

def main() -> int:
    """Run CI workflow automation."""
    logger = setup_logging(level='INFO')

    try:
        # Load configuration
        config = load_config()
        logger.info(f"Loaded config version {config['version']}")

        # Detect changes
        changed = detect_changes('origin/main', 'HEAD')
        logger.info(f"Detected {len(changed)} changed files")

        # Categorize changes
        categories = categorize_changes(changed)
        for category, files in categories.items():
            if files:
                logger.info(f"{category}: {len(files)} files")

        # Generate test matrix
        branch = get_current_branch()
        matrix = generate_test_matrix(config, branch, changed)

        # Run tests for changed languages
        for language, configs in matrix.items():
            if should_run_tests(language, changed):
                logger.info(f"Running {language} tests: {len(configs)} configs")
                # Run tests...

        return 0

    except Exception as e:
        logger.error(f"CI workflow failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

### Example 2: Automated Release

```python
#!/usr/bin/env python3
"""Automated release workflow."""

from workflow_common import load_config, setup_logging, get_current_branch
from release_workflow import (
    detect_version_bump,
    get_next_version,
    get_release_config,
    generate_release_notes,
    build_release_assets,
    create_release,
)

def main() -> int:
    """Run release workflow."""
    logger = setup_logging(level='INFO')

    try:
        # Load config and get branch info
        config = load_config()
        branch = get_current_branch()
        release_config = get_release_config(config, branch)

        # Check if releases allowed
        if release_config.get('locked'):
            logger.warning(f"Branch {branch} is locked")
            return 0

        # Detect version bump
        bump_type = detect_version_bump()
        current_version = get_latest_tag(prefix='v').lstrip('v')
        next_version = get_next_version(current_version, bump_type)
        tag = f"v{next_version}"

        logger.info(f"Releasing {tag} ({bump_type} bump)")

        # Generate release notes
        notes = generate_release_notes(f"v{current_version}", 'HEAD')

        # Build assets
        assets = []
        for language in ['go', 'rust']:
            if f"{language}_version" in release_config:
                built = build_release_assets(config, language)
                assets.extend(built)

        # Create release
        release = create_release(
            tag,
            f"Version {next_version}",
            notes,
            assets=assets
        )

        logger.info(f"Release created: {release['html_url']}")
        return 0

    except Exception as e:
        logger.error(f"Release failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

### Example 3: Documentation Generation

```python
#!/usr/bin/env python3
"""Generate API documentation."""

from workflow_common import load_config, setup_logging
from docs_workflow import (
    generate_module_docs,
    detect_cross_references,
    generate_dependency_graph,
    build_docs_site,
)

def main() -> int:
    """Generate documentation."""
    logger = setup_logging(level='INFO')

    try:
        config = load_config()

        # Generate API docs
        logger.info("Generating API documentation")
        docs = generate_module_docs(
            '.',
            'docs/api',
            exclude_patterns=['*_test.go', 'vendor/*']
        )
        logger.info(f"Generated docs for {len(docs)} packages")

        # Generate dependency graph
        logger.info("Generating dependency graph")
        generate_dependency_graph(
            '.',
            'docs/architecture/dependencies.md',
            format='mermaid'
        )

        # Build docs site
        logger.info("Building documentation site")
        site_config = {
            'title': 'API Documentation',
            'versions': ['1.23', '1.24', '1.25'],
            'theme': 'just-the-docs',
        }
        build_docs_site('docs', '_site', site_config)

        logger.info("Documentation generation complete")
        return 0

    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

---

## Testing Guidelines

### Unit Testing

All helper functions require unit tests:

```python
def test_parse_version():
    """Test version parsing."""
    major, minor, patch = parse_version('1.23.5')
    assert major == 1
    assert minor == 23
    assert patch == 5

    # Test with 'v' prefix
    major, minor, patch = parse_version('v2.0.1')
    assert major == 2
    assert minor == 0
    assert patch == 1
```

### Integration Testing

Test helper integration:

```python
def test_ci_workflow_integration():
    """Test complete CI workflow."""
    config = load_config()
    changed = detect_changes()
    matrix = generate_test_matrix(config, 'main', changed)

    assert 'go' in matrix or 'python' in matrix
    for language, configs in matrix.items():
        assert len(configs) > 0
        for item in configs:
            assert 'version' in item
            assert 'os' in item
```

### Mock GitHub API

Use mocks for GitHub API calls:

```python
@patch('automation_workflow.github_api_call')
def test_create_release(mock_api):
    """Test release creation."""
    mock_api.return_value = {'id': 123, 'html_url': 'https://...'}

    release = create_release('v1.0.0', 'Version 1.0.0', 'Release notes')

    assert release['id'] == 123
    mock_api.assert_called_once()
```

---

## Performance Considerations

### Caching

- Cache configuration after first load
- Cache Git operations (branch, tags)
- Cache dependency check results (5 minute TTL)

### Parallelization

- Run language tests in parallel
- Build release assets concurrently
- Generate documentation for packages in parallel

### Rate Limiting

- Respect GitHub API rate limits (5000/hour authenticated)
- Implement exponential backoff for retries
- Use conditional requests (If-None-Match)

---

## Security Best Practices

### Secrets Handling

- Never log secrets or tokens
- Use GitHub Actions secrets for sensitive data
- Rotate tokens regularly
- Validate all inputs before use

### Input Validation

```python
def validate_version(version: str) -> bool:
    """Validate version string format."""
    pattern = r'^\d+\.\d+\.\d+$'
    if not re.match(pattern, version):
        raise ValidationError(f"Invalid version format: {version}")
    return True
```

### Command Injection Prevention

```python
def safe_git_command(args: list[str]) -> str:
    """Execute git command safely."""
    # Validate args
    for arg in args:
        if any(char in arg for char in [';', '|', '&', '$', '`']):
            raise SecurityError(f"Invalid character in argument: {arg}")

    # Execute with subprocess
    return subprocess.run(
        ['git'] + args,
        capture_output=True,
        text=True,
        check=True
    ).stdout
```

---

## Maintenance Notes

### Deprecation Policy

Functions marked for deprecation:

```python
def old_function():
    """Old function (DEPRECATED).

    .. deprecated:: 1.1.0
        Use :func:`new_function` instead.
    """
    warnings.warn(
        'old_function is deprecated, use new_function',
        DeprecationWarning,
        stacklevel=2
    )
    return new_function()
```

### Version Compatibility

- Minimum Python: 3.13
- Minimum Go: 1.23
- Minimum Node: 20 LTS
- Minimum Rust: stable (1.70+)

### Breaking Changes

All breaking changes require:

1. Major version bump
2. Migration guide in CHANGELOG.md
3. Deprecation warnings in previous version
4. Update to all affected workflows

---

## Related Documentation

- [Configuration Schema](config-schema.md)
- [CI Workflows Implementation](../implementation/ci-workflows.md)
- [Release Workflows Implementation](../implementation/release-workflows.md)
- [Testing Strategy](../implementation/testing-strategy.md)
- [Migration Guide](../operations/migration-guide.md)
- [Troubleshooting Guide](../operations/troubleshooting.md)

---

**Document Version**: 1.0.0 **Last Review**: 2025-10-15 **Next Review**: 2025-11-15
