#!/bin/bash
# file: .github/workflows/scripts/detect-languages.sh
# version: 1.0.0
# guid: 8a9b0c1d-2e3f-4a5b-6c7d-8e9f0a1b2c3d

set -euo pipefail

# Detect project languages and generate matrices
# Uses environment variables: SKIP_LANGUAGE_DETECTION, GO_ENABLED, PYTHON_ENABLED, RUST_ENABLED, FRONTEND_ENABLED, DOCKER_ENABLED, PROTOBUF_ENABLED

SKIP_DETECTION="${SKIP_LANGUAGE_DETECTION:-false}"
GO_ENABLED="${GO_ENABLED:-false}"
PYTHON_ENABLED="${PYTHON_ENABLED:-false}"
RUST_ENABLED="${RUST_ENABLED:-false}"
FRONTEND_ENABLED="${FRONTEND_ENABLED:-false}"
DOCKER_ENABLED="${DOCKER_ENABLED:-false}"
PROTOBUF_ENABLED="${PROTOBUF_ENABLED:-false}"

# Use input overrides if language detection is skipped
if [[ "$SKIP_DETECTION" == "true" ]]; then
    echo "has-go=$GO_ENABLED" >> $GITHUB_OUTPUT
    echo "has-python=$PYTHON_ENABLED" >> $GITHUB_OUTPUT
    echo "has-rust=$RUST_ENABLED" >> $GITHUB_OUTPUT
    echo "has-frontend=$FRONTEND_ENABLED" >> $GITHUB_OUTPUT
    echo "has-docker=$DOCKER_ENABLED" >> $GITHUB_OUTPUT
    echo "protobuf-needed=$PROTOBUF_ENABLED" >> $GITHUB_OUTPUT
else
    # Auto-detect languages
    has_go="false"
    has_python="false"
    has_rust="false"
    has_frontend="false"
    has_docker="false"
    protobuf_needed="false"
    primary_lang="unknown"

    # Go detection
    if [[ -f "go.mod" || -f "main.go" || -d "cmd" || -d "pkg" ]]; then
        has_go="true"
        primary_lang="go"
    fi

    # Python detection
    if [[ -f "setup.py" || -f "pyproject.toml" || -f "requirements.txt" || -f "poetry.lock" ]]; then
        has_python="true"
        [[ "$primary_lang" == "unknown" ]] && primary_lang="python"
    fi

    # Rust detection
    if [[ -f "Cargo.toml" || -f "Cargo.lock" ]]; then
        has_rust="true"
        [[ "$primary_lang" == "unknown" ]] && primary_lang="rust"
    fi

    # Frontend detection
    if [[ -f "package.json" || -d "webui" || -d "frontend" || -d "ui" ]]; then
        has_frontend="true"
        [[ "$primary_lang" == "unknown" ]] && primary_lang="frontend"
    fi

    # Docker detection
    if [[ -f "Dockerfile" || -f "docker-compose.yml" || -f "docker-compose.yaml" ]]; then
        has_docker="true"
    fi

    # Protobuf detection
    if [[ -f "buf.yaml" || -f "buf.gen.yaml" || -n "$(find . -name '*.proto' -type f 2>/dev/null | head -1)" ]]; then
        protobuf_needed="true"
    fi

    echo "has-go=$has_go" >> $GITHUB_OUTPUT
    echo "has-python=$has_python" >> $GITHUB_OUTPUT
    echo "has-rust=$has_rust" >> $GITHUB_OUTPUT
    echo "has-frontend=$has_frontend" >> $GITHUB_OUTPUT
    echo "has-docker=$has_docker" >> $GITHUB_OUTPUT
    echo "protobuf-needed=$protobuf_needed" >> $GITHUB_OUTPUT
    echo "primary-language=$primary_lang" >> $GITHUB_OUTPUT
fi

# Generate build matrices (simplified for reusable workflow)
echo 'go-matrix={"go-version":["1.22","1.23","1.24"],"os":["ubuntu-latest","macos-latest"]}' >> $GITHUB_OUTPUT
echo 'python-matrix={"python-version":["3.11","3.12","3.13"],"os":["ubuntu-latest","macos-latest"]}' >> $GITHUB_OUTPUT
echo 'rust-matrix={"rust-version":["stable","beta"],"os":["ubuntu-latest","macos-latest"]}' >> $GITHUB_OUTPUT
echo 'frontend-matrix={"node-version":["18","20","22"],"os":["ubuntu-latest"]}' >> $GITHUB_OUTPUT
echo 'docker-matrix={"platform":["linux/amd64","linux/arm64"]}' >> $GITHUB_OUTPUT
