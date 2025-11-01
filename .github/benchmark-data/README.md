# file: .github/benchmark-data/README.md

# version: 1.0.0

# guid: benchmark-data-readme-2025-10-automation

Benchmark suites write their historical data here via `github-action-benchmark`. Each JSON file is
generated automatically by the CI workflows and is **not** intended for manual editing. The files
are committed so developers can review changes locally and provide baselines for new suites.

Files:

- `rust.json`
- `node.json`
- `python.json`

The CI jobs upload the same files as artifacts to preserve history after runs on forks. Downstream
repositories can add additional suites by following the same naming convention.
