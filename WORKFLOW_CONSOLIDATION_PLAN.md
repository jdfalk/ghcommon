<!-- file: WORKFLOW_CONSOLIDATION_PLAN.md -->
<!-- version: 1.0.0 -->
<!-- guid: a1b2c3d4-e5f6-7890-abcd-ef1234567890 -->

# GitHub Workflows Consolidation Plan

**Date**: 2025-12-19 **Author**: GitHub Copilot **Status**: Draft - Awaiting
Approval

## Executive Summary

This plan outlines the consolidation of reusable GitHub Actions workflows from
the `ghcommon` repository into separate, versioned GitHub Actions repositories.
This will improve maintainability, versioning, discoverability, and reusability
across all projects.

## Current State Analysis

### Existing Workflows in ghcommon

Based on analysis of `.github/workflows/*`, we have:

#### Release Workflows (Primary Candidates for Actions)

1. **release-docker.yml** - Docker image building and publishing
2. **release-frontend.yml** - Frontend/Node.js releases
3. **release-go.yml** - Go module releases with SDK support
4. **release-protobuf.yml** - Protocol buffer releases
5. **release-python.yml** - Python package releases
6. **release-rust.yml** - Rust crate releases

#### Automation Workflows (Secondary Candidates)

7. **auto-module-tagging.yml** - Automatic Go module tagging for SDKs
8. **manager-sync-dispatcher.yml** - Repository synchronization dispatcher
   (DISABLED)
9. **sync-receiver.yml** - Repository synchronization receiver (DISABLED)

#### Reusable Workflows (Already Modular, May Convert)

10. **reusable-maintenance.yml** - Dependency updates, cleanup, license checks
11. **reusable-security.yml** - Security scanning and vulnerability checks
12. **reusable-ci.yml** - General CI testing
13. **reusable-protobuf.yml** - Protocol buffer validation and generation
14. **reusable-advanced-cache.yml** - Advanced caching strategies

#### Workflows NOT Candidates for Actions

- **ci.yml**, **ci-tests.yml** - Repository-specific CI
- **documentation.yml** - Repository-specific docs generation
- **issue-automation.yml**, **pr-automation.yml** - Automation specific to
  ghcommon
- **performance-monitoring.yml**, **workflow-analytics.yml** - Monitoring
  specific to ghcommon
- **security.yml** - Calls reusable-security.yml

## Proposed Action Repositories

### Priority 1: Release Actions (High Value, High Reusability)

#### 1. `release-docker-action`

**Repository**: `jdfalk/release-docker-action` **Purpose**: Build and publish
Docker images to multiple registries **Source Workflow**: `release-docker.yml`

**Key Features**:

- Multi-stage Docker builds
- Multi-platform support (linux/amd64, linux/arm64)
- Publishing to Docker Hub, GHCR, and custom registries
- Semantic versioning support
- Build caching optimization
- Security scanning integration

**Inputs**:

```yaml
inputs:
  dockerfile:
    description: 'Path to Dockerfile'
    required: false
    default: 'Dockerfile'
  context:
    description: 'Build context path'
    required: false
    default: '.'
  platforms:
    description: 'Target platforms (comma-separated)'
    required: false
    default: 'linux/amd64,linux/arm64'
  registries:
    description: 'Target registries (comma-separated: dockerhub,ghcr,custom)'
    required: false
    default: 'dockerhub,ghcr'
  tags:
    description: 'Image tags (comma-separated)'
    required: true
  build-args:
    description: 'Build arguments (multiline KEY=VALUE)'
    required: false
  push:
    description: 'Push images to registries'
    required: false
    default: true
```

#### 2. `release-go-action`

**Repository**: `jdfalk/release-go-action` **Purpose**: Release Go modules with
automatic SDK tagging support **Source Workflow**: `release-go.yml`

**Key Features**:

- Go module versioning and tagging
- Automatic SDK module tagging (pkg/module/v1 pattern)
- Cross-compilation for multiple platforms
- Binary artifact uploading
- GoReleaser integration
- Checksum generation
- Release notes automation

**Inputs**:

```yaml
inputs:
  go-version:
    description: 'Go version to use'
    required: false
    default: '1.23'
  platforms:
    description: 'Target platforms for cross-compilation'
    required: false
    default: 'linux/amd64,linux/arm64,darwin/amd64,darwin/arm64,windows/amd64'
  enable-sdk-tagging:
    description: 'Enable automatic SDK module tagging'
    required: false
    default: true
  sdk-path:
    description: 'Path to SDK modules'
    required: false
    default: 'sdks/go/v1'
  use-goreleaser:
    description: 'Use GoReleaser for releases'
    required: false
    default: false
  release-notes:
    description: 'Path to release notes file'
    required: false
```

