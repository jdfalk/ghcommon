<!-- file: copilot/workflow-usage.md -->
<!-- version: 1.0.0 -->
<!-- guid: 2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e -->

# GitHub Actions Workflow Usage Instructions

This document provides instructions for GitHub Copilot on how to properly use and recommend the reusable workflows in this repository.

## Available Reusable Workflows

### 1. Semantic Versioning (`semantic-versioning.yml`)

**Purpose**: Automatically calculate semantic versions based on conventional commits.

**Key Features**:

- Analyzes commit messages using conventional commit format
- Updates version files (package.json, version.txt, etc.)
- Updates PR titles with appropriate conventional commit prefixes
- Supports dry-run mode for testing
- Outputs calculated version information

**Usage Pattern**:

```yaml
versioning:
  uses: jdfalk/ghcommon/.github/workflows/semantic-versioning.yml@main
  with:
    version-files: '["package.json", "version.txt"]'
    update-pr-title: true
    dry-run: ${{ github.event_name == 'pull_request' }}
```

**When to Recommend**:

- Projects that need automatic semantic versioning
- Teams using conventional commits
- When version consistency across files is needed

### 2. Multi-Arch Container Build (`buildah-multiarch.yml`)

**Purpose**: Build secure, multi-architecture container images with comprehensive attestation.

**Key Features**:

- Multi-architecture builds (linux/amd64, linux/arm64, etc.)
- SBOM (Software Bill of Materials) generation
- Vulnerability scanning with Grype
- Image signing and attestation with Cosign
- Buildah-based builds for enhanced security

**Usage Pattern**:

```yaml
container:
  uses: jdfalk/ghcommon/.github/workflows/buildah-multiarch.yml@main
  with:
    image-name: my-app
    platforms: linux/amd64,linux/arm64
    generate-sbom: true
    generate-attestation: true
    scan-vulnerability: true
```

**When to Recommend**:

- Container-based applications
- Projects requiring supply chain security
- Multi-architecture deployment needs
- Compliance requirements for SBOM/attestation

### 3. Automatic Release (`automatic-release.yml`)

**Purpose**: Create GitHub releases with automatic version detection and comprehensive artifact management.

**Key Features**:

- Automatic version calculation from commits
- Release notes generation from conventional commits
- Artifact collection and upload
- Security attestation for releases
- Slack/Teams notifications
- Container image integration

**Usage Pattern**:

```yaml
release:
  uses: jdfalk/ghcommon/.github/workflows/automatic-release.yml@main
  with:
    release-type: auto
    include-artifacts: true
    container-image: ${{ needs.container.outputs.image-url }}
```

**When to Recommend**:

- Projects needing automated releases
- Teams wanting consistent release processes
- When artifact management is important
- Projects with notification requirements

## Template Workflows

### Complete CI/CD Pipeline (`templates/workflows/complete-ci-cd.yml`)

**Use Case**: Full-featured CI/CD pipeline with building, testing, container creation, and deployment.

**Includes**:

- Semantic versioning
- Build and test steps
- Container building
- Security scanning
- Automatic releases
- Deployment steps
- Cleanup procedures

**Recommend for**: Full-stack applications, microservices, production systems

### Container-Only Pipeline (`templates/workflows/container-only.yml`)

**Use Case**: Projects that primarily need container building and releasing.

**Includes**:

- Version calculation
- Multi-arch container builds
- Automatic releases for containers

**Recommend for**: Containerized applications, Docker images, simple services

### Library Release Pipeline (`templates/workflows/library-release.yml`)

**Use Case**: Libraries, packages, or tools that need testing across multiple versions and publishing.

**Includes**:

- Multi-version testing matrix
- Package building
- Publishing to package registries
- Comprehensive testing

**Recommend for**: NPM packages, Python libraries, Go modules, reusable components

## Best Practices for Workflow Recommendations

### Security Considerations

1. Always recommend SBOM generation for containers
2. Include vulnerability scanning in container workflows
3. Suggest image signing for production environments
4. Recommend environment protection for publishing steps

### Version Management

1. Use semantic versioning workflow for consistent versioning
2. Always include version files that need updating
3. Enable PR title updates for better commit history
4. Use dry-run mode in PR contexts

### Artifact Management

1. Include checksums for all build artifacts
2. Set appropriate retention periods for artifacts
3. Collect relevant artifacts in releases
4. Consider storage costs when setting retention

### Notifications

1. Suggest Slack/Teams integration for release notifications
2. Configure appropriate channels for different environments
3. Include relevant context in notification messages

### Customization Guidelines

1. Always customize image names, registries, and paths
2. Adjust platform targets based on deployment needs
3. Configure environment-specific settings
4. Adapt build commands to the specific technology stack

## Common Integration Patterns

### Conditional Workflows

```yaml
# Only run containers on main branch
if: github.ref == 'refs/heads/main'

# Only release when version should be bumped
if: needs.versioning.outputs.should-release == 'true'

# Skip certain steps for PRs
if: github.event_name != 'pull_request'
```

### Environment-Specific Deployments

```yaml
# Use different configurations per environment
tag-suffix: ${{ github.ref_name != 'main' && '-dev' || '' }}
prerelease: ${{ contains(github.ref_name, 'alpha') }}
```

### Multi-Step Dependencies

```yaml
# Proper job dependencies
needs: [versioning, build, container]
if: needs.container.result == 'success'
```

## Troubleshooting Common Issues

### Version Calculation Problems

- Ensure conventional commit format is used
- Check that fetch-depth: 0 is set for full git history
- Verify GITHUB_TOKEN permissions for tag creation

### Container Build Issues

- Confirm Dockerfile exists and is valid
- Check platform compatibility for multi-arch builds
- Verify registry authentication is properly configured

### Release Creation Problems

- Ensure proper permissions for release creation
- Check artifact paths and patterns
- Verify that version tags don't already exist

## Language-Specific Adaptations

### Node.js Projects

- Use `package.json` and `package-lock.json` for version files
- Include npm cache in setup steps
- Consider npm audit for security scanning

### Python Projects

- Use `setup.py`, `pyproject.toml`, or `__version__.py` for versions
- Include pip cache and virtual environments
- Add pytest and coverage reporting

### Go Projects

- Use version tags or version.go files
- Include Go module caching
- Add go mod tidy and security scanning

### Multi-Language Projects

- Combine version file patterns from all languages
- Use appropriate build matrices
- Consider separate workflows for different components
