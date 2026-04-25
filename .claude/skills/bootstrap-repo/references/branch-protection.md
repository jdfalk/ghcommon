# Branch Protection — source of truth

This document specifies the protection ruleset applied to `main` by the bootstrap-repo
skill. The script `apply_branch_protection.sh` mirrors this exactly.

## Endpoint

```
PUT /repos/{owner}/{repo}/branches/main/protection
```

Via `gh`:

```bash
gh api -X PUT "repos/${OWNER}/${REPO}/branches/main/protection" --input -
```

This endpoint requires admin permission on the repo.

## Payload

`<CONTEXTS>` is a JSON array of status check names produced by
`discover_status_checks.py` against the repo's `.github/workflows/` directory.
If empty, `required_status_checks` becomes `null` (no checks required).

```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": <CONTEXTS>
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 0,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": true
}
```

## Per-field rationale

### `required_status_checks`

| Subfield   | Value          | Why                                                                                                                         |
| ---------- | -------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `strict`   | `true`         | Branches must be up-to-date with `main` before merge — combined with `allow_update_branch: true`, this is one button click. |
| `contexts` | autodiscovered | See `discover_status_checks.py`. Contexts are the `jobs.<id>` keys from any workflow that triggers on `pull_request`.       |

### `enforce_admins`: `false`

You're the solo owner. Hotfix-on-main during incidents is more important than ceremonial equality. Flip to `true` when a team forms.

### `required_pull_request_reviews`

| Subfield                          | Value   | Why                                                                                                        |
| --------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------- |
| `required_approving_review_count` | `0`     | Solo maintainer; no human reviewer to wait on. CI is the gate, not approval.                               |
| `dismiss_stale_reviews`           | `true`  | Pushing new commits invalidates prior approvals. Defense against merging a different PR than was reviewed. |
| `require_code_owner_reviews`      | `false` | No CODEOWNERS-based gating; with 0 required reviews this is moot anyway.                                   |
| `require_last_push_approval`      | `false` | Same reasoning — 0 required reviews.                                                                       |

### `required_linear_history`: `true`

Belt-and-suspenders with `allow_rebase_merge: true` / `allow_merge_commit: false`. Even if repo settings drift, the branch protection enforces no merge commits.

### `allow_force_pushes` / `allow_deletions`: both `false`

User policy: disallow all delete. Force-push to `main` is never the right answer; revert is.

### `required_conversation_resolution`: `true`

PR review threads must be resolved before merge. Forces closure on "I'll fix that later" comments. Solo workflow trade-off: one resolve-all click per PR.

### `lock_branch`: `false`

Locking would prevent direct pushes to `main`. With `enforce_admins: false`, you can push directly when needed; locking would override that.

### `restrictions`: `null`

No user/team push restrictions. The protection itself (PR required + status checks) provides the gate.

### `block_creations`: `false`

Ref creation under `main` is allowed (unused for the default branch but required field).

### `allow_fork_syncing`: `true`

Allow forks to sync from upstream — non-controversial; default-on for public repos.

## Status check discovery

The `contexts` array is built by `discover_status_checks.py` with this logic:

1. Glob `.github/workflows/*.yml` and `*.yaml`.
2. For each workflow, parse YAML.
3. Filter to workflows whose `on:` block contains `pull_request` (as key, list element, or `pull_request_target`).
4. Collect `jobs.<id>` keys (the keys, not the `name:` values).
5. Deduplicate, sort.

### Matrix-job caveat

A workflow like:

```yaml
jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
```

produces _check names_ like `build (ubuntu-latest)` and `build (macos-latest)`. The
discovered context is `build` (the job ID), which won't match either.

Trade-off accepted: the matrix checks still run on every PR and are visible in the UI;
they just aren't formally required. `strict: true` ensures the branch is up-to-date,
so any failure that would block in a non-matrix job will still be visible. Making
matrix checks formally required would require expanding the matrix in the protection
config, which would make every matrix change a two-PR affair.

## Edge cases

### Repo has zero workflows

`contexts` is `[]`. `required_status_checks` becomes `null` in the payload (the API
distinguishes "no required checks" from "required checks: empty list"). `apply_branch_protection.sh`
handles this transformation.

### Default branch isn't `main`

Out of scope for this skill. The skill assumes `main`. Adopting a repo with `master`
or another default branch requires renaming the default branch first (manual step).

### `main` doesn't exist yet

Branch protection cannot be applied to a non-existent branch. `bootstrap_repo.sh` ensures
at least one commit exists on `main` before this step runs (initial sync commit).

## Idempotency

`PUT` replaces the entire protection ruleset. Re-running with the same payload yields
the same state. `verify_bootstrap.sh` performs a `GET` and structural diff to confirm.
