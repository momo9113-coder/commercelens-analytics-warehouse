# CommerceLens Project Handoff

Last updated: 2026-07-15.

## Scope

This repository is the data/analytics-engineering project in a three-repository MSc application portfolio. Keep it focused on reproducible ingestion, SQL modeling, data-quality evidence, analytical communication, and static publication. Do not add an unnecessary live database or turn it into a generic dashboard monorepo.

## Read First

1. `README.md`
2. `AGENTS.md`
3. `docs/DEPLOYMENT.md`
4. `data/README.md`
5. `src/commercelens/warehouse.py`
6. `src/commercelens/quality.py`
7. `src/commercelens/report.py`
8. `sql/staging/staging.sql`
9. `sql/marts/marts.sql`
10. `sql/analysis/analysis.sql`
11. `tests/`

## Current State

- GitHub: `https://github.com/momo9113-coder/commercelens-analytics-warehouse`
- Live report: `https://momo9113-coder.github.io/commercelens-analytics-warehouse/`
- Default branch: `main`
- Dataset: public Olist Brazilian E-Commerce snapshot, licensed `CC-BY-NC-SA-4.0` on Kaggle.
- First full build: 99,441 order facts after all 8 data-quality checks passed.
- Dated descriptive results: gross item-plus-freight value 15,843,553.24; late-delivery rate 7.9%; average review score 4.087.
- Local fixture tests: 2 passing as of 2026-07-15.
- GitHub Actions `tests` and `publish-report`: passing on the current public `main` branch.

The published values are descriptive snapshot results, not causal or financial-performance claims.

## Architecture

```text
Olist CSV snapshot -> raw_* -> stg_* -> fct_orders / seller mart
                                      |-> 8 quality checks
                                      `-> HTML + PNG static report -> GitHub Pages
```

- `warehouse.py` validates required files, loads DuckDB raw tables, and runs staging/mart SQL.
- CSV parsing uses `parallel=false` because the full Olist reviews file contains quoted newlines that conflict with parallel scanning and `null_padding=true`.
- `quality.py` runs the executable checks and blocks publication on failure.
- `report.py` generates the committed aggregate site in `site/`.
- Fixture CSVs support network-free CI; they are not valid analytical evidence.

## Local Workflow

Run commands from the repository root.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m commercelens.cli report --data-dir data/fixtures --db-path reports/fixture.duckdb --output-dir site
.\.venv\Scripts\python.exe -m commercelens.cli quality --data-dir data/raw --db-path reports/commercelens.duckdb --output reports/quality.json
.\.venv\Scripts\python.exe -m commercelens.cli report --data-dir data/raw --db-path reports/commercelens.duckdb --output-dir site
```

If `.venv` does not exist, create it and install `.[dev,data]`. Python 3.12 is used in CI; the existing Windows development environment was created with Python 3.14.3.

## Data And Secrets

- Kaggle authentication is external to this repository. `scripts/download_olist.py` invokes the configured CLI but never reads or copies credential files.
- `data/raw/`, `reports/*.duckdb`, generated local quality files, `.venv/`, and caches are ignored.
- `site/` contains only aggregate HTML/PNG publication artifacts and is intentionally committed.
- Never commit Kaggle tokens, raw Olist CSVs/archives, browser cookies, GitHub credentials, or a local DuckDB file.
- Retain source attribution and the `CC-BY-NC-SA-4.0` notice in public documentation and reports.

## Guardrails

- Never publish fixture metrics as full-data results.
- Run all quality checks before regenerating or committing `site/` from the full snapshot.
- Do not describe correlations between delivery and reviews as causal effects.
- Keep metric names literal. `gross item-plus-freight value` is not labeled as realized revenue or GMV.
- GitHub Pages should deploy committed static assets; CI must not overwrite the full report with fixture output.

## Next Priorities

1. Add a concise written analysis of region and seller patterns, with SQL links and limitations.
2. Add data lineage/checksum metadata for the full local snapshot without publishing raw files.
3. Pin or lock dependencies and confirm fixture CI on the locked environment.
4. Add a report screenshot to the README and tighten mobile table presentation if needed.
5. Tag an application-ready release after conclusions and reproducibility evidence are stable.
