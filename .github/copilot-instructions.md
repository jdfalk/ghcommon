# file: README.md

# Copilot Instructions

## File Identification

- Always check the first line of a file for a comment in the format `# file: $(relative_path_to_file)`
- Use this path to determine which file you're working on and where to apply generated changes
- If this comment is present, prioritize it over any other indications of file path
- When generating code modifications, reference this path in your response

## Code Documentation

- Always extensively document functions with parameters, return values, and purpose
- Always extensively document methods with parameters, return values, and purpose
- Always extensively document classes with their responsibilities and usage patterns
- Always document tests with clear descriptions of what's being tested and expected outcomes
- Always escape triple backticks with a backslash in documentation
- Use consistent documentation style (JSDoc, docstrings, etc.) based on the codebase

## Documentation Organization Policy

### File Responsibilities

- **README.md**: Repository introduction, setup instructions, basic usage, and immediate critical information new users need. Include major breaking changes at the top temporarily for visibility.
- **TODO.md**: Project roadmap, planning, implementation status, architectural decisions, reasoning behind choices, diagrams, and detailed technical plans.
- **CHANGELOG.md**: All version information, release notes, major breaking changes, feature additions, bug fixes, and consolidated technical documentation that would otherwise be scattered across multiple files.

## Go Code Style

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

## Commit Message Standards (REQUIRED)

Format: `<type>[optional scope]: <description>`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**REQUIRED**: Always include "Files changed:" section in commit body with summary and links:
```
Files changed:
- Added feature implementation: [src/feature.js](src/feature.js)
- Updated tests: [test/feature.test.js](test/feature.test.js)
```

- Use imperative present tense ("add" not "added")
- Don't capitalize first letter of description
- No period at end of description
- Keep descriptions under 50 characters
- Include motivation and contrast with previous behavior in body

## Testing Standards

- Follow Arrange-Act-Assert pattern in tests
- Use descriptive test names: `test[UnitOfWork_StateUnderTest_ExpectedBehavior]`
- Test one specific behavior per test case
- Mock external dependencies
- Cover both happy paths and edge cases
- Write deterministic tests with consistent results
- Keep tests independent of each other
- Include meaningful assertion messages

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

## Security & Best Practices

- Avoid hardcoding sensitive information
- Follow secure coding practices
- Use proper error handling with meaningful messages
- Validate inputs appropriately
- Consider performance implications of code changes
- Look for injection vulnerabilities (SQL, XSS, CSRF)
- Review authentication and authorization checks
- Verify secure handling of sensitive data
- Check input validation and output encoding

## Version Control Standards

- Write clear commit messages that explain the purpose of changes
- Keep pull requests focused on a single feature or fix
- Reference issue numbers in commits and PRs when applicable (only real issues)
- Use conventional commit format consistently
- Include comprehensive file change documentation in all commits

## Project-Specific Guidelines

- Import from project modules rather than duplicating functionality
- Respect the established architecture patterns
- Before suggesting one-off commands, first check if there's a defined task in tasks.json that can accomplish the same goal
- Follow the documentation organization policy for file responsibilities
- Use meaningful variable names that indicate purpose
- Keep functions small and focused on a single responsibility

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
