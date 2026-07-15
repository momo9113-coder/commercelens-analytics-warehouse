# Deployment And Operations

Last verified: 2026-07-15.

## Public Services

- GitHub repository: `https://github.com/momo9113-coder/commercelens-analytics-warehouse`
- GitHub Pages report: `https://momo9113-coder.github.io/commercelens-analytics-warehouse/`
- Test workflow: `.github/workflows/test.yml`
- Pages workflow: `.github/workflows/pages.yml`

## Authentication Model

The repository contains no cloud key.

- GitHub pushes use the developer's Git credential helper or GitHub CLI outside the repository.
- GitHub Actions receives a short-lived built-in `GITHUB_TOKEN`; no repository secret was added for Pages.
- The Pages workflow requests only `contents: read`, `pages: write`, and `id-token: write`.
- Never add a personal access token, GitHub CLI token, browser cookie, Kaggle token, or credential-manager output to the repository.

## Publication Model

The public report is generated locally from the complete ignored Olist snapshot. Only the aggregate files in `site/` are committed. GitHub Actions publishes that committed directory unchanged.

The CI fixture has a different purpose: it proves the pipeline executes without network access. It must never replace the full-data public report.

Safe full-report update sequence:

```powershell
.\.venv\Scripts\python.exe -m commercelens.cli quality --data-dir data/raw --db-path reports/commercelens.duckdb --output reports/quality.json
.\.venv\Scripts\python.exe -m commercelens.cli report --data-dir data/raw --db-path reports/commercelens.duckdb --output-dir site
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
git diff -- site
```

Review the metric definitions, attribution, date coverage, charts, and table before committing `site/`.

## GitHub Pages

Pages is configured with build type `workflow`. The `publish-report` workflow uploads `site/` and deploys it with GitHub's official Pages Actions. GitHub Pages has no hibernation and no fixed free-trial expiry for this public repository. Current usage is far below the documented site-size and bandwidth limits.

## Verification

After each publication change:

1. Confirm both `tests` and `publish-report` succeeded in GitHub Actions.
2. Open the Pages URL in a signed-out/private browser.
3. Confirm the report states the Olist source, license, date coverage, and non-causal limitation.
4. Confirm `monthly_reliability.png` and `review_by_delivery.png` load.
5. Confirm the public numbers match the locally reviewed full-snapshot output.

## Recovery

- If tests fail, do not publish a new report.
- If `configure-pages` fails on a new repository, enable Pages with build type `workflow` using an authenticated administrator or GitHub settings.
- If deployment fails after a valid build, inspect the Pages job and repository Pages settings.
- If the public report is wrong, revert the responsible commit and regenerate from the verified snapshot; never patch numbers manually in `site/index.html`.
- If a credential is exposed, revoke/rotate it immediately and remove it from Git history; deleting only the latest file is insufficient.
