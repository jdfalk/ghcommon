<!-- file: .github/instructions/go.instructions.md -->
<!-- version: 1.9.0 -->
<!-- guid: 4a5b6c7d-8e9f-1a2b-3c4d-5e6f7a8b9c0d -->
<!-- DO NOT EDIT: This file is managed centrally in ghcommon repository -->
<!-- To update: Create an issue/PR in jdfalk/ghcommon -->

<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
---
applyTo: "**/*.go"
description: |
  Go language-specific coding, documentation, and testing rules for Copilot/AI agents and VS Code Copilot customization. These rules extend the general instructions in `general-coding.instructions.md` and merge all unique content from the Google Go Style Guide.
---
<!-- markdownlint-enable -->
<!-- prettier-ignore-end -->

# Go Coding Instructions

- Follow the [general coding instructions](general-coding.instructions.md).
- Follow the
  [Google Go Style Guide](https://google.github.io/styleguide/go/index.html) for
  additional best practices.
- All Go files must begin with the required file header (see general
  instructions for details and Go example).

## Core Principles

- Clarity over cleverness: Code should be clear and readable
- Simplicity: Prefer simple solutions over complex ones
- Consistency: Follow established patterns within the codebase
- Readability: Code is written for humans to read

## Version Requirements

- **MANDATORY**: All Go projects must use Go 1.23.0 or higher
- **NO EXCEPTIONS**: Do not use older Go versions in any repository
- Update `go.mod` files to specify `go 1.23` minimum version
- Update `go.work` files to specify `go 1.23` minimum version
- All Go file headers must use version 1.23.0 or higher
- Use `go version` to verify your installation meets requirements

## Architecture: Go Version Strategy

This repository uses **branch-aware version targeting** to support multiple Go versions across parallel release tracks, enabling gradual adoption of Go 1.24 and 1.25 features while maintaining stability for production systems.

### Supported Go Versions

The following Go versions are supported with branch-specific policies:

- **Go 1.23**: Stable production version (supported on all branches)
- **Go 1.24**: Current stable with modern features (main branch + stable-1-go-1.24)
- **Go 1.25**: Latest with cutting-edge features (main branch only)

### Branch-Specific Version Policies

#### Main Branch

- **Go Versions**: 1.23, 1.24, 1.25
- **Policy**: Latest versions with all features
- **Use Case**: Active development, new features, testing
- **Feature Access**: All Go 1.25 features available

#### Stable Branches (stable-1-go-X.XX)

- **Go Versions**: Locked to specific version
- **Policy**: Version-locked for stability
- **Examples**:
  - `stable-1-go-1.24`: Go 1.24 only
  - `stable-1-go-1.23`: Go 1.23 only
- **Use Case**: Production deployments, long-term support
- **Feature Access**: Features available in locked version only

#### EOL and Work-Stopped Branches

- **EOL Branches**: Critical security fixes only
- **Work-Stopped Branches**: No further development
- **Policy**: Maintained for legacy systems, no new features

### Feature Adoption Timeline

#### Go 1.24 Features (Available Now)

- **testing.B.Loop()**: New benchmark loop syntax (see testing section)
- **Improved error wrapping**: Enhanced error context
- **Performance improvements**: Faster compilation, runtime optimizations

**Adoption**:

- ✅ Main branch: Use freely
- ✅ stable-1-go-1.24: Use freely
- ❌ stable-1-go-1.23: Not available

#### Go 1.25 Features (Available on Main)

- **os.Root()**: Filesystem root isolation (see security section)
- **Generic optimization**: Core Types removal, performance improvements
- **Integer range iteration**: `for i := range n {}` syntax (see iteration section)
- **Enhanced type inference**: Improved generic type deduction

**Adoption**:

- ✅ Main branch: Use freely for new code
- ⏳ stable-1-go-1.24: Wait for branch policy update
- ❌ stable-1-go-1.23: Not available

### Version Detection in Workflows

The CI/CD system automatically detects appropriate Go versions based on branch configuration:

```yaml
# Automatically resolved from workflow-versions.yml
go-versions:
  main: ["1.23", "1.24", "1.25"]
  stable-1-go-1.24: ["1.24"]
  stable-1-go-1.23: ["1.23"]
```

**Workflow Behavior**:

- **Main branch**: Tests against all supported versions
- **Stable branches**: Tests against locked version only
- **Release builds**: Uses highest version for the branch

### Migration Guide

#### Adopting Go 1.24 Features

1. **Verify Branch Policy**:

   ```bash
   # Check current branch
   git branch --show-current

   # Verify Go version in go.mod
   grep "^go " go.mod
   ```

2. **Update go.mod (if needed)**:

   ```go
   go 1.24
   ```

3. **Use New Features**:

   - Replace manual benchmark loops with `testing.B.Loop()`
   - Leverage improved error wrapping
   - Benefit from performance improvements automatically

#### Adopting Go 1.25 Features

1. **Confirm Main Branch**:

   ```bash
   git branch --show-current
   # Must be: main
   ```

2. **Update go.mod**:

   ```go
   go 1.25
   ```

3. **Use New Features**:

   - Use `os.Root()` for filesystem isolation in sandboxed operations
   - Replace traditional `for i := 0; i < n; i++` with `for i := range n {}`
   - Benefit from generic optimizations automatically
   - Leverage enhanced type inference

### Best Practices

#### Version Selection

- **New Projects**: Start with Go 1.24 for stability
- **Experimental Features**: Use Go 1.25 on main branch only
- **Production Code**: Use stable branches with locked versions

#### Feature Flags

Use build tags for version-specific features:

```go
//go:build go1.24

package mypackage

// Go 1.24-specific implementation using testing.B.Loop()
```

```go
//go:build go1.25

package mypackage

// Go 1.25-specific implementation using os.Root()
```

#### Compatibility

- **Write for minimum version**: Target Go 1.23 for maximum compatibility
- **Test across versions**: CI tests all supported versions on main branch
- **Document requirements**: Clearly state minimum Go version in README

### Version-Specific Sections

This document includes detailed sections for version-specific features:

- **testing.B.Loop() (Go 1.24+)**: See benchmarking section below
- **os.Root() (Go 1.25)**: See filesystem isolation section below
- **Integer Range Iteration (Go 1.25)**: See iteration patterns section below
- **Generic Optimization (Go 1.25)**: See generics section below

### Decision: When to Upgrade

#### Upgrade to Go 1.24 When

- ✅ Need improved benchmark testing with `testing.B.Loop()`
- ✅ Want better error wrapping capabilities
- ✅ Require performance improvements
- ✅ Ready to test on stable-1-go-1.24 branch

#### Upgrade to Go 1.25 When

- ✅ Need filesystem isolation with `os.Root()`
- ✅ Want cleaner integer range iteration
- ✅ Benefit from generic optimizations
- ✅ Working on main branch for active development
- ❌ **NOT for stable branches** (wait for policy update)

### Platform Support

All Go versions support the same platforms:

- **Linux**: amd64, arm64
- **macOS**: amd64 (Intel), arm64 (Apple Silicon)
- **NO WINDOWS**: Windows platform not supported

Cross-compilation configured for all targets in `.cargo/config.toml` and release workflows.

## Naming Conventions

- Use short, concise, evocative package names (lowercase, no underscores)
- Use camelCase for unexported names, PascalCase for exported names
- Use short names for short-lived variables, descriptive names for longer-lived
  variables
- Use PascalCase for exported constants, camelCase for unexported constants
- Single-method interfaces should end in "-er" (e.g., Reader, Writer)

## Code Organization

- Use `goimports` to format imports automatically
- Group imports: standard library, third-party, local
- No blank lines within groups, one blank line between groups
- Keep functions short and focused
- Use blank lines to separate logical sections
- Order: receiver, name, parameters, return values

## Formatting

- Use tabs for indentation, spaces for alignment
- Opening brace on same line as declaration, closing brace on its own line
- No strict line length limit, but aim for readability

## Comments

- Every package should have a package comment
- Public functions must have comments starting with the function name
- Comment exported variables, explain purpose and constraints

## Error Handling

- Use lowercase for error messages, no punctuation at end
- Be specific about what failed
- Create custom error types for specific error conditions
- Use `errors.Is` and `errors.As` for error checking

## Best Practices

- Use short variable declarations (`:=`) when possible
- Use `var` for zero values or when type is important
- Use `make()` for slices and maps with known capacity
- Accept interfaces, return concrete types
- Keep interfaces small and focused
- Use channels for communication between goroutines
- Use sync primitives for protecting shared state
- Test file names end with `_test.go`, test function names start with `Test`
- Use table-driven tests for multiple scenarios

## Required File Header

All Go files must begin with a standard header as described in the
[general coding instructions](general-coding.instructions.md). Example for Go:

```go
// file: path/to/file.go
// version: 1.0.0
// guid: 123e4567-e89b-12d3-a456-426614174000
```

## Google Go Style Guide (Complete)

Follow the complete Google Go Style Guide below for all Go code:

### Google Go Style Guide (Complete)

This style guide provides comprehensive conventions for writing clean, readable, and maintainable Go code.

#### Formatting

**gofmt:** All Go code must be formatted with `gofmt`. This is non-negotiable.

**Line Length:** No hard limit, but prefer shorter lines. Break long lines sensibly.

**Indentation:** Use tabs for indentation (handled automatically by gofmt).

**Spacing:** Let gofmt handle spacing. Generally:
- No space inside parentheses: `f(a, b)`
- Space around binary operators: `a + b`
- No space around unary operators: `!condition`

#### Naming Conventions

**Packages:**
- Short, concise, evocative names
- Lowercase, no underscores or mixedCaps
- Often single words

```go
// Good
package user
package httputil
package json

// Bad
package userService
package http_util
```

**Interfaces:**
- Use -er suffix for single-method interfaces
- Use MixedCaps

```go
// Good
type Reader interface {
    Read([]byte) (int, error)
}

type FileWriter interface {
    WriteFile(string, []byte) error
}

// Bad
type IReader interface {  // Don't prefix with I
    Read([]byte) (int, error)
}
```

**Functions and Methods:**
- Use MixedCaps
- Exported functions start with capital letter
- Unexported functions start with lowercase letter

```go
// Good - exported
func CalculateTotal(price, tax float64) float64 {
    return price + tax
}

// Good - unexported
func validateInput(input string) bool {
    return len(input) > 0
}
```

**Variables:**
- Use MixedCaps
- Short names for short scopes
- Longer descriptive names for longer scopes

```go
// Good - short scope
for i, v := range items {
    process(i, v)
}

// Good - longer scope
func processUserData(userData map[string]interface{}) error {
    userID, exists := userData["id"]
    if !exists {
        return errors.New("user ID not found")
    }
    // ... more processing
}

// Bad
func processUserData(d map[string]interface{}) error {  // 'd' too short for scope
    userIdentificationNumber, exists := d["id"]  // Too long for simple value
    // ...
}
```

**Constants:**
- Use MixedCaps
- Group related constants in blocks

```go
// Good
const (
    StatusOK       = 200
    StatusNotFound = 404
    StatusError    = 500
)

const DefaultTimeout = 30 * time.Second

// Bad
const STATUS_OK = 200  // Don't use underscores
```

#### Package Organization

**Package Names:**
- Choose package names that are both short and clear
- Avoid generic names like "util", "common", "misc"
- Package name should describe what it provides, not what it contains

```go
// Good
package user     // for user management
package auth     // for authentication
package httputil // for HTTP utilities

// Bad
package utils    // Too generic
package stuff    // Too vague
```

**Import Organization:**
- Group imports: standard library, third-party, local
- Use goimports to handle this automatically

```go
import (
    // Standard library
    "fmt"
    "os"
    "time"

    // Third-party
    "github.com/gorilla/mux"
    "google.golang.org/grpc"

    // Local
    "myproject/internal/auth"
    "myproject/pkg/utils"
)
```

#### Error Handling

**Error Strings:**
- Don't capitalize error messages
- Don't end with punctuation
- Be descriptive but concise

```go
// Good
return fmt.Errorf("failed to connect to database: %w", err)
return errors.New("invalid user ID")

// Bad
return errors.New("Failed to connect to database.")  // Capitalized, punctuation
return errors.New("error")  // Too vague
```

**Error Wrapping:**
- Use fmt.Errorf with %w verb to wrap errors
- Add context to errors as they bubble up

```go
func processUser(id string) error {
    user, err := getUserFromDB(id)
    if err != nil {
        return fmt.Errorf("failed to get user %s: %w", id, err)
    }

    if err := validateUser(user); err != nil {
        return fmt.Errorf("user validation failed: %w", err)
    }

    return nil
}
```

**Error Checking:**
- Check errors immediately after operations
- Don't ignore errors (use _ only when truly appropriate)

```go
// Good
file, err := os.Open(filename)
if err != nil {
    return fmt.Errorf("failed to open file: %w", err)
}
defer file.Close()

// Bad
file, _ := os.Open(filename)  // Ignoring error
// ... later in code ...
if file == nil {  // Too late to handle properly
    return errors.New("file is nil")
}
```

#### Function Design

**Function Length:** Keep functions short and focused. If a function is very long, consider breaking it up.

**Function Signature:**
- Related parameters should be grouped
- Use meaningful parameter names

```go
// Good
func CreateUser(firstName, lastName, email string, age int) *User {
    return &User{
        FirstName: firstName,
        LastName:  lastName,
        Email:     email,
        Age:       age,
    }
}

// Bad
func CreateUser(a, b, c string, d int) *User {  // Unclear parameter names
    return &User{
        FirstName: a,
        LastName:  b,
        Email:     c,
        Age:       d,
    }
}
```

**Return Values:**
- Return errors as the last value
- Use named return parameters sparingly

```go
// Good
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

// Acceptable for short, clear functions
func split(path string) (dir, file string) {
    // ... implementation
    return
}
```

#### Struct Design

**Field Organization:**
- Group related fields together
- Consider field alignment for memory efficiency

```go
type User struct {
    // Identity fields
    ID       int64
    Username string
    Email    string

    // Personal information
    FirstName string
    LastName  string
    Age       int

    // Metadata
    CreatedAt time.Time
    UpdatedAt time.Time
    Active    bool
}
```

**Constructor Functions:**
- Use New prefix for constructor functions
- Return pointers for structs that will be modified

```go
func NewUser(username, email string) *User {
    return &User{
        Username:  username,
        Email:     email,
        CreatedAt: time.Now(),
        Active:    true,
    }
}
```

#### Concurrency

**Goroutines:**
- Use goroutines for independent tasks
- Always consider how goroutines will exit

```go
// Good
func processItems(items []Item) {
    var wg sync.WaitGroup

    for _, item := range items {
        wg.Add(1)
        go func(item Item) {
            defer wg.Done()
            process(item)
        }(item)
    }

    wg.Wait()
}
```

**Channels:**
- Use channels for communication between goroutines
- Close channels when done sending

```go
func producer(ch chan<- int) {
    defer close(ch)
    for i := 0; i < 10; i++ {
        ch <- i
    }
}

func consumer(ch <-chan int) {
    for value := range ch {
        fmt.Println(value)
    }
}
```

#### Comments and Documentation

**Package Comments:**
- Every package should have a package comment
- Use complete sentences

```go
// Package user provides functionality for user management,
// including authentication, authorization, and user data operations.
package user
```

**Function Comments:**
- Document all exported functions
- Start with the function name
- Explain what the function does, not how

```go
// CalculateTotal computes the total price including tax.
// It returns an error if the tax rate is negative.
func CalculateTotal(price, taxRate float64) (float64, error) {
    if taxRate < 0 {
        return 0, errors.New("tax rate cannot be negative")
    }
    return price * (1 + taxRate), nil
}
```

**Inline Comments:**
- Use for complex logic or non-obvious code
- Explain why, not what

```go
// Sort items by priority to ensure high-priority items are processed first
sort.Slice(items, func(i, j int) bool {
    return items[i].Priority > items[j].Priority
})
```

#### Testing

**Test Functions:**
- Use TestXxx naming convention
- Use t.Run for subtests

```go
func TestCalculateTotal(t *testing.T) {
    tests := []struct {
        name     string
        price    float64
        taxRate  float64
        expected float64
        hasError bool
    }{
        {
            name:     "positive values",
            price:    100.0,
            taxRate:  0.1,
            expected: 110.0,
            hasError: false,
        },
        {
            name:     "negative tax rate",
            price:    100.0,
            taxRate:  -0.1,
            expected: 0.0,
            hasError: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result, err := CalculateTotal(tt.price, tt.taxRate)

            if tt.hasError {
                if err == nil {
                    t.Errorf("expected error, got none")
                }
                return
            }

            if err != nil {
                t.Errorf("unexpected error: %v", err)
                return
            }

            if result != tt.expected {
                t.Errorf("expected %f, got %f", tt.expected, result)
            }
        })
    }
}
```

**Benchmark Functions:**

```go
func BenchmarkCalculateTotal(b *testing.B) {
    for i := 0; i < b.N; i++ {
        CalculateTotal(100.0, 0.1)
    }
}
```

## Benchmarking with testing.B.Loop() (Go 1.24+)

**Available**: Go 1.24 and later

Go 1.24 introduces `testing.B.Loop()`, a new method for writing benchmark loops that replaces the traditional `for i := 0; i < b.N; i++` pattern. This new approach provides better compiler optimizations and cleaner benchmark code.

### Basic Usage

#### Traditional Approach (Go 1.23 and earlier)

```go
func BenchmarkProcessData(b *testing.B) {
    data := generateTestData()
    b.ResetTimer() // Reset timer after setup

    for i := 0; i < b.N; i++ {
        processData(data)
    }
}
```

#### Modern Approach (Go 1.24+)

```go
func BenchmarkProcessData(b *testing.B) {
    data := generateTestData()
    b.ResetTimer() // Reset timer after setup

    for b.Loop() {
        processData(data)
    }
}
```

### Key Benefits

1. **Cleaner Syntax**: Eliminates the need for explicit loop variable
2. **Compiler Optimizations**: Better optimization opportunities for the compiler
3. **Consistent Pattern**: Matches the style of `for range` loops
4. **No Manual Counter**: Removes potential for off-by-one errors

### When to Use testing.B.Loop()

✅ **Use testing.B.Loop() when:**

- Writing new benchmarks in Go 1.24+ codebases
- Refactoring existing benchmarks for modernization
- Working on main branch or stable-1-go-1.24 branches
- Benchmark doesn't need the iteration index

❌ **Use traditional loop when:**

- Maintaining Go 1.23 compatibility
- Need access to iteration index (rare in benchmarks)
- Working on stable-1-go-1.23 or older branches

### Complete Examples

#### Simple Function Benchmark

```go
// Traditional (Go 1.23)
func BenchmarkStringConcat(b *testing.B) {
    for i := 0; i < b.N; i++ {
        _ = "hello" + "world"
    }
}

// Modern (Go 1.24+)
func BenchmarkStringConcat(b *testing.B) {
    for b.Loop() {
        _ = "hello" + "world"
    }
}
```

#### Benchmark with Setup

```go
func BenchmarkDatabaseQuery(b *testing.B) {
    // Setup (not measured)
    db := setupTestDatabase()
    defer db.Close()

    query := "SELECT * FROM users WHERE active = ?"
    b.ResetTimer() // Start timing here

    for b.Loop() {
        rows, err := db.Query(query, true)
        if err != nil {
            b.Fatal(err)
        }
        rows.Close()
    }
}
```

#### Benchmark with Sub-Benchmarks

```go
func BenchmarkJSONOperations(b *testing.B) {
    data := map[string]interface{}{
        "name": "John Doe",
        "age":  30,
        "active": true,
    }

    b.Run("Marshal", func(b *testing.B) {
        for b.Loop() {
            _, err := json.Marshal(data)
            if err != nil {
                b.Fatal(err)
            }
        }
    })

    b.Run("Unmarshal", func(b *testing.B) {
        jsonData, _ := json.Marshal(data)
        var result map[string]interface{}

        for b.Loop() {
            err := json.Unmarshal(jsonData, &result)
            if err != nil {
                b.Fatal(err)
            }
        }
    })
}
```

#### Parallel Benchmarks

```go
func BenchmarkConcurrentProcessor(b *testing.B) {
    processor := NewProcessor()

    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() { // Note: RunParallel uses pb.Next(), not b.Loop()
            processor.Process(generateRandomData())
        }
    })
}
```

**Important**: When using `b.RunParallel()`, continue using `pb.Next()` in the parallel function. The `testing.B.Loop()` method is for sequential benchmarks only.

### Migration Strategy

#### Gradual Migration (Recommended)

1. **Update go.mod** to Go 1.24:

   ```go
   go 1.24
   ```

2. **Use build tags** for version-specific benchmarks:

   ```go
   //go:build go1.24

   package mypackage

   import "testing"

   func BenchmarkModern(b *testing.B) {
       for b.Loop() {
           // benchmark code
       }
   }
   ```

3. **Keep compatibility versions** for older Go:

   ```go
   //go:build !go1.24

   package mypackage

   import "testing"

   func BenchmarkModern(b *testing.B) {
       for i := 0; i < b.N; i++ {
           // same benchmark code
       }
   }
   ```

#### Complete Migration (Go 1.24+ Only)

Replace all traditional benchmark loops:

```bash
# Find all traditional benchmark loops
grep -r "for i := 0; i < b.N; i++" . --include="*_test.go"

# Replace with testing.B.Loop()
# (Do this carefully, reviewing each change)
```

### Best Practices

#### DO: Use for Simple Iterations

```go
func BenchmarkSimpleOperation(b *testing.B) {
    for b.Loop() {
        result := expensiveOperation()
        _ = result // Prevent compiler optimization
    }
}
```

#### DO: Reset Timer After Setup

```go
func BenchmarkWithSetup(b *testing.B) {
    data := setupTestData() // Not measured
    b.ResetTimer()          // Start measuring here

    for b.Loop() {
        process(data)
    }
}
```

#### DO: Use Sub-Benchmarks for Comparisons

```go
func BenchmarkStringBuilding(b *testing.B) {
    b.Run("Concat", func(b *testing.B) {
        for b.Loop() {
            _ = "a" + "b" + "c"
        }
    })

    b.Run("Builder", func(b *testing.B) {
        for b.Loop() {
            var builder strings.Builder
            builder.WriteString("a")
            builder.WriteString("b")
            builder.WriteString("c")
            _ = builder.String()
        }
    })
}
```

#### DON'T: Access Non-Existent Loop Variable

```go
// Bad - no loop variable with testing.B.Loop()
func BenchmarkBad(b *testing.B) {
    for b.Loop() {
        // Can't use i here - it doesn't exist
        fmt.Println(i) // Compile error
    }
}

// Good - use traditional loop if you need the index
func BenchmarkWithIndex(b *testing.B) {
    for i := 0; i < b.N; i++ {
        if i%100 == 0 {
            // Do something every 100 iterations
        }
    }
}
```

#### DON'T: Mix with RunParallel

```go
// Wrong - use pb.Next() with RunParallel
func BenchmarkParallel(b *testing.B) {
    b.RunParallel(func(pb *testing.PB) {
        for b.Loop() { // Wrong! Use pb.Next()
            process()
        }
    })
}

// Correct
func BenchmarkParallel(b *testing.B) {
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() { // Correct
            process()
        }
    })
}
```

### Performance Characteristics

The `testing.B.Loop()` method provides the same performance as traditional loops while offering:

- **Better Compiler Optimization**: Simpler loop structure allows for better optimizations
- **Reduced Overhead**: Eliminates unnecessary loop variable management
- **Consistent Behavior**: Same iteration count as `for i := 0; i < b.N; i++`

### Branch-Specific Guidelines

#### Main Branch

- ✅ Use `testing.B.Loop()` for all new benchmarks
- ✅ Refactor existing benchmarks when convenient
- ✅ Both styles acceptable during transition

#### stable-1-go-1.24

- ✅ Use `testing.B.Loop()` for all new benchmarks
- ✅ Migration encouraged but not required

#### stable-1-go-1.23

- ❌ Cannot use `testing.B.Loop()` (not available)
- ✅ Continue using traditional loop syntax

### Compatibility Check

Ensure your code targets the correct Go version:

```go
// In go.mod
go 1.24  // Required for testing.B.Loop()
```

```go
// In benchmark file (optional build tag)
//go:build go1.24

package mypackage

import "testing"

func BenchmarkModern(b *testing.B) {
    for b.Loop() {
        // Modern benchmark code
    }
}
```

## Filesystem Isolation with os.Root() (Go 1.25+)

> **Availability**: Go 1.25+ only. Not available on Go 1.23 or 1.24.

### Overview

The `os.Root()` API introduced in Go 1.25 provides secure filesystem isolation by creating a restricted view of the filesystem rooted at a specific directory. This is critical for sandboxing untrusted code, implementing secure file operations, and preventing path traversal attacks.

### Why Use os.Root()?

- **Security Sandboxing**: Prevent access to files outside a designated directory tree
- **Path Traversal Protection**: Automatically blocks `..` and symlink escapes
- **Multi-Tenant Isolation**: Safely isolate operations for different users/tenants
- **Plugin Security**: Sandbox plugin file operations to specific directories
- **Testing Isolation**: Create isolated filesystem views for tests

### Basic Usage

```go
package main

import (
    "fmt"
    "os"
)

func main() {
    // Create a filesystem root at /safe/directory
    root, err := os.Root("/safe/directory")
    if err != nil {
        fmt.Fprintf(os.Stderr, "Failed to create root: %v\n", err)
        return
    }
    defer root.Close()

    // All file operations through root are isolated to /safe/directory
    file, err := root.Open("data.txt") // Actually opens /safe/directory/data.txt
    if err != nil {
        fmt.Fprintf(os.Stderr, "Failed to open file: %v\n", err)
        return
    }
    defer file.Close()

    // Attempts to escape are blocked
    _, err = root.Open("../../../etc/passwd") // Returns error, cannot escape
    if err != nil {
        fmt.Println("Path traversal blocked (expected)")
    }
}
```

### Complete Example: Sandboxed File Server

```go
package main

import (
    "fmt"
    "io"
    "net/http"
    "os"
    "path/filepath"
)

// SecureFileServer serves files only from a sandboxed directory
type SecureFileServer struct {
    root *os.Root
}

func NewSecureFileServer(baseDir string) (*SecureFileServer, error) {
    // Create isolated filesystem view
    root, err := os.Root(baseDir)
    if err != nil {
        return nil, fmt.Errorf("failed to create root: %w", err)
    }

    return &SecureFileServer{root: root}, nil
}

func (s *SecureFileServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    // Clean the path but root isolation prevents escapes anyway
    cleanPath := filepath.Clean(r.URL.Path)

    // Open file through isolated root
    file, err := s.root.Open(cleanPath)
    if err != nil {
        http.Error(w, "File not found", http.StatusNotFound)
        return
    }
    defer file.Close()

    // Get file info for content type detection
    info, err := file.Stat()
    if err != nil {
        http.Error(w, "Internal error", http.StatusInternalServerError)
        return
    }

    // Serve the file
    http.ServeContent(w, r, info.Name(), info.ModTime(), file)
}

func (s *SecureFileServer) Close() error {
    return s.root.Close()
}

func main() {
    server, err := NewSecureFileServer("/var/www/public")
    if err != nil {
        fmt.Fprintf(os.Stderr, "Failed to create server: %v\n", err)
        os.Exit(1)
    }
    defer server.Close()

    http.Handle("/files/", server)
    http.ListenAndServe(":8080", nil)
}
```

### Example: Secure Plugin Execution

```go
package main

import (
    "fmt"
    "os"
    "path/filepath"
)

type PluginSandbox struct {
    root      *os.Root
    pluginID  string
}

func NewPluginSandbox(pluginID string) (*PluginSandbox, error) {
    // Create isolated directory for this plugin
    sandboxDir := filepath.Join("/var/plugins", pluginID)
    if err := os.MkdirAll(sandboxDir, 0755); err != nil {
        return nil, fmt.Errorf("failed to create sandbox: %w", err)
    }

    // Create filesystem root for isolation
    root, err := os.Root(sandboxDir)
    if err != nil {
        return nil, fmt.Errorf("failed to create root: %w", err)
    }

    return &PluginSandbox{
        root:     root,
        pluginID: pluginID,
    }, nil
}

// ReadConfig safely reads plugin configuration
func (s *PluginSandbox) ReadConfig(filename string) ([]byte, error) {
    file, err := s.root.Open(filename)
    if err != nil {
        return nil, fmt.Errorf("config not found: %w", err)
    }
    defer file.Close()

    return io.ReadAll(file)
}

// WriteOutput safely writes plugin output
func (s *PluginSandbox) WriteOutput(filename string, data []byte) error {
    file, err := s.root.Create(filename)
    if err != nil {
        return fmt.Errorf("failed to create output: %w", err)
    }
    defer file.Close()

    _, err = file.Write(data)
    return err
}

// ListFiles lists files in the sandbox
func (s *PluginSandbox) ListFiles() ([]string, error) {
    dir, err := s.root.Open(".")
    if err != nil {
        return nil, err
    }
    defer dir.Close()

    entries, err := dir.Readdir(-1)
    if err != nil {
        return nil, err
    }

    var files []string
    for _, entry := range entries {
        files = append(files, entry.Name())
    }
    return files, nil
}

func (s *PluginSandbox) Close() error {
    return s.root.Close()
}
```

### Example: Secure Testing Isolation

```go
package mypackage_test

import (
    "os"
    "path/filepath"
    "testing"
)

func TestWithIsolatedFS(t *testing.T) {
    // Create temporary directory for test
    tempDir := t.TempDir()

    // Create isolated filesystem view
    root, err := os.Root(tempDir)
    if err != nil {
        t.Fatalf("Failed to create root: %v", err)
    }
    defer root.Close()

    // Create test files in isolated environment
    testData := []byte("test content")
    if err := root.WriteFile("test.txt", testData, 0644); err != nil {
        t.Fatalf("Failed to write test file: %v", err)
    }

    // Test file operations in isolation
    data, err := root.ReadFile("test.txt")
    if err != nil {
        t.Fatalf("Failed to read file: %v", err)
    }

    if string(data) != string(testData) {
        t.Errorf("Data mismatch: got %q, want %q", data, testData)
    }

    // Verify path traversal is blocked
    _, err = root.ReadFile("../../../../../etc/passwd")
    if err == nil {
        t.Error("Path traversal should have been blocked")
    }
}
```

### Security Considerations

#### ✅ DO: Use for Untrusted Code

```go
// Good - isolate untrusted plugin operations
func executePlugin(pluginPath string) error {
    root, err := os.Root(filepath.Dir(pluginPath))
    if err != nil {
        return err
    }
    defer root.Close()

    // Plugin can only access files within its directory
    return runPluginInSandbox(root, filepath.Base(pluginPath))
}
```

#### ✅ DO: Validate Before Creating Root

```go
// Good - validate directory exists and is safe
func createSafeRoot(path string) (*os.Root, error) {
    // Ensure path exists
    info, err := os.Stat(path)
    if err != nil {
        return nil, fmt.Errorf("invalid path: %w", err)
    }

    // Ensure it's a directory
    if !info.IsDir() {
        return nil, fmt.Errorf("path is not a directory: %s", path)
    }

    // Create isolated root
    return os.Root(path)
}
```

#### ✅ DO: Always Close Roots

```go
// Good - clean up root when done
root, err := os.Root("/sandbox")
if err != nil {
    return err
}
defer root.Close() // Always clean up

// Use root for operations
```

#### ❌ DON'T: Trust User-Provided Paths Without Validation

```go
// Bad - no validation of user input
func openUserFile(userPath string) error {
    root, _ := os.Root(userPath) // Could be anything!
    defer root.Close()
    // ...
}

// Good - validate user input first
func openUserFile(userPath string) error {
    // Validate path is within allowed directory
    allowedBase := "/var/user-data"
    cleanPath := filepath.Clean(userPath)
    if !filepath.HasPrefix(cleanPath, allowedBase) {
        return fmt.Errorf("path outside allowed directory")
    }

    root, err := os.Root(cleanPath)
    if err != nil {
        return err
    }
    defer root.Close()
    // ...
}
```

#### ❌ DON'T: Assume Root Prevents All Attacks

```go
// Bad - root isolation doesn't prevent logic errors
func processFile(filename string) error {
    root, _ := os.Root("/data")
    defer root.Close()

    // Still vulnerable to logic errors:
    // - SQL injection if filename used in queries
    // - Command injection if filename passed to exec
    // - Resource exhaustion if file is huge

    file, _ := root.Open(filename)
    // ... process file without size limits (bad!)
}

// Good - combine root isolation with other security measures
func processFile(filename string) error {
    root, err := os.Root("/data")
    if err != nil {
        return err
    }
    defer root.Close()

    // Validate filename
    if err := validateFilename(filename); err != nil {
        return err
    }

    file, err := root.Open(filename)
    if err != nil {
        return err
    }
    defer file.Close()

    // Check file size before processing
    info, err := file.Stat()
    if err != nil {
        return err
    }
    if info.Size() > maxFileSize {
        return fmt.Errorf("file too large: %d bytes", info.Size())
    }

    // Process with limits
    return processWithLimits(file, info.Size())
}
```

### Performance Characteristics

The `os.Root()` API provides:

- **Minimal Overhead**: Root creation is lightweight (similar to opening a directory)
- **No Path Rewriting**: Operations are enforced at the kernel level where possible
- **Efficient Checking**: Path validation happens once at root creation
- **Scalable**: Multiple roots can coexist for different isolation contexts

### Branch-Specific Guidelines

#### Main Branch (Go 1.25+)

- ✅ Use `os.Root()` for all sandboxing operations
- ✅ Refactor existing sandboxing code to use `os.Root()`
- ✅ Document security benefits in code comments

#### stable-1-go-1.24 and stable-1-go-1.23

- ❌ Cannot use `os.Root()` (not available)
- ✅ Use alternative approaches:
  - Manual path validation with `filepath.Clean()` and prefix checking
  - chroot (Unix-specific, requires privileges)
  - Container-level isolation
  - Third-party libraries like `securejoin`

### Compatibility Check

```go
// In go.mod
go 1.25  // Required for os.Root()
```

```go
// With build tags for version-specific code
//go:build go1.25

package secure

import "os"

func CreateSandbox(dir string) (*os.Root, error) {
    return os.Root(dir)
}
```

```go
// Fallback for older versions
//go:build !go1.25

package secure

import (
    "fmt"
    "os"
)

type Root struct {
    basePath string
}

func (r *Root) Close() error {
    return nil
}

func CreateSandbox(dir string) (*Root, error) {
    // Fallback implementation using manual validation
    return &Root{basePath: dir}, nil
}
```

### Migration from Manual Path Validation

**Before (Go 1.24 and earlier):**

```go
func openSandboxedFile(baseDir, filename string) (*os.File, error) {
    // Manual validation required
    cleanPath := filepath.Clean(filename)
    if filepath.IsAbs(cleanPath) {
        return nil, fmt.Errorf("absolute paths not allowed")
    }

    fullPath := filepath.Join(baseDir, cleanPath)
    if !strings.HasPrefix(fullPath, baseDir) {
        return nil, fmt.Errorf("path escapes base directory")
    }

    return os.Open(fullPath)
}
```

**After (Go 1.25+):**

```go
func openSandboxedFile(baseDir, filename string) (*os.File, error) {
    root, err := os.Root(baseDir)
    if err != nil {
        return nil, err
    }
    defer root.Close()

    // Root automatically prevents escapes
    return root.Open(filename)
}
```

### Integration with Existing Security Practices

#### Combine with Capabilities

```go
import (
    "os"
    "syscall"
)

// Drop privileges and create sandbox
func createSecureSandbox(dir string) (*os.Root, error) {
    // Drop unnecessary capabilities (Unix)
    if err := dropCapabilities(); err != nil {
        return nil, err
    }

    // Create filesystem isolation
    return os.Root(dir)
}

func dropCapabilities() error {
    // Implementation depends on platform
    // Use syscall or x/sys/unix for capability management
    return nil
}
```

#### Combine with Resource Limits

```go
import (
    "os"
    "syscall"
)

// Create sandbox with resource limits
type SandboxConfig struct {
    BaseDir     string
    MaxFileSize int64
    MaxFiles    int
}

func CreateLimitedSandbox(cfg SandboxConfig) (*os.Root, error) {
    // Set resource limits
    var rlimit syscall.Rlimit
    rlimit.Cur = uint64(cfg.MaxFiles)
    rlimit.Max = uint64(cfg.MaxFiles)
    if err := syscall.Setrlimit(syscall.RLIMIT_NOFILE, &rlimit); err != nil {
        return nil, fmt.Errorf("failed to set file limit: %w", err)
    }

    // Create filesystem isolation
    return os.Root(cfg.BaseDir)
}
```

This covers the essential Go style guidelines including formatting, naming conventions, package organization, error handling, function design, struct design, concurrency, comments, and testing best practices.
