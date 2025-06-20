# AI Automation Instructions

This document provides comprehensive guidelines for AI-driven development work in this repository.

## Git Operations

### Rebasing

When rebasing branches, use these commands and adapt to merge conflicts:

```shell
branch=$(git rev-parse --abbrev-ref HEAD) && \
upstream=$(git config --get branch."$branch".remote || git remote | head -n1) && \
git stash push -u -m "auto-stash before rebase" && \
git pull --rebase "$upstream" main && \
if git ls-remote --exit-code --heads "$upstream" "$branch" > /dev/null 2>&1; then \
  git push --force-with-lease; \
else \
  git push -u "$upstream" "$branch"; \
fi && \
git stash pop
```

### Commit Messages

Follow conventional commits format with **mandatory file change documentation**:

```text
<type>[optional scope]: <description>

[optional body explaining motivation and changes]

Files changed:
- Summary of change: [file.ext](relative/path/to/file.ext)
- Another change summary: [file2.ext](relative/path/to/file2.ext)

[optional footer with issue references]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Rules:**
- Use imperative, present tense ("add" not "added")
- Keep description under 50 characters
- **ALWAYS include "Files changed:" section** with summaries and links
- Only reference real issues, never fictional ones
- Use `!` or `BREAKING CHANGE:` for breaking changes

## GitHub Issues Management

### Issue Workflow

When working on GitHub issues:

1. **Label the issue** with `codex` to indicate AI work in progress
2. **Add a comment** explaining your plan of action
3. **Reference the issue** in PR comments and commits
4. **Update issue status** as work progresses

### Issue Updates Format

Use the `issue_updates.json` file with grouped format:

```json
{
  "create": [
    {
      "title": "Issue Title",
      "body": "Detailed description with context",
      "labels": ["label1", "label2"],
      "assignees": ["username"],
      "milestone": 1,
      "guid": "create-unique-id-2025-06-20"
    }
  ],
  "update": [
    {
      "number": 123,
      "labels": ["codex", "in-progress"],
      "guid": "update-issue-123-2025-06-20"
    }
  ],
  "comment": [
    {
      "number": 123,
      "body": "## Plan of Action\n\n1. Analyze the problem\n2. Implement solution\n3. Add tests\n4. Update documentation",
      "guid": "plan-comment-123-2025-06-20"
    }
  ],
  "close": [
    {
      "number": 123,
      "state_reason": "completed",
      "guid": "close-issue-123-2025-06-20"
    }
  ],
  "delete": [
    {
      "number": 999,
      "guid": "delete-issue-999-2025-06-20"
    }
  ]
}
```

## Pull Request Guidelines

### PR Description Structure

```markdown
## Description
[Concise overview of changes - what and why]

## Motivation
[Why these changes were necessary - business context]

## Changes
- Specific change 1
- Specific change 2
- Architectural decisions made

## Testing
[How changes were tested - unit, integration, manual]

## Screenshots
[For UI changes - before/after, mobile views]

## Related Issues
Closes #123
Fixes #456
Related to #789
```

### PR Best Practices

- Keep PRs focused on single feature/fix
- Respond to review comments promptly
- Update description if significant changes occur
- Tag appropriate reviewers
- Include breaking change migrations if applicable

## Code Review Guidelines

### Review Focus Areas (Priority Order)

1. **Correctness** - Does it work as intended?
2. **Security** - Any vulnerabilities or data exposure?
3. **Performance** - Scalability and efficiency concerns?
4. **Readability** - Clear naming and structure?
5. **Maintainability** - Future-proof and modular?
6. **Test Coverage** - Adequate and meaningful tests?

### Review Comment Standards

- Be specific about required changes
- Explain **why** changes are needed, not just what
- Provide constructive feedback with examples
- Differentiate between required changes and suggestions
- Ask questions for clarification when needed

## Code Documentation Standards

### Function/Method Documentation

```javascript
/**
 * Processes subtitle files and converts them to target format
 * @param {string} inputPath - Path to the source subtitle file
 * @param {string} outputPath - Destination path for converted file
 * @param {Object} options - Configuration options
 * @param {string} options.format - Target format (srt, vtt, ass)
 * @param {boolean} options.preserveTimings - Whether to keep original timings
 * @returns {Promise<ConversionResult>} Result object with success status and metadata
 * @throws {ValidationError} When input file format is unsupported
 */
