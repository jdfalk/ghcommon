<!-- file: docs/agent-plan.md -->
<!-- version: 1.0.0 -->
<!-- guid: 7f3c1b2a-5d6e-4c8f-9a1b-2c3d4e5f6a7b -->

# Custom Agent Ecosystem and Instruction Consolidation

This document explains the design, rationale, and operating model for our custom
VS Code subagents. It centralizes task-specific guidance inside subagents,
reduces scattered repository-wide instruction files, and aligns all work with
Google Style Guides.

## Goals

- Reduce top-level instruction sprawl by embedding focused rules in subagents.
- Keep a minimal global policy: semantic commits, file headers/versioning, and
  “use VS Code tasks first + MCP GitHub tools for git ops”.
- Align language behavior with Google Style Guides wherever possible.
- Enable the main agent to delegate complex tasks to specialized subagents with
  clear inputs and outputs.

## Guiding Principles

- Subagents should be narrow in scope, with explicit inputs/outputs and clear
  boundaries (what they do, and when not to use them).
- Prefer Google Style Guides as primary references for coding, docs, and
  workflows: <https://google.github.io/styleguide/>
- Retain key global instructions that are truly cross-cutting (e.g.,
  conventional commits, version bump protocol, task/utility usage).
- Document handoffs: each subagent supports “Start Implementation” and “Open in
  Editor” handoffs.

## Catalog of Subagents (Prioritized)

### Core Workflow Agents

**Documentation Curator**

- Purpose: Generate or update docs, READMEs, changelogs, and API notes from
  code/tests/workflows.
- Typical inputs: paths/files to summarize; target doc files; change summaries.
- Typical outputs: updated docs; changelog entries; doc diffs.
- Not for: speculative APIs without code/tests; binary-only repos.
- Style alignment: Google Markdown Style Guide; consistent headings, lists,
  links.

**Lint & Format Conductor**

- Purpose: Unify lint/format across shell, Python, Go, Rust (and optional
  JS/TS).
- Typical inputs: file globs; formatter configs; staged changes.
- Typical outputs: autoreformatted files; violation report; suggested config
  updates.
- Not for: repos mandating CI-only formatting or strict non-local changes.
- Style alignment: Google language style guides; respectful of local configs.

**Test Orchestrator**

- Purpose: Discover/run unit tests with focused selection and coverage deltas.
- Typical inputs: files or test names; environment matrix; test configuration.
- Typical outputs: pass/fail summary; flaky candidates; coverage changes.
- Not for: long-running integrations requiring unavailable infra.
- Style alignment: AAA test structure; language-specific discovery conventions.

**Dependency Auditor**

- Purpose: Audit and propose safe upgrades with lockfile integrity.
- Typical inputs: manifests (e.g., `go.mod`, `Cargo.toml`, `requirements.txt`);
  target ranges.
- Typical outputs: upgrade plan; diffs; lockfile updates; risk notes.
- Not for: compliance-locked pinned builds.
- Style alignment: semantic versioning discipline; minimal-change strategy.

**Git Hygiene Guardian**

- Purpose: Enforce conventional commit headers, branch naming, and PR templates.
- Typical inputs: staged changes; commit message; branch metadata.
- Typical outputs: validation feedback; corrected templates; commit body
  scaffolds.
- Not for: emergency hotfixes demanding speed over format.
- Style alignment: Conventional commits per repository policy.

### Language-Focused Agents

**Python Static Analyzer**

- Purpose: Type/complexity/security-lite checks beyond basic linters; docstring
  verification.
- Typical inputs: paths; analyzer rules; typing goals.
- Typical outputs: warnings with locations; fix hints; docstring gaps.
- Not for: generated code.
- Style alignment: Google Python Style Guide (imports grouping, docstrings,
  typing).

**Go Static Analyzer**

- Purpose: `go vet`, staticcheck, module sanity, build tags; package
  organization.
- Typical inputs: paths; build tags; modules.
- Typical outputs: findings prioritized by severity; suggested fixes.
- Not for: trivial scripts; generated code.
- Style alignment: Google Go Style Guide (imports grouping, comments, errors,
  pkg org).

**Rust Static Analyzer**

- Purpose: Clippy with safety hints; edition alignment; idioms
  (ownership/borrowing).
- Typical inputs: paths; features; edition targets.
- Typical outputs: actionable lint groups; edition updates; unsafe hotspots.
- Not for: generated code.
- Style alignment: Rust community standards (`rustfmt`, `clippy`), consistent
  documentation and error handling.

**Shell Workflow Assistant**

- Purpose: Robustness/portability improvements (set -euo pipefail, quoting,
  error handling).
- Typical inputs: shell scripts; target shells; env assumptions.
- Typical outputs: portability fixes; risk mitigation suggestions.
- Not for: specialized shells or interactive scripts.
- Style alignment: Google Shell Style Guide; heredoc as last resort.

### Protobuf Agents

**Protobuf Builder**

- Purpose: Buf-based code generation across languages; config validation.
- Typical inputs: Buf module/path; generator targets; buf configs.
- Typical outputs: generated sources; logs; lint results.
- Not for: missing canonical Buf config or unsupported custom generators.
- Style alignment: Protobuf Edition 2023; 1-1-1 design; module prefixes; imports
  ordering.

**Protobuf Cycle Resolver**

- Purpose: Detect/resolve import cycles; propose refactor steps and module
  boundaries.
- Typical inputs: `.proto` graph; module boundaries; common types.
- Typical outputs: refactor plan; import rewrites; split suggestions.
- Not for: small single-module schemas with intentional cycles.
- Style alignment: 1-1-1 per-file entity; cross-module common types;
  cycle-avoidance patterns.

### CI/Workflow Agents

**CI Workflow Doctor**

