# bootstrap-repo skill

## Goal

Add a `bootstrap-repo` skill at `.claude/skills/bootstrap-repo/` that creates a
new GitHub repo (or adopts an existing one) and applies the full ghcommon house
standard: merge settings, branch protection, labels, dependabot, instruction
files, and flavor-specific overlays for action / library / service repos. The
skill orchestrates existing ghcommon scripts where they exist
(`sync-repo-setup.py`, `sync-github-labels.py`) and fills the one real gap —
repo settings + branch protection — with new shell scripts calling `gh api`
directly.

In parallel, a Haiku subagent splits `ACTION_REPO_STANDARDS.md` into three
flavor docs, audits `labels.json` against live repos, and updates `AGENTS.md` /
`CLAUDE.md` to point at the new structure.

## Affected files

### New (this PR)

- `.claude/skills/bootstrap-repo/SKILL.md` — thin trigger doc + flavor decision
  tree, <100 lines
- `.claude/skills/bootstrap-repo/scripts/bootstrap_repo.sh` — main entry;
  orchestrates 1–9 below
- `.claude/skills/bootstrap-repo/scripts/apply_repo_settings.sh` —
  `gh api PATCH /repos/:o/:r` with the agreed JSON
- `.claude/skills/bootstrap-repo/scripts/apply_branch_protection.sh` —
  `gh api PUT /repos/:o/:r/branches/main/protection`; autodiscovers status
  checks from `.github/workflows/*.yml` job IDs (only workflows with
  `pull_request` trigger)
- `.claude/skills/bootstrap-repo/scripts/discover_status_checks.py` — YAML
  parser; outputs newline-separated job IDs
- `.claude/skills/bootstrap-repo/scripts/verify_bootstrap.sh` — reads back
  settings + protection, diffs against expected, exits non-zero on drift
- `.claude/skills/bootstrap-repo/references/repo-settings.md` — exact JSON +
  rationale per setting
- `.claude/skills/bootstrap-repo/references/branch-protection.md` — protection
  payload + matrix-job caveat
- `.claude/skills/bootstrap-repo/references/flavors.md` — action vs library vs
  service file lists, derived from new `docs/standards/`

### Touched (this PR)

