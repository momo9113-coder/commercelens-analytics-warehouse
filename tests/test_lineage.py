from pathlib import Path

from commercelens.lineage import build_snapshot_manifest, write_snapshot_manifest


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"


def test_snapshot_manifest_contains_hashes_without_local_paths(tmp_path: Path) -> None:
    manifest = build_snapshot_manifest(FIXTURE_DIR)
    assert len(manifest["files"]) == 7
    assert all(len(entry["sha256"]) == 64 for entry in manifest["files"])
    output = write_snapshot_manifest(manifest, tmp_path / "snapshot.json")
    content = output.read_text(encoding="utf-8")
    assert str(FIXTURE_DIR) not in content
