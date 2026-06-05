<!-- file: ACTION_VERSIONS.md -->
<!-- version: 1.0.2 -->
<!-- guid: b2c3d4e5-f6a7-8901-bcde-f12345678901 -->
<!-- last-edited: 2026-01-19 -->

# GitHub Actions Version Reference

This file tracks the pinned versions and commit hashes for all jdfalk/\*
actions.

**Last Updated:** 2025-12-21 11:10:38

## Action Versions

| Action Repository          | Version | Commit Hash | Usage                                                 |
| -------------------------- | ------- | ----------- | ----------------------------------------------------- |
| auto-module-tagging-action | v1.0.0  | `992b70e`   | `falkcorp/gha-auto-module-tagging@992b70e # v1.0.0`   |
| release-docker-action      | v1.0.0  | `7a5440f`   | `falkcorp/gha-release-docker@7a5440f # v1.0.0`        |
| release-frontend-action    | v1.0.0  | `4292378`   | `falkcorp/gha-release-frontend@4292378 # v1.0.0`      |
| release-go-action          | v2.0.1  | `8e3ea4b`   | `falkcorp/gha-release-go@8e3ea4b # v2.0.1`            |
| release-protobuf-action    | v1.0.0  | `0ea205f`   | `falkcorp/gha-release-protobuf-base@0ea205f # v1.0.0` |
| release-python-action      | v1.0.0  | `a5acdd5`   | `falkcorp/gha-release-python@a5acdd5 # v1.0.0`        |
| release-rust-action        | v1.0.0  | `0c21e31`   | `falkcorp/gha-release-rust@0c21e31 # v1.0.0`          |

## Update Instructions

To update action versions:

1. Release a new version of the action (creates tag)
2. Run `scripts/pin-actions-to-hashes.py` to update hashes
3. Commit and push the updated workflows

## Manual Update

If you need to manually update an action:

```yaml
# Get the commit hash for a tag
gh api /repos/jdfalk/ACTION-NAME/git/ref/tags/vX.Y.Z --jq ".object.sha"

# Update in workflow
uses: jdfalk/ACTION-NAME@COMMIT_HASH # vX.Y.Z
```
