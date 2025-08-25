#!/usr/bin/env python3
# file: tools/mass-protovalidate-injector.py
# version: 1.0.0
# guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d

"""
Mass protovalidate injection tool for protobuf files.
Automatically adds protovalidate imports and validation rules to all protobuf files.
Designed to work autonomously with the copilot-agent-util for execution.
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass

@dataclass
class ValidationRule:
    """Represents a validation rule to be applied to a field."""
    field_type: str
    rule_pattern: str
    description: str

class MassProtovalidateInjector:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.pkg_dir = self.repo_root / "pkg"
        self.files_processed = 0
        self.rules_added = 0
        
        # Define validation rules for common field types
        self.validation_rules = {
            "string": [
                ValidationRule("email", "email = true", "Email validation"),
                ValidationRule("uri", "uri = true", "URI validation"),
                ValidationRule("uuid", "uuid = true", "UUID validation"),
                ValidationRule("ip", "ip = true", "IP address validation"),
                ValidationRule("hostname", "hostname = true", "Hostname validation"),
                ValidationRule("non_empty", "min_len = 1", "Non-empty string"),
                ValidationRule("max_len", "max_len = 255", "Maximum length limit"),
            ],
            "int32": [
                ValidationRule("positive", "gt = 0", "Positive integer"),
                ValidationRule("non_negative", "gte = 0", "Non-negative integer"),
                ValidationRule("range", "gte = 1, lte = 100", "Range validation"),
            ],
            "int64": [
                ValidationRule("positive", "gt = 0", "Positive long"),
                ValidationRule("non_negative", "gte = 0", "Non-negative long"),
                ValidationRule("timestamp", "gt = 0", "Timestamp validation"),
            ],
            "double": [
                ValidationRule("positive", "gt = 0", "Positive double"),
                ValidationRule("non_negative", "gte = 0", "Non-negative double"),
                ValidationRule("percentage", "gte = 0, lte = 100", "Percentage validation"),
            ],
            "float": [
                ValidationRule("positive", "gt = 0", "Positive float"),
                ValidationRule("non_negative", "gte = 0", "Non-negative float"),
            ],
            "repeated": [
                ValidationRule("min_items", "min_items = 1", "Minimum items required"),
                ValidationRule("max_items", "max_items = 100", "Maximum items limit"),
                ValidationRule("unique", "unique = true", "Unique items only"),
            ]
        }

    def has_protovalidate_import(self, content: str) -> bool:
        """Check if the file already has protovalidate import."""
        return 'import "buf/validate/validate.proto"' in content

    def add_protovalidate_import(self, content: str) -> str:
        """Add protovalidate import to the proto file."""
        if self.has_protovalidate_import(content):
            return content
        
        lines = content.split('\n')
        new_lines = []
        import_added = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # Add import after edition and before package
            if line.strip().startswith('edition = ') and not import_added:
                # Look for the next non-empty, non-comment line
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or lines[j].strip().startswith('//')):
                    new_lines.append(lines[j])
                    j += 1
                
                # Add the import before package declaration
                new_lines.append('')
                new_lines.append('import "buf/validate/validate.proto";')
                import_added = True
        
        return '\n'.join(new_lines)

    def detect_field_validation_opportunities(self, content: str) -> List[Dict]:
        """Detect fields that could benefit from validation rules."""
        opportunities = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('//'):
                continue
            
            # Match field definitions: type name = number;
            field_match = re.match(r'\s*(repeated\s+)?(\w+)\s+(\w+)\s*=\s*(\d+)\s*;', line)
            if field_match:
                repeated = field_match.group(1) is not None
                field_type = field_match.group(2)
                field_name = field_match.group(3)
                field_number = field_match.group(4)
                
                # Suggest validation rules based on field name and type
                suggested_rules = self.suggest_validation_rules(field_name, field_type, repeated)
                
                if suggested_rules:
                    opportunities.append({
                        'line_number': i + 1,
                        'original_line': line,
                        'field_name': field_name,
                        'field_type': field_type,
                        'field_number': field_number,
                        'repeated': repeated,
                        'suggested_rules': suggested_rules
                    })
        
        return opportunities

    def suggest_validation_rules(self, field_name: str, field_type: str, repeated: bool) -> List[ValidationRule]:
        """Suggest appropriate validation rules based on field name and type."""
        suggestions = []
        field_name_lower = field_name.lower()
        
        # Handle repeated fields
        if repeated:
            if field_type in self.validation_rules:
                suggestions.extend(self.validation_rules["repeated"])
        
        # Handle specific field types
        if field_type in self.validation_rules:
            base_rules = self.validation_rules[field_type]
            
            # Apply heuristics based on field names
            if field_type == "string":
                if "email" in field_name_lower:
                    suggestions.append(next(r for r in base_rules if r.field_type == "email"))
                elif any(term in field_name_lower for term in ["url", "uri", "link"]):
                    suggestions.append(next(r for r in base_rules if r.field_type == "uri"))
                elif any(term in field_name_lower for term in ["id", "uuid", "guid"]):
                    suggestions.append(next(r for r in base_rules if r.field_type == "uuid"))
                elif any(term in field_name_lower for term in ["ip", "address"]):
                    suggestions.append(next(r for r in base_rules if r.field_type == "ip"))
                elif any(term in field_name_lower for term in ["host", "domain"]):
                    suggestions.append(next(r for r in base_rules if r.field_type == "hostname"))
                else:
                    # Default string validations
                    suggestions.append(next(r for r in base_rules if r.field_type == "non_empty"))
                    suggestions.append(next(r for r in base_rules if r.field_type == "max_len"))
            
            elif field_type in ["int32", "int64"]:
                if any(term in field_name_lower for term in ["count", "size", "length", "amount"]):
                    suggestions.append(next(r for r in base_rules if r.field_type == "non_negative"))
                elif any(term in field_name_lower for term in ["id", "number", "port"]):
                    suggestions.append(next(r for r in base_rules if r.field_type == "positive"))
                elif "timestamp" in field_name_lower or "time" in field_name_lower:
                    if field_type == "int64":
                        suggestions.append(next(r for r in base_rules if r.field_type == "timestamp"))
            
            elif field_type in ["double", "float"]:
                if any(term in field_name_lower for term in ["percent", "ratio", "rate"]):
                    suggestions.append(next(r for r in base_rules if r.field_type == "percentage"))
                elif any(term in field_name_lower for term in ["amount", "value", "score"]):
                    suggestions.append(next(r for r in base_rules if r.field_type == "non_negative"))
        
        return suggestions

    def add_validation_rules_to_field(self, line: str, rules: List[ValidationRule]) -> str:
        """Add validation rules to a field definition line."""
        if not rules or "[(validate.rules)" in line:
            return line
        
        # Remove the semicolon and add validation rules
        line_without_semicolon = line.rstrip(';').rstrip()
        
        # Get the field type from the line to determine the correct validation syntax
        field_match = re.match(r'\s*(repeated\s+)?(\w+)\s+(\w+)\s*=\s*(\d+)', line)
        if not field_match:
            return line
        
        repeated = field_match.group(1) is not None
        field_type = field_match.group(2)
        
        # Build validation rules based on field type
        if repeated:
            # For repeated fields, use repeated validation
            combined_rules = rules[0].rule_pattern
            new_line = f"{line_without_semicolon} [(validate.rules).repeated.{combined_rules}];"
        elif field_type == "string":
            combined_rules = rules[0].rule_pattern
            new_line = f"{line_without_semicolon} [(validate.rules).string.{combined_rules}];"
        elif field_type in ["int32", "int64", "double", "float"]:
            combined_rules = rules[0].rule_pattern
            new_line = f"{line_without_semicolon} [(validate.rules).{field_type}.{combined_rules}];"
        else:
            return line
        
        return new_line

    def process_proto_file(self, proto_file: Path, auto_apply: bool = False) -> bool:
        """Process a single proto file to add protovalidate."""
        if not proto_file.exists():
            return False
        
        print(f"\nProcessing: {proto_file}")
        
        with open(proto_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # Step 1: Add protovalidate import if missing
        if not self.has_protovalidate_import(content):
            content = self.add_protovalidate_import(content)
            modified = True
            print(f"  ✓ Added protovalidate import")
        else:
            print(f"  - Protovalidate import already present")
        
        # Step 2: Detect validation opportunities
        opportunities = self.detect_field_validation_opportunities(content)
        
        if opportunities:
            print(f"  Found {len(opportunities)} fields that could benefit from validation:")
            
            lines = content.split('\n')
            
            for opp in opportunities:
                field_info = f"{opp['field_name']} ({opp['field_type']})"
                print(f"    Line {opp['line_number']}: {field_info}")
                
                if auto_apply and opp['suggested_rules']:
                    # Apply the first suggested rule automatically
                    rule = opp['suggested_rules'][0]
                    old_line = lines[opp['line_number'] - 1]
                    new_line = self.add_validation_rules_to_field(old_line, [rule])
                    
                    if new_line != old_line:
                        lines[opp['line_number'] - 1] = new_line
                        modified = True
                        self.rules_added += 1
                        print(f"      ✓ Applied: {rule.description}")
                    else:
                        print(f"      - Validation already present")
            
            if auto_apply and modified:
                content = '\n'.join(lines)
        else:
            print(f"  - No fields found requiring validation")
        
        # Write back if modified
        if modified:
            with open(proto_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.files_processed += 1
            print(f"  ✓ File updated successfully")
            return True
        else:
            print(f"  - No changes needed")
            return False

    def process_all_proto_files(self, auto_apply: bool = False):
        """Process all proto files in the repository."""
        print("Scanning for protobuf files...")
        
        proto_files = list(self.repo_root.rglob("*.proto"))
        
        if not proto_files:
            print("No protobuf files found in the repository.")
            print("You can create example proto files using the create_example_proto_files() method.")
            return
        
        print(f"Found {len(proto_files)} protobuf files")
        
        for proto_file in proto_files:
            self.process_proto_file(proto_file, auto_apply=auto_apply)
        
        print(f"\n=== Summary ===")
        print(f"Files processed: {self.files_processed}")
        print(f"Validation rules added: {self.rules_added}")

    def create_example_proto_files(self):
        """Create example proto files to demonstrate protovalidate usage."""
        examples = [
            {
                "path": "pkg/common/proto/user.proto",
                "package": "gcommon.v1.common",
                "content": '''// file: pkg/common/proto/user.proto
// version: 1.0.0
// guid: 1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d

edition = "2023";

package gcommon.v1.common;

option go_package = "github.com/jdfalk/ghcommon/pkg/common/proto;commonpb";

// User represents a user account in the system.
message User {
  // Unique identifier for the user account.
  string user_id = 1;
  
  // User's email address.
  string email = 2;
  
  // User's display name.
  string display_name = 3;
  
  // User's age (must be positive).
  int32 age = 4;
  
  // User's profile image URL.
  string avatar_url = 5;
  
  // User's account balance (non-negative).
  double account_balance = 6;
  
  // List of user's roles.
  repeated string roles = 7;
}'''
            },
            {
                "path": "pkg/auth/proto/auth_request.proto",
                "package": "gcommon.v1.auth",
                "content": '''// file: pkg/auth/proto/auth_request.proto
// version: 1.0.0
// guid: 2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e

edition = "2023";

package gcommon.v1.auth;

option go_package = "github.com/jdfalk/ghcommon/pkg/auth/proto;authpb";

// AuthRequest represents an authentication request.
message AuthRequest {
  // User's email address for authentication.
  string email = 1;
  
  // User's password (minimum 8 characters).
  string password = 2;
  
  // Remember me flag.
  bool remember_me = 3;
  
  // Session timeout in seconds.
  int32 session_timeout = 4;
  
  // Client IP address.
  string client_ip = 5;
  
  // User agent string.
  string user_agent = 6;
}'''
            },
            {
                "path": "pkg/metrics/proto/metric_data.proto",
                "package": "gcommon.v1.metrics",
                "content": '''// file: pkg/metrics/proto/metric_data.proto
// version: 1.0.0
// guid: 3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f

edition = "2023";

package gcommon.v1.metrics;

option go_package = "github.com/jdfalk/ghcommon/pkg/metrics/proto;metricspb";

// MetricData represents a metric data point.
message MetricData {
  // Metric name identifier.
  string metric_name = 1;
  
  // Metric value.
  double value = 2;
  
  // Timestamp when metric was recorded (Unix timestamp).
  int64 timestamp = 3;
  
  // Metric tags for categorization.
  repeated string tags = 4;
  
  // Sample rate (0.0 to 1.0).
  double sample_rate = 5;
  
  // Source hostname.
  string hostname = 6;
  
  // Metric unit.
  string unit = 7;
}'''
            }
        ]
        
        print("Creating example protobuf files...")
        
        for example in examples:
            proto_path = self.repo_root / example["path"]
            proto_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(proto_path, "w", encoding="utf-8") as f:
                f.write(example["content"])
            
            print(f"  ✓ Created: {example['path']}")
        
        print(f"\nCreated {len(examples)} example protobuf files.")
        print("Now run the protovalidate injection process...")

    def run_buf_lint(self) -> tuple[int, str]:
        """Run buf lint to validate the changes."""
        try:
            result = subprocess.run(
                ["copilot-agent-util", "buf", "lint"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            return result.returncode, result.stderr
        except Exception as e:
            return 1, str(e)

    def generate_validation_report(self) -> str:
        """Generate a comprehensive validation report."""
        report = []
        report.append("# Protovalidate Implementation Report")
        report.append("")
        report.append(f"**Repository**: {self.repo_root}")
        report.append(f"**Files Processed**: {self.files_processed}")
        report.append(f"**Validation Rules Added**: {self.rules_added}")
        report.append("")
        
        # List all proto files with their validation status
        proto_files = list(self.repo_root.rglob("*.proto"))
        if proto_files:
            report.append("## Protobuf Files Status")
            report.append("")
            for proto_file in proto_files:
                with open(proto_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                has_import = self.has_protovalidate_import(content)
                has_rules = "[(validate.rules)" in content
                
                status = "✅ Complete" if has_import and has_rules else "⚠️ Partial" if has_import else "❌ Missing"
                report.append(f"- `{proto_file.relative_to(self.repo_root)}`: {status}")
        
        report.append("")
        report.append("## Validation Rule Patterns Applied")
        report.append("")
        for field_type, rules in self.validation_rules.items():
            report.append(f"### {field_type.title()} Fields")
            for rule in rules:
                report.append(f"- **{rule.field_type}**: `{rule.rule_pattern}` - {rule.description}")
            report.append("")
        
        report.append("## Next Steps")
        report.append("")
        report.append("1. Review the applied validation rules")
        report.append("2. Run `buf lint` to verify syntax")
        report.append("3. Run `buf generate` to test code generation")
        report.append("4. Customize validation rules as needed")
        report.append("5. Add additional validation rules for domain-specific requirements")
        
        return "\n".join(report)

def main():
    if len(sys.argv) > 1:
        repo_root = sys.argv[1]
    else:
        repo_root = os.getcwd()
    
    injector = MassProtovalidateInjector(repo_root)
    
    # Check if there are any proto files
    proto_files = list(Path(repo_root).rglob("*.proto"))
    
    if not proto_files:
        print("No protobuf files found. Creating example files...")
        injector.create_example_proto_files()
        print("\nExample files created. Run the script again to apply protovalidate.")
        return
    
    print(f"Found {len(proto_files)} protobuf files. Processing...")
    
    # Process all proto files with automatic rule application
    injector.process_all_proto_files(auto_apply=True)
    
    # Generate report
    report = injector.generate_validation_report()
    report_path = Path(repo_root) / "protovalidate_implementation_report.md"
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"\nDetailed report saved to: {report_path}")
    
    # Run buf lint to verify
    print("\nRunning buf lint to verify changes...")
    returncode, output = injector.run_buf_lint()
    if returncode == 0:
        print("✅ Buf lint passed successfully!")
    else:
        print(f"⚠️ Buf lint warnings/errors:")
        print(output)

if __name__ == "__main__":
    main()