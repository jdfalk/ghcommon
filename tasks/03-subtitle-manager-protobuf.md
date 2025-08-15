# Task 3: Subtitle Manager Protobuf Implementation

<!-- file: tasks/03-subtitle-manager-protobuf.md -->
<!-- version: 1.0.0 -->
<!-- guid: 34567890-3456-3456-3456-345678901def -->

## Overview

Implement comprehensive protobuf definitions for subtitle-manager, integrate with gcommon protobuf ecosystem, and create a fully functional subtitle processing system with gRPC services.

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

Follow all instructions from:

- [General coding instructions](../.github/instructions/general-coding.instructions.md)
- [Go instructions](../.github/instructions/go.instructions.md)
- [Protobuf instructions](../.github/instructions/protobuf.instructions.md)
- [Rust utility instructions](../.github/instructions/rust-utility.instructions.md)

Download copilot-agent-util from: https://github.com/jdfalk/copilot-agent-util-rust

## Subtitle Manager Architecture Plan

### Core Components

1. **Subtitle Processing Engine**
   - Parse various subtitle formats (SRT, VTT, ASS, etc.)
   - Convert between formats
   - Validate subtitle timing and content
   - Apply transformations and corrections

2. **Storage Management**
   - File system operations for subtitle files
   - Metadata storage and indexing
   - Backup and versioning
   - Cache management

3. **API Services**
   - gRPC services for subtitle operations
   - RESTful API gateway
   - Streaming support for large files
   - Batch processing capabilities

4. **Integration Layer**
   - gcommon protobuf integration
   - Shared authentication and authorization
   - Common logging and metrics
   - Configuration management

### Protobuf Design

Following the 1-1-1 design pattern, we need these proto definitions:

## Task Breakdown

### Task 3.1: Core Subtitle Message Types

**File:** `tasks/03.1-subtitle-core-messages.md`

Create fundamental message types for subtitle processing:

- `SubtitleRecord` - Individual subtitle entry with timing and text
- `SubtitleFile` - Complete subtitle file with metadata
- `SubtitleFormat` - Enum for supported formats
- `SubtitleMetadata` - File properties and processing info
- `TimingInfo` - Start/end times with validation
- `SubtitleContent` - Text content with styling information

### Task 3.2: Subtitle Processing Service

**File:** `tasks/03.2-subtitle-processing-service.md`

Implement subtitle processing operations:

- `SubtitleProcessingService` - Main gRPC service
- `ParseSubtitleRequest/Response` - Parse subtitle files
- `ConvertFormatRequest/Response` - Format conversion
- `ValidateSubtitleRequest/Response` - Timing and content validation
- `ApplyTransformRequest/Response` - Apply corrections and changes

### Task 3.3: Storage and Management Service

**File:** `tasks/03.3-subtitle-storage-service.md`

Handle subtitle file storage and management:

- `SubtitleStorageService` - File management gRPC service
- `StoreSubtitleRequest/Response` - Save subtitle files
- `RetrieveSubtitleRequest/Response` - Load subtitle files
- `SearchSubtitleRequest/Response` - Find subtitles by criteria
- `ListSubtitleRequest/Response` - Browse available subtitles

### Task 3.4: Integration with gcommon

**File:** `tasks/03.4-gcommon-integration.md`

Integrate with existing gcommon protobuf ecosystem:

- Use gcommon auth types for authentication
- Integrate with gcommon logging and metrics
- Use shared error handling patterns
- Implement consistent API patterns

### Task 3.5: Service Implementation

**File:** `tasks/03.5-service-implementation.md`

Implement the actual Go services:

- gRPC server setup with proper middleware
- Service method implementations
- Error handling and validation
- Testing and integration tests

### Task 3.6: API Gateway and REST Interface

**File:** `tasks/03.6-api-gateway.md`

Create REST API gateway for subtitle services:

- HTTP to gRPC translation
- OpenAPI documentation
- Authentication middleware
- Rate limiting and monitoring

## Detailed Protobuf Specifications

### Subtitle Core Types

```protobuf
// SubtitleRecord represents a single subtitle entry
message SubtitleRecord {
  int32 sequence = 1;
  TimingInfo timing = 2;
  SubtitleContent content = 3;
  map<string, string> metadata = 4;
}

// SubtitleFile represents a complete subtitle file
message SubtitleFile {
  SubtitleMetadata metadata = 1;
  repeated SubtitleRecord records = 2;
  SubtitleFormat format = 3;
  bytes raw_content = 4;
}

// TimingInfo represents subtitle timing
message TimingInfo {
  int64 start_time_ms = 1;
  int64 end_time_ms = 2;
  int64 duration_ms = 3;
}

// SubtitleContent represents text content with styling
message SubtitleContent {
  string text = 1;
  SubtitleStyling styling = 2;
  repeated string lines = 3;
}
```

### Service Definitions

```protobuf
// Main subtitle processing service
service SubtitleProcessingService {
  rpc ParseSubtitle(ParseSubtitleRequest) returns (ParseSubtitleResponse);
  rpc ConvertFormat(ConvertFormatRequest) returns (ConvertFormatResponse);
  rpc ValidateSubtitle(ValidateSubtitleRequest) returns (ValidateSubtitleResponse);
  rpc ApplyTransformation(ApplyTransformRequest) returns (ApplyTransformResponse);
  rpc BatchProcess(BatchProcessRequest) returns (stream BatchProcessResponse);
}

// Subtitle storage and management service
service SubtitleStorageService {
  rpc StoreSubtitle(StoreSubtitleRequest) returns (StoreSubtitleResponse);
  rpc RetrieveSubtitle(RetrieveSubtitleRequest) returns (RetrieveSubtitleResponse);
  rpc SearchSubtitles(SearchSubtitleRequest) returns (SearchSubtitleResponse);
  rpc ListSubtitles(ListSubtitleRequest) returns (ListSubtitleResponse);
  rpc DeleteSubtitle(DeleteSubtitleRequest) returns (DeleteSubtitleResponse);
}
```

