# Cross-Registry Workflow Tasks - Quick Reference

## What Has Been Created

### Directory Structure

```
/Users/jdfalk/repos/github.com/jdfalk/ghcommon/docs/cross-registry-todos/
├── README.md (298 lines) - Master index and execution guide
├── TASK_GENERATION_STATUS.md (463 lines) - Tracking document for all 20 tasks
├── task-01-fix-yaml-syntax.md (552 lines) - Fix YAML cache restore-keys
├── task-02-docker-packages.md (932 lines) - Verify Docker package publishing
└── task-03-rust-packages.md (1,350 lines) - Implement Rust crate publishing
```

**Total Created**: 3,595 lines across 5 files **Remaining to Create**: 17 task files (~36,000+
lines)

## Key Issues Addressed

### 1. YAML Syntax Error (Task 01)

**Problem**: Trailing hyphens in cache restore-keys in `release-rust.yml` lines 231-236
**Solution**: Remove trailing hyphens from all three cache blocks **Status**: Ready to implement

### 2. GitHub Packages Publishing (Tasks 02-07)

**Problem**: Only Docker images are published to ghcr.io; Rust/Go/Python/Frontend/Protobuf artifacts
are not published **Solution**: Add publishing steps to each release-\*.yml workflow **Status**:

- Docker (Task 02): Verification task - already working ✅
- Rust (Task 03): Detailed implementation plan created
- Go/Python/Frontend/Protobuf (Tasks 04-07): Need to be created

### 3. CI Workflow Consolidation (Tasks 08-10)

**Problem**:

- `ghcommon/.github/workflows/ci.yml` - Simple wrapper that calls reusable-ci.yml
- `ghcommon/.github/workflows/reusable-ci.yml` - Basic reusable workflow with limited features
- `ubuntu-autoinstall-agent/.github/workflows/ci.yml` - Full-featured CI with many advanced
  capabilities

**Solution**: Merge the best features from both into an enhanced reusable-ci.yml that both repos can
use **Status**: Analysis and implementation plans need to be created

### 4. Repository Config Integration (Tasks 11-14)

**Problem**: Workflows use hardcoded values and workflow_dispatch inputs instead of reading from
`repository-config.yml` **Solution**: Create config loader and integrate it into all reusable
workflows **Status**: Design and implementation plans need to be created

### 5. Script Extraction (Tasks 15-17)

**Problem**: Many inline Python/Bash scripts in workflows make them hard to maintain and test
**Solution**: Extract scripts to `.github/workflows/scripts/` directory **Status**: Extraction plans
need to be created

### 6. Testing & Validation (Tasks 18-20)

**Problem**: Need comprehensive testing of all changes **Solution**: Create testing strategies for
packages, workflows, and config **Status**: Testing plans need to be created

## Task File Structure

Each task file follows this comprehensive structure:

1. **Header** (50-100 lines): Metadata, overview, prerequisites
2. **Current State Analysis** (200-400 lines): What exists now, what's missing
3. **Design Section** (300-600 lines): Architecture, decisions, alternatives
4. **Implementation Steps** (800-1,500 lines): Detailed step-by-step with complete code
5. **Validation** (400-600 lines): Testing and verification procedures
6. **Troubleshooting** (500-800 lines): Common issues and solutions
7. **Testing Strategy** (300-500 lines): How to test the changes
8. **Post-Implementation** (200-300 lines): Documentation and follow-up
9. **Resources** (100-200 lines): Links and references

**Total per task**: 2,000-4,000 lines of actionable, detailed content

## Key Design Principles

### Idempotency

All tasks check current state before making changes:

```bash
# Always check first
if [ condition ]; then
  echo "Already done, skipping"
else
  perform_action
fi
```

### Independence

Each task can be completed without dependencies on others

### Completeness

Every command includes:

- What it does
- Expected output
- How to interpret results
- What to do if it fails

### Safety

All tasks include:

- Backup procedures
- Validation steps
- Rollback instructions
- Error handling

## Repository Context

### ghcommon Repository

- **Path**: `/Users/jdfalk/repos/github.com/jdfalk/ghcommon`
- **Purpose**: Central workflow infrastructure hub
- **Key Files**:
  - `.github/workflows/reusable-*.yml` - Reusable workflows
  - `.github/workflows/release-*.yml` - Release orchestrators
  - `.github/repository-config.yml` - Configuration schema
  - `scripts/` - Python automation tools

