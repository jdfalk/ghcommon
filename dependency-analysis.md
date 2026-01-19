<!-- file: dependency-analysis.md -->
<!-- version: 2.1.0 -->
<!-- guid: a1b2c3d4-e5f6-7890-1234-567890abcdef -->
<!-- last-edited: 2026-01-19 -->

# Dependency Analysis for ghcommon Repository

**Analysis Date:** November 1, 2025 **Purpose:** Map all file dependencies to
identify unused files and cleanup opportunities **Status:** ✅ **COMPLETE**

> Update (v2.1.0): Analyzer now supports CLI options, default excludes, and a
> "full" mode for large Mermaid/DOT outputs. See enhancements and usage below.

## 📊 Executive Summary

The comprehensive dependency analysis has been completed successfully!

### Key Statistics

- Latest run (with default excludes and full output):
- root: 1,503 files
- docs: 163 files
- scripts: 62 files
- workflows: 59 files
- tools: 2 files
- templates: 4 files
- examples: 16 files
- tests: 13 files
- Potentially Unused Files (current): 320
- Note: Category totals are listed individually; the root category overlaps with
  subfolders.

### Files Generated

All analysis outputs are located in the `dependency-analysis/` directory:

1. **dependencies.txt** - ASCII art dependency graph
2. **dependencies.dot** - Graphviz DOT format (can generate PNG with:
   `dot -Tpng dependencies.dot -o dependencies.png`)
3. **dependencies.mermaid.md** - Mermaid.js graph for GitHub rendering
4. **dependencies.html** - Interactive HTML report (open in browser)
5. **dependencies.json** - Raw JSON data for programmatic analysis
6. **analysis.log** - Complete progress log

---

## ✨ Enhancements (v2.1.0)

- Added CLI with options:
- `--root` to select the analysis root
- `--exclude` to skip noisy directories (default: `.git,node_modules,.venv`)
- `--full` to remove Mermaid node/edge limits (enables very large graphs)
- `--mermaid-max-files`, `--mermaid-max-edges` to tune Mermaid output size
- `--log-level` to adjust verbosity
- Fixed HTML generation robustness and improved logging.
- Explanation of size differences:
- Mermaid intentionally defaults to conservative limits for readability and
  performance; JSON/DOT/ASCII are exhaustive. Use `--full` to lift limits.

### How to run

From the repository root (uses the repo’s virtualenv):

- Full graph with default excludes:
- `/Users/jdfalk/repos/github.com/jdfalk/ghcommon/.venv/bin/python analyze-dependencies.py --root . --exclude .git,node_modules,.venv --full`
- Tuned Mermaid limits (example):
- `/Users/jdfalk/repos/github.com/jdfalk/ghcommon/.venv/bin/python analyze-dependencies.py --root . --mermaid-max-files 500 --mermaid-max-edges 5000`

## Analysis Progress

### Phase 1: Root Directory Files ✅

- ✅ Scanned root directory
- ✅ Found 1,495 files (including .venv)
- ✅ Tracked references

### Phase 2: Documentation Files ✅

- ✅ Scanned docs/ directory
- ✅ Found 163 documentation files
- ✅ Mapped cross-references

### Phase 3: Scripts ✅

- ✅ Scanned scripts/ directory
- ✅ Found 61 script files
- ✅ Mapped script dependencies

### Phase 4: Workflows ✅

- ✅ Scanned .github/workflows/
- ✅ Found 53 workflow files
- ✅ Mapped reusable workflow calls

### Phase 5: Supporting Directories ✅

- ✅ tools/ - 2 files
- ✅ templates/ - 4 files
- ✅ examples/ - 16 files
- ✅ tests/ - 13 files

---

## 🎯 Recommendations for Cleanup

### High Priority (Safe to Remove)

Based on the orphan analysis, the following categories likely contain unused
files:

1. **Virtual Environment (.venv/)** - Majority of orphans
   - **Action:** Exclude .venv/ from repository (add to .gitignore)
   - **Impact:** Removes ~1,200 files

2. **Old Documentation Artifacts**
   - Cross-registry-todos with many parts
   - Refactor documents that may be outdated
   - **Action:** Review and archive or remove

3. **Duplicate/Legacy Scripts**
   - Multiple versions of similar scripts
   - **Action:** Consolidate and remove duplicates

### Medium Priority (Requires Review)

1. **Workflow Templates**
   - Some example files may not be actively used
   - **Action:** Audit which are referenced in documentation

2. **Test Files**
   - Verify all test files are run by CI
   - **Action:** Review test coverage

3. **Configuration Files**
   - Multiple linter configs at root
   - **Action:** Consolidate where possible

### Low Priority (Keep)

1. **Core Workflows** (.github/workflows/)
2. **Active Scripts** (scripts/ with dependencies)
3. **Main Documentation** (README.md, CONTRIBUTING.md, etc.)
4. **Templates** (templates/workflows/)

---

## Detailed Findings

### Root Directory Files

**Total:** 1,495 files (mostly from .venv/)

**Key Active Files:**

- README.md - Main documentation
- package.json - Node dependencies
- requirements.txt - Python dependencies
- Various config files (.golangci.yml, .pylintrc, etc.)
