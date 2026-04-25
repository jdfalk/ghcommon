#!/usr/bin/env bash
# Apply branch protection on `main` for OWNER/REPO via gh api PUT.
# See references/branch-protection.md for the canonical payload and rationale.
#
# Status check contexts are autodiscovered from .github/workflows/ in the
# repo's local checkout. If WORKFLOWS_DIR is unset, defaults to
# "${REPO_PATH}/.github/workflows" where REPO_PATH is the third arg.
#
# Usage:
#   apply_branch_protection.sh <owner> <repo> <repo_path>

set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <owner> <repo> <repo_path>" >&2
  exit 2
fi

OWNER="$1"
REPO="$2"
REPO_PATH="$3"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOWS_DIR="${WORKFLOWS_DIR:-${REPO_PATH}/.github/workflows}"

# Discover status check contexts (job IDs from PR-triggering workflows).
if [[ -d ${WORKFLOWS_DIR} ]]; then
  mapfile -t CONTEXTS < <(python3 "${SCRIPT_DIR}/discover_status_checks.py" "${WORKFLOWS_DIR}")
else
  CONTEXTS=()
fi

# Build required_status_checks JSON: null if no contexts, object otherwise.
if [[ ${#CONTEXTS[@]} -eq 0 ]]; then
  REQUIRED_CHECKS_JSON="null"
  echo "→ No PR-triggering workflows found; required_status_checks=null"
else
  CONTEXTS_JSON=$(printf '%s\n' "${CONTEXTS[@]}" | jq -R . | jq -s .)
  REQUIRED_CHECKS_JSON=$(jq -n --argjson c "${CONTEXTS_JSON}" \
    '{strict: true, contexts: $c}')
  echo "→ Discovered ${#CONTEXTS[@]} required check(s): ${CONTEXTS[*]}"
fi

PAYLOAD=$(jq -n --argjson rsc "${REQUIRED_CHECKS_JSON}" '{
    required_status_checks: $rsc,
    enforce_admins: false,
    required_pull_request_reviews: {
        dismiss_stale_reviews: true,
        require_code_owner_reviews: false,
        required_approving_review_count: 0,
        require_last_push_approval: false
    },
    restrictions: null,
    required_linear_history: true,
    allow_force_pushes: false,
    allow_deletions: false,
    block_creations: false,
    required_conversation_resolution: true,
    lock_branch: false,
    allow_fork_syncing: true
}')

echo "→ Applying branch protection on ${OWNER}/${REPO}:main"
echo "${PAYLOAD}" | gh api -X PUT "repos/${OWNER}/${REPO}/branches/main/protection" --input - >/dev/null
echo "✓ Branch protection applied"
