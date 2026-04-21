from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


def save_artifact(obj: Any, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(obj, path)
    return path


def load_artifact(path: str | Path) -> Any:
    return joblib.load(path)


def estimate_uplift_economics(
    scored_users: pd.DataFrame,
    score_col: str = "churn_proba",
    threshold: float = 0.6,
    avg_order_value_rub: float = 780.0,
    gross_margin_pct: float = 0.28,
    retention_campaign_cost_rub: float = 95.0,
    expected_save_rate: float = 0.19,
) -> dict[str, float]:
    target_users = scored_users.loc[scored_users[score_col] >= threshold].copy()
    n_users = len(target_users)
    if n_users == 0:
        return {
            "n_targeted_users": 0.0,
            "campaign_cost_rub": 0.0,
            "saved_users": 0.0,
            "gross_profit_uplift_rub": 0.0,
            "net_uplift_rub": 0.0,
            "roi": 0.0,
        }

    campaign_cost = n_users * retention_campaign_cost_rub
    saved_users = n_users * expected_save_rate
    gross_profit_uplift = saved_users * avg_order_value_rub * gross_margin_pct
    net_uplift = gross_profit_uplift - campaign_cost
    roi = net_uplift / campaign_cost if campaign_cost else 0.0

    return {
        "n_targeted_users": float(n_users),
        "campaign_cost_rub": float(campaign_cost),
        "saved_users": float(saved_users),
        "gross_profit_uplift_rub": float(gross_profit_uplift),
        "net_uplift_rub": float(net_uplift),
        "roi": float(roi),
    }


def top_k_precision(y_true: np.ndarray, y_score: np.ndarray, k: int = 1000) -> float:
    if len(y_true) == 0:
        return 0.0
    k = int(np.clip(k, 1, len(y_true)))
    top_idx = np.argsort(-y_score)[:k]
    return float(np.mean(y_true[top_idx]))
