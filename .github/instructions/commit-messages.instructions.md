<!-- file: .github/instructions/commit-messages.instructions.md -->
<!-- version: 1.0.0 -->
<!-- guid: c0mm1712-e553-4a6e-9f8b-1234567890ab -->

applyTo: "\*\*" description: | Conventional commit message format rules for all
Copilot/AI agents and VS Code Copilot customization. These rules apply to all
git commits and follow the project's commit message standards. For details, see
the main documentation in `.github/copilot-instructions.md`.

---

# Conventional Commit Message Instructions

These instructions are the canonical source for all conventional commit message
formatting rules in this repository. They are used by GitHub Copilot for commit
message generation and follow our established standards.

- Follow the [general coding instructions](general-coding.instructions.md) for
  basic file formatting rules.
- All commit formatting and workflow rules are found in
  `.github/instructions/*.instructions.md` files.
- Document all changes comprehensively in commit messages.
- For agent/AI-specific instructions, see [AGENTS.md](../AGENTS.md) and related
  files.

For more details and the full system, see
[copilot-instructions.md](../copilot-instructions.md).

## Template Structure

**IMPORTANT**: Only include issue numbers if you are working on a specific
GitHub issue. Do not use placeholder numbers like #123.

For commits that address multiple issues, use this multi-issue format:

```text
type(scope): primary description

Brief description of the overall changes and their purpose.

Issues Addressed:

type(scope): description
- path/to/file1.ext - Description of changes
- path/to/file2.ext - Description of changes
- path/to/file3.ext - Description of changes

type(scope): description
- path/to/file4.ext - Description of changes
- path/to/file5.ext - Description of changes

type(scope): description
- path/to/file6.ext - Description of changes
```

For single commits, use the standard format:

```text
type(scope): description

Brief description of what was changed and why.

Files changed:
- [path/to/file1.ext](path/to/file1.ext) - Description of changes
- [path/to/file2.ext](path/to/file2.ext) - Description of changes
```

Only if working on a specific issue, include the issue number:

```text
type(scope): description (#actual-issue-number)

Brief description of what was changed and why.

Files changed:
- [path/to/file1.ext](path/to/file1.ext) - Description of changes
- [path/to/file2.ext](path/to/file2.ext) - Description of changes

Closes #actual-issue-number
```

For commits without a specific issue, omit the issue number entirely:

```text
type(scope): description

Brief description of what was changed and why.

Files changed:
- path/to/file1.ext - Description of changes
- path/to/file2.ext - Description of changes
```

## Guidelines

### Commit Header

- Use conventional commit format: `type(scope): description`
- Include issue number only if working on a specific issue:
  `type(scope): description (#issue-number)`
- Keep the header under 72 characters
- Use present tense ("add feature" not "added feature")
- Be specific and descriptive

### Body Structure

- **Single Issue**: Use "Files changed:" section
- **Multiple Issues**: Use "Issues Addressed:" with subsections
- Group files by the issue they address
- Include brief context about the overall changes

### Conventional Commit Types

- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic changes)
- `refactor`: Code refactoring (no functional changes)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, build changes, etc.
- `perf`: Performance improvements
- `ci`: CI/CD changes
- `build`: Build system changes
- `revert`: Reverting previous commits

### File Documentation

- **Always list every modified file**
- Explain what changed in each file, not just what the file does
- Use relative paths from repository root as markdown links:
  `[path/to/file.ext](path/to/file.ext)`
- Be specific about the nature of changes

### Issue References

- Include issue numbers in the header: `(#123)`
- Use closing keywords in footer: `Closes #123, #456`
- For related issues: `Related to #999`
- Omit issue references if not working on a specific issue

## Examples

### Multi-Issue Commit Example

```text
feat(auth): implement user authentication system (#123)

Added comprehensive authentication system with JWT tokens, profile management,
and updated documentation to support the new auth workflow.

Issues Addressed:

feat(auth): implement JWT token validation (#123)
- [src/middleware/auth.js](src/middleware/auth.js) - JWT validation logic and middleware
- [src/routes/api.js](src/routes/api.js) - Applied auth middleware to protected routes
- [tests/auth.test.js](tests/auth.test.js) - Comprehensive test coverage for auth flow

feat(ui): add user profile page (#456)
- [src/components/UserProfile.jsx](src/components/UserProfile.jsx) - Main profile component with edit functionality
- [src/styles/profile.css](src/styles/profile.css) - Responsive styling for profile page

docs(readme): update installation instructions (#789)
- [README.md](README.md) - Updated installation and auth setup documentation

Closes #123, #456, #789
```

### Single-Issue Commit Example

```text
fix(search): resolve pagination bug in results (#542)

Fixed issue where search results pagination was not properly handling
empty result sets, causing infinite loading states.

Files changed:
- [src/components/SearchResults.jsx](src/components/SearchResults.jsx) - Added null check for empty results
- [src/hooks/useSearchPagination.js](src/hooks/useSearchPagination.js) - Fixed pagination logic for edge cases
- [tests/search.test.js](tests/search.test.js) - Added test coverage for empty result pagination

Closes #542
```

### Simple Commit Example

```text
style(ui): format search component files

Applied prettier formatting to search-related components.

Files changed:
- [src/components/SearchBar.jsx](src/components/SearchBar.jsx) - Code formatting only
- [src/components/SearchResults.jsx](src/components/SearchResults.jsx) - Code formatting only
```

### Breaking Change Example

```text
feat(api)!: restructure user authentication endpoints (#345)

BREAKING CHANGE: Authentication endpoints have been restructured.
The /auth/login endpoint now returns different response format.

Issues Addressed:

feat(api): restructure authentication endpoints (#345)
- [src/routes/auth.js](src/routes/auth.js) - New endpoint structure and response format
- [src/middleware/auth.js](src/middleware/auth.js) - Updated to handle new token format
- [docs/api.md](docs/api.md) - Updated API documentation

Closes #345
```

## Best Practices

### Do

1. **Be specific** - Explain what changed and why
2. **Group by issue** - Keep related changes together
3. **List all files** - Don't leave any modified files undocumented
4. **Use present tense** - "add" not "added"
5. **Reference issues only when working on specific issues** - Don't use
   placeholder numbers
6. **Be consistent** - Follow the format every time

### Don't

1. **Mix unrelated changes** - One commit per logical change set
2. **Use vague descriptions** - "fix stuff" or "update files"
3. **Forget file listings** - Every file should be documented
4. **Use placeholder issue numbers** - Only reference real issues you're working
   on
5. **Use past tense** - Avoid "fixed" or "added"

## Integration with VS Code

Your VS Code settings are configured to use these commit message guidelines.
When generating commit messages with GitHub Copilot, it will follow this format
automatically.

## Atomic Commits

- **One logical change per commit** - Don't mix features, fixes, and docs
- **Complete changes** - Don't split related files across commits
- **Buildable commits** - Each commit should leave the code in a working state
- **Issue-focused** - Group files by the issue they address, not by file type
