#!/usr/bin/env bash
# Verify a repository matches ghcommon bootstrap expectations.
# Reads back repo settings + branch protection via gh api and diffs against
# the canonical payload from references/repo-settings.md and branch-protection.md.
#
# Exits 0 on full match, 1 on any drift, 2 on usage error.
#
# Usage:
#   verify_bootstrap.sh --owner OWNER --repo REPO \
#                       [--repo-path PATH] [--flavor FLAVOR]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

OWNER=""
REPO=""
REPO_PATH=""
FLAVOR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
  --owner)
    OWNER="$2"
    shift 2
    ;;
  --repo)
    REPO="$2"
    shift 2
    ;;
  --repo-path)
    REPO_PATH="$2"
    shift 2
    ;;
  --flavor)
    FLAVOR="$2"
    shift 2
    ;;
  *)
    echo "unknown arg: $1" >&2
    exit 2
    ;;
  esac
done

[[ -z ${OWNER} || -z ${REPO} ]] && {
  echo "usage: $0 --owner OWNER --repo REPO [--repo-path PATH] [--flavor FLAVOR]" >&2
  exit 2
}

DRIFT=0

# ---------- repo settings ----------

EXPECTED_SETTINGS=$(
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

echo "→ Checking repo settings on ${OWNER}/${REPO}"
ACTUAL=$(gh api "repos/${OWNER}/${REPO}")
while IFS= read -r key; do
  expected=$(echo "${EXPECTED_SETTINGS}" | jq -r ".${key}")
  actual=$(echo "${ACTUAL}" | jq -r ".${key}")
  if [[ ${expected} != "${actual}" ]]; then
    echo "  ✗ ${key}: expected=${expected} actual=${actual}"
    DRIFT=1
  fi
done < <(echo "${EXPECTED_SETTINGS}" | jq -r 'keys[]')

if [[ ${DRIFT} -eq 0 ]]; then
  echo "  ✓ Repo settings match"
fi

# ---------- branch protection ----------

echo "→ Checking branch protection on ${OWNER}/${REPO}:main"
PROTECTION=$(gh api "repos/${OWNER}/${REPO}/branches/main/protection" 2>/dev/null || echo "")

if [[ -z ${PROTECTION} ]]; then
  echo "  ✗ No protection on main"
  DRIFT=1
else
  check() {
    local path="$1" expected="$2"
    local actual
    actual=$(echo "${PROTECTION}" | jq -r "${path}")
    if [[ ${actual} != "${expected}" ]]; then
      echo "  ✗ ${path}: expected=${expected} actual=${actual}"
      DRIFT=1
    fi
  }
  # required_status_checks may be null (no PR-triggering workflows). Only check
  # .strict when the object exists.
  HAS_RSC=$(echo "${PROTECTION}" | jq -r '.required_status_checks != null')
  if [[ ${HAS_RSC} == "true" ]]; then
    check '.required_status_checks.strict' 'true'
  fi
  check '.enforce_admins.enabled' 'false'
  check '.required_pull_request_reviews.dismiss_stale_reviews' 'true'
  check '.required_pull_request_reviews.required_approving_review_count' '0'
  check '.required_linear_history.enabled' 'true'
  check '.allow_force_pushes.enabled' 'false'
  check '.allow_deletions.enabled' 'false'
  check '.required_conversation_resolution.enabled' 'true'

  # Status check contexts: compare against discover_status_checks output
  if [[ -n ${REPO_PATH} && -d "${REPO_PATH}/.github/workflows" ]]; then
    EXPECTED_CONTEXTS=$(python3 "${SCRIPT_DIR}/discover_status_checks.py" \
      "${REPO_PATH}/.github/workflows" | sort)
    ACTUAL_CONTEXTS=$(echo "${PROTECTION}" |
      jq -r '.required_status_checks.contexts[]?' | sort)
    if [[ ${EXPECTED_CONTEXTS} != "${ACTUAL_CONTEXTS}" ]]; then
      echo "  ✗ status check contexts drift:"
      diff <(echo "${EXPECTED_CONTEXTS}") <(echo "${ACTUAL_CONTEXTS}") || true
      DRIFT=1
    fi
  fi

  if [[ ${DRIFT} -eq 0 ]]; then
    echo "  ✓ Branch protection matches"
  fi
fi

# ---------- summary ----------

if [[ ${DRIFT} -eq 0 ]]; then
  echo ""
  echo "✅ ${OWNER}/${REPO} is bootstrap-compliant${FLAVOR:+ (${FLAVOR})}"
  exit 0
else
  echo ""
  echo "❌ ${OWNER}/${REPO} has drift; re-run bootstrap_repo.sh to fix"
  exit 1
fi
