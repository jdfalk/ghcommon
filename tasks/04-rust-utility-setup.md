# Task 4: Rust Utility Setup and Distribution

<!-- file: tasks/04-rust-utility-setup.md -->
<!-- version: 1.0.0 -->
<!-- guid: 34567890-3456-3456-3456-345678901cde -->

## Overview

Ensure the `copilot-agent-util` Rust utility is properly available, documented, and distributed across all repositories. This utility is critical for consistent task execution and logging.

## Critical Instructions

**NEVER edit README.md, CHANGELOG.md, TODO.md or other documentation files directly. ALWAYS use:**
- `scripts/create-doc-update.sh` for documentation updates
- `scripts/create-issue-update.sh` for issue updates
- This prevents merge conflicts between multiple AI agents

**ALWAYS follow the VS Code task priority:**
1. Use VS Code tasks first (via `run_task` tool)
2. Use `copilot-agent-util` / `copilot-agent-utilr`
3. Manual terminal commands only as last resort

## Rust Utility Instructions

<!-- file: .github/instructions/rust-utility.instructions.md -->
<!-- version: 1.1.0 -->
<!-- guid: 8e9f0a1b-2c3d-4e5f-6a7b-8c9d0e1f2a3b -->

---
applyTo: "**/*.rs"
description: |
  Rust language-specific coding, documentation, and testing rules for the copilot-agent-util project. These rules extend the general instructions and implement Rust best practices.
---

# Rust Utility Coding Instructions

## Core Principles

- Follow the [general coding instructions](general-coding.instructions.md)
- Follow [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- Use Rust 1.70.0 or higher
- Prioritize safety, performance, and ergonomics

## Copilot Agent Utility

The `copilot-agent-util` is a Rust-based command-line tool that provides enhanced logging, error handling, and automation for VS Code tasks.

### Installation Options

1. **From Source (Recommended for development)**:
   ```bash
   git clone https://github.com/jdfalk/copilot-agent-util-rust
   cd copilot-agent-util-rust
   cargo build --release
   cp target/release/copilot-agent-util /usr/local/bin/
   ```

2. **From Repository Copy**:
   - The utility source is included in `tools/copilot-agent-util-rust/`
   - Build locally: `cd tools/copilot-agent-util-rust && cargo build --release`

3. **Binary Releases**:
   - Download from: https://github.com/jdfalk/copilot-agent-util-rust/releases
   - Available for macOS, Linux, and Windows

### Key Features

- **Enhanced Logging**: All output logged to `logs/` folder with timestamps
- **Error Handling**: Standardized error reporting and debugging information
- **Workspace Awareness**: Runs in correct directory with proper context
- **Task Integration**: Seamless integration with VS Code tasks
- **Args File Support**: Use `--args-file` for complex configurations

### Usage Examples

```bash
# Basic git operations
copilot-agent-util git status
copilot-agent-util git add .
copilot-agent-util git commit -m "message"
copilot-agent-util git push

# With args file
copilot-agent-util --args-file copilot-util-args git status

# Protocol buffer operations
copilot-agent-util buf generate
copilot-agent-util buf lint

# Custom commands
copilot-agent-util exec "find . -name '*.go' -type f"
```

## Required File Header

All Rust files must begin with a standard header:

```rust
// file: path/to/file.rs
// version: 1.0.0
// guid: 123e4567-e89b-12d3-a456-426614174000
```

## Naming Conventions

- Use `snake_case` for variables and functions
- Use `PascalCase` for types and traits
- Use `SCREAMING_SNAKE_CASE` for constants
- Use descriptive names that indicate purpose

## Error Handling

- Use `Result<T, E>` for fallible operations
- Create custom error types using `thiserror`
- Provide meaningful error messages
- Use `?` operator for error propagation

## Documentation

- Document all public items with `///` comments
- Include examples in documentation
- Use `#[doc(hidden)]` for internal implementation details
- Write integration tests demonstrating usage

## Testing

- Unit tests in the same file using `#[cfg(test)]`
- Integration tests in `tests/` directory
- Use descriptive test names
- Test both success and error cases

## Performance

- Use `&str` instead of `String` when possible
- Prefer iterators over loops for functional operations
- Use `Cow<str>` for conditional ownership
- Profile performance-critical code

## Dependencies

- Minimize external dependencies
- Use well-maintained crates from crates.io
- Pin versions in `Cargo.toml`
- Regularly update dependencies for security

## Build Configuration

```toml
[package]
name = "copilot-agent-util"
version = "0.1.0"
edition = "2021"
rust-version = "1.70.0"

[dependencies]
# Minimal set of well-maintained dependencies
```

## Tasks to Complete

### 1. Utility Installation Verification
- [ ] Verify `copilot-agent-util` is available in all repositories
- [ ] Test basic functionality (git, buf commands)
- [ ] Verify logging output is working
- [ ] Check args file configuration

### 2. Documentation Updates
- [ ] Update instructions to reference utility location
- [ ] Add installation guide to main README (use doc update script)
- [ ] Create usage examples and troubleshooting guide
- [ ] Document args file format and usage

### 3. Repository Distribution
- [ ] Ensure utility source is in `tools/` directory
- [ ] Verify build process works from source
- [ ] Test cross-platform compatibility
- [ ] Create installation scripts if needed

### 4. Integration Testing
- [ ] Test with all existing VS Code tasks
- [ ] Verify logging consistency across repositories
- [ ] Test error handling and recovery
- [ ] Validate args file processing

### 5. Performance Optimization
- [ ] Profile execution time for common operations
- [ ] Optimize startup time
- [ ] Reduce memory usage where possible
- [ ] Test with large repositories

## Error Resolution Steps

### Common Issues
1. **Binary not found**: Add to PATH or use full path
2. **Permission denied**: Check executable permissions
3. **Build failures**: Verify Rust version and dependencies
4. **Log file issues**: Check directory permissions

### Debugging
- Check log files in `logs/` directory
- Use `--verbose` flag for detailed output
- Verify current working directory
- Check args file syntax if using

## Expected Deliverables

1. Verified utility installation across all repositories
2. Updated documentation with installation instructions
3. Working examples and troubleshooting guide
4. Integration tests confirming functionality
5. Performance benchmarks and optimization report

## Success Criteria

- [ ] All repositories can use the utility successfully
- [ ] VS Code tasks execute without errors
- [ ] Logging output is consistent and useful
- [ ] Documentation is complete and accurate
- [ ] Build process is reliable and fast
