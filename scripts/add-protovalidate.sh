#!/bin/bash
# file: scripts/add-protovalidate.sh
# version: 1.0.0
# guid: b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e

# Wrapper script for protovalidate-adder.py to integrate with repository tooling

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TOOL_PATH="$REPO_ROOT/tools/protovalidate-adder.py"

# Default options
DRY_RUN=""
COMPATIBILITY=""
FILE=""
VERBOSE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --compatibility-mode)
            COMPATIBILITY="--compatibility-mode"
            shift
            ;;
        --file)
            FILE="--file $2"
            shift 2
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run                 Show what would be changed without making changes"
            echo "  --compatibility-mode      Add validation rules as comments"
            echo "  --file PATH              Process a specific proto file"
            echo "  --verbose                Enable verbose output"
            echo "  --help                   Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Process all proto files"
            echo "  $0 --dry-run                         # Preview changes"
            echo "  $0 --compatibility-mode              # Add as comments"
            echo "  $0 --file pkg/auth/proto/auth.proto  # Process specific file"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not installed"
    exit 1
fi

# Check if the tool exists
if [[ ! -f "$TOOL_PATH" ]]; then
    echo "Error: protovalidate-adder.py not found at $TOOL_PATH"
    exit 1
fi

# Make sure the tool is executable
chmod +x "$TOOL_PATH"

# Run the tool
echo "Running protovalidate-adder.py..."
echo "Repository root: $REPO_ROOT"
echo ""

cd "$REPO_ROOT"
python3 "$TOOL_PATH" --repo-root "$REPO_ROOT" $DRY_RUN $COMPATIBILITY $FILE

echo ""
echo "Protovalidate addition completed."

# If not in dry-run mode and files were modified, suggest next steps
if [[ -z "$DRY_RUN" ]] && [[ -z "$COMPATIBILITY" ]]; then
    echo ""
    echo "Next steps:"
    echo "1. Review the changes: git diff"
    echo "2. Test proto compilation: buf generate"
    echo "3. Run proto linting: buf lint"
    echo "4. Commit changes: git add . && git commit -m 'feat(proto): add protovalidate validation rules'"
fi