#!/bin/bash
# file: .github/scripts/sync-receiver-generate-summary.sh
# version: 1.0.0
# guid: j7k8l9m0-n1o2-p3q4-r5s6-t7u8v9w0x1y2

set -e

SYNC_TYPE="$1"
SOURCE_REPO="$2"
SOURCE_SHA="$3"
HAS_CHANGES="$4"

echo "## Sync Receiver Summary" >> $GITHUB_STEP_SUMMARY
echo "- **Sync Type:** $SYNC_TYPE" >> $GITHUB_STEP_SUMMARY
echo "- **Source Repo:** $SOURCE_REPO" >> $GITHUB_STEP_SUMMARY
echo "- **Source SHA:** $SOURCE_SHA" >> $GITHUB_STEP_SUMMARY
echo "- **Changes Made:** $HAS_CHANGES" >> $GITHUB_STEP_SUMMARY
