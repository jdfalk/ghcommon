<!-- file: copilot/code-style-markdown.md -->
<!-- version: 1.0.0 -->
<!-- guid: e2f8a5b1-9c4d-4e2f-8a5b-4d9c8a5b1e2f -->

# Markdown Coding Style Guide

This guide provides comprehensive guidelines for writing clean, consistent Markdown documents following industry best practices and accessibility standards.

## File Structure and Organization

### File Naming

- Use lowercase letters and hyphens: `user-guide.md`, `api-reference.md`
- Be descriptive and specific: `installation-guide.md` not `guide.md`
- Use `.md` extension for Markdown files

### Document Structure

- Start with a single H1 heading (document title)
- Use hierarchical heading structure (H1 → H2 → H3)
- Include table of contents for long documents
- End with references/links section if applicable

## Heading Guidelines

### Heading Hierarchy

- **H1 (`#`)**: Document title only (one per document)
- **H2 (`##`)**: Major sections
- **H3 (`###`)**: Subsections
- **H4-H6**: Use sparingly for deep nesting

### Heading Format

```markdown
# Document Title

## Major Section

### Subsection

#### Minor Section (use sparingly)
```

### Heading Best Practices

- Use descriptive, specific headings
- Maintain consistent capitalization (Title Case or sentence case)
- Avoid punctuation in headings except question marks
- Keep headings concise but informative

## Text Formatting

### Emphasis and Strong Text

- **Bold text**: `**important**` or `__important__`
- _Italic text_: `*emphasis*` or `_emphasis_`
- Use bold for UI elements, commands, strong emphasis
- Use italics for definitions, foreign words, light emphasis

### Code and Technical Elements

- **Inline code**: Use backticks `code` for variables, functions, file names
- **Code blocks**: Use triple backticks with language specification

````markdown
```python
def hello_world():
    print("Hello, World!")
```
````

````

### Links and References
- **External links**: `[Link text](https://example.com)`
- **Internal links**: `[Section](#section-name)`
- **Reference links**: `[Link text][ref]` with `[ref]: https://example.com` at bottom
- Use descriptive link text, avoid "click here" or "read more"

## Lists and Structure

### Unordered Lists
- Use hyphens (`-`) for consistency
- Maintain proper indentation (2 spaces for sub-items)
- Use parallel structure in list items

```markdown
- First item
- Second item
  - Sub-item one
  - Sub-item two
- Third item
````

### Ordered Lists

- Use numbers with periods: `1.`, `2.`, `3.`
- Can use `1.` for all items (auto-numbering)
- Maintain consistent indentation

```markdown
1. First step
2. Second step
   1. Sub-step one
   2. Sub-step two
3. Third step
```

### Task Lists

- Use for actionable items: `- [ ]` (incomplete), `- [x]` (complete)

```markdown
- [x] Completed task
- [ ] Pending task
- [ ] Another pending task
```

## Tables

### Table Structure

- Use proper alignment with pipes (`|`)
- Include header row with separator
- Align columns consistently

```markdown
| Header 1 | Header 2 | Header 3 |
| -------- | -------- | -------- |
| Row 1    | Data     | More     |
| Row 2    | Data     | More     |
```

### Table Alignment

- Left align: `|:---------|`
- Center align: `|:--------:|`
- Right align: `|---------:|`

### Table Best Practices

- Keep tables simple and readable
- Use tables for tabular data only
- Consider alternatives for complex data
- Ensure tables are responsive/accessible

## Code Documentation

### Code Blocks

- Always specify language for syntax highlighting
- Use descriptive comments in code examples
- Keep examples concise but complete

````markdown
```javascript
// Function to calculate area of a circle
function calculateArea(radius) {
  return Math.PI * radius * radius;
}
```
````

````

### Command Examples
- Use code blocks for multi-line commands
- Use inline code for single commands
- Include expected output when helpful

```markdown
Run the following command:

```bash
npm install --save-dev eslint
````

This will install ESLint as a development dependency.

````

## Images and Media

### Image Syntax
- Use descriptive alt text: `![Alt text](image.png)`
- Include title attributes when helpful: `![Alt text](image.png "Title")`
- Use relative paths for local images

### Image Best Practices
- Optimize images for web (appropriate size/format)
- Provide alt text for accessibility
- Use captions when necessary
- Consider image placement and flow

## Line Length and Whitespace

### Line Length
- Aim for 80-100 characters per line
- Break long lines at natural points (punctuation, conjunctions)
- Consider readability over strict limits

### Whitespace Usage
- One blank line between major sections
- No trailing whitespace at line ends
- Consistent indentation (2 or 4 spaces)
- Single space after periods and other punctuation

## Special Elements

### Blockquotes
- Use for quotes, callouts, or emphasized content
- Maintain proper attribution

```markdown
> This is a blockquote with proper formatting.
> It can span multiple lines.
>
> — Author Name
````

### Horizontal Rules

- Use three hyphens: `---`
- Separate major document sections
- Use sparingly for visual separation

### Footnotes

- Use for additional information or citations
- Format: `Text with footnote[^1]`
- Define at bottom: `[^1]: Footnote content`

## Accessibility Guidelines

### Alt Text

- Provide meaningful descriptions for images
- Describe function/purpose, not just appearance
- Keep alt text concise but descriptive

### Link Text

- Use descriptive link text that makes sense out of context
- Avoid generic phrases like "click here"
- Indicate if link opens external site or downloads file

### Structure

- Use proper heading hierarchy for screen readers
- Ensure logical document flow
- Use lists for grouped information

## Validation and Quality

### Content Quality

- Write clear, concise sentences
- Use active voice when possible
- Maintain consistent tone and style
- Proofread for grammar and spelling

### Technical Validation

- Validate Markdown syntax with linters
- Test links to ensure they work
- Check code examples for accuracy
- Verify image paths and accessibility

### Tools and Linting

- Use markdownlint for style consistency
- Employ spell checkers and grammar tools
- Test rendering in multiple viewers
- Validate HTML output when converting

## Examples

### Well-Formatted Document Structure

````markdown
# Project Documentation

## Overview

This project provides a comprehensive solution for...

## Installation

### Prerequisites

Before installing, ensure you have:

- Node.js 14 or higher
- npm 6 or higher

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/user/project.git
   ```
````

2. Install dependencies:
   ```bash
   npm install
   ```

## Usage

### Basic Usage

To use the basic features:

```javascript
const project = require("project");
project.init();
```

### Advanced Configuration

For advanced users, you can configure...

## API Reference

### Methods

| Method               | Description            | Parameters         |
| -------------------- | ---------------------- | ------------------ |
| `init()`             | Initialize the project | None               |
| `configure(options)` | Set configuration      | `options` (Object) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

```

## Common Mistakes to Avoid

### Formatting Issues
- Inconsistent heading hierarchy
- Missing blank lines around code blocks
- Improper list indentation
- Mixing ordered and unordered list styles

### Content Issues
- Generic or unclear link text
- Missing alt text for images
- Overly long lines that hurt readability
- Inconsistent tone or style

### Technical Issues
- Broken internal/external links
- Missing language specification in code blocks
- Improperly escaped special characters
- Inconsistent file naming conventions

This style guide ensures your Markdown documents are readable, accessible, and maintainable across different platforms and tools.
```
