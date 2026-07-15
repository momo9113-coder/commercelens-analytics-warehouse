from __future__ import annotations

import argparse
from pathlib import Path

from .quality import assert_quality, run_quality_checks, write_quality_report
from .report import generate_report
from .warehouse import build_warehouse, connect


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and inspect the CommerceLens DuckDB warehouse.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "quality", "report"):
        command = subparsers.add_parser(name)
        command.add_argument("--data-dir", type=Path, required=True)
        command.add_argument("--db-path", type=Path, default=Path("reports/commercelens.duckdb"))
    subparsers.choices["quality"].add_argument("--output", type=Path, default=Path("reports/quality.json"))
    subparsers.choices["report"].add_argument("--output-dir", type=Path, default=Path("site"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "build":
        build_warehouse(args.data_dir, args.db_path)
        print(args.db_path)
        return
    if args.command == "quality":
        build_warehouse(args.data_dir, args.db_path)
        connection = connect(args.db_path, read_only=True)
        try:
            results = run_quality_checks(connection)
        finally:
            connection.close()
        write_quality_report(results, args.output)
        for result in results:
            print(f"{result.name}: {'PASS' if result.passed else 'FAIL'} ({result.failures})")
        assert_quality(results)
        return
    build_warehouse(args.data_dir, args.db_path)
    connection = connect(args.db_path, read_only=True)
    try:
        results = run_quality_checks(connection)
    finally:
        connection.close()
    assert_quality(results)
    output = generate_report(args.db_path, args.output_dir)
    print(output)


if __name__ == "__main__":
    main()
