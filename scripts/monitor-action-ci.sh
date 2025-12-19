#!/bin/bash
# file: scripts/monitor-action-ci.sh
# version: 1.0.0
# guid: b2c3d4e5-f6a7-8901-bcde-f12345678901

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

echo "Monitoring CI status for GitHub Actions..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
  clear
  echo "=========================================="
  echo "GitHub Actions CI Status"
  date
  echo "=========================================="
  echo ""

  all_passing=true

  for action in "${ACTIONS[@]}"; do
    printf "%-30s " "$action:"

    status=$(gh run list --repo "$OWNER/$action" --limit 1 --json status,conclusion --jq '.[0]')
    run_status=$(echo "$status" | jq -r '.status')
    conclusion=$(echo "$status" | jq -r '.conclusion // "running"')

    if [ "$run_status" = "completed" ]; then
      if [ "$conclusion" = "success" ]; then
        echo "✓ PASSED"
      else
        echo "✗ FAILED ($conclusion)"
        all_passing=false
      fi
    else
      echo "⟳ IN PROGRESS"
      all_passing=false
    fi
  done

  echo ""
  echo "=========================================="
  if [ "$all_passing" = true ]; then
    echo "✓ All CI workflows passing!"
    echo "Ready to tag with: ./scripts/tag-actions-v1.sh"
    break
  else
    echo "Waiting for CI to complete..."
    echo "Next check in 30 seconds..."
  fi
  echo "=========================================="

  sleep 30
done
