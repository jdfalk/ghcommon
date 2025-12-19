#!/bin/bash
# file: scripts/quick-start-guide.sh
# version: 1.0.0
# guid: f6a7b8c9-d0e1-2345-fghi-456789012345

# Quick Start Guide - Execute All Steps in Order
# This script shows the commands to run, but executes them one at a time
# with confirmation to allow review at each step.

set -euo pipefail

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       GitHub Actions Pinning - Quick Start Guide           ║"
echo "╔════════════════════════════════════════════════════════════╗"
echo ""
echo "This guide will walk you through:"
echo "  1. Fixing git issues in release-go-action"
echo "  2. Tagging release-go-action as v2.0.0"
echo "  3. Pinning all actions to commit hashes"
echo "  4. Next steps for workflow conversion"
echo ""

# Step 1: Check release-go-action status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Check release-go-action status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd /Users/jdfalk/repos/github.com/jdfalk/release-go-action

echo "Current git status:"
git status
echo ""

read -p "Do you want to commit and push changes? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "Committing changes..."
  git add -A
  git commit --no-verify -m "feat(action)!: switch to GoReleaser-based approach

BREAKING CHANGE: Complete rewrite to use GoReleaser for Go releases.

This is a major version change (v1 -> v2) due to different input parameters,
workflow approach, and GoReleaser as core build tool.

Files changed:
- action.yml - New GoReleaser-based implementation
- .goreleaser.example.yml - Example configuration for users
- README.md - Updated usage documentation
- TODO.md - Updated task list"

  echo "Pushing to origin main..."
  git push origin main
  echo "✅ Changes committed and pushed"
else
  echo "⏭️  Skipping commit (you can do this manually later)"
fi

echo ""

# Step 2: Tag release-go-action
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Tag release-go-action as v2.0.0"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This will create tags: v2.0.0, v2.0, v2"
echo ""

read -p "Run tagging script? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon
  ./scripts/tag-release-go-v2.sh
  echo "✅ release-go-action tagged as v2.0.0"
else
  echo "⏭️  Skipping tagging (run ./scripts/tag-release-go-v2.sh manually)"
fi

echo ""

# Step 3: Pin actions to hashes
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Pin all actions to commit hashes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This will:"
echo "  - Discover all jdfalk/* actions"
echo "  - Get latest tags and commit hashes"
echo "  - Update workflows to hash@commit # version format"
echo "  - Generate ACTION_VERSIONS.md"
echo ""

read -p "Run pinning script? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon
  python3 scripts/pin-actions-to-hashes.py

  echo ""
  echo "Review changes:"
  git diff .github/workflows/
  echo ""

  read -p "Commit and push changes? (y/n) " -n 1 -r
  echo ""
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add .github/workflows/ ACTION_VERSIONS.md
    git commit -m "chore(workflows): pin actions to commit hashes

Pin all jdfalk/* actions to specific commit hashes with version comments
for security and reproducibility.

Changes:
- Updated all workflow files to use hash@commit # version format
- Generated ACTION_VERSIONS.md reference table
- release-go-action pinned to v2.0.0 (GoReleaser rewrite)

See ACTION_VERSIONS.md for complete version/hash mapping."

    git push origin main
    echo "✅ Changes committed and pushed"
  else
    echo "⏭️  Skipping commit (you can review and commit manually)"
  fi
else
  echo "⏭️  Skipping pinning (run python3 scripts/pin-actions-to-hashes.py manually)"
fi

echo ""

# Final summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ QUICK START COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. Monitor CI status:"
echo "   ./scripts/trigger-and-monitor-ci.sh"
echo ""
echo "2. Review ACTION_VERSIONS.md:"
echo "   cat ACTION_VERSIONS.md"
echo ""
echo "3. Convert workflows to use new actions:"
echo "   - See ACTION_PINNING_PLAN.md Step 5"
echo ""
echo "4. Test and validate everything works"
echo ""
echo "5. Tag all actions as v1.0.0 when ready:"
echo "   ./scripts/tag-actions-v1.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 DOCUMENTATION:"
echo "   - ACTION_PINNING_PLAN.md - Complete strategy"
echo "   - OVERNIGHT_PROGRESS_SUMMARY.md - What was done"
echo "   - TODO.md - Task tracking"
echo ""
echo "🎉 You're 80% done! Just follow the next steps above."
echo ""
