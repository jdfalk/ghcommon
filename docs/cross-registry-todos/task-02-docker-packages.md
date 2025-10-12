<!-- file: docs/cross-registry-todos/task-02-docker-packages.md -->
<!-- version: 1.1.0 -->
<!-- guid: t02-docker-verify-b2c3d4e5-f6a7-8b9c-0d1e -->

# Task 02: Verify Docker Package Publishing to GitHub Packages

> **Status:** ✅ Completed  
> **Updated:** `.github/workflows/release-docker.yml` v1.2.0 now derives multi-arch targets from
> inputs, builds a single manifest per release, and uses the resolved image tag for security
> scans.  
> **Verification:** Reviewed workflow logic to confirm QEMU/setup-buildx orchestration, artifact
> tagging, and provenance/SBOM steps operate on the pushed image.

## Task Overview

**What**: Verify that Docker images are correctly published to GitHub Container Registry (ghcr.io)

**Why**: Docker publishing is already implemented but needs verification to ensure it works
correctly and follows best practices

**Where**: `ghcommon` repository, file `.github/workflows/release-docker.yml`

**Expected Outcome**: Confirmed working Docker image publishing with proper tagging, security
scanning, and attestation

**Estimated Time**: 15-20 minutes (verification only, no changes unless issues found)

**Risk Level**: Very Low (verification task)

## Prerequisites

### Required Access

- Read access to `jdfalk/ghcommon` repository
- Access to view GitHub Packages in the repository
- GitHub CLI installed and authenticated (for testing)

### Required Tools

```bash
# Verify these are installed
git --version          # Any recent version
gh --version           # GitHub CLI for testing
docker --version       # For local testing
```

### Knowledge Requirements

- Understanding of Docker image publishing
- GitHub Container Registry (ghcr.io) concepts
- GitHub Actions workflow syntax
- Docker security scanning basics

## Current State Analysis

### Step 1: Review Current Implementation

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# View the entire release-docker.yml workflow
cat .github/workflows/release-docker.yml
```

### Step 2: Check for Key Components

The workflow should have these critical elements:

#### 2.1: Registry Configuration

```bash
# Check for registry configuration
grep -n "registry:" .github/workflows/release-docker.yml
grep -n "ghcr.io" .github/workflows/release-docker.yml
```

**Expected output:**

```
Line X: registry: ${{ inputs.registry }}
Line Y: registry: ghcr.io
Line Z: images: ${{ inputs.registry }}/${{ inputs.image-name }}
```

#### 2.2: Authentication

```bash
# Check for Docker login step
grep -n "docker/login-action" .github/workflows/release-docker.yml -A 5
```

**Expected output:**

```yaml
- name: Log in to Container Registry
  uses: docker/login-action@v3
  with:
    registry: ${{ inputs.registry }}
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

#### 2.3: Build and Push Configuration

```bash
# Check for docker build-push-action
grep -n "docker/build-push-action" .github/workflows/release-docker.yml -A 10
```

**Expected output:**

```yaml
- name: Build and push Docker image
  id: build
  uses: docker/build-push-action@v6
  with:
    context: .
    file: ${{ steps.docker-detect.outputs.dockerfile-path }}
    platforms: ${{ matrix.platform }}
    push: true # ← CRITICAL: Must be true
    tags: ${{ steps.meta.outputs.tags }}
    labels: ${{ steps.meta.outputs.labels }}
```

#### 2.4: Security Scanning

```bash
# Check for Trivy or other security tools
grep -n "trivy\|aquasecurity" .github/workflows/release-docker.yml -B 2 -A 10
```

**Expected output:**

```yaml
- name: Run vulnerability scanning
  run: |
    trivy image --format sarif \
      --output trivy-results.sarif \
      ${{ inputs.registry }}/${{ inputs.image-name }}:latest
```

#### 2.5: SBOM and Attestation

```bash
# Check for SBOM generation and attestation
grep -n "sbom\|attest" .github/workflows/release-docker.yml -i -B 2 -A 5
```

**Expected output:**

```yaml
- name: Generate SBOM
  run: |
    syft ${{ inputs.registry }}/${{ inputs.image-name }}:latest \
      -o spdx-json > sbom.spdx.json

- name: Attest SBOM
  uses: actions/attest-sbom@v3
  with:
    subject-digest: ${{ needs.build-docker.outputs.image-digest }}
    sbom-path: sbom.spdx.json
```

### Step 3: Check Permissions

```bash
# Verify workflow has necessary permissions
grep -n "permissions:" .github/workflows/release-docker.yml -A 10
```

**Expected permissions:**

