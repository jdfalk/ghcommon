<!-- file: docs/refactors/workflows/v2/version-policy.md -->
<!-- version: 1.0.0 -->
<!-- guid: c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f -->

# Language Version Support Policy

## Overview

This document defines which language versions are officially supported in ghcommon workflows and
when versions are deprecated.

## Core Policy

**Support Latest 2 Stable Versions Only**

Rationale:

- **Security**: Older versions lack critical security patches
- **Maintenance**: Testing N versions requires N times the resources
- **Modern Features**: Enables use of latest language capabilities
- **Industry Alignment**: Matches common enterprise support policies

**Deprecation Timeline**: 2 versions + 180 days

- When version N+2 is released, version N is marked deprecated
- After 180 days, deprecated version is removed from workflows
- This provides 6+ months for testing and upgrading

## Supported Versions

### Go

**Current Support**: 1.23, 1.24

| Version | Status        | Support Added | Deprecated After | Removed After        |
| ------- | ------------- | ------------- | ---------------- | -------------------- |
| 1.24    | ✅ Supported  | 2024-08-13    | Go 1.26 release  | +180 days            |
| 1.23    | ✅ Supported  | 2024-02-06    | Go 1.25 release  | +180 days            |
| 1.22    | ❌ Deprecated | 2023-08-08    | 2024-08-13       | 2025-02-09 (removed) |

**Update Frequency**: Every 6 months (February, August) **Deprecation Policy**: Version N deprecated
when N+2 releases, removed 180 days later

**Configuration**:

```yaml
languages:
  versions:
    go: ['1.23', '1.24']
```

**Resources**:

