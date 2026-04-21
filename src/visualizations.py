from __future__ import annotations

from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def repeat_order_rate_figure(repeat_df: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        repeat_df,
        x="window_days",
        y="repeat_rate_pct",
        text=repeat_df["repeat_rate_pct"].map(lambda value: f"{value:.1f}%"),
        title="Repeat Order Rate by Window",
        labels={
            "window_days": "Days after first order",
            "repeat_rate_pct": "Users with repeat order, %",
        },
    )
    fig.update_traces(marker_color="#2563EB", textposition="outside", cliponaxis=False)
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        yaxis_ticksuffix="%",
        margin=dict(l=60, r=30, t=70, b=50),
    )
    return fig


def retention_curve_figure(retention_df: pd.DataFrame) -> go.Figure:
    return repeat_order_rate_figure(retention_df)


def rfm_bubble_figure(rfm_df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        rfm_df,
        x="recency_days",
        y="frequency_orders",
        size="monetary_rub",
        color="segment",
        hover_data=["user_id", "rfm_score"],
        title="RFM Segmentation Bubble Chart",
        labels={
            "recency_days": "Recency (days)",
            "frequency_orders": "Frequency (orders)",
            "monetary_rub": "Monetary value (RUB)",
        },
        size_max=35,
    )
    fig.update_layout(template="plotly_white")
    return fig


def metric_card_figure(metrics: dict[str, float], title: str = "Model Quality") -> go.Figure:
    fig = go.Figure()
    values = [
        f"ROC-AUC: {metrics.get('roc_auc', 0):.3f}",
        f"PR-AUC: {metrics.get('pr_auc', 0):.3f}",
        f"F1: {metrics.get('f1', 0):.3f}",
        f"Recall: {metrics.get('recall', 0):.3f}",
    ]
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=metrics.get("roc_auc", 0),
            number={"valueformat": ".3f"},
            title={"text": "<br>".join([title] + values)},
        )
    )
    fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=70, b=20))
    return fig


def feature_importance_figure(importance_df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    top = importance_df.head(top_n).iloc[::-1]
    fig = go.Figure(
        data=[
            go.Bar(
                x=top["importance"],
                y=top["feature"],
                orientation="h",
                marker_color="#0a9396",
            )
        ]
    )
    fig.update_layout(
        template="plotly_white",
        title="Top Model Features",
        xaxis_title="Importance",
        yaxis_title="Feature",
    )
    return fig


def dashboard_summary_figure(
    dates: Iterable,
    orders: Iterable,
    gmv: Iterable,
    dau: Iterable,
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(dates), y=list(orders), name="Orders", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=list(dates), y=list(gmv), name="GMV (RUB)", mode="lines"))
    fig.add_trace(go.Scatter(x=list(dates), y=list(dau), name="DAU", mode="lines"))
    fig.update_layout(
        template="plotly_white",
        title="Core Product Metrics Trend",
        xaxis_title="Date",
        yaxis_title="Value",
        legend_orientation="h",
        legend_y=-0.25,
    )
    return fig
