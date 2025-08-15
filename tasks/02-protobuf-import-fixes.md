# Task 2: Protobuf Import Issues Resolution

<!-- file: tasks/02-protobuf-import-fixes.md -->
<!-- version: 1.0.0 -->
<!-- guid: 23456789-2345-2345-2345-234567890bcd -->

## Overview

Fix protobuf import issues across all Go files, ensure proper proto generation, and resolve type conflicts. Many Go files are importing wrong proto packages or using custom types instead of generated protobuf types.

## Critical Instructions

**NEVER edit README.md, CHANGELOG.md, TODO.md or other documentation files directly. ALWAYS use:**

- `scripts/create-doc-update.sh` for documentation updates
- `scripts/create-issue-update.sh` for issue updates
- This prevents merge conflicts between multiple AI agents

**ALWAYS follow the VS Code task priority:**

1. Use VS Code tasks first (via `run_task` tool)
2. Use `copilot-agent-util` / `copilot-agent-utilr`
3. Manual terminal commands only as last resort

## Repository Standards

### Protobuf Instructions

<!-- file: .github/instructions/protobuf.instructions.md -->
<!-- version: 3.0.0 -->
<!-- guid: 7d6c5b4a-3c2d-1e0f-9a8b-7c6d5e4f3a2b -->
<!-- DO NOT EDIT: This file is managed centrally in ghcommon repository -->
<!-- To update: Create an issue/PR in jdfalk/ghcommon -->

---
applyTo: "**/*.proto"
description: |
  Protocol Buffers (protobuf) style and documentation rules for Copilot/AI agents and VS Code Copilot customization. These rules extend the general instructions in `general-coding.instructions.md` and implement comprehensive protobuf best practices including the 1-1-1 design pattern, Edition 2023 features, and Google's style guide.
---

# Protobuf Coding Instructions

## Core Principles

