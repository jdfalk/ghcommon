# JavaScript Code Style Guide

This guide follows Google's JavaScript Style Guide.

## File Structure

- Use `camelCase` for file names
- Each file should contain exactly one ES module
- Prefer ES6 modules (`import`/`export`) over other module systems

## Formatting

- Use 2 spaces for indentation
- Line length maximum of 80 characters
- Use semicolons to terminate statements
- Use single quotes for string literals
- Add trailing commas for multi-line object/array literals
- Use parentheses only where required for clarity or priority

## Naming Conventions

- `functionNamesLikeThis`
- `variableNamesLikeThis`
- `ClassNamesLikeThis`
- `EnumNamesLikeThis`
- `methodNamesLikeThis`
- `CONSTANT_VALUES_LIKE_THIS`
- `private_values_with_underscore` (convention only)
- `package-names-like-this`

## Comments

- Use JSDoc for documentation
- Comment all non-obvious code sections

```javascript
/**
 * Fetches data from the given URL.
 * @param {string} url The URL to fetch from
 * @param {Object=} options Request options
 * @return {Promise<Object>} The JSON response
 */
async function fetchData(url, options = {}) {
  // Implementation
}
```

## Language Features

- Use `const` and `let` instead of `var`
- Use arrow functions for anonymous functions, especially callbacks
- Use template literals instead of string concatenation
- Use object/array destructuring where it improves readability
- Use default parameters instead of conditional statements
- Use spread operator and rest parameters where appropriate

## ES6+ Features to Use

- Classes with appropriate inheritance patterns
- Modules with explicit imports and exports
- Promises and async/await for asynchronous operations
- Iterators and generators where appropriate
- Map and Set for complex data structures

## Best Practices

- Avoid using the global scope
- Avoid deeply nested code blocks
- Use early returns to reduce nesting
- Limit line length to improve readability
- Separate logic and display concerns

## Error Handling

- Always handle Promise rejections
- Use try/catch blocks appropriately
- Provide useful error messages

## Testing

- Write unit tests for all code
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

## Tools

- ESLint for code linting
- Prettier for code formatting
- Configure tools to match Google's JavaScript Style Guide
