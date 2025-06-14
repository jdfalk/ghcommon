# Go Code Style Guide

This guide follows the official Go style conventions and best practices.

## Code Formatting

- Use `gofmt` or `go fmt` to automatically format code
- Line length is flexible, but keep it reasonable (under 100 characters is common)
- Use tabs for indentation (not spaces)
- No trailing whitespace

## Naming Conventions

- Package names: short, concise, lowercase, no underscores (`strconv`, not `string_converter`)
- Interface names: use -er suffix for interfaces describing actions (`Reader`, `Writer`)
- Variable/function names: use MixedCaps or mixedCaps, not underscores
- Exported (public) names: must begin with a capital letter (`MarshalJSON`)
- Unexported (private) names: must begin with a lowercase letter (`marshalState`)
- Acronyms in names should be all caps (`HTTPServer`, not `HttpServer`)

```go
// Good naming examples
type Reader interface {
    Read(p []byte) (n int, err error)
}

func ServeHTTP(w http.ResponseWriter, r *http.Request) {
    localAddress := r.RemoteAddr
    // ...
}
```

## Package Organization

- One package per directory
- Package name matches the last element of the import path
- Keep package names short and descriptive
- Organize by functionality, not by type
- `internal` packages are only accessible within the parent package
- `main` package is for executables

## Imports

- Group imports into blocks separated by blank lines:
  1. Standard library packages
  2. Third-party packages
  3. Your project's packages
- Use import aliases only when necessary to avoid naming conflicts
- Do not use relative imports
- Do not use dot imports (e.g., `import . "fmt"`)

```go
import (
    "fmt"
    "io"
    "log"

    "github.com/pkg/errors"
    "golang.org/x/net/context"

    "yourproject/models"
    "yourproject/controllers"
)
```

## Comments and Documentation

- All exported (public) declarations should have doc comments
- Start comments with the name of the thing being described
- Comments should be full sentences, ending with period
- Use // for line comments, not /* */  <!-- markdownlint-disable-line MD037 -->
- Use `godoc` conventions for package documentation

```go
// Package maildir implements reading and writing mail messages
// from a maildir structure on disk.
package maildir

// ErrInvalidMaildir is returned when a maildir is not valid.
var ErrInvalidMaildir = errors.New("invalid maildir")

// ReadMessage reads a message from the specified maildir.
// It returns the Message and any error encountered.
func ReadMessage(dir string) (*Message, error) {
    // Implementation
}
```

## Error Handling

- Always check errors
- Return errors rather than using panic
- Error variables should be named `ErrXxx`
- Error types should be named `XxxError`
- Use `errors.New` or `fmt.Errorf` for simple errors
- Consider using error wrapping (Go 1.13+) to add context to errors

```go
// Error handling example
f, err := os.Open(filename)
if err != nil {
    return nil, fmt.Errorf("opening %s: %w", filename, err)
}
defer f.Close()
```

## Control Structures

- Don't use parentheses around conditionals
- Put else on the same line as the closing brace
- Early returns are encouraged to reduce nesting
- Prefer switch over long if-else chains
- Empty switch is idiomatic for long if-else chains

```go
// Switch example
switch food := getFood(); food {
case "apple":
    // ...
case "banana":
    // ...
default:
    // ...
}

// Early return example
func process(data []byte) error {
    if len(data) == 0 {
        return errors.New("empty data")
    }

    // Continue processing...
    return nil
}
```

## Functions and Methods

- Keep functions short and focused
- Prefer methods with value receivers unless you need to modify the receiver
- Return early on errors to avoid deep nesting
- Use named result parameters only when it improves clarity
- Function parameters typically appear in order of importance

## Concurrency

- Don't start goroutines without knowing how they will exit
- Avoid sharing memory; use channels to communicate
- Use select for multi-way concurrent control
- Always use mutexes or channels for accessing shared data
- Consider using sync.WaitGroup for managing groups of goroutines

## Tools

- Use `go fmt` for code formatting
- Use `go vet` to find potential issues
- Use `golint` for style checking
- Use `go test` for running tests
- Use `go mod` for dependency management

## Best Practices

- Defer file and resource closing
- Return structs by value, slices and maps by reference
- Prefer composition over inheritance
- Use context for cancellation and deadlines
- Use slices instead of arrays in most cases
- Interface satisfaction is implicit
- Provide useful zero values for structs when possible
- Avoid unnecessary pointer usage
