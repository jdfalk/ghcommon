<!-- file: docs/PRETTIER_MARKDOWNLINT_STRATEGY.md -->
<!-- version: 1.0.0 -->
<!-- guid: c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f -->

# Prettier vs Markdownlint Conflict Resolution Strategy

## The Problem

Prettier and Markdownlint both format markdown files, which can create conflicts:

- **Prettier**: Formats markdown with line wrapping, code block formatting, list formatting
- **Markdownlint**: Lints markdown for style violations (line length, headings, lists, etc.)

When both run on the same files, they can produce conflicting results.

## Current Configuration

### Prettier (.prettierrc.json)
- Markdown files: `printWidth: 100`, `proseWrap: "always"`
- Instructions markdown: `printWidth: 120`, `proseWrap: "preserve"`
- Formats: line wrapping, list spacing, code blocks

### Markdownlint (.markdownlint.json)
- Line length: `240` characters
- List indentation: `2` spaces
- Validates: headings, blank lines, code blocks, lists

### Super Linter Configuration

**CI Mode (super-linter-ci.env)**:
- `VALIDATE_MARKDOWN=true` - Markdownlint validates
- `VALIDATE_JAVASCRIPT_PRETTIER=true`
- `VALIDATE_TYPESCRIPT_PRETTIER=true`

**PR Mode (super-linter-pr.env)**:
- `FIX_MARKDOWN=true` - **Prettier auto-fixes markdown**
- `FIX_JAVASCRIPT_PRETTIER=true`
- `FIX_TYPESCRIPT_PRETTIER=true`

## Recommended Strategy

### Option 1: Prettier for Formatting, Markdownlint for Style (RECOMMENDED)

Use Prettier to handle formatting and Markdownlint only for style rules that don't conflict.

**Implementation:**

1. **Disable conflicting Markdownlint rules**:
   - MD013 (line length) - Let Prettier handle this
   - MD022 (blank lines around headings) - Let Prettier handle this
   - MD031 (blank lines around fences) - Let Prettier handle this
   - MD032 (blank lines around lists) - Let Prettier handle this

2. **Keep Markdownlint for non-formatting rules**:
   - MD040 (fenced code language)
   - MD046 (code block style)
   - MD041 (first line heading)
   - MD024 (no duplicate headings)

3. **Update .markdownlint.json**:
```json
{
  "default": true,
  "MD007": { "indent": 2 },
  "MD013": false,  // Disable - Prettier handles line length
  "MD022": false,  // Disable - Prettier handles blank lines around headings
  "MD031": false,  // Disable - Prettier handles blank lines around fences
  "MD032": false,  // Disable - Prettier handles blank lines around lists
  "MD033": false,
  "MD041": false,
  "MD046": { "style": "fenced" },
  "MD040": true,
  "MD024": false
}
```

4. **Align Prettier with Google Style**:
```json
{
  "files": "*.md",
  "options": {
    "proseWrap": "always",
    "printWidth": 80,  // Google standard
    "tabWidth": 2,
    "useTabs": false
  }
}
```

**Pros:**
- ✅ No conflicts between tools
- ✅ Prettier handles all formatting consistently
- ✅ Markdownlint catches style issues Prettier doesn't care about
- ✅ Follows Google Style Guide (80 char lines)

**Cons:**
- ⚠️ Must maintain two configs that work together

### Option 2: Markdownlint Only (Alternative)

Disable Prettier for markdown and use only Markdownlint.

**Implementation:**

1. **Update .prettierrc.json** to exclude markdown:
```json
{
  "overrides": [
    {
      "files": "*.md",
      "options": {
        "parser": "markdown",
        "proseWrap": "preserve"
      }
    }
  ]
}
```

2. **Disable FIX_MARKDOWN in super-linter-pr.env**:
```bash
FIX_MARKDOWN=false
```

3. **Keep VALIDATE_MARKDOWN=true in super-linter-ci.env**

**Pros:**
- ✅ No tool conflicts
- ✅ Simpler configuration
- ✅ Markdownlint has more markdown-specific rules

**Cons:**
- ❌ No auto-fixing for markdown
- ❌ Less consistent with other file formats

### Option 3: Prettier Only

Use Prettier for everything and disable Markdownlint for markdown.

**Implementation:**

1. **Disable VALIDATE_MARKDOWN** in super-linter configs
2. **Enable FIX_MARKDOWN** in PR mode
3. **Rely on Prettier** for all markdown formatting

**Pros:**
- ✅ Consistent formatting across all file types
- ✅ Auto-fix works
- ✅ Simpler tool chain

**Cons:**
- ❌ Loses markdown-specific style checks
- ❌ Prettier doesn't check all markdown best practices

