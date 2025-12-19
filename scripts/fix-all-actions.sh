#!/bin/bash
# file: scripts/fix-all-actions.sh
# version: 1.0.0
# guid: c5d1e2f3-4a5b-6c7d-8e9f-0a1b2c3d4e5f

set -euo pipefail

REPOS=(
  "release-docker-action"
  "release-go-action"
  "release-frontend-action"
  "release-python-action"
  "release-protobuf-action"
  "auto-module-tagging-action"
)

LOGS_DIR="logs/action-fixes"
mkdir -p "$LOGS_DIR"

echo "=========================================="
echo "Fixing All GitHub Actions"
date
echo "=========================================="
echo ""

for repo in "${REPOS[@]}"; do
  echo "=== Analyzing $repo ==="

  # Get latest run ID
  RUN_ID=$(gh run list --repo "jdfalk/$repo" --limit 1 \
    --json databaseId --jq '.[0].databaseId')

  if [ -z "$RUN_ID" ]; then
    echo "No runs found for $repo"
    continue
  fi

  # Save failed logs
  LOG_FILE="$LOGS_DIR/${repo}-latest.log"
  gh run view "$RUN_ID" --repo "jdfalk/$repo" --log-failed >"$LOG_FILE" 2>&1 || true

  echo "Logs saved to: $LOG_FILE"

  # Extract key errors
  echo "Key errors:"
  grep -i "error\|failed" "$LOG_FILE" | head -5 || echo "No obvious errors found"

  echo ""
done

echo "=========================================="
echo "Analysis complete. Review logs in $LOGS_DIR"
echo "=========================================="
