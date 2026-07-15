from __future__ import annotations

from pathlib import Path

import duckdb


DATASET_FILES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
}
SQL_DIR = Path(__file__).resolve().parents[2] / "sql"


def required_files(data_dir: Path) -> dict[str, Path]:
    data_dir = Path(data_dir)
    files = {name: data_dir / filename for name, filename in DATASET_FILES.items()}
    missing = [str(path) for path in files.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required dataset files: " + ", ".join(missing))
    return files


def _quoted_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def _load_raw_tables(connection: duckdb.DuckDBPyConnection, data_dir: Path) -> None:
    for table_name, path in required_files(data_dir).items():
        connection.execute(
            f"CREATE OR REPLACE TABLE raw_{table_name} AS "
            f"SELECT * FROM read_csv_auto('{_quoted_path(path)}', header=true, null_padding=true, parallel=false)"
        )


def _execute_sql_file(connection: duckdb.DuckDBPyConnection, path: Path) -> None:
    connection.execute(path.read_text(encoding="utf-8"))


def connect(db_path: Path | str = ":memory:", read_only: bool = False) -> duckdb.DuckDBPyConnection:
    if str(db_path) != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path), read_only=read_only)


def build_warehouse(
    data_dir: Path,
    db_path: Path | str = ":memory:",
    sql_dir: Path = SQL_DIR,
) -> Path | str:
    connection = connect(db_path)
    try:
        _load_raw_tables(connection, Path(data_dir))
        _execute_sql_file(connection, sql_dir / "staging" / "staging.sql")
        _execute_sql_file(connection, sql_dir / "marts" / "marts.sql")
    finally:
        connection.close()
    return db_path