async function convertSubtitles(inputPath, outputPath, options = {}) {
  // Implementation...
}
```

### Class Documentation

```javascript
/**
 * Manages subtitle provider integrations and download operations
 * 
 * This class handles authentication, rate limiting, and retry logic
 * for various subtitle providers like OpenSubtitles, Subscene, etc.
 * 
 * @example
 * const manager = new SubtitleProviderManager({
 *   apiKey: 'your-key',
 *   retryAttempts: 3
 * });
 * 
 * const subtitles = await manager.search('Movie Title', 'en');
 */
class SubtitleProviderManager {
  // Implementation...
}
```

## File Identification and Organization

### File Header Comments

Always include file identification in the first line:

```javascript
// file: src/components/SubtitlePlayer.jsx
```

```python
# file: scripts/convert_subtitles.py
```

```markdown
<!-- file: docs/API.md -->
```

### Documentation Organization

- **README.md**: Repository introduction, setup, basic usage, critical info
- **TODO.md**: Project roadmap, implementation status, architectural decisions
- **CHANGELOG.md**: Version history, breaking changes, technical documentation

## Security and Best Practices

### Security Checklist

- [ ] No hardcoded secrets or API keys
- [ ] Input validation for all user data
- [ ] Proper authentication and authorization
- [ ] SQL injection prevention
- [ ] XSS protection for web interfaces
- [ ] Secure dependency management

### Code Quality Standards

- Use meaningful variable and function names
- Keep functions small and focused (single responsibility)
- Prefer explicit type annotations where applicable
- Follow established project patterns and conventions
- Write comprehensive tests for new functionality
- Handle errors gracefully with proper logging

## Testing Requirements

### Test Coverage Standards

- Unit tests for all business logic
- Integration tests for component interactions
- Edge case and error condition testing
- Performance tests for critical paths
- End-to-end tests for user workflows

### Test Documentation

```javascript
describe('SubtitleConverter', () => {
  describe('convertToSRT', () => {
    it('should convert VTT subtitle format to SRT with proper timing adjustment', async () => {
      // Test implementation...
    });
    
    it('should handle malformed timestamp formats gracefully', async () => {
      // Test implementation...
    });
  });
});
```

## Project-Specific Guidelines

### Architecture Patterns

- Import from project modules rather than duplicating functionality
- Respect established architecture patterns
- Check for existing tasks in `tasks.json` before suggesting commands
- Follow the Universal Tagging System for entity management
- Use the unified issue management workflow for GitHub operations

### Development Workflow

1. **Check existing tasks** in VS Code tasks before running terminal commands
2. **Use unified workflows** for issue management, testing, and deployment
3. **Follow the established provider pattern** for new integrations
4. **Maintain backward compatibility** unless breaking changes are documented
5. **Update documentation** alongside code changes

## Error Handling and Logging

### Error Handling Patterns

```javascript
try {
  const result = await riskyOperation();
  return { success: true, data: result };
} catch (error) {
  logger.error('Operation failed', { 
    operation: 'riskyOperation',
    error: error.message,
    stack: error.stack 
  });
  
  return { 
    success: false, 
    error: 'Operation failed. Please try again.' 
  };
}
```

### Logging Standards

- Use structured logging with context
- Include operation names and relevant metadata
- Log errors with full stack traces
- Use appropriate log levels (debug, info, warn, error)
- Avoid logging sensitive information

## Performance Considerations

### Performance Checklist

- [ ] Avoid N+1 database queries
- [ ] Implement appropriate caching strategies
- [ ] Use pagination for large datasets
- [ ] Optimize database queries with proper indexes
- [ ] Consider memory usage for large file operations
- [ ] Profile performance-critical code paths

### Scalability Guidelines

- Design for horizontal scaling where possible
- Use asynchronous operations for I/O-bound tasks
- Implement proper resource cleanup
- Consider rate limiting for external API calls
- Monitor resource usage and set appropriate limits