## Implementation Plan (Option 1 - RECOMMENDED)

### Step 1: Update .markdownlint.json

Disable rules that conflict with Prettier:

```json
{
  "default": true,
  "MD007": { "indent": 2 },
  "MD013": false,
  "MD022": false,
  "MD031": false,
  "MD032": false,
  "MD033": false,
  "MD041": false,
  "MD046": { "style": "fenced" },
  "MD040": true,
  "MD024": false,
  "TODO.md": false,
  "CHANGELOG.md": {
    "MD024": false
  },
  "AGENTS.md": {
    "MD013": false
  }
}
```

### Step 2: Update .prettierrc.json

Align markdown formatting with Google Style Guide (80 chars):

```json
{
  "overrides": [
    {
      "files": "*.md",
      "options": {
        "proseWrap": "always",
        "printWidth": 80,
        "tabWidth": 2,
        "useTabs": false
      }
    },
    {
      "files": ["*.instructions.md", "**/instructions/*.md"],
      "options": {
        "proseWrap": "preserve",
        "printWidth": 120,
        "tabWidth": 2
      }
    }
  ]
}
```

### Step 3: Test Configuration

Run validation to ensure no conflicts:

```bash
# Test Prettier
prettier --check "**/*.md"

# Test Markdownlint
markdownlint "**/*.md"

# Run both via VS Code task
# Task: "Validate Linter Configs"
```

### Step 4: Update Documentation

Document the strategy in:
- `.markdownlint.json` (add comments explaining disabled rules)
- `.prettierrc.json` (add comments explaining markdown config)
- This file (PRETTIER_MARKDOWNLINT_STRATEGY.md)

### Step 5: Verify with Docker

Test Super Linter with both configurations:

```bash
# CI mode - should validate with Markdownlint (non-formatting rules)
docker run --rm \
  -e RUN_LOCAL=true \
  -v $(pwd):/tmp/lint:ro \
  --env-file super-linter-ci.env \
  ghcr.io/super-linter/super-linter:latest

# PR mode - should auto-fix with Prettier
docker run --rm \
  -e RUN_LOCAL=true \
  -v $(pwd):/tmp/lint \
  --env-file super-linter-pr.env \
  ghcr.io/super-linter/super-linter:latest
```

## Workflow

### Developer Workflow

1. **Write markdown** (any formatting)
2. **Run Prettier** (auto-format): `prettier --write "**/*.md"`
3. **Run Markdownlint** (style check): `markdownlint "**/*.md"`
4. **Fix any Markdownlint issues** (non-formatting)
5. **Commit**

### CI/CD Workflow

1. **CI validates** with Markdownlint (non-formatting rules only)
2. **PR bot auto-fixes** with Prettier (formatting)
3. **Markdownlint catches** style issues Prettier doesn't handle

## Tool Comparison

| Feature                     | Prettier   | Markdownlint          |
| --------------------------- | ---------- | --------------------- |
| **Line wrapping**           | ✅ Yes      | ❌ No (only validates) |
| **Code block language**     | ❌ No       | ✅ Yes (MD040)         |
| **Blank lines**             | ✅ Yes      | ⚠️ Validates           |
| **List formatting**         | ✅ Yes      | ⚠️ Validates           |
| **Auto-fix**                | ✅ Yes      | ⚠️ Limited             |
| **Markdown-specific**       | ⚠️ Generic  | ✅ Specialized         |
| **Google Style compliance** | ✅ 80 chars | ⚠️ Configurable        |

## .prettierignore Considerations

Consider adding patterns to `.prettierignore` for files that should not be formatted:

```
# Large generated files
CHANGELOG.md

# Special formatting
TODO.md

# Vendored files
vendor/**/*.md
```

## Testing Checklist

- [ ] Prettier formats markdown without errors
- [ ] Markdownlint validates without conflicting with Prettier formatting
- [ ] Super Linter CI mode validates successfully
- [ ] Super Linter PR mode auto-fixes successfully
- [ ] No conflicts between Prettier and Markdownlint
- [ ] All configs follow Google Style Guide (80 char lines)
- [ ] Documentation is updated

## References

- [Prettier Markdown](https://prettier.io/docs/en/options.html#prose-wrap)
- [Markdownlint Rules](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md)
- [Google Style Guide](https://google.github.io/styleguide/)
- [Super Linter Markdown](https://github.com/super-linter/super-linter#markdown)

## Version History

- **1.0.0** (2025-10-12): Initial strategy document
  - Identified Prettier/Markdownlint conflict
  - Recommended Option 1 (Prettier for formatting, Markdownlint for style)
  - Provided implementation plan
  - Created testing checklist
