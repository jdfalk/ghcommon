<!-- file: docs/refactors/workflows/v2/github-packages-setup.md -->
<!-- version: 1.0.0 -->
<!-- guid: c2d3e4f5-a6b7-8c9d-0e1f-2a3b4c5d6e7f -->

# GitHub Packages Setup

This guide explains how to configure GitHub Packages publishing for multi-version
support with branch-specific tags.

## Overview

The v2 workflow system publishes packages to GitHub Packages with
branch-aware tagging:

- **Main branch**: Packages tagged as `latest` and semantic version
- **Stable branches**: Packages tagged with language-specific versions

## Supported Languages

### Go Modules

**Publishing from main branch**:

```bash
# Tag: v1.2.3
# Package: github.com/owner/repo@v1.2.3
```

**Publishing from stable-1-go-1.24 branch**:

```bash
# Tag: v1.2.3-go124
# Package: github.com/owner/repo@v1.2.3-go124
```

**Consuming packages**:

```bash
# Latest version (from main)
go get github.com/owner/repo@latest

# Specific stable version
go get github.com/owner/repo@v1.2.3-go124
```

### Python Packages (PyPI)

**Publishing from main branch**:

```bash
# Package: package-name==1.2.3
```

**Publishing from stable-1-python-3.13 branch**:

```bash
# Package: package-name==1.2.3+python313
```

**Consuming packages**:

```bash
# Latest version
pip install package-name

# Specific stable version
pip install package-name==1.2.3+python313
```

### Node.js Packages (npm)

**Publishing from main branch**:

```bash
# Package: @owner/package@1.2.3
# Tag: latest
```

**Publishing from stable-1-node-20 branch**:

```bash
# Package: @owner/package@1.2.3-node20
# Tag: node20
```

**Consuming packages**:

```bash
# Latest version
npm install @owner/package

# Specific stable version
npm install @owner/package@1.2.3-node20
```

### Rust Crates (crates.io)

**Publishing from main branch**:

```bash
# Crate: package-name 1.2.3
```

**Publishing from stable-1-rust-stable branch**:

```bash
# Crate: package-name 1.2.3+rust-stable
```

**Consuming crates**:

```toml
# Latest version
[dependencies]
package-name = "1.2.3"

# Specific stable version
[dependencies]
package-name = "1.2.3+rust-stable"
```

## Configuration Requirements

### Repository Settings

1. **Enable GitHub Packages**:
   - Go to repository Settings → Actions → General
   - Under "Workflow permissions", select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"

2. **Add Package Registry**:
   - Go to repository Settings → Packages
   - Link to repository if not already linked

### Secrets Configuration

No additional secrets required for GitHub Packages. The workflow uses
`GITHUB_TOKEN` automatically.

For publishing to external registries (PyPI, npm, crates.io), add these
secrets:

- `PYPI_TOKEN` - PyPI API token
- `NPM_TOKEN` - npm access token
- `CARGO_REGISTRY_TOKEN` - crates.io API token

### Repository Config

Add to `.github/repository-config.yml`:

```yaml
workflows:
  experimental:
    use_new_release: true

packages:
  registries:
    github: true
    pypi: false  # Enable when ready
    npm: false   # Enable when ready
    cargo: false # Enable when ready
```

## Testing

Test package publishing with draft releases:

```bash
# Trigger draft release
gh workflow run release.yml \
  --ref main \
  -f draft=true \
  -f version=0.0.1-test
```

## Troubleshooting

### Package Not Found

**Problem**: Package not appearing in GitHub Packages

**Solution**:
1. Check workflow permissions (read/write required)
2. Verify package is linked to repository
3. Check workflow logs for publishing errors

### Version Conflicts

**Problem**: Version already exists error

**Solution**:
1. Increment version number
2. For testing, use prerelease versions (e.g., 1.2.3-rc1)
3. Delete old test packages from GitHub Packages UI

### Tag Already Exists

**Problem**: Git tag already exists error

**Solution**:
1. Delete the tag: `git tag -d v1.2.3 && git push origin :refs/tags/v1.2.3`
2. Increment version number
3. Use semantic versioning correctly (patch/minor/major)

## Best Practices

1. **Use semantic versioning**: Follow MAJOR.MINOR.PATCH format
2. **Test with drafts**: Always test with draft releases first
3. **Tag naming**: Let the workflow generate tags automatically
4. **Branch lifecycle**: Remove old stable branches after deprecation period
5. **Documentation**: Keep package changelogs updated

## Migration from Legacy System

If migrating from an existing package publishing system:

1. Enable `use_new_release: true` feature flag
2. Test with draft releases on a test branch
3. Verify packages appear in GitHub Packages
4. Update consumer documentation with new package names
5. Gradually migrate consumers to new package versions
6. Deprecate old package publishing after successful migration

## Additional Resources

- [GitHub Packages Documentation](https://docs.github.com/packages)
- [Semantic Versioning Spec](https://semver.org/)
- [Workflow v2 Architecture](architecture.md)
- [Release Workflow Reference](reference/workflow-reference.md)