- [Go Release History](https://go.dev/doc/devel/release)
- [Go Security Policy](https://go.dev/security/policy)

---

### Python

**Current Support**: 3.13, 3.14

| Version | Status        | Support Added | Deprecated After      | Removed After        |
| ------- | ------------- | ------------- | --------------------- | -------------------- |
| 3.14    | ✅ Supported  | 2025-10-01    | Python 3.16 (2027-10) | +180 days            |
| 3.13    | ✅ Supported  | 2024-10-01    | Python 3.15 (2026-10) | +180 days            |
| 3.12    | ❌ Deprecated | 2023-10-02    | 2025-10-01            | 2026-03-30 (removed) |

**Update Frequency**: Annually (October) **Deprecation Policy**: Version N deprecated when N+2
releases, removed 180 days later

**Configuration**:

```yaml
languages:
  versions:
    python: ['3.13', '3.14']
```

**Resources**:

- [Python Release Schedule](https://peps.python.org/pep-0619/)
- [Python Security Policy](https://www.python.org/dev/security/)

---

### Node.js

**Current Support**: 20 LTS, 22 LTS

| Version | Status        | LTS Start  | Deprecated After      | Removed After        |
| ------- | ------------- | ---------- | --------------------- | -------------------- |
| 22 LTS  | ✅ Supported  | 2024-10-29 | Node 24 LTS (2026-10) | +180 days            |
| 20 LTS  | ✅ Supported  | 2023-10-24 | Node 24 LTS (2026-10) | +180 days            |
| 18 LTS  | ❌ Deprecated | 2022-10-25 | 2024-10-29            | 2025-04-27 (removed) |

**Update Frequency**: Every 12 months (October, even-numbered versions become LTS) **Deprecation
Policy**: Version N deprecated when N+2 LTS releases, removed 180 days later

**Configuration**:

```yaml
languages:
  versions:
    node: ['20', '22'] # LTS versions only
```

**Resources**:

- [Node.js Release Schedule](https://github.com/nodejs/Release)
- [Node.js Security](https://nodejs.org/en/about/security/)

---

### Rust

**Current Support**: stable, stable-1 (rolling)

| Channel  | Status           | Update Frequency              |
| -------- | ---------------- | ----------------------------- |
| stable   | ✅ Supported     | Every 6 weeks                 |
| stable-1 | ✅ Supported     | Previous stable (6 weeks old) |
| beta     | ❌ Not Supported | Too unstable for CI           |
| nightly  | ❌ Not Supported | Breaking changes              |

**Current Versions** (as of 2025-10-12):

- stable: 1.82.0
- stable-1: 1.81.0

**Configuration**:

```yaml
languages:
  versions:
    rust: ['stable', 'stable-1']
```

**Resources**:

- [Rust Release Schedule](https://forge.rust-lang.org/)
- [Rust Security](https://www.rust-lang.org/policies/security)

---

## Version Update Process

### Automated Detection

Workflow checks for new versions weekly:

```yaml
# .github/workflows/version-check.yml
name: Check Language Versions
on:
  schedule:
    - cron: '0 9 * * MON' # Every Monday at 9 AM UTC
  workflow_dispatch:

jobs:
  check-versions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for new versions
        run: python scripts/check_language_versions.py
      - name: Create update PR if needed
        if: env.NEW_VERSIONS_AVAILABLE == 'true'
        run: gh pr create --title "Update language versions" --body "$PR_BODY"
```

### Update Checklist

When a new version is released:

- [ ] **Week 1: Evaluation**
  - [ ] Review release notes for breaking changes
  - [ ] Test in isolated branch
  - [ ] Update version matrix in repository-config.yml
  - [ ] Run integration tests

- [ ] **Week 2: Rollout**
  - [ ] Update documentation
  - [ ] Merge version update PR
  - [ ] Monitor workflow runs for failures
  - [ ] Communicate to teams via #engineering

- [ ] **Week 3: Deprecation**
  - [ ] Mark oldest version as deprecated in docs
  - [ ] Add deprecation warnings to workflows
  - [ ] Notify teams of upcoming removal

- [ ] **Week 4-8: Sunset**
  - [ ] Remove deprecated version from config
  - [ ] Archive test results for deprecated version
  - [ ] Update all documentation references

### Communication Template

```markdown
## Language Version Update: Go 1.25

**Summary**: Go 1.25 has been released. We will add support and deprecate Go 1.23.

**Timeline**:

- 2025-08-20: Go 1.25 available in workflows
- 2025-09-01: Go 1.23 marked deprecated (warnings)
- 2025-10-01: Go 1.23 removed from workflows

**Action Required**:

- Review Go 1.25 release notes: https://go.dev/doc/go1.25
- Test your projects with Go 1.25
- Update local development environments
- Fix any breaking changes before Oct 1

**Breaking Changes**:

- [List major breaking changes here]

**Questions**: Reply in #go-users or file an issue
```

## Deprecation Warnings

### In Workflows

When a version is deprecated, workflows emit warnings:

```yaml
- name: Warn about deprecated version
  if: matrix.go-version == '1.23'
  run: |
    echo "::warning::Go 1.23 is deprecated and will be removed on 2025-10-01"
    echo "::warning::Please update to Go 1.24 or later"
    echo "::warning::See: https://github.com/jdfalk/ghcommon/docs/refactors/workflows/v2/version-policy.md"
```

### In Helper Scripts

```python
def check_version_support(language: str, version: str) -> None:
    """Warn if using deprecated version."""
    deprecated = {
        "go": {"1.23": "2025-10-01"},
        "python": {"3.12": "2025-10-01"},
    }

    if version in deprecated.get(language, {}):
        removal_date = deprecated[language][version]
        print(f"⚠️  {language} {version} is deprecated")
        print(f"⚠️  Will be removed on {removal_date}")
        print(f"⚠️  Please update to a supported version")
```

## Exception Process

### Requesting Extended Support

In rare cases, extended support for older versions may be granted:

**Valid Reasons**:

- Critical production dependency requires old version
- Upstream library incompatibility with new version
- Security-patched older version needed for compliance

**Process**:

1. File issue: "Request: Extend support for [language] [version]"
2. Provide justification and timeline
3. Security team reviews
4. If approved, add to exceptions list

**Exceptions List**:

Currently none.

## Testing Matrix Strategy

### Full Matrix (All Combinations)

Use when:

- Language updates require comprehensive testing
- Breaking changes detected in new version
- Critical infrastructure changes

```yaml
strategy:
  matrix:
    go: ['1.23', '1.24']
    os: [ubuntu-latest, macos-latest]
# Result: 4 jobs (2 versions × 2 OS)
```

### Optimized Matrix (Strategic Subset)

Use for:

- Regular CI runs (save CI minutes)
- PR validation
- Draft/WIP branches

```yaml
strategy:
  matrix:
    include:
      - go: '1.24'
        os: ubuntu-latest # Latest version, primary OS
      - go: '1.24'
        os: macos-latest # Latest version, macOS
      - go: '1.23'
        os: ubuntu-latest # Previous version, primary OS
# Result: 3 jobs (strategic coverage)
```

### Matrix Generation Helper

```python
def generate_test_matrix(
    language: str,
    strategy: str = "optimized"
) -> dict[str, list[dict[str, str]]]:
    """Generate test matrix based on strategy."""
    versions = get_supported_versions(language)

    if strategy == "full":
        return {
            "include": [
                {"version": v, "os": os}
                for v in versions
                for os in ["ubuntu-latest", "macos-latest"]
            ]
        }

    # Optimized: latest on all OS, previous on ubuntu only
    return {
        "include": [
            {"version": versions[0], "os": "ubuntu-latest"},
            {"version": versions[0], "os": "macos-latest"},
            {"version": versions[1], "os": "ubuntu-latest"},
        ]
    }
```

## Version Pinning in Workflows

### GitHub Actions Versions

Pin actions to **commit SHA**, not tags:

```yaml
# ✅ CORRECT: Pinned to immutable SHA
- uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab # v4.1.1

# ❌ WRONG: Mutable tag (can be force-pushed)
- uses: actions/checkout@v4
```

### Language Installer Actions

```yaml
# Go
- uses: actions/setup-go@0a12ed9d6a96ab950c8f026ed9f722fe0da7ef32 # v5.0.2
  with:
    go-version: ${{ matrix.go-version }}

# Python
- uses: actions/setup-python@f677139bbe7f9c59b41e40162b753c062f5d49a3 # v5.2.0
  with:
    python-version: ${{ matrix.python-version }}

# Node
- uses: actions/setup-node@1e60f620b9541d16bece96c5465dc8ee9832be0b # v4.0.3
  with:
    node-version: ${{ matrix.node-version }}

# Rust
- uses: dtolnay/rust-toolchain@be73d7920c329f220ce78e0234b8f96b7ae60248
  with:
    toolchain: ${{ matrix.rust-version }}
```

## References

- **Code Style**: `.github/instructions/general-coding.instructions.md`
- **Testing Standards**: `.github/instructions/test-generation.instructions.md`
- **Workflow Guidelines**: `.github/instructions/github-actions.instructions.md`
- **Architecture**: [architecture.md](architecture.md)
- **Helper API**: [reference/helper-api.md](reference/helper-api.md)

---

**Last Updated**: 2025-10-12 **Next Review**: 2025-11-12 (monthly) **Document Owner**: Platform
Engineering Team
