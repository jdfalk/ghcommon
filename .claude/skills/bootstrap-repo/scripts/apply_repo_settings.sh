#!/usr/bin/env bash
# Apply repository-level settings to OWNER/REPO via gh api PATCH.
# See references/repo-settings.md for the canonical payload and rationale.
#
# Usage:
#   apply_repo_settings.sh <owner> <repo>

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <owner> <repo>" >&2
  exit 2
fi

OWNER="$1"
REPO="$2"

PAYLOAD=$(
  cat <<'JSON'
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
JSON
)

echo "→ Applying repo settings to ${OWNER}/${REPO}"
echo "${PAYLOAD}" | gh api -X PATCH "repos/${OWNER}/${REPO}" --input - >/dev/null
echo "✓ Repo settings applied"

# Clear any interaction-limit so PRs/issues/comments are open to all users.
# (We considered collaborators_only, but GitHub caps the expiry at six_months
# which made the restriction annoying to keep in place.)
gh api -X DELETE "repos/${OWNER}/${REPO}/interaction-limits" >/dev/null 2>&1 || true
echo "✓ Interaction limits cleared"