### ubuntu-autoinstall-agent Repository

- **Path**: `/Users/jdfalk/repos/github.com/jdfalk/ubuntu-autoinstall-agent`
- **Purpose**: Rust application for Ubuntu autoinstall
- **Key Files**:
  - `.github/workflows/ci.yml` - Full-featured CI (source of truth)
  - `Cargo.toml` - Rust project configuration
  - Will consume enhanced workflows from ghcommon

## Workflow Dispatch Limit

**Critical constraint**: GitHub Actions allows maximum 10 inputs on `workflow_dispatch`

When consolidating workflows, inputs must be organized intelligently:

- Group related options
- Use sensible defaults
- Consider boolean flags vs choice inputs
- Prioritize most commonly changed values

## Environment Variable Policy

**Rule**: Never use GitHub context variables directly in scripts

❌ **Wrong**:

```bash
run: |
  echo "Ref: ${{ github.ref }}"
  if [ "${{ github.event_name }}" = "push" ]; then
```

✅ **Correct**:

```bash
env:
  GITHUB_REF: ${{ github.ref }}
  GITHUB_EVENT_NAME: ${{ github.event_name }}
run: |
  echo "Ref: $GITHUB_REF"
  if [ "$GITHUB_EVENT_NAME" = "push" ]; then
```

## Commit Message Format

All commits MUST use conventional commits:

```
type(scope): brief description

Detailed explanation of what changed and why.

Changes:
- Bullet point list of specific changes
- Include file names and what was modified
- Note any breaking changes

Related to task: task-XX-name
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `perf`, `build`

## Next Steps for AI Agent

### Immediate Tasks (Priority 1 - Packages)

1. Create `task-04-go-packages.md` (~2,000 lines)
2. Create `task-05-python-packages.md` (~2,000 lines)
3. Create `task-06-frontend-packages.md` (~2,000 lines)
4. Create `task-07-protobuf-packages.md` (~2,000 lines)

### Follow-up Tasks (Priority 2 - CI)

5. Create `task-08-analyze-ci-workflows.md` (~4,000 lines)
6. Create `task-09-consolidate-ci-workflows.md` (~4,000 lines)
7. Create `task-10-update-ci-callers.md` (~4,000 lines)

### Remaining Tasks (Priority 3-5)

8-14. Config integration tasks 15-17. Script extraction tasks 18-20. Testing and validation tasks

## Quality Checklist

Each task file must:

- [ ] Be completely actionable (copy-paste executable)
- [ ] Include all necessary commands with expected outputs
- [ ] Have comprehensive error handling
- [ ] Include rollback procedures
- [ ] Be idempotent (can run multiple times safely)
- [ ] Be independent (no hard dependencies on other tasks)
- [ ] Have 2,000-4,000 lines of useful content
- [ ] Include validation steps
- [ ] Include troubleshooting section
- [ ] Update file version headers when modifying files

## File Naming Convention

```
task-[number]-[short-description].md
```

Examples:

- `task-01-fix-yaml-syntax.md`
- `task-08-analyze-ci-workflows.md`
- `task-15-extract-ci-scripts.md`

## Documentation Standards

### Code Blocks Must Include

```yaml
# 1. Comments explaining what the code does
# 2. Why this approach was chosen
# 3. What the expected outcome is
# 4. Common pitfalls to avoid

- name: Example Step
  run: |
    echo "Clear description of what happens"
    command --with --flags
```

### Commands Must Include

```bash
# Description of what we're checking
command --to --run

# Expected output:
# Show what success looks like
# Explain how to interpret results
```

### Validation Must Include

- Syntax validation
- Logical validation
- Integration validation
- End-to-end validation
- Performance validation (where applicable)

## Success Metrics

A task is considered complete when:

1. File is created with 2,000-4,000 lines
2. All sections are present and detailed
3. All code examples are complete (no placeholders)
4. All commands are tested and working
5. Troubleshooting covers 10-15 issues
6. Validation procedures are comprehensive
7. No markdown linting errors (or documented exceptions)
8. File committed with proper conventional commit message

## Current Status

**Created**: 5 files, 3,595 lines (8.8% of 40,000 line goal) **In Progress**: None **Next**: Create
task-04 through task-20 (17 files remaining)

---

**For AI Agent**: Start with task-04-go-packages.md and follow the same comprehensive format
established in task-03-rust-packages.md. Each task should be 2,000-4,000 lines with complete,
actionable instructions.