### Integration Points

1. **Authentication:** Use `gcommon/auth` protobuf types
2. **Logging:** Integrate with `gcommon/logging` types
3. **Metrics:** Use `gcommon/metrics` for monitoring
4. **Errors:** Follow `gcommon/errors` patterns
5. **Configuration:** Use `gcommon/config` types

## Implementation Requirements

### Phase 1: Protobuf Definitions (Tasks 3.1-3.4)

- Create all proto files following 1-1-1 pattern
- Use Edition 2023 for all proto files
- Implement proper module prefixes (`Subtitle` prefix)
- Generate Go code and verify imports
- Test protobuf serialization/deserialization

### Phase 2: Service Implementation (Task 3.5)

- Implement gRPC services in Go
- Add proper middleware (auth, logging, metrics)
- Create comprehensive unit tests
- Add integration tests with sample data
- Implement proper error handling

### Phase 3: API Gateway (Task 3.6)

- Create REST API gateway using grpc-gateway
- Generate OpenAPI documentation
- Add HTTP middleware for auth and logging
- Implement request/response validation
- Add rate limiting and monitoring

### Phase 4: Integration Testing

- Test with real subtitle files
- Performance testing with large files
- End-to-end testing of complete workflows
- Load testing of concurrent operations
- Integration testing with gcommon components

## File Structure

```
subtitle-manager/
├── pkg/
│   ├── subtitle/
│   │   ├── proto/
│   │   │   ├── messages/
│   │   │   │   ├── subtitle_record.proto
│   │   │   │   ├── subtitle_file.proto
│   │   │   │   ├── subtitle_metadata.proto
│   │   │   │   └── timing_info.proto
│   │   │   ├── enums/
│   │   │   │   ├── subtitle_format.proto
│   │   │   │   └── processing_status.proto
│   │   │   ├── services/
│   │   │   │   ├── processing_service.proto
│   │   │   │   └── storage_service.proto
│   │   │   ├── requests/
│   │   │   │   ├── parse_subtitle_request.proto
│   │   │   │   ├── convert_format_request.proto
│   │   │   │   └── store_subtitle_request.proto
│   │   │   └── responses/
│   │   │       ├── parse_subtitle_response.proto
│   │   │       ├── convert_format_response.proto
│   │   │       └── store_subtitle_response.proto
│   │   ├── processing/
│   │   │   ├── parser.go
│   │   │   ├── converter.go
│   │   │   └── validator.go
│   │   ├── storage/
│   │   │   ├── filesystem.go
│   │   │   ├── metadata.go
│   │   │   └── cache.go
│   │   └── grpc/
│   │       ├── processing_service.go
│   │       └── storage_service.go
│   └── gateway/
│       ├── rest.go
│       └── middleware.go
├── gen/ (generated protobuf code)
├── api/ (OpenAPI specs)
├── tests/
│   ├── integration/
│   └── testdata/
└── cmd/
    ├── server/
    └── client/
```

## Acceptance Criteria

### Protobuf Implementation

- [ ] All proto files use Edition 2023
- [ ] Follow 1-1-1 design pattern strictly
- [ ] Use consistent `Subtitle` module prefix
- [ ] Proper `go_package` options
- [ ] Integration with gcommon proto types
- [ ] Successful `buf generate` execution
- [ ] No import or compilation errors

### Service Implementation

- [ ] Complete gRPC service implementations
- [ ] Proper middleware integration (auth, logging, metrics)
- [ ] Comprehensive unit test coverage (>90%)
- [ ] Integration tests with real subtitle files
- [ ] Error handling follows gcommon patterns
- [ ] Performance benchmarks meet requirements

### API Gateway

- [ ] REST API gateway fully functional
- [ ] OpenAPI documentation generated
- [ ] Authentication and authorization working
- [ ] Rate limiting implemented
- [ ] Monitoring and metrics collection
- [ ] Integration tests for REST endpoints

### Documentation and Maintenance

- [ ] All files have proper headers with version/GUID
- [ ] Documentation created using proper scripts
- [ ] No direct edits to README/CHANGELOG/TODO
- [ ] Task completion tracked in issues
- [ ] Code follows all style guidelines

## Dependencies

1. **gcommon protobuf types** - Must be available and properly generated
2. **buf tool** - For protobuf generation and linting
3. **Go 1.23+** - For service implementation
4. **grpc-gateway** - For REST API gateway
5. **copilot-agent-util** - For development operations

## Deliverables

1. **Complete protobuf definitions** for subtitle operations
2. **Fully implemented gRPC services** with proper middleware
3. **REST API gateway** with OpenAPI documentation
4. **Comprehensive test suite** with >90% coverage
5. **Integration with gcommon** auth, logging, and metrics
6. **Performance benchmarks** and optimization
7. **Deployment configuration** and documentation

## Notes

- Start with Task 3.1 (core messages) as foundation
- Each subtask can be assigned to different AI agents
- Test protobuf generation after each proto file addition
- Focus on type safety and proper error handling
- Ensure backward compatibility with existing subtitle formats
- Plan for future extensibility and additional formats
- Consider memory efficiency for large subtitle files
- Implement proper streaming for big file operations
