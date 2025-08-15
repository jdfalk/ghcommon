#!/bin/bash
# file: .github/scripts/sync-receiver-sync-files.sh
# version: 1.0.0
# guid: g4h5i6j7-k8l9-m0n1-o2p3-q4r5s6t7u8v9

set -e

SYNC_TYPE="$1"

echo "Performing sync of type: $SYNC_TYPE"

# Create directories if they don't exist
mkdir -p .github/workflows
mkdir -p .github/instructions
mkdir -p .github/prompts
mkdir -p .github/scripts
mkdir -p scripts
mkdir -p .github/linters

case "$SYNC_TYPE" in
    "all"|"workflows")
        echo "Syncing workflows..."
        # Copy specific workflows (not sync workflows to avoid recursion)
        cp ghcommon-source/.github/workflows/pr-automation.yml .github/workflows/ 2>/dev/null || true
        cp ghcommon-source/.github/workflows/release*.yml .github/workflows/ 2>/dev/null || true
        ;;&
    "all"|"instructions")
        echo "Syncing instructions..."
        cp ghcommon-source/.github/copilot-instructions.md .github/ 2>/dev/null || true
        cp ghcommon-source/.github/instructions/* .github/instructions/ 2>/dev/null || true
        ;;&
    "all"|"prompts")
        echo "Syncing prompts..."
        cp -r ghcommon-source/.github/prompts/* .github/prompts/ 2>/dev/null || true
        ;;&
    "all"|"scripts")
        echo "Syncing scripts..."
        cp -r ghcommon-source/scripts/* scripts/ 2>/dev/null || true
        cp -r ghcommon-source/.github/scripts/* .github/scripts/ 2>/dev/null || true
        chmod +x .github/scripts/sync-*.sh 2>/dev/null || true
        ;;&
    "all"|"linters")
        echo "Syncing linters..."
        cp -r ghcommon-source/.github/linters/* .github/linters/ 2>/dev/null || true
        ;;&
    "all"|"labels")
        echo "Syncing labels..."
        cp ghcommon-source/labels.json . 2>/dev/null || true
        cp ghcommon-source/labels.md . 2>/dev/null || true
        ;;
esac

# Create symlinks for linters
# Create .vscode directory if it doesn't exist
mkdir -p .vscode

# Create symlink to linters directory if it exists and .vscode/linters doesn't already exist
if [ -d ".github/linters" ] && [ ! -e ".vscode/linters" ]; then
    ln -sf ../.github/linters .vscode/linters
    echo "Created symlink: .vscode/linters -> ../.github/linters"
fi
