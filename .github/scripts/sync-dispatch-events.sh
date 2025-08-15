#!/bin/bash
# file: .github/scripts/sync-dispatch-events.sh
# version: 1.0.0
# guid: e2f3g4h5-i6j7-k8l9-m0n1-o2p3q4r5s6t7

set -e

SYNC_TYPE="$1"
TARGET_REPOS="$2"
GITHUB_REPOSITORY="$3"
GITHUB_SHA="$4"

if [ -z "$SYNC_TYPE" ]; then
    SYNC_TYPE="all"
fi

echo "Dispatching sync events for type: $SYNC_TYPE"

# Convert repos to array and dispatch to each
echo "$TARGET_REPOS" | tr ',' '\n' | while read -r repo; do
    repo=$(echo "$repo" | xargs)  # trim whitespace
    if [ -n "$repo" ]; then
        echo "Dispatching to: $repo"
        gh api repos/$repo/dispatches \
            --method POST \
            --field event_type="sync-from-ghcommon" \
            --field client_payload="{\"sync_type\":\"$SYNC_TYPE\",\"source_repo\":\"$GITHUB_REPOSITORY\",\"source_sha\":\"$GITHUB_SHA\"}" \
            || echo "Failed to dispatch to $repo (repo may not exist or no access)"
    fi
done
