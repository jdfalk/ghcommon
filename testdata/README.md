# file: testdata/README.md
# version: 1.0.0
# guid: 5a7f9d2c-4b3e-4e51-9f2f-2c3d4a5b6c7d

# Test Data Fixtures

This directory contains minimal language fixtures used to validate the reusable
CI/release workflows end-to-end. Each subdirectory holds a self-contained
“hello world” style project that exercises the corresponding toolchain.

| Language / Stack | Entry Point | Notes |
| --- | --- | --- |
| Python | `python/hello_world.py` | Prints a success banner when executed. |
| Go | `go/main.go` | Builds a CLI that prints greeting text. |
| Rust | `rust/src/main.rs` | Cargo project with single binary target. |
| Node.js | `node/index.js` | Simple script managed by `npm run start`. |
| Docker | `docker/Dockerfile` | Multi-stage image that copies the Go sample. |
| Protobuf | `protobuf/hello.proto` | Trivial message to drive code generation. |

> The fixtures are intentionally lightweight. They should build quickly while
> touching the critical paths for each language’s workflow steps.
