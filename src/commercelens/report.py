from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .warehouse import connect


def _format_metric(name: str, value: object) -> str:
    if pd.isna(value):
        return "not available"
    if name == "orders":
        return f"{int(value):,}"
    if name == "gross_item_freight_value":
        return f"{float(value):,.2f}"
    if name == "late_delivery_rate":
        return f"{float(value):.1%}"
    if isinstance(value, (float, int)):
        return f"{float(value):.3f}"
    return str(value)


def _save_monthly_chart(frame: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(9, 4.5))
    if not frame.empty:
        labels = pd.to_datetime(frame["month"]).dt.strftime("%Y-%m")
        rates = frame["late_delivery_rate"].astype(float)
        axis.plot(labels, rates, marker="o", color="#0f766e", linewidth=2)
        axis.set_ylim(0, min(1.0, max(0.1, float(rates.max()) * 1.25)))
        axis.set_ylabel("Late-delivery rate")
        axis.tick_params(axis="x", rotation=45)
        axis.grid(axis="y", alpha=0.25)
    axis.set_title("Monthly late-delivery rate")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def _save_review_chart(frame: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(6, 4.5))
    if not frame.empty:
        labels = ["On time", "Late"]
        values = [
            float(frame.loc[frame["late_delivery"] == 0, "average_review_score"].iloc[0]) if (frame["late_delivery"] == 0).any() else 0.0,
            float(frame.loc[frame["late_delivery"] == 1, "average_review_score"].iloc[0]) if (frame["late_delivery"] == 1).any() else 0.0,
        ]
        axis.bar(labels, values, color=["#2563eb", "#dc2626"])
        axis.set_ylim(0, 5)
        axis.set_ylabel("Average review score")
    axis.set_title("Reviews by delivery status")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def generate_report(db_path: Path | str, output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    connection = connect(db_path, read_only=True)
    try:
        metrics = connection.execute(
            """
            SELECT
                COUNT(*) AS orders,
                COALESCE(SUM(order_value), 0) AS gross_item_freight_value,
                COALESCE(AVG(late_delivery), 0) AS late_delivery_rate,
                AVG(avg_review_score) AS average_review_score,
                AVG(delivery_days) AS average_delivery_days,
                MIN(order_purchase_timestamp) AS purchase_start,
                MAX(order_purchase_timestamp) AS purchase_end
            FROM fct_orders
            """
        ).fetchdf()
        monthly = connection.execute(
            """
            SELECT DATE_TRUNC('month', order_purchase_timestamp) AS month,
                   COUNT(*) AS orders,
                   SUM(order_value) AS gross_item_freight_value,
                   AVG(late_delivery) AS late_delivery_rate
            FROM fct_orders
            WHERE order_purchase_timestamp IS NOT NULL
            GROUP BY 1 ORDER BY 1
            """
        ).fetchdf()
        review_breakdown = connection.execute(
            """
            SELECT late_delivery, AVG(avg_review_score) AS average_review_score
            FROM fct_orders
            WHERE avg_review_score IS NOT NULL
            GROUP BY 1 ORDER BY 1
            """
        ).fetchdf()
        sellers = connection.execute(
            """
            SELECT seller_id, order_count, allocated_gross_item_freight_value, late_delivery_rate, average_review_score
            FROM fct_seller_performance
            ORDER BY order_count DESC, seller_id
            LIMIT 10
            """
        ).fetchdf()
    finally:
        connection.close()

    monthly_path = output_dir / "monthly_reliability.png"
    review_path = output_dir / "review_by_delivery.png"
    _save_monthly_chart(monthly, monthly_path)
    _save_review_chart(review_breakdown, review_path)
    values = metrics.iloc[0].to_dict()
    purchase_start = values.pop("purchase_start")
    purchase_end = values.pop("purchase_end")
    coverage = f"{purchase_start:%Y-%m-%d} to {purchase_end:%Y-%m-%d}" if pd.notna(purchase_start) and pd.notna(purchase_end) else "not available"
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    metric_rows = "".join(
        f"<tr><th>{escape(str(key).replace('_', ' ').title())}</th><td>{escape(_format_metric(key, value))}</td></tr>"
        for key, value in values.items()
    )
    seller_display = sellers.rename(columns={
        "seller_id": "Seller ID",
        "order_count": "Order count",
        "allocated_gross_item_freight_value": "Allocated item + freight value",
        "late_delivery_rate": "Late-delivery rate",
        "average_review_score": "Average review score",
    })
    seller_display["Order count"] = seller_display["Order count"].map(lambda value: f"{int(value):,}")
    seller_display["Allocated item + freight value"] = seller_display["Allocated item + freight value"].map(lambda value: f"{value:,.2f}")
    seller_display["Late-delivery rate"] = seller_display["Late-delivery rate"].map(lambda value: f"{value:.1%}")
    seller_display["Average review score"] = seller_display["Average review score"].map(lambda value: f"{value:.3f}" if pd.notna(value) else "not available")
    seller_html = f'<div class="table-wrap">{seller_display.to_html(index=False, classes="data", border=0)}</div>'
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CommerceLens Analytics Report</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#17202a}}h1{{margin-bottom:.2rem}}.muted{{color:#5f6b76}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem}}img{{width:100%;height:auto;border:1px solid #d8dee4}}table{{border-collapse:collapse;width:100%;margin:1rem 0}}th,td{{border-bottom:1px solid #d8dee4;padding:.45rem;text-align:left}}th{{background:#f6f8fa}}.data{{font-size:.9rem}}.table-wrap{{overflow-x:auto}}</style></head>
<body><h1>CommerceLens Analytics Report</h1><p class="muted">Source: <a href="https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce">Olist Brazilian E-Commerce Public Dataset</a> (Kaggle, CC-BY-NC-SA-4.0). Purchase coverage: {coverage}. Generated: {generated_at}.</p><p class="muted">These are descriptive associations, not causal claims.</p>
<h2>Key metrics</h2><table>{metric_rows}</table>
<div class="grid"><figure><img src="monthly_reliability.png" alt="Monthly delivery reliability"><figcaption>Monthly late-delivery rate.</figcaption></figure>
<figure><img src="review_by_delivery.png" alt="Review score by delivery status"><figcaption>Average review score by delivery status.</figcaption></figure></div>
<h2>Largest sellers by order count</h2>{seller_html}
<h2>Reproduce</h2><p><code>python -m commercelens.cli report --data-dir data/fixtures --db-path reports/fixture.duckdb --output-dir site</code></p>
</body></html>"""
    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path
