<!-- file: ACTION_VERSIONS.md -->
<!-- version: 1.0.0 -->
<!-- guid: b2c3d4e5-f6a7-8901-bcde-f12345678901 -->

# GitHub Actions Version Reference

This file tracks the pinned versions and commit hashes for all jdfalk/\* actions.

**Last Updated:** 2025-12-19 13:05:05

## Action Versions

| Action Repository          | Version | Commit Hash | Usage                                                |
| -------------------------- | ------- | ----------- | ---------------------------------------------------- |
| auto-module-tagging-action | v1.0.0  | `7deb63a`   | `jdfalk/auto-module-tagging-action@7deb63a # v1.0.0` |
| release-docker-action      | v1.0.0  | `7a5440f`   | `jdfalk/release-docker-action@7a5440f # v1.0.0`      |
| release-frontend-action    | v1.0.0  | `db00d5a`   | `jdfalk/release-frontend-action@db00d5a # v1.0.0`    |
| release-go-action          | v2.0.0  | `97aa844`   | `jdfalk/release-go-action@97aa844 # v2.0.0`          |
| release-protobuf-action    | v1.0.0  | `be2b747`   | `jdfalk/release-protobuf-action@be2b747 # v1.0.0`    |
| release-python-action      | v1.0.0  | `a456dbe`   | `jdfalk/release-python-action@a456dbe # v1.0.0`      |
| release-rust-action        | v1.0.0  | `900408d`   | `jdfalk/release-rust-action@900408d # v1.0.0`        |

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