- Purpose: Validate/repair GitHub Actions across languages/runners; reserved
  keyword issues; token policies.
- Typical inputs: workflow files; runner matrix; recent failure logs.
- Typical outputs: fixed YAML; rationale; simulated validation outcomes.
- Not for: enterprise runners you cannot emulate.
- Style alignment: GitHub Actions best practices; permissions; caching;
  deterministic builds.

**Cross-Repo Sync Manager**

- Purpose: Safely propagate shared configs/workflows to target repos with
  exclusions.
- Typical inputs: source paths; target repo lists; exclusions; versioning
  policy.
- Typical outputs: per-repo diffs; sync reports; conflict notes.
- Not for: repos with divergent policy requiring bespoke configs.
- Style alignment: Sync safety checklist; dry-run-first; version bump
  discipline.

### Security/Release Agents

**Security Scanner Coordinator**

- Purpose: SAST/secret/license scans with consistent policy enforcement.
- Typical inputs: codebase; policies; baseline; allowed tools.
- Typical outputs: findings triage; remediation suggestions; false positive
  filters.
- Not for: binary-only repos or policy-restricted scanning.
- Style alignment: Secrets handling; least privilege; dependency security
  practices.

**Release & Version Steward**

- Purpose: Semantic versioning, tag creation, release notes from commits/labels.
- Typical inputs: commit history; PR labels; release type.
- Typical outputs: version bump; tags; release notes.
- Not for: repos not using semantic commits.
- Style alignment: Semver flows; changelog templates; pre-release tags.

**Performance Micro-Bencher**

- Purpose: Add targeted benchmarks and profiling hooks where missing.
- Typical inputs: functions/files; workload hints; benchmark framework choice.
- Typical outputs: benchmark code; profiles; hotspot list.
- Not for: external I/O-bound services without mocks.
- Style alignment: Language-appropriate benchmarking tool guidance.

**Migration Planner**

- Purpose: Plan larger refactors (Go generics; Rust edition updates; Python
  typing adoption).
- Typical inputs: current code; target features/editions; constraints.
- Typical outputs: phased plan; risks; sample diffs (non-binding).
- Not for: greenfield or already-migrated codebases.
- Style alignment: Minimal disruption; test-first; incremental rollout.

## Instruction Consolidation Strategy

### Move Into Subagents

- Language-specific style, lint, and formatting guidance becomes embedded in
  subagent descriptors (short, task-focused).
  - Python: docstrings, typing, imports grouping, naming, AAA tests.
  - Go: imports grouping, comments, error messaging, package organization.
  - Rust: `rustfmt`, `clippy`, naming, error handling, docs.
  - Shell: strict modes, quoting, portability; heredoc last resort.
  - Protobuf: Edition 2023; 1-1-1; module prefixes; canonical imports;
    request/response patterns.
- CI/workflow best practices captured in CI Workflow Doctor (permissions,
  caching, matrices, tokens, pinned actions).
- Security guidelines consolidate under Security Scanner Coordinator.

### Keep as Global Instructions

- Conventional commit standards (see repository
  `commit-messages.instructions.md`).
- Minimal “general coding instructions” for:
  - Required file header + semantic version bump protocol.
  - Use VS Code tasks first; use MCP GitHub tools for git operations.
  - Single pointer to Google Style Guides.
- Protobuf: brief global note referencing Edition 2023 and 1-1-1; deep specifics
  live in protobuf subagents.

## Rollout Order

1. Implement Core: Documentation Curator, Lint & Format Conductor, Test
   Orchestrator, Protobuf Builder, CI Workflow Doctor.
2. Add Language agents: Python/Go/Rust/Shell.
3. Add Dependency Auditor, Git Hygiene Guardian.
4. Add Protobuf Cycle Resolver, Cross-Repo Sync Manager.
5. Add Security Scanner Coordinator, Release & Version Steward.
6. Optional: Performance Micro-Bencher, Migration Planner.

## Delegation & Handoffs

- The Main Agent routes requests to matching subagent(s) based on intent and
  inputs.
- Subagents include narrow, task-scoped instructions and produce structured
  outputs (comments, diffs, plans).
- Each subagent will include handoffs:
  - **Start Implementation**: invokes the appropriate implementation
    agent/tooling.
  - **Open in Editor**: generates an untitled prompt/file for human refinement.

## Google Style Guide References

- Global reference: <https://google.github.io/styleguide/>
- Python: Google Python Style Guide — linting, docstrings, typing, imports, AAA
  tests.
- Go: Google Go Style Guide — imports grouping, comments, errors, pkg
  organization.
- JavaScript/TypeScript: Google JS/TS Style Guides — if applicable.
- Shell: Google Shell Style Guide — strict modes, quoting, heredoc caution.
- HTML/CSS: Google HTML/CSS Guide — if applicable.
- R: Google/Tidyverse R Guide — if applicable.
- Protobuf: Protobuf Style Guide + Edition 2023 — 1-1-1, import order, field
  presence options, message/service patterns.
- Rust: Community standards via `rustfmt`/`clippy` with consistent docs and
  error handling.

Each subagent embeds a short “Style Alignment” note and enforces a practical
subset of these rules.

## Validation & Maintenance

- Validation: After agent creation, use “what subagents can you use?” and trial
  prompts for each agent.
- Maintenance: Update agents when Google guides or repo policies change; keep
  global instructions minimal and stable.
- Auditing: Quarterly pass to ensure subagent instructions remain correct and
  consistent.

## Next Steps

- Scaffold `.agent.md` files for the top 5 agents in the user profile with
  concise descriptions, argument hints, embedded task instructions, and
  handoffs.
- Validate discovery and run small trial tasks for each.
- Proceed down the rollout order, ensuring consolidation of related instruction
  content.
