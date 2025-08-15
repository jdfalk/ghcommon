#!/bin/bash
# file: .github/scripts/sync-release-detect-language.sh
# version: 1.0.0
# guid: k8l9m0n1-o2p3-q4r5-s6t7-u8v9w0x1y2z3

set -e

FORCE_LANGUAGE="$1"

# If language is forced via input, use that
if [[ "$FORCE_LANGUAGE" != "auto" && "$FORCE_LANGUAGE" != "" ]]; then
    echo "language=$FORCE_LANGUAGE" >> $GITHUB_OUTPUT
    echo "should-release=true" >> $GITHUB_OUTPUT
    echo "Forced language: $FORCE_LANGUAGE"
    exit 0
fi

# Auto-detect based on key files
DETECTED_LANGUAGE=""

# Check for Rust
if [[ -f "Cargo.toml" ]]; then
    DETECTED_LANGUAGE="rust"
# Check for Go
elif [[ -f "go.mod" ]]; then
    DETECTED_LANGUAGE="go"
# Check for Python
elif [[ -f "pyproject.toml" || -f "setup.py" || -f "requirements.txt" ]]; then
    DETECTED_LANGUAGE="python"
# Check for Node.js/JavaScript
elif [[ -f "package.json" ]]; then
    # Check if it's TypeScript
    if [[ -f "tsconfig.json" || -f "*.ts" ]]; then
        DETECTED_LANGUAGE="typescript"
    else
        DETECTED_LANGUAGE="javascript"
    fi
# Default fallback
else
    echo "No supported language detected"
    echo "should-release=false" >> $GITHUB_OUTPUT
    exit 0
fi

echo "language=$DETECTED_LANGUAGE" >> $GITHUB_OUTPUT
echo "should-release=true" >> $GITHUB_OUTPUT
echo "Detected language: $DETECTED_LANGUAGE"
