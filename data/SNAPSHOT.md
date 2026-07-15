# Snapshot fingerprint

`snapshot_manifest.json` records the source URL, source license, logical input table, filename, byte size, and SHA-256 for each of the seven CSV files consumed by the warehouse.

Generate it with:

```powershell
python -m commercelens.cli snapshot --data-dir data/raw --output data/snapshot_manifest.json
```

The manifest contains no credentials, raw rows, absolute local paths, or personal information. The downloaded geolocation and category-translation files are not included because the current warehouse does not consume them.
