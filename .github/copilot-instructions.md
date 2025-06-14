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

## Code Style

- Follow the established code style in the repository
- Use consistent naming conventions for variables, functions, and classes
- Prefer explicit type annotations where applicable
- Keep functions small and focused on a single responsibility
- Use meaningful variable names that indicate purpose
- Refer to language-specific style guidelines in `.github/code-style-*.md` files which override these general guidelines when conflicts occur

## Testing

- Write comprehensive tests for new functionality
- When updating tests, update the documentation to maintain consistency
- Follow test naming conventions used in the codebase
- Include edge cases and error handling in tests
- Maintain test coverage when modifying existing code
- Follow additional testing guidelines specified in `.github/testing-*.md` files which override these general guidelines when conflicts occur

## Security & Best Practices

- Avoid hardcoding sensitive information
- Follow secure coding practices
- Use proper error handling
- Validate inputs appropriately
- Consider performance implications of code changes

## Version Control

- Write clear commit messages that explain the purpose of changes
- Keep pull requests focused on a single feature or fix
- Reference issue numbers in commits and PRs when applicable
- Follow commit message guidelines specified in `.github/commit-messages-*.md` files which override these general guidelines when conflicts occur

## Project-Specific

- Import from project modules rather than duplicating functionality
- Respect the established architecture patterns
- Before suggesting one-off commands, first check if there's a defined task in tasks.json that can accomplish the same goal
