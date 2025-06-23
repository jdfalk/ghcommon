# Conventional Commits Guide

## Format

Use this template for your conventional commits:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Types

Use these standardized types to categorize your changes:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Changes that don't affect code meaning (formatting, white-space, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `test`: Adding or modifying tests
- `build`: Changes to build system or external dependencies
- `ci`: Changes to CI configuration and scripts
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit

## Description Guidelines

- Use imperative, present tense ("add" not "added" or "adds")
- Don't capitalize first letter
- No period at the end
- Keep descriptions concise (50 chars or less)
- Be specific and clear about what changed
- Avoid vague terms like "fixes" or "updates" without context
- Ensure commit messages are formatted consistently

## File Changes Documentation (REQUIRED)

- **ALWAYS list ALL files that were changed in the body of the commit message**
- Format each file listing with a brief summary of what changed, followed by a markdown link
- Use bullet points for listing multiple files
- Example:

  ```markdown
  Files changed:

  - Added SSO provider implementation: [src/auth/SSOProvider.js](src/auth/SSOProvider.js)
  - Updated auth context to support SSO flow: [src/auth/AuthContext.js](src/auth/AuthContext.js)
  - Added SSO login button to form: [src/components/LoginForm.js](src/components/LoginForm.js)
  ```

- For repository links, use the full URL format: `Summary: [file.js](https://github.com/owner/repo/blob/branch/file.js)`
- Include a clear, concise summary of what changed in each file
- No commit should be submitted without this file change documentation

## Body Guidelines

- Use imperative, present tense
- Include motivation for the change
- Contrast with previous behavior
- Use blank line to separate from description
- Wrap at 72 characters
- Summarize the commits as the first line
- **Always include a "Files changed:" section with a summary and markdown links for all modified files**
- Organize file changes by type (added, modified, deleted) when appropriate

## Footer Guidelines

- Use for referencing ACTUAL issues: `Fixes #123` or `Closes #456`
- Never reference fictional issue numbers - only include references to real issues
- Breaking changes must start with `BREAKING CHANGE:` followed by explanation
- Reference ticket numbers as: `[#123]` or specific project format

## Breaking Changes

Indicate breaking changes either:

- With `!` after type/scope: `feat(api)!: remove deprecated endpoints`
- In footer: `BREAKING CHANGE: environment variables now use different naming convention`

## Scope Guidelines

- Use consistent scope names throughout the project
- Keep scopes lowercase
- Use short nouns describing the affected component
- Common scopes: api, auth, core, ui, config, etc.

## Special Instructions

- For multi-line commit messages, ensure proper formatting with `-m` flag or by writing in commit editor
- Never add issue references unless they're for actual issues in your project

## Examples

> **Note:** The examples below show the format - replace issue numbers with actual issues from your project or omit the reference entirely.

```text
feat(auth): add SSO login option

Implement single sign-on login functionality using OAuth2

Files changed:
- Added SSO provider implementation: [src/auth/SSOProvider.js](https://github.com/jdfalk/gcommon/blob/main/src/auth/SSOProvider.js)
- Updated auth context to support SSO flow: [src/auth/AuthContext.js](https://github.com/jdfalk/gcommon/blob/main/src/auth/AuthContext.js)
- Added SSO login button to form: [src/components/LoginForm.js](https://github.com/jdfalk/gcommon/blob/main/src/components/LoginForm.js)

Closes #ISSUE_NUMBER  # Only include if there's an actual issue
```

```text
fix(api): prevent race condition in user creation

The previous implementation allowed concurrent requests to create
duplicate users with the same email address.

Files changed:
- Added database locking mechanism: [src/api/userController.js](https://github.com/jdfalk/gcommon/blob/main/src/api/userController.js)
- Enhanced email validation logic: [src/services/validation.js](https://github.com/jdfalk/gcommon/blob/main/src/services/validation.js)

Fixes #ISSUE_NUMBER  # Only include if there's an actual issue
```

```text
docs: update README with new API endpoints

Files changed:
- Added new endpoints documentation: [README.md](https://github.com/jdfalk/gcommon/blob/main/README.md)
- Created detailed API reference: [docs/API.md](https://github.com/jdfalk/gcommon/blob/main/docs/API.md)
```

```text
feat(api)!: change response format to JSON API spec

BREAKING CHANGE: API responses now follow JSON API specification.
Clients will need to update their parsers.

Files changed:
- Implemented JSON API formatter: [src/api/responseFormatter.js](https://github.com/jdfalk/gcommon/blob/main/src/api/responseFormatter.js)
- Updated middleware to use new format: [src/middleware/apiResponse.js](https://github.com/jdfalk/gcommon/blob/main/src/middleware/apiResponse.js)
- Adjusted tests for new response structure: [tests/api/responses.test.js](https://github.com/jdfalk/gcommon/blob/main/tests/api/responses.test.js)
```

```text
refactor(core): simplify error handling logic

Files changed:
- Consolidated error handlers: [src/core/errorHandler.js](https://github.com/jdfalk/gcommon/blob/main/src/core/errorHandler.js)
- Created reusable error utilities: [src/utils/errors.js](https://github.com/jdfalk/gcommon/blob/main/src/utils/errors.js)
```
