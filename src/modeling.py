from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

try:
    from xgboost import XGBClassifier
except ImportError:  # pragma: no cover - fallback is used if xgboost is unavailable
    XGBClassifier = None

from sklearn.ensemble import HistGradientBoostingClassifier


@dataclass
class ModelingResult:
    model: Any
    threshold: float
    metrics: dict[str, float]
    feature_names: list[str]
    x_train: pd.DataFrame
    x_test: pd.DataFrame
    y_train: np.ndarray
    y_test: np.ndarray
    y_pred_proba: np.ndarray
    y_pred_label: np.ndarray


def _best_balanced_threshold(y_true: np.ndarray, y_pred_proba: np.ndarray) -> float:
    thresholds = np.unique(np.concatenate(([0.0], y_pred_proba, [1.0])))
    best_threshold = 0.5
    best_balanced_accuracy = -np.inf
    best_f1 = -np.inf

    for threshold in thresholds:
        y_pred = (y_pred_proba >= threshold).astype(int)
        balanced_acc = balanced_accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        if balanced_acc > best_balanced_accuracy or (
            np.isclose(balanced_acc, best_balanced_accuracy) and f1 > best_f1
        ):
            best_threshold = float(threshold)
            best_balanced_accuracy = float(balanced_acc)
            best_f1 = float(f1)

    return best_threshold


def train_churn_model(
    dataset: pd.DataFrame,
    target_col: str = "churn_label",
    test_size: float = 0.25,
    random_state: int = 42,
) -> ModelingResult:
    if target_col not in dataset.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")

    x = dataset.drop(columns=[target_col, "future_orders_cnt", "user_id"], errors="ignore")
    y = dataset[target_col].astype(int).to_numpy()

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=test_size, random_state=random_state, stratify=y
    )

    if XGBClassifier is not None:
        model = XGBClassifier(
            n_estimators=350,
            max_depth=5,
            learning_rate=0.06,
            subsample=0.9,
            colsample_bytree=0.85,
            reg_alpha=0.2,
            reg_lambda=1.4,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=random_state,
        )
    else:
        model = HistGradientBoostingClassifier(
            max_depth=6,
            learning_rate=0.08,
            max_iter=320,
            random_state=random_state,
        )

    model.fit(x_train, y_train)

    if hasattr(model, "predict_proba"):
        y_pred_proba = model.predict_proba(x_test)[:, 1]
    else:
        y_pred_proba = model.decision_function(x_test)
        y_pred_proba = (y_pred_proba - y_pred_proba.min()) / np.clip(
            y_pred_proba.max() - y_pred_proba.min(), 1e-9, None
        )

    threshold = _best_balanced_threshold(y_test, y_pred_proba)
    y_pred_label = (y_pred_proba >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred_label).ravel()
    metrics = {
        "roc_auc": float(roc_auc_score(y_test, y_pred_proba)),
        "pr_auc": float(average_precision_score(y_test, y_pred_proba)),
        "f1": float(f1_score(y_test, y_pred_label)),
        "precision": float(precision_score(y_test, y_pred_label, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred_label, zero_division=0)),
        "tp": float(tp),
        "fp": float(fp),
        "tn": float(tn),
        "fn": float(fn),
    }

    return ModelingResult(
        model=model,
        threshold=threshold,
        metrics=metrics,
        feature_names=list(x.columns),
        x_train=x_train,
        x_test=x_test,
        y_train=y_train,
        y_test=y_test,
        y_pred_proba=y_pred_proba,
        y_pred_label=y_pred_label,
    )


def get_feature_importance(model: Any, feature_names: list[str], top_n: int = 25) -> pd.DataFrame:
    if hasattr(model, "feature_importances_"):
        importance = model.feature_importances_
    else:
        importance = np.zeros(len(feature_names))
    frame = pd.DataFrame({"feature": feature_names, "importance": importance})
    return frame.sort_values("importance", ascending=False).head(top_n).reset_index(drop=True)
