# Code Review Guidelines

## Review Focus Areas

When reviewing code, prioritize these areas:

```markdown
1. Correctness
2. Security
3. Performance
4. Readability
5. Maintainability
6. Test Coverage
```

## Correctness Guidelines

- Verify the code does what it claims to do
- Check edge cases and error handling
- Ensure compatibility with existing systems
- Validate business logic implementation
- Look for off-by-one errors, null references, and other common bugs

## Security Guidelines

- Look for injection vulnerabilities (SQL, XSS, CSRF)
- Review authentication and authorization checks
- Check for secure handling of sensitive data
- Verify input validation and output encoding
- Examine cryptographic implementations
- Identify potential security risks in dependencies

## Performance Guidelines

- Look for N+1 queries and excessive database calls
- Review resource-intensive operations
- Check for unnecessary computations or memory usage
- Identify potential bottlenecks or scalability issues
- Verify appropriate caching strategies

## Readability Guidelines

- Check naming conventions for clarity and consistency
- Verify appropriate comments for complex logic
- Look for code organization and structure
- Check for consistent coding style
- Ensure documentation is up-to-date

## Maintainability Guidelines

- Look for code duplication that could be refactored
- Check for adherence to SOLID principles
- Review for modular, reusable components
- Ensure appropriate abstraction levels
- Verify backward compatibility considerations

## Test Coverage Guidelines

- Verify unit tests cover the main functionality
- Check integration tests for component interactions
- Look for tests of edge cases and error conditions
- Ensure tests are meaningful, not just for coverage
- Verify mocks and stubs are appropriate

## Review Comment Guidelines

- Be specific about what needs changing
- Explain why a change is needed, not just what
- Provide constructive feedback with examples
- Differentiate between required changes and suggestions
- Ask questions when something isn't clear

## Review Process

- Start with a high-level overview before diving into details
- Use a checklist approach to ensure comprehensive review
- Focus on the most critical issues first
- Don't nitpick on style issues that should be handled by linters
- Consider the context and constraints of the changes
- Review tests as carefully as production code

## Special Considerations

- For UI changes, check accessibility and responsiveness
- For API changes, verify documentation and versioning
- For database changes, review migration plans and data integrity
- For security-sensitive code, apply extra scrutiny
- For performance-critical sections, request benchmarks

## Best Practices

- Review smaller chunks of code more frequently
- Use automated tools to catch common issues
- Be respectful and assume positive intent
- Focus on the code, not the author
- Acknowledge good practices and clever solutions
- Follow up on suggested changes in subsequent reviews
- Take time to understand the code rather than rushing
- Consider pairing for complex reviews
