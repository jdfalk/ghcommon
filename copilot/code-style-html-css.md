<!-- file: copilot/code-style-html-css.md -->
<!-- version: 1.0.0 -->
<!-- guid: 9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d -->

# file: copilot/code-style-html-css.md

<!-- Google HTML/CSS Style Guide Summary -->
<!-- Source: https://google.github.io/styleguide/htmlcssguide.html -->

# HTML/CSS Style Guide (Google)

This document summarizes Google's HTML and CSS style guides for use in code generation and review.

## Core Principles

- **Consistency**: Follow the same conventions throughout the project
- **Readability**: Write code that is easy to read and understand
- **Maintainability**: Code should be easy to modify and extend
- **Performance**: Consider the impact on page load times and rendering
- **Accessibility**: Ensure content is accessible to all users

## HTML Guidelines

### Document Type

- Use HTML5 doctype
- Always include `<!DOCTYPE html>`

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Page Title</title>
  </head>
  <body>
    <p>Hello, world!</p>
  </body>
</html>
```

### HTML Validity

- Use valid HTML where possible
- Validate with tools like W3C HTML validator
- Close all elements that require closing

### Encoding

- Use UTF-8 encoding
- Specify encoding in HTML documents

```html
<meta charset="utf-8" />
```

### Semantics

- Use HTML according to its purpose
- Use elements for what they're meant for
- Provide alternative content for multimedia

```html
<!-- Good - semantic markup -->
<article>
  <header>
    <h1>Article Title</h1>
    <time datetime="2023-12-01">December 1, 2023</time>
  </header>
  <p>Article content...</p>
</article>

<!-- Avoid - non-semantic -->
<div class="article-title">Article Title</div>
<div class="article-date">December 1, 2023</div>
<div>Article content...</div>
```

### Structure and Formatting

#### Indentation

- Use 2 spaces for indentation
- Don't use tabs

#### Capitalization

- Use lowercase for element names, attributes, and values
- Exception: text content and `CDATA`

```html
<!-- Good -->
<img src="google.png" alt="Google" />

<!-- Avoid -->
<img src="google.png" alt="Google" />
```

#### Trailing Whitespace

- Remove trailing whitespace from lines

#### Line Length

- Avoid lines longer than 80 characters when practical
- Break long attribute lists across multiple lines

```html
<!-- Good -->
<button class="btn btn-primary" data-toggle="modal" data-target="#myModal">
  Click me
</button>
```

### HTML Quotation Marks

- Use double quotation marks for attribute values

```html
<!-- Good -->
<a class="maia-button maia-button-secondary">Sign in</a>

<!-- Avoid -->
<a class="maia-button maia-button-secondary">Sign in</a>
```

### Multimedia Fallback

- Provide alternative content for multimedia elements

```html
<!-- Good -->
<img src="spreadsheet.png" alt="Spreadsheet screenshot" />
<video controls>
  <source src="movie.mp4" type="video/mp4" />
  <p>
    Your browser doesn't support video.
    <a href="movie.mp4">Download the video</a>.
  </p>
</video>
```

### Forms

- Use appropriate input types
- Include labels for form controls
- Use fieldsets for related form controls

```html
<form>
  <fieldset>
    <legend>Personal Information</legend>
    <label for="name">Name:</label>
    <input type="text" id="name" name="name" required />

    <label for="email">Email:</label>
    <input type="email" id="email" name="email" required />
  </fieldset>

  <button type="submit">Submit</button>
</form>
```

## CSS Guidelines

### CSS Validity

- Use valid CSS where possible
- Validate with tools like W3C CSS validator

### ID and Class Naming

- Use meaningful names that reflect purpose or content
- Use lowercase with hyphens for separation
- Avoid presentational names

```css
/* Good - functional names */
.navigation {
}
.author {
}
.error-message {
}

/* Avoid - presentational names */
.red {
}
.left {
}
.big {
}
```

### ID and Class Name Style

- Use lowercase letters
- Separate words with hyphens
- Use abbreviations and acronyms sparingly

```css
/* Good */
.video-id {
}
.ads-sample {
}

/* Avoid */
.videoId {
}
.ads_sample {
}
```

### Type Selectors

- Avoid qualifying ID and class names with type selectors
- Exceptions: when necessary for specificity

```css
/* Good */
.example {
}
.error {
}

/* Avoid */
ul.example {
}
div.error {
}
```

### Shorthand Properties

- Use shorthand properties when possible
- Be explicit when setting specific values

```css
/* Good */
border-top: 0;
font:
  100%/1.6 palatino,
  georgia,
  serif;
padding: 0 1em 2em;

/* Avoid when shorthand is available */
border-top-style: none;
font-family: palatino, georgia, serif;
font-size: 100%;
line-height: 1.6;
padding-bottom: 2em;
padding-left: 1em;
padding-right: 1em;
padding-top: 0;
```

### 0 and Units

- Omit unit specification after 0 values
- Omit leading 0s in decimal values

```css
/* Good */
margin: 0;
padding: 0;
font-size: 0.8em;

/* Avoid */
margin: 0px;
padding: 0em;
font-size: 0.8em;
```

### Hexadecimal Notation

- Use 3-character hexadecimal notation where possible
- Use lowercase letters

```css
/* Good */
color: #ebc;
color: #fff;

