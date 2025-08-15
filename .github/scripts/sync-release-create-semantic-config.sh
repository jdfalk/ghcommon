#!/bin/bash
# file: .github/scripts/sync-release-create-semantic-config.sh
# version: 1.0.0
# guid: d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a

set -euo pipefail

# Create semantic-release configuration based on language type
# Usage: sync-release-create-semantic-config.sh <language>

LANGUAGE="${1:-}"

if [[ -z "$LANGUAGE" ]]; then
    echo "Error: Language parameter required"
    echo "Usage: $0 <language>"
    exit 1
fi

echo "Creating semantic-release config for $LANGUAGE project..."

# Base configuration for all languages
BASE_CONFIG='{
  "branches": ["main"],
  "plugins": [
    [
      "@semantic-release/commit-analyzer",
      {
        "preset": "conventionalcommits",
        "releaseRules": [
          {"type": "feat", "release": "minor"},
          {"type": "fix", "release": "patch"},
          {"type": "perf", "release": "patch"},
          {"type": "revert", "release": "patch"},
          {"type": "docs", "release": false},
          {"type": "style", "release": false},
          {"type": "chore", "release": false},
          {"type": "refactor", "release": "patch"},
          {"type": "test", "release": false},
          {"type": "build", "release": false},
          {"type": "ci", "release": false},
          {"breaking": true, "release": "major"}
        ]
      }
    ],
    [
      "@semantic-release/release-notes-generator",
      {
        "preset": "conventionalcommits"
      }
    ]'

case "$LANGUAGE" in
    "rust")
        cat > .releaserc.json << EOF
${BASE_CONFIG},
    [
      "@semantic-release/exec",
      {
        "prepareCmd": "sed -i 's/^version = \".*\"/version = \"\\\${nextRelease.version}\"/' Cargo.toml"
      }
    ],
    [
      "@semantic-release/changelog",
      {
        "changelogFile": "CHANGELOG.md"
      }
    ],
    [
      "@semantic-release/git",
      {
        "assets": ["Cargo.toml", "CHANGELOG.md"],
        "message": "chore(release): \\\${nextRelease.version} [skip ci]\\n\\n\\\${nextRelease.notes}"
      }
    ],
    [
      "@semantic-release/github",
      {
        "assets": [
          "./releases/*.tar.gz",
          "./releases/*.zip"
        ]
      }
    ]
  ]
}
EOF
        ;;
    "go")
        cat > .releaserc.json << EOF
${BASE_CONFIG},
    [
      "@semantic-release/exec",
      {
        "prepareCmd": "echo \"\\\${nextRelease.version}\" > VERSION"
      }
    ],
    [
      "@semantic-release/changelog",
      {
        "changelogFile": "CHANGELOG.md"
      }
    ],
    [
      "@semantic-release/git",
      {
        "assets": ["VERSION", "CHANGELOG.md"],
        "message": "chore(release): \\\${nextRelease.version} [skip ci]\\n\\n\\\${nextRelease.notes}"
      }
    ],
    [
      "@semantic-release/github",
      {
        "assets": [
          "./releases/*.tar.gz",
          "./releases/*.zip"
        ]
      }
    ]
  ]
}
EOF
        ;;
    "python")
        cat > .releaserc.json << EOF
${BASE_CONFIG},
    [
      "@semantic-release/exec",
      {
        "prepareCmd": "python scripts/update_version.py \\\${nextRelease.version}"
      }
    ],
    [
      "@semantic-release/changelog",
      {
        "changelogFile": "CHANGELOG.md"
      }
    ],
    [
      "@semantic-release/git",
      {
        "assets": ["pyproject.toml", "setup.py", "__init__.py", "CHANGELOG.md"],
        "message": "chore(release): \\\${nextRelease.version} [skip ci]\\n\\n\\\${nextRelease.notes}"
      }
    ],
    [
      "@semantic-release/github",
      {
        "assets": [
          "./dist/*.whl",
          "./dist/*.tar.gz"
        ]
      }
    ]
  ]
}
EOF
        ;;
    "javascript")
        cat > .releaserc.json << EOF
${BASE_CONFIG},
    "@semantic-release/npm",
    [
      "@semantic-release/changelog",
      {
        "changelogFile": "CHANGELOG.md"
      }
    ],
    [
      "@semantic-release/git",
      {
        "assets": ["package.json", "package-lock.json", "CHANGELOG.md"],
        "message": "chore(release): \\\${nextRelease.version} [skip ci]\\n\\n\\\${nextRelease.notes}"
      }
    ],
    "@semantic-release/github"
  ]
}
EOF
        ;;
    "typescript")
        cat > .releaserc.json << EOF
${BASE_CONFIG},
    "@semantic-release/npm",
    [
      "@semantic-release/changelog",
      {
        "changelogFile": "CHANGELOG.md"
      }
    ],
    [
      "@semantic-release/git",
      {
        "assets": ["package.json", "package-lock.json", "CHANGELOG.md"],
        "message": "chore(release): \\\${nextRelease.version} [skip ci]\\n\\n\\\${nextRelease.notes}"
      }
    ],
    [
      "@semantic-release/github",
      {
        "assets": [
          "./artifacts/*.tgz"
        ]
      }
    ]
  ]
}
EOF
        ;;
    *)
        echo "Error: Unsupported language: $LANGUAGE"
        exit 1
        ;;
esac

echo "Semantic-release config created successfully for $LANGUAGE"
