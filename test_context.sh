#!/bin/bash

# Load instruction context for better AI suggestions
load_instruction_context() {
  local repo_dir="$1"
  local instruction_dir="$repo_dir/.github/instructions"
  local context_file=$(mktemp)

  if [ -d "$instruction_dir" ]; then
    echo "# Coding Instructions Context" >"$context_file"
    echo "" >>"$context_file"

    # Include general coding instructions
    if [ -f "$instruction_dir/general-coding.instructions.md" ]; then
      echo "## General Coding Instructions" >>"$context_file"
      head -30 "$instruction_dir/general-coding.instructions.md" >>"$context_file"
      echo "" >>"$context_file"
    fi

    # Include commit message guidelines
    if [ -f "$repo_dir/.github/commit-messages.md" ]; then
      echo "## Commit Message Guidelines" >>"$context_file"
      head -20 "$repo_dir/.github/commit-messages.md" >>"$context_file"
      echo "" >>"$context_file"
    fi

    # Include shell-specific instructions if available
    if [ -f "$instruction_dir/shell.instructions.md" ]; then
      echo "## Shell Coding Instructions" >>"$context_file"
      head -15 "$instruction_dir/shell.instructions.md" >>"$context_file"
      echo "" >>"$context_file"
    fi
  else
    # Create minimal context if no instructions found
    echo "# Basic Guidelines" >"$context_file"
    echo "Use conventional commit format: type(scope): description" >>"$context_file"
    echo "Common types: feat, fix, docs, style, refactor, test, chore" >>"$context_file"
  fi

  echo "$context_file"
}

echo "Testing instruction context loading for subtitle-manager..."
echo "=========================================="

# Test the function
context_file=$(load_instruction_context "/Users/jdfalk/repos/github.com/jdfalk/subtitle-manager")

echo "Generated context file: $context_file"
echo "Context sample (first 20 lines):"
echo "=========================================="
head -20 "$context_file"
echo "=========================================="
echo "File size: $(wc -l <"$context_file") lines"

# Clean up
rm -f "$context_file"

echo "Test completed successfully!"
