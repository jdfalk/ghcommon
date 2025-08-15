#!/bin/bash
# file: .github/scripts/sync-generate-summary.sh
# version: 1.0.0
# guid: f3g4h5i6-j7k8-l9m0-n1o2-p3q4r5s6t7u8

set -e

SYNC_TYPE="$1"
TARGET_REPOS="$2"
GITHUB_SHA="$3"

echo "## Sync Dispatch Summary" >> $GITHUB_STEP_SUMMARY
echo "- **Sync Type:** ${SYNC_TYPE:-all}" >> $GITHUB_STEP_SUMMARY
echo "- **Target Repos:** $TARGET_REPOS" >> $GITHUB_STEP_SUMMARY
echo "- **Source SHA:** $GITHUB_SHA" >> $GITHUB_STEP_SUMMARY
