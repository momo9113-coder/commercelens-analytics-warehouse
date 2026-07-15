from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .analysis import MONTH_MIN_ORDERS, SELLER_MIN_ORDERS, STATE_MIN_ORDERS, collect_analysis
from .warehouse import connect


def _format_metric(name: str, value: object) -> str:
    if pd.isna(value):
        return "not available"
    if name in {"orders", "late_delivery_eligible_orders"}:
        return f"{int(value):,}"
    if name == "gross_item_freight_value":
        return f"{float(value):,.2f}"
    if name == "late_delivery_rate":
        return f"{float(value):.1%}"
    if isinstance(value, (float, int)):
        return f"{float(value):.3f}"
    return str(value)


def _save_monthly_chart(frame: pd.DataFrame, path: Path) -> None:
    frame = frame.loc[frame["eligible_orders"] >= MONTH_MIN_ORDERS].copy()
    figure, axis = plt.subplots(figsize=(9, 4.5))
    if not frame.empty:
        labels = pd.to_datetime(frame["month"]).dt.strftime("%Y-%m")
        rates = frame["late_delivery_rate"].astype(float)
        axis.plot(labels, rates, marker="o", color="#0f766e", linewidth=2)
        axis.set_ylim(0, min(1.0, max(0.1, float(rates.max()) * 1.25)))
        axis.set_ylabel("Late-delivery rate")
        axis.tick_params(axis="x", rotation=45)
        axis.grid(axis="y", alpha=0.25)
    axis.set_title(f"Monthly reliability (at least {MONTH_MIN_ORDERS:,} eligible orders)")
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def _save_review_chart(frame: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(6, 4.5))
    if not frame.empty:
        values = []
        for flag in (0, 1):
            match = frame.loc[frame["late_delivery"] == flag, "average_review_score"]
            values.append(float(match.iloc[0]) if not match.empty else 0.0)
        bars = axis.bar(["On time", "Late"], values, color=["#2563eb", "#dc2626"])
        axis.bar_label(bars, fmt="%.2f", padding=3)
        axis.set_ylim(0, 5)
        axis.set_ylabel("Average review score")
    axis.set_title("Reviews by delivery status")
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def _save_state_chart(frame: pd.DataFrame, path: Path) -> None:
    qualified = frame.loc[frame["eligible_orders"] >= STATE_MIN_ORDERS].copy()
    qualified = qualified.sort_values("late_delivery_rate").tail(12)
    figure, axis = plt.subplots(figsize=(7, 5))
    if not qualified.empty:
        bars = axis.barh(qualified["customer_state"], qualified["late_delivery_rate"], color="#7c3aed")
        axis.bar_label(bars, labels=[f"{value:.1%}" for value in qualified["late_delivery_rate"]], padding=3)
        axis.set_xlabel("Late-delivery rate")
        axis.set_xlim(0, max(0.18, float(qualified["late_delivery_rate"].max()) * 1.2))
        axis.grid(axis="x", alpha=0.2)
    axis.set_title(f"State reliability (at least {STATE_MIN_ORDERS:,} eligible orders)")
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def _row(frame: pd.DataFrame, column: str, value: object) -> dict[str, object]:
    match = frame.loc[frame[column] == value]
    return match.iloc[0].to_dict() if not match.empty else {}


def _number(row: dict[str, object], key: str) -> float:
    value = row.get(key, float("nan"))
    return float(value) if not pd.isna(value) else float("nan")


