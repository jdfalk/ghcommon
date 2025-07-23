<!-- file: PACKAGE_NAMING_RESOLUTION.md -->
<!-- version: 1.0.0 -->
<!-- guid: 7dbb26f1-96fb-42db-bae1-38799f9a0012 -->

# Package Naming Resolution

This document tracks the agreed-upon package naming conventions for all gcommon protobuf definitions.

## Conventions

- All packages follow the format `gcommon.v1.<module>`.
- Go package option uses the module path `github.com/jdfalk/gcommon/proto/gcommon/v1` with an appropriate import alias.
- Edition 2023 is required for all proto files.

These rules ensure consistency across modules as we complete remaining protobuf implementations.

This document explains package names used for generated protobuf code.

- Go packages follow the pattern `github.com/jdfalk/ghcommon/proto/<path>`.
- Protobuf packages use the `gcommon.v1.<service>` namespace.
