# Protovalidate Implementation Guide

This document provides comprehensive instructions for implementing protovalidate validation across all protobuf files in the repository.

## Overview

This repository now includes:

1. **buf configuration** with protovalidate dependency (`buf.yaml`)
2. **Automated protovalidate injection tool** (`tools/mass-protovalidate-injector.py`)
3. **Example protobuf files** with protovalidate rules applied
4. **Code generation configuration** (`buf.gen.yaml`)

## Quick Start

### For New Repositories (No Proto Files)

```bash
# Run the tool to create example files and apply protovalidate
cd /path/to/your/repo
python3 tools/mass-protovalidate-injector.py
```

### For Existing Repositories (With Proto Files)

```bash
# Copy the tool and configuration files
cp /path/to/ghcommon/buf.yaml .
cp /path/to/ghcommon/buf.gen.yaml .
cp /path/to/ghcommon/tools/mass-protovalidate-injector.py tools/

# Run the tool to add protovalidate to all existing proto files
python3 tools/mass-protovalidate-injector.py
```

## Tool Features

### Automatic Import Addition

The tool automatically adds the protovalidate import to all proto files:

```protobuf
import "buf/validate/validate.proto";
```

### Smart Validation Rule Detection

The tool intelligently suggests validation rules based on:

- **Field names**: `email` → email validation, `url` → URI validation
- **Field types**: `string` → min_len, `int32` → positive/non-negative
- **Common patterns**: `id` fields → UUID validation, `timestamp` → positive validation

### Supported Field Types and Validations

#### String Fields

```protobuf
string email = 1 [(validate.rules).string.email = true];
string url = 2 [(validate.rules).string.uri = true];
string user_id = 3 [(validate.rules).string.uuid = true];
string ip_address = 4 [(validate.rules).string.ip = true];
string hostname = 5 [(validate.rules).string.hostname = true];
string name = 6 [(validate.rules).string.min_len = 1];
string description = 7 [(validate.rules).string.max_len = 255];
```

#### Numeric Fields

```protobuf
int32 count = 1 [(validate.rules).int32.gte = 0];
int32 port = 2 [(validate.rules).int32.gt = 0];
int64 timestamp = 3 [(validate.rules).int64.gt = 0];
double percentage = 4 [(validate.rules).double.gte = 0, lte = 100];
float score = 5 [(validate.rules).float.gte = 0];
```

#### Repeated Fields

```protobuf
repeated string tags = 1 [(validate.rules).repeated.min_items = 1];
repeated int32 values = 2 [(validate.rules).repeated.max_items = 100];
repeated string unique_ids = 3 [(validate.rules).repeated.unique = true];
```

## Configuration Files

### buf.yaml

```yaml
version: v1
breaking:
  use:
    - FILE
lint:
  use:
    - DEFAULT
    - COMMENTS
    - FILE_LOWER_SNAKE_CASE
deps:
  - buf.build/bufbuild/protovalidate
```

### buf.gen.yaml

```yaml
version: v1
plugins:
  - plugin: buf.build/protocolbuffers/go
    out: sdks/go
    opt:
      - paths=source_relative
      - module=github.com/your-org/your-repo
  - plugin: buf.build/grpc/go
    out: sdks/go
    opt:
      - paths=source_relative
      - require_unimplemented_servers=false
```

## Usage Examples

### Running the Tool

```bash
# Create example files (if no proto files exist)
python3 tools/mass-protovalidate-injector.py

# Process all proto files automatically
python3 tools/mass-protovalidate-injector.py
```

### Tool Output

```
Found 3 protobuf files. Processing...
Scanning for protobuf files...
Found 3 protobuf files

Processing: /path/to/user.proto
  ✓ Added protovalidate import
  Found 5 fields that could benefit from validation:
    Line 17: user_id (string)
      ✓ Applied: UUID validation
    Line 20: email (string)
      ✓ Applied: Email validation
  ✓ File updated successfully

=== Summary ===
Files processed: 3
Validation rules added: 16
```

## Validation with Buf

### Install Buf

```bash
# Install buf CLI
curl -sSL "https://github.com/bufbuild/buf/releases/latest/download/buf-$(uname -s)-$(uname -m)" \
  -o "/usr/local/bin/buf"
chmod +x "/usr/local/bin/buf"
```