def generate_report(db_path: Path | str, output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    connection = connect(db_path, read_only=True)
    try:
        analysis = collect_analysis(connection)
    finally:
        connection.close()

    monthly_path = output_dir / "monthly_reliability.png"
    review_path = output_dir / "review_by_delivery.png"
    state_path = output_dir / "state_reliability.png"
    _save_monthly_chart(analysis.monthly, monthly_path)
    _save_review_chart(analysis.delivery_review, review_path)
    _save_state_chart(analysis.states, state_path)

    values = analysis.metrics.iloc[0].to_dict()
    purchase_start = values.pop("purchase_start")
    purchase_end = values.pop("purchase_end")
    coverage = f"{purchase_start:%Y-%m-%d} to {purchase_end:%Y-%m-%d}" if pd.notna(purchase_start) and pd.notna(purchase_end) else "not available"
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    labels = {
        "orders": "Orders in warehouse",
        "late_delivery_eligible_orders": "Orders eligible for late-delivery rate",
        "gross_item_freight_value": "Gross item + freight value",
        "late_delivery_rate": "Late-delivery rate (eligible orders)",
        "average_review_score": "Average review score",
        "average_delivery_days": "Average delivery days",
    }
    metric_rows = "".join(
        f"<tr><th>{escape(labels[key])}</th><td>{escape(_format_metric(key, value))}</td></tr>"
        for key, value in values.items()
    )

    on_time = _row(analysis.delivery_review, "late_delivery", 0)
    late = _row(analysis.delivery_review, "late_delivery", 1)
    review_gap = _number(on_time, "average_review_score") - _number(late, "average_review_score")
    low_review_gap = _number(late, "low_review_rate") - _number(on_time, "low_review_rate")
    stable_months = analysis.monthly.loc[analysis.monthly["eligible_orders"] >= MONTH_MIN_ORDERS]
    peak_month = stable_months.sort_values("late_delivery_rate", ascending=False).iloc[0] if not stable_months.empty else None

    qualified_states = analysis.states.loc[analysis.states["eligible_orders"] >= STATE_MIN_ORDERS].copy()
    highest_state = qualified_states.sort_values("late_delivery_rate", ascending=False).iloc[0] if not qualified_states.empty else None
    lowest_state = qualified_states.sort_values("late_delivery_rate").iloc[0] if not qualified_states.empty else None
    state_display = qualified_states.head(12).rename(columns={
        "customer_state": "State",
        "eligible_orders": "Eligible orders",
        "late_delivery_rate": "Late-delivery rate",
        "average_review_score": "Average review",
        "average_delivery_days": "Average delivery days",
    })
    if not state_display.empty:
        state_display["Eligible orders"] = state_display["Eligible orders"].map(lambda value: f"{int(value):,}")
        state_display["Late-delivery rate"] = state_display["Late-delivery rate"].map(lambda value: f"{value:.1%}")
        state_display["Average review"] = state_display["Average review"].map(lambda value: f"{value:.3f}")
        state_display["Average delivery days"] = state_display["Average delivery days"].map(lambda value: f"{value:.2f}")
    state_html = f'<div class="table-wrap">{state_display.to_html(index=False, classes="data", border=0)}</div>'

    seller_summary = analysis.seller_summary.iloc[0].to_dict()
    watchlist = analysis.seller_watchlist.rename(columns={
        "seller_id": "Seller ID",
        "eligible_orders": "Eligible orders",
        "late_delivery_rate": "Late-delivery rate",
        "average_review_score": "Average review",
    })
    if not watchlist.empty:
        watchlist["Seller ID"] = watchlist["Seller ID"].map(lambda value: f"{value[:8]}...")
        watchlist["Eligible orders"] = watchlist["Eligible orders"].map(lambda value: f"{int(value):,}")
        watchlist["Late-delivery rate"] = watchlist["Late-delivery rate"].map(lambda value: f"{value:.1%}")
        watchlist["Average review"] = watchlist["Average review"].map(lambda value: f"{value:.3f}" if pd.notna(value) else "not available")
    watchlist_html = f'<div class="table-wrap">{watchlist.to_html(index=False, classes="data", border=0)}</div>'

    month_finding = "No month met the minimum volume threshold."
    if peak_month is not None:
        month_finding = (
            f"{peak_month['month']:%B %Y} had the highest late-delivery rate among months with at least "
            f"{MONTH_MIN_ORDERS:,} eligible orders: {peak_month['late_delivery_rate']:.1%} across "
            f"{int(peak_month['eligible_orders']):,} orders."
        )
    state_finding = "No state met the minimum volume threshold."
    if highest_state is not None and lowest_state is not None:
        state_finding = (
            f"Among states with at least {STATE_MIN_ORDERS:,} eligible orders, {highest_state['customer_state']} "
            f"had a {highest_state['late_delivery_rate']:.1%} late rate versus {lowest_state['late_delivery_rate']:.1%} "
            f"in {lowest_state['customer_state']}, a descriptive gap of "
            f"{highest_state['late_delivery_rate'] - lowest_state['late_delivery_rate']:.1%}."
        )
    seller_finding = (
        f"Across {int(seller_summary['eligible_sellers']):,} sellers with at least {SELLER_MIN_ORDERS} eligible orders, "
        f"the median late rate was {seller_summary['median_late_delivery_rate']:.1%}, the 90th percentile was "
        f"{seller_summary['p90_late_delivery_rate']:.1%}, and the seller-level late-rate/review correlation was "
        f"{seller_summary['late_review_correlation']:.3f}."
        if not pd.isna(seller_summary.get("median_late_delivery_rate"))
        else "The fixture is too small for a seller distribution."
    )

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CommerceLens Analytics Report</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#17202a;line-height:1.5}}h1{{margin-bottom:.2rem}}h2{{margin-top:2.2rem;border-bottom:1px solid #d8dee4;padding-bottom:.35rem}}.muted{{color:#5f6b76}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.25rem}}figure{{margin:0}}img{{width:100%;height:auto;border:1px solid #d8dee4}}table{{border-collapse:collapse;width:100%;margin:1rem 0}}th,td{{border-bottom:1px solid #d8dee4;padding:.5rem;text-align:left}}th{{background:#f6f8fa}}.data{{font-size:.9rem}}.table-wrap{{overflow-x:auto}}li{{margin:.55rem 0}}code{{overflow-wrap:anywhere}}</style></head>
<body><h1>CommerceLens Analytics Report</h1><p class="muted">Source: <a href="https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce">Olist Brazilian E-Commerce Public Dataset</a> (Kaggle, CC-BY-NC-SA-4.0). Purchase coverage: {coverage}. Generated: {generated_at}.</p><p class="muted">These are descriptive associations from a historical snapshot, not causal or realized-revenue claims.</p>
<h2>Key metrics</h2><table>{metric_rows}</table>
<h2>Operational findings</h2><ul>
<li><strong>Delivery and reviews:</strong> among reviewed eligible orders, late deliveries averaged {_number(late, 'average_review_score'):.3f} stars versus {_number(on_time, 'average_review_score'):.3f} on time, a {review_gap:.3f}-point gap. The 1-2 star review rate was {low_review_gap * 100:.1f} percentage points higher in the late group.</li>
<li><strong>Monthly reliability:</strong> {month_finding}</li>
<li><strong>Geography:</strong> {state_finding}</li>
<li><strong>Seller dispersion:</strong> {seller_finding}</li>
</ul>
<div class="grid"><figure><img src="monthly_reliability.png" alt="Monthly delivery reliability"><figcaption>Monthly late-delivery rate with a minimum-volume filter.</figcaption></figure>
<figure><img src="review_by_delivery.png" alt="Review score by delivery status"><figcaption>Average review score by delivery status.</figcaption></figure>
<figure><img src="state_reliability.png" alt="State late-delivery rates"><figcaption>State reliability with a minimum-volume filter.</figcaption></figure></div>
<h2>High-volume state comparison</h2><p>States shown have at least {STATE_MIN_ORDERS:,} eligible orders; the table is ordered by order volume.</p>{state_html}
<h2>Seller reliability watchlist</h2><p>Highest late-delivery rates among sellers with at least {SELLER_MIN_ORDERS} eligible orders. Truncated IDs remain dataset identifiers, not business names.</p>{watchlist_html}
<h2>Method and reproduction</h2><p>The late-delivery denominator includes only orders with both actual and estimated delivery timestamps. SQL definitions are versioned in <a href="https://github.com/momo9113-coder/commercelens-analytics-warehouse/blob/main/sql/analysis/analysis.sql">analysis.sql</a>; interpretation and limitations are documented in <a href="https://github.com/momo9113-coder/commercelens-analytics-warehouse/blob/main/docs/ANALYSIS.md">docs/ANALYSIS.md</a>.</p><p><code>python -m commercelens.cli report --data-dir data/raw --db-path reports/commercelens.duckdb --output-dir site</code></p>
</body></html>"""
    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path