#### 3. `release-python-action`

**Repository**: `jdfalk/release-python-action` **Purpose**: Build and publish
Python packages to PyPI **Source Workflow**: `release-python.yml`

**Key Features**:

- Build wheel and source distributions
- PyPI and TestPyPI publishing
- Version validation
- Poetry/setuptools support
- Dependency auditing
- Package signing

**Inputs**:

```yaml
inputs:
  python-version:
    description: 'Python version to use'
    required: false
    default: '3.13'
  build-system:
    description: 'Build system (poetry, setuptools, hatch)'
    required: false
    default: 'poetry'
  publish-to:
    description: 'Target repository (pypi, testpypi)'
    required: false
    default: 'pypi'
  package-dir:
    description: 'Package directory'
    required: false
    default: '.'
  skip-existing:
    description: 'Skip upload if version already exists'
    required: false
    default: true
```

#### 4. `release-rust-action`

**Repository**: `jdfalk/release-rust-action` **Purpose**: Build and publish Rust
crates **Source Workflow**: `release-rust.yml`

**Key Features**:

- Cargo build and test
- Crates.io publishing
- Cross-compilation support
- Binary artifact generation
- Documentation generation
- Version validation

**Inputs**:

```yaml
inputs:
  rust-version:
    description: 'Rust toolchain version'
    required: false
    default: 'stable'
  targets:
    description: 'Target triples for cross-compilation'
    required: false
    default: 'x86_64-unknown-linux-gnu,x86_64-apple-darwin,x86_64-pc-windows-msvc'
  publish-to-crates:
    description: 'Publish to crates.io'
    required: false
    default: true
  generate-docs:
    description: 'Generate and publish documentation'
    required: false
    default: true
  package-name:
    description: 'Crate name (if different from repo name)'
    required: false
```

#### 5. `release-frontend-action`

**Repository**: `jdfalk/release-frontend-action` **Purpose**: Build and release
frontend applications **Source Workflow**: `release-frontend.yml`

**Key Features**:

- Node.js/npm/yarn/pnpm support
- Build optimization
- Asset minification
- NPM package publishing
- Static site deployment
- CDN integration

**Inputs**:

```yaml
inputs:
  node-version:
    description: 'Node.js version'
    required: false
    default: '20'
  package-manager:
    description: 'Package manager (npm, yarn, pnpm)'
    required: false
    default: 'npm'
  build-command:
    description: 'Build command'
    required: false
    default: 'npm run build'
  publish-npm:
    description: 'Publish to NPM registry'
    required: false
    default: false
  deploy-target:
    description: 'Deployment target (none, pages, vercel, netlify, s3)'
    required: false
    default: 'none'
```

#### 6. `release-protobuf-action`

**Repository**: `jdfalk/release-protobuf-action` **Purpose**: Validate, build,
and release Protocol Buffer definitions **Source Workflow**:
`release-protobuf.yml`

**Key Features**:

- Buf validation and linting
- Code generation for multiple languages
- SDK packaging and tagging
- Breaking change detection
- Documentation generation
- BSR (Buf Schema Registry) publishing

**Inputs**:

```yaml
inputs:
  buf-version:
    description: 'Buf CLI version'
    required: false
    default: 'latest'
  generate-languages:
    description:
      'Languages to generate (comma-separated: go,python,typescript,rust)'
    required: false
    default: 'go'
  sdk-output-path:
    description: 'Output path for generated SDKs'
    required: false
    default: 'sdks'
  publish-to-bsr:
    description: 'Publish to Buf Schema Registry'
    required: false
    default: false
  breaking-check:
    description: 'Enforce breaking change checks'
    required: false
    default: true
```

### Priority 2: Automation Actions (Medium Value, High Reusability)

#### 7. `auto-module-tagging-action`

**Repository**: `jdfalk/auto-module-tagging-action` **Purpose**: Automatically
create Go module tags for SDK packages **Source Workflow**:
`auto-module-tagging.yml`

**Key Features**:

- Automatic detection of Go SDK modules
- Tag creation for each module version
- Validation of module structure
- Support for multi-module repositories

**Inputs**:

