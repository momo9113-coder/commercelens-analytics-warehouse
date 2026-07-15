from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import duckdb


@dataclass(frozen=True)
class QualityResult:
    name: str
    passed: bool
    failures: int
    detail: str


CHECKS: tuple[tuple[str, str, str], ...] = (
    (
        "duplicate_order_ids",
        "SELECT COUNT(*) FROM (SELECT order_id FROM stg_orders GROUP BY order_id HAVING COUNT(*) > 1)",
        "stg_orders.order_id must be unique",
    ),
    (
        "orphan_order_items",
        "SELECT COUNT(*) FROM stg_order_items i LEFT JOIN stg_orders o USING (order_id) WHERE o.order_id IS NULL",
        "every order item must reference an order",
    ),
    (
        "orphan_reviews",
        "SELECT COUNT(*) FROM stg_reviews r LEFT JOIN stg_orders o USING (order_id) WHERE o.order_id IS NULL",
        "every review must reference an order",
    ),
    (
        "negative_item_amounts",
        "SELECT COUNT(*) FROM stg_order_items WHERE price < 0 OR freight_value < 0",
        "price and freight value must be non-negative",
    ),
    (
        "invalid_order_status",
        "SELECT COUNT(*) FROM stg_orders WHERE order_status NOT IN ('delivered', 'shipped', 'canceled', 'invoiced', 'processing', 'unavailable', 'approved', 'created')",
        "order status must use the Olist status vocabulary",
    ),
    (
        "delivery_before_purchase",
        "SELECT COUNT(*) FROM stg_orders WHERE order_delivered_customer_date < order_purchase_timestamp",
        "delivery cannot precede purchase",
    ),
    (
        "duplicate_fct_orders",
        "SELECT COUNT(*) FROM (SELECT order_id FROM fct_orders GROUP BY order_id HAVING COUNT(*) > 1)",
        "fct_orders must have one row per order",
    ),
    (
        "invalid_review_score",
        "SELECT COUNT(*) FROM stg_reviews WHERE review_score IS NOT NULL AND (review_score < 1 OR review_score > 5)",
        "review scores must be between one and five",
    ),
    (
        "invalid_late_delivery_eligibility",
        """SELECT COUNT(*) FROM fct_orders
        WHERE (order_delivered_customer_date IS NOT NULL
               AND order_estimated_delivery_date IS NOT NULL
               AND late_delivery IS NULL)
           OR ((order_delivered_customer_date IS NULL
                OR order_estimated_delivery_date IS NULL)
               AND late_delivery IS NOT NULL)""",
        "late-delivery flags require both actual and estimated delivery timestamps",
    ),
)


def run_quality_checks(connection: duckdb.DuckDBPyConnection) -> list[QualityResult]:
    results: list[QualityResult] = []
    for name, query, detail in CHECKS:
        failures = int(connection.execute(query).fetchone()[0])
        results.append(QualityResult(name=name, passed=failures == 0, failures=failures, detail=detail))
    return results


def write_quality_report(results: list[QualityResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(result) for result in results], indent=2), encoding="utf-8")


def assert_quality(results: list[QualityResult]) -> None:
    failures = [result for result in results if not result.passed]
    if failures:
        summary = "; ".join(f"{result.name}={result.failures}" for result in failures)
        raise ValueError(f"Data quality checks failed: {summary}")