/* Avoid */
color: #eebbcc;
color: #fff;
```

### Formatting Rules

#### Declaration Order

- Alphabetize declarations for consistent code
- Ignore vendor prefixes for sorting

```css
.example {
  background: fuchsia;
  border: 1px solid;
  -moz-border-radius: 4px;
  -webkit-border-radius: 4px;
  border-radius: 4px;
  color: black;
  text-align: center;
  text-indent: 2em;
}
```

#### Block Content Indentation

- Indent all block content (rules within rules, declarations)

```css
@media screen, projection {
  html {
    background: #fff;
    color: #444;
  }
}
```

#### Declaration Stops

- Use semicolon after every declaration
- Include semicolon after the last declaration in a block

```css
/* Good */
.test {
  display: block;
  height: 100px;
}
```

#### Property Name Stops

- Use space after colon following property name
- No space before colon

```css
/* Good */
h3 {
  font-weight: normal;
  line-height: 1.2;
}
```

#### Declaration Block Separation

- Use space before opening brace
- Place closing brace on new line

```css
/* Good */
.video {
  margin-top: 1em;
}

.audio {
  margin-bottom: 2em;
}
```

#### Selector and Declaration Separation

- Start new line for each selector and declaration

```css
/* Good */
h1,
h2,
h3 {
  font-weight: normal;
  line-height: 1.2;
}
```

#### Rule Separation

- Separate rules by new lines

```css
html {
  background: #fff;
}

body {
  margin: auto;
  width: 50%;
}
```

### CSS Quotation Marks

- Use single quotation marks for attribute selectors and property values
- Use double quotes when needed (e.g., font names with spaces)

```css
/* Good */
@import url("//www.google.com/css/maia.css");

html {
  font-family: "open sans", arial, sans-serif;
}

/* When spaces are present */
font-family: "Helvetica Neue", Arial, sans-serif;
```

## Advanced CSS Guidelines

### Specificity

- Keep specificity low when possible
- Avoid using !important
- Use class selectors over element selectors

```css
/* Good - low specificity */
.nav-item {
}
.nav-item.active {
}

/* Avoid - high specificity */
nav ul li a.nav-link.active {
}
```

### CSS Architecture

#### Component-Based Approach

- Write modular, reusable components
- Use consistent naming conventions
- Keep components self-contained

```css
/* Component: Button */
.btn {
  display: inline-block;
  padding: 0.5em 1em;
  border: 1px solid #ccc;
  background: #f5f5f5;
  text-decoration: none;
}

.btn--primary {
  background: #007cba;
  border-color: #006ba6;
  color: white;
}

.btn--large {
  padding: 0.75em 1.5em;
  font-size: 1.125em;
}
```

#### Layout Patterns

```css
/* Grid Layout */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

/* Flexbox Layout */
.flex-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.flex-item {
  flex: 1;
}
```

### Responsive Design

- Use mobile-first approach
- Use relative units (em, rem, %, vw, vh)
- Use CSS Grid and Flexbox for layouts

```css
/* Mobile first */
.container {
  width: 100%;
  padding: 1rem;
}

/* Tablet and up */
@media screen and (min-width: 768px) {
  .container {
    max-width: 750px;
    margin: 0 auto;
  }
}

/* Desktop and up */
@media screen and (min-width: 1024px) {
  .container {
    max-width: 1200px;
    padding: 2rem;
  }
}
```

### Performance Considerations

#### CSS Optimization

- Minimize the use of expensive properties (box-shadow, border-radius, etc.)
- Use efficient selectors
- Avoid deep nesting

```css
/* Good - efficient */
.button {
}
.button:hover {
}

/* Avoid - inefficient */
div.container ul.nav li.nav-item a.nav-link:hover {
}
```

#### Critical CSS

- Inline critical CSS for above-the-fold content
- Load non-critical CSS asynchronously

### Accessibility

- Ensure sufficient color contrast
- Use focus indicators
- Don't rely solely on color to convey information

```css
/* Good - accessible focus indicator */
.button:focus {
  outline: 2px solid #007cba;
  outline-offset: 2px;
}

/* Good - high contrast */
.error-message {
  color: #d32f2f;
  background: #ffebee;
  border: 1px solid #d32f2f;
}
```

## Modern CSS Features

### Custom Properties (CSS Variables)

```css
:root {
  --primary-color: #007cba;
  --secondary-color: #6c757d;
  --font-family: "Helvetica Neue", Arial, sans-serif;
  --border-radius: 4px;
}

.button {
  background-color: var(--primary-color);
  font-family: var(--font-family);
  border-radius: var(--border-radius);
}
```

### Logical Properties

```css
/* Good - logical properties for internationalization */
.content {
  margin-block-start: 1rem;
  margin-inline-end: 2rem;
  padding-inline: 1rem;
}

/* Traditional - physical properties */
.content-traditional {
  margin-top: 1rem;
  margin-right: 2rem;
  padding-left: 1rem;
  padding-right: 1rem;
}
```

## Tools and Validation

### Recommended Tools

- **Linting**: stylelint with Google's config
- **Formatting**: Prettier with appropriate settings
- **Validation**: W3C CSS Validator
- **Accessibility**: axe-core, WAVE

### Build Process

- Minify CSS for production
- Use autoprefixer for vendor prefixes
- Optimize CSS delivery (critical CSS, async loading)

This style guide should be used as the foundation for all HTML and CSS code generation and formatting decisions.