```yaml
inputs:
  version-tag:
    description: 'Base version tag (e.g., v1.3.0)'
    required: true
  sdk-base-path:
    description: 'Base path for SDK modules'
    required: false
    default: 'sdks/go/v1'
  tag-prefix:
    description: 'Prefix for module tags'
    required: false
    default: 'pkg'
  dry-run:
    description: 'Perform dry run without creating tags'
    required: false
    default: false
```

### Priority 3: Reusable Workflow Conversions (Lower Priority)

#### 8. `maintenance-action`

**Repository**: `jdfalk/maintenance-action` **Purpose**: Automated repository
maintenance tasks **Source Workflow**: `reusable-maintenance.yml`

**Key Features**:

- Dependency updates (Go, Python, Rust, Node.js)
- Cache cleanup
- License compliance checking
- Stale issue/PR management
- Security audit

#### 9. `security-scan-action`

**Repository**: `jdfalk/security-scan-action` **Purpose**: Comprehensive
security scanning **Source Workflow**: `reusable-security.yml`

**Key Features**:

- Dependency vulnerability scanning
- SAST (Static Application Security Testing)
- Secret scanning
- Container image scanning
- License compliance

## Implementation Plan

### Phase 1: Repository Creation and Setup (Week 1)

#### Step 1.1: Create Action Repositories

For each action repository:

1. **Create repository via GitHub CLI**:

```bash
gh repo create jdfalk/release-docker-action \
  --public \
  --description "GitHub Action for building and publishing Docker images" \
  --add-readme

gh repo create jdfalk/release-go-action \
  --public \
  --description "GitHub Action for releasing Go modules with SDK support" \
  --add-readme

gh repo create jdfalk/release-python-action \
  --public \
  --description "GitHub Action for building and publishing Python packages" \
  --add-readme

gh repo create jdfalk/release-rust-action \
  --public \
  --description "GitHub Action for building and publishing Rust crates" \
  --add-readme

gh repo create jdfalk/release-frontend-action \
  --public \
  --description "GitHub Action for building and releasing frontend applications" \
  --add-readme

gh repo create jdfalk/release-protobuf-action \
  --public \
  --description "GitHub Action for Protocol Buffer releases and SDK generation" \
  --add-readme

gh repo create jdfalk/auto-module-tagging-action \
  --public \
  --description "GitHub Action for automatic Go module tagging" \
  --add-readme
```

2. **Add repositories to current workspace**:

```bash
cd /Users/jdfalk/repos/github.com/jdfalk
git clone https://github.com/jdfalk/release-docker-action.git
git clone https://github.com/jdfalk/release-go-action.git
git clone https://github.com/jdfalk/release-python-action.git
git clone https://github.com/jdfalk/release-rust-action.git
git clone https://github.com/jdfalk/release-frontend-action.git
git clone https://github.com/jdfalk/release-protobuf-action.git
git clone https://github.com/jdfalk/auto-module-tagging-action.git
```

3. **Initialize each repository with standard structure**:

```
action-repo/
├── action.yml (or action.yaml)
├── README.md
├── LICENSE
├── .github/
│   ├── workflows/
│   │   ├── test.yml
│   │   ├── release.yml
│   │   └── ci.yml
│   └── ISSUE_TEMPLATE/
├── src/ (if using TypeScript/JavaScript action)
├── dist/ (compiled action code)
└── examples/
    └── basic-usage.yml
```

#### Step 1.2: Extract and Convert Workflows

For each action:

1. **Extract workflow logic** from ghcommon workflow file
2. **Convert to composite action** (`action.yml`)
3. **Create action metadata** with inputs/outputs
4. **Add comprehensive README** with usage examples
5. **Setup CI/CD** for the action itself
6. **Create initial release** (v1.0.0)

### Phase 2: Action Development (Weeks 2-3)

#### Standard Action Template Structure

Each action will follow this structure:

**action.yml** (Composite Action):

```yaml
name: 'Release [Technology] Action'
description: '[Description of what the action does]'
author: 'jdfalk'

branding:
  icon: 'package'
  color: 'blue'

inputs:
  # Technology-specific inputs

outputs:
  # Technology-specific outputs

runs:
  using: 'composite'
  steps:
    - name: Validate inputs
      shell: bash
      run: |
        # Input validation logic

    - name: Setup environment
      shell: bash
      run: |
        # Environment setup

    - name: Execute main action logic
      shell: bash
      run: |
        # Core action functionality

    - name: Generate outputs
      shell: bash
      run: |
        # Output generation
```

#### Priority Order for Development

