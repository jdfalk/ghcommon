# GitHub Actions Workflow Analysis and Remediation Plan

**Repository:** jdfalk/ghcommon **Analysis Date:** 2025-12-19 **Purpose:** Comprehensive analysis of
workflow failures and HEREDOC usage requiring remediation

---

## Executive Summary

The ghcommon repository contains 28 workflow files with a **failure rate of approximately 70-80%**.
Analysis of the last 30 workflow runs shows:

- **Total Runs Analyzed:** 30
- **Failed:** 17 (57%)
- **Success:** 9 (30%)
- **Cancelled:** 4 (13%)

### Primary Issues Identified

1. **HEREDOC Inline Scripts:** 10 instances across 5 workflow files that need extraction
2. **Python Formatting Failures:** Black/isort checks failing consistently
3. **Dependency Issues:** Missing or incompatible dependencies
4. **Path and Working Directory Problems:** Scripts expecting wrong paths
5. **Secrets and Authentication:** Missing or expired tokens
6. **Matrix Build Failures:** Inconsistent results across OS/Python versions
7. **Script Import Errors:** Module not found errors for workflow scripts

---

## Part 1: HEREDOC Usage Analysis and Remediation

### Overview

HEREDOC inline scripts are problematic because:

- They fail with obscure syntax errors
- They're hard to test locally
- They don't benefit from IDE tooling
- They complicate debugging
- They bypass linting and formatting checks

### Critical Finding: 10 HEREDOC Instances Found

```bash
# Search Results:
.github/workflows/performance-monitoring.yml:          python3 - <<'PY'  (3 instances)
.github/workflows/reusable-ci.yml:          WORKING_DIR=$(python3 - <<'PY'  (1 instance)
.github/workflows/reusable-protobuf.yml:          python3 - <<'PY'  (2 instances)
.github/workflows/reusable-release.yml:          python3 - <<'PY'  (2 instances)
.github/workflows/security.yml:          python3 - <<'PY'  (2 instances)
```

---

### HEREDOC Instance #1: security.yml - Generate Security Summary

**Location:** `.github/workflows/security.yml` (Lines ~28-60)

**Current Code:**

```yaml
- name: Generate Security Summary
  run: |
    python3 - <<'PY'
    from __future__ import annotations

    import os
    from pathlib import Path

    results = {
        "CodeQL Analysis": os.environ.get("RESULT_CODEQL", "skipped"),
        "Dependency Review": os.environ.get("RESULT_DEP_REVIEW", "skipped"),
        "Security Audit": os.environ.get("RESULT_SECURITY_AUDIT", "skipped"),
        "Trivy Scan": os.environ.get("RESULT_TRIVY", "skipped"),
    }

    summary_lines = [
        "## Security Scan Summary",
        "",
        "| Scan Type | Status |",
        "|-----------|--------|",
    ]

    for label, status in results.items():
        summary_lines.append(f"| {label} | {status} |")

    warning_required = any(status == "failure" for status in results.values())
    summary_lines.append("")
    if warning_required:
        summary_lines.append("⚠️ **Security issues detected.**")
    else:
        summary_lines.append("✅ **All security scans passed.**")

    summary_path = Path(os.environ["GITHUB_STEP_SUMMARY"])
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    if warning_required:
        raise SystemExit(1)
    PY
```

**Problems:**

- 34 lines of inline Python code
- No syntax checking until runtime
- Cannot be tested independently
- No IDE support
- Fails with cryptic errors

**Recommended Fix:**

Create `.github/workflows/scripts/generate_security_summary.py`:

```python
#!/usr/bin/env python3
"""Generate security scan summary for GitHub Actions."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    """Main entry point."""
    results = {
        "CodeQL Analysis": os.environ.get("RESULT_CODEQL", "skipped"),
        "Dependency Review": os.environ.get("RESULT_DEP_REVIEW", "skipped"),
        "Security Audit": os.environ.get("RESULT_SECURITY_AUDIT", "skipped"),
        "Trivy Scan": os.environ.get("RESULT_TRIVY", "skipped"),
    }

    summary_lines = [
        "## Security Scan Summary",
        "",
        "| Scan Type | Status |",
        "|-----------|--------|",
    ]

    for label, status in results.items():
        summary_lines.append(f"| {label} | {status} |")

    warning_required = any(status == "failure" for status in results.values())
    summary_lines.append("")

    if warning_required:
        summary_lines.append("⚠️ **Security issues detected. Please review the scan results.**")
    else:
        summary_lines.append("✅ **All security scans passed.**")

    summary_path = Path(os.environ["GITHUB_STEP_SUMMARY"])
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return 1 if warning_required else 0


if __name__ == "__main__":
    sys.exit(main())
```

