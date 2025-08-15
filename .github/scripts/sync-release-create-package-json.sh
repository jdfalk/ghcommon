#!/bin/bash
# file: .github/scripts/sync-release-create-package-json.sh
# version: 1.0.0
# guid: c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f

set -euo pipefail

# Create package.json for semantic-release based on language type
# Usage: sync-release-create-package-json.sh <language>

LANGUAGE="${1:-}"

if [[ -z "$LANGUAGE" ]]; then
    echo "Error: Language parameter required"
    echo "Usage: $0 <language>"
    exit 1
fi

echo "Creating package.json for $LANGUAGE project..."

case "$LANGUAGE" in
    "rust")
        cat > package.json << 'EOF'
{
  "name": "rust-project",
  "version": "0.0.0-development",
  "private": true,
  "devDependencies": {
    "@semantic-release/changelog": "^6.0.3",
    "@semantic-release/git": "^10.0.1",
    "@semantic-release/github": "^9.2.6",
    "@semantic-release/exec": "^6.0.3",
    "semantic-release": "^22.0.12",
    "conventional-changelog-conventionalcommits": "^7.0.2"
  }
}
EOF
        ;;
    "go")
        cat > package.json << 'EOF'
{
  "name": "go-project",
  "version": "0.0.0-development",
  "private": true,
  "devDependencies": {
    "@semantic-release/changelog": "^6.0.3",
    "@semantic-release/git": "^10.0.1",
    "@semantic-release/github": "^9.2.6",
    "@semantic-release/exec": "^6.0.3",
    "semantic-release": "^22.0.12",
    "conventional-changelog-conventionalcommits": "^7.0.2"
  }
}
EOF
        ;;
    "python")
        cat > package.json << 'EOF'
{
  "name": "python-project",
  "version": "0.0.0-development",
  "private": true,
  "devDependencies": {
    "@semantic-release/changelog": "^6.0.3",
    "@semantic-release/git": "^10.0.1",
    "@semantic-release/github": "^9.2.6",
    "@semantic-release/exec": "^6.0.3",
    "semantic-release": "^22.0.12",
    "conventional-changelog-conventionalcommits": "^7.0.2"
  }
}
EOF
        ;;
    "javascript"|"typescript")
        cat > package.json << 'EOF'
{
  "name": "js-ts-project",
  "version": "0.0.0-development",
  "private": true,
  "devDependencies": {
    "@semantic-release/changelog": "^6.0.3",
    "@semantic-release/git": "^10.0.1",
    "@semantic-release/github": "^9.2.6",
    "@semantic-release/npm": "^11.0.3",
    "semantic-release": "^22.0.12",
    "conventional-changelog-conventionalcommits": "^7.0.2"
  }
}
EOF
        ;;
    *)
        echo "Error: Unsupported language: $LANGUAGE"
        exit 1
        ;;
esac

echo "Package.json created successfully for $LANGUAGE"
