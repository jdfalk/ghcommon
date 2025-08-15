#!/bin/bash
# file: .github/scripts/sync-receiver-check-changes.sh
# version: 1.0.0
# guid: h5i6j7k8-l9m0-n1o2-p3q4-r5s6t7u8v9w0

set -e

if git diff --quiet; then
    echo "has_changes=false" >> $GITHUB_OUTPUT
    echo "No changes detected"
else
    echo "has_changes=true" >> $GITHUB_OUTPUT
    echo "Changes detected:"
    git diff --name-only
fi
