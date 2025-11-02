<!-- file: docs/cross-registry-todos/task-07/t07-part1.md -->
<!-- version: 1.1.0 -->
<!-- guid: t07-protobuf-packages-part1-l5m6n7o8-p9q0 -->

# Task 07 Part 1: Protobuf Package Publishing - Overview

> **Status:** ✅ Completed  
> **Updated:** `.github/workflows/release-protobuf.yml` v1.3.0 now pushes modules to Buf Schema
> Registry (when `BUF_TOKEN` is configured) after artifacts are generated.  
> **Verification:** Job summaries report publish outcomes, and Buf pushes occur only on tagged
> releases with the secret present.

## Task Overview

**Priority:** 2 (High) **Estimated Lines:** ~3,500 lines (6 parts) **Complexity:** High
**Dependencies:** Tasks 01, 03 (Rust), 04 (Go), 05 (Python), 06 (npm)

## Objective

Create a comprehensive workflow for publishing protobuf packages to multiple registries:

1. **Buf Schema Registry (BSR)** - Primary protobuf repository
2. **Multi-Language SDKs** - Generated code packages
3. **GitHub Releases** - Versioned protobuf artifacts
4. **Container Registry** - Docker images with protoc tooling

## What This Task Accomplishes

### Primary Goals

1. **Buf BSR Publishing**: Push protobuf schemas to Buf Schema Registry
2. **Multi-Language SDK Generation**: Generate SDKs for Go, Python, TypeScript, Rust
3. **Package Publishing**: Publish generated SDKs to language-specific registries
4. **Versioning**: Semantic versioning for protobuf schemas and SDKs
5. **Documentation**: Auto-generate API documentation from protobuf comments
6. **Validation**: Lint and breaking change detection

### Workflow Structure

```
protobuf-release.yml
├── detect-protobuf-changes     # Detect .proto files
├── validate-protobuf           # Buf lint and breaking change detection
├── publish-buf-bsr             # Push to Buf Schema Registry
├── generate-go-sdk             # Generate and publish Go module
├── generate-python-sdk         # Generate and publish Python package
├── generate-typescript-sdk     # Generate and publish npm package
├── generate-rust-sdk           # Generate and publish Rust crate
├── create-github-release       # Create release with artifacts
├── verify-publication          # Verify all registries
└── collect-metrics             # Generate metrics report
```

## Prerequisites

### Required Accounts and Tokens

**1. Buf Schema Registry Account**

- Create account: <https://buf.build/>
- Organization: `buf.build/your-org`
- Repository: `buf.build/your-org/your-repo`

**2. Buf Authentication Token**

```bash
# Generate token at https://buf.build/settings/tokens
# Add as GitHub secret: BUF_TOKEN
```

**3. Language Registry Access**

- **Go**: GitHub (automatic via tags)
- **Python**: PyPI + GitHub Packages (NPM_TOKEN, GITHUB_TOKEN)
- **TypeScript**: npm + GitHub Packages (NPM_TOKEN)
- **Rust**: crates.io + GitHub (CARGO_REGISTRY_TOKEN)

### Required GitHub Secrets

```yaml
# In repository settings > Secrets and variables > Actions
BUF_TOKEN: # Buf Schema Registry authentication
CARGO_REGISTRY_TOKEN: # crates.io publishing
NPM_TOKEN: # npm registry publishing
PYPI_TOKEN: # PyPI publishing
GITHUB_TOKEN: # Automatic (GitHub Packages, releases)
```

### Repository Structure

```
repository/
├── proto/                    # Protobuf source files
│   └── v1/
│       ├── api.proto
│       ├── types.proto
│       └── service.proto
├── buf.yaml                  # Buf configuration
├── buf.gen.yaml             # Code generation configuration
├── buf.lock                 # Buf dependency lock
├── .github/
│   └── workflows/
│       └── protobuf-release.yml
└── gen/                     # Generated code output (gitignored)
    ├── go/
    ├── python/
    ├── typescript/
    └── rust/
```

## Buf Schema Registry Basics

### Why Use BSR?

**Benefits:**

1. **Central Schema Repository**: Single source of truth for protobuf schemas
2. **Dependency Management**: Automatic transitive dependency resolution
3. **Breaking Change Detection**: Automated compatibility checking
4. **Version Management**: Semantic versioning for schemas
5. **Multi-Language Support**: Generate SDKs for any language
6. **Documentation**: Auto-generated API docs
7. **Private Schemas**: Support for private/internal APIs

### BSR vs Traditional Protobuf

**Traditional Approach:**

- Protobuf files in git repository
- Manual dependency management
- Copy/paste across repositories
- Manual breaking change checks
- Per-repository code generation

**BSR Approach:**

- Centralized schema registry
- Automatic dependency resolution
- Import from BSR (`buf.build/org/repo`)
- Automated breaking change detection
- Remote code generation

### BSR Repository Structure

**Format:** `buf.build/{owner}/{repository}`

**Example:**

```
buf.build/jdfalk/ghcommon
├── proto/v1/           # Module: proto/v1
│   ├── api.proto
│   └── types.proto
└── proto/v2/           # Module: proto/v2
    └── service.proto
```

**Commits and Tags:**

- **Commits**: Immutable SHA references (like git)
- **Tags**: Human-readable version labels (v1.0.0)
- **Branches**: Not supported (BSR is append-only)

## Buf Configuration Files

### buf.yaml - Module Configuration

```yaml
# buf.yaml
version: v2
modules:
  - path: proto
    name: buf.build/jdfalk/ghcommon
deps:
  - buf.build/googleapis/googleapis
  - buf.build/grpc-ecosystem/grpc-gateway
lint:
  use:
    - DEFAULT
    - COMMENTS
  except:
    - PACKAGE_VERSION_SUFFIX
breaking:
  use:
    - FILE
  ignore:
    - proto/v1/deprecated.proto
```

**Key Fields:**

- `version`: Buf config version (v1 or v2)
- `modules`: List of protobuf modules in repository
- `modules[].name`: Full BSR path for publishing
- `deps`: External BSR dependencies
- `lint`: Linting rules configuration
- `breaking`: Breaking change detection rules

### buf.gen.yaml - Code Generation

```yaml
# buf.gen.yaml
version: v2
managed:
  enabled: true
  override:
    - file_option: go_package_prefix
      value: github.com/jdfalk/ghcommon/gen/go
plugins:
  # Go
  - remote: buf.build/protocolbuffers/go
    out: gen/go
    opt:
      - paths=source_relative
  - remote: buf.build/grpc/go
    out: gen/go
    opt:
      - paths=source_relative

  # Python
  - remote: buf.build/protocolbuffers/python
    out: gen/python
  - remote: buf.build/grpc/python
    out: gen/python

  # TypeScript
  - remote: buf.build/connectrpc/es
    out: gen/typescript
    opt:
      - target=ts

  # Rust
  - remote: buf.build/protocolbuffers/rust
    out: gen/rust
```

**Key Fields:**

- `version`: Generation config version
- `managed`: Managed mode (automatic import path generation)
- `plugins`: List of code generation plugins
- `plugins[].remote`: BSR-hosted plugin
- `plugins[].out`: Output directory
- `plugins[].opt`: Plugin-specific options

### buf.lock - Dependency Lock

```yaml
# buf.lock
version: v2
deps:
  - name: buf.build/googleapis/googleapis
    commit: 75b4300737fb4efca0831636be94e517
  - name: buf.build/grpc-ecosystem/grpc-gateway
    commit: 3f42134f4c564983838425bc43c7a65f
```

**Auto-generated:** Run `buf mod update` to regenerate

## Multi-Language SDK Publishing Strategy

### Strategy Overview

Each language SDK is published to its native registry:

| Language   | Primary Registry  | Secondary Registry | Package Name Pattern         |
| ---------- | ----------------- | ------------------ | ---------------------------- |
| Go         | GitHub (git tags) | -                  | `github.com/org/repo/gen/go` |
| Python     | PyPI              | GitHub Packages    | `org-repo-proto`             |
| TypeScript | npm               | GitHub Packages    | `@org/repo-proto`            |
| Rust       | crates.io         | GitHub Container   | `org-repo-proto`             |

### Version Synchronization

**Problem:** Keep protobuf schema versions in sync with generated SDKs

**Solution:** Use git tags with language-specific prefixes

```
Tag Pattern: {language}-v{version}

Examples:
- proto-v1.2.3        # Buf BSR tag
- go-v1.2.3           # Go module tag
- python-v1.2.3       # Python package tag
- typescript-v1.2.3   # npm package tag
- rust-v1.2.3         # Rust crate tag
```

**Workflow Trigger:**

```yaml
on:
  push:
    tags:
      - 'proto-v*' # Trigger on protobuf version tags
```

### Semantic Versioning for Protobuf

**Patch (x.y.Z):**

- Documentation changes
- New optional fields
- New RPC methods (backward compatible)

**Minor (x.Y.z):**

- New message types
- New service definitions
- New enum values (backward compatible)

**Major (X.y.z):**

- Removed fields
- Changed field types
- Removed RPCs
- Renamed messages/services

## Sample Protobuf Structure

### proto/v1/api.proto