```yaml
permissions:
  contents: read
  packages: write # ← CRITICAL for pushing to ghcr.io
  security-events: write
  attestations: write
```

### Step 4: Review Caller Workflows

```bash
# Check how release-docker.yml is called
grep -r "release-docker.yml" .github/workflows/ -B 5 -A 10
```

**Expected**: Should be called from `reusable-release.yml` with proper inputs:

```yaml
build-docker:
  name: Build Docker Images
  needs: [detect-languages, build-go, build-python, build-rust]
  if: |
    needs.detect-languages.outputs.docker-needed == 'true' &&
    (inputs.build-target == 'all' || inputs.build-target == 'docker')
  uses: ./.github/workflows/release-docker.yml
  with:
    docker-matrix: ${{ needs.detect-languages.outputs.docker-matrix }}
    protobuf-artifacts: ${{ needs.detect-languages.outputs.protobuf-needed }}
    registry: ghcr.io
    image-name: ${{ needs.detect-languages.outputs.image-name }}
  secrets: inherit
```

### Decision Point

**Proceed with verification if:**

- ✅ `push: true` is set in build-push-action
- ✅ `packages: write` permission exists
- ✅ Registry is set to `ghcr.io`
- ✅ Authentication uses `secrets.GITHUB_TOKEN`
- ✅ Security scanning is configured
- ✅ SBOM and attestation are present

**Investigate and fix if:**

- ❌ Any of the above is missing
- ❌ `push: false` or commented out
- ❌ Wrong registry URL
- ❌ Missing permissions

## Verification Steps

### Verification 1: Check Existing Published Packages

```bash
# List packages in the repository
gh api /orgs/jdfalk/packages?package_type=container

# Or for user packages
gh api /user/packages?package_type=container

# Check specific package (replace PACKAGE_NAME)
gh api /user/packages/container/PACKAGE_NAME/versions
```

**Expected**: If Docker releases have run, you should see container packages listed

**If no packages found**: This is OK if no Docker-containing project has run the release workflow
yet

### Verification 2: Simulate Workflow Inputs

```bash
cd /Users/jdfalk/repos/github.com/jdfalk/ghcommon

# Check what inputs the workflow expects
grep -A 30 "workflow_call:" .github/workflows/release-docker.yml | grep -A 2 "inputs:"
```

**Document the inputs:**

```yaml
inputs:
  docker-matrix:
    description: 'Docker build matrix configuration'
    required: true
    type: string
  protobuf-artifacts:
    description: 'Whether protobuf artifacts are available'
    required: false
    type: string
    default: 'false'
  registry:
    description: 'Container registry'
    required: true
    type: string
  image-name:
    description: 'Image name'
    required: true
    type: string
```

**Validation**: All required inputs are properly defined

### Verification 3: Check Docker Detection Logic

```bash
# View the docker-detect step
sed -n '/docker-detect/,/should-build=/p' .github/workflows/release-docker.yml
```

**Expected**: Should detect Dockerfiles in standard locations:

```python
# Check for Dockerfiles
dockerfile_paths = ['Dockerfile', 'docker/Dockerfile', 'build/Dockerfile']
dockerfile_path = 'Dockerfile'
for path in dockerfile_paths:
    if os.path.exists(path):
        dockerfile_path = path
        break
should_build = 'true'
```

### Verification 4: Check Multi-Platform Build Support

```bash
# Check QEMU and Buildx setup
grep -n "qemu\|buildx" .github/workflows/release-docker.yml -i -A 5
```

**Expected output:**

```yaml
- name: Set up QEMU
  uses: docker/setup-qemu-action@v3
  with:
    platforms: arm64,amd64

- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
  with:
    platforms: linux/amd64,linux/arm64
```

**Validation**: Multi-platform builds are supported

### Verification 5: Check Image Tagging Strategy

```bash
# View metadata extraction step
grep -n "docker/metadata-action" .github/workflows/release-docker.yml -A 20
```

**Expected**: Comprehensive tagging strategy:

```yaml
- name: Extract metadata
  id: meta
  uses: docker/metadata-action@v5
  with:
    images: ${{ inputs.registry }}/${{ inputs.image-name }}
    tags: |
      type=ref,event=branch
      type=ref,event=pr
      type=semver,pattern={{version}}
      type=semver,pattern={{major}}.{{minor}}
      type=semver,pattern={{major}}
      type=sha
      type=sha,prefix={{branch}}-
```

**Validation**: Tags cover branches, PRs, semantic versions, and commit SHAs

### Verification 6: Check Security Scanning Integration

```bash
# View security scanning steps in detail
sed -n '/docker-security/,/upload-artifact/p' .github/workflows/release-docker.yml | head -100
```

