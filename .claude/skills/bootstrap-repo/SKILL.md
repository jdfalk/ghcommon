---
name: bootstrap-repo
description: Create a new GitHub repo or apply ghcommon house standards to an existing one. Use when the user says "create a new repo", "bootstrap a repo", "set up a new repo to our standards", "apply our standards to repo X", "make this repo compliant", "new action/library/service repo", or wants merge settings, branch protection, labels, dependabot, and instruction files configured in one shot. Wraps gh repo create, applies repo-level settings (rebase-only, auto-merge, no delete) and branch protection on main, runs ghcommon's label and instruction-file sync scripts, and seeds flavor-specific overlay files.
---

# bootstrap-repo

Apply the full jdfalk/ghcommon house standard to a repo: settings, branch
protection, labels, dependabot, instruction files, flavor overlay.

## When to use

- Creating a brand-new repo (`--mode create`)
- Bringing an existing repo into compliance (`--mode adopt`)
- Re-running for idempotency / drift correction

## How it works

The skill is a thin wrapper. The actual work is in `scripts/bootstrap_repo.sh`,
which orchestrates:

1. `gh repo create` (create mode) or `gh repo view` (adopt mode)
2. `apply_repo_settings.sh` — `PATCH /repos/:o/:r` with merge/visibility settings
3. `ghcommon/scripts/sync-repo-setup.py` — copies instructions, dependabot, etc
4. `ghcommon/scripts/sync-github-labels.py` — applies all labels from `labels.json`
5. Flavor-specific overlay (action.yml, CHANGELOG.md, Dockerfile)
6. Seed `.github/repository-config.yml` with `repository.type: <flavor>`
7. Initial bootstrap commit + push to `main`
8. `apply_branch_protection.sh` — `PUT /repos/:o/:r/branches/main/protection`
9. `verify_bootstrap.sh` — read-back diff against expected state

Steps 2 and 8 are split because branch protection requires `main` to exist.

## Decision tree

**Pick the mode.**

- New repo doesn't exist yet → `--mode create`
- Repo already exists → `--mode adopt`

**Pick the flavor.** See `references/flavors.md` for full file lists.

- Building a GitHub Action → `--flavor action`
- Building a reusable library/SDK/package → `--flavor library`
- Building a deployable service or app → `--flavor service`

## Usage

```bash
# Create a new private library repo
.claude/skills/bootstrap-repo/scripts/bootstrap_repo.sh \
    --flavor library --mode create --name my-new-thing

# Adopt an existing service repo
.claude/skills/bootstrap-repo/scripts/bootstrap_repo.sh \
    --flavor service --mode adopt --name existing-service

# Common flags
#   --owner OWNER         (default: jdfalk)
#   --private | --public  (default: --private; create mode only)
#   --ghcommon PATH       (default: ~/repos/github.com/jdfalk/ghcommon)
#   --repo-path PATH      (skip clone, use this checkout)
#   --skip-protection     (don't apply branch protection)
#   --skip-labels         (don't sync labels)
```

## Verification

After running, `verify_bootstrap.sh` runs automatically and exits non-zero on drift.
Standalone use:

```bash
.claude/skills/bootstrap-repo/scripts/verify_bootstrap.sh \
    --owner jdfalk --repo my-thing --flavor library \
    --repo-path ~/repos/github.com/jdfalk/my-thing
```

## What this skill does NOT do

- **Secrets** — does not seed `CI_APP_ID` or any other secret. Run
  `ghcommon/scripts/setup-ci-app.sh` after bootstrap. Tracked: ghcommon issue #264.
- **Default branch rename** — assumes `main`; manual fix needed for `master` repos.
- **Create org/personal templates** — uses `jdfalk/jft-<flavor>-template` if it
  exists; falls back to empty. The library and service templates don't exist yet.
- **Modify existing files** — `sync-repo-setup.py` is version-aware and won't
  clobber locally-modified files.

## References

- `references/repo-settings.md` — every repo-level setting and why
- `references/branch-protection.md` — protection ruleset and the matrix-job caveat
- `references/flavors.md` — per-flavor file inventory