- `AGENTS.md` — add bootstrap-repo skill to skills index (only if subagent
  hasn't already)

### Out of scope (separate PR by Haiku subagent, parallel)

- `docs/standards/action-repo.md`, `library-repo.md`, `service-repo.md`,
  `README.md` — split from `ACTION_REPO_STANDARDS.md`
- `docs/label-audit-2026-04-24.md` — diff of `labels.json` vs live
  `gh api repos/:o/:r/labels` across all active jdfalk repos, with proposed
  colors/descriptions
- `AGENTS.md`, `CLAUDE.md` — pointers to new standards docs

### Out of scope (future, tracked separately)

- Secret provisioning automation — issue
  [#264](https://github.com/jdfalk/ghcommon/issues/264)
- Creating `jft-library-template` and `jft-service-template` — done after skill
  stabilizes by running the skill against empty repos and flipping
  `isTemplate: true`

## Confirmed design decisions

| Decision                                   | Value                                                                                                                                                                                                                                             |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Owner default                              | hardcoded `jdfalk`, override via `--owner`                                                                                                                                                                                                        |
| Status check discovery                     | parse YAML `jobs.<id>` keys from workflows triggering on `pull_request`; matrix expansions accepted as visible-but-not-required                                                                                                                   |
| `web_commit_signoff_required`              | **off**                                                                                                                                                                                                                                           |
| `required_conversation_resolution`         | **on**                                                                                                                                                                                                                                            |
| `enforce_admins`                           | **off**                                                                                                                                                                                                                                           |
| `has_issues` / `has_wiki` / `has_projects` | **on / off / off**                                                                                                                                                                                                                                |
| Merge settings                             | rebase-only (`allow_merge_commit: false`, `allow_squash_merge: false`, `allow_rebase_merge: true`), `allow_auto_merge: true`, `delete_branch_on_merge: false`, `allow_update_branch: true`, `allow_deletions: false`, `allow_force_pushes: false` |
| Required approvals                         | 0 (with `dismiss_stale_reviews: true`)                                                                                                                                                                                                            |
| Secrets                                    | manual checklist printed; not seeded                                                                                                                                                                                                              |
| Subagent dispatch                          | parallel, file-scope split                                                                                                                                                                                                                        |

## Steps

Each step is a single conventional commit on `feat/bootstrap-repo-skill`.

1. **Scaffold skill via init_skill.py.**
   `python ~/.claude/skills/skill-creator/scripts/init_skill.py bootstrap-repo --path .claude/skills/`.
   Delete the example files we won't use.
2. **Write `references/repo-settings.md` and
   `references/branch-protection.md`.** These are the source of truth — script
   payloads will mirror them. Documenting first prevents drift.
3. **Write `scripts/discover_status_checks.py`.** Pure function: dir → list of
   job IDs. Unit-testable in isolation.
4. **Write `scripts/apply_repo_settings.sh` and
   `scripts/apply_branch_protection.sh`.** Each is a single `gh api` call with
   payload from step 2's docs. Idempotent (PATCH/PUT semantics).
5. **Write `scripts/bootstrap_repo.sh`.** The orchestrator. Flavor flag, mode
   flag, owner flag, ghcommon-path resolution, calls 3–4 in order, then shells
   out to ghcommon's `sync-repo-setup.py` and `sync-github-labels.py`, then
   flavor overlay copy, then commit/push, then `verify_bootstrap.sh`.
6. **Write `scripts/verify_bootstrap.sh`.** Reads back via `gh api GET`, diffs
   against expected, prints a colored summary. Used both inline at end of
   bootstrap and standalone for adoption auditing.
7. **Write `references/flavors.md`.** Enumerates per-flavor file lists; must
   align with what subagent puts in `docs/standards/`. If subagent's PR isn't
   merged yet, link to the docs by anticipated path with a note.
8. **Write `SKILL.md`.** Thin: trigger description, flavor decision tree,
   call-out to `scripts/bootstrap_repo.sh`. Cite references for "why".
9. **Dry-run on a throwaway repo.** Create `jdfalk/bootstrap-test-DELETE-ME`
   (private), run skill in adopt mode, verify settings stuck, run again to
   confirm idempotency, delete repo.
10. **Open PR.** Title `feat: add bootstrap-repo skill`. Reference issue #264.

## Parallel work (Haiku subagent, dispatched at step 1)

Self-contained prompt; no shared writes with the skill PR.

- **Audit labels.json** against live labels in all non-archived `jdfalk/*` repos
  (use `gh api`). Output `docs/label-audit-2026-04-24.md` with: missing labels
  per repo, labels in `labels.json` not used anywhere, suggested
  colors/descriptions for the 242 grey entries grouped by prefix (`tech:`,
  `priority:`, `size:`, `type:`).
- **Split** `ACTION_REPO_STANDARDS.md` into `docs/standards/action-repo.md`,
  `library-repo.md`, `service-repo.md`, plus `docs/standards/README.md` index.
  Library and service variants extrapolate from the action variant by removing
  action-specific files (`action.yml`, `ruff.toml` for non-Python) and adding
  service-specific ones (Dockerfile, deployment section).
- **Update** `AGENTS.md` and `CLAUDE.md` to link new docs.
- **Open separate PR** titled
  `docs: split repo standards by flavor and audit labels`.
- **Hard constraint**: write only under `docs/standards/`,
  `docs/label-audit-*.md`, `AGENTS.md`, `CLAUDE.md`. Do not touch `.claude/`,
  `scripts/`, `labels.json` (audit only — actual changes proposed in the audit
  doc for human review), `.github/`.

## Test strategy

**Unit-ish** (run from worktree):

```
# YAML parsing produces expected job IDs against ghcommon's own workflows
python .claude/skills/bootstrap-repo/scripts/discover_status_checks.py .github/workflows/

# Shellcheck on every shell script
shellcheck .claude/skills/bootstrap-repo/scripts/*.sh
```

**Integration** (against throwaway repo, step 9):

```
# Create private throwaway
gh repo create jdfalk/bootstrap-test-DELETE-ME --private --description "DELETE ME" --add-readme
# Run skill in adopt mode
.claude/skills/bootstrap-repo/scripts/bootstrap_repo.sh \
    --flavor library --mode adopt --name bootstrap-test-DELETE-ME

# Verify expected state
.claude/skills/bootstrap-repo/scripts/verify_bootstrap.sh \
    --owner jdfalk --repo bootstrap-test-DELETE-ME --flavor library

# Idempotency: run bootstrap again, expect zero diffs from verify
.claude/skills/bootstrap-repo/scripts/bootstrap_repo.sh \
    --flavor library --mode adopt --name bootstrap-test-DELETE-ME
.claude/skills/bootstrap-repo/scripts/verify_bootstrap.sh \
    --owner jdfalk --repo bootstrap-test-DELETE-ME --flavor library

# Clean up
gh repo delete jdfalk/bootstrap-test-DELETE-ME --yes
```

**Success criteria:**

- `verify_bootstrap.sh` exits 0 on first run after bootstrap.
- Second bootstrap run produces zero file diffs in the worktree (`git status`
  clean) and `verify_bootstrap.sh` still exits 0.
- Branch protection on `main` is visible in GitHub UI with the agreed settings.
- All 242 labels are present on the throwaway repo.
- `shellcheck` passes on all scripts.

## Rollback

- Worktree: `git worktree remove ../ghcommon-bootstrap-repo-skill --force` from
  main repo.
- Throwaway repo: `gh repo delete jdfalk/bootstrap-test-DELETE-ME --yes`.
- Subagent's PR: close without merge if its proposed label colors are wrong; the
  audit doc itself is non-destructive.
- This PR: revert single commit on `main` if the skill ever ships and turns out
  to be net-negative; the skill is additive and doesn't modify any existing
  scripts.
