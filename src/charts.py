"""
Interactive & Publication-Quality Visualization Suite.
Digital Payment Failure Analysis
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure project root is in sys.path so the module works standalone
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config import FIGURES_DIR, LIGHT_THEME_COLORS
from src.metrics import (
    calculate_grouped_metrics,
    calculate_failure_reasons_breakdown,
    calculate_hourly_metrics,
    calculate_dow_metrics,
)

logger = logging.getLogger(__name__)


def apply_base_layout(fig: go.Figure, title_text: str) -> go.Figure:
    """Apply consistent light-themed professional styling to any Plotly figure.
    
    Guarantees dark, readable text on light backgrounds with proper margins,
    crisp gridlines, and professional legends.
    """
    fig.update_layout(
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            size=12,
            color="#1F2937"
        ),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        margin=dict(l=65, r=45, t=65, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            font=dict(color="#1F2937", size=11)
        ),
        title=dict(
            text=title_text,
            x=0.01,
            xanchor="left",
            font=dict(
                family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                size=15,
                color="#0F172A"
            )
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font_size=12,
            font_family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            font_color="#0F172A",
            bordercolor="#CBD5E1"
        )
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#E2E8F0",
        zeroline=False,
        tickfont=dict(color="#334155", size=11),
        title_font=dict(color="#0F172A", size=12),
        linecolor="#CBD5E1"
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#E2E8F0",
        zeroline=False,
        tickfont=dict(color="#334155", size=11),
        title_font=dict(color="#0F172A", size=12),
        linecolor="#CBD5E1"
    )
    return fig


def plot_status_distribution(df: pd.DataFrame) -> go.Figure:
    """Donut chart illustrating overall platform success vs. failure proportion."""
    counts = df["transaction_status"].value_counts().reset_index()
    counts.columns = ["Status", "Count"]
    total = counts["Count"].sum()
    counts["Percentage"] = (counts["Count"] / total * 100).round(2)

    color_map = {
        "SUCCESS": "#10B981",  # Emerald Green
        "FAILED": "#EF4444"    # Rose Red
    }

    fig = go.Figure(
        data=[
            go.Pie(
                labels=counts["Status"],
                values=counts["Count"],
                hole=0.58,
                marker=dict(
                    colors=[color_map.get(s, "#94A3B8") for s in counts["Status"]],
                    line=dict(color="#FFFFFF", width=2)
                ),
                textinfo="label+percent",
                textposition="inside",
                insidetextfont=dict(color="#FFFFFF", size=12),
                hovertemplate="<b>%{label}</b><br>Transactions: %{value:,}<br>Proportion: %{percent}<extra></extra>"
            )
        ]
    )
    apply_base_layout(fig, "<b>Platform Transaction Outcome Distribution</b>")
    fig.add_annotation(
        text=f"<span style='font-size:11px;color:#64748B;'>Total Volume</span><br><b style='font-size:17px;color:#0F172A;'>{total:,}</b>",
        x=0.5, y=0.5,
        font=dict(family="Inter, sans-serif"),
        showarrow=False
    )
    fig.update_layout(showlegend=False)
    return fig


def plot_failure_rate_by_bank(df: pd.DataFrame) -> go.Figure:
    """Bar chart ranking core banking switches by observed failure rate."""
    bank_df = calculate_grouped_metrics(df, "bank_switch")
    bank_df = bank_df.sort_values(by="failure_rate_pct", ascending=True)

    colors = [
        "#EF4444" if rate > 15 else "#3B82F6"
        for rate in bank_df["failure_rate_pct"]
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=bank_df["bank_switch"],
            x=bank_df["failure_rate_pct"],
            orientation="h",
            marker=dict(color=colors, line=dict(color="#FFFFFF", width=1)),
            text=[f"<b>{rate:.2f}%</b> (n={int(vol):,})" for rate, vol in zip(bank_df["failure_rate_pct"], bank_df["total_transactions"])],
            textposition="outside",
            textfont=dict(color="#1F2937", size=11),
            cliponaxis=False,
            hovertemplate="<b>%{y} Switch</b><br>Failure Rate: %{x:.2f}%<extra></extra>"
        )
    )

    apply_base_layout(fig, "<b>Failure Rate by Core Bank Switch</b> (Annotated with Volume)")
    max_rate = bank_df["failure_rate_pct"].max() if len(bank_df) > 0 else 25
    fig.update_xaxes(title_text="Failure Rate (%)", range=[0, max(max_rate * 1.35, 15)])
    fig.update_yaxes(title_text="Bank Switch")
    return fig


def plot_failure_rate_by_method(df: pd.DataFrame) -> go.Figure:
    """Bar chart comparing failure rates across payment instruments."""
    pm_df = calculate_grouped_metrics(df, "payment_method")
    pm_df = pm_df.sort_values(by="failure_rate_pct", ascending=False)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=pm_df["payment_method"],
            y=pm_df["failure_rate_pct"],
            marker=dict(color="#1E3A8A", line=dict(color="#FFFFFF", width=1)),
            text=[f"<b>{rate:.2f}%</b><br>({int(fail):,} fails)" for rate, fail in zip(pm_df["failure_rate_pct"], pm_df["failed_transactions"])],
            textposition="outside",
            textfont=dict(color="#1F2937", size=11),
            cliponaxis=False,
            hovertemplate="<b>%{x}</b><br>Failure Rate: %{y:.2f}%<br>Total Txns: %{customdata:,}<extra></extra>",
            customdata=pm_df["total_transactions"]
        )
    )

    apply_base_layout(fig, "<b>Failure Rate by Payment Instrument</b>")
    max_rate = pm_df["failure_rate_pct"].max() if len(pm_df) > 0 else 25
    fig.update_xaxes(title_text="Payment Method")
    fig.update_yaxes(title_text="Failure Rate (%)", range=[0, max(max_rate * 1.35, 20)])
    return fig


def plot_failure_reasons_breakdown(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart depicting the Pareto distribution of failure root causes."""
    reasons_df = calculate_failure_reasons_breakdown(df)
    reasons_df = reasons_df.sort_values(by="failed_count", ascending=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=[f"{r} ({e})" for r, e in zip(reasons_df["failure_reason"], reasons_df["error_code"])],
            x=reasons_df["failed_count"],
            orientation="h",
            marker=dict(color="#2563EB", line=dict(color="#FFFFFF", width=1)),
            text=[f"<b>{int(c):,}</b> ({s:.1f}%)" for c, s in zip(reasons_df["failed_count"], reasons_df["share_of_failures_pct"])],
            textposition="outside",
            textfont=dict(color="#1F2937", size=11),
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Failure Count: %{x:,}<extra></extra>"
        )
    )

    apply_base_layout(fig, "<b>Root-Cause Failure Reasons & Error Codes (Pareto)</b>")
    max_count = reasons_df["failed_count"].max() if len(reasons_df) > 0 else 1000
    fig.update_xaxes(title_text="Failed Transactions Count", range=[0, max_count * 1.25])
    fig.update_yaxes(title_text="Failure Reason (Error Code)")
    return fig