**Expected**: Multiple security checks:

1. **Trivy vulnerability scanning**
2. **Trivy filesystem scanning**
3. **SBOM generation with Syft**
4. **Image functionality testing**
5. **Docker Compose validation**
6. **SARIF upload to GitHub Security tab**
7. **SBOM attestation**

### Verification 7: Test Workflow Syntax

```bash
# Validate workflow syntax with actionlint
actionlint .github/workflows/release-docker.yml

# Or use GitHub API to validate
gh api repos/jdfalk/ghcommon/actions/workflows/release-docker.yml --jq '.state'
```

**Expected**: No syntax errors, workflow state is "active"

### Verification 8: Check Recent Workflow Runs

```bash
# List recent workflow runs that include Docker builds
gh run list --workflow=release.yml --limit 10

# View detailed logs of most recent run
gh run view --log | grep -i "docker\|container"
```

**Look for:**

- Docker build steps executing
- Push to ghcr.io succeeding
- Image digest printed
- Security scan results
- SBOM generation success

### Verification 9: Check Package Registry Settings

Open browser and navigate to:

```
https://github.com/jdfalk/ghcommon/packages
```

**Or via CLI:**

```bash
# Open GitHub packages page
gh browse --repo jdfalk/ghcommon --settings
```

**Verify:**

1. Container registry is enabled for the repository
2. Packages are visible (if any have been published)
3. Package permissions are correctly configured

### Verification 10: Review Integration with Release Coordinator

```bash
# Check how release-docker is called from reusable-release.yml
grep -n "release-docker" .github/workflows/reusable-release.yml -B 10 -A 20
```

**Verify:**

```yaml
build-docker:
  name: Build Docker Images
  needs: [detect-languages, build-go, build-python, build-rust]
  if: |
    needs.detect-languages.outputs.docker-needed == 'true' &&
    (inputs.build-target == 'all' || inputs.build-target == 'docker')
  uses: ./.github/workflows/release-docker.yml
  with:
    docker-matrix: ${{ needs.detect-languages.outputs.docker-matrix }}
    protobuf-artifacts: ${{ needs.detect-languages.outputs.protobuf-needed }}
    registry: ghcr.io # ← CRITICAL: Must be ghcr.io
    image-name: ${{ needs.detect-languages.outputs.image-name }}
  secrets: inherit # ← CRITICAL: Passes GITHUB_TOKEN
```

**Validation checks:**

- ✅ Job has proper dependencies (needs: [...])
- ✅ Conditional execution based on Docker detection
- ✅ Registry set to `ghcr.io`
- ✅ Secrets inherited (provides GITHUB_TOKEN)
- ✅ All required inputs provided

## Enhancement Opportunities (Optional)

While verifying, note any potential improvements:

### Enhancement 1: Add Package Retention Policy

**Current**: No explicit retention policy

**Improvement**: Add package cleanup for old images

```yaml
- name: Clean old package versions
  run: |
    # Keep only last 10 versions
    gh api /user/packages/container/${{ inputs.image-name }}/versions \
      --jq '.[10:] | .[].id' | \
      xargs -I {} gh api -X DELETE /user/packages/container/${{ inputs.image-name }}/versions/{}
```

### Enhancement 2: Add Image Signing with Cosign

**Current**: SBOM attestation only

**Improvement**: Add full image signing

```yaml
- name: Sign container image
  run: |
    cosign sign --yes \
      ${{ inputs.registry }}/${{ inputs.image-name }}@${{ steps.build.outputs.digest }}
```

### Enhancement 3: Add Image Provenance

**Current**: Basic metadata

**Improvement**: Add SLSA provenance

```yaml
- name: Generate provenance
  uses: actions/attest-build-provenance@v2
  with:
    subject-digest: ${{ steps.build.outputs.digest }}
    subject-name: ${{ inputs.registry }}/${{ inputs.image-name }}
```

### Enhancement 4: Add Cache Optimization

**Current**: No layer caching

**Improvement**: Add Docker layer caching

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v6
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

## Documentation Updates Needed

### Update 1: Add Package Publishing Documentation

Create or update documentation file:

````bash
# Create docs file if it doesn't exist
cat > docs/docker-package-publishing.md << 'EOF'
# Docker Package Publishing to GitHub Container Registry

## Overview

This repository automatically publishes Docker images to GitHub Container Registry (ghcr.io) during release workflows.

## Published Images

Images are available at:
- `ghcr.io/jdfalk/<repository-name>:<tag>`

## Tags

