# GitHub Common Workflows

A comprehensive repository of reusable GitHub Actions workflows and templates for automated CI/CD, semantic versioning, multi-architecture container builds, and secure release management.

## 🚀 Quick Start

Choose the setup that matches your project type:

### For Complete CI/CD Pipeline

```bash
curl -sSL https://raw.githubusercontent.com/jdfalk/ghcommon/main/scripts/setup-repository.sh | bash -s complete
```

### For Container-Only Projects

```bash
curl -sSL https://raw.githubusercontent.com/jdfalk/ghcommon/main/scripts/setup-repository.sh | bash -s container
```

### For Library/Package Projects

```bash
curl -sSL https://raw.githubusercontent.com/jdfalk/ghcommon/main/scripts/setup-repository.sh | bash -s library
```

## 📋 What's Included

### Reusable Workflows

| Workflow                                                                                  | Purpose                        | Key Features                                                             |
| ----------------------------------------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------ |
| [`semantic-versioning.yml`](.github/workflows/semantic-versioning.yml)                    | Automatic version calculation  | Conventional commits, PR title updates, version file updates             |
| [`buildah-multiarch.yml`](.github/workflows/buildah-multiarch.yml)                        | Multi-arch container builds    | SBOM generation, vulnerability scanning, attestation, signing            |
| [`automatic-release.yml`](.github/workflows/automatic-release.yml)                        | Automated GitHub releases      | Release notes, artifact management, notifications                        |
| [`unified-issue-management.yml`](.github/workflows/reusable-unified-issue-management.yml) | Comprehensive issue management | JSON-driven updates, Copilot tickets, duplicate closure, security alerts |

### Templates

| Template                                                         | Description                | Use Case                                   |
| ---------------------------------------------------------------- | -------------------------- | ------------------------------------------ |
| [`complete-ci-cd.yml`](templates/workflows/complete-ci-cd.yml)   | Full CI/CD pipeline        | Full-stack applications, microservices     |
| [`container-only.yml`](templates/workflows/container-only.yml)   | Container-focused pipeline | Containerized applications, Docker images  |
| [`library-release.yml`](templates/workflows/library-release.yml) | Package release pipeline   | NPM packages, Python libraries, Go modules |

### Supporting Tools

- **Setup Scripts**: Automated repository configuration
- **Validation Tools**: Repository readiness verification
- **Copilot Instructions**: AI-assisted workflow implementation
- **Security Guidelines**: Best practices and compliance

## 🔧 Core Features

### Semantic Versioning

- **Automatic version calculation** based on conventional commits
- **Multi-file version updates** (package.json, version.txt, etc.)
- **PR title enhancement** with conventional commit prefixes
- **Dry-run support** for testing

### Multi-Architecture Container Builds

- **Cross-platform builds** (linux/amd64, linux/arm64, linux/arm/v7)
- **Security-first approach** with Buildah
- **SBOM generation** with Syft
- **Vulnerability scanning** with Grype
- **Image signing** and attestation with Cosign
- **Comprehensive artifact management**

### Automated Releases

- **Smart version detection** from commit messages
- **Automated release notes** from conventional commits
- **Artifact collection** and attachment
- **Security attestations** for releases
- **Slack/Teams notifications**
- **Container image integration**

### Issue Management

- **Comprehensive issue tracking** with GitHub Issues
- **Automated ticket creation** from PRs and commits
- **Duplicate issue detection** and closure
- **Security vulnerability alerts** integration
- **Distributed file processing** with automatic archival
- **Conflict-free parallel development** using GUID-based updates

### Label Synchronization

- **Centralized label management** across multiple repositories
- **Standard label configuration** with consistent colors and descriptions
- **Automated sync scheduling** with customizable frequency
- **Safe mode** (no deletions) and cleanup mode support
- **Dry-run testing** before applying changes
- **Batch repository processing** from configuration files

## 📖 Usage Examples

### Basic Semantic Versioning

```yaml
versioning:
  uses: jdfalk/ghcommon/.github/workflows/semantic-versioning.yml@main
  with:
    version-files: '["package.json", "version.txt"]'
    update-pr-title: true
    dry-run: ${{ github.event_name == 'pull_request' }}
```

### Multi-Arch Container Build

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

### Automatic Release

```yaml
release:
  uses: jdfalk/ghcommon/.github/workflows/automatic-release.yml@main
  with:
    release-type: auto
    include-artifacts: true
    container-image: ${{ needs.container.outputs.image-url }}
```

### Issue Management Workflow