1. **Week 2**:
   - release-docker-action (most straightforward)
   - release-go-action (most complex, includes SDK tagging)
   - release-python-action

2. **Week 3**:
   - release-rust-action
   - release-frontend-action
   - release-protobuf-action
   - auto-module-tagging-action

### Phase 3: Testing and Documentation (Week 4)

#### For Each Action

1. **Create test workflows** in the action repository
2. **Test in real repositories**:
   - audiobook-organizer (Go, Docker)
   - subtitle-manager (Go, Docker, Protobuf)
   - copilot-agent-util-rust (Rust)
   - apt-cacher-go (Go, Docker)

3. **Documentation**:
   - Comprehensive README with examples
   - Input/output documentation
   - Versioning guide
   - Migration guide from old workflows

4. **Security**:
   - Secret handling best practices
   - Dependabot configuration
   - Security policy

### Phase 4: Migration (Week 5)

#### Update Consuming Repositories

For each repository using ghcommon workflows:

1. **Replace workflow calls** with action usage:

**Before** (using ghcommon workflow):

```yaml
jobs:
  release:
    uses: jdfalk/ghcommon/.github/workflows/release-docker.yml@main
    with:
      dockerfile: Dockerfile
      platforms: linux/amd64,linux/arm64
    secrets: inherit
```

**After** (using action):

```yaml
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: jdfalk/release-docker-action@v1
        with:
          dockerfile: Dockerfile
          platforms: linux/amd64,linux/arm64
          registries: dockerhub,ghcr
```

2. **Test thoroughly** in each repository
3. **Update documentation**
4. **Remove deprecated workflows** from ghcommon

### Phase 5: Maintenance and Iteration (Ongoing)

1. **Versioning**: Use semantic versioning for all actions
2. **Release management**: Major/minor/patch releases as needed
3. **Community support**: Issues, PRs, discussions
4. **Documentation updates**: Keep examples current
5. **Security updates**: Regular dependency updates

## Benefits

### For Action Repositories

1. **Independent Versioning**: Each action can evolve independently
2. **Focused Development**: Smaller, more maintainable codebases
3. **Better Testing**: Dedicated test suites per action
4. **Clear Ownership**: Each action has its own repository
5. **Discoverability**: Actions appear in GitHub Marketplace

### For Consuming Repositories

1. **Explicit Dependencies**: Pin action versions with `@v1` tags
2. **Faster Updates**: Update actions independently
3. **Better Documentation**: Action-specific docs in each repo
4. **Reduced Coupling**: No dependency on ghcommon repository
5. **Improved Security**: Actions can be audited independently

### For Organization

1. **Reusability**: Actions usable by any repository, even outside organization
2. **Community Contribution**: Others can contribute improvements
3. **Standardization**: Consistent release processes across all projects
4. **Maintenance**: Easier to maintain focused actions vs. monolithic workflows
5. **Visibility**: Actions in marketplace increase project visibility

## Migration Strategy

### Backward Compatibility

1. **Keep ghcommon workflows** for 3 months after action releases
2. **Add deprecation notices** to ghcommon workflows
3. **Create migration guide** for each workflow → action conversion
4. **Provide side-by-side examples**

### Rollout Plan

1. **Week 1-3**: Create and develop actions
2. **Week 4**: Test in 1-2 repositories
3. **Week 5**: Migrate 50% of repositories
4. **Week 6**: Migrate remaining repositories
5. **Month 2-3**: Deprecation period for ghcommon workflows
6. **Month 4**: Remove deprecated ghcommon workflows

## Technical Considerations

### Action Type: Composite vs. JavaScript vs. Docker

**Recommendation**: Use **Composite Actions** for all release actions because:

- ✅ No compilation step required
- ✅ Easier to maintain and debug
- ✅ Direct use of existing shell scripts
- ✅ Better performance (no container startup)
- ✅ Transparent execution (visible steps)

**JavaScript Actions**: Consider for future utility actions that need:

- Complex logic
- API integrations
- Node.js ecosystem tools

**Docker Actions**: Avoid unless specific containerization required

### Secrets Handling

Actions cannot directly access secrets. Pattern:

