<!-- file: testdata/go/README.md -->
<!-- version: 1.0.0 -->
<!-- guid: 4d5f6a7b-8c9d-0e1f-2a3b-4c5d6e7f8a9b -->
<!-- last-edited: 2026-01-19 -->

# Go Test Fixtures

This directory contains a complete Go module used for testing pre-commit hooks and other Go tooling
in the ghcommon repository.

## Structure

- `go.mod` - Go module definition
- `main.go` - Main package entry point
- `calculator.go` - Simple calculator library for testing
- `calculator_test.go` - Comprehensive test suite

## Purpose

This test fixture ensures that all Go-related pre-commit hooks can run successfully:

- `go-build-mod` - Verifies the module builds
- `go-build-pkg` - Verifies packages build
- `go-test-mod` - Runs tests for the module
- `go-test-pkg` - Runs tests for packages
- `go-vet` - Runs vet analysis
- `go-fmt` - Checks formatting

## Running Tests

```bash
cd testdata/go
go test -v ./...
go build
```

## Expected Output

All tests should pass, and the build should succeed.
