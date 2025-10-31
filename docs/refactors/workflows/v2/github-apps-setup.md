<!-- file: docs/refactors/workflows/v2/github-apps-setup.md -->
<!-- version: 1.0.0 -->
<!-- guid: d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a -->

# GitHub Apps Setup Guide

## Overview

Phase 5 workflows use a GitHub App for elevated API rate limits, granular permissions, and
installation-scoped automation. This guide documents how to provision the app, store credentials,
and operate it securely alongside `automation_workflow.py`.

## Create the GitHub App

1. Navigate to **Organization Settings → Developer Settings → GitHub Apps → New GitHub App**.
2. Supply base metadata:
   - **Name**: `Workflow Automation v2`
   - **Homepage URL**: `https://github.com/<org>/ghcommon`
   - **Webhook**: leave disabled (workflows poll APIs directly)
3. Configure repository permissions:
   - Actions: **Read & write**
   - Contents: **Read & write**
   - Issues: **Read & write**
   - Pull requests: **Read & write**
   - Metadata: **Read**
4. Configure organization permissions (if available):
   - Administration: **Read**
   - Members: **Read**
5. Choose **Only on this account** for installation restrictions and create the app.

## Generate a Private Key

1. In the app overview, scroll to **Private keys**.
2. Click **Generate a private key** and store the downloaded `.pem` file in a secure location.
3. Record the **App ID** displayed near the top of the settings page.

## Install the App

1. Click **Install App** in the left navigation.
2. Select the organization account.
3. Choose **All repositories** (recommended) or a curated subset required by automation.
4. Confirm installation and capture the installation ID from the resulting URL:
   `https://github.com/organizations/<org>/settings/installations/<installation_id>`.

## Store Secrets

Add the following secrets to the repository or org-level secret store:

```bash
# App identifier (integer value)
gh secret set GITHUB_APP_ID --body "123456"

# Installation identifier (integer value)
gh secret set GITHUB_APP_INSTALLATION_ID --body "789012"

# PEM private key (multi-line)
gh secret set GITHUB_APP_PRIVATE_KEY < path/to/private-key.pem
```

When using repository environments, scope the secrets to workflows that require the credentials.

## Using the App in Workflows

`automation_workflow.py` exposes a `github-app-token` command that emits a JWT or can exchange it
for an installation token.

Example workflow step:

```yaml
- name: Generate installation token
  id: gha-token
  run: |
    python .github/workflows/scripts/automation_workflow.py github-app-token \
      --app-id "${{ secrets.GITHUB_APP_ID }}" \
      --private-key-file private-key.pem \
      --expires-in 540 > app.jwt
    python - <<'PY' app_jwt="$(cat app.jwt)" \
      install_id="${{ secrets.GITHUB_APP_INSTALLATION_ID }}"
    from automation_workflow import get_installation_access_token
    import json, os
    token = get_installation_access_token(
        app_id=os.environ['GITHUB_APP_ID'],
        private_key=open('private-key.pem').read(),
        installation_id=os.environ['GITHUB_APP_INSTALLATION_ID'],
    )
    Path('token.json').write_text(json.dumps(token, indent=2))
    PY
```

In streamlined workflows, bundle the private key via a temporary file using `printf` with masked
secrets.

## Security Considerations

- Treat the private key as a highly sensitive secret; rotate it when members change.
- Use short `expires-in` values (≤10 minutes) when generating JWTs.
- Avoid logging tokens. Mask outputs or write them to temporary files removed at the end of the job.
- Restrict app installation to repositories that require automation.
- Monitor audit logs for token generation failures or unusual activity.

## Troubleshooting

| Symptom                                  | Probable Cause                                   | Resolution                                                              |
| ---------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------- |
| `Failed to obtain installation token`    | Incorrect installation ID or missing permissions | Verify installation ID and ensure the app has Actions/Contents access.  |
| `Signature has expired`                  | JWT lifetime too long or system clock drift      | Use `expires-in` between 60-600 seconds and confirm UTC time on runner. |
| `Resource not accessible by integration` | App lacks required permission                    | Update app permissions and reinstall to refresh grants.                 |
| `Bad credentials` during REST calls      | Token expired mid-run                            | Regenerate token inside long-running jobs before performing API calls.  |

## Maintenance

- Review app installations monthly and remove unused repositories.
- Rotate the private key at least twice a year or upon incident response.
- Capture metrics from `automation_workflow.collect_workflow_metrics` to audit API error rates tied
  to the app.

## References

- [GitHub Apps documentation](https://docs.github.com/en/apps)
- [REST API authentication](https://docs.github.com/en/rest/overview/authenticating-to-the-rest-api)
- `.github/workflows/scripts/automation_workflow.py`
