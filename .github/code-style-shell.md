# file: copilot/code-style-shell.md

<!-- Google Shell Style Guide Summary -->
<!-- Source: https://google.github.io/styleguide/shellguide.html -->

# Shell Style Guide (Google)

This document summarizes Google's Shell scripting style guide for use in code generation and review.

## Core Principles

- **Readability**: Scripts should be clear and easy to understand
- **Robustness**: Handle errors gracefully and fail safely
- **Portability**: Write scripts that work across different environments
- **Maintainability**: Code should be easy to modify and debug
- **Security**: Avoid common security pitfalls

## Which Shell to Use

### Bash

- Use bash for scripts that need arrays, pattern substitution, or other advanced features
- Always include `#!/bin/bash` as the first line
- Use bash 4.0+ features when available

### Shell (sh)

- Use `/bin/sh` for simple scripts or maximum portability
- Avoid bash-specific features when using sh

```bash
#!/bin/bash
# Use bash for scripts with advanced features

#!/bin/sh
# Use sh for simple, portable scripts
```

## File Extensions

- Use `.sh` extension for shell scripts
- Make scripts executable: `chmod +x script.sh`

## Script Header

- Start with shebang line
- Include description and usage information
- Include author and modification date if required

```bash
#!/bin/bash
#
# Script description: What this script does
# Usage: script_name.sh [options] [arguments]
# Author: Your Name
# Last Modified: YYYY-MM-DD

set -euo pipefail  # Fail on errors, undefined variables, pipe failures
```

## Error Handling

### Set Options

- Use `set -e` to exit on command failures
- Use `set -u` to exit on undefined variables
- Use `set -o pipefail` to catch pipe failures

```bash
#!/bin/bash
set -euo pipefail

# Alternative: combine in one line
#!/bin/bash
set -euo pipefail
```

### Error Messages

- Write error messages to stderr
- Include script name and line number when possible
- Use meaningful error messages

```bash
readonly SCRIPT_NAME="$(basename "$0")"

error() {
  echo "${SCRIPT_NAME}: ERROR: $*" >&2
}

warning() {
  echo "${SCRIPT_NAME}: WARNING: $*" >&2
}

info() {
  echo "${SCRIPT_NAME}: INFO: $*" >&2
}

# Usage
if [[ ! -f "$config_file" ]]; then
  error "Config file not found: $config_file"
  exit 1
fi
```

## Variables

### Naming

- Use lowercase for local variables
- Use UPPERCASE for environment variables and constants
- Use descriptive names

```bash
# Local variables
local user_name="john"
local file_count=10

# Constants and environment variables
readonly CONFIG_FILE="/etc/myapp/config"
readonly MAX_RETRIES=3
export PATH="/usr/local/bin:$PATH"
```

### Quoting

- Quote variables to prevent word splitting and pathname expansion
- Use double quotes for variables, single quotes for string literals

```bash
# Good - quoted variables
file_name="my file.txt"
cp "$file_name" "$destination_dir/"

# Bad - unquoted variables (dangerous)
cp $file_name $destination_dir/

# Single quotes for literals
echo 'Hello, $USER'  # Literal $USER
echo "Hello, $USER"  # Expands to actual username
```

### Variable Declaration

- Use `local` for function variables
- Use `readonly` for constants
- Initialize variables when declaring

```bash
function process_files() {
  local input_dir="$1"
  local output_dir="$2"
  local file_count=0
  readonly temp_dir="/tmp/processing.$$"

  # Process files...
}
```

## Functions

### Function Definition

- Use the `function` keyword or just parentheses
- Place opening brace on the same line
- Use local variables

```bash
# Preferred style
function backup_database() {
  local db_name="$1"
  local backup_dir="$2"

  # Function implementation
}

# Alternative style (also acceptable)
backup_database() {
  local db_name="$1"
  local backup_dir="$2"

  # Function implementation
}
```

### Function Documentation

- Document function purpose, parameters, and return values
- Use consistent documentation format

