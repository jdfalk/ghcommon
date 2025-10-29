<!-- file: docs/refactors/workflows/v2/reference/config-schema.md -->
<!-- version: 1.0.0 -->
<!-- guid: d56e7f82-3d4e-5f6a-c8e9-0a1b2c3d4e5f -->

# Configuration Schema Reference

Complete JSON schema documentation for `workflow-versions.yml`, the central configuration file for the v2 workflow system.

## Table of Contents

- [Overview](#overview)
- [File Location](#file-location)
- [Schema Definition](#schema-definition)
- [Top-Level Fields](#top-level-fields)
- [Version Configuration](#version-configuration)
- [Feature Flags](#feature-flags)
- [Branch Policies](#branch-policies)
- [Advanced Configuration](#advanced-configuration)
- [Validation Rules](#validation-rules)
- [Examples](#examples)
- [Migration Guide](#migration-guide)

---

## Overview

The `workflow-versions.yml` file is the central configuration for the v2 workflow system. It defines:

- **Language versions** for each branch
- **Feature flags** to enable/disable v2 features
- **Branch policies** for stable branch management
- **Advanced settings** for caching, metrics, and automation

### Key Principles

1. **Single Source of Truth**: All version and feature configuration in one file
2. **Branch-Aware**: Different versions for main vs. stable branches
3. **Feature Toggles**: Gradual rollout via feature flags
4. **Validation**: Schema validation ensures configuration correctness
5. **Backward Compatible**: v1 workflows continue working if v2 disabled

---

## File Location

```text
.github/workflow-versions.yml
```text

This file must be in the repository root's `.github/` directory.

---

## Schema Definition

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Workflow Versions Configuration",
  "description": "Configuration for v2 workflow system with branch-aware versions and feature flags",
  "type": "object",
  "required": ["version"],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Schema version (semantic versioning)"
    },
    "use_workflow_v2": {
      "type": "boolean",
      "default": false,
      "description": "Global flag to enable/disable v2 workflow system"
    },
    "versions": {
      "type": "object",
      "description": "Language and tool versions per branch",
      "properties": {
        "go": {
          "$ref": "#/definitions/languageVersions"
        },
        "python": {
          "$ref": "#/definitions/languageVersions"
        },
        "node": {
          "$ref": "#/definitions/languageVersions"
        },
        "rust": {
          "$ref": "#/definitions/languageVersions"
        },
        "actions": {
          "$ref": "#/definitions/actionVersions"
        }
      }
    },
    "feature_flags": {
      "$ref": "#/definitions/featureFlags"
    },
    "branch_policies": {
      "type": "object",
      "description": "Branch-specific configuration",
      "patternProperties": {
        "^stable-1-.*$": {
          "$ref": "#/definitions/branchPolicy"
        }
      }
    },
    "advanced": {
      "$ref": "#/definitions/advancedConfig"
    }
  },
  "definitions": {
    "languageVersions": {
      "type": "object",
      "required": ["main"],
      "properties": {
        "main": {
          "type": "string",
          "description": "Version for main branch (latest)"
        },
        "stable-1": {
          "type": "string",
          "description": "Version for stable-1 branches (N-1)"
        },
        "stable-2": {
          "type": "string",
          "description": "Version for stable-2 branches (N-2, deprecated)"
        }
      }
    },
    "actionVersions": {
      "type": "object",
      "description": "GitHub Actions versions",
      "properties": {
        "checkout": {
          "type": "string",
          "pattern": "^v\\d+$"
        },
        "setup-go": {
          "type": "string",
          "pattern": "^v\\d+$"
        },
        "setup-python": {
          "type": "string",
          "pattern": "^v\\d+$"
        },
        "setup-node": {
          "type": "string",
          "pattern": "^v\\d+$"
        },
        "cache": {
          "type": "string",
          "pattern": "^v\\d+$"
        },
        "upload-artifact": {
          "type": "string",
          "pattern": "^v\\d+$"
        },
        "download-artifact": {
          "type": "string",
          "pattern": "^v\\d+$"
        }
      }
    },
    "featureFlags": {
      "type": "object",
      "description": "Feature toggles for v2 system",
      "properties": {
        "use_change_detection": {
          "type": "boolean",
          "default": false
        },
        "use_matrix_generation": {
          "type": "boolean",
          "default": false
        },
        "use_release_automation": {
          "type": "boolean",
          "default": false
        },
        "use_docs_automation": {
          "type": "boolean",
          "default": false
        },
        "use_maintenance_automation": {
          "type": "boolean",
          "default": false
        },
        "use_advanced_features": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "branchPolicy": {
      "type": "object",
      "description": "Policy for a specific stable branch",
      "properties": {
        "go_version": {
          "type": "string"
        },
        "python_version": {
          "type": "string"
        },
        "node_version": {
          "type": "string"
        },
        "rust_version": {
          "type": "string"
        },
        "locked": {
          "type": "boolean",
          "default": false,
          "description": "If true, no more changes allowed (branch deprecated)"
        },
        "end_of_life": {
          "type": "string",
          "format": "date",
          "description": "Date when branch reaches EOL (YYYY-MM-DD)"
        },
        "work_stopped": {
          "type": "string",
          "format": "date",
          "description": "Date when active work stopped (YYYY-MM-DD)"
        }
      }
    },
    "advancedConfig": {
      "type": "object",
      "description": "Advanced configuration options",
      "properties": {
        "cache": {
          "$ref": "#/definitions/cacheConfig"
        },
        "metrics": {
          "$ref": "#/definitions/metricsConfig"
        },
        "github_app": {
          "$ref": "#/definitions/githubAppConfig"
        }
      }
    },
    "cacheConfig": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": true
        },
        "key_prefix": {
          "type": "string",
          "default": "v2"
        },
        "restore_keys": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "paths": {
          "type": "object",
          "properties": {
            "go": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "python": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "node": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "rust": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          }
        }
      }
    },
    "metricsConfig": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "collect_build_times": {
          "type": "boolean",
          "default": true
        },
        "collect_test_results": {
          "type": "boolean",
          "default": true
        },
        "collect_cache_stats": {
          "type": "boolean",
          "default": true
        },
        "retention_days": {
          "type": "integer",
          "minimum": 1,
          "maximum": 90,
          "default": 30
        }
      }
    },
    "githubAppConfig": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "app_id": {
          "type": "string"
        },
        "installation_id": {
          "type": "string"
        }
      }
    }
  }
}
```text

---

## Top-Level Fields

### `version` (required)

**Type:** `string`  
**Format:** Semantic version (e.g., `"1.0.0"`)  
**Description:** Schema version for the configuration file.

```yaml
version: "1.0.0"
```text

**Rules:**
- Must follow semantic versioning (MAJOR.MINOR.PATCH)
- Increment MAJOR for breaking schema changes
- Increment MINOR for new optional fields
- Increment PATCH for documentation/fixes

### `use_workflow_v2`

**Type:** `boolean`  
**Default:** `false`  
**Description:** Global flag to enable/disable the entire v2 workflow system.

```yaml
use_workflow_v2: true
```text

**Behavior:**
- `true`: v2 workflows and helper scripts enabled
- `false`: Falls back to v1 workflows (if present)

**Use Cases:**
- **Gradual Rollout**: Enable for specific repositories first
- **Emergency Rollback**: Disable if v2 has critical issues
- **Testing**: Enable in test repositories only

---

## Version Configuration

### `versions`

**Type:** `object`  
**Description:** Language and tool versions for different branches.

#### Language Version Object

Each language has three version slots:

```yaml
versions:
  go:
    main: "1.25"      # Latest version for main branch
    stable-1: "1.24"  # N-1 version for stable branches
    stable-2: "1.23"  # N-2 version (deprecated, work stopped)
```text

**Supported Languages:**

#### Go

```yaml
versions:
  go:
    main: "1.25"
    stable-1: "1.24"
    stable-2: "1.23"  # Optional
```text

**Valid Versions:**
- Format: `"1.XX"` (e.g., `"1.23"`, `"1.24"`, `"1.25"`)
- Must be released Go versions
- Follows Go's version numbering (no `v` prefix)

**Version Policy:**
- **main**: Latest stable Go release
- **stable-1**: Previous major version (N-1)
- **stable-2**: Two versions back (N-2, deprecated)

#### Python

```yaml
versions:
  python:
    main: "3.14"
    stable-1: "3.13"
    stable-2: "3.12"  # Optional
```text

**Valid Versions:**
- Format: `"3.XX"` (e.g., `"3.12"`, `"3.13"`, `"3.14"`)
- Must be released Python versions
- Python 3 only (no Python 2 support)

**Version Policy:**
- **main**: Latest stable Python release
- **stable-1**: Previous minor version (N-1)
- **stable-2**: Two versions back (N-2, deprecated)

#### Node.js

```yaml
versions:
  node:
    main: "22"
    stable-1: "20"
```text

**Valid Versions:**
- Format: `"XX"` (e.g., `"20"`, `"22"`)
- LTS versions preferred
- Even-numbered releases (LTS schedule)

**Version Policy:**
- **main**: Current LTS
- **stable-1**: Previous LTS

#### Rust

```yaml
versions:
  rust:
    main: "stable"
    stable-1: "stable-1"
```text

**Valid Versions:**
- `"stable"`: Current stable release
- `"stable-1"`: Previous stable release (N-1)
- `"1.XX.Y"`: Specific version (e.g., `"1.75.0"`)

**Version Policy:**
- **main**: `"stable"` (latest stable)
- **stable-1**: `"stable-1"` or specific version

#### Actions

```yaml
versions:
  actions:
    checkout: "v4"
    setup-go: "v5"
    setup-python: "v5"
    setup-node: "v4"
    cache: "v4"
    upload-artifact: "v4"
    download-artifact: "v4"
```text

**Valid Versions:**
- Format: `"vX"` (e.g., `"v3"`, `"v4"`, `"v5"`)
- Must be published GitHub Actions versions
- Major version only (no minor/patch)

**Supported Actions:**
- `checkout`: actions/checkout
- `setup-go`: actions/setup-go
- `setup-python`: actions/setup-python
- `setup-node`: actions/setup-node
- `cache`: actions/cache
- `upload-artifact`: actions/upload-artifact
- `download-artifact`: actions/download-artifact

---

## Feature Flags

### `feature_flags`

**Type:** `object`  
**Description:** Toggles for individual v2 features.

```yaml
feature_flags:
  use_change_detection: true
  use_matrix_generation: true
  use_release_automation: false
  use_docs_automation: false
  use_maintenance_automation: false
  use_advanced_features: false
```text

### Individual Flags

#### `use_change_detection`

**Type:** `boolean`  
**Default:** `false`  
**Phase:** Phase 1 - CI Modernization

**What It Enables:**
- Automated change detection using helper scripts
- Path-based filtering for CI jobs
- Smart workflow triggering based on changed files

**Dependencies:**
- Requires `use_workflow_v2: true`
- Requires `.github/helpers/ci_workflow.py`

**Example:**
```yaml
feature_flags:
  use_change_detection: true
```text

**Workflow Usage:**
```yaml
jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      go_changed: ${{ steps.changes.outputs.go }}
    steps:
      - uses: actions/checkout@v4
      - name: Detect changes
        id: changes
        run: |
          python3 .github/helpers/ci_workflow.py detect-changes
```text

#### `use_matrix_generation`

**Type:** `boolean`  
**Default:** `false`  
**Phase:** Phase 1 - CI Modernization

**What It Enables:**
- Dynamic matrix generation based on branch
- Branch-aware version selection
- Automatic platform matrix creation

**Dependencies:**
- Requires `use_workflow_v2: true`
- Requires `.github/helpers/ci_workflow.py`
- Requires `versions` configuration

**Example:**
```yaml
feature_flags:
  use_matrix_generation: true
```text

**Workflow Usage:**
```yaml
jobs:
  generate-matrix:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.matrix.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
      - name: Generate matrix
        id: matrix
        run: |
          python3 .github/helpers/ci_workflow.py generate-matrix \
            --language go \
            --branch ${{ github.ref_name }}
```text

#### `use_release_automation`

**Type:** `boolean`  
**Default:** `false`  
**Phase:** Phase 2 - Release Consolidation

**What It Enables:**
- Automated release version detection
- Branch-aware release tagging
- Multi-platform release builds

**Dependencies:**
- Requires `use_workflow_v2: true`
- Requires `.github/helpers/release_workflow.py`
- Requires `versions` and `branch_policies` configuration

**Example:**
```yaml
feature_flags:
  use_release_automation: true
```text

**Workflow Usage:**
```yaml
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Determine version
        id: version
        run: |
          python3 .github/helpers/release_workflow.py detect-version \
            --branch ${{ github.ref_name }}
```text

#### `use_docs_automation`

**Type:** `boolean`  
**Default:** `false`  
**Phase:** Phase 3 - Documentation Automation

**What It Enables:**
- Automated documentation generation from code
- AST-based documentation parsing
- Version-aware documentation builds

**Dependencies:**
- Requires `use_workflow_v2: true`
- Requires `.github/helpers/docs_workflow.py`

**Example:**
```yaml
feature_flags:
  use_docs_automation: true
```text

**Workflow Usage:**
```yaml
jobs:
  generate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate documentation
        run: |
          python3 .github/helpers/docs_workflow.py generate \
            --language go \
            --output docs/
```text

#### `use_maintenance_automation`

**Type:** `boolean`  
**Default:** `false`  
**Phase:** Phase 4 - Maintenance Automation

**What It Enables:**
- Automated dependency updates
- Stale issue/PR detection
- Security vulnerability scanning

**Dependencies:**
- Requires `use_workflow_v2: true`
- Requires `.github/helpers/maintenance_workflow.py`

**Example:**
```yaml
feature_flags:
  use_maintenance_automation: true
```text

**Workflow Usage:**
```yaml
jobs:
  update-dependencies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for updates
        run: |
          python3 .github/helpers/maintenance_workflow.py check-updates \
            --language go
```text

#### `use_advanced_features`

**Type:** `boolean`  
**Default:** `false`  
**Phase:** Phase 5 - Advanced Features

**What It Enables:**
- GitHub Apps integration
- Advanced caching strategies
- Workflow metrics and analytics

**Dependencies:**
- Requires `use_workflow_v2: true`
- Requires `.github/helpers/automation_workflow.py`
- Requires `advanced.github_app` configuration (if using GitHub Apps)

**Example:**
```yaml
feature_flags:
  use_advanced_features: true
```text

**Workflow Usage:**
```yaml
jobs:
  collect-metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Collect metrics
        run: |
          python3 .github/helpers/automation_workflow.py collect-metrics
```text

---

## Branch Policies

### `branch_policies`

**Type:** `object`  
**Description:** Branch-specific configuration for stable branches.

```yaml
branch_policies:
  "stable-1-go-1.24":
    go_version: "1.24"
    locked: false
    end_of_life: "2026-02-15"
    work_stopped: "2025-08-15"
  
  "stable-1-python-3.13":
    python_version: "3.13"
    locked: false
    end_of_life: "2029-10-01"
    work_stopped: null
```text

### Branch Policy Object

#### `go_version`

**Type:** `string`  
**Description:** Locked Go version for this branch.

```yaml
branch_policies:
  "stable-1-go-1.24":
    go_version: "1.24"
```text

**Rules:**
- Must match format from `versions.go`
- Cannot be changed once branch is locked
- Overrides `versions.go.stable-1` for this specific branch

#### `python_version`

**Type:** `string`  
**Description:** Locked Python version for this branch.

```yaml
branch_policies:
  "stable-1-python-3.13":
    python_version: "3.13"
```text

**Rules:**
- Must match format from `versions.python`
- Cannot be changed once branch is locked
- Overrides `versions.python.stable-1` for this specific branch

#### `node_version`

**Type:** `string`  
**Description:** Locked Node.js version for this branch.

```yaml
branch_policies:
  "stable-1-node-20":
    node_version: "20"
```text

#### `rust_version`

**Type:** `string`  
**Description:** Locked Rust version for this branch.

```yaml
branch_policies:
  "stable-1-rust-1.75":
    rust_version: "1.75.0"
```text

#### `locked`

**Type:** `boolean`  
**Default:** `false`  
**Description:** If true, no more changes allowed to this branch.

```yaml
branch_policies:
  "stable-1-go-1.23":
    go_version: "1.23"
    locked: true
```text

**When to Lock:**
- Branch has reached N+2 (two major versions behind)
- 180 days after `work_stopped` date
- Security updates only

**Effects:**
- CI still runs but no feature development
- PRs may be rejected
- Only critical security patches accepted

#### `end_of_life`

**Type:** `string`  
**Format:** `YYYY-MM-DD`  
**Description:** Date when branch reaches end of life.

```yaml
branch_policies:
  "stable-1-go-1.24":
    end_of_life: "2026-02-15"
```text

**Rules:**
- Must be future date when set
- Typically 1-2 years after branch creation
- Aligns with upstream language EOL dates

**After EOL:**
- CI disabled
- No more updates (including security)
- Branch archived

#### `work_stopped`

**Type:** `string`  
**Format:** `YYYY-MM-DD`  
**Description:** Date when active development stopped.

```yaml
branch_policies:
  "stable-1-go-1.24":
    work_stopped: "2025-08-15"
```text

**Rules:**
- Set when branch becomes N+2
- Typically when newer stable branch created
- 180 days later, branch becomes `locked: true`

**After Work Stopped:**
- Only critical bug fixes
- Security patches still accepted
- No new features

### Branch Naming Convention

Stable branches follow this pattern:

```text
stable-1-{language}-{version}
```text

**Examples:**
- `stable-1-go-1.24`
- `stable-1-python-3.13`
- `stable-1-node-20`
- `stable-1-rust-1.75`

**Multi-Language Branches:**
For branches with multiple locked versions:

```text
stable-1-go-1.24-python-3.13
```text

---

## Advanced Configuration

### `advanced`

**Type:** `object`  
**Description:** Advanced configuration for caching, metrics, and GitHub Apps.

```yaml
advanced:
  cache:
    enabled: true
    key_prefix: "v2"
    paths:
      go:
        - "~/go/pkg/mod"
        - "~/.cache/go-build"
  
  metrics:
    enabled: true
    collect_build_times: true
    retention_days: 30
  
  github_app:
    enabled: false
```text

### Cache Configuration

#### `advanced.cache.enabled`

**Type:** `boolean`  
**Default:** `true`  
**Description:** Enable/disable caching system.

```yaml
advanced:
  cache:
    enabled: true
```text

#### `advanced.cache.key_prefix`

**Type:** `string`  
**Default:** `"v2"`  
**Description:** Prefix for cache keys.

```yaml
advanced:
  cache:
    key_prefix: "v2-custom"
```text

**Use Cases:**
- Invalidate all caches: change prefix
- Separate caches per environment
- Version-specific cache keys

#### `advanced.cache.restore_keys`

**Type:** `array` of `string`  
**Description:** Fallback cache keys.

```yaml
advanced:
  cache:
    restore_keys:
      - "v2-"
      - "v1-"
```text

**Behavior:**
- Tries keys in order
- First match used
- Allows cache migration between versions

#### `advanced.cache.paths`

**Type:** `object`  
**Description:** Language-specific cache paths.

```yaml
advanced:
  cache:
    paths:
      go:
        - "~/go/pkg/mod"
        - "~/.cache/go-build"
      python:
        - "~/.cache/pip"
        - ".venv"
      node:
        - "~/.npm"
        - "node_modules"
      rust:
        - "~/.cargo"
        - "target"
```text

**Rules:**
- Paths can use `~` for home directory
- Relative paths from repository root
- Wildcards not supported (use directories)

### Metrics Configuration

#### `advanced.metrics.enabled`

**Type:** `boolean`  
**Default:** `false`  
**Description:** Enable metrics collection.

```yaml
advanced:
  metrics:
    enabled: true
```text

#### `advanced.metrics.collect_build_times`

**Type:** `boolean`  
**Default:** `true`  
**Description:** Collect build duration metrics.

```yaml
advanced:
  metrics:
    collect_build_times: true
```text

**Metrics Collected:**
- Job duration
- Step duration
- Total workflow time

#### `advanced.metrics.collect_test_results`

**Type:** `boolean`  
**Default:** `true`  
**Description:** Collect test result metrics.

```yaml
advanced:
  metrics:
    collect_test_results: true
```text

**Metrics Collected:**
- Test count (passed/failed/skipped)
- Test duration
- Flaky test detection

#### `advanced.metrics.collect_cache_stats`

**Type:** `boolean`  
**Default:** `true`  
**Description:** Collect cache performance metrics.

```yaml
advanced:
  metrics:
    collect_cache_stats: true
```text

**Metrics Collected:**
- Cache hit rate
- Cache size
- Cache restore time

#### `advanced.metrics.retention_days`

**Type:** `integer`  
**Range:** 1-90  
**Default:** `30`  
**Description:** How long to retain metrics.

```yaml
advanced:
  metrics:
    retention_days: 30
```text

### GitHub App Configuration

#### `advanced.github_app.enabled`

**Type:** `boolean`  
**Default:** `false`  
**Description:** Use GitHub App for authentication.

```yaml
advanced:
  github_app:
    enabled: true
```text

**Benefits:**
- Higher API rate limits
- More granular permissions
- Better security than PATs

#### `advanced.github_app.app_id`

**Type:** `string`  
**Description:** GitHub App ID.

```yaml
advanced:
  github_app:
    app_id: "123456"
```text

**Where to Find:**
- GitHub Settings → Developer settings → GitHub Apps
- App settings page shows App ID

#### `advanced.github_app.installation_id`

**Type:** `string`  
**Description:** Installation ID for this repository.

```yaml
advanced:
  github_app:
    installation_id: "12345678"
```text

**Where to Find:**
- Install app to repository/organization
- Installation ID in URL or API response

**Secrets Required:**
- `GH_APP_PRIVATE_KEY`: Private key (PEM format)

---

## Validation Rules

### Schema Validation

The v2 system validates `workflow-versions.yml` on every workflow run.

#### Validation Script

```python
#!/usr/bin/env python3
"""Validate workflow-versions.yml against schema."""

import yaml
import jsonschema
from pathlib import Path


def load_config(config_path: str) -> dict:
    """Load configuration file.
    
    Args:
        config_path: Path to workflow-versions.yml.
    
    Returns:
        dict: Parsed configuration.
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def validate_config(config: dict, schema: dict) -> list:
    """Validate configuration against schema.
    
    Args:
        config: Configuration to validate.
        schema: JSON schema.
    
    Returns:
        list: Validation errors (empty if valid).
    """
    validator = jsonschema.Draft7Validator(schema)
    return list(validator.iter_errors(config))


if __name__ == "__main__":
    config = load_config(".github/workflow-versions.yml")
    schema = load_config(".github/helpers/config-schema.json")
    
    errors = validate_config(config, schema)
    
    if errors:
        print("❌ Validation errors:")
        for error in errors:
            print(f"  - {error.message}")
            print(f"    Path: {'.'.join(str(p) for p in error.path)}")
        exit(1)
    else:
        print("✅ Configuration valid")
```text

### Common Validation Errors

#### Missing Required Field

```yaml
# ❌ Invalid: missing version
use_workflow_v2: true
```text

**Error:**
```text
'version' is a required property
```text

**Fix:**
```yaml
# ✅ Valid
version: "1.0.0"
use_workflow_v2: true
```text

#### Invalid Version Format

```yaml
# ❌ Invalid: not semantic version
version: "1.0"
```text

**Error:**
```text
'1.0' does not match pattern '^\\d+\\.\\d+\\.\\d+$'
```text

**Fix:**
```yaml
# ✅ Valid
version: "1.0.0"
```text

#### Invalid Branch Policy Key

```yaml
# ❌ Invalid: doesn't match pattern
branch_policies:
  "my-branch":
    go_version: "1.24"
```text

**Error:**
```text
'my-branch' does not match pattern '^stable-1-.*$'
```text

**Fix:**
```yaml
# ✅ Valid
branch_policies:
  "stable-1-go-1.24":
    go_version: "1.24"
```text

#### Invalid Action Version

```yaml
# ❌ Invalid: missing 'v' prefix
versions:
  actions:
    checkout: "4"
```text

**Error:**
```text
'4' does not match pattern '^v\\d+$'
```text

**Fix:**
```yaml
# ✅ Valid
versions:
  actions:
    checkout: "v4"
```text

---

## Examples

### Minimal Configuration

Simplest valid configuration:

```yaml
version: "1.0.0"
use_workflow_v2: false
```text

**Use Case:** Repository not using v2 yet.

### Basic v2 Configuration

Enable v2 with minimal features:

```yaml
version: "1.0.0"
use_workflow_v2: true

versions:
  go:
    main: "1.25"
    stable-1: "1.24"

feature_flags:
  use_change_detection: true
  use_matrix_generation: true
```text

**Use Case:** Initial v2 adoption with core CI features.

### Multi-Language Configuration

Support multiple languages:

```yaml
version: "1.0.0"
use_workflow_v2: true

versions:
  go:
    main: "1.25"
    stable-1: "1.24"
  
  python:
    main: "3.14"
    stable-1: "3.13"
  
  node:
    main: "22"
    stable-1: "20"
  
  rust:
    main: "stable"
    stable-1: "stable-1"
  
  actions:
    checkout: "v4"
    setup-go: "v5"
    setup-python: "v5"
    setup-node: "v4"

feature_flags:
  use_change_detection: true
  use_matrix_generation: true
  use_release_automation: true
```text

**Use Case:** Polyglot repository with multiple languages.

### Full Configuration with All Features

Complete configuration with all features enabled:

```yaml
version: "1.0.0"
use_workflow_v2: true

versions:
  go:
    main: "1.25"
    stable-1: "1.24"
    stable-2: "1.23"
  
  python:
    main: "3.14"
    stable-1: "3.13"
  
  node:
    main: "22"
    stable-1: "20"
  
  rust:
    main: "stable"
    stable-1: "1.75.0"
  
  actions:
    checkout: "v4"
    setup-go: "v5"
    setup-python: "v5"
    setup-node: "v4"
    cache: "v4"
    upload-artifact: "v4"
    download-artifact: "v4"

feature_flags:
  use_change_detection: true
  use_matrix_generation: true
  use_release_automation: true
  use_docs_automation: true
  use_maintenance_automation: true
  use_advanced_features: true

branch_policies:
  "stable-1-go-1.24":
    go_version: "1.24"
    python_version: "3.13"
    locked: false
    end_of_life: "2026-02-15"
    work_stopped: "2025-08-15"
  
  "stable-1-go-1.23":
    go_version: "1.23"
    python_version: "3.12"
    locked: true
    end_of_life: "2025-08-01"
    work_stopped: "2025-02-01"

advanced:
  cache:
    enabled: true
    key_prefix: "v2"
    restore_keys:
      - "v2-"
      - "v1-"
    paths:
      go:
        - "~/go/pkg/mod"
        - "~/.cache/go-build"
      python:
        - "~/.cache/pip"
        - ".venv"
      node:
        - "~/.npm"
        - "node_modules"
      rust:
        - "~/.cargo"
        - "target"
  
  metrics:
    enabled: true
    collect_build_times: true
    collect_test_results: true
    collect_cache_stats: true
    retention_days: 30
  
  github_app:
    enabled: true
    app_id: "123456"
    installation_id: "12345678"
```text

**Use Case:** Production setup with all v2 features.

### Configuration for Gradual Rollout

Enable features incrementally:

```yaml
# Week 1: Enable v2 with change detection only
version: "1.0.0"
use_workflow_v2: true

versions:
  go:
    main: "1.25"

feature_flags:
  use_change_detection: true
  use_matrix_generation: false  # Not yet
  use_release_automation: false
  use_docs_automation: false
  use_maintenance_automation: false
  use_advanced_features: false
```text

```yaml
# Week 2: Add matrix generation
version: "1.0.0"
use_workflow_v2: true

versions:
  go:
    main: "1.25"
    stable-1: "1.24"

feature_flags:
  use_change_detection: true
  use_matrix_generation: true  # ← Enabled
  use_release_automation: false
  use_docs_automation: false
  use_maintenance_automation: false
  use_advanced_features: false
```text

```yaml
# Week 3: Add release automation
version: "1.0.0"
use_workflow_v2: true

versions:
  go:
    main: "1.25"
    stable-1: "1.24"

feature_flags:
  use_change_detection: true
  use_matrix_generation: true
  use_release_automation: true  # ← Enabled
  use_docs_automation: false
  use_maintenance_automation: false
  use_advanced_features: false

branch_policies:
  "stable-1-go-1.24":
    go_version: "1.24"
```text

**Use Case:** Safe incremental feature adoption.

---

## Migration Guide

### From v1 to v2

#### Step 1: Create Initial Configuration

```bash
#!/bin/bash
# Create workflow-versions.yml

cat > .github/workflow-versions.yml <<EOF
version: "1.0.0"
use_workflow_v2: false  # Start disabled

versions:
  go:
    main: "1.25"

feature_flags:
  use_change_detection: false
  use_matrix_generation: false
EOF
```text

#### Step 2: Validate Configuration

```bash
#!/bin/bash
# Validate with helper script

python3 .github/helpers/workflow_common.py validate-config \
  --config .github/workflow-versions.yml
```text

#### Step 3: Enable v2 in Test Repository

```yaml
# .github/workflow-versions.yml in test repo
version: "1.0.0"
use_workflow_v2: true  # Enable for testing

versions:
  go:
    main: "1.25"

feature_flags:
  use_change_detection: true  # Test first feature
  use_matrix_generation: false
```text

#### Step 4: Enable Features Incrementally

Follow the gradual rollout example above, enabling one feature per week.

#### Step 5: Create Stable Branches

When creating stable branches:

```yaml
# Add branch policy
branch_policies:
  "stable-1-go-1.24":
    go_version: "1.24"
    locked: false
    end_of_life: "2026-02-15"
```text

#### Step 6: Enable Advanced Features

After all core features working:

```yaml
feature_flags:
  use_advanced_features: true

advanced:
  cache:
    enabled: true
  metrics:
    enabled: true
```text

---

## Summary

The `workflow-versions.yml` configuration file provides:

1. **Centralized Configuration**: Single source of truth for versions and features
2. **Branch-Aware Versioning**: Different versions for main and stable branches
3. **Feature Toggles**: Gradual rollout via feature flags
4. **Validation**: Schema validation ensures correctness
5. **Flexibility**: Advanced configuration for caching, metrics, and GitHub Apps
6. **Safety**: Rollback via `use_workflow_v2: false`

Use this reference when creating or modifying workflow configuration files.
