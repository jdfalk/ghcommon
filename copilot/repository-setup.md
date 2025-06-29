<!-- file: copilot/repository-setup.md -->
<!-- version: 1.0.0 -->
<!-- guid: 4e1f7b2c-8d5e-9f4e-1f7b-2c8d4e1f7b2c -->
<!-- version: 1.0.0 -->
<!-- guid: 3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f -->

# Repository Setup Guide

This guide provides step-by-step instructions for setting up a repository to use the reusable workflows from this common repository.

## Quick Setup

### 1. Add Workflow File

Copy one of the template workflows from `templates/workflows/` to your repository's `.github/workflows/` directory:

```bash
# For a complete CI/CD pipeline
curl -o .github/workflows/ci-cd.yml https://raw.githubusercontent.com/jdfalk/ghcommon/main/templates/workflows/complete-ci-cd.yml

# For container-only pipeline
curl -o .github/workflows/container.yml https://raw.githubusercontent.com/jdfalk/ghcommon/main/templates/workflows/container-only.yml

# For library/package releases
curl -o .github/workflows/release.yml https://raw.githubusercontent.com/jdfalk/ghcommon/main/templates/workflows/library-release.yml
```

### 2. Required Repository Settings

#### Permissions

Ensure your repository has the following permissions configured:

**Actions Permissions** (Settings → Actions → General):

- ✅ Allow all actions and reusable workflows
- ✅ Allow actions created by GitHub
- ✅ Allow actions by Marketplace verified creators

**Workflow Permissions** (Settings → Actions → General → Workflow permissions):

- ✅ Read and write permissions
- ✅ Allow GitHub Actions to create and approve pull requests

#### Branch Protection Rules

For the main branch (Settings → Branches):

- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Include administrators

### 3. Required Secrets

#### For Container Workflows

No additional secrets required when using GitHub Container Registry (ghcr.io). The `GITHUB_TOKEN` is automatically available.

#### For External Registries

- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password or access token
- `AWS_ACCESS_KEY_ID` - For ECR
- `AWS_SECRET_ACCESS_KEY` - For ECR

#### For Notifications (Optional)

- `SLACK_WEBHOOK_URL` - Slack webhook for release notifications
- `TEAMS_WEBHOOK_URL` - Microsoft Teams webhook for notifications

#### For Package Publishing

- `NPM_TOKEN` - For publishing to npm
- `PYPI_TOKEN` - For publishing to PyPI
- `NUGET_TOKEN` - For publishing to NuGet

### 4. Required Files

#### Dockerfile (for container workflows)

Create a `Dockerfile` in your repository root:

```dockerfile
# Example Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .

EXPOSE 3000
CMD ["npm", "start"]
```

#### Version Files (for semantic versioning)

Ensure you have version files that the workflow can update:

**package.json** (Node.js):

```json
{
  "name": "my-app",
  "version": "1.0.0"
}
```

**version.txt** (Generic):

```
1.0.0
```

\***\*init**.py\*\* (Python):

```python
__version__ = "1.0.0"
```

## Conventional Commits Setup

### Commit Message Format

Use conventional commit format for automatic versioning:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types**:

- `feat:` - New feature (minor version bump)
- `fix:` - Bug fix (patch version bump)
- `feat!:` or `fix!:` - Breaking change (major version bump)
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

**Examples**:

```
feat: add user authentication
fix: resolve memory leak in data processing
feat!: change API response format
docs: update installation instructions
```

### Git Hooks (Optional)

Add a commit message linter to ensure conventional commit format:

```bash
# Install commitizen
npm install -g commitizen cz-conventional-changelog
echo '{ "path": "cz-conventional-changelog" }' > ~/.czrc

# Use 'git cz' instead of 'git commit'
git cz
```

## Environment-Specific Configuration

### Development Environment

```yaml
# Use in pull requests
dry-run: true
push: false
prerelease: true
tag-suffix: -dev
```

### Staging Environment

```yaml
# Use for staging branch
prerelease: true
tag-suffix: -staging
scan-vulnerability: true
```

### Production Environment

```yaml
# Use for main branch
prerelease: false
generate-sbom: true
generate-attestation: true
scan-vulnerability: true
```

## Troubleshooting

### Common Issues

#### Permission Denied Errors

- Check workflow permissions in repository settings
- Ensure `GITHUB_TOKEN` has required permissions
- Verify branch protection rules don't block the action

#### Version Calculation Issues

- Ensure commits follow conventional commit format
- Check that repository has git history (not a fresh repo)
- Verify fetch-depth: 0 in checkout action

#### Container Build Failures

- Verify Dockerfile exists and is valid
- Check that all required build contexts are available
- Ensure base images are accessible

#### Release Creation Failures

- Check that tag doesn't already exist
- Verify GitHub token has release creation permissions
- Ensure artifact paths are correct

### Debug Mode

Enable debug logging by adding this secret to your repository:

- `ACTIONS_RUNNER_DEBUG` = `true`
- `ACTIONS_STEP_DEBUG` = `true`

## Customization Examples

### Multi-Language Repository

```yaml
versioning:
  uses: jdfalk/ghcommon/.github/workflows/semantic-versioning.yml@main
  with:
    version-files: '["package.json", "setup.py", "Cargo.toml", "go.mod"]'
```

### Multiple Container Images

```yaml
container-api:
  uses: jdfalk/ghcommon/.github/workflows/buildah-multiarch.yml@main
  with:
    image-name: my-app-api
    dockerfile: ./api/Dockerfile
    context: ./api

container-web:
  uses: jdfalk/ghcommon/.github/workflows/buildah-multiarch.yml@main
  with:
    image-name: my-app-web
    dockerfile: ./web/Dockerfile
    context: ./web
```

### Conditional Workflows

```yaml
container:
  if: contains(github.event.head_commit.message, '[build-container]') || github.ref == 'refs/heads/main'
  uses: jdfalk/ghcommon/.github/workflows/buildah-multiarch.yml@main
```

## Migration Guide

### From GitHub Actions Starter Workflows

1. Replace existing workflow files with templates
2. Add conventional commit format to your development process
3. Update branch protection rules
4. Test with a pull request

### From Other CI/CD Systems

1. Export environment variables and secrets
2. Convert build scripts to GitHub Actions format
3. Update deployment targets to use new artifact URLs
4. Test incrementally with feature branches

## Best Practices

### Repository Organization

- Keep workflows in `.github/workflows/`
- Store reusable scripts in `.github/scripts/`
- Document workflow customizations in `README.md`

### Security

- Use environment protection for production deployments
- Rotate secrets regularly
- Enable vulnerability scanning
- Review workflow changes carefully

### Performance

- Use caching for dependencies
- Optimize Docker builds with multi-stage builds
- Set appropriate artifact retention periods
- Clean up old releases and artifacts regularly
