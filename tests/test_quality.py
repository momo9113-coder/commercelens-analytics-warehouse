from pathlib import Path

from commercelens.quality import run_quality_checks
from commercelens.warehouse import build_warehouse, connect


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"


def test_fixture_warehouse_passes_quality_checks(tmp_path: Path) -> None:
    db_path = tmp_path / "fixture.duckdb"
    build_warehouse(FIXTURE_DIR, db_path)
    connection = connect(db_path, read_only=True)
    try:
        results = run_quality_checks(connection)
    finally:
        connection.close()
    assert len(results) == 8
    assert all(result.passed for result in results), results
