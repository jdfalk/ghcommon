<!-- file: scripts/template_repo/README.md -->
<!-- version: 1.1.0 -->
<!-- guid: 9a1b8d2e-4c57-4c3e-bb5f-7a3e12e6b4a1 -->
<!-- last-edited: 2026-01-19 -->

# Template Repository Scripts

These scripts scaffold a minimal, public-safe template repository folder on your local machine with
common GitHub configuration, workflows, issue/PR templates, linters, and docs. They include a
validation step to ensure no secrets are present. No passwords or tokens are embedded in any
generated files.

Important: These scripts operate on a target directory you specify. They do not modify the current
repository’s Git configuration, do not create submodules, and do not add nested repos. Any optional
GitHub operations happen only inside the target folder you point to.

## Scripts

- `scaffold_template_repo.py` — Generate the template repository structure and files
- `validate_template_repo.py` — Scan the generated repo for potential secrets
- `push_with_gh.py` — Optional: initialize git and create/push a repo using GitHub CLI (`gh`)

## Quick start

1. Scaffold the repo structure (dry run prints file list only):

```bash
python3 scripts/template_repo/scaffold_template_repo.py \
  --target ./template-repo-minimal \
  --name template-repo-minimal \
  --owner jdfalk \
  --description "Minimal public template repository" \
  --license MIT \
  --dry-run
```

1. Generate files:

```bash
python3 scripts/template_repo/scaffold_template_repo.py \
  --target ./template-repo-minimal \
  --name template-repo-minimal \
  --owner jdfalk \
  --description "Minimal public template repository" \
  --license MIT
```

1. Validate no secrets:

```bash
python3 scripts/template_repo/validate_template_repo.py ./template-repo-minimal
```

1. (Optional) Initialize a GitHub repo and push with GitHub CLI (no tokens in files):

```bash
python3 scripts/template_repo/push_with_gh.py \
  --target ./template-repo-minimal \
  --owner jdfalk \
  --repo template-repo-minimal \
  --private
```

## Notes

- All generated content is public-safe by default and contains no passwords or secrets.
- You can customize files after generation; re-run the validator before publishing. -- If you prefer
  a different license, pass `--license Apache-2.0` when scaffolding.
