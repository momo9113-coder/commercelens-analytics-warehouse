# Dated Operations Analysis

Analysis date: 2026-07-15.

## Scope And Denominators

The warehouse contains 99,441 order facts from the dated Olist snapshot. Late-delivery analysis uses the 96,476 orders that have both actual and estimated delivery timestamps. Orders without either timestamp have a `NULL` late-delivery flag and are excluded from that rate rather than treated as on time.

All nine executable data-quality checks passed before this analysis was generated. The exact seven input files, byte sizes, and SHA-256 hashes are versioned in [`data/snapshot_manifest.json`](../data/snapshot_manifest.json). Raw CSVs and the DuckDB file remain outside Git.

## Findings

### Delivery And Reviews

Among 95,830 eligible orders with a review:

| Delivery status | Reviewed orders | Average review | 1-2 star rate | Average delivery days |
|---|---:|---:|---:|---:|
| On time | 88,168 | 4.294 | 9.2% | 10.82 |
| Late | 7,662 | 2.567 | 54.0% | 31.34 |

Late orders had an average review score 1.728 points lower, while their 1-2 star rate was 44.8 percentage points higher. This is a descriptive association. The snapshot does not establish that lateness alone caused the review difference.

### Monthly Reliability

Among months with at least 1,000 eligible orders, March 2018 had the highest late-delivery rate: 21.36% across 7,003 orders. February 2018 was next at 16.00% across 6,556 orders. The result identifies a period for investigation; it does not identify a root cause.

### Geographic Variation

Among states with at least 1,000 eligible orders, the observed late-delivery rate ranged from 5.00% in PR to 15.32% in CE, a 10.33 percentage-point spread. BA (14.04%) and RJ (13.47%) were also above the snapshot-wide 8.11% rate. Geography may proxy for distance, carrier mix, seller mix, infrastructure, or unobserved factors, so no state effect is claimed.

### Seller Dispersion

There were 210 sellers with at least 100 eligible orders. Their median late-delivery rate was 6.75%, the 90th percentile was 12.76%, and the maximum was 23.14%. The seller-level correlation between late-delivery rate and average review was -0.466. This aggregated correlation is useful for prioritization, not causal attribution or individual performance judgment.

## Metric Definitions

- `orders`: one row per Olist order in `fct_orders`.
- `gross item + freight value`: sum of item price plus freight from the snapshot; it is not labeled as realized revenue or GMV.
- `late-delivery rate`: average of the 0/1 late flag only where actual and estimated delivery timestamps both exist.
- `low review`: an average order review score of 1 or 2.
- State minimum: 1,000 eligible orders.
- Seller minimum: 100 eligible orders.

The executable definitions are in [`sql/analysis/analysis.sql`](../sql/analysis/analysis.sql) and the report query layer is in [`src/commercelens/analysis.py`](../src/commercelens/analysis.py).

## Reproduce

```powershell
python -m commercelens.cli snapshot --data-dir data/raw --output data/snapshot_manifest.json
python -m commercelens.cli quality --data-dir data/raw --db-path reports/commercelens.duckdb --output reports/quality.json
python -m commercelens.cli report --data-dir data/raw --db-path reports/commercelens.duckdb --output-dir site
python -m pytest
```

## Limitations

The dataset is observational, historical, and non-commercially licensed. Missing timestamps and reviews are not random by assumption. State and seller comparisons are not adjusted for product mix, distance, carrier, seasonality, or customer characteristics. The October 2018 endpoint is partial, and low-volume edge months are excluded from highlighted monthly conclusions. Results should not be generalized beyond this snapshot without renewed validation.