```yaml
name: Issue Management

on:
  push:
    branches: [main]
    paths:
      - "issue_updates.json"
      - ".github/issue-updates/*.json"
  pull_request_review_comment:
    types: [created, edited, deleted]
  schedule:
    - cron: "0 2 * * *" # Daily maintenance
  workflow_dispatch:

jobs:
  issue-management:
    uses: jdfalk/ghcommon/.github/workflows/reusable-unified-issue-management.yml@main
    with:
      operations: "auto" # Auto-detect based on event
      issue_updates_file: "issue_updates.json"
      issue_updates_directory: ".github/issue-updates"
      cleanup_issue_updates: true
    secrets: inherit
```

### Label Synchronization Workflow

```yaml
name: Sync Labels from ghcommon

on:
  workflow_dispatch:
  schedule:
    - cron: "0 3 1 * *" # Monthly on 1st at 3 AM UTC

jobs:
  sync-labels:
    uses: jdfalk/ghcommon/.github/workflows/reusable-label-sync.yml@main
    with:
      repositories: ${{ github.repository }}
      source-repo: "jdfalk/ghcommon"
      delete-extra-labels: false # Safe mode
    secrets: inherit
```
```

**Features**:

- JSON-driven issue updates (legacy and distributed formats)
- Copilot review comment tickets
- Duplicate issue detection and closure
- CodeQL security alert integration
- GUID-based duplicate prevention
- Parallel development with no merge conflicts
- **Automatic PR creation** for processed file archival
- **Workflow summary reports** with detailed operation status

**Helper Script**: Copy the issue creation helper to your repository:

```bash
curl -fsSL https://raw.githubusercontent.com/jdfalk/ghcommon/main/scripts/create-issue-update.sh -o scripts/create-issue-update.sh
chmod +x scripts/create-issue-update.sh

# Usage examples:
./scripts/create-issue-update.sh create "Add dark mode" "Implement dark theme" "enhancement,ui"
./scripts/create-issue-update.sh comment 123 "Testing completed successfully"
```

**Documentation**: [docs/unified-issue-management.md](docs/unified-issue-management.md)
**Examples**: [examples/workflows/](examples/workflows/)

## 🛡️ Security Features

- **Supply chain security** with SBOMs and attestations
- **Vulnerability scanning** for containers and dependencies
- **Image signing** with Cosign and keyless signing
- **Least privilege access** patterns
- **Secret management** best practices
- **Compliance-ready** documentation and controls

## 🔒 Requirements

### Repository Permissions

- **Actions**: Read and write permissions
- **Packages**: Write permissions (for container registries)
- **Contents**: Write permissions (for releases and tags)
- **Pull Requests**: Write permissions (for PR updates)

### Required Secrets (Optional)

- `SLACK_WEBHOOK_URL` - For release notifications
- `TEAMS_WEBHOOK_URL` - For Teams notifications
- External registry credentials (if not using GitHub Container Registry)

## 📚 Documentation

### Setup Guides

- [Repository Setup Guide](.github/repository-setup.md) - Complete setup instructions
- [Security Guidelines](.github/security-guidelines.md) - Security best practices
- [Workflow Usage](.github/workflow-usage.md) - Detailed workflow documentation

### Templates

- [Complete CI/CD](templates/workflows/complete-ci-cd.yml) - Full pipeline template
- [Container Only](templates/workflows/container-only.yml) - Container-focused template
- [Library Release](templates/workflows/library-release.yml) - Package release template

## 🚦 Validation

Validate your repository setup:

```bash
curl -sSL https://raw.githubusercontent.com/jdfalk/ghcommon/main/scripts/validate-setup.sh | bash
```

This will check:

- ✅ Workflow file syntax
- ✅ Required files and structure
- ✅ Git configuration
- ✅ Conventional commit usage
- ✅ Security best practices

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with the validation script
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/jdfalk/ghcommon/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jdfalk/ghcommon/discussions)
- **Security**: See [SECURITY.md](SECURITY.md) for reporting security issues

## 🏷️ Versioning

This project uses [Semantic Versioning](https://semver.org/). See [CHANGELOG.md](CHANGELOG.md) for version history.

## 🙏 Acknowledgments

- GitHub Actions team for the platform
- [Buildah](https://buildah.io/) for secure container builds
- [Syft](https://github.com/anchore/syft) for SBOM generation
- [Grype](https://github.com/anchore/grype) for vulnerability scanning
- [Cosign](https://github.com/sigstore/cosign) for container signing
- [Conventional Commits](https://www.conventionalcommits.org/) for commit standards
