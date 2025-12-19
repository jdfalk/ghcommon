#!/bin/bash
# file: scripts/tag-actions-v1.sh
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7890-abcd-ef1234567890

set -euo pipefail

# Action repositories to tag
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
VERSION="1.0.0"

echo "=========================================="
echo "Tagging GitHub Actions v${VERSION}"
echo "=========================================="
echo ""

for action in "${ACTIONS[@]}"; do
  echo "Processing: $action"
  echo "---"

  cd "/Users/jdfalk/repos/github.com/jdfalk/$action"

  # Check if CI is passing
  echo "  Checking CI status..."
  if ! gh run list --repo "$OWNER/$action" --limit 1 --json conclusion --jq '.[0].conclusion' | grep -q "success"; then
    echo "  ⚠️  WARNING: Latest CI run not successful. Check: https://github.com/$OWNER/$action/actions"
    read -p "  Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "  Skipping $action"
      continue
    fi
  else
    echo "  ✓ CI passing"
  fi

  # Fetch latest
  echo "  Fetching latest changes..."
  git fetch --all --tags

  # Create/update tags with force
  echo "  Creating tags: v${VERSION}, v1.0, v1"
  git tag -f "v${VERSION}"
  git tag -f "v1.0"
  git tag -f "v1"

  # Push tags with force
  echo "  Pushing tags..."
  git push -f origin "v${VERSION}"
  git push -f origin "v1.0"
  git push -f origin "v1"

  echo "  ✓ Tagged: https://github.com/$OWNER/$action/releases"
  echo ""
done

echo "=========================================="
echo "All actions tagged successfully!"
echo "=========================================="
echo ""
echo "Tagged repositories:"
for action in "${ACTIONS[@]}"; do
  echo "  - https://github.com/$OWNER/$action/releases/tag/v${VERSION}"
done
echo ""
echo "Note: Tags v1.0.0, v1.0, and v1 have been created/updated with force."
echo "GitHub Releases will be created automatically by the release workflows."
