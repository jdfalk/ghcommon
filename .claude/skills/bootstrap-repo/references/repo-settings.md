# Repository Settings — source of truth

This document is the canonical specification for repository-level settings applied
by the bootstrap-repo skill. The script `apply_repo_settings.sh` mirrors this exactly.
If they ever disagree, this doc wins.

## Endpoint

```
PATCH /repos/{owner}/{repo}
```

Via `gh`:

```bash
gh api -X PATCH "repos/${OWNER}/${REPO}" --input -
```

## Payload

```json
{
  "allow_merge_commit": false,
  "allow_squash_merge": false,
  "allow_rebase_merge": true,
  "allow_auto_merge": true,
  "delete_branch_on_merge": false,
  "allow_update_branch": true,
  "has_issues": true,
  "has_projects": false,
  "has_wiki": false,
  "web_commit_signoff_required": false
}
```

## Per-field rationale

| Field                         | Value   | Why                                                                                                                                                    |
| ----------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `allow_merge_commit`          | `false` | Merge commits clutter history with non-linear topology; rebase-only keeps `git log` readable.                                                          |
| `allow_squash_merge`          | `false` | Squash merges discard the in-PR commit history that `git bisect` and reviewers benefit from. Conventional commits within a PR are first-class history. |
| `allow_rebase_merge`          | `true`  | Linear history. The only allowed merge style.                                                                                                          |
| `allow_auto_merge`            | `true`  | PRs can be marked auto-merge once required checks pass; reduces context-switching.                                                                     |
| `delete_branch_on_merge`      | `false` | User policy: disallow all delete. Branches are kept post-merge so old refs resolve.                                                                    |
| `allow_update_branch`         | `true`  | The "Update branch" button on PRs; keeps branches in sync with `main` without local pulls.                                                             |
| `has_issues`                  | `true`  | Used by dependabot, labeler workflows, and AI agent issue creation flows.                                                                              |
| `has_projects`                | `false` | Repo-level Projects (classic) are deprecated UX; org-level Projects supersede.                                                                         |
| `has_wiki`                    | `false` | Wikis are not versioned with code, not searchable via `grep`, and tend to rot. Documentation lives in-repo.                                            |
| `web_commit_signoff_required` | `false` | DCO sign-off enforcement breaks GitHub web edits and AI bot commits (Claude, Copilot). Identity is already assured by gh CLI auth and PR review.       |

## Settings deliberately not in payload

These exist on the GitHub API but are intentionally not set by this skill:

- `description`, `homepage`, `topics` — content-level; set per-repo by humans.
- `private` — set at create time, not bootstrap time. Adoption mode never changes visibility.
- `archived` — never auto-toggled; user-initiated only.
- `default_branch` — left as `main` (default). Renaming the default branch breaks too much downstream tooling to be done implicitly.
- `security_and_analysis.*` — set via separate org-level policy; skill doesn't override.

## Idempotency

`PATCH` is idempotent. Re-running with the same payload is a no-op from the user's
perspective; the API returns the current state regardless of whether anything changed.
The `verify_bootstrap.sh` script GETs the same fields and diffs against this payload
to confirm.