```bash
#######################################
# Backs up a database to specified directory
# Arguments:
#   $1: Database name
#   $2: Backup directory path
# Returns:
#   0 if successful, 1 on error
# Outputs:
#   Writes backup status to stdout
#######################################
function backup_database() {
  local db_name="$1"
  local backup_dir="$2"

  if [[ -z "$db_name" || -z "$backup_dir" ]]; then
    error "Database name and backup directory required"
    return 1
  fi

  # Backup implementation
  info "Database $db_name backed up to $backup_dir"
  return 0
}
```

### Return Values

- Use return codes consistently (0 for success, non-zero for error)
- Use meaningful return codes
- Capture return values when needed

```bash
function file_exists() {
  local file="$1"
  [[ -f "$file" ]]
}

# Usage
if file_exists "$config_file"; then
  source "$config_file"
else
  error "Config file not found: $config_file"
  exit 1
fi
```

## Conditionals

### Test Constructs

- Use `[[ ]]` instead of `[ ]` for tests
- Use appropriate operators for different types of tests

```bash
# String comparisons
if [[ "$user" == "admin" ]]; then
  echo "Admin user detected"
fi

# Numeric comparisons
if [[ $count -gt 10 ]]; then
  echo "Count exceeds limit"
fi

# File tests
if [[ -f "$file" ]]; then
  echo "File exists"
fi

if [[ -d "$directory" ]]; then
  echo "Directory exists"
fi

# Multiple conditions
if [[ -f "$file" && -r "$file" ]]; then
  echo "File exists and is readable"
fi
```

### Case Statements

- Use case statements for multiple string comparisons
- Include a default case

```bash
case "$environment" in
  production|prod)
    echo "Production environment"
    readonly LOG_LEVEL="error"
    ;;
  staging|stage)
    echo "Staging environment"
    readonly LOG_LEVEL="warning"
    ;;
  development|dev)
    echo "Development environment"
    readonly LOG_LEVEL="debug"
    ;;
  *)
    error "Unknown environment: $environment"
    exit 1
    ;;
esac
```

## Loops

### For Loops

- Use appropriate loop constructs for different scenarios
- Quote variables in loops

```bash
# Loop over files
for file in "$directory"/*.txt; do
  if [[ -f "$file" ]]; then
    process_file "$file"
  fi
done

# Loop over array elements
files=("file1.txt" "file2.txt" "file3.txt")
for file in "${files[@]}"; do
  process_file "$file"
done

# C-style loop
for ((i = 0; i < 10; i++)); do
  echo "Iteration $i"
done
```

### While Loops

```bash
# Reading file line by line
while IFS= read -r line; do
  process_line "$line"
done < "$input_file"

# Counter-based loop
counter=0
while [[ $counter -lt $max_iterations ]]; do
  perform_task
  ((counter++))
done
```

## Command Substitution

- Use `$(command)` instead of backticks
- Quote command substitution results

```bash
# Good
current_date="$(date +%Y-%m-%d)"
file_count="$(ls -1 "$directory" | wc -l)"

# Avoid
current_date=`date +%Y-%m-%d`
```

## Arrays

### Array Declaration and Usage

```bash
# Array declaration
files=("file1.txt" "file2.txt" "file3.txt")
declare -a processed_files

# Adding elements
files+=("file4.txt")
processed_files[0]="result1.txt"

# Accessing elements
first_file="${files[0]}"
all_files="${files[@]}"

# Array length
file_count="${#files[@]}"

# Looping over array
for file in "${files[@]}"; do
  echo "Processing: $file"
done
```

## String Manipulation

### String Operations

```bash
# String length
name="john"
name_length="${#name}"

# Substring extraction
filename="document.pdf"
extension="${filename##*.}"        # pdf
basename="${filename%.*}"          # document

# String replacement
text="Hello, World!"
modified="${text/World/Universe}"   # Hello, Universe!

# Case conversion (bash 4.0+)
upper_name="${name^^}"              # JOHN
lower_name="${name,,}"              # john
```

## Input/Output

### Reading Input

```bash
# Reading user input
read -p "Enter your name: " user_name
read -s -p "Enter password: " password  # Silent input
echo  # New line after silent input

# Reading with timeout
if read -t 10 -p "Continue? (y/n): " response; then
  echo "User response: $response"
else
  echo "Timeout occurred"
fi
```

### Output Redirection

