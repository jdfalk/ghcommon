<!-- file: .github/copilot-instructions.md -->
<!-- version: 1.1.1 -->
<!-- guid: 7a8b9c1d-2e3f-4a5b-6c7d-8e9f0a1b2c3d -->

# Copilot Instructions

## File Identification

- Always check the first line of a file for a comment in the format `# file: $(relative_path_to_file)`
- Use this path to determine which file you're working on and where to apply generated changes
- If this comment is present, prioritize it over any other indications of file path
- When generating code modifications, reference this path in your response
- Always ensure every file begins with the standard header, using the correct comment syntax for the file type (e.g., `# file: ...` for Python, `// file: ...` for Go, `<!-- file: ... -->` for Markdown, etc.).
- The header must include:
  - The exact relative file path from the repository root (e.g., `# file: path/to/file.py`)
  - The file's semantic version (e.g., `# version: 1.0.0`)
  - The file's GUID (e.g., `# guid: 123e4567-e89b-12d3-a456-426614174000`)
- If this header is present, always use it to determine the file's identity and where to apply changes. Prioritize this over any other indications of file path.
- When generating code modifications, reference the file path from this header in your response.

## Code Documentation

- Always extensively document functions with parameters, return values, and purpose
- Always extensively document methods with parameters, return values, and purpose
- Always extensively document classes with their responsibilities and usage patterns
- Always document tests with clear descriptions of what's being tested and expected outcomes
- Always escape triple backticks with a backslash in documentation
- Use consistent documentation style (JSDoc, docstrings, etc.) based on the codebase

## Markdown Formatting Guidelines

- **Before manually fixing markdown issues, always use Prettier first**
- Check for a VS Code task or run `prettier --write *.md` to format markdown files
- If a Prettier task exists in `.vscode/tasks.json`, use it instead of manual formatting
- After running Prettier, only manually fix remaining issues that Prettier cannot resolve
- If no Prettier setup exists, ask the user to run Prettier formatting first, then fix remaining issues
- Focus manual fixes on content structure, not formatting that automated tools can handle

## Documentation Organization Policy

### File Responsibilities

- **README.md**: Repository introduction, setup instructions, basic usage, and immediate critical information new users need. Include major breaking changes at the top temporarily for visibility.
- **TODO.md**: Project roadmap, planning, implementation status, architectural decisions, reasoning behind choices, diagrams, and detailed technical plans.
- **CHANGELOG.md**: All version information, release notes, major breaking changes, feature additions, bug fixes, and consolidated technical documentation that would otherwise be scattered across multiple files.

## Go Code Style (Primary Language)

- Use `gofmt` or `go fmt` to automatically format code
- Use tabs for indentation (not spaces), line length under 100 characters
- Package names: short, concise, lowercase, no underscores (`strconv`, not `string_converter`)
- Interface names: use -er suffix for interfaces describing actions (`Reader`, `Writer`)
- Variable/function names: use MixedCaps or mixedCaps, not underscores
- Exported (public) names: must begin with a capital letter (`MarshalJSON`)
- Unexported (private) names: must begin with a lowercase letter (`marshalState`)
- Acronyms in names should be all caps (`HTTPServer`, not `HttpServer`)
- Group imports: standard library, third-party packages, your project's packages
- All exported declarations should have doc comments starting with the name
- Always check errors, return errors rather than using panic
- Use early returns to reduce nesting
- Defer file and resource closing
- Use context for cancellation and deadlines
- Keep functions short and focused
- Prefer methods with value receivers unless you need to modify the receiver
- Use channels to communicate, avoid sharing memory

## Python Code Style

- Use 4 spaces for indentation (no tabs)
- Maximum line length of 80 characters
- Import order: standard library, third-party, application-specific
- One import per line, no wildcard imports
- Naming: `module_name`, `ClassName`, `method_name`, `CONSTANT_NAME`, `_private_attribute`
- Use docstrings for all public modules, functions, classes, and methods
- Follow PEP 8 standards
- Use type hints where applicable
- Prefer list comprehensions over loops where readable

## TypeScript/JavaScript Code Style

- Use 2 spaces for indentation
- Use semicolons consistently
- Prefer `const` over `let`, avoid `var`
- Use meaningful variable names, prefer descriptive over short
- Use PascalCase for classes, camelCase for functions/variables
- Use UPPER_SNAKE_CASE for constants
- Always use explicit type annotations in TypeScript
- Prefer interfaces over types for object shapes
- Use async/await over promises where possible

## Markdown Code Style