def plot_hourly_trend_dual_axis(df: pd.DataFrame) -> go.Figure:
    """Dual-axis chart illustrating hourly transaction volume alongside failure rate and latency spikes."""
    hourly_df = calculate_hourly_metrics(df)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Bar: Transaction Volume
    fig.add_trace(
        go.Bar(
            x=hourly_df["hour_of_day"],
            y=hourly_df["total_transactions"],
            name="Volume (Attempts)",
            marker=dict(
                color="rgba(59, 130, 246, 0.20)",
                line=dict(color="#3B82F6", width=1)
            ),
            hovertemplate="Hour %{x}:00<br>Total Txns: %{y:,}<extra></extra>"
        ),
        secondary_y=False
    )

    # Line: Failure Rate
    fig.add_trace(
        go.Scatter(
            x=hourly_df["hour_of_day"],
            y=hourly_df["failure_rate_pct"],
            name="Failure Rate (%)",
            mode="lines+markers",
            line=dict(color="#EF4444", width=3),
            marker=dict(size=7, color="#EF4444"),
            hovertemplate="Hour %{x}:00<br>Failure Rate: %{y:.2f}%<extra></extra>"
        ),
        secondary_y=True
    )

    # Line: P95 Latency
    fig.add_trace(
        go.Scatter(
            x=hourly_df["hour_of_day"],
            y=hourly_df["p95_latency_ms"],
            name="P95 Latency (ms)",
            mode="lines",
            line=dict(color="#D97706", width=2.5, dash="dot"),
            hovertemplate="Hour %{x}:00<br>P95 Latency: %{y:.1f} ms<extra></extra>"
        ),
        secondary_y=False
    )

    apply_base_layout(fig, "<b>Hourly Telemetry: Volume vs. Failure Rate & Response Latency</b>")
    fig.update_xaxes(
        title_text="Hour of Day (24-Hour Clock)",
        tickmode="linear",
        tick0=0,
        dtick=2,
        tickfont=dict(color="#334155", size=11),
        title_font=dict(color="#0F172A", size=12)
    )
    fig.update_yaxes(
        title_text="Volume / P95 Latency (ms)",
        secondary_y=False,
        showgrid=True,
        gridcolor="#E2E8F0",
        tickfont=dict(color="#334155", size=11),
        title_font=dict(color="#0F172A", size=12)
    )
    max_fail = hourly_df["failure_rate_pct"].max() if len(hourly_df) > 0 else 25
    fig.update_yaxes(
        title_text="Failure Rate (%)",
        secondary_y=True,
        showgrid=False,
        range=[0, max(max_fail * 1.35, 25)],
        tickfont=dict(color="#EF4444", size=11),
        title_font=dict(color="#EF4444", size=12)
    )
    return fig