```bash
# Redirect stdout and stderr
command > output.log 2> error.log

# Redirect both to same file
command > combined.log 2>&1

# Append to file
command >> output.log

# Discard output
command > /dev/null 2>&1
```

## File Operations

### File Testing

```bash
# Common file tests
if [[ -f "$file" ]]; then
  echo "Regular file exists"
fi

if [[ -d "$directory" ]]; then
  echo "Directory exists"
fi

if [[ -r "$file" ]]; then
  echo "File is readable"
fi

if [[ -w "$file" ]]; then
  echo "File is writable"
fi

if [[ -x "$file" ]]; then
  echo "File is executable"
fi
```

### File Processing

```bash
# Create temporary files safely
temp_file="$(mktemp)"
trap 'rm -f "$temp_file"' EXIT

# Process file line by line
while IFS= read -r line; do
  # Process line
  echo "Processing: $line"
done < "$input_file"
```

## Signal Handling

### Trap Usage

```bash
#!/bin/bash
set -euo pipefail

# Cleanup function
cleanup() {
  local exit_code=$?
  echo "Cleaning up temporary files..."
  rm -rf "$temp_dir"
  exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Create temporary directory
temp_dir="$(mktemp -d)"

# Script logic here...
```

## Best Practices

### Security

- Validate all input
- Use absolute paths when possible
- Avoid using user input in command construction

```bash
# Good - validate input
function process_user_file() {
  local user_file="$1"

  # Validate input
  if [[ -z "$user_file" ]]; then
    error "Filename required"
    return 1
  fi

  # Validate file path
  if [[ "$user_file" =~ \.\. ]]; then
    error "Path traversal not allowed"
    return 1
  fi

  # Process file safely
  cp "$user_file" "$SAFE_DIRECTORY/"
}
```

### Performance

- Avoid unnecessary command substitutions
- Use built-in operations when possible
- Minimize external command calls

```bash
# Good - use bash built-ins
if [[ -n "$variable" ]]; then
  # Variable is not empty
fi

# Avoid - unnecessary external command
if [[ "$(echo -n "$variable" | wc -c)" -gt 0 ]]; then
  # Variable is not empty
fi
```

### Portability

- Use POSIX-compliant constructs when possible
- Test scripts on target platforms
- Document platform requirements

```bash
# Portable way to get script directory
script_dir="$(cd "$(dirname "$0")" && pwd)"

# Check for required commands
for cmd in curl jq; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    error "Required command not found: $cmd"
    exit 1
  fi
done
```

## Formatting

### Indentation

- Use 2 spaces for indentation
- Be consistent throughout the script

### Line Length

- Keep lines under 80 characters when practical
- Break long lines at logical points

```bash
# Good - break long command
rsync -avz --exclude='*.tmp' \
      --exclude='*.log' \
      "$source_dir/" \
      "$destination_dir/"

# Good - break long condition
if [[ "$environment" == "production" && \
      "$user" == "admin" && \
      -f "$config_file" ]]; then
  # Execute admin tasks
fi
```

## Common Patterns

### Argument Parsing

```bash
function usage() {
  cat << EOF
Usage: $0 [OPTIONS] FILE...

OPTIONS:
  -h, --help      Show this help message
  -v, --verbose   Enable verbose output
  -o, --output    Output directory

EXAMPLES:
  $0 -v -o /tmp file1.txt file2.txt
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      usage
      exit 0
      ;;
    -v|--verbose)
      verbose=true
      shift
      ;;
    -o|--output)
      output_dir="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -*)
      error "Unknown option: $1"
      usage >&2
      exit 1
      ;;
    *)
      files+=("$1")
      shift
      ;;
  esac
done
```

### Configuration Loading

```bash
# Load configuration with defaults
function load_config() {
  local config_file="$1"

  # Set defaults
  readonly DEFAULT_TIMEOUT=30
  readonly DEFAULT_RETRIES=3

  # Load config if exists
  if [[ -f "$config_file" ]]; then
    source "$config_file"
  fi

  # Use defaults if not set
  readonly TIMEOUT="${TIMEOUT:-$DEFAULT_TIMEOUT}"
  readonly RETRIES="${RETRIES:-$DEFAULT_RETRIES}"
}
```

This style guide should be used as the foundation for all Shell script generation and formatting decisions.
