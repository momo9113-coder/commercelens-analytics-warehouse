from __future__ import annotations

from dataclasses import dataclass

import duckdb
import pandas as pd


@dataclass(frozen=True)
class AnalysisFrames:
    metrics: pd.DataFrame
    monthly: pd.DataFrame
    delivery_review: pd.DataFrame
    states: pd.DataFrame
    seller_summary: pd.DataFrame
    seller_watchlist: pd.DataFrame


SELLER_MIN_ORDERS = 100
STATE_MIN_ORDERS = 1000
MONTH_MIN_ORDERS = 1000


def collect_analysis(connection: duckdb.DuckDBPyConnection) -> AnalysisFrames:
    metrics = connection.execute(
        """
        SELECT
            COUNT(*) AS orders,
            COUNT(*) FILTER (WHERE late_delivery IS NOT NULL) AS late_delivery_eligible_orders,
            COALESCE(SUM(order_value), 0) AS gross_item_freight_value,
            AVG(late_delivery) AS late_delivery_rate,
            AVG(avg_review_score) AS average_review_score,
            AVG(delivery_days) AS average_delivery_days,
            MIN(order_purchase_timestamp) AS purchase_start,
            MAX(order_purchase_timestamp) AS purchase_end
        FROM fct_orders
        """
    ).fetchdf()
    monthly = connection.execute(
        """
        SELECT
            DATE_TRUNC('month', order_purchase_timestamp) AS month,
            COUNT(*) AS eligible_orders,
            AVG(late_delivery) AS late_delivery_rate,
            AVG(avg_review_score) AS average_review_score
        FROM fct_orders
        WHERE late_delivery IS NOT NULL
          AND order_purchase_timestamp IS NOT NULL
        GROUP BY 1
        ORDER BY 1
        """
    ).fetchdf()
    delivery_review = connection.execute(
        """
        SELECT
            late_delivery,
            COUNT(*) AS reviewed_orders,
            AVG(avg_review_score) AS average_review_score,
            AVG(CASE WHEN avg_review_score <= 2 THEN 1.0 ELSE 0.0 END) AS low_review_rate,
            AVG(delivery_days) AS average_delivery_days,
            AVG(order_value) AS average_order_value
        FROM fct_orders
        WHERE late_delivery IS NOT NULL
          AND avg_review_score IS NOT NULL
        GROUP BY 1
        ORDER BY 1
        """
    ).fetchdf()
    states = connection.execute(
        """
        SELECT
            c.customer_state,
            COUNT(*) AS eligible_orders,
            AVG(f.late_delivery) AS late_delivery_rate,
            AVG(f.avg_review_score) AS average_review_score,
            AVG(f.delivery_days) AS average_delivery_days
        FROM fct_orders f
        JOIN stg_customers c USING (customer_id)
        WHERE f.late_delivery IS NOT NULL
        GROUP BY 1
        ORDER BY eligible_orders DESC, customer_state
        """
    ).fetchdf()
    seller_cte = f"""
        WITH order_sellers AS (
            SELECT DISTINCT order_id, seller_id
            FROM stg_order_items
        ), seller AS (
            SELECT
                os.seller_id,
                COUNT(*) AS eligible_orders,
                AVG(f.late_delivery) AS late_delivery_rate,
                AVG(f.avg_review_score) AS average_review_score
            FROM order_sellers os
            JOIN fct_orders f USING (order_id)
            WHERE f.late_delivery IS NOT NULL
            GROUP BY 1
            HAVING COUNT(*) >= {SELLER_MIN_ORDERS}
        )
    """
    seller_summary = connection.execute(
        seller_cte
        + """
        SELECT
            COUNT(*) AS eligible_sellers,
            MIN(late_delivery_rate) AS min_late_delivery_rate,
            MEDIAN(late_delivery_rate) AS median_late_delivery_rate,
            QUANTILE_CONT(late_delivery_rate, 0.9) AS p90_late_delivery_rate,
            MAX(late_delivery_rate) AS max_late_delivery_rate,
            CORR(late_delivery_rate, average_review_score) AS late_review_correlation
        FROM seller
        """
    ).fetchdf()
    seller_watchlist = connection.execute(
        seller_cte
        + """
        SELECT seller_id, eligible_orders, late_delivery_rate, average_review_score
        FROM seller
        ORDER BY late_delivery_rate DESC, eligible_orders DESC, seller_id
        LIMIT 5
        """
    ).fetchdf()
    return AnalysisFrames(
        metrics=metrics,
        monthly=monthly,
        delivery_review=delivery_review,
        states=states,
        seller_summary=seller_summary,
        seller_watchlist=seller_watchlist,
    )
