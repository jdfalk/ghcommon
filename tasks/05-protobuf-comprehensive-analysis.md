# Task 5: Comprehensive Protobuf Import Analysis and Resolution

<!-- file: tasks/05-protobuf-comprehensive-analysis.md -->
<!-- version: 1.0.0 -->
<!-- guid: 45678901-4567-4567-4567-456789012def -->

## Overview

Perform comprehensive analysis of all protobuf files, Go imports, and generated code across all repositories. Identify and fix all import issues, type conflicts, and missing generated files.

## Critical Instructions

**NEVER edit README.md, CHANGELOG.md, TODO.md or other documentation files directly. ALWAYS use:**

- `scripts/create-doc-update.sh` for documentation updates
- `scripts/create-issue-update.sh` for issue updates
- This prevents merge conflicts between multiple AI agents

**ALWAYS follow the VS Code task priority:**

1. Use VS Code tasks first (via `run_task` tool)
2. Use `copilot-agent-util` / `copilot-agent-utilr`
3. Manual terminal commands only as last resort

## Copilot Agent Utility

Download and install from: <https://github.com/jdfalk/copilot-agent-util-rust>

Or build from source in `tools/copilot-agent-util-rust/`:

```bash
cd tools/copilot-agent-util-rust
cargo build --release
cp target/release/copilot-agent-util /usr/local/bin/
```

## Repository Standards

### Complete Protobuf Instructions

<!-- file: .github/instructions/protobuf.instructions.md -->
<!-- version: 3.0.0 -->
<!-- guid: 7d6c5b4a-3c2d-1e0f-9a8b-7c6d5e4f3a2b -->

## Analysis Tasks

### 1. Protobuf File Inventory

Use the utility to run comprehensive analysis:

```bash
# Check all proto files
copilot-agent-util buf lint

# Generate comprehensive report
copilot-agent-util exec "find . -name '*.proto' -type f | sort > proto_inventory.txt"

# Check for import errors
copilot-agent-util exec "grep -r 'import.*proto' pkg/ | sort > proto_imports.txt"
```

**Required Actions:**

- [ ] List all `.proto` files across all repositories
- [ ] Document current import structure
- [ ] Identify missing or broken imports
- [ ] Check for circular dependencies
- [ ] Validate Edition 2023 compliance

### 2. Go Import Analysis

Analyze all Go files importing protobuf packages:

```bash
# Find all Go files with proto imports
copilot-agent-util exec "find . -name '*.go' -type f -exec grep -l 'proto' {} \; | sort > go_proto_files.txt"

# Check for import errors
copilot-agent-util exec "find . -name '*.go' -type f -exec go build {} \; 2>&1 | tee go_build_errors.txt"
```

**Required Actions:**

- [ ] Identify all Go files importing proto packages
- [ ] Document current import paths being used
- [ ] Find files using wrong import paths
- [ ] Identify files using custom types instead of generated ones
- [ ] List missing generated Go files

### 3. Generated Code Verification

Verify all protobuf code generation:

```bash
# Clean and regenerate all proto code
copilot-agent-util buf generate --clean

# Check generated files
copilot-agent-util exec "find . -name '*.pb.go' -type f | sort > generated_files.txt"
```

**Required Actions:**

- [ ] Verify all proto files generate Go code correctly
- [ ] Check for missing `_grpc.pb.go` files
- [ ] Validate generated code matches proto definitions
- [ ] Ensure no manual edits to generated files
- [ ] Check for outdated generated code

### 4. Import Path Standardization

Standardize all import paths across repositories:

Expected format: `github.com/jdfalk/gcommon/pkg/MODULE/proto`

**Required Actions:**

- [ ] Document current import path patterns
- [ ] Identify inconsistent import paths
- [ ] Update `go.mod` files with correct module paths
- [ ] Fix import statements in all Go files
- [ ] Update proto import statements

### 5. Type Usage Analysis

Analyze usage of protobuf types vs custom types:

```bash
# Find custom type definitions that should use proto
copilot-agent-util exec "grep -r 'type.*struct' pkg/ | grep -v '.pb.go' > custom_types.txt"

# Find functions that should use proto types
copilot-agent-util exec "grep -r 'func.*Request\\|Response' pkg/ | grep -v '.pb.go' > custom_funcs.txt"
```

**Required Actions:**

- [ ] Identify custom types that duplicate proto definitions
- [ ] Find functions using custom types instead of proto types
- [ ] List interfaces that should use proto types
- [ ] Document conversion functions needed
- [ ] Plan migration from custom to proto types

## Specific Repository Analysis