### Validate Syntax

```bash
# Check protobuf syntax and style
buf lint

# Generate code
buf generate

# Breaking change detection
buf breaking --against '.git#branch=main'
```

## Advanced Customization

### Custom Validation Rules

You can add custom validation rules by modifying the `validation_rules` dictionary in the tool:

```python
self.validation_rules = {
    "string": [
        ValidationRule("custom", "pattern = '^[A-Z][a-z]+$'", "Custom pattern"),
        # ... existing rules
    ]
}
```

### Field-Specific Rules

For specific validation needs, manually edit proto files:

```protobuf
// Custom validation rules
string password = 1 [(validate.rules).string = {
  min_len: 8,
  max_len: 128,
  pattern: "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)[a-zA-Z\\d@$!%*?&]{8,}$"
}];

// Complex numeric validation
int32 age = 2 [(validate.rules).int32 = {
  gte: 0,
  lte: 150
}];

// Message validation
repeated User users = 3 [(validate.rules).repeated = {
  min_items: 1,
  max_items: 1000,
  items: {
    message: {
      required: true
    }
  }
}];
```

## Integration with CI/CD

Add buf validation to your CI/CD pipeline:

```yaml
# .github/workflows/protobuf-validation.yml
name: Protobuf Validation
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: bufbuild/buf-setup-action@v1
      - name: Lint protobuf files
        run: buf lint
      - name: Generate code
        run: buf generate
      - name: Breaking change detection
        if: github.event_name == 'pull_request'
        run: buf breaking --against '.git#branch=${{ github.base_ref }}'
```

## Troubleshooting

### Common Issues

1. **Missing protovalidate dependency**
   ```
   Error: import "buf/validate/validate.proto": file not found
   ```
   Solution: Ensure `buf.build/bufbuild/protovalidate` is in `buf.yaml` deps.

2. **Invalid validation syntax**
   ```
   Error: expected field name or '}'
   ```
   Solution: Check validation rule syntax matches protovalidate format.

3. **Tool not finding proto files**
   ```
   No protobuf files found in the repository.
   ```
   Solution: Ensure proto files are in the repository and have `.proto` extension.

### Validation Debugging

```bash
# Check specific file
buf lint path/to/file.proto

# Verbose output
buf lint --debug

# Check dependencies
buf mod ls-files
```

## Performance Considerations

For repositories with thousands of proto files:

1. **Run in batches**: Process files in smaller groups to manage memory usage
2. **Parallel processing**: The tool processes files sequentially but can be modified for parallel processing
3. **Selective processing**: Use file filters to process specific modules or directories

## Best Practices

1. **Review generated rules**: Always review automatically applied validation rules
2. **Test thoroughly**: Run buf generate and test generated code
3. **Document custom rules**: Add comments explaining complex validation logic
4. **Version control**: Commit changes in logical chunks for easier review
5. **CI integration**: Add buf validation to your CI pipeline

## Example Proto File

Here's a complete example of a proto file with protovalidate rules:

```protobuf
// file: pkg/user/proto/user_service.proto
// version: 1.0.0
// guid: 1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d

edition = "2023";

import "buf/validate/validate.proto";

package gcommon.v1.user;

option go_package = "github.com/your-org/repo/pkg/user/proto;userpb";

// CreateUserRequest with comprehensive validation
message CreateUserRequest {
  // User email (must be valid email format)
  string email = 1 [(validate.rules).string.email = true];
  
  // Display name (1-100 characters)
  string display_name = 2 [(validate.rules).string = {
    min_len: 1,
    max_len: 100
  }];
  
  // Age (must be 13-120)
  int32 age = 3 [(validate.rules).int32 = {
    gte: 13,
    lte: 120
  }];
  
  // Profile tags (1-10 unique tags)
  repeated string tags = 4 [(validate.rules).repeated = {
    min_items: 1,
    max_items: 10,
    unique: true,
    items: {
      string: {
        min_len: 1,
        max_len: 50
      }
    }
  }];
}
```

This comprehensive guide should help you implement protovalidate across thousands of protobuf files efficiently and correctly.