from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .warehouse import required_files


SOURCE_URL = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
SOURCE_LICENSE = "CC-BY-NC-SA-4.0"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_snapshot_manifest(data_dir: Path) -> dict[str, object]:
    files = required_files(data_dir)
    entries = [
        {
            "logical_table": logical_table,
            "filename": path.name,
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for logical_table, path in files.items()
    ]
    return {
        "schema_version": 1,
        "dataset": "Olist Brazilian E-Commerce Public Dataset",
        "source_url": SOURCE_URL,
        "license": SOURCE_LICENSE,
        "files": entries,
    }


def write_snapshot_manifest(manifest: dict[str, object], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return output
