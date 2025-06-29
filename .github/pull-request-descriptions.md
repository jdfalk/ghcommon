# Pull Request Description Guidelines

## Structure

Use this template for your pull request descriptions:

```markdown
## Description

[Concise overview of the changes]

## Motivation

[Why these changes were necessary]

## Changes

[Detailed list of changes made]

## Testing

[How the changes were tested]

## Screenshots

[If applicable]

## Related Issues

[Links to related tickets/issues]
```

## Description Guidelines

- Keep it concise but informative (1-3 sentences)
- Focus on the "what" and "why" not just the "how"
- Use present tense ("add feature" not "added feature")
- Avoid jargon unless necessary for technical clarity

## Motivation Section Guidelines

- Explain why changes were needed
- Reference business goals or user needs when appropriate
- Link to design documents or specifications when available
- Provide context for reviewers who may not be familiar with the problem

## Changes Section Guidelines

- Use bullet points for multiple changes
- Be specific about what was changed
- Group related changes together
- Include both code changes and any workflow/process changes
- Highlight architectural decisions or tradeoffs made

## Testing Section Guidelines

- Describe how changes were tested (unit tests, integration tests, manual testing)
- Include test coverage information if available
- Note edge cases that were specifically tested
- Mention any testing tools or environments used

## Screenshots Guidelines

- Include before/after screenshots for UI changes
- Use annotations or highlights to point out specific changes
- Include mobile/responsive views if applicable
- Use GIFs or videos for demonstrating interactions or animations

## Related Issues Guidelines

- Use the format: `Closes #123`, `Fixes #456`, or `Related to #789`
- Link to all relevant issues/tickets
- If applicable, link to design documents or specifications

## Special Cases

- For breaking changes, include a "Breaking Changes" section with migration instructions
- For performance improvements, include benchmark results
- For security fixes, note the severity and impact
- For dependency updates, include rationale and any potential impacts

## Best Practices

- Keep the PR focused on a single feature or fix
- Avoid mixing unrelated changes
- Respond to review comments promptly
- Update the description if significant changes occur during review
- Tag appropriate reviewers based on areas of expertise
- Use the PR template provided by the repository when available

## Examples

```markdown
## Description

Add JWT authentication to the API endpoints

## Motivation

Our API currently uses basic authentication which doesn't meet security requirements for the new client portal.

## Changes

- Added JWT middleware to authenticate API requests
- Created token generation endpoint at `/api/auth/token`
- Updated user model to store refresh tokens
- Added environment variables for JWT secret and expiration

## Testing

- Added unit tests for token generation and validation
- Tested integration with frontend using Postman collection
- Verified token expiration and refresh flow

## Related Issues

Closes #234
Related to #156
```
