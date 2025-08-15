#!/bin/bash
# file: .github/scripts/sync-receiver-commit-push.sh
# version: 1.0.0
# guid: i6j7k8l9-m0n1-o2p3-q4r5-s6t7u8v9w0x1

set -e

SOURCE_REPO="$1"
SOURCE_SHA="$2"
SYNC_TYPE="$3"

git config --local user.email "action@github.com"
git config --local user.name "GitHub Action"
git add .
git commit -m "sync: update files from ghcommon

Source: $SOURCE_REPO
SHA: $SOURCE_SHA
Sync type: $SYNC_TYPE"
git push
