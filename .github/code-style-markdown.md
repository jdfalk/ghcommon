# Markdown Style Guide

This guide follows common Markdown best practices and industry standards.

## Headers

- Use ATX-style headers with a space after the hash signs (`#`)
- Use sentence case for headers (capitalize first word and proper nouns only)
- Include one blank line before and after headers (except at the beginning of the document)
- Use appropriate header hierarchy without skipping levels
- Limit document to one H1 header

```markdown
# Document title

## Section heading

### Subsection heading
```

## Formatting

- Use asterisks for emphasis: `*italic*` and `**bold**`
- Use backticks for `inline code`
- Use triple backticks for code blocks with language specification
- Use > for blockquotes, with a space after the >
- Use horizontal rules sparingly (three hyphens: `---`)
- Use trailing spaces for line breaks or use HTML `<br>` tags

## Lists

- Use hyphen (`-`) for unordered list items
- Use numbers followed by periods (`1.`) for ordered lists
- Indent nested lists with 2 or 4 spaces
- Include a blank line before and after lists
- Be consistent with your list marker style throughout the document

```markdown
- First item
- Second item
  - Nested item
  - Another nested item
- Third item

1. First step
2. Second step
   1. Substep one
   2. Substep two
3. Third step
```

## Links and Images

- Use reference-style links for repeated URLs
- Use descriptive link text that makes sense out of context
- Include alt text for all images
- Use relative paths for local images and resources
- Place reference links at the bottom of the section or document

```markdown
[Visit GitHub][github-link]

![Alt text for the image](path/to/image.png)

[github-link]: https://github.com
```

## Code Blocks

- Always specify the language for syntax highlighting
- Use fenced code blocks with triple backticks
- Avoid indented code blocks (four spaces)
- Include a blank line before and after code blocks

````markdown
```javascript
function example() {
  const value = 'This is a code example';
  return value;
}
```
````

## Tables

- Use tables sparingly and keep them simple
- Align the pipes vertically for better readability
- Use a minimum of three hyphens in each column of the separator row
- Include a blank line before and after tables

```markdown
| Header 1 | Header 2 | Header 3 |
| -------- | -------- | -------- |
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```

## General Document Structure

- Include a single H1 title at the top of the document
- Follow a logical and hierarchical structure
- Group related content under appropriate headings
- Keep line length to a maximum of 80-100 characters
- Use blank lines to separate logical sections
- End file with a newline character

## Extensions and Special Features

- Use HTML sparingly and only when Markdown syntax is insufficient
- Support for extensions may vary across platforms, so stick to standard Markdown when possible
- Document any specialized Markdown extensions used in the project
- Consider compatibility across different Markdown parsers

## Front Matter

- For static site generators, use YAML front matter at the top of the file
- Separate front matter from content with triple dashes

```markdown
---
title: Document Title
author: Author Name
date: 2023-01-01
tags: [markdown, style guide]
---

# Document content begins here
```

## File Naming and Organization

- Use lowercase for file names
- Use hyphens instead of spaces in file names (`markdown-style-guide.md`)
- Group related Markdown files in directories
- Include a README.md file in each directory to explain its contents

## Best Practices

- Check for broken links regularly
- Validate Markdown using linters like markdownlint
- Use consistent formatting throughout all project documentation
- Prefer native Markdown over HTML when possible
- Consider accessibility when writing documentation
