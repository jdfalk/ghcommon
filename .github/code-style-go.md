<!-- file: copilot/code-style-go.md -->
<!-- version: 1.0.0 -->
<!-- guid: 4c7f1a2d-5e8b-4c7f-1a2d-8b5e1a4c7f1a -->

# Go Style Guide (Google)

This document summarizes Google's Go style guide for use in code generation and review.

## Core Principles

- **Clarity over cleverness**: Code should be clear and readable
- **Simplicity**: Prefer simple solutions over complex ones
- **Consistency**: Follow established patterns within the codebase
- **Readability**: Code is written for humans to read

## Naming Conventions

### Packages

- Use short, concise, evocative names
- Use lowercase, single words when possible
- Avoid abbreviations unless they're well-known
- Examples: `time`, `http`, `json`

### Functions and Variables

- Use camelCase for unexported names
- Use PascalCase for exported names
- Use short names for short-lived variables
- Use descriptive names for longer-lived variables
- Examples: `userID`, `ParseURL`, `count`, `maxRetries`

### Constants

- Use PascalCase for exported constants
- Use camelCase for unexported constants
- Group related constants with `iota` when appropriate

### Interfaces

- Single-method interfaces should end in "-er"
- Examples: `Reader`, `Writer`, `Handler`

## Code Organization

### Import Formatting

- Use `goimports` to format imports automatically
- Group imports: standard library, third-party, local
- No blank lines within groups, one blank line between groups

```go
import (
    "fmt"
    "os"

    "github.com/example/external"

    "myproject/internal/config"
)
```

### Function Declaration

- Keep functions short and focused
- Use blank lines to separate logical sections
- Order: receiver, name, parameters, return values

```go
func (r *receiver) FunctionName(param1 type1, param2 type2) (returnType, error) {
    // implementation
}
```

## Formatting

### Line Length

- No strict limit, but aim for readability
- Break long lines at logical points
- Prefer shorter lines when possible

### Indentation

- Use tabs for indentation
- Use spaces for alignment

### Braces

- Opening brace on same line as declaration
- Closing brace on its own line

```go
if condition {
    // code
} else {
    // code
}
```

## Comments

### Package Comments

- Every package should have a package comment
- Start with "Package packagename"
- Explain the package's purpose

### Function Comments

- Public functions must have comments
- Start with the function name
- Explain what the function does, not how

```go
// ParseURL parses a raw URL string and returns a URL structure.
func ParseURL(rawurl string) (*URL, error) {
    // implementation
}
```

### Variable Comments

- Comment exported variables
- Explain the purpose and any constraints

## Error Handling

### Error Messages

- Use lowercase for error messages
- Don't end with punctuation
- Be specific about what failed

```go
return fmt.Errorf("failed to parse URL %q: %w", url, err)
```

### Error Types

- Create custom error types for specific error conditions
- Use `errors.Is` and `errors.As` for error checking

## Best Practices

### Variable Declaration

- Use short variable declarations (`:=`) when possible
- Use `var` for zero values or when type is important

```go
// Preferred
count := 0
var users []User

// When type clarity is needed
var timeout time.Duration = 30 * time.Second
```

### Slices and Maps

- Use `make()` for slices and maps with known capacity
- Check for nil before using

```go
users := make([]User, 0, expectedCount)
cache := make(map[string]Value, expectedSize)
```

### Interfaces

- Accept interfaces, return concrete types
- Keep interfaces small and focused
- Define interfaces in the consuming package

### Concurrency

- Use channels for communication between goroutines
- Use sync package primitives for protecting shared state
- Don't communicate by sharing memory; share memory by communicating

### Testing

- Test file names end with `_test.go`
- Test function names start with `Test`
- Use table-driven tests for multiple scenarios

```go
func TestParseURL(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    *URL
        wantErr bool
    }{
        // test cases
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // test implementation
        })
    }
}
```

## Code Quality

### Linting

- Use `golangci-lint` with Google-style configuration
- Address all linter warnings
- Use `gofmt` and `goimports` for formatting

### Documentation

- Write clear, concise documentation
- Include examples for public APIs
- Use godoc conventions

### Performance

- Profile before optimizing
- Prefer clarity over premature optimization
- Use appropriate data structures

## Common Patterns

### Option Pattern

```go
type Config struct {
    timeout time.Duration
    retries int
}

type Option func(*Config)

func WithTimeout(d time.Duration) Option {
    return func(c *Config) {
        c.timeout = d
    }
}

func NewClient(opts ...Option) *Client {
    config := &Config{
        timeout: 30 * time.Second,
        retries: 3,
    }
    for _, opt := range opts {
        opt(config)
    }
    return &Client{config: config}
}
```

### Builder Pattern

- Use when constructing complex objects
- Provide sensible defaults
- Make the zero value useful when possible

## Anti-patterns to Avoid

- Don't use `init()` functions unless absolutely necessary
- Don't use global variables
- Don't ignore errors
- Don't use panic for normal error handling
- Don't use `interface{}` unless necessary
- Don't over-engineer with premature abstractions

## Tools and Configuration

### Required Tools

- `gofmt`: Format Go source code
- `goimports`: Format imports
- `golangci-lint`: Comprehensive linting
- `go vet`: Static analysis

### IDE Configuration

- Configure editor to run `gofmt` on save
- Enable import organization
- Configure linter integration

This style guide should be used as the foundation for all Go code generation and formatting decisions.
