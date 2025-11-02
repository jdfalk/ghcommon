#!/bin/bash
# file: .github/test-files/test.sh
# version: 1.0.0
# guid: a6b7c8d9-e0f1-2a3b-4c5d-6e7f8a9b0c1d

# Test Shell Script
# Purpose: Test bash linting and shfmt formatting

set -euo pipefail

# Constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

# Functions
print_info() {
  local message="$1"
  echo "[INFO] ${message}"
}

print_error() {
  local message="$1"
  echo "[ERROR] ${message}" >&2
}

validate_input() {
  local input="$1"

  if [[ -z ${input} ]]; then
    print_error "Input cannot be empty"
    return 1
  fi

  print_info "Input validated: ${input}"
  return 0
}

# Main function
main() {
  print_info "Starting ${SCRIPT_NAME}"

  # Array example
  local files=("file1.txt" "file2.txt" "file3.txt")

  # Loop example
  for file in "${files[@]}"; do
    print_info "Processing: ${file}"
  done

  # Conditional example
  if validate_input "test"; then
    print_info "Validation successful"
  else
    print_error "Validation failed"
    exit 1
  fi

  print_info "Script completed successfully"
}

# Entry point
main "$@"
