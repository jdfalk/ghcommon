#!/usr/bin/env python3
# file: tools/protovalidate-adder.py
# version: 1.0.0
# guid: 3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f

"""
Automated tool to add protovalidate imports and validation rules to protobuf files.
Designed to work with thousands of proto files efficiently and follow repository standards.
"""

import os
import re
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple


class ProtovalidateAdder:
    """Tool to add protovalidate support to protobuf files."""
    
    def __init__(self, repo_root: str, dry_run: bool = False, compatibility_mode: bool = False):
        self.repo_root = Path(repo_root)
        self.pkg_dir = self.repo_root / "pkg"
        self.dry_run = dry_run
        self.compatibility_mode = compatibility_mode
        self.files_processed = 0
        self.files_modified = 0
        
        # Choose validation import based on mode
        if compatibility_mode:
            self.validation_import = '// import "buf/validate/validate.proto"; // Commented out - add dependency first'
        else:
            self.validation_import = 'import "buf/validate/validate.proto";'
        
    def find_all_proto_files(self) -> List[Path]:
        """Find all .proto files in the repository."""
        proto_files = []
        
        # Look in pkg directory (main location)
        if self.pkg_dir.exists():
            proto_files.extend(self.pkg_dir.rglob("*.proto"))
        
        # Look in other potential directories
        for subdir in ["proto", "protos", "api", "schemas"]:
            subdir_path = self.repo_root / subdir
            if subdir_path.exists():
                proto_files.extend(subdir_path.rglob("*.proto"))
        
        return proto_files
    
    def has_protovalidate_import(self, content: str) -> bool:
        """Check if file already has protovalidate import."""
        return 'buf/validate/validate.proto' in content or 'validate.proto' in content
    
    def get_import_insertion_point(self, lines: List[str]) -> int:
        """Find the best place to insert the protovalidate import."""
        # Look for existing imports section
        import_lines = []
        for i, line in enumerate(lines):
            if line.strip().startswith('import '):
                import_lines.append(i)
        
        if import_lines:
            # Insert after the last import
            return import_lines[-1] + 1
        
        # No imports found, look for package declaration
        for i, line in enumerate(lines):
            if line.strip().startswith('package '):
                return i + 2  # Leave a blank line after package
        
        # No package found, look for edition declaration
        for i, line in enumerate(lines):
            if line.strip().startswith('edition '):
                return i + 2  # Leave a blank line after edition
        
        # No edition found, look for syntax declaration (proto2/proto3)
        for i, line in enumerate(lines):
            if line.strip().startswith('syntax '):
                return i + 2  # Leave a blank line after syntax
        
        # If no suitable location found, insert after file header
        header_end = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('//') or line.strip() == '':
                header_end = i + 1
            else:
                break
        
        return header_end
    
    def add_protovalidate_import(self, content: str) -> str:
        """Add protovalidate import to the proto file content."""
        if self.has_protovalidate_import(content):
            return content
        
        lines = content.split('\n')
        insertion_point = self.get_import_insertion_point(lines)
        
        # Insert the import with proper spacing
        new_lines = lines.copy()
        new_lines.insert(insertion_point, '')  # Add blank line before
        new_lines.insert(insertion_point + 1, self.validation_import)
        
        return '\n'.join(new_lines)
    
    def get_field_validation_rules(self, field_type: str, field_name: str) -> Optional[str]:
        """Generate appropriate validation rules based on field type and name."""
        rules = []
        
        # String field validations
        if field_type in ['string']:
            if any(keyword in field_name.lower() for keyword in ['id', 'uuid', 'guid']):
                rules.append('string.min_len = 1')
            elif 'email' in field_name.lower():
                rules.append('string.pattern = "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,}$"')
            elif 'name' in field_name.lower():
                rules.append('string.min_len = 1')
                rules.append('string.max_len = 255')
            elif 'url' in field_name.lower():
                rules.append('string.uri = true')
            else:
                rules.append('string.min_len = 1')
        
        # Numeric field validations
        elif field_type in ['int32', 'int64', 'uint32', 'uint64']:
            if 'age' in field_name.lower():
                rules.append(f'{field_type}.gte = 0')
                rules.append(f'{field_type}.lte = 150')
            elif 'count' in field_name.lower() or 'size' in field_name.lower():
                rules.append(f'{field_type}.gte = 0')
            elif 'port' in field_name.lower():
                rules.append(f'{field_type}.gte = 1')
                rules.append(f'{field_type}.lte = 65535')
            else:
                rules.append(f'{field_type}.gte = 0')
        
        # Float/double validations
        elif field_type in ['float', 'double']:
            if 'percentage' in field_name.lower() or 'percent' in field_name.lower():
                rules.append(f'{field_type}.gte = 0.0')
                rules.append(f'{field_type}.lte = 100.0')
            elif 'score' in field_name.lower() or 'rating' in field_name.lower():
                rules.append(f'{field_type}.gte = 0.0')
                rules.append(f'{field_type}.lte = 10.0')
            else:
                rules.append(f'{field_type}.gte = 0.0')
        
        # Repeated field validations
        if 'repeated' in field_type:
            rules.append('repeated.min_items = 1')
        
        if rules:
            if self.compatibility_mode:
                return f" // [(validate.rules).{', '.join(rules)}] // Add when protovalidate dependency is available"
            else:
                return f" [(validate.rules).{', '.join(rules)}]"
        
        return None
    
    def add_field_validations(self, content: str) -> str:
        """Add validation rules to fields in the proto file."""
        lines = content.split('\n')
        new_lines = []
        
        in_message = False
        message_indent = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Track if we're inside a message
            if stripped.startswith('message ') and stripped.endswith('{'):
                in_message = True
                message_indent = len(line) - len(line.lstrip())
                new_lines.append(line)
                continue
            elif stripped == '}' and in_message:
                current_indent = len(line) - len(line.lstrip())
                if current_indent == message_indent:
                    in_message = False
                new_lines.append(line)
                continue
            
            # Process field lines
            if in_message and '=' in stripped and not stripped.startswith('//'):
                # Match field pattern: [repeated] type name = number [options];
                field_match = re.match(
                    r'^(\s*)((?:repeated\s+)?)([\w.]+)\s+(\w+)\s*=\s*(\d+)(?:\s*\[(.*?)\])?\s*;?\s*(?://.*)?$',
                    line
                )
                
                if field_match:
                    indent, repeated, field_type, field_name, field_number, existing_options, *rest = field_match.groups()
                    
                    # Skip if already has validation rules
                    if existing_options and 'validate.rules' in existing_options:
                        new_lines.append(line)
                        continue
                    
                    full_type = repeated + field_type
                    validation_rule = self.get_field_validation_rules(full_type, field_name)
                    
                    if validation_rule:
                        if existing_options:
                            # Add to existing options
                            new_options = f"{existing_options}, {validation_rule.strip(' []')}"
                            new_line = f"{indent}{repeated}{field_type} {field_name} = {field_number} [{new_options}];"
                        else:
                            # Add new options or comments
                            if self.compatibility_mode:
                                new_line = f"{indent}{repeated}{field_type} {field_name} = {field_number};{validation_rule}"
                            else:
                                new_line = f"{indent}{repeated}{field_type} {field_name} = {field_number}{validation_rule};"
                        
                        new_lines.append(new_line)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def process_proto_file(self, proto_file: Path) -> bool:
        """Process a single proto file to add protovalidate support."""
        try:
            with open(proto_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Step 1: Add protovalidate import
            content = self.add_protovalidate_import(original_content)
            
            # Step 2: Add field validations
            content = self.add_field_validations(content)
            
            # Check if content was modified
            modified = content != original_content
            
            if modified and not self.dry_run:
                with open(proto_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ Modified: {proto_file}")
                self.files_modified += 1
            elif modified and self.dry_run:
                print(f"✓ Would modify: {proto_file}")
                self.files_modified += 1
            else:
                print(f"- Unchanged: {proto_file}")
            
            self.files_processed += 1
            return modified
            
        except Exception as e:
            print(f"✗ Error processing {proto_file}: {e}")
            return False
    
    def run_buf_lint(self) -> Tuple[int, str]:
        """Run buf lint to verify proto files are valid."""
        try:
            result = subprocess.run(
                ["buf", "lint"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            return result.returncode, result.stderr
        except Exception as e:
            return 1, str(e)
    
    def process_all_files(self) -> None:
        """Process all proto files in the repository."""
        proto_files = self.find_all_proto_files()
        
        if not proto_files:
            print("No proto files found in the repository.")
            print("Expected locations: pkg/*/proto/*.proto")
            return
        
        print(f"Found {len(proto_files)} proto files to process")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print()
        
        for proto_file in proto_files:
            self.process_proto_file(proto_file)
        
        print()
        print(f"Summary:")
        print(f"  Files processed: {self.files_processed}")
        print(f"  Files modified: {self.files_modified}")
        print(f"  Files unchanged: {self.files_processed - self.files_modified}")
        
        if not self.dry_run and self.files_modified > 0:
            print()
            print("Running buf lint to verify changes...")
            returncode, output = self.run_buf_lint()
            if returncode == 0:
                print("✓ All proto files pass buf lint")
            else:
                print("✗ Some proto files have lint issues:")
                print(output)


def main():
    parser = argparse.ArgumentParser(
        description="Add protovalidate imports and validation rules to protobuf files"
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Root directory of the repository (default: current directory)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making actual changes"
    )
    parser.add_argument(
        "--file",
        help="Process a specific proto file instead of all files"
    )
    parser.add_argument(
        "--compatibility-mode",
        action="store_true",
        help="Add validation rules as comments (when protovalidate dependency is not available)"
    )
    
    args = parser.parse_args()
    
    # Resolve repository root
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        print(f"Error: Repository root does not exist: {repo_root}")
        sys.exit(1)
    
    adder = ProtovalidateAdder(str(repo_root), args.dry_run, args.compatibility_mode)
    
    if args.file:
        # Process single file
        file_path = Path(args.file).resolve()
        if not file_path.exists():
            print(f"Error: File does not exist: {file_path}")
            sys.exit(1)
        
        print(f"Processing single file: {file_path}")
        adder.process_proto_file(file_path)
    else:
        # Process all files
        adder.process_all_files()


if __name__ == "__main__":
    main()