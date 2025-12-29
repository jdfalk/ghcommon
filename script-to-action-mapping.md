# Script to Action Mapping

## Already Covered by Existing Actions ✅

| Script                                    | Existing Action            | Notes                              |
| ----------------------------------------- | -------------------------- | ---------------------------------- |
| detect_languages.py / detect-languages.sh | detect-languages-action    | ✅ Already exists                  |
| generate-version.sh                       | generate-version-action    | ✅ Already exists                  |
| release-strategy.sh                       | release-strategy-action    | ✅ Already exists                  |
| load_repository_config.py                 | load-config-action         | ✅ Already exists                  |
| get_frontend_working_dir.py               | get-frontend-config-action | ✅ Already exists (outputs dir)    |
| package_release_assets.py                 | package-assets-action      | ✅ Already exists                  |
| generate_security_summary.py              | security-summary-action    | ✅ Already exists                  |
| build_go_release.py                       | release-go-action          | ✅ Part of release-go-action       |
| collect_rust_crate_metadata.py            | release-rust-action        | ✅ Part of release-rust-action     |
| configure_cargo_registry.py               | release-rust-action        | ✅ Part of release-rust-action     |
| detect_docker_config.py                   | release-docker-action      | ✅ Part of release-docker-action   |
| detect_frontend_package.py                | release-frontend-action    | ✅ Part of release-frontend-action |
| detect_python_package.py                  | release-python-action      | ✅ Part of release-python-action   |
| determine_docker_platforms.py             | release-docker-action      | ✅ Part of release-docker-action   |
| publish_to_github_packages.py             | release-docker-action      | ✅ Part of release-docker-action   |
| run_python_release_tests.py               | release-python-action      | ✅ Part of release-python-action   |
| validate_docker_compose.py                | release-docker-action      | ✅ Part of release-docker-action   |
| verify_python_protobuf_plugins.py         | release-python-action      | ✅ Part of release-python-action   |
| write_go_module_metadata.py               | release-go-action          | ✅ Part of release-go-action       |
| write_pypirc.py                           | release-python-action      | ✅ Part of release-python-action   |
| parse_protobuf_config.py                  | release-protobuf-action    | ✅ Part of release-protobuf-action |
| check_protobuf_artifacts.py               | release-protobuf-action    | ✅ Part of release-protobuf-action |

## Need New Actions 🚧

| Script                                 | Proposed Action                    | Priority | Usage                              |
| -------------------------------------- | ---------------------------------- | -------- | ---------------------------------- |
| ci_workflow.py                         | ci-workflow-helpers-action         | HIGH     | Used by reusable-ci.yml            |
| intelligent_labeling.py                | pr-auto-label-action               | MEDIUM   | Used by pr-automation.yml          |
| automation_workflow.py                 | workflow-analytics-action          | LOW      | Used by workflow-analytics.yml     |
| generate_workflow_analytics_summary.py | workflow-analytics-action          | LOW      | Same as above                      |
| docs_workflow.py                       | docs-generator-action              | MEDIUM   | Used by documentation.yml          |
| capture_benchmark_metrics.py           | benchmark-metrics-action           | LOW      | Used by performance-monitoring.yml |
| maintenance_workflow.py                | maintenance-tasks-action           | LOW      | Used by maintenance.yml            |
| sync_receiver.py                       | sync-receiver-action               | MEDIUM   | Used by sync-receiver.yml          |
| release_workflow.py                    | Merge into release-\*-action       | HIGH     | Shared release logic               |
| generate_release_summary.py            | Merge into release-strategy-action | MEDIUM   | Part of release flow               |
| generate-changelog.sh                  | Merge into release-strategy-action | MEDIUM   | Part of release flow               |
| download_nltk_data.py                  | nlp-setup-action                   | LOW      | Specific to NLP projects           |
| workflow_common.py                     | Embed in actions                   | N/A      | Library code                       |
| test-scripts.sh                        | N/A                                | N/A      | Internal testing only              |

## Recommendations

### High Priority (Convert Now)

1. **ci_workflow.py** → Create `ci-workflow-helpers-action`
   - Heavy usage in reusable-ci.yml
   - Multiple commands (go-setup, go-test, python-install, etc.)
   - Should be split into focused actions or kept as composite

2. **release_workflow.py + generate_release_summary.py + generate-changelog.sh**
   - Merge into `release-strategy-action` or create `release-utils-action`
   - Common logic shared across all release actions

### Medium Priority (Convert Soon)

3. **intelligent_labeling.py** → Create `pr-auto-label-action`
4. **docs_workflow.py** → Create `docs-generator-action`
5. **sync_receiver.py** → Create `sync-receiver-action`

### Low Priority (Convert Later)

6. **automation_workflow.py + generate_workflow_analytics_summary.py** →
   `workflow-analytics-action`
7. **capture_benchmark_metrics.py** → `benchmark-metrics-action`
8. **maintenance_workflow.py** → `maintenance-tasks-action`
9. **download_nltk_data.py** → `nlp-setup-action` (or keep as script if rarely
   used)

### Skip

- **workflow_common.py**: Library code, embed in actions
- **test-scripts.sh**: Internal testing only