### gcommon Repository

Primary repository containing shared protobuf definitions:

**Key Files to Analyze:**

```bash
# Check auth service
copilot-agent-util exec "find pkg/auth -name '*.go' -type f"
copilot-agent-util exec "find pkg/auth -name '*.proto' -type f"

# Check common types
copilot-agent-util exec "find pkg/common -name '*.go' -type f"
copilot-agent-util exec "find pkg/common -name '*.proto' -type f"

# Check all modules
copilot-agent-util exec "ls -la pkg/"
```

**Expected Issues:**

- Missing generated files
- Incorrect import paths
- Type conflicts between modules
- Circular import dependencies

### subtitle-manager Repository

Repository using gcommon protobuf definitions:

**Key Files to Analyze:**

```bash
# Check main application files
copilot-agent-util exec "find . -name '*.go' -type f | head -20"

# Check for proto usage
copilot-agent-util exec "grep -r 'proto' . --include='*.go'"

# Check go.mod dependencies
copilot-agent-util exec "cat go.mod"
```

**Expected Issues:**

- Importing wrong gcommon version
- Using custom types instead of proto types
- Missing proto dependencies
- Incorrect module references

## Resolution Strategy

### Phase 1: Assessment and Documentation

1. **Run Analysis Commands** using `copilot-agent-util`
2. **Generate Comprehensive Report** with findings
3. **Prioritize Issues** by impact and complexity
4. **Create Fix Plan** with dependencies mapped

### Phase 2: Proto File Fixes

1. **Update Edition 2023** compliance
2. **Fix Import Statements** in proto files
3. **Resolve Circular Dependencies**
4. **Regenerate All Code** with buf generate

### Phase 3: Go Import Fixes

1. **Update go.mod Files** with correct versions
2. **Fix Import Paths** in all Go files
3. **Replace Custom Types** with proto types
4. **Add Missing Interfaces** for proto types

### Phase 4: Testing and Validation

1. **Build All Modules** to verify fixes
2. **Run Unit Tests** to catch regressions
3. **Integration Testing** across repositories
4. **Performance Testing** for proto usage

## Error Resolution Patterns

### Common Import Issues

```go
// WRONG:
import "github.com/jdfalk/gcommon/auth/proto"

// CORRECT:
import authpb "github.com/jdfalk/gcommon/pkg/auth/proto"
```

### Common Type Issues

```go
// WRONG: Custom type
type AuthRequest struct {
    Token string
    User  string
}

// CORRECT: Use proto type
func Authenticate(req *authpb.AuthorizeRequest) (*authpb.AuthorizeResponse, error) {
    // Implementation
}
```

### Common Generation Issues

```bash
# Fix buf.gen.yaml configuration
copilot-agent-util exec "cat buf.gen.yaml"

# Ensure proper buf.yaml setup
copilot-agent-util exec "cat buf.yaml"

# Clean regeneration
copilot-agent-util buf generate --clean
```

## Expected Deliverables

1. **Comprehensive Analysis Report**
   - Complete inventory of all proto files
   - List of all import issues
   - Documentation of current vs expected structure
   - Priority-ranked fix list

2. **Fixed Proto Files**
   - All files using Edition 2023
   - Correct import statements
   - No circular dependencies
   - Complete generated code

3. **Fixed Go Files**
   - Correct import paths
   - Using proto types instead of custom types
   - All build errors resolved
   - Consistent coding standards

4. **Updated Documentation**
   - Import path standards
   - Type usage guidelines
   - Build and generation procedures
   - Troubleshooting guide

5. **Test Suite**
   - Unit tests for all modules
   - Integration tests across repositories
   - Build verification scripts
   - Performance benchmarks

## Success Criteria

- [ ] All protobuf files compile without errors
- [ ] All Go files build successfully
- [ ] No import path conflicts
- [ ] Consistent use of proto types
- [ ] Complete test coverage
- [ ] Documentation is up to date
- [ ] Performance meets requirements
- [ ] Cross-repository compatibility verified

## Tools and Utilities

Use these commands with `copilot-agent-util`:

```bash
# Protobuf operations
copilot-agent-util buf lint
copilot-agent-util buf generate
copilot-agent-util buf breaking --against .git#branch=main

# Go operations  
copilot-agent-util exec "go mod tidy"
copilot-agent-util exec "go build ./..."
copilot-agent-util exec "go test ./..."

# Analysis operations
copilot-agent-util exec "find . -name '*.proto' -type f"
copilot-agent-util exec "grep -r 'import.*proto' ."
copilot-agent-util exec "go list -m all"
```
