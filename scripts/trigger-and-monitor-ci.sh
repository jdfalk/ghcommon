#!/bin/bash
# file: scripts/trigger-and-monitor-ci.sh
# version: 1.1.0
# guid: c3d4e5f6-a7b8-9012-cdef-123456789012

set -euo pipefail

ACTIONS=(
  "release-docker-action"
  "release-go-action"
  "release-frontend-action"
  "release-python-action"
  "release-rust-action"
  "release-protobuf-action"
  "auto-module-tagging-action"
)

OWNER="jdfalk"
LOG_DIR="logs/ci-failures"
MAX_WAIT_MINUTES=15
CHECK_INTERVAL=30

mkdir -p "$LOG_DIR"

echo "=========================================="
echo "Triggering CI for GitHub Actions"
echo "=========================================="
echo ""

# Trigger CI on all repos
for action in "${ACTIONS[@]}"; do
  echo "Triggering CI for: $action"

  # Trigger the CI workflow via workflow_dispatch
  if gh workflow run ci.yml --repo "$OWNER/$action"; then
    echo "  ✓ Triggered"
  else
    echo "  ⚠️  Failed to trigger (may not support workflow_dispatch)"

    # Alternative: trigger via empty commit
    echo "  Attempting to trigger via empty commit..."
    cd "${REPO_BASE_DIR:-$HOME/repos}/$action"
    git fetch origin main
    git checkout main
    git pull origin main
    git commit --allow-empty -m "chore: trigger CI"
    git push origin main
    echo "  ✓ Pushed empty commit to trigger CI"
    cd "${REPO_BASE_DIR:-$HOME/repos}/ghcommon"
  fi
  echo ""
done

echo "=========================================="
echo "Waiting 10 seconds for workflows to start..."
echo "=========================================="
sleep 10

# Monitor CI status
echo ""
echo "Starting monitoring..."
echo ""

start_time=$(date +%s)
all_passed=false

while true; do
  current_time=$(date +%s)
  elapsed=$((current_time - start_time))
  elapsed_minutes=$((elapsed / 60))

  if [ $elapsed_minutes -ge $MAX_WAIT_MINUTES ]; then
    echo ""
    echo "=========================================="
    echo "⚠️  TIMEOUT: CI monitoring exceeded $MAX_WAIT_MINUTES minutes"
    echo "=========================================="
    break
  fi

  echo "=========================================="
  echo "GitHub Actions CI Status"
  date
  echo "Elapsed: ${elapsed_minutes}m / ${MAX_WAIT_MINUTES}m"
  echo "=========================================="
  echo ""

  all_success=true
  all_failed=true
  failed_actions=()

  for action in "${ACTIONS[@]}"; do
    # Get the latest CI workflow run status
    status=$(gh run list \
      --repo "$OWNER/$action" \
      --workflow=ci.yml \
      --limit 1 \
      --json conclusion \
      --jq '.[0].conclusion // "in_progress"')

    if [ "$status" = "success" ]; then
      echo "$action: ✓ PASSED"
      all_failed=false
    elif [ "$status" = "failure" ]; then
      echo "$action: ✗ FAILED"
      failed_actions+=("$action")
      all_success=false
    elif [ "$status" = "in_progress" ] || [ "$status" = "null" ] || [ "$status" = "" ]; then
      echo "$action: ⏳ RUNNING"
      all_success=false
      all_failed=false
    else
      echo "$action: ⚠️  $status"
      all_success=false
      all_failed=false
    fi
  done

  echo ""

  # Check if all passed
  if $all_success; then
    echo "=========================================="
    echo "✓ All CI workflows passed!"
    echo "=========================================="
    all_passed=true
    break
  fi

  # Check if all failed
  if $all_failed; then
    echo "=========================================="
    echo "✗ All CI workflows failed!"
    echo "Collecting failure logs..."
    echo "=========================================="

    for action in "${ACTIONS[@]}"; do
      echo ""
      echo "Fetching logs for: $action"
      log_file="$LOG_DIR/${action}_$(date +%Y%m%d_%H%M%S).log"

      # Get the run ID
      run_id=$(gh run list \
        --repo "$OWNER/$action" \
        --workflow=ci.yml \
        --limit 1 \
        --json databaseId \
        --jq '.[0].databaseId')

      if [ -n "$run_id" ] && [ "$run_id" != "null" ]; then
        echo "  Run ID: $run_id"
        echo "  Saving to: $log_file"
        gh run view "$run_id" --repo "$OWNER/$action" --log >"$log_file" 2>&1 || true
        echo "  ✓ Saved"
      else
        echo "  ⚠️  No run found"
      fi
    done

    echo ""
    echo "=========================================="
    echo "Failure logs saved to: $LOG_DIR"
    echo "=========================================="
    exit 1
  fi

  # If some failed, collect their logs
  if [ ${#failed_actions[@]} -gt 0 ]; then
    echo "Collecting logs for failed actions..."
    echo ""

    for action in "${failed_actions[@]}"; do
      log_file="$LOG_DIR/${action}_$(date +%Y%m%d_%H%M%S).log"

      # Get the run ID
      run_id=$(gh run list \
        --repo "$OWNER/$action" \
        --workflow=ci.yml \
        --limit 1 \
        --json databaseId \
        --jq '.[0].databaseId')

      if [ -n "$run_id" ] && [ "$run_id" != "null" ]; then
        echo "  $action: Saving logs to $log_file"
        gh run view "$run_id" --repo "$OWNER/$action" --log >"$log_file" 2>&1 || true
      fi
    done
    echo ""
  fi

  echo "=========================================="
  echo "Waiting for CI to complete..."
  echo "Next check in $CHECK_INTERVAL seconds..."
  echo "=========================================="
  sleep $CHECK_INTERVAL
done

if $all_passed; then
  echo ""
  echo "=========================================="
  echo "✓ Ready to proceed with tagging!"
  echo "=========================================="
  exit 0
else
  echo ""
  echo "=========================================="
  echo "⚠️  CI did not fully pass. Review logs in: $LOG_DIR"
  echo "=========================================="
  exit 1
fi