- Use consistent heading hierarchy (don't skip levels)
- Use fenced code blocks with language specification
- Keep line length reasonable (80-100 characters)
- Use meaningful link text (not "click here")
- Use consistent bullet point style (-, not \*)
- Add blank lines around code blocks and headers

## Commit Message Standards (REQUIRED)

Format: `<type>[optional scope]: <description>`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**REQUIRED**: Always include "Files changed:" section in commit body with summary and links:

```
Files changed:
- Added subtitle processing: [cmd/convert.go](cmd/convert.go)
- Updated web UI handler: [webui/handlers.go](webui/handlers.go)
```

- Use imperative present tense ("add" not "added")
- Don't capitalize first letter of description
- No period at end of description
- Keep descriptions under 50 characters
- Include motivation and contrast with previous behavior in body
- Reference real issues only: `Fixes #123` or `Closes #456`

## Testing Standards

- Follow Arrange-Act-Assert pattern in tests
- Use descriptive test names: `test[UnitOfWork_StateUnderTest_ExpectedBehavior]`
- Test one specific behavior per test case
- Mock external dependencies
- Cover both happy paths and edge cases
- Write deterministic tests with consistent results
- Keep tests independent of each other
- Include meaningful assertion messages
- Use table-driven tests in Go when testing multiple scenarios

Test Types:

- **Unit Tests**: Single function/method in isolation
- **Integration Tests**: Component interactions
- **Functional Tests**: Complete features from user perspective
- **Performance Tests**: Response times and resource usage
- **Security Tests**: Vulnerabilities and safeguards

## Code Review Guidelines

Review Priority Areas:

1. **Correctness**: Verify code does what it claims, check edge cases and error handling
2. **Security**: Look for injection vulnerabilities, auth/authorization, secure data handling
3. **Performance**: Check for N+1 queries, resource-intensive operations, scalability issues
4. **Readability**: Naming conventions, comments for complex logic, code organization
5. **Maintainability**: Code duplication, SOLID principles, modular components
6. **Test Coverage**: Unit tests for main functionality, edge cases, meaningful tests

Review Process:

- Start with high-level overview before details
- Be specific about what needs changing and why
- Provide constructive feedback with examples
- Differentiate between required changes and suggestions
- Focus on critical issues first, not style issues handled by linters
- Review tests as carefully as production code

## Security & Best Practices

- Avoid hardcoding sensitive information (API keys, passwords, tokens)
- Follow secure coding practices
- Use proper error handling with meaningful messages
- Validate inputs appropriately (sanitize file paths, validate formats)
- Consider performance implications of code changes
- Look for injection vulnerabilities (command injection in file processing)
- Review file handling security (path traversal, file size limits)
- Verify secure handling of subtitle file content
- Check input validation for subtitle formats and encodings
- Use secure defaults for file permissions and temporary files

## Subtitle Manager Specific Guidelines

- Handle subtitle file encoding detection properly (UTF-8, UTF-16, etc.)
- Validate subtitle file formats before processing
- Use appropriate error handling for file I/O operations
- Consider memory usage when processing large subtitle files
- Implement proper cleanup of temporary files
- Use streaming for large file operations when possible
- Follow established patterns for subtitle format detection
- Ensure thread-safety in concurrent subtitle processing
- Validate time codes and subtitle sequence integrity
- Handle malformed subtitle files gracefully

## Version Control Standards

- Write clear commit messages that explain the purpose of changes
- Keep pull requests focused on a single feature or fix
- Reference issue numbers in commits and PRs when applicable (only real issues)
- Use conventional commit format consistently
- Include comprehensive file change documentation in all commits
- Use semantic versioning for releases
- Tag releases appropriately

## Project-Specific Guidelines

- Import from project modules rather than duplicating functionality
- Respect the established architecture patterns
- Before suggesting one-off commands, first check if there's a defined task in tasks.json that can accomplish the same goal
- Follow the documentation organization policy for file responsibilities
- Use meaningful variable names that indicate purpose
- Keep functions small and focused on a single responsibility
- Use the existing CLI framework patterns for new commands
- Follow established patterns for web UI handlers and templates
- Use appropriate logging levels and structured logging

## Includes

For additional detailed guidelines, refer to these comprehensive style and process documents:

### Code Style Guidelines

- [Go Code Style](code-style-go.md)
- [Python Code Style](code-style-python.md)
- [TypeScript Code Style](code-style-typescript.md)
- [JavaScript Code Style](code-style-javascript.md)
- [Markdown Code Style](code-style-markdown.md)
- [Protobuf Code Style](code-style-protobuf.md)
- [GitHub Actions Code Style](code-style-github-actions.md)

### Development Process Guidelines

- [Commit Message Standards](commit-messages.md)
- [Pull Request Descriptions](pull-request-descriptions.md)
- [Code Review Guidelines](review-selection.md)
- [Test Generation Guidelines](test-generation.md)

## Code Documentation Guidelines

### Development Workflow Instructions

1. **Write the code first** - Focus on implementing the core functionality and logic
2. **Complete the implementation** - Ensure all features and requirements are fully implemented
3. **Run formatting tools** - Apply code formatters (e.g., Prettier, Black, gofmt) to standardize code style
4. **Run linting tools** - Execute linters (e.g., ESLint, pylint, golint) to catch potential issues
5. **Fix linting issues** - Address any warnings or errors identified by the linter

### Important Notes

- Prioritize getting functional code written before worrying about style and linting rules
- Only address linting issues during development if they represent major errors that prevent further development
- Minor style and linting issues should be resolved at the end of the development process
- This approach allows for faster development iteration and reduces interruptions during the coding phase