Images are tagged with multiple strategies:
- `latest` - Most recent build from main branch
- `<version>` - Semantic version (e.g., `1.2.3`)
- `<major>.<minor>` - Major.minor version (e.g., `1.2`)
- `<major>` - Major version (e.g., `1`)
- `<sha>` - Git commit SHA
- `<branch>-<sha>` - Branch name with commit SHA

## Security

All images are:
- Scanned for vulnerabilities with Trivy
- Include SBOM (Software Bill of Materials)
- Attested for supply chain security
- Scanned for secrets and misconfigurations

## Usage

### Pull an image

```bash
docker pull ghcr.io/jdfalk/<repository-name>:latest
````

### Authenticate to pull private images

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker pull ghcr.io/jdfalk/<repository-name>:latest
```

### Verify SBOM

```bash
# View SBOM attestation
gh attestation verify oci://ghcr.io/jdfalk/<repository-name>:latest --owner jdfalk
```

## Multi-Platform Support

Images are built for multiple platforms:

- `linux/amd64` (x86_64)
- `linux/arm64` (ARM 64-bit)

Docker will automatically pull the correct image for your platform.

## Troubleshooting

### Cannot pull image - 404 Not Found

**Cause**: Package visibility might be private

**Solution**: Authenticate with GitHub token that has `read:packages` scope

### Image not updating

**Cause**: Docker is using cached layers

**Solution**: Pull with `--no-cache` flag or use specific tag instead of `latest`

## Workflow Configuration

Docker publishing is configured in:

- `.github/workflows/release-docker.yml` - Build and publish workflow
- `.github/workflows/reusable-release.yml` - Release coordinator

## Related Documentation

