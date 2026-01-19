<!-- file: docs/LINTER_CONFIG_LOCATIONS.md -->
<!-- version: 1.0.0 -->
<!-- guid: 8a9b0c1d-2e3f-4a5b-6c7d-8e9f0a1b2c3d -->
<!-- last-edited: 2026-01-19 -->

# Linter Configuration File Locations in ghcommon

This document provides a comprehensive reference for all linter configuration files in the ghcommon
repository.

## 🎯 Key Finding: All Configs in Root Directory

**IMPORTANT**: Unlike some other repositories, ghcommon stores **ALL** linter configuration files in
the **repository root directory**, not in `.github/linters/`.

This is the correct and preferred approach for Super Linter, as it:

- Keeps configs with the code they govern
- Allows linters to work both in Super Linter and local development
- Avoids symlink complexity
- Follows common repository conventions

## 📁 Complete List of Linter Config Files

### Super Linter Environment Files

| File                  | Location | Purpose                                      |
| --------------------- | -------- | -------------------------------------------- |
| `super-linter-ci.env` | Root     | Super Linter configuration for CI workflows  |
| `super-linter-pr.env` | Root     | Super Linter configuration for PR validation |

### Language-Specific Linter Configs

| Language/Tool             | File                 | Location | Purpose                                |
| ------------------------- | -------------------- | -------- | -------------------------------------- |
| **JavaScript/TypeScript** | `.eslintrc.yml`      | Root     | ESLint configuration                   |
| **Markdown**              | `.markdownlint.json` | Root     | Markdownlint configuration             |
| **YAML**                  | `.yaml-lint.yml`     | Root     | YAML linting rules                     |
| **YAML**                  | `.yamllint`          | Root     | Alternative YAML linter config         |
| **Python**                | `.pylintrc`          | Root     | Pylint configuration                   |
| **Python**                | `ruff.toml`          | Root     | Ruff (Python linter/formatter) config  |
| **Python**                | `.python-black`      | Root     | Black formatter configuration          |
| **Rust**                  | `clippy.toml`        | Root     | Clippy (Rust linter) configuration     |
| **Rust**                  | `rustfmt.toml`       | Root     | Rustfmt (Rust formatter) configuration |
| **Go**                    | `.golangci.yml`      | Root     | GolangCI-Lint configuration            |
| **Prettier**              | `.prettierrc`        | Root     | Prettier formatter configuration       |
| **Prettier**              | `.prettierignore`    | Root     | Prettier ignore patterns               |
| **Commitlint**            | `.commitlintrc.js`   | Root     | Commit message linting rules           |

### Total Count

- **15 configuration files** in root directory
- **0 configuration files** in `.github/linters/`
- **0 symlinks** (all regular files)

## 🚫 What Does NOT Exist

- **`.github/linters/` directory** - Does not exist in ghcommon
- **Symlinks** - No symlinked config files
- **Duplicated configs** - Each linter has one canonical config location

## 📝 Super Linter Configuration Variables

When configuring Super Linter in ghcommon, use these patterns:

### Correct: Point to Root Directory Configs

```bash
# In super-linter-ci.env or super-linter-pr.env
JAVASCRIPT_ES_CONFIG_FILE=.eslintrc.yml
MARKDOWN_CONFIG_FILE=.markdownlint.json
YAML_CONFIG_FILE=.yaml-lint.yml
PYTHON_PYLINT_CONFIG_FILE=.pylintrc
```

### Incorrect: Do NOT Reference .github/linters/

```bash
# ❌ WRONG - This directory doesn't exist in ghcommon
JAVASCRIPT_ES_CONFIG_FILE=.github/linters/.eslintrc.yml
MARKDOWN_CONFIG_FILE=.github/linters/.markdownlint.json
```

## 🔍 Verification Commands

### List All Linter Configs

```bash
# Find all linter config files in root
ls -la | grep -E '(lint|prettier|clippy|rustfmt|ruff|golangci|yamllint|black|commitlint|super-linter)'
```

### Verify No Symlinks

```bash
# Check that configs are regular files, not symlinks
ls -l .markdownlint.json .eslintrc.yml .yaml-lint.yml .pylintrc .golangci.yml | grep -v '^-'
# Should return empty (no non-regular files)
```

### Check for .github/linters/ Directory

```bash
# Verify directory doesn't exist
ls -la .github/linters/
# Should return: "No such file or directory"
```

## 🔄 Comparison with Other Repositories

Different repositories in the jdfalk organization use different approaches:

| Repository                   | Config Location    | Notes                            |
| ---------------------------- | ------------------ | -------------------------------- |
| **ghcommon**                 | Root directory     | All 15 configs in root           |
| **ubuntu-autoinstall-agent** | `.github/linters/` | Uses subdirectory approach       |
| **gcommon-proto**            | Mixed              | Some in root, some in `.github/` |
| **subtitle-manager**         | Root directory     | Similar to ghcommon              |

**Recommendation**: When syncing configurations FROM ghcommon TO other repositories, be aware that
target repositories may use different locations. The sync scripts should handle this appropriately.

## 📚 Related Documentation

- [Super Linter Configuration Strategy](super-linter-config-strategy.md) - To be created in Task 16
- [Super Linter Test Results](super-linter-test-results.md) - To be created after Tasks 17-22
- [General Coding Instructions](../.github/instructions/general-coding.instructions.md) - File
  header requirements
- [PROMPT_CATEGORIZATION.md](PROMPT_CATEGORIZATION.md) - Notes about linter config location
  flexibility

## 🎓 Best Practices for ghcommon

1. **Keep configs in root directory** - Don't create `.github/linters/`
2. **Use regular files, not symlinks** - Ensures Super Linter and local tools work correctly
3. **Reference root paths in Super Linter env files** - Use `TOOL_CONFIG_FILE=.configfile` not
   `.github/linters/.configfile`
4. **Update documentation when adding new linters** - Keep this file current
5. **Test locally before committing** - Ensure linters work with new configs

## 🔧 Maintenance Notes

**Last Verified**: October 12, 2025 **Total Config Files**: 15 **Super Linter Version**: (check
super-linter-ci.env for version)

When adding a new linter:

1. Create config file in root directory
2. Add entry to this document
3. Update Super Linter .env file with `TOOL_CONFIG_FILE=.configname`
4. Test with Super Linter test workflow (Task 17)
5. Update version of this document

---

**Need to update this document?** Follow the direct-edit workflow:

1. Edit this file directly
2. Increment version number (e.g., 1.0.0 → 1.1.0)
3. Commit with conventional commit message
4. See AGENTS.md for workflow details
