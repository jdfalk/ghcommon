#!/bin/bash
# file: fix_instruction_frontmatter.sh
# version: 1.0.0
# guid: f1e2d3c4-b5a6-9e8f-7d6c-5b4a3e2f1d0e

# Fix malformed frontmatter in instruction files across all repositories

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to fix a single instruction file
fix_instruction_file() {
    local file="$1"
    local backup_file="${file}.backup"

    # Create backup
    cp "$file" "$backup_file"

    # Read the file and check if it needs fixing
    if grep -q "^applyTo:" "$file" && ! grep -q "^---$" "$file"; then
        log_info "Fixing frontmatter in: $file"

        # Create temporary file for the fixed content
        local temp_file=$(mktemp)

        # Extract the header comments and applyTo/description lines
        local in_header=true
        local found_applyTo=false

        while IFS= read -r line; do
            if [[ "$line" =~ ^<!--.*-->$ ]] || [[ "$line" =~ ^<!--.*$ ]] || [[ "$line" =~ ^.*-->$ ]] || [[ -z "$line" ]]; then
                # This is a comment line or empty line, keep it
                echo "$line" >> "$temp_file"
            elif [[ "$line" =~ ^applyTo: ]]; then
                # Found applyTo line, start frontmatter
                echo "---" >> "$temp_file"
                echo "$line" >> "$temp_file"
                found_applyTo=true
                in_header=false
            elif [[ "$found_applyTo" == true ]] && [[ "$line" =~ ^description: ]]; then
                # Found description line, add it
                echo "$line" >> "$temp_file"
            elif [[ "$found_applyTo" == true ]] && [[ "$line" =~ ^[[:space:]].* ]] && [[ ! "$line" =~ ^---$ ]] && [[ ! "$line" =~ ^#.* ]]; then
                # This is a continuation of the description (indented)
                echo "$line" >> "$temp_file"
            elif [[ "$found_applyTo" == true ]] && [[ "$line" =~ ^---$ ]]; then
                # Found existing end of frontmatter
                echo "$line" >> "$temp_file"
                break
            elif [[ "$found_applyTo" == true ]] && [[ "$line" =~ ^#.* ]]; then
                # Found the start of content, close frontmatter
                echo "---" >> "$temp_file"
                echo "" >> "$temp_file"
                echo "$line" >> "$temp_file"
                break
            else
                # Regular content line
                if [[ "$found_applyTo" == true ]]; then
                    # Close frontmatter if we haven't already
                    echo "---" >> "$temp_file"
                    echo "" >> "$temp_file"
                fi
                echo "$line" >> "$temp_file"
                found_applyTo=false
                in_header=false
            fi
        done < "$file"

        # Add the rest of the file
        if [[ "$found_applyTo" == true ]]; then
            # We might need to copy the rest of the file
            tail -n +$(grep -n "^#" "$file" | head -1 | cut -d: -f1) "$file" >> "$temp_file"
        else
            # Copy remaining lines
            local current_line_num=$(wc -l < "$temp_file")
            local total_lines=$(wc -l < "$file")
            if [[ $current_line_num -lt $total_lines ]]; then
                tail -n +$((current_line_num + 1)) "$file" >> "$temp_file"
            fi
        fi

        # Replace the original file
        mv "$temp_file" "$file"

        log_success "Fixed: $file"
    else
        log_info "Skipping (already correct or no applyTo): $file"
        rm "$backup_file"
    fi
}

# Main execution
main() {
    log_info "Fixing instruction file frontmatter across all repositories"

    # Find all instruction files
    local instruction_files=(
        "/Users/jdfalk/repos/github.com/jdfalk/gcommon/.github/instructions"
        "/Users/jdfalk/repos/github.com/jdfalk/ghcommon/.github/instructions"
        "/Users/jdfalk/repos/github.com/jdfalk/subtitle-manager/.github/instructions"
        "/Users/jdfalk/repos/github.com/jdfalk/audiobook-organizer/.github/instructions"
        "/Users/jdfalk/repos/github.com/jdfalk/apt-cacher-go/.github/instructions"
    )

    local fixed_count=0

    for dir in "${instruction_files[@]}"; do
        if [[ -d "$dir" ]]; then
            log_info "Processing directory: $dir"

            # Find all .instructions.md files
            while IFS= read -r -d '' file; do
                fix_instruction_file "$file"
                ((fixed_count++))
            done < <(find "$dir" -name "*.instructions.md" -type f -print0)
        else
            log_warning "Directory not found: $dir"
        fi
    done

    log_success "Processing complete! Fixed $fixed_count instruction files."
    log_info "Backup files created with .backup extension"
}

main "$@"
