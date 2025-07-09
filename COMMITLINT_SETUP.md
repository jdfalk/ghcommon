<!-- file: COMMITLINT_SETUP.md -->
<!-- version: 1.0.0 -->
<!-- guid: b2c3d4e5-f6a7-8901-bcde-f23456789012 -->

# Commitlint Setup

This repository uses [commitlint](https://commitlint.js.org/) to enforce our conventional commit standards.

## Installation

If you want to run commitlint locally, install the dependencies:

```bash
npm install
```

## Usage

### Manual Validation

Check the last commit:
```bash
npm run commitlint
```

Check commits in a range (CI):
```bash
npm run commitlint-ci
```

### Git Hooks (Optional)

To automatically validate commits before they're created, you can install a git hook:

```bash
# Install husky (one-time setup)
npm install --save-dev husky
npx husky install

# Add commit-msg hook
npx husky add .husky/commit-msg 'npx --no-install commitlint --edit "$1"'
```

## Configuration

The commitlint configuration is in `.commitlintrc.js` and follows our standards:

- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `build`, `ci`, `revert`
- **Format**: `type(scope): subject` (scope is optional)
- **Subject**: 10-72 characters, lowercase, no period
- **Body**: Should include "Files changed:" section

## Examples

✅ **Good commits:**

```text
feat: add commitlint configuration

Files changed:
- `.commitlintrc.js` - commitlint configuration
- `package.json` - commitlint dependencies

fix(api): handle null response in user service

Files changed:
- `src/api/user.service.js` - add null check
```

❌ **Bad commits:**

```text
Fixed stuff                    # No type
feat: Add new feature.         # Period at end
feat: a                        # Too short
FEAT: new feature              # Wrong case
```

## Integration

Commitlint is automatically enabled in our Super Linter configuration via:

- `VALIDATE_GIT_COMMITLINT=true` in `.github/super-linter.env`
- Integrated in `.github/workflows/reusable-super-linter.yml`
