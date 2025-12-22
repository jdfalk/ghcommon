#!/bin/bash

# Test script for instruction context loading

# Source the main script to get the function
source scripts/multi-repo-rebase.sh

echo "Testing instruction context loading for subtitle-manager..."
echo "=========================================="

# Test the function
context_file=$(load_instruction_context "$HOME/repos/subtitle-manager")

echo "Generated context file: $context_file"
echo "Contents:"
echo "=========================================="
cat "$context_file"
echo "=========================================="

# Clean up
rm -f "$context_file"

echo "Test completed!"
