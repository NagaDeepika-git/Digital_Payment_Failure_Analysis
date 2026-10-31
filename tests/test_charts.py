"""
Tests for Visualization Suite & Light Theme Styling.
Digital Payment Failure Analysis
"""

import pytest
import plotly.graph_objects as go
from src.charts import (
    apply_base_layout,
    plot_status_distribution,
    plot_failure_rate_by_bank,
    plot_failure_rate_by_method,
    plot_failure_reasons_breakdown,
    plot_hourly_trend_dual_axis,
    plot_peak_hour_bank_breakdown,
    plot_latency_box_by_status,
    plot_amount_band_failure_rate,
)


def test_apply_base_layout():
    """Verify that apply_base_layout injects proper light theme styling."""
    fig = go.Figure(data=[go.Bar(x=["A", "B"], y=[1, 2])])
    styled_fig = apply_base_layout(fig, "Test Title")

    assert styled_fig.layout.paper_bgcolor == "#FFFFFF"
    assert styled_fig.layout.plot_bgcolor == "#F8FAFC"
    assert styled_fig.layout.font.color == "#1F2937"
    assert styled_fig.layout.title.text == "Test Title"
    assert styled_fig.layout.title.font.color == "#0F172A"


def test_all_chart_generators(sample_cleaned_dataframe):
    """Verify that all 8 chart generators return valid Plotly Figures on sample data."""
    df = sample_cleaned_dataframe

    figs = [
        plot_status_distribution(df),
        plot_failure_rate_by_bank(df),
        plot_failure_rate_by_method(df),
        plot_failure_reasons_breakdown(df),
        plot_hourly_trend_dual_axis(df),
        plot_peak_hour_bank_breakdown(df),
        plot_latency_box_by_status(df),
        plot_amount_band_failure_rate(df),
    ]

    for fig in figs:
        assert isinstance(fig, go.Figure)
        assert fig.layout.paper_bgcolor == "#FFFFFF"
        assert fig.layout.plot_bgcolor == "#F8FAFC"
        assert len(fig.data) >= 1
