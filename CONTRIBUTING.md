# file: CONTRIBUTING.md

# Contributing to GitHub Common Workflows

Thank you for your interest in contributing to GitHub Common Workflows! This
document provides guidelines and information for contributors.

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to
follow. Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Issues

1. **Search existing issues** to avoid duplicates
2. **Use issue templates** when available
3. **Provide detailed information** including:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Logs or error messages

### Suggesting Features

1. **Check existing feature requests** to avoid duplicates
2. **Use the feature request template**
3. **Provide context** about:
   - Use case and motivation
   - Proposed solution
   - Alternative approaches considered
   - Impact on existing functionality

### Submitting Pull Requests

#### Before You Start

1. **Fork the repository** and create your branch from `main`
2. **Check existing PRs** to avoid duplicate work
3. **Discuss significant changes** in an issue first

#### Development Process

1. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the style guidelines

3. **Test your changes**:

   ```bash
   # Validate workflow syntax
   ./scripts/validate-setup.sh

   # Test with a sample repository
   ./scripts/setup-repository.sh complete
   ```

4. **Update documentation** as needed

5. **Follow conventional commit format**:
   ```
   feat: add new workflow for multi-language projects
   fix: resolve issue with container registry authentication
   docs: update setup instructions for Windows users
   ```

#### Pull Request Guidelines

1. **Use the PR template**
2. **Include tests** for new functionality
3. **Update documentation** for any user-facing changes
4. **Ensure CI passes** before requesting review
5. **Link related issues** using keywords (fixes #123)

## Development Guidelines

### Workflow Development

#### Security First

- Always follow the security guidelines in `.github/security-guidelines.md`
- Use least privilege permissions
- Validate all inputs
- Pin action versions to specific commits or tags

#### Best Practices

- Make workflows reusable and configurable
- Provide comprehensive input validation
- Include proper error handling
- Document all inputs and outputs
- Use meaningful job and step names

#### Example Workflow Structure

```yaml
name: Descriptive Workflow Name

on:
  workflow_call:
    inputs:
      input-name:
        description: 'Clear description of the input'
        required: true
        type: string
    outputs:
      output-name:
        description: 'Clear description of the output'
        value: ${{ jobs.job-name.outputs.output-name }}

jobs:
  job-name:
    name: Descriptive Job Name
    runs-on: ubuntu-latest
    outputs:
      output-name: ${{ steps.step-id.outputs.output-name }}

    steps:
      - name: Descriptive Step Name
        id: step-id
        # Step implementation
```

### Documentation Standards

#### File Headers

All documentation files should include the file path comment:

```markdown
# file: path/to/file.md
```

#### Structure

- Use clear, descriptive headings
- Include code examples where appropriate
- Provide both basic and advanced usage examples
- Include troubleshooting sections
- Link to related documentation

#### Code Examples

- Use realistic, working examples
- Include necessary context and setup
- Explain non-obvious parts
- Follow the same style guidelines as the codebase

### Testing

#### Workflow Testing

1. **Syntax validation** with GitHub CLI or yaml parsers
2. **Integration testing** with sample repositories
3. **Security scanning** of workflow files
4. **Manual testing** across different scenarios

#### Script Testing

1. **Unit tests** for individual functions
2. **Integration tests** with real repositories
3. **Error condition testing**
4. **Cross-platform compatibility** (macOS, Linux, Windows)

## Style Guidelines

### YAML Workflows

- Use 2-space indentation
- Quote string values that might be ambiguous
- Use descriptive names for jobs, steps, and IDs
- Group related inputs and outputs
- Include comments for complex logic

### Shell Scripts

- Follow shellcheck recommendations
- Use strict error handling (`set -euo pipefail`)
- Include help text and usage examples
- Use consistent function naming
- Validate inputs and provide meaningful error messages

### Markdown Documentation

- Follow markdown linting rules
- Use consistent heading structure
- Include proper code formatting
- Use tables for structured information
- Include relevant links and references

## Submission Process

### Before Submitting

1. **Run validation scripts**:

   ```bash
   ./scripts/validate-setup.sh
   ```

2. **Test with multiple project types**:

   ```bash
   # Test each template
   ./scripts/setup-repository.sh complete
   ./scripts/setup-repository.sh container
   ./scripts/setup-repository.sh library
   ```

3. **Review security implications**

4. **Update relevant documentation**

### Review Process

1. **Automated checks** must pass (CI, linting, security scans)
2. **Manual review** by maintainers
3. **Security review** for workflow changes
4. **Documentation review** for user-facing changes
5. **Testing verification** with real-world scenarios

### After Approval

1. **Squash and merge** for feature PRs
2. **Update CHANGELOG.md** if needed
3. **Tag releases** following semantic versioning
4. **Update documentation** if needed

## Release Process

### Version Strategy

- Follow [Semantic Versioning](https://semver.org/)
- Use conventional commits for automatic versioning
- Create releases for significant changes
- Maintain backwards compatibility when possible

### Release Steps

1. **Update CHANGELOG.md**
2. **Create release PR**
3. **Tag the release** after merge
4. **Update documentation** with new version references
5. **Announce** significant releases

## Getting Help

### Resources

- **Documentation**: `.github/` directory
- **Examples**: `/templates/` directory
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for general questions

### Maintainer Contact

- Create an issue for bugs or feature requests
- Use discussions for general questions
- Tag maintainers (@jdfalk) for urgent security issues

## Recognition

Contributors are recognized in several ways:

- Listed in release notes for significant contributions
- Mentioned in repository contributors
- Invited to review related PRs
- Acknowledged in documentation updates

Thank you for contributing to GitHub Common Workflows!
