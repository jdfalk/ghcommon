#!/bin/bash
# file: .github/workflows/scripts/detect-languages.sh
# version: 1.1.0
# guid: 8a9b0c1d-2e3f-4a5b-6c7d-8e9f0a1b2c3d

set -euo pipefail

# Detect project languages and generate matrices
# Uses environment variables: SKIP_LANGUAGE_DETECTION, BUILD_TARGET, GO_ENABLED, PYTHON_ENABLED, RUST_ENABLED, FRONTEND_ENABLED, DOCKER_ENABLED, PROTOBUF_ENABLED

SKIP_DETECTION="${SKIP_LANGUAGE_DETECTION:-false}"
BUILD_TARGET_RAW="${BUILD_TARGET:-all}"
GO_ENABLED="${GO_ENABLED:-auto}"
PYTHON_ENABLED="${PYTHON_ENABLED:-auto}"
RUST_ENABLED="${RUST_ENABLED:-auto}"
FRONTEND_ENABLED="${FRONTEND_ENABLED:-auto}"
DOCKER_ENABLED="${DOCKER_ENABLED:-auto}"
PROTOBUF_ENABLED="${PROTOBUF_ENABLED:-auto}"

normalize_override() {
  local value="${1:-auto}"
  case "$value" in
  true | false) echo "$value" ;;
  *) echo "auto" ;;
  esac
}

BUILD_TARGET=$(echo "$BUILD_TARGET_RAW" | tr '[:upper:]' '[:lower:]')
GO_ENABLED=$(normalize_override "$GO_ENABLED")
PYTHON_ENABLED=$(normalize_override "$PYTHON_ENABLED")
RUST_ENABLED=$(normalize_override "$RUST_ENABLED")
FRONTEND_ENABLED=$(normalize_override "$FRONTEND_ENABLED")
DOCKER_ENABLED=$(normalize_override "$DOCKER_ENABLED")
PROTOBUF_ENABLED=$(normalize_override "$PROTOBUF_ENABLED")

derive_flag_from_target() {
  local override="$1"
  local target_key="$2"
  local default_value="$3"

  if [[ $override == "true" ]]; then
    echo "true"
  elif [[ $override == "false" ]]; then
    echo "false"
  else
    if [[ $BUILD_TARGET == "all" ]]; then
      echo "true"
    elif [[ $BUILD_TARGET == *","* ]]; then
      # Support comma-separated build targets
      IFS=',' read -ra targets <<<"$BUILD_TARGET"
      for entry in "${targets[@]}"; do
        local entry_normalized
        entry_normalized=$(echo "$entry" | tr '[:upper:]' '[:lower:]' | tr -d ' ')
        if [[ $entry_normalized == "$target_key" ]]; then
          echo "true"
          return
        fi
      done
      echo "$default_value"
    elif [[ $BUILD_TARGET == "$target_key" ]]; then
      echo "true"
    else
      echo "$default_value"
    fi
  fi
}

# Use input overrides if language detection is skipped
if [[ $SKIP_DETECTION == "true" ]]; then
  has_go=$(derive_flag_from_target "$GO_ENABLED" "go" "false")
  has_python=$(derive_flag_from_target "$PYTHON_ENABLED" "python" "false")
  has_rust=$(derive_flag_from_target "$RUST_ENABLED" "rust" "false")
  has_frontend=$(derive_flag_from_target "$FRONTEND_ENABLED" "frontend" "false")
  has_docker=$(derive_flag_from_target "$DOCKER_ENABLED" "docker" "false")
  protobuf_needed=$(derive_flag_from_target "$PROTOBUF_ENABLED" "protobuf" "false")

  primary_lang="multi"
  if [[ $BUILD_TARGET != "all" && $BUILD_TARGET != *","* ]]; then
    primary_lang="$BUILD_TARGET"
  elif [[ $has_rust == "true" ]]; then
    primary_lang="rust"
  elif [[ $has_go == "true" ]]; then
    primary_lang="go"
  elif [[ $has_python == "true" ]]; then
    primary_lang="python"
  elif [[ $has_frontend == "true" ]]; then
    primary_lang="frontend"
  elif [[ $has_docker == "true" ]]; then
    primary_lang="docker"
  fi

  echo "has-go=$has_go" >>$GITHUB_OUTPUT
  echo "has-python=$has_python" >>$GITHUB_OUTPUT
  echo "has-rust=$has_rust" >>$GITHUB_OUTPUT
  echo "has-frontend=$has_frontend" >>$GITHUB_OUTPUT
  echo "has-docker=$has_docker" >>$GITHUB_OUTPUT
  echo "protobuf-needed=$protobuf_needed" >>$GITHUB_OUTPUT
  echo "primary-language=$primary_lang" >>$GITHUB_OUTPUT
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
    [[ $primary_lang == "unknown" ]] && primary_lang="python"
  fi

  # Rust detection
  if [[ -f "Cargo.toml" || -f "Cargo.lock" ]]; then
    has_rust="true"
    [[ $primary_lang == "unknown" ]] && primary_lang="rust"
  fi

  # Frontend detection
  if [[ -f "package.json" || -d "webui" || -d "frontend" || -d "ui" ]]; then
    has_frontend="true"
    [[ $primary_lang == "unknown" ]] && primary_lang="frontend"
  fi

  # Docker detection
  if [[ -f "Dockerfile" || -f "docker-compose.yml" || -f "docker-compose.yaml" ]]; then
    has_docker="true"
  fi

  # Protobuf detection
  if [[ -f "buf.yaml" || -f "buf.gen.yaml" || -n "$(find . -name '*.proto' -type f 2>/dev/null | head -1)" ]]; then
    protobuf_needed="true"
  fi

  echo "has-go=$has_go" >>$GITHUB_OUTPUT
  echo "has-python=$has_python" >>$GITHUB_OUTPUT
  echo "has-rust=$has_rust" >>$GITHUB_OUTPUT
  echo "has-frontend=$has_frontend" >>$GITHUB_OUTPUT
  echo "has-docker=$has_docker" >>$GITHUB_OUTPUT
  echo "protobuf-needed=$protobuf_needed" >>$GITHUB_OUTPUT
  echo "primary-language=$primary_lang" >>$GITHUB_OUTPUT
fi

# Generate build matrices (simplified for reusable workflow)
echo 'go-matrix={"go-version":["1.22","1.23","1.24"],"os":["ubuntu-latest","macos-latest"]}' >>$GITHUB_OUTPUT
echo 'python-matrix={"python-version":["3.11","3.12","3.13"],"os":["ubuntu-latest","macos-latest"]}' >>$GITHUB_OUTPUT
echo 'rust-matrix={"rust-version":["stable","beta"],"os":["ubuntu-latest","macos-latest"]}' >>$GITHUB_OUTPUT
echo 'frontend-matrix={"node-version":["18","20","22"],"os":["ubuntu-latest"]}' >>$GITHUB_OUTPUT
echo 'docker-matrix={"platform":["linux/amd64","linux/arm64"]}' >>$GITHUB_OUTPUT