- Follow the [general coding instructions](general-coding.instructions.md)
- Follow the
  [Google Protobuf Style Guide](https://protobuf.dev/programming-guides/style/)
- Implement the **1-1-1 Design Pattern**: **ONE** message/enum/service per file
- Use [Edition 2023](https://protobuf.dev/programming-guides/editions/) for all
  new files
- Follow [Proto Best Practices](https://protobuf.dev/best-practices/dos-donts/)

## Required File Header

All protobuf files must begin with a standard header as described in the
[general coding instructions](general-coding.instructions.md):

```protobuf
// file: path/to/file.proto
// version: 1.0.0
// guid: 123e4567-e89b-12d3-a456-426614174000

edition = "2023";

package your.package.name;

option go_package = "github.com/owner/repo/path/to/package;packagepb";
```

## Edition 2023 Requirements

- **MANDATORY**: All proto files MUST use `edition = "2023";` as the first
  non-comment line
- Enhanced features with better defaults and future-proofing
- Improved validation and hybrid API support
- Better backwards compatibility with proto2/proto3

## 1-1-1 Design Pattern (MANDATORY)

Each protobuf file contains exactly ONE of:

- One message definition
- One enum definition
- One service definition

### Benefits

- **Modularity**: Easy to find and modify specific types
- **Dependency Management**: Clear import relationships
- **Code Generation**: Cleaner generated code
- **Team Collaboration**: Reduces merge conflicts
- **Build Optimization**: Smaller transitive dependencies

### File Organization Structure

```
pkg/module/proto/
├── types/             # Basic types for import (shared)
│   ├── status.proto   # Common enums
│   ├── error.proto    # Error types
│   └── metadata.proto # Metadata structures
├── messages/          # 1-1-1 message definitions
│   ├── user_info.proto
│   └── config_data.proto
├── enums/             # 1-1-1 enum definitions
│   ├── user_status.proto
│   └── priority_level.proto
├── services/          # 1-1-1 service definitions
│   ├── auth_service.proto
│   └── user_service.proto
├── requests/          # Request message definitions
│   ├── create_user_request.proto
│   └── get_user_request.proto
└── responses/         # Response message definitions
    └── get_user_response.proto
```

## Naming Conventions

### CRITICAL: Module Prefix Strategy for Avoiding Conflicts

**Problem**: Multiple packages can have similar message names, causing import conflicts and confusion.

**Solution**: Use consistent module prefixes for all message types to ensure uniqueness across the entire project.

### Module Prefix Rules (MANDATORY)

1. **All messages MUST include module prefix**: `{Module}{MessageName}`
2. **Consistent prefixing**: Either ALL messages in a module have prefixes OR NONE do
3. **Module prefix examples**:

### Module Prefix Mapping

| Module     | Prefix     | Examples                                                              |
| ---------- | ---------- | --------------------------------------------------------------------- |
| `auth`     | `Auth`     | `AuthUserInfo`, `AuthSessionData`, `AuthLoginRequest`                 |
| `subtitle` | `Subtitle` | `SubtitleRecord`, `SubtitleMetadata`, `SubtitleProcessingJob`         |
| `metrics`  | `Metrics`  | `MetricsHealthStatus`, `MetricsBatchOptions`, `MetricsCollectionData` |
| `logging`  | `Log`      | `LogEntry`, `LogLevel`, `LogConfiguration`                            |
| `storage`  | `Storage`  | `StorageBackend`, `StorageConfiguration`, `StorageMetrics`            |

### General Naming Rules

- **Messages**: PascalCase (e.g., `UserProfile`, `AuthRequest`)
- **Fields**: snake_case (e.g., `user_id`, `created_at`)
- **Enums**: PascalCase (e.g., `UserStatus`, `LogLevel`)
- **Enum values**: SCREAMING_SNAKE_CASE (e.g., `USER_STATUS_ACTIVE`)
- **Services**: PascalCase ending in `Service` (e.g., `AuthService`)
- **RPCs**: PascalCase verbs (e.g., `CreateUser`, `GetProfile`)

## Package Naming

- Use reverse domain notation: `com.company.product.module`
- For GitHub projects: `github.com.owner.repo.module`
- Keep packages short and meaningful
- Use dots to separate logical components

## Go Package Options

**MANDATORY** for all proto files:

```protobuf
option go_package = "github.com/owner/repo/path/to/package;packagepb";
```

### Guidelines

- Path should reflect the actual Go import path
- Package alias should end with `pb` (e.g., `authpb`, `userpb`)
- Use lowercase for package aliases
- Match the proto package structure

## Field Guidelines

### Field Numbers

- Use 1-15 for frequently used fields (more efficient encoding)
- Reserve numbers 19000-19999 for internal use
- Never reuse field numbers
- Use `reserved` keyword for deprecated fields

### Field Types

- Prefer `string` over `bytes` for text data
- Use `int64` for timestamps (Unix epoch)
- Use `repeated` instead of custom collection types
- Use `oneof` for mutually exclusive fields

### Field Naming

- Use snake_case consistently
- Be descriptive but concise
- Avoid abbreviations unless well-known
- Use consistent naming across related messages

## Service Definitions

### RPC Naming

- Use verb-noun pattern: `CreateUser`, `GetProfile`, `DeleteSession`
- Use `List` for collection retrieval: `ListUsers`
- Use `Batch` for bulk operations: `BatchCreateUsers`

### Request/Response Messages

- Always create dedicated request/response types
- Name them `{RPC}Request` and `{RPC}Response`
- Include common fields like pagination in requests
- Include metadata fields in responses

### Example Service

```protobuf
service UserService {
  rpc CreateUser(CreateUserRequest) returns (CreateUserResponse);
  rpc GetUser(GetUserRequest) returns (GetUserResponse);
  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse);
  rpc UpdateUser(UpdateUserRequest) returns (UpdateUserResponse);
  rpc DeleteUser(DeleteUserRequest) returns (DeleteUserResponse);
}
```

## Validation and Documentation

### Field Documentation

- Document all fields with clear, concise comments
- Include constraints and validation rules
- Explain relationships between fields
- Document default behaviors

### Message Documentation

- Explain the purpose and use case of each message
- Document any business logic or constraints
- Include usage examples when helpful

### Service Documentation

- Document each RPC method's behavior
- Include error conditions and responses
- Document authentication/authorization requirements

## Evolution and Compatibility

### Adding Fields

- Always use new field numbers
- Make new fields optional
- Provide sensible defaults
- Document backward compatibility impact

### Deprecating Fields

- Use `deprecated = true` option
- Document replacement patterns
- Plan migration timeline
- Use `reserved` for removed fields

### Version Management

- Include version information in package names when needed
- Use semantic versioning for breaking changes
- Maintain compatibility within major versions

## Best Practices

### Performance

- Order fields by usage frequency (most used: 1-15)
- Use appropriate field types for data size
- Consider message size and nesting depth
- Use pagination for large collections

### Security

- Validate all input fields
- Sanitize string fields appropriately
- Use proper authentication for services
- Document security requirements

### Testing

- Create comprehensive test cases for all messages
- Test serialization/deserialization
- Validate field constraints
- Test service implementations

### Code Organization

- Group related proto files logically
- Use consistent directory structure
- Maintain clear import dependencies
- Follow the 1-1-1 pattern strictly

## Common Anti-Patterns to Avoid

1. **Multiple entities per file** - violates 1-1-1 pattern
2. **Inconsistent naming** - mixing conventions
3. **Reusing field numbers** - breaks compatibility
4. **Overly nested messages** - impacts performance
5. **Missing documentation** - reduces maintainability
6. **Circular imports** - creates dependency issues
7. **Generic message types** - reduces type safety

### Go Language Standards

Follow the complete [Go instructions](../.github/instructions/go.instructions.md) which require Go 1.23+ and include comprehensive style guidelines.

### Rust Utility Instructions

Use the [Rust utility](../.github/instructions/rust-utility.instructions.md) for all development operations. Download from: https://github.com/jdfalk/copilot-agent-util-rust

## Current Issues Identified

### 1. Import Path Problems

**Files with Issues:**
- `pkg/auth/grpc/authz_service.go` - Importing wrong proto paths
- Multiple files importing non-existent or incorrectly named proto packages
- Go files using custom types instead of generated protobuf types

**Common Problems:**
- Wrong import paths to generated proto files
- Missing or incorrectly configured `go_package` options in proto files
- Proto files not following the 1-1-1 design pattern
- Inconsistent module prefixes causing naming conflicts

### 2. Missing Proto Generation

**Issues:**
- Some proto files may not be generating Go code properly
- `buf.gen.yaml` configuration may be incomplete or incorrect
- Generated files may not be in expected locations
- Import paths in Go files don't match generated package structure

### 3. Type Conflicts and Custom Types

**Problems:**
- Some Go files define their own types instead of using generated proto types
- Type mismatches between proto definitions and Go implementations
- Services not properly implementing generated proto interfaces
- Request/response types defined in Go instead of proto

## Tasks to Complete

### Phase 1: Proto Analysis and Cleanup

1. **Analyze all `.proto` files**
   - Verify they follow Edition 2023 requirements
   - Check 1-1-1 design pattern compliance
   - Validate `go_package` options are correct
   - Ensure module prefixes are consistent

2. **Check buf configuration**
   - Verify `buf.yaml` and `buf.gen.yaml` are properly configured
   - Ensure output directories are correct
   - Check lint and breaking change rules

3. **Run proto generation**
   - Use VS Code task: "Buf Generate with Output"
   - Verify all proto files generate Go code successfully
   - Check generated files are in expected locations

### Phase 2: Go File Import Fixes

1. **Identify import issues**
   - Scan all `.go` files for proto imports
   - Check if import paths match generated package structure
   - Identify files using custom types instead of proto types

2. **Fix import paths**
   - Update incorrect import statements
   - Ensure consistent use of generated proto packages
   - Remove unused imports

3. **Replace custom types**
   - Identify custom structs that should use proto types
   - Replace with proper proto message types
   - Update function signatures and method implementations

### Phase 3: Service Implementation Fixes

1. **Fix service implementations**
   - Ensure services properly embed `UnimplementedXXXServer` types
   - Update method signatures to match generated interfaces
   - Fix request/response type usage

2. **Update method implementations**
   - Use proper proto types for parameters and returns
   - Fix type conversions and field access
   - Ensure proper error handling

### Phase 4: Testing and Validation

1. **Build verification**
   - Run `go build` on all modules
   - Fix any compilation errors
   - Ensure no import cycle issues

2. **Integration testing**
   - Test protobuf serialization/deserialization
   - Verify gRPC services work correctly
   - Check backward compatibility

## Specific Files to Fix

### High Priority

1. **`pkg/auth/grpc/authz_service.go`**
   - Fix proto import paths
   - Ensure proper proto type usage
   - Verify service interface implementation

2. **All files in `pkg/auth/`**
   - Check for consistent proto usage
   - Fix any import path issues
   - Ensure generated types are used

### Proto Files to Review

1. **Check all `.proto` files for:**
   - Edition 2023 compliance
   - Proper `go_package` options
   - 1-1-1 design pattern
   - Module prefix consistency

### Generated Code Verification

1. **Ensure proper generation:**
   - Check `gen/` or equivalent output directories
   - Verify Go files are generated for all proto files
   - Check package structure matches import expectations

## Expected Deliverables

1. **Fixed proto files**
   - All proto files follow Edition 2023
   - Proper `go_package` options
   - 1-1-1 design pattern compliance
   - Consistent module prefixes

2. **Updated Go files**
   - Correct proto import paths
   - Use of generated proto types instead of custom types
   - Proper service interface implementations
   - All compilation errors resolved

3. **Working protobuf generation**
   - `buf generate` runs without errors
   - Generated files in correct locations
   - Import paths match generated structure

4. **Testing validation**
   - All modules build successfully
   - Integration tests pass
   - No import cycle issues

## Acceptance Criteria

- [ ] All `.proto` files use Edition 2023
- [ ] All proto files follow 1-1-1 design pattern
- [ ] All `go_package` options are correct
- [ ] All Go imports point to correct generated packages
- [ ] No custom types where proto types should be used
- [ ] All services implement proper proto interfaces
- [ ] `buf generate` runs without errors
- [ ] All Go modules build successfully
- [ ] No compilation or import errors
- [ ] Integration tests pass

## Repository Scope

Focus on these repositories:

1. `/Users/jdfalk/repos/github.com/jdfalk/gcommon` (primary)
2. `/Users/jdfalk/repos/github.com/jdfalk/subtitle-manager`
3. Any other repositories using protobuf from gcommon

## Notes

- Start with `gcommon` as it appears to be the primary proto definition repository
- Test proto generation after each change
- Use VS Code tasks for buf operations when possible
- Document any breaking changes or migration requirements
- Focus on getting the foundation right before expanding to other repos
