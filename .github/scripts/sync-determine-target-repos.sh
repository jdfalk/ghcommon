#!/bin/bash
# file: .github/scripts/sync-determine-target-repos.sh
# version: 1.0.0
# guid: d1e2f3g4-h5i6-j7k8-l9m0-n1o2p3q4r5s6

set -e

TARGET_REPOS_INPUT="$1"
TARGET_REPOS_ENV="$2"

if [ "$TARGET_REPOS_INPUT" = "all" ] || [ -z "$TARGET_REPOS_INPUT" ]; then
    echo "repos<<EOF" >> $GITHUB_OUTPUT
    echo "$TARGET_REPOS_ENV" >> $GITHUB_OUTPUT
    echo "EOF" >> $GITHUB_OUTPUT
else
    echo "repos=$TARGET_REPOS_INPUT" >> $GITHUB_OUTPUT
fi
