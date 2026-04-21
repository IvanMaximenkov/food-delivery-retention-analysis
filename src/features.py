from __future__ import annotations

import numpy as np
import pandas as pd


def _compute_order_aggregates(orders: pd.DataFrame) -> pd.DataFrame:
    delivered = orders.loc[orders["order_status"] == "delivered"].copy()
    delivered["order_date"] = pd.to_datetime(delivered["order_ts"]).dt.date

    grouped = (
        delivered.groupby("user_id")
        .agg(
            total_orders=("order_id", "count"),
            total_gmv_rub=("basket_value_rub", "sum"),
            avg_order_value_rub=("basket_value_rub", "mean"),
            avg_discount_rub=("discount_rub", "mean"),
            avg_delivery_fee_rub=("delivery_fee_rub", "mean"),
            avg_delivery_minutes=("delivery_minutes", "mean"),
            avg_margin_rub=("gross_margin_rub", "mean"),
            first_order_ts=("order_ts", "min"),
            last_order_ts=("order_ts", "max"),
            active_order_days=("order_date", "nunique"),
        )
        .reset_index()
    )

    grouped["avg_orders_per_active_day"] = (
        grouped["total_orders"] / grouped["active_order_days"].replace(0, np.nan)
    ).fillna(0.0)
    return grouped


def _compute_session_aggregates(sessions: pd.DataFrame) -> pd.DataFrame:
    sessions = sessions.copy()
    sessions["session_start_ts"] = pd.to_datetime(sessions["session_start_ts"])
    sessions["session_end_ts"] = pd.to_datetime(sessions["session_end_ts"])
    sessions["session_minutes"] = (
        sessions["session_end_ts"] - sessions["session_start_ts"]
    ).dt.total_seconds() / 60
    sessions["session_minutes"] = sessions["session_minutes"].clip(lower=0.1, upper=240)

    grouped = (
        sessions.groupby("user_id")
        .agg(
            total_sessions=("session_id", "count"),
            avg_session_minutes=("session_minutes", "mean"),
            push_open_rate=("is_push_opened", "mean"),
            session_to_order_rate=("did_order", "mean"),
            last_session_ts=("session_start_ts", "max"),
        )
        .reset_index()
    )
    return grouped


def _compute_ab_features(assignments: pd.DataFrame) -> pd.DataFrame:
    assignments = assignments.copy()
    assignments["is_treatment"] = (assignments["variant"] == "treatment").astype(int)
    return assignments[["user_id", "variant", "is_treatment", "assigned_at"]]


def build_user_level_features(
    users: pd.DataFrame,
    orders: pd.DataFrame,
    sessions: pd.DataFrame,
    assignments: pd.DataFrame,
    label_horizon_days: int = 30,
    inactivity_threshold_days: int = 28,
    reference_date: str | None = None,
) -> pd.DataFrame:
    users = users.copy()
    users["registration_ts"] = pd.to_datetime(users["registration_ts"])
    orders = orders.copy()
    orders["order_ts"] = pd.to_datetime(orders["order_ts"])
    sessions = sessions.copy()
    sessions["session_start_ts"] = pd.to_datetime(sessions["session_start_ts"])
    sessions["session_end_ts"] = pd.to_datetime(sessions["session_end_ts"])
    assignments = assignments.copy()
    assignments["assigned_at"] = pd.to_datetime(assignments["assigned_at"])

    if reference_date is None:
        max_observed_order_ts = orders["order_ts"].max()
        if pd.isna(max_observed_order_ts):
            reference_ts = users["registration_ts"].max()
        else:
            reference_ts = max_observed_order_ts - pd.Timedelta(days=label_horizon_days)
    else:
        reference_ts = pd.Timestamp(reference_date)

    historical_orders = orders.loc[orders["order_ts"] <= reference_ts].copy()
    historical_sessions = sessions.loc[sessions["session_start_ts"] <= reference_ts].copy()
    historical_assignments = assignments.loc[assignments["assigned_at"] <= reference_ts].copy()

    order_features = _compute_order_aggregates(historical_orders)
    session_features = _compute_session_aggregates(historical_sessions)
    ab_features = _compute_ab_features(historical_assignments)

    features = users.merge(order_features, on="user_id", how="left")
    features = features.merge(session_features, on="user_id", how="left")
    features = features.merge(ab_features, on="user_id", how="left")

    date_cols = ["first_order_ts", "last_order_ts", "last_session_ts", "assigned_at"]
    for col in date_cols:
        if col in features:
            features[col] = pd.to_datetime(features[col])

    features["days_since_registration"] = (
        reference_ts - features["registration_ts"]
    ).dt.days.clip(lower=0)
    features["days_since_last_order"] = (
        reference_ts - features["last_order_ts"]
    ).dt.days.fillna(999).astype(int)
    features["days_since_last_session"] = (
        reference_ts - features["last_session_ts"]
    ).dt.days.fillna(999).astype(int)
    features["days_since_assignment"] = (
        reference_ts - features["assigned_at"]
    ).dt.days.fillna(999).astype(int)

    numeric_defaults = {
        "total_orders": 0,
        "total_gmv_rub": 0.0,
        "avg_order_value_rub": 0.0,
        "avg_discount_rub": 0.0,
        "avg_delivery_fee_rub": 0.0,
        "avg_delivery_minutes": 0.0,
        "avg_margin_rub": 0.0,
        "active_order_days": 0,
        "avg_orders_per_active_day": 0.0,
        "total_sessions": 0,
        "avg_session_minutes": 0.0,
        "push_open_rate": 0.0,
        "session_to_order_rate": 0.0,
        "is_treatment": 0,
    }
    for col, default in numeric_defaults.items():
        if col in features:
            features[col] = features[col].fillna(default)

    features["order_intensity"] = (
        features["total_orders"] / (features["days_since_registration"] + 1)
    )
    features["gmv_per_day"] = features["total_gmv_rub"] / (features["days_since_registration"] + 1)
    features["engagement_ratio"] = (
        features["total_sessions"] / (features["days_since_registration"] + 1)
    )
    features["is_model_eligible"] = (
        (features["total_orders"] > 0) & (features["days_since_last_order"] <= inactivity_threshold_days)
    ).astype(int)

    future_cutoff = reference_ts + pd.Timedelta(days=label_horizon_days)
    future_orders = orders.loc[
        (orders["order_status"] == "delivered")
        & (orders["order_ts"] > reference_ts)
        & (orders["order_ts"] <= future_cutoff)
    ][["user_id", "order_id"]]
    has_future_order = future_orders.groupby("user_id")["order_id"].count().rename("future_orders_cnt")

    features = features.merge(has_future_order, on="user_id", how="left")
    features["future_orders_cnt"] = features["future_orders_cnt"].fillna(0).astype(int)
    features["churn_label"] = (features["future_orders_cnt"] == 0).astype(int)
    return features


def make_modeling_dataset(features: pd.DataFrame, eligible_only: bool = True) -> pd.DataFrame:
    features = features.copy()
    if eligible_only and "is_model_eligible" in features.columns:
        features = features.loc[features["is_model_eligible"] == 1].copy()

    categorical_cols = ["acquisition_channel", "city", "device_os", "gender", "loyalty_tier", "variant"]
    date_cols = ["registration_ts", "first_order_ts", "last_order_ts", "last_session_ts", "assigned_at"]
    features[categorical_cols] = features[categorical_cols].fillna("unknown")
    dataset = pd.get_dummies(
        features.drop(columns=date_cols + ["is_model_eligible"], errors="ignore"),
        columns=categorical_cols,
        drop_first=False,
    )
    return dataset