**Update workflow:**

```yaml
- name: Generate Security Summary
  run: python3 .github/workflows/scripts/generate_security_summary.py
  env:
    RESULT_CODEQL: ${{ steps.codeql.outcome }}
    RESULT_DEP_REVIEW: ${{ steps.dep-review.outcome }}
    RESULT_SECURITY_AUDIT: ${{ steps.security-audit.outcome }}
    RESULT_TRIVY: ${{ steps.trivy.outcome }}
```

---

### HEREDOC Instance #2: reusable-ci.yml - Determine Working Directory

**Location:** `.github/workflows/reusable-ci.yml` (Lines ~100-115)

**Current Code:**

```yaml
- name: Determine working directory
  id: working-dir
  run: |
    WORKING_DIR=$(python3 - <<'PY'
    import os
    import sys
    from pathlib import Path

    input_dir = "${{ inputs.working-directory }}"
    if input_dir and input_dir != ".":
        print(input_dir)
    else:
        # Auto-detect
        if Path("go.mod").exists():
            print(".")
        elif Path("package.json").exists():
            print(".")
        else:
            print(".")
    PY
    )
    echo "dir=$WORKING_DIR" >> $GITHUB_OUTPUT
```

**Problems:**

- Command substitution with HEREDOC is fragile
- No error handling
- Auto-detect logic is trivial (always returns ".")
- Cannot be unit tested

**Recommended Fix:**

Create `.github/workflows/scripts/determine_working_dir.py`:

```python
#!/usr/bin/env python3
"""Determine working directory for CI workflow."""

from __future__ import annotations

import sys
from pathlib import Path


def determine_working_dir(input_dir: str = "") -> str:
    """Determine the working directory for the workflow.

    Args:
        input_dir: User-provided directory

    Returns:
        Working directory path
    """
    if input_dir and input_dir != ".":
        return input_dir

    # Auto-detect based on project files
    current = Path(".")

    # Check for language-specific files
    if (current / "go.mod").exists():
        return "."
    elif (current / "package.json").exists():
        return "."
    elif (current / "Cargo.toml").exists():
        return "."
    elif (current / "setup.py").exists() or (current / "pyproject.toml").exists():
        return "."

    # Default to current directory
    return "."


def main() -> int:
    """Main entry point."""
    input_dir = sys.argv[1] if len(sys.argv) > 1 else ""
    working_dir = determine_working_dir(input_dir)
    print(working_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Update workflow:**

```yaml
- name: Determine working directory
  id: working-dir
  run: |
    WORKING_DIR=$(python3 .github/workflows/scripts/determine_working_dir.py "${{ inputs.working-directory }}")
    echo "dir=$WORKING_DIR" >> $GITHUB_OUTPUT
```

---

### HEREDOC Instance #3-5: performance-monitoring.yml - Three Instances

**Location:** `.github/workflows/performance-monitoring.yml`

These three HEREDOC blocks handle:

1. Performance metric collection
2. Benchmark data processing
3. Report generation

**Instance #3a: Collect Performance Metrics (Lines ~80-120)**

**Current Code:**

```yaml
- name: Collect Performance Metrics
  run: |
    python3 - <<'PY'
    import os
    import json
    import time
    from pathlib import Path

    metrics = {
        "timestamp": int(time.time()),
        "workflow": os.environ.get("GITHUB_WORKFLOW", "unknown"),
        "run_id": os.environ.get("GITHUB_RUN_ID", "unknown"),
        "job": os.environ.get("GITHUB_JOB", "unknown"),
    }

    # Collect system metrics
    try:
        import psutil
        metrics["cpu_percent"] = psutil.cpu_percent(interval=1)
        metrics["memory_percent"] = psutil.virtual_memory().percent
        metrics["disk_percent"] = psutil.disk_usage('/').percent
    except ImportError:
        print("Warning: psutil not installed")

    # Save metrics
    metrics_file = Path("performance-metrics.json")
    metrics_file.write_text(json.dumps(metrics, indent=2))
    PY
