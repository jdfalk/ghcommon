# file: PROTOVALIDATE_INTEGRATION.md
# version: 1.0.0
# guid: 9c0d1e2f-3a4b-5c6d-7e8f-9a0b1c2d3e4f

# Protovalidate Integration for ghcommon Repository

This document describes the comprehensive protovalidate integration system for the ghcommon repository, designed to add validation rules to thousands of protobuf files efficiently.

## Overview

The protovalidate integration consists of:

1. **Automated Tool**: `tools/protovalidate-adder.py` - Adds protovalidate imports and validation rules
2. **Configuration**: `buf.yaml` and `buf.gen.yaml` - Buf configuration with protovalidate support
3. **Example Files**: Sample protobuf files demonstrating best practices
4. **Documentation**: This guide and integration instructions

## Features

### Automated Protovalidate Addition

The `protovalidate-adder.py` tool provides:

- **Mass Processing**: Handles thousands of proto files efficiently
- **Smart Import Detection**: Adds protovalidate import only if missing
- **Intelligent Validation Rules**: Generates appropriate rules based on field types and names
- **Existing Rule Preservation**: Doesn't overwrite existing validation rules
- **Dry Run Mode**: Preview changes before applying them
- **Compatibility Mode**: Add rules as comments when dependency isn't available

### Intelligent Validation Rules

The tool automatically generates validation rules based on field patterns:

#### String Fields
- **ID fields** (`user_id`, `client_id`, etc.): `string.min_len = 1`
- **Email fields**: `string.pattern = "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"`
- **Name fields**: `string.min_len = 1, string.max_len = 255`
- **URL fields**: `string.uri = true`
- **General strings**: `string.min_len = 1`

#### Numeric Fields
- **Age fields**: `int32.gte = 0, int32.lte = 150`
- **Count/Size fields**: `int32.gte = 0`
- **Port fields**: `int32.gte = 1, int32.lte = 65535`
- **Percentage fields**: `float.gte = 0.0, float.lte = 100.0`
- **Score/Rating fields**: `double.gte = 0.0, double.lte = 10.0`

#### Array Fields
- **Repeated fields**: `repeated.min_items = 1`

## Usage

### Basic Usage

```bash
# Process all proto files in the repository
python3 tools/protovalidate-adder.py

# Dry run to preview changes
python3 tools/protovalidate-adder.py --dry-run

# Process a specific file
python3 tools/protovalidate-adder.py --file pkg/auth/proto/auth_request.proto

# Compatibility mode (adds rules as comments)
python3 tools/protovalidate-adder.py --compatibility-mode
```

### Command Line Options

- `--repo-root PATH`: Repository root directory (default: current directory)
- `--dry-run`: Show what would be changed without making actual changes
- `--file PATH`: Process a specific proto file instead of all files
- `--compatibility-mode`: Add validation rules as comments when dependency isn't available

### Example Output

```
Found 4 proto files to process
Mode: LIVE

✓ Modified: /path/to/pkg/common/proto/user_info.proto
✓ Modified: /path/to/pkg/auth/proto/auth_request.proto
✓ Modified: /path/to/pkg/queue/proto/queue_message.proto
- Unchanged: /path/to/pkg/common/proto/config_data.proto

Summary:
  Files processed: 4
  Files modified: 3
  Files unchanged: 1

Running buf lint to verify changes...
✓ All proto files pass buf lint
```

## Configuration Files

### buf.yaml

Basic buf configuration with protovalidate dependency:

```yaml
version: v1
name: buf.build/jdfalk/ghcommon
deps:
  - buf.build/bufbuild/protovalidate
lint:
  use:
    - DEFAULT
    - COMMENTS
    - FILE_LOWER_SNAKE_CASE
```

### buf.gen.yaml

Code generation configuration with protovalidate support:

```yaml
version: v1
plugins:
  - plugin: buf.build/protocolbuffers/go
    out: .
    opt:
      - paths=source_relative
  - plugin: buf.build/bufbuild/validate-go
    out: .
    opt:
      - paths=source_relative
```

## Example Proto Files

### Before Processing

```protobuf
syntax = "proto3";

package gcommon.v1.auth;

message AuthRequest {
  string username = 1;
  string password = 2;
  string email = 3;
  int32 timeout_seconds = 4;
  repeated string scopes = 5;
}
```

### After Processing

```protobuf
syntax = "proto3";

package gcommon.v1.auth;

import "buf/validate/validate.proto";

message AuthRequest {
  string username = 1 [(validate.rules).string.min_len = 1, string.max_len = 255];
  string password = 2 [(validate.rules).string.min_len = 1];
  string email = 3 [(validate.rules).string.pattern = "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"];
  int32 timeout_seconds = 4 [(validate.rules).int32.gte = 0];
  repeated string scopes = 5 [(validate.rules).repeated.min_items = 1];
}
```

## Integration with Existing Tools

The protovalidate system integrates with existing repository tools:

### Mass Protobuf Fixer
- The existing `mass-protobuf-fixer.py` can be used alongside protovalidate-adder
- Run protovalidate-adder first, then mass-protobuf-fixer for import cleanup

### Protobuf Cycle Fixer
- The `protobuf-cycle-fixer.py` works with protovalidate-enhanced files
- No conflicts with validation imports

### VS Code Tasks
- Integration with repository's VS Code task system
- Can be run via task for consistent logging

## Best Practices

### Field Naming Conventions
- Use descriptive field names for better automatic validation
- Follow patterns like `user_id`, `email_address`, `timeout_seconds` for intelligent rule generation

### Custom Validation Rules
- The tool preserves existing validation rules
- Add custom rules manually for complex business logic
- Use field options for domain-specific validation

### Performance Considerations
- The tool is designed to handle thousands of files efficiently
- Uses streaming processing for large files
- Minimal memory footprint for batch operations

## Troubleshooting

### Common Issues

1. **Import Not Found**
   ```
   Error: buf/validate/validate.proto: file does not exist
   ```
   **Solution**: Run `buf mod update` or use `--compatibility-mode`

2. **Buf Lint Errors**
   ```
   Error: editions are not yet supported
   ```
   **Solution**: Update proto files to use `syntax = "proto3"` instead of `edition = "2023"`

3. **Permission Errors**
   ```
   Error: Permission denied
   ```
   **Solution**: Ensure script is executable: `chmod +x tools/protovalidate-adder.py`

### Validation

After running the tool, verify the results:

```bash
# Check generated validation rules
grep -r "validate.rules" pkg/

# Lint proto files
buf lint

# Generate code to test compilation
buf generate
```

## Contributing

When adding new validation patterns:

1. Update the `get_field_validation_rules()` method in `protovalidate-adder.py`
2. Add test cases with example proto files
3. Update this documentation with new patterns
4. Test with the existing repository protobuf files

## References

- [Protovalidate Documentation](https://protovalidate.com/)
- [Protovalidate Quickstart](https://protovalidate.com/quickstart/#add-protovalidate-to-schemas)
- [Buf CLI Documentation](https://docs.buf.build/)
- [Repository Protobuf Instructions](.github/instructions/protobuf.instructions.md)

## License

This integration follows the same license as the ghcommon repository.