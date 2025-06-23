# Protocol Buffers Style Guide - Edition 2023

## Overview

This style guide defines standards for Protocol Buffers in the GCommon project, focusing on Edition 2023 features with hybrid API support. We're transitioning from syntax-based protobuf to edition-based protobuf for better future-proofing and enhanced features.

## Table of Contents

- [Edition 2023 Features](#edition-2023-features)
- [File Structure](#file-structure)
- [Naming Conventions](#naming-conventions)
- [Message Design](#message-design)
- [Service Design](#service-design)
- [Field Guidelines](#field-guidelines)
- [Common Types](#common-types)
- [Hybrid API Support](#hybrid-api-support)
- [Code Generation](#code-generation)
- [Documentation](#documentation)
- [Examples](#examples)

## Edition 2023 Features

### Edition Declaration

All proto files MUST use Edition 2023:

```protobuf
edition = "2023";
```

### Key Edition 2023 Benefits

- **Enhanced Features**: Improved field features and validation
- **Better Defaults**: More sensible default behaviors
- **Future-Proof**: Designed for long-term evolution
- **Hybrid APIs**: Support for both REST and gRPC APIs
- **Improved Validation**: Built-in field validation capabilities

## File Structure

### File Organization

```text
pkg/
├── common/proto/           # Shared common types
├── auth/proto/            # Authentication service protos
├── cache/proto/           # Cache service protos
├── config/proto/          # Configuration service protos
├── db/proto/              # Database service protos
├── health/proto/          # Health check service protos
├── log/proto/             # Logging service protos
├── metrics/proto/         # Metrics service protos
├── queue/proto/           # Queue service protos
└── web/proto/             # Web service protos
```

### File Header Template

```protobuf
edition = "2023";

// Package documentation describing the service purpose
package gcommon.v1.service_name;

option go_package = "github.com/jdfalk/gcommon/pkg/service_name/proto";

// Standard imports for common types
import "pkg/common/proto/common.proto";
import "google/api/annotations.proto";
import "google/protobuf/timestamp.proto";
import "validate/validate.proto";
```

## Naming Conventions

### Packages

- Use `gcommon.v1.service_name` format
- Use lowercase with underscores for multi-word names
- Include version in package name for API evolution

### Messages

- Use PascalCase: `UserAccount`, `OrderStatus`
- Use descriptive, unambiguous names
- Avoid abbreviations unless widely understood

### Fields

- Use snake_case: `user_id`, `created_at`, `is_active`
- Use descriptive names that indicate purpose
- Boolean fields should start with `is_`, `has_`, `can_`, `should_`

### Services

- Use PascalCase with "Service" suffix: `AuthService`, `CacheService`
- Use descriptive service names that indicate domain

### RPCs

- Use PascalCase verbs: `GetUser`, `CreateOrder`, `ListItems`
- Follow REST-like patterns: `Get`, `List`, `Create`, `Update`, `Delete`

### Enums

- Use PascalCase for enum names: `UserStatus`, `OrderType`
- Use SCREAMING_SNAKE_CASE for values: `USER_STATUS_ACTIVE`, `ORDER_TYPE_RETAIL`
- Include enum name prefix in values to avoid conflicts

## Message Design

### Request/Response Patterns

```protobuf
// Standard request pattern
message GetUserRequest {
  string user_id = 1 [(validate.rules).string.min_len = 1];

  // Optional fields for additional context
  repeated string fields = 2;  // Field selection
  gcommon.v1.common.AuditLog audit = 3;
}

// Standard response pattern
message GetUserResponse {
  User user = 1;
  gcommon.v1.common.AuditLog audit = 2;
}

// List pattern with pagination
message ListUsersRequest {
  int32 page_size = 1 [(validate.rules).int32 = {gte: 1, lte: 1000}];
  string page_token = 2;
  string filter = 3;  // Filter expression
  string order_by = 4;  // Sort order
}

message ListUsersResponse {
  repeated User users = 1;
  string next_page_token = 2;
  int32 total_count = 3;
}
```

### Common Message Patterns

```protobuf
// Use common types from gcommon.v1.common
message UserAccount {
  string id = 1 [(validate.rules).string.uuid = true];
  string name = 2 [(validate.rules).string.min_len = 1];
  string email = 3 [(validate.rules).string.email = true];

  // Use common timestamp pattern
  google.protobuf.Timestamp created_at = 4;
  google.protobuf.Timestamp updated_at = 5;

  // Use common retry policy
  gcommon.v1.common.RetryPolicy retry_policy = 6;

  // Use common audit logging
  gcommon.v1.common.AuditLog audit = 7;
}
```

## Service Design

### Service Definition Pattern

```protobuf
service AuthService {
  // Authentication operations
  rpc Login(LoginRequest) returns (LoginResponse) {
    option (google.api.http) = {
      post: "/v1/auth/login"
      body: "*"
    };
  }

  rpc Logout(LogoutRequest) returns (LogoutResponse) {
    option (google.api.http) = {
      post: "/v1/auth/logout"
      body: "*"
    };
  }

  // User management operations
  rpc GetUser(GetUserRequest) returns (GetUserResponse) {
    option (google.api.http) = {
      get: "/v1/users/{user_id}"
    };
  }

  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse) {
    option (google.api.http) = {
      get: "/v1/users"
    };
  }

  rpc CreateUser(CreateUserRequest) returns (CreateUserResponse) {
    option (google.api.http) = {
      post: "/v1/users"
      body: "*"
    };
  }

  rpc UpdateUser(UpdateUserRequest) returns (UpdateUserResponse) {
    option (google.api.http) = {
      patch: "/v1/users/{user.id}"
      body: "user"
    };
  }

  rpc DeleteUser(DeleteUserRequest) returns (DeleteUserResponse) {
    option (google.api.http) = {
      delete: "/v1/users/{user_id}"
    };
  }
}
```

## Field Guidelines

### Field Numbers

- Use 1-15 for frequently used fields (single byte encoding)
- Reserve 16-2047 for less frequent fields
- Never reuse field numbers
- Reserve field numbers for future use when removing fields

### Field Types

```protobuf
message FieldExamples {
  // Identifiers - use string for UUIDs, int64 for auto-increment
  string uuid_id = 1 [(validate.rules).string.uuid = true];
  int64 sequence_id = 2 [(validate.rules).int64.gte = 0];

  // Strings with validation
  string email = 3 [(validate.rules).string.email = true];
  string name = 4 [(validate.rules).string = {min_len: 1, max_len: 255}];
  string url = 5 [(validate.rules).string.uri = true];

  // Numbers with constraints
  int32 count = 6 [(validate.rules).int32 = {gte: 0}];
  double percentage = 7 [(validate.rules).double = {gte: 0.0, lte: 100.0}];

  // Timestamps
  google.protobuf.Timestamp created_at = 8;

  // Enums
  Status status = 9 [(validate.rules).enum.defined_only = true];

  // Repeated fields
  repeated string tags = 10 [(validate.rules).repeated.max_items = 50];

  // Maps
  map<string, string> metadata = 11 [(validate.rules).map.max_pairs = 100];
}
```

### Validation Rules

Use protoc-gen-validate for field validation:

```protobuf
message ValidationExamples {
  // String validation
  string username = 1 [(validate.rules).string = {
    pattern: "^[a-zA-Z0-9_]+$",
    min_len: 3,
    max_len: 50
  }];

  // Numeric validation
  int32 port = 2 [(validate.rules).int32 = {gte: 1, lte: 65535}];

  // Collection validation
  repeated string items = 3 [(validate.rules).repeated = {
    min_items: 1,
    max_items: 100,
    unique: true
  }];

  // Custom validation
  string custom_field = 4 [(validate.rules).string.pattern = "^CUSTOM_.*"];
}
```

## Common Types

### Use Shared Common Types

Import and use types from `pkg/common/proto/common.proto`:

```protobuf
import "pkg/common/proto/common.proto";

message ServiceRequest {
  // Use common audit logging
  gcommon.v1.common.AuditLog audit = 1;

  // Use common retry policy
  gcommon.v1.common.RetryPolicy retry_policy = 2;

  // Use common cache policy
  gcommon.v1.common.CachePolicy cache_policy = 3;

  // Use common circuit breaker config
  gcommon.v1.common.CircuitBreakerConfig circuit_breaker = 4;

  // Use common batch operation
  gcommon.v1.common.BatchOperation batch_config = 5;

  // Use common subscription info
  gcommon.v1.common.SubscriptionInfo subscription = 6;
}
```

## Hybrid API Support

### REST and gRPC Annotations

All services MUST support both REST and gRPC:

```protobuf
import "google/api/annotations.proto";

service ExampleService {
  rpc GetResource(GetResourceRequest) returns (GetResourceResponse) {
    option (google.api.http) = {
      get: "/v1/resources/{resource_id}"
    };
  }

  rpc CreateResource(CreateResourceRequest) returns (CreateResourceResponse) {
    option (google.api.http) = {
      post: "/v1/resources"
      body: "*"
    };
  }

  rpc UpdateResource(UpdateResourceRequest) returns (UpdateResourceResponse) {
    option (google.api.http) = {
      patch: "/v1/resources/{resource.id}"
      body: "resource"
    };
  }

  rpc DeleteResource(DeleteResourceRequest) returns (DeleteResourceResponse) {
    option (google.api.http) = {
      delete: "/v1/resources/{resource_id}"
    };
  }

  rpc ListResources(ListResourcesRequest) returns (ListResourcesResponse) {
    option (google.api.http) = {
      get: "/v1/resources"
    };
  }
}
```

### URL Path Conventions

- Use RESTful URL patterns: `/v1/resources/{id}`
- Use kebab-case for multi-word resources: `/v1/user-accounts/{id}`
- Include version in path: `/v1/`, `/v2/`
- Use standard HTTP methods: GET, POST, PUT, PATCH, DELETE

## Code Generation

### Go Package Options

```protobuf
option go_package = "github.com/jdfalk/gcommon/pkg/service_name/proto";
```

### Generated Code Organization

```text
pkg/service_name/proto/
├── service.pb.go           # Generated message types
├── service_grpc.pb.go      # Generated gRPC service
├── service.pb.gw.go        # Generated REST gateway
└── service.pb.validate.go  # Generated validation
```

## Documentation

### Message Documentation

```protobuf
// UserAccount represents a user account in the system.
// This message contains all the essential information about a user
// including their profile data, authentication details, and audit trail.
message UserAccount {
  // Unique identifier for the user account.
  // Must be a valid UUID v4 format.
  string id = 1 [(validate.rules).string.uuid = true];

  // Display name for the user.
  // Must be between 1 and 255 characters.
  string name = 2 [(validate.rules).string = {min_len: 1, max_len: 255}];

  // Email address for the user.
  // Must be a valid email format and unique across the system.
  string email = 3 [(validate.rules).string.email = true];
}
```

### Service Documentation

```protobuf
// AuthService provides authentication and user management capabilities.
// This service handles user login, logout, registration, and profile management.
// It supports both gRPC and REST APIs for maximum flexibility.
service AuthService {
  // Login authenticates a user with email and password.
  // Returns authentication tokens on successful login.
  rpc Login(LoginRequest) returns (LoginResponse);

  // GetUser retrieves user account information by user ID.
  // Requires valid authentication token.
  rpc GetUser(GetUserRequest) returns (GetUserResponse);
}
```

## Examples

### Complete Service Example

```protobuf
edition = "2023";

// Cache service provides distributed caching capabilities
package gcommon.v1.cache;

option go_package = "github.com/jdfalk/gcommon/pkg/cache/proto";

import "pkg/common/proto/common.proto";
import "google/api/annotations.proto";
import "google/protobuf/duration.proto";
import "google/protobuf/timestamp.proto";
import "validate/validate.proto";

// CacheService provides distributed caching operations
service CacheService {
  // Get retrieves a value from cache by key
  rpc Get(GetRequest) returns (GetResponse) {
    option (google.api.http) = {
      get: "/v1/cache/{key}"
    };
  }

  // Set stores a value in cache with optional TTL
  rpc Set(SetRequest) returns (SetResponse) {
    option (google.api.http) = {
      put: "/v1/cache/{key}"
      body: "*"
    };
  }

  // Delete removes a value from cache
  rpc Delete(DeleteRequest) returns (DeleteResponse) {
    option (google.api.http) = {
      delete: "/v1/cache/{key}"
    };
  }
}

// GetRequest requests a cache value by key
message GetRequest {
  // Cache key to retrieve
  string key = 1 [(validate.rules).string.min_len = 1];

  // Optional cache policy override
  gcommon.v1.common.CachePolicy cache_policy = 2;

  // Audit information
  gcommon.v1.common.AuditLog audit = 3;
}

// GetResponse returns cache value and metadata
message GetResponse {
  // Cache value (empty if not found)
  bytes value = 1;

  // Whether the key was found
  bool found = 2;

  // When the value expires
  google.protobuf.Timestamp expires_at = 3;

  // Audit information
  gcommon.v1.common.AuditLog audit = 4;
}

// SetRequest stores a value in cache
message SetRequest {
  // Cache key
  string key = 1 [(validate.rules).string.min_len = 1];

  // Value to store
  bytes value = 2;

  // Time-to-live for the entry
  google.protobuf.Duration ttl = 3 [(validate.rules).duration.gte.seconds = 1];

  // Cache policy
  gcommon.v1.common.CachePolicy cache_policy = 4;

  // Audit information
  gcommon.v1.common.AuditLog audit = 5;
}

// SetResponse confirms cache storage
message SetResponse {
  // Whether the operation succeeded
  bool success = 1;

  // When the value will expire
  google.protobuf.Timestamp expires_at = 2;

  // Audit information
  gcommon.v1.common.AuditLog audit = 3;
}

// DeleteRequest removes a cache entry
message DeleteRequest {
  // Cache key to delete
  string key = 1 [(validate.rules).string.min_len = 1];

  // Audit information
  gcommon.v1.common.AuditLog audit = 2;
}

// DeleteResponse confirms cache deletion
message DeleteResponse {
  // Whether the key was found and deleted
  bool deleted = 1;

  // Audit information
  gcommon.v1.common.AuditLog audit = 2;
}
```

## Best Practices Summary

1. **Always use Edition 2023** for new proto files
2. **Include comprehensive validation** using protoc-gen-validate
3. **Support both REST and gRPC** with proper HTTP annotations
4. **Use common types** from `pkg/common/proto/common.proto`
5. **Follow consistent naming** conventions across all services
6. **Document everything** with clear, comprehensive comments
7. **Use semantic versioning** in package names for API evolution
8. **Validate all inputs** with appropriate constraints
9. **Include audit trails** in all service operations
10. **Design for extensibility** with reserved field numbers

This style guide ensures consistency, maintainability, and future-proofing across all Protocol Buffer definitions in the GCommon project.

## Message Design

### Request/Response Patterns

```protobuf
// Standard request pattern
message GetUserRequest {
  string user_id = 1 [(validate.rules).string.min_len = 1];

  // Optional fields for additional context
  repeated string fields = 2;  // Field selection
  gcommon.v1.common.AuditLog audit = 3;
}

// Standard response pattern
message GetUserResponse {
  User user = 1;
  gcommon.v1.common.AuditLog audit = 2;
}

// List pattern with pagination
message ListUsersRequest {
  int32 page_size = 1 [(validate.rules).int32 = {gte: 1, lte: 1000}];
  string page_token = 2;
  string filter = 3;  // Filter expression
  string order_by = 4;  // Sort order
}

message ListUsersResponse {
  repeated User users = 1;
  string next_page_token = 2;
  int32 total_count = 3;
}
```

### Common Message Patterns

```protobuf
// Use common types from gcommon.v1.common
message UserAccount {
  string id = 1 [(validate.rules).string.uuid = true];
  string name = 2 [(validate.rules).string.min_len = 1];
  string email = 3 [(validate.rules).string.email = true];

  // Use common timestamp pattern
  google.protobuf.Timestamp created_at = 4;
  google.protobuf.Timestamp updated_at = 5;

  // Use common retry policy
  gcommon.v1.common.RetryPolicy retry_policy = 6;

  // Use common audit logging
  gcommon.v1.common.AuditLog audit = 7;
}
```

## Service Design

### Service Definition Pattern

```protobuf
service AuthService {
  // Authentication operations
  rpc Login(LoginRequest) returns (LoginResponse) {
    option (google.api.http) = {
      post: "/v1/auth/login"
      body: "*"
    };
  }

  rpc Logout(LogoutRequest) returns (LogoutResponse) {
    option (google.api.http) = {
      post: "/v1/auth/logout"
      body: "*"
    };
  }

  // User management operations
  rpc GetUser(GetUserRequest) returns (GetUserResponse) {
    option (google.api.http) = {
      get: "/v1/users/{user_id}"
    };
  }

  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse) {
    option (google.api.http) = {
      get: "/v1/users"
    };
  }

  rpc CreateUser(CreateUserRequest) returns (CreateUserResponse) {
    option (google.api.http) = {
      post: "/v1/users"
      body: "*"
    };
  }

  rpc UpdateUser(UpdateUserRequest) returns (UpdateUserResponse) {
    option (google.api.http) = {
      patch: "/v1/users/{user.id}"
      body: "user"
    };
  }

  rpc DeleteUser(DeleteUserRequest) returns (DeleteUserResponse) {
    option (google.api.http) = {
      delete: "/v1/users/{user_id}"
    };
  }
}
```

## Field Guidelines

### Field Numbers

- Use 1-15 for frequently used fields (single byte encoding)
- Reserve 16-2047 for less frequent fields
- Never reuse field numbers
- Reserve field numbers for future use when removing fields

### Field Types

```protobuf
message FieldExamples {
  // Identifiers - use string for UUIDs, int64 for auto-increment
  string uuid_id = 1 [(validate.rules).string.uuid = true];
  int64 sequence_id = 2 [(validate.rules).int64.gte = 0];

  // Strings with validation
  string email = 3 [(validate.rules).string.email = true];
  string name = 4 [(validate.rules).string = {min_len: 1, max_len: 255}];
  string url = 5 [(validate.rules).string.uri = true];

  // Numbers with constraints
  int32 count = 6 [(validate.rules).int32 = {gte: 0}];
  double percentage = 7 [(validate.rules).double = {gte: 0.0, lte: 100.0}];

  // Timestamps
  google.protobuf.Timestamp created_at = 8;

  // Enums
  Status status = 9 [(validate.rules).enum.defined_only = true];

  // Repeated fields
  repeated string tags = 10 [(validate.rules).repeated.max_items = 50];

  // Maps
  map<string, string> metadata = 11 [(validate.rules).map.max_pairs = 100];
}
```

### Validation Rules

Use protoc-gen-validate for field validation:

```protobuf
message ValidationExamples {
  // String validation
  string username = 1 [(validate.rules).string = {
    pattern: "^[a-zA-Z0-9_]+$",
    min_len: 3,
    max_len: 50
  }];

  // Numeric validation
  int32 port = 2 [(validate.rules).int32 = {gte: 1, lte: 65535}];

  // Collection validation
  repeated string items = 3 [(validate.rules).repeated = {
    min_items: 1,
    max_items: 100,
    unique: true
  }];

  // Custom validation
  string custom_field = 4 [(validate.rules).string.pattern = "^CUSTOM_.*"];
}
```

## Common Types

### Use Shared Common Types

Import and use types from `pkg/common/proto/common.proto`:

```protobuf
import "pkg/common/proto/common.proto";

message ServiceRequest {
  // Use common audit logging
  gcommon.v1.common.AuditLog audit = 1;

  // Use common retry policy
  gcommon.v1.common.RetryPolicy retry_policy = 2;

  // Use common cache policy
  gcommon.v1.common.CachePolicy cache_policy = 3;

  // Use common circuit breaker config
  gcommon.v1.common.CircuitBreakerConfig circuit_breaker = 4;

  // Use common batch operation
  gcommon.v1.common.BatchOperation batch_config = 5;

  // Use common subscription info
  gcommon.v1.common.SubscriptionInfo subscription = 6;
}
```

## Hybrid API Support

### REST and gRPC Annotations

All services MUST support both REST and gRPC:

```protobuf
import "google/api/annotations.proto";

service ExampleService {
  rpc GetResource(GetResourceRequest) returns (GetResourceResponse) {
    option (google.api.http) = {
      get: "/v1/resources/{resource_id}"
    };
  }

  rpc CreateResource(CreateResourceRequest) returns (CreateResourceResponse) {
    option (google.api.http) = {
      post: "/v1/resources"
      body: "*"
    };
  }

  rpc UpdateResource(UpdateResourceRequest) returns (UpdateResourceResponse) {
    option (google.api.http) = {
      patch: "/v1/resources/{resource.id}"
      body: "resource"
    };
  }

  rpc DeleteResource(DeleteResourceRequest) returns (DeleteResourceResponse) {
    option (google.api.http) = {
      delete: "/v1/resources/{resource_id}"
    };
  }

  rpc ListResources(ListResourcesRequest) returns (ListResourcesResponse) {
    option (google.api.http) = {
      get: "/v1/resources"
    };
  }
}
```

### URL Path Conventions

- Use RESTful URL patterns: `/v1/resources/{id}`
- Use kebab-case for multi-word resources: `/v1/user-accounts/{id}`
- Include version in path: `/v1/`, `/v2/`
- Use standard HTTP methods: GET, POST, PUT, PATCH, DELETE

## Code Generation

### Go Package Options

```protobuf
option go_package = "github.com/jdfalk/gcommon/pkg/service_name/proto";
```

### Generated Code Organization

```
pkg/service_name/proto/
├── service.pb.go           # Generated message types
├── service_grpc.pb.go      # Generated gRPC service
├── service.pb.gw.go        # Generated REST gateway
└── service.pb.validate.go  # Generated validation
```

## Documentation

### Message Documentation

```protobuf
// UserAccount represents a user account in the system.
// This message contains all the essential information about a user
// including their profile data, authentication details, and audit trail.
message UserAccount {
  // Unique identifier for the user account.
  // Must be a valid UUID v4 format.
  string id = 1 [(validate.rules).string.uuid = true];

  // Display name for the user.
  // Must be between 1 and 255 characters.
  string name = 2 [(validate.rules).string = {min_len: 1, max_len: 255}];

  // Email address for the user.
  // Must be a valid email format and unique across the system.
  string email = 3 [(validate.rules).string.email = true];
}
```

### Service Documentation

```protobuf
// AuthService provides authentication and user management capabilities.
// This service handles user login, logout, registration, and profile management.
// It supports both gRPC and REST APIs for maximum flexibility.
service AuthService {
  // Login authenticates a user with email and password.
  // Returns authentication tokens on successful login.
  rpc Login(LoginRequest) returns (LoginResponse);

  // GetUser retrieves user account information by user ID.
  // Requires valid authentication token.
  rpc GetUser(GetUserRequest) returns (GetUserResponse);
}
```

## Examples

### Complete Service Example

```protobuf
edition = "2023";

// Cache service provides distributed caching capabilities
package gcommon.v1.cache;

option go_package = "github.com/jdfalk/gcommon/pkg/cache/proto";

import "pkg/common/proto/common.proto";
import "google/api/annotations.proto";
import "google/protobuf/duration.proto";
import "google/protobuf/timestamp.proto";
import "validate/validate.proto";

// CacheService provides distributed caching operations
service CacheService {
  // Get retrieves a value from cache by key
  rpc Get(GetRequest) returns (GetResponse) {
    option (google.api.http) = {
      get: "/v1/cache/{key}"
    };
  }

  // Set stores a value in cache with optional TTL
  rpc Set(SetRequest) returns (SetResponse) {
    option (google.api.http) = {
      put: "/v1/cache/{key}"
      body: "*"
    };
  }

  // Delete removes a value from cache
  rpc Delete(DeleteRequest) returns (DeleteResponse) {
    option (google.api.http) = {
      delete: "/v1/cache/{key}"
    };
  }
}

// GetRequest requests a cache value by key
message GetRequest {
  // Cache key to retrieve
  string key = 1 [(validate.rules).string.min_len = 1];

  // Optional cache policy override
  gcommon.v1.common.CachePolicy cache_policy = 2;

  // Audit information
  gcommon.v1.common.AuditLog audit = 3;
}

// GetResponse returns cache value and metadata
message GetResponse {
  // Cache value (empty if not found)
  bytes value = 1;

  // Whether the key was found
  bool found = 2;

  // When the value expires
  google.protobuf.Timestamp expires_at = 3;

  // Audit information
  gcommon.v1.common.AuditLog audit = 4;
}

// SetRequest stores a value in cache
message SetRequest {
  // Cache key
  string key = 1 [(validate.rules).string.min_len = 1];

  // Value to store
  bytes value = 2;

  // Time-to-live for the entry
  google.protobuf.Duration ttl = 3 [(validate.rules).duration.gte.seconds = 1];

  // Cache policy
  gcommon.v1.common.CachePolicy cache_policy = 4;

  // Audit information
  gcommon.v1.common.AuditLog audit = 5;
}

// SetResponse confirms cache storage
message SetResponse {
  // Whether the operation succeeded
  bool success = 1;

  // When the value will expire
  google.protobuf.Timestamp expires_at = 2;

  // Audit information
  gcommon.v1.common.AuditLog audit = 3;
}

// DeleteRequest removes a cache entry
message DeleteRequest {
  // Cache key to delete
  string key = 1 [(validate.rules).string.min_len = 1];

  // Audit information
  gcommon.v1.common.AuditLog audit = 2;
}

// DeleteResponse confirms cache deletion
message DeleteResponse {
  // Whether the key was found and deleted
  bool deleted = 1;

  // Audit information
  gcommon.v1.common.AuditLog audit = 2;
}
```

## Best Practices Summary

1. **Always use Edition 2023** for new proto files
2. **Include comprehensive validation** using protoc-gen-validate
3. **Support both REST and gRPC** with proper HTTP annotations
4. **Use common types** from `pkg/common/proto/common.proto`
5. **Follow consistent naming** conventions across all services
6. **Document everything** with clear, comprehensive comments
7. **Use semantic versioning** in package names for API evolution
8. **Validate all inputs** with appropriate constraints
9. **Include audit trails** in all service operations
10. **Design for extensibility** with reserved field numbers

This style guide ensures consistency, maintainability, and future-proofing across all Protocol Buffer definitions in the GCommon project.
