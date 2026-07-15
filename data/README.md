# Data acquisition

`data/raw/` is intentionally ignored by Git. To obtain the public Olist snapshot:

```powershell
python -m pip install -r requirements-data.txt
python scripts/download_olist.py --data-dir data/raw
```

The script invokes `python -m kaggle datasets download -d olistbr/brazilian-ecommerce --unzip` and expects Kaggle credentials to be configured outside the repository. It does not read, print, or copy credential files. Kaggle lists the dataset under `CC-BY-NC-SA-4.0`; raw data remains outside Git and the generated report attributes the source.

After download, build the warehouse and static site:

```powershell
python -m commercelens.cli snapshot --data-dir data/raw --output data/snapshot_manifest.json
python -m commercelens.cli report --data-dir data/raw --db-path reports/commercelens.duckdb --output-dir site
```

Only the generated aggregate report and charts in `site/` are intended for publication. Do not commit raw CSV files, the downloaded archive, or the DuckDB database.

The committed manifest contains only file metadata and SHA-256 values. It allows a future run to confirm that the exact input snapshot is being analyzed without redistributing the licensed data.