```protobuf
// file: proto/v1/api.proto
// version: 1.0.0
// guid: proto-api-v1-a1b2c3d4-e5f6

syntax = "proto3";

package ghcommon.v1;

option go_package = "github.com/jdfalk/ghcommon/gen/go/ghcommon/v1;ghcommonv1";

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

// User represents a system user
message User {
  // Unique user identifier
  string id = 1;

  // User's email address
  string email = 2;

  // User's display name
  string name = 3;

  // Account creation timestamp
  google.protobuf.Timestamp created_at = 4;

  // Account last updated timestamp
  google.protobuf.Timestamp updated_at = 5;
}

// UserService manages user operations
service UserService {
  // GetUser retrieves a user by ID
  rpc GetUser(GetUserRequest) returns (User) {}

  // ListUsers retrieves all users with pagination
  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse) {}

  // CreateUser creates a new user
  rpc CreateUser(CreateUserRequest) returns (User) {}

  // UpdateUser updates an existing user
  rpc UpdateUser(UpdateUserRequest) returns (User) {}

  // DeleteUser removes a user
  rpc DeleteUser(DeleteUserRequest) returns (google.protobuf.Empty) {}
}

// GetUserRequest is the request for GetUser
message GetUserRequest {
  // User ID to retrieve
  string id = 1;
}

// ListUsersRequest is the request for ListUsers
message ListUsersRequest {
  // Page number (1-based)
  int32 page = 1;

  // Items per page
  int32 page_size = 2;
}

// ListUsersResponse is the response for ListUsers
message ListUsersResponse {
  // List of users
  repeated User users = 1;

  // Total number of users
  int32 total = 2;

  // Current page number
  int32 page = 3;

  // Items per page
  int32 page_size = 4;
}

// CreateUserRequest is the request for CreateUser
message CreateUserRequest {
  // User email address
  string email = 1;

  // User display name
  string name = 2;
}

// UpdateUserRequest is the request for UpdateUser
message UpdateUserRequest {
  // User ID to update
  string id = 1;

  // New email address (optional)
  optional string email = 2;

  // New display name (optional)
  optional string name = 3;
}

// DeleteUserRequest is the request for DeleteUser
message DeleteUserRequest {
  // User ID to delete
  string id = 1;
}
```

## Local Testing Setup

### Install Buf CLI

```bash
# macOS
brew install bufbuild/buf/buf

# Linux
curl -sSL \
  "https://github.com/bufbuild/buf/releases/latest/download/buf-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/buf
chmod +x /usr/local/bin/buf

# Verify installation
buf --version
```

### Initialize Buf Configuration

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Create proto directory structure
mkdir -p proto/v1

# Copy example proto file
cat > proto/v1/api.proto << 'EOF'
syntax = "proto3";
package ghcommon.v1;
option go_package = "github.com/jdfalk/ghcommon/gen/go/ghcommon/v1;ghcommonv1";

message Hello {
  string message = 1;
}
EOF

# Initialize buf.yaml
buf config init

# Update buf.yaml with BSR name
cat > buf.yaml << 'EOF'
version: v2
modules:
  - path: proto
    name: buf.build/jdfalk/ghcommon
lint:
  use:
    - DEFAULT
breaking:
  use:
    - FILE
EOF

# Create buf.gen.yaml
cat > buf.gen.yaml << 'EOF'
version: v2
plugins:
  - remote: buf.build/protocolbuffers/go
    out: gen/go
    opt:
      - paths=source_relative
EOF
```

### Test Buf Commands Locally

```bash
# Lint protobuf files
buf lint

# Check for breaking changes (requires previous commit)
buf breaking --against '.git#branch=main'

# Generate code
buf generate

# Format protobuf files
buf format -w

# List all messages
buf ls-files
```

### Test BSR Authentication

```bash
# Login to Buf (requires BUF_TOKEN)
echo $BUF_TOKEN | buf registry login buf.build --username jdfalk --token-stdin

# Verify authentication
buf registry whoami

# Logout
buf registry logout buf.build
```

## Expected Artifacts

After successful execution, you should have:

1. **Buf Schema Registry:**
   - Published schemas at `buf.build/jdfalk/ghcommon`
   - Tagged with `proto-v{version}`
   - Breaking change report

2. **Go Module:**
   - Published via git tag `go-v{version}`
   - Importable as `github.com/jdfalk/ghcommon/gen/go`

3. **Python Package:**
   - Published to PyPI as `jdfalk-ghcommon-proto`
   - Published to GitHub Packages
   - Version `{version}`

4. **TypeScript Package:**
   - Published to npm as `@jdfalk/ghcommon-proto`
   - Published to GitHub Packages
   - Version `{version}`

5. **Rust Crate:**
   - Published to crates.io as `jdfalk-ghcommon-proto`
   - Version `{version}`

6. **GitHub Release:**
   - Tag `proto-v{version}`
   - Attached artifacts (all generated SDKs)
   - Auto-generated changelog

## Success Criteria

- [ ] Buf linting passes with no errors
- [ ] No breaking changes detected (or documented)
- [ ] Schemas published to BSR successfully
- [ ] Go module tagged and importable
- [ ] Python package published to PyPI
- [ ] TypeScript package published to npm
- [ ] Rust crate published to crates.io
- [ ] GitHub release created with artifacts
- [ ] All SDKs installable in their respective ecosystems
- [ ] API documentation generated

## Next Steps

**Continue to Part 2:** Workflow setup, protobuf detection, and Buf validation.
