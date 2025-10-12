<!-- file: docs/SUPER_LINTER_CONFIG_COMPARISON.md -->
<!-- version: 1.0.0 -->
<!-- guid: 9b0c1d2e-3f4a-5b6c-7d8e-9f0a1b2c3d4e -->

# Super Linter Configuration Comparison

This document compares Super Linter configurations across different repositories to identify best practices and ensure consistency.

## Repositories Compared

1. **ghcommon** - Workflow infrastructure repository
2. **ubuntu-autoinstall-agent** - Rust-based automation tool

## Configuration File Locations

| Repository               | Config Location              | Notes               |
| ------------------------ | ---------------------------- | ------------------- |
| ghcommon                 | `super-linter-ci.env` (root) | All configs in root |
| ubuntu-autoinstall-agent | `super-linter-ci.env` (root) | All configs in root |

**Finding**: Both repositories use the root directory approach, which is the preferred pattern.

## Version Comparison

| Repository               | Version | Status                               |
| ------------------------ | ------- | ------------------------------------ |
| ghcommon                 | 1.1.0   | Base version                         |
| ubuntu-autoinstall-agent | 1.1.3   | More recent (3 patch versions ahead) |

## Core Configuration

### Identical Settings

Both repositories share the same core configuration:

```bash
VALIDATE_ALL_CODEBASE=false
DEFAULT_BRANCH=main
DISABLE_ERRORS=false
LOG_LEVEL=INFO
CREATE_LOG_FILE=true
```

## Language Validation Differences

### Languages in Both Repositories

| Language       | ghcommon                            | ubuntu-autoinstall-agent            | Notes     |
| -------------- | ----------------------------------- | ----------------------------------- | --------- |
| Bash/Shell     | ✅ VALIDATE_BASH=true                | ✅ VALIDATE_BASH=true                | Identical |
| Bash Exec      | ✅ VALIDATE_BASH_EXEC=true           | ✅ VALIDATE_BASH_EXEC=true           | Identical |
| Docker         | ✅ VALIDATE_DOCKERFILE_HADOLINT=true | ✅ VALIDATE_DOCKERFILE_HADOLINT=true | Identical |
| EditorConfig   | ✅ VALIDATE_EDITORCONFIG=true        | ✅ VALIDATE_EDITORCONFIG=true        | Identical |
| Environment    | ✅ VALIDATE_ENV=true                 | ✅ VALIDATE_ENV=true                 | Identical |
| GitHub Actions | ✅ VALIDATE_GITHUB_ACTIONS=true      | ✅ VALIDATE_GITHUB_ACTIONS=true      | Identical |
| HTML           | ✅ VALIDATE_HTML=true                | ✅ VALIDATE_HTML=true                | Identical |
| JSON           | ✅ VALIDATE_JSON=true                | ✅ VALIDATE_JSON=true                | Identical |
| JSONC          | ✅ VALIDATE_JSONC=true               | ✅ VALIDATE_JSONC=true               | Identical |
| Markdown       | ✅ VALIDATE_MARKDOWN=true            | ✅ VALIDATE_MARKDOWN=true            | Identical |
| Protobuf       | ✅ VALIDATE_PROTOBUF=true            | ✅ VALIDATE_PROTOBUF=true            | Identical |
| Rust 2021      | ✅ VALIDATE_RUST_2021=true           | ✅ VALIDATE_RUST_2021=true           | Identical |
| Rust Clippy    | ✅ VALIDATE_RUST_CLIPPY=true         | ✅ VALIDATE_RUST_CLIPPY=true         | Identical |
| Shell Format   | ✅ VALIDATE_SHELL_SHFMT=true         | ✅ VALIDATE_SHELL_SHFMT=true         | Identical |
| YAML           | ✅ VALIDATE_YAML=true                | ✅ VALIDATE_YAML=true                | Identical |

### Languages Only in ghcommon

| Language              | ghcommon                                       | Reason                                |
| --------------------- | ---------------------------------------------- | ------------------------------------- |
| Go                    | ✅ VALIDATE_GO=true                             | ghcommon has Go code                  |
| JavaScript/TypeScript | ✅ Enabled (all variants)                       | ghcommon has JS/TS workflow scripts   |
| Python                | ✅ Enabled (Black, Pylint, Flake8, Isort, Ruff) | ghcommon has extensive Python scripts |
| XML                   | ✅ VALIDATE_XML=true                            | ghcommon may have XML configs         |

### Languages Disabled in ubuntu-autoinstall-agent

| Language              | ubuntu-autoinstall-agent | Reason            |
| --------------------- | ------------------------ | ----------------- |
| Go                    | ❌ Commented out          | Rust-only project |
| JavaScript/TypeScript | ❌ Explicitly disabled    | No JS/TS code     |
| Python                | ❌ Commented out          | Rust-only project |
| XML                   | ❌ Commented out          | Not needed        |

## Configuration File References

### ghcommon (Root Directory Paths)