```yaml
# In consuming repository workflow
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: jdfalk/release-docker-action@v1
        with:
          registries: dockerhub,ghcr
        env:
          DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
          DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Versioning Strategy

1. **Major versions** (v1, v2, v3): Breaking changes
2. **Minor versions** (v1.1, v1.2): New features, backward compatible
3. **Patch versions** (v1.1.1, v1.1.2): Bug fixes

Use **major version tags** for ease of use:

```yaml
uses: jdfalk/release-docker-action@v1  # Tracks latest v1.x.x
uses: jdfalk/release-docker-action@v1.2  # Tracks latest v1.2.x
uses: jdfalk/release-docker-action@v1.2.3  # Specific version
```

## Repository Structure Example

### release-docker-action Repository

```
release-docker-action/
├── action.yml                    # Action definition
├── README.md                     # Comprehensive documentation
├── LICENSE                       # MIT License
├── CHANGELOG.md                  # Version history
├── .github/
│   ├── workflows/
│   │   ├── test.yml             # Test action on push
│   │   ├── release.yml          # Create releases
│   │   └── ci.yml               # Continuous integration
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml           # Dependency updates
├── scripts/
│   ├── build-docker.sh          # Main build script
│   ├── validate-inputs.sh       # Input validation
│   └── publish-images.sh        # Publishing logic
├── examples/
│   ├── basic-usage.yml          # Simple example
│   ├── multi-platform.yml       # Multi-platform build
│   ├── multiple-registries.yml  # Multiple registries
│   └── advanced.yml             # Advanced configuration
└── docs/
    ├── inputs.md                # Detailed input documentation
    ├── outputs.md               # Output documentation
    ├── migration.md             # Migration from workflows
    └── troubleshooting.md       # Common issues
```

## Success Criteria

1. ✅ All 7 priority actions created and released
2. ✅ Each action has comprehensive documentation
3. ✅ Each action has test coverage
4. ✅ At least 2 real repositories using each action
5. ✅ Migration guide for each ghcommon workflow
6. ✅ Deprecation notices in ghcommon
7. ✅ No breaking changes for consuming repositories during migration
8. ✅ Performance equal to or better than ghcommon workflows
9. ✅ Security review completed for all actions
10. ✅ Community contribution guidelines in place

## Risks and Mitigation

| Risk                         | Impact | Mitigation                                                       |
| ---------------------------- | ------ | ---------------------------------------------------------------- |
| Breaking changes in actions  | High   | Semantic versioning, deprecation notices, migration guides       |
| Action dependencies outdated | Medium | Dependabot, regular maintenance schedule                         |
| Security vulnerabilities     | High   | Security scanning, audit logging, secret handling best practices |
| Migration complexity         | Medium | Gradual rollout, side-by-side running, comprehensive testing     |
| Documentation gaps           | Low    | Template-based docs, peer review, user feedback                  |
| Maintenance burden           | Medium | Automation, clear ownership, community contributions             |

## Next Steps (Pending Approval)

1. **Approve this plan** ✋ **(WAITING FOR YOUR APPROVAL)**
2. **Create action repositories** via GitHub CLI/MCP tools
3. **Clone repositories** to local workspace
4. **Begin Phase 1**: Repository setup and structure creation
5. **Begin Phase 2**: Extract and convert first 3 actions
6. **Schedule reviews**: End of each phase

## Timeline Summary

| Phase   | Duration  | Activities                 | Deliverables                      |
| ------- | --------- | -------------------------- | --------------------------------- |
| Phase 1 | Week 1    | Repository creation, setup | 7 action repositories initialized |
| Phase 2 | Weeks 2-3 | Action development         | 7 working actions with tests      |
| Phase 3 | Week 4    | Testing, documentation     | Tested actions, complete docs     |
| Phase 4 | Week 5    | Migration                  | Updated consuming repositories    |
| Phase 5 | Ongoing   | Maintenance                | Continued support and updates     |

**Total Initial Effort**: ~5 weeks for full implementation **Ongoing Effort**:
~4-8 hours/month for maintenance

## Questions for Consideration

1. Should we create **all actions at once** or prioritize certain ones?
2. Should actions be **public immediately** or start as private?
3. Do we want to enable **GitHub Marketplace** listing?
4. Should we include **telemetry/analytics** in actions?
5. What **support level** are we committing to for these actions?
6. Should we create a **mono-repo** for all actions or separate repos?
   (Recommendation: Separate)

## Conclusion

This consolidation will significantly improve the maintainability,
discoverability, and reusability of our release automation. By creating focused,
well-documented GitHub Actions, we enable not only our own projects but
potentially the broader community to benefit from our release workflows.

**Recommendation**: Proceed with implementation, starting with Priority 1
actions (release-docker-action, release-go-action, release-python-action) as
proof of concept, then expand to remaining actions based on learnings.

---

**Awaiting approval to proceed with implementation.** 🚀