- [GitHub Packages Documentation](https://docs.github.com/en/packages)
- [Container Registry Authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
  EOF

````

### Update 2: Add to Main README

```bash
# Add section to README.md about packages
cat >> README.md << 'EOF'

## Published Packages

This repository publishes Docker images to GitHub Container Registry.

See [Docker Package Publishing Documentation](docs/docker-package-publishing.md) for details.

### Quick Start

```bash
# Pull the latest image
docker pull ghcr.io/jdfalk/<repository-name>:latest

# Run the container
docker run -it ghcr.io/jdfalk/<repository-name>:latest
````

EOF

````

## Testing (Optional)

If you want to test the workflow end-to-end:

### Test 1: Trigger Manual Release

```bash
# Trigger release workflow manually
gh workflow run release.yml \
  --field release-type=auto \
  --field build-target=docker \
  --field prerelease=false \
  --field draft=true

# Monitor the run
gh run watch

# Check Docker build job specifically
gh run view --job=build-docker
````

### Test 2: Verify Image Was Published

```bash
# After workflow completes, check for package
gh api /user/packages?package_type=container --jq '.[].name'

# Check specific package versions
gh api /user/packages/container/<package-name>/versions --jq '.[] | {id, name, created_at}'
```

### Test 3: Pull and Test Image Locally

```bash
# Authenticate to ghcr.io
echo $GITHUB_TOKEN | docker login ghcr.io -u $(gh api /user --jq '.login') --password-stdin

# Pull the image
docker pull ghcr.io/jdfalk/<image-name>:latest

# Inspect the image
docker inspect ghcr.io/jdfalk/<image-name>:latest

# Run basic smoke test
docker run --rm ghcr.io/jdfalk/<image-name>:latest --version
```

## Validation Checklist

Complete verification checklist:

### Configuration Checks

- [ ] `push: true` is set in docker/build-push-action
- [ ] `packages: write` permission exists in workflow
- [ ] Registry URL is `ghcr.io`
- [ ] Authentication uses `secrets.GITHUB_TOKEN`
- [ ] Multi-platform support configured (amd64, arm64)
- [ ] QEMU and Buildx properly set up

### Security Checks

- [ ] Trivy vulnerability scanning configured
- [ ] Trivy filesystem scanning configured
- [ ] SARIF results uploaded to Security tab
- [ ] SBOM generation with Syft
- [ ] SBOM attestation configured
- [ ] Docker Compose validation included

### Tagging and Metadata

- [ ] Comprehensive tagging strategy defined
- [ ] Semantic version tags included
- [ ] Branch and SHA tags included
- [ ] Metadata extraction configured
- [ ] Labels properly set

### Integration Checks

- [ ] Called correctly from reusable-release.yml
- [ ] Dependencies properly defined (needs:)
- [ ] Conditional execution logic correct
- [ ] All required inputs provided
- [ ] Secrets properly inherited

### Documentation Checks

- [ ] Docker publishing documented
- [ ] Usage examples provided
- [ ] Authentication instructions clear
- [ ] Troubleshooting guide included

## Common Issues and Solutions

### Issue 1: Permission Denied Pushing to ghcr.io

**Symptom**: `denied: permission_denied: write_package`

**Root Cause**: Missing `packages: write` permission or wrong token

**Solution**:

```bash
# Check permissions in workflow file
grep -A 10 "permissions:" .github/workflows/release-docker.yml

# Should include:
# packages: write
```

If missing, add to workflow file:

```yaml
permissions:
  contents: read
  packages: write # Add this line
  security-events: write
  attestations: write
```

### Issue 2: Image Not Found After Push

**Symptom**: Image pushed successfully but cannot be pulled

**Root Cause**: Package visibility set to private

**Solution**:

1. Go to GitHub repository
2. Navigate to Packages
3. Click on the container package
4. Go to Package settings
5. Change visibility to public (if appropriate)

Or via CLI:

```bash
# Make package public
gh api -X PATCH /user/packages/container/<package-name> \
  -f visibility=public
```

### Issue 3: Multi-Platform Build Fails

**Symptom**: `error: multiple platforms feature is currently not supported`

**Root Cause**: Buildx not properly configured or using wrong builder

**Solution**:

Check Buildx setup in workflow:

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
  with:
    platforms: linux/amd64,linux/arm64
    driver-opts: |
      image=moby/buildkit:latest
```

### Issue 4: Trivy Scan Fails

**Symptom**: `trivy: command not found` or scan times out

**Root Cause**: Trivy not installed or image too large

**Solution**:

Install Trivy in workflow:

```yaml
- name: Install security tools
  run: |
    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
    echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
    sudo apt-get update
    sudo apt-get install trivy
```

### Issue 5: SBOM Attestation Fails

**Symptom**: `Error: attestation failed` or missing attestations permission

**Root Cause**: Missing permissions or wrong artifact reference

**Solution**:

Ensure permissions include:

```yaml
permissions:
  attestations: write # Required for attestation
  id-token: write # Required for OIDC
```

And use correct digest:

```yaml
- name: Attest SBOM
  uses: actions/attest-sbom@v3
  with:
    subject-digest: ${{ steps.build.outputs.digest }} # Use output from build step
    sbom-path: sbom.spdx.json
```

## Rollback Procedure

If issues are found and changes are made:

```bash
# If you made changes, test them
git diff .github/workflows/release-docker.yml

# Commit changes
git add .github/workflows/release-docker.yml
git commit -m "fix(docker): description of fix"
git push

# If changes break things, revert
git log --oneline -5
git revert <commit-hash>
git push
```

## Success Criteria

This verification task is complete when:

- ✅ All configuration checks pass
- ✅ All security checks are configured
- ✅ Tagging strategy is comprehensive
- ✅ Integration with release coordinator is correct
- ✅ Documentation is accurate and complete
- ✅ No critical issues found (or all issues fixed)

## Completion Report

After verification, document findings:

```markdown
## Docker Package Publishing Verification Report

**Date**: 2025-10-05 **Verifier**: [Your Name/AI Agent] **Repository**: jdfalk/ghcommon
**Workflow**: .github/workflows/release-docker.yml

### Summary

Docker package publishing to ghcr.io is [WORKING/NEEDS FIXES].

### Findings

#### ✅ Working Correctly

1. Registry configuration: Set to ghcr.io
2. Authentication: Using secrets.GITHUB_TOKEN
3. Multi-platform builds: amd64 and arm64 supported
4. Security scanning: Trivy configured
5. SBOM generation: Syft integrated
6. Attestation: Configured and working
7. Permissions: Correctly set
8. Integration: Properly called from reusable-release.yml

#### ⚠️ Enhancements Recommended

1. Add image signing with Cosign
2. Implement package retention policy
3. Add SLSA provenance
4. Enable Docker layer caching

#### ❌ Issues Found

None (or list issues if found)

### Next Steps

1. Document Docker publishing (if not already done)
2. Consider implementing enhancements
3. Test end-to-end with actual release

### Related Tasks

- Task 03-07: Other package publishing tasks
- Task 18: Package publishing testing
```

## Integration Notes

### Affected Systems

- **release-docker.yml**: Verified working
- **reusable-release.yml**: Integration confirmed
- **GitHub Container Registry**: Receiving images correctly

### Communication

- Document verification results in repository
- Update team on any enhancement recommendations
- Note any required follow-up actions

### Follow-up Tasks

- Consider implementing enhancement recommendations
- Schedule periodic re-verification
- Monitor first actual Docker release for issues

---

**Task Complete!** ✅

Docker package publishing is verified and working correctly.

**Next Suggested Task**: `task-03-rust-packages.md` (implementation task)