```bash
# JavaScript/TypeScript
JAVASCRIPT_ES_CONFIG_FILE=.eslintrc.yml
TYPESCRIPT_ES_CONFIG_FILE=.eslintrc.yml

# Python
PYTHON_BLACK_CONFIG_FILE=.python-black
PYTHON_PYLINT_CONFIG_FILE=.pylintrc

# Markdown
MARKDOWN_CONFIG_FILE=.markdownlint.json

# YAML
YAML_CONFIG_FILE=.yaml-lint.yml

# Rust
RUST_CLIPPY_CONFIG_FILE=clippy.toml
```

**Pattern**: All paths are relative to root directory (no `.github/linters/` prefix)

### ubuntu-autoinstall-agent (Mixed Approach)

```bash
# Commented out (would use .github/linters/ if enabled):
# JAVASCRIPT_ES_CONFIG_FILE=.github/linters/.eslintrc.yml
# TYPESCRIPT_ES_CONFIG_FILE=.github/linters/.eslintrc.yml
# PYTHON_BLACK_CONFIG_FILE=.github/linters/.python-black
# PYTHON_PYLINT_CONFIG_FILE=.github/linters/.pylintrc

# Active configs (root directory):
# MARKDOWN_CONFIG_FILE=.markdownlint.json  # Commented but shows root pattern
YAML_CONFIG_FILE=.yaml-lint.yml
RUST_CLIPPY_CONFIG_FILE=clippy.toml
```

**Pattern**: Active configs use root directory paths, but commented-out configs show legacy `.github/linters/` approach

## Filter Exclusions

Both repositories use **identical** filter regex:

```bash
FILTER_REGEX_EXCLUDE=.*(vendor|node_modules|\.git|\.vscode|\.pb\.go|_pb2\.py|\.generated\.|\.min\.|\.map|coverage|\.tmp|dist|build).*
```

This excludes:

- `vendor/` and `node_modules/` - Dependency directories
- `.git/` and `.vscode/` - VCS and IDE directories
- `.pb.go` and `_pb2.py` - Generated protobuf files
- `.generated.`, `.min.`, `.map` - Generated/minified files
- `coverage/`, `.tmp/`, `dist/`, `build/` - Build artifacts

## Key Differences Summary

| Aspect                | ghcommon                                 | ubuntu-autoinstall-agent |
| --------------------- | ---------------------------------------- | ------------------------ |
| **Version**           | 1.1.0                                    | 1.1.3 (newer)            |
| **Languages**         | Multi-language (Go, Python, JS/TS, Rust) | Rust-focused             |
| **Config Paths**      | All root directory                       | All root directory       |
| **Python Validation** | 5 validators enabled                     | Commented out            |
| **Go Validation**     | Enabled                                  | Commented out            |
| **JS/TS Validation**  | All variants enabled                     | Explicitly disabled      |

## Recommendations

### For ghcommon

1. ✅ **Config paths are correct** - Using root directory for all configs
2. ✅ **Language coverage is appropriate** - Matches repository's multi-language nature
3. ⚠️ **Consider version update** - ubuntu-autoinstall-agent is on v1.1.3 (3 patches ahead)
4. ✅ **Filter exclusions are comprehensive**

### For Cross-Repository Consistency

1. **Adopt root directory pattern** - Both repositories should use root directory for all linter configs
2. **Remove `.github/linters/` references** - Even in comments, to avoid confusion
3. **Sync versions** - Update ghcommon to v1.1.3 or higher
4. **Document config file locations** - Each repository should document where its linter configs live

## Action Items

### Immediate (Priority)

1. Update ghcommon's super-linter-ci.env version from 1.1.0 to 1.1.3
2. Ensure all `*_CONFIG_FILE` variables point to root directory (already correct)
3. Review and update MARKDOWN_CONFIG_FILE to be explicitly set (currently implicit)

### Future Enhancements

1. Create shared base configuration that both repositories can extend
2. Document configuration patterns in SUPER_LINTER_CONFIG_STRATEGY.md (Task 16)
3. Test configurations with Super Linter test workflow (Tasks 17-22)

## Configuration Best Practices Learned

From comparing these two repositories:

1. **Use root directory for all linter configs** - Simpler and more standard
2. **Explicitly disable unused validators** - Clearer than commenting them out
3. **Keep filter regex comprehensive** - Exclude all generated/vendor content
4. **Match validators to repository languages** - Don't enable validators for languages you don't use
5. **Version your configuration files** - Include version in file header
6. **Document deviations** - Comment why certain validators are disabled

## Related Documentation

- [Linter Config Locations](LINTER_CONFIG_LOCATIONS.md) - Where configs are stored in ghcommon
- [Super Linter Config Strategy](super-linter-config-strategy.md) - To be created in Task 16
- [Super Linter Test Results](super-linter-test-results.md) - To be created after Tasks 17-22

---

**Document Version**: 1.0.0
**Last Updated**: October 12, 2025
**Compared Repositories**: 2 (ghcommon v1.1.0, ubuntu-autoinstall-agent v1.1.3)
**Next Review**: After implementing Task 15 config updates