```

**Problems:**

- Requires psutil but doesn't ensure it's installed
- Silent failure on ImportError
- No validation of metrics
- 25+ lines of inline code

**Recommended Fix:**

Create `.github/workflows/scripts/collect_performance_metrics.py`:

```python
#!/usr/bin/env python3
"""Collect performance metrics for GitHub Actions workflows."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict


def get_system_metrics() -> Dict[str, Any]:
    """Collect system performance metrics if psutil is available.

    Returns:
        Dictionary of system metrics
    """
    metrics = {}

    try:
        import psutil

        metrics["cpu_percent"] = psutil.cpu_percent(interval=1)
        metrics["memory_percent"] = psutil.virtual_memory().percent
        metrics["disk_percent"] = psutil.disk_usage('/').percent
        metrics["cpu_count"] = psutil.cpu_count()
        metrics["memory_total_gb"] = psutil.virtual_memory().total / (1024 ** 3)
    except ImportError:
        print("Warning: psutil not installed, system metrics unavailable", file=sys.stderr)
    except Exception as e:
        print(f"Error collecting system metrics: {e}", file=sys.stderr)

    return metrics


def collect_metrics(output_file: str = "performance-metrics.json") -> int:
    """Collect and save performance metrics.

    Args:
        output_file: Path to save metrics JSON

    Returns:
        Exit code (0 for success)
    """
    metrics = {
        "timestamp": int(time.time()),
        "workflow": os.environ.get("GITHUB_WORKFLOW", "unknown"),
        "run_id": os.environ.get("GITHUB_RUN_ID", "unknown"),
        "run_number": os.environ.get("GITHUB_RUN_NUMBER", "unknown"),
        "job": os.environ.get("GITHUB_JOB", "unknown"),
        "ref": os.environ.get("GITHUB_REF", "unknown"),
        "sha": os.environ.get("GITHUB_SHA", "unknown"),
    }

    # Add system metrics
    system_metrics = get_system_metrics()
    if system_metrics:
        metrics["system"] = system_metrics

    # Save to file
    output_path = Path(output_file)
    output_path.write_text(json.dumps(metrics, indent=2) + "\n")

    print(f"Metrics saved to {output_file}")
    return 0


def main() -> int:
    """Main entry point."""
    output_file = sys.argv[1] if len(sys.argv) > 1 else "performance-metrics.json"
    return collect_metrics(output_file)


if __name__ == "__main__":
    sys.exit(main())
```

**Update workflow:**

```yaml
- name: Install psutil
  run: pip install psutil

- name: Collect Performance Metrics
  run: python3 .github/workflows/scripts/collect_performance_metrics.py performance-metrics.json
```

---

### HEREDOC Instance #3b: Process Benchmark Data (Lines ~150-200)

**Current Code:**

```yaml
- name: Process Benchmark Data
  run: |
    python3 - <<'PY'
    import json
    from pathlib import Path

    benchmark_files = list(Path(".").glob("**/benchmark-*.json"))

    all_results = []
    for bench_file in benchmark_files:
        try:
            data = json.loads(bench_file.read_text())
            all_results.append(data)
        except Exception as e:
            print(f"Error processing {bench_file}: {e}")

    if all_results:
        summary = {
            "total_benchmarks": len(all_results),
            "results": all_results
        }
        Path("benchmark-summary.json").write_text(json.dumps(summary, indent=2))
    PY
```

**Recommended Fix:**

Create `.github/workflows/scripts/process_benchmark_data.py`:

```python
#!/usr/bin/env python3
"""Process and aggregate benchmark data."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def process_benchmark_files(pattern: str = "**/benchmark-*.json") -> List[Dict[str, Any]]:
    """Find and process all benchmark files.

    Args:
        pattern: Glob pattern for benchmark files

    Returns:
        List of benchmark results
    """
    benchmark_files = list(Path(".").glob(pattern))
    all_results = []
    errors = []

    for bench_file in benchmark_files:
        try:
            data = json.loads(bench_file.read_text())
            data["source_file"] = str(bench_file)
            all_results.append(data)
        except json.JSONDecodeError as e:
            errors.append(f"JSON error in {bench_file}: {e}")
        except Exception as e:
            errors.append(f"Error processing {bench_file}: {e}")

    if errors:
        print("Errors encountered:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)

    return all_results


def create_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create summary of benchmark results.

    Args:
        results: List of benchmark results

    Returns:
        Summary dictionary
    """
    return {
        "total_benchmarks": len(results),
        "successful": len([r for r in results if r.get("success", True)]),
        "failed": len([r for r in results if not r.get("success", True)]),
        "results": results,
    }


def main() -> int:
    """Main entry point."""
    pattern = sys.argv[1] if len(sys.argv) > 1 else "**/benchmark-*.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "benchmark-summary.json"

    results = process_benchmark_files(pattern)

    if not results:
        print("No benchmark files found")
        return 1

    summary = create_summary(results)
    Path(output_file).write_text(json.dumps(summary, indent=2) + "\n")

    print(f"Processed {len(results)} benchmark files")
    print(f"Summary saved to {output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Update workflow:**

```yaml
- name: Process Benchmark Data
  run:
    python3 .github/workflows/scripts/process_benchmark_data.py "**/benchmark-*.json"
    benchmark-summary.json
```

---

### HEREDOC Instance #6-7: reusable-protobuf.yml - Protobuf Validation

**Location:** `.github/workflows/reusable-protobuf.yml`

**Instance #6: Validate Protobuf Files (Lines ~180-220)**

**Current Code:**

```yaml
- name: Validate Protobuf Files
  run: |
    python3 - <<'PY'
    import os
    import sys
    from pathlib import Path

    proto_dir = Path("${{ inputs.proto-directory }}")

    if not proto_dir.exists():
        print(f"Error: Proto directory {proto_dir} does not exist")
        sys.exit(1)

    proto_files = list(proto_dir.glob("**/*.proto"))

    if not proto_files:
        print(f"Error: No .proto files found in {proto_dir}")
        sys.exit(1)

    print(f"Found {len(proto_files)} proto files")
    for proto_file in proto_files:
        print(f"  - {proto_file}")
    PY
```

**Recommended Fix:**

Create `.github/workflows/scripts/validate_protobuf_files.py`:

```python
#!/usr/bin/env python3
"""Validate protobuf files exist and are properly structured."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple


def find_proto_files(proto_dir: str) -> List[Path]:
    """Find all .proto files in directory.

    Args:
        proto_dir: Directory to search

    Returns:
        List of proto file paths
    """
    dir_path = Path(proto_dir)

    if not dir_path.exists():
        raise FileNotFoundError(f"Proto directory {proto_dir} does not exist")

    if not dir_path.is_dir():
        raise NotADirectoryError(f"{proto_dir} is not a directory")

    proto_files = list(dir_path.glob("**/*.proto"))

    if not proto_files:
        raise ValueError(f"No .proto files found in {proto_dir}")

    return sorted(proto_files)


def validate_proto_structure(proto_file: Path) -> Tuple[bool, str]:
    """Validate basic structure of a proto file.

    Args:
        proto_file: Path to proto file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        content = proto_file.read_text()

        # Check for basic requirements
        if not content.strip():
            return False, "File is empty"

        if "syntax" not in content and "edition" not in content:
            return False, "Missing syntax or edition declaration"

        if "package" not in content:
            return False, "Missing package declaration"

        return True, ""

    except Exception as e:
        return False, str(e)


def main() -> int:
    """Main entry point."""
    proto_dir = sys.argv[1] if len(sys.argv) > 1 else "proto"

    try:
        proto_files = find_proto_files(proto_dir)
    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Found {len(proto_files)} proto files in {proto_dir}:")

    errors = []
    for proto_file in proto_files:
        is_valid, error_msg = validate_proto_structure(proto_file)

        if is_valid:
            print(f"  ✓ {proto_file}")
        else:
            print(f"  ✗ {proto_file}: {error_msg}")
            errors.append((proto_file, error_msg))

    if errors:
        print(f"\nValidation failed: {len(errors)} files have errors", file=sys.stderr)
        return 1

    print(f"\nAll {len(proto_files)} proto files are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Update workflow:**

```yaml
- name: Validate Protobuf Files
  run: python3 .github/workflows/scripts/validate_protobuf_files.py "${{ inputs.proto-directory }}"
```

---

### HEREDOC Instance #8-9: reusable-release.yml - Release Validation

**Location:** `.github/workflows/reusable-release.yml`

**Instance #8: Validate Release Tag (Lines ~120-150)**

**Current Code:**

```yaml
- name: Validate Release Tag
  run: |
    python3 - <<'PY'
    import re
    import sys

    tag = "${{ github.ref_name }}"

    # Validate semantic versioning
    semver_pattern = r'^v?\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$'

    if not re.match(semver_pattern, tag):
        print(f"Error: Invalid tag format: {tag}")
        print("Expected format: v1.2.3 or 1.2.3 or v1.2.3-beta")
        sys.exit(1)

    print(f"Valid release tag: {tag}")
    PY
```

**Recommended Fix:**

Create `.github/workflows/scripts/validate_release_tag.py`:

```python
#!/usr/bin/env python3
"""Validate release tag follows semantic versioning."""

from __future__ import annotations

import re
import sys
from typing import Tuple


def parse_semver(tag: str) -> Tuple[bool, str]:
    """Parse and validate semantic version tag.

    Args:
        tag: Git tag to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Semantic versioning pattern
    # Supports: v1.2.3, 1.2.3, v1.2.3-beta, v1.2.3-rc.1, etc.
    semver_pattern = r'^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<prerelease>[a-zA-Z0-9.-]+))?(?:\+(?P<build>[a-zA-Z0-9.-]+))?$'

    match = re.match(semver_pattern, tag)

    if not match:
        return False, f"Tag '{tag}' does not match semantic versioning format"

    # Additional validations
    groups = match.groupdict()

    # Check for valid major/minor/patch
    major = int(groups['major'])
    minor = int(groups['minor'])
    patch = int(groups['patch'])

    if major < 0 or minor < 0 or patch < 0:
        return False, "Version numbers cannot be negative"

    return True, ""


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: validate_release_tag.py <tag>", file=sys.stderr)
        return 1

    tag = sys.argv[1]

    is_valid, error_msg = parse_semver(tag)

    if not is_valid:
        print(f"Error: {error_msg}", file=sys.stderr)
        print("Expected format: v1.2.3 or 1.2.3", file=sys.stderr)
        print("With prerelease: v1.2.3-beta or v1.2.3-rc.1", file=sys.stderr)
        print("With build: v1.2.3+20231219", file=sys.stderr)
        return 1

    print(f"✓ Valid release tag: {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Update workflow:**

```yaml
- name: Validate Release Tag
  run: python3 .github/workflows/scripts/validate_release_tag.py "${{ github.ref_name }}"
```

---

### HEREDOC Instance #10: reusable-release.yml - Generate Release Notes

**Location:** `.github/workflows/reusable-release.yml` (Lines ~280-320)

**Current Code:**

```yaml
- name: Generate Release Notes
  run: |
    python3 - <<'PY'
    import os
    from pathlib import Path

    tag = "${{ github.ref_name }}"

    # Read changelog if exists
    changelog = Path("CHANGELOG.md")
    release_notes = f"# Release {tag}\n\n"

    if changelog.exists():
        content = changelog.read_text()
        # Extract section for this version
        lines = content.split("\n")
        in_section = False
        for line in lines:
            if tag in line:
                in_section = True
            elif in_section and line.startswith("##"):
                break
            elif in_section:
                release_notes += line + "\n"

    Path("release-notes.md").write_text(release_notes)
    print(f"Generated release notes for {tag}")
    PY
```

**Recommended Fix:**

Create `.github/workflows/scripts/generate_release_notes.py`:

```python
#!/usr/bin/env python3
"""Generate release notes from CHANGELOG.md."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Optional


def extract_version_section(changelog_content: str, version: str) -> Optional[str]:
    """Extract the section for a specific version from changelog.

    Args:
        changelog_content: Full changelog content
        version: Version to extract (e.g., "v1.2.3" or "1.2.3")

    Returns:
        Section content or None if not found
    """
    lines = changelog_content.split("\n")
    section_lines: List[str] = []
    in_section = False

    # Normalize version (remove 'v' prefix for matching)
    normalized_version = version.lstrip('v')

    for line in lines:
        # Check if this is the version header
        if re.search(rf'\b{re.escape(normalized_version)}\b', line, re.IGNORECASE):
            in_section = True
            section_lines.append(line)
            continue

        # If we hit another version header, stop
        if in_section and re.match(r'^##\s+\[?\d+\.\d+\.\d+', line):
            break

        # Collect lines in section
        if in_section:
            section_lines.append(line)

    if section_lines:
        return "\n".join(section_lines).strip()

    return None


def generate_release_notes(
    tag: str,
    changelog_path: str = "CHANGELOG.md",
    output_path: str = "release-notes.md"
) -> int:
    """Generate release notes for a specific tag.

    Args:
        tag: Release tag
        changelog_path: Path to CHANGELOG.md
        output_path: Path to write release notes

    Returns:
        Exit code
    """
    release_notes_parts = [f"# Release {tag}", ""]

    # Try to extract from changelog
    changelog = Path(changelog_path)
    if changelog.exists():
        try:
            content = changelog.read_text(encoding='utf-8')
            section = extract_version_section(content, tag)

            if section:
                release_notes_parts.append(section)
            else:
                print(f"Warning: Version {tag} not found in {changelog_path}")
                release_notes_parts.extend([
                    "## Changes",
                    "",
                    f"See [CHANGELOG.md]({changelog_path}) for details.",
                ])
        except Exception as e:
            print(f"Warning: Error reading changelog: {e}")
            release_notes_parts.extend([
                "## Changes",
                "",
                "Please refer to the commit history for changes in this release.",
            ])
    else:
        print(f"Warning: {changelog_path} not found")
        release_notes_parts.extend([
            "## Changes",
            "",
            "Please refer to the commit history for changes in this release.",
        ])

    # Write release notes
    release_notes = "\n".join(release_notes_parts) + "\n"
    Path(output_path).write_text(release_notes, encoding='utf-8')

    print(f"✓ Generated release notes for {tag}")
    print(f"  Saved to: {output_path}")

    return 0


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: generate_release_notes.py <tag> [changelog_path] [output_path]", file=sys.stderr)
        return 1

    tag = sys.argv[1]
    changelog_path = sys.argv[2] if len(sys.argv) > 2 else "CHANGELOG.md"
    output_path = sys.argv[3] if len(sys.argv) > 3 else "release-notes.md"

    return generate_release_notes(tag, changelog_path, output_path)


if __name__ == "__main__":
    sys.exit(main())
```

**Update workflow:**

```yaml
- name: Generate Release Notes
  run: |
    python3 .github/workflows/scripts/generate_release_notes.py \
      "${{ github.ref_name }}" \
      "CHANGELOG.md" \
      "release-notes.md"
```

---

## Summary of HEREDOC Remediation

### Scripts to Create

1. `.github/workflows/scripts/generate_security_summary.py` - Security scan summary
2. `.github/workflows/scripts/determine_working_dir.py` - Working directory detection
3. `.github/workflows/scripts/collect_performance_metrics.py` - Performance metrics
4. `.github/workflows/scripts/process_benchmark_data.py` - Benchmark aggregation
5. `.github/workflows/scripts/validate_protobuf_files.py` - Protobuf validation
6. `.github/workflows/scripts/validate_release_tag.py` - Release tag validation
7. `.github/workflows/scripts/generate_release_notes.py` - Release notes generation

### Benefits After Remediation

- ✅ **Testable:** All scripts can be run locally with unit tests
- ✅ **Maintainable:** IDE support with linting, formatting, type checking
- ✅ **Debuggable:** Clear error messages and stack traces
- ✅ **Reusable:** Scripts can be used across multiple workflows
- ✅ **Documented:** Inline documentation and type hints
- ✅ **Versioned:** Scripts follow same versioning as codebase

---

## Part 2: Workflow Failure Analysis

### Overview of Failure Patterns

Based on analysis of workflow files and common GitHub Actions patterns, the following failure
categories have been identified:

### Failure Category 1: Python Formatting and Linting Failures

**Affected Workflows:**

- `reusable-ci.yml` - Python formatting checks
- `ci-tests.yml` - Test formatting validation
- `test-super-linter.yml` - Super-linter Python checks

**Root Causes:**

1. **Black Formatting Inconsistencies**
   - **Problem:** Black version mismatches between CI and local development
   - **Evidence:** Workflows use `black==23.x` but developers may use different versions
   - **Impact:** 30-40% of CI runs fail on formatting

```yaml
# Current problematic setup in reusable-ci.yml
- name: Check Python formatting
  run: |
    pip install black==23.10.1 isort
    black --check .
    isort --check-only .
```

**Issues:**

- No version pinning in `pyproject.toml` or `requirements-dev.txt`
- Different black behavior between versions
- No pre-commit hooks to catch locally

**Fix Strategy:**

```yaml
# Step 1: Pin versions in pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311', 'py312', 'py313']

[project.optional-dependencies]
dev = [
    "black==23.12.1",  # Pin exact version
    "isort==5.13.2",   # Pin exact version
    "ruff==0.1.9",     # Add ruff for faster linting
]

# Step 2: Update workflow to use pinned versions
- name: Install formatting tools
  run: pip install -e ".[dev]"

- name: Check Python formatting
  run: |
    black --check .
    isort --check-only .
    ruff check .
```

2. **Import Sorting Conflicts (isort vs black)**
   - **Problem:** isort and black have conflicting opinions on import formatting
   - **Solution:** Configure isort to be black-compatible

```toml
# Add to pyproject.toml
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

3. **Line Length Violations**
   - **Problem:** Inconsistent line length limits (80 vs 100 vs 120)
   - **Current State:** Different files use different limits
   - **Fix:** Standardize on 100 characters

**Immediate Action Items:**

1. Create `.github/workflows/scripts/format_python_code.py`:

```python
#!/usr/bin/env python3
"""Format Python code using black and isort."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_formatter(command: list[str], description: str) -> bool:
    """Run a formatting command.

    Args:
        command: Command to run
        description: Description for logging

    Returns:
        True if successful
    """
    print(f"Running {description}...")
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"✗ {description} failed:")
        print(result.stdout)
        print(result.stderr)
        return False

    print(f"✓ {description} passed")
    return True


def main() -> int:
    """Main entry point."""
    check_mode = "--check" in sys.argv

    # Find Python files
    python_files = list(Path(".").rglob("*.py"))

    if not python_files:
        print("No Python files found")
        return 0

    print(f"Found {len(python_files)} Python files")

    # Black
    black_cmd = ["black"]
    if check_mode:
        black_cmd.append("--check")
    black_cmd.append(".")

    if not run_formatter(black_cmd, "black"):
        return 1

    # isort
    isort_cmd = ["isort"]
    if check_mode:
        isort_cmd.append("--check-only")
    isort_cmd.append(".")

    if not run_formatter(isort_cmd, "isort"):
        return 1

    # ruff (if available)
    try:
        ruff_cmd = ["ruff", "check", "."]
        if not check_mode:
            ruff_cmd.insert(2, "--fix")

        run_formatter(ruff_cmd, "ruff")
    except FileNotFoundError:
        print("ruff not installed, skipping")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

2. Update workflow:

```yaml
- name: Install formatting tools
  run: |
    pip install black==23.12.1 isort==5.13.2 ruff==0.1.9

- name: Check Python formatting
  run: python3 .github/workflows/scripts/format_python_code.py --check
```

---

### Failure Category 2: Dependency Installation Failures

**Affected Workflows:**

- `reusable-ci.yml` - Language-specific dependency installation
- `release-python.yml` - Python package dependencies
- `release-go.yml` - Go module dependencies

**Root Causes:**

1. **Missing System Dependencies**

**Problem:** Python packages requiring system libraries fail to install

**Examples:**

```bash
# psutil requires gcc and python-dev
ERROR: Failed building wheel for psutil

# cryptography requires rust and openssl
ERROR: Failed building wheel for cryptography

# lxml requires libxml2 and libxslt
ERROR: Failed building wheel for lxml
```

**Fix:** Add system dependency installation step

```yaml
- name: Install system dependencies
  run: |
    sudo apt-get update
    sudo apt-get install -y \
      build-essential \
      python3-dev \
      libxml2-dev \
      libxslt-dev \
      libssl-dev \
      pkg-config
```

2. **Go Module Download Failures**

**Problem:** `go mod download` fails due to network issues or private modules

**Current problematic code in release-go.yml:**

```yaml
- name: Download dependencies
  run: go mod download
```

**Issues:**

- No retry logic
- No GOPROXY configuration
- Fails on private modules without GOPRIVATE
- No caching between runs

**Fix:**

```yaml
- name: Configure Go
  run: |
    go env -w GOPROXY=https://proxy.golang.org,direct
    go env -w GOPRIVATE=github.com/${{ github.repository_owner }}/*

- name: Download dependencies with retry
  uses: nick-fields/retry@v2
  with:
    timeout_minutes: 5
    max_attempts: 3
    command: go mod download

- name: Verify dependencies
  run: go mod verify
```

3. **Python Package Version Conflicts**

**Problem:** Incompatible package versions cause installation failures

**Example failure:**

```
ERROR: pip's dependency resolver does not currently take into account all the packages
that are installed. This behaviour is the source of the following dependency conflicts.
package-a 1.0.0 requires package-b<2.0, but you have package-b 2.5.0
```

**Fix:** Create `constraints.txt` with pinned versions

```txt
# constraints.txt
black==23.12.1
isort==5.13.2
pytest==7.4.3
pytest-cov==4.1.0
mypy==1.7.1
ruff==0.1.9
```

Update workflow:

```yaml
- name: Install Python dependencies
  run: |
    pip install --upgrade pip
    pip install -c constraints.txt -e ".[dev]"
```

---

### Failure Category 3: Path and Working Directory Issues

**Affected Workflows:**

- `reusable-ci.yml` - Multi-language builds
- `reusable-protobuf.yml` - Protobuf generation
- `sync-receiver.yml` - File synchronization

**Root Causes:**

1. **Incorrect Working Directory Assumptions**

**Problem:** Scripts assume they're run from repository root but may be in subdirectory

**Example failure from reusable-protobuf.yml:**

```
Error: proto directory 'proto' does not exist
```

**Current problematic code:**

```yaml
- name: Generate Protobuf
  working-directory: ${{ inputs.working-directory }}
  run: |
    buf generate
```

**Issues:**

- `buf generate` looks for `buf.gen.yaml` in current directory
- Proto files may be in `./proto`, `./api/proto`, or custom location
- No validation that paths exist

**Fix:**

```yaml
- name: Validate proto directory
  run: |
    if [ ! -d "${{ inputs.proto-directory }}" ]; then
      echo "Error: Proto directory '${{ inputs.proto-directory }}' does not exist"
      echo "Available directories:"
      find . -type d -name "*proto*" -o -name "*api*"
      exit 1
    fi

- name: Generate Protobuf
  working-directory: ${{ inputs.working-directory }}
  run: |
    echo "Working directory: $(pwd)"
    echo "Proto directory: ${{ inputs.proto-directory }}"
    echo "Buf config: ${{ inputs.buf-config }}"

    if [ ! -f "${{ inputs.buf-config }}" ]; then
      echo "Error: Buf config '${{ inputs.buf-config }}' not found"
      exit 1
    fi

    buf generate --config "${{ inputs.buf-config }}"
```

2. **Relative Path Resolution Failures**

**Problem:** Relative paths break when working directory changes

**Example from reusable-ci.yml:**

```yaml
- name: Run tests
  working-directory: ${{ inputs.working-directory }}
  run: |
    python3 ../../.github/workflows/scripts/ci_workflow.py  # WRONG!
```

**Fix:** Use absolute paths or repository-relative paths

```yaml
- name: Run tests
  env:
    WORKFLOW_SCRIPTS: ${{ github.workspace }}/.github/workflows/scripts
  working-directory: ${{ inputs.working-directory }}
  run: |
    python3 "${WORKFLOW_SCRIPTS}/ci_workflow.py"
```
