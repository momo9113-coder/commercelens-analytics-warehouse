from pathlib import Path

from commercelens.report import generate_report
from commercelens.warehouse import build_warehouse


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"


def test_report_contains_metrics_and_charts(tmp_path: Path) -> None:
    db_path = tmp_path / "fixture.duckdb"
    output_dir = tmp_path / "site"
    build_warehouse(FIXTURE_DIR, db_path)
    index = generate_report(db_path, output_dir)
    html = index.read_text(encoding="utf-8")
    assert "CommerceLens Analytics Report" in html
    assert "Operational findings" in html
    assert "Orders eligible for late-delivery rate" in html
    assert (output_dir / "monthly_reliability.png").exists()
    assert (output_dir / "review_by_delivery.png").exists()
    assert (output_dir / "state_reliability.png").exists()
