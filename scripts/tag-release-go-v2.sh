#!/bin/bash
# file: scripts/tag-release-go-v2.sh
# version: 1.0.0
# guid: c3d4e5f6-a7b8-9012-cdef-123456789012

set -euo pipefail

# Tag release-go-action as v2.0.0 (breaking change)
cd "${REPO_BASE_DIR:-$HOME/repos}/release-go-action"

echo "🏷️  Tagging release-go-action as v2.0.0..."

# Create annotated tag
git tag -a v2.0.0 -m "v2.0.0 - GoReleaser-based Release Action

BREAKING CHANGE: Complete rewrite to use GoReleaser for Go releases.

This is a major version change (v1 -> v2) due to:
- Different input parameters (GoReleaser config vs manual builds)
- Different workflow approach (GoReleaser as core)
- Simplified action interface

Key Changes:
- Uses GoReleaser for all build/release operations
- Supports .goreleaser.yml configuration
- Cross-platform builds via GoReleaser
- Automatic changelog generation
- Docker image builds (if configured)

Migration Guide:
1. Add .goreleaser.yml to your repository
2. Update workflow to use v2 action
3. Remove manual build steps
4. Configure GoReleaser for your needs

See .goreleaser.example.yml for configuration examples."

# Push tag
git push origin v2.0.0

# Create v2 and v2.0 tags (for major/minor tracking)
git tag -f v2 -m "v2 - Latest v2.x.x release"
git tag -f v2.0 -m "v2.0 - Latest v2.0.x release"
git push -f origin v2 v2.0

echo "✅ Tagged release-go-action: v2.0.0, v2.0, v2"
echo ""
echo "Commit hash for pinning:"
git rev-parse --short HEAD