def plot_peak_hour_bank_breakdown(df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart comparing peak (20:00-22:59) vs. off-peak failure rates across bank switches."""
    df_copy = df.copy()
    if "is_peak_window" not in df_copy.columns:
        ts = pd.to_datetime(df_copy["transaction_timestamp"])
        df_copy["is_peak_window"] = ts.dt.hour.isin([20, 21, 22]).astype(int)

    def calc_rates(sub):
        tot = len(sub)
        fail = (sub["transaction_status"] == "FAILED").sum()
        return (fail / tot * 100.0) if tot > 0 else 0.0

    peak = df_copy[df_copy["is_peak_window"] == 1].groupby("bank_switch").apply(calc_rates, include_groups=False).reset_index()
    peak.columns = ["bank_switch", "peak_rate"]

    offpeak = df_copy[df_copy["is_peak_window"] == 0].groupby("bank_switch").apply(calc_rates, include_groups=False).reset_index()
    offpeak.columns = ["bank_switch", "offpeak_rate"]

    merged = peak.merge(offpeak, on="bank_switch")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=merged["bank_switch"],
            y=merged["peak_rate"],
            name="Peak Window (20:00 - 22:59)",
            marker=dict(color="#EF4444", line=dict(color="#FFFFFF", width=1)),
            text=[f"<b>{r:.1f}%</b>" for r in merged["peak_rate"]],
            textposition="outside",
            textfont=dict(color="#1F2937", size=11),
            cliponaxis=False
        )
    )
    fig.add_trace(
        go.Bar(
            x=merged["bank_switch"],
            y=merged["offpeak_rate"],
            name="Off-Peak Baseline",
            marker=dict(color="#3B82F6", line=dict(color="#FFFFFF", width=1)),
            text=[f"<b>{r:.1f}%</b>" for r in merged["offpeak_rate"]],
            textposition="outside",
            textfont=dict(color="#1F2937", size=11),
            cliponaxis=False
        )
    )

    apply_base_layout(fig, "<b>Switch Failure Rates: Peak Congestion vs. Off-Peak Baseline</b>")
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text="Bank Switch")
    max_peak = max(merged["peak_rate"].max(), merged["offpeak_rate"].max()) if len(merged) > 0 else 30
    fig.update_yaxes(title_text="Failure Rate (%)", range=[0, max(max_peak * 1.3, 40)])
    return fig


def plot_latency_box_by_status(df: pd.DataFrame) -> go.Figure:
    """Box plot contrasting response latency distributions across terminal outcomes."""
    sample_df = df.sample(n=min(5000, len(df)), random_state=42)

    fig = go.Figure()
    for status, color in [("SUCCESS", "#10B981"), ("FAILED", "#EF4444")]:
        sub = sample_df[sample_df["transaction_status"] == status]
        if not sub.empty:
            fig.add_trace(
                go.Box(
                    y=sub["latency_ms"],
                    name=status,
                    marker=dict(color=color),
                    boxpoints="outliers",
                    hovertemplate=f"<b>Status: {status}</b><br>Latency: %{{y}} ms<extra></extra>"
                )
            )

    apply_base_layout(fig, "<b>Response Latency Distribution by Terminal Outcome</b>")
    fig.update_xaxes(title_text="Transaction Status")
    fig.update_yaxes(title_text="Response Latency (ms)")
    fig.update_layout(showlegend=False)
    return fig


def plot_amount_band_failure_rate(df: pd.DataFrame) -> go.Figure:
    """Bar chart illustrating failure rates across transaction ticket size tiers."""
    df_copy = df.copy()
    if "amount_band" not in df_copy.columns:
        from src.feature_engineering import engineer_features
        df_copy = engineer_features(df_copy)

    amt_df = calculate_grouped_metrics(df_copy, "amount_band")
    colors = ["#1E3A8A", "#2563EB", "#0284C7", "#F59E0B"]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=amt_df["amount_band"],
            y=amt_df["failure_rate_pct"],
            marker=dict(color=colors[:len(amt_df)], line=dict(color="#FFFFFF", width=1)),
            text=[f"<b>{rate:.2f}%</b><br>({int(fail):,} fails)" for rate, fail in zip(amt_df["failure_rate_pct"], amt_df["failed_transactions"])],
            textposition="outside",
            textfont=dict(color="#1F2937", size=11),
            cliponaxis=False,
            hovertemplate="<b>%{x}</b><br>Failure Rate: %{y:.2f}%<br>Total Volume: %{customdata:,}<extra></extra>",
            customdata=amt_df["total_transactions"]
        )
    )

    apply_base_layout(fig, "<b>Failure Rate by Transaction Ticket Size Tier</b>")
    max_rate = amt_df["failure_rate_pct"].max() if len(amt_df) > 0 else 20
    fig.update_xaxes(title_text="Amount Band")
    fig.update_yaxes(title_text="Failure Rate (%)", range=[0, max(max_rate * 1.35, 20)])
    fig.update_layout(showlegend=False)
    return fig


def export_all_report_figures(df: pd.DataFrame = None) -> None:
    """Generate and save publication-quality static chart assets to reports/figures/."""
    from src.data_loader import load_processed_data
    if df is None:
        df = load_processed_data()

    if "amount_band" not in df.columns or "is_peak_window" not in df.columns:
        from src.feature_engineering import engineer_features
        df = engineer_features(df)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Exporting publication figures to reports/figures/...")

    figures = {
        "status_distribution.html": plot_status_distribution(df),
        "failure_rate_by_bank.html": plot_failure_rate_by_bank(df),
        "failure_rate_by_method.html": plot_failure_rate_by_method(df),
        "failure_reasons_pareto.html": plot_failure_reasons_breakdown(df),
        "hourly_trend_dual_axis.html": plot_hourly_trend_dual_axis(df),
        "peak_hour_bank_breakdown.html": plot_peak_hour_bank_breakdown(df),
        "latency_box_by_status.html": plot_latency_box_by_status(df),
        "amount_band_failure_rate.html": plot_amount_band_failure_rate(df),
    }

    for filename, fig in figures.items():
        html_path = FIGURES_DIR / filename
        fig.write_html(str(html_path))

    logger.info("All interactive figure HTML assets exported successfully.")


if __name__ == "__main__":
    export_all_report_figures()
    print("=" * 60)
    print("FIGURES GENERATION COMPLETE")
    print("=" * 60)
