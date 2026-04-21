from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def ensure_dir(path: str | Path) -> Path:
    folder = Path(path)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def load_csv_table(path: str | Path, parse_dates: list[str] | None = None) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=parse_dates)


def create_mysql_engine(
    user: str,
    password: str,
    host: str = "localhost",
    port: int = 3306,
    database: str = "food_delivery_analytics",
    echo: bool = False,
) -> Engine:
    uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    return create_engine(uri, echo=echo, pool_pre_ping=True, future=True)


def safe_divide(numerator: float | int, denominator: float | int) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def winsorize_series(series: pd.Series, lower_q: float = 0.01, upper_q: float = 0.99) -> pd.Series:
    lower = series.quantile(lower_q)
    upper = series.quantile(upper_q)
    return series.clip(lower=lower, upper=upper)


def to_feature_matrix(df: pd.DataFrame, target_col: str) -> tuple[pd.DataFrame, np.ndarray]:
    x = df.drop(columns=[target_col])
    y = df[target_col].astype(int).to_numpy()
    return x, y


def summarize_binary_target(y: np.ndarray | pd.Series, label: str = "target") -> dict[str, Any]:
    arr = np.asarray(y)
    positive_rate = float(arr.mean()) if len(arr) else 0.0
    return {"label": label, "n_obs": int(len(arr)), "positive_rate": positive_rate}
