"""
ai_models/common/data_cleaning.py
Reusable data-cleaning primitives: missing-value handling, outlier removal,
and standardisation / normalisation used by every AI domain's preprocessing
pipeline.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

FillStrategy = Literal["mean", "median", "mode", "ffill", "constant"]
OutlierMethod = Literal["iqr", "zscore"]


def fill_missing(df: pd.DataFrame, columns: list[str] | None = None, strategy: FillStrategy = "mean", constant: float | str = 0.0) -> pd.DataFrame:
    """Fill missing values in the selected (or all) columns.

    Args:
        df: Input dataframe (a copy is returned).
        columns: Columns to clean; defaults to every column.
        strategy: 'mean', 'median', 'mode', 'ffill' or 'constant'.
        constant: Value used when strategy == 'constant'.

    Returns:
        A new dataframe with missing values filled.
    """
    out = df.copy()
    cols = list(columns) if columns else list(out.columns)
    for col in cols:
        if col not in out.columns or not out[col].isna().any():
            continue
        if strategy == "mean":
            out[col] = out[col].fillna(pd.to_numeric(out[col], errors="coerce").mean())
        elif strategy == "median":
            out[col] = out[col].fillna(pd.to_numeric(out[col], errors="coerce").median())
        elif strategy == "mode":
            mode = out[col].mode()
            out[col] = out[col].fillna(mode.iloc[0] if not mode.empty else constant)
        elif strategy == "ffill":
            out[col] = out[col].ffill()
        elif strategy == "constant":
            out[col] = out[col].fillna(constant)
        else:
            raise ValueError(f"Unsupported fill strategy: {strategy}")
    return out


def remove_outliers(df: pd.DataFrame, columns: list[str], method: OutlierMethod = "iqr", threshold: float = 1.5) -> pd.DataFrame:
    """Remove rows whose values in *any* of the given columns are outliers.

    - 'iqr': points outside [Q1 - threshold*IQR, Q3 + threshold*IQR].
    - 'zscore': points with an absolute z-score above `threshold`.

    Args:
        df: Input dataframe.
        columns: Numeric columns used to flag outliers.
        method: 'iqr' or 'zscore'.
        threshold: IQR multiplier or z-score bound.

    Returns:
        A new dataframe with outlier rows dropped.
    """
    out = df.copy()
    mask = np.ones(len(out), dtype=bool)
    for col in columns:
        if col not in out.columns:
            continue
        values = pd.to_numeric(out[col], errors="coerce")
        if method == "iqr":
            q1, q3 = values.quantile(0.25), values.quantile(0.75)
            low, high = q1 - threshold * (q3 - q1), q3 + threshold * (q3 - q1)
            mask &= values.between(low, high)
        elif method == "zscore":
            std = values.std()
            if not std or np.isnan(std):
                continue
            z = (values - values.mean()).abs() / std
            mask &= z <= threshold
        else:
            raise ValueError(f"Unsupported outlier method: {method}")
    return out[mask]


def standardize(df: pd.DataFrame, columns: list[str], scaler: StandardScaler | None = None) -> tuple[pd.DataFrame, StandardScaler]:
    """Centre + scale the selected columns to zero mean / unit variance.

    Args:
        df: Input dataframe.
        columns: Numeric columns to transform.
        scaler: A fitted scaler to reuse (or None to fit a fresh one).

    Returns:
        (transformed dataframe, fitted StandardScaler).
    """
    scaler = scaler or StandardScaler()
    out = df.copy()
    out[columns] = scaler.fit_transform(out[columns])
    return out, scaler


def normalize(df: pd.DataFrame, columns: list[str], scaler: MinMaxScaler | None = None) -> tuple[pd.DataFrame, MinMaxScaler]:
    """Scale the selected columns into the [0, 1] range.

    Args:
        df: Input dataframe.
        columns: Numeric columns to transform.
        scaler: A fitted scaler to reuse (or None to fit a fresh one).

    Returns:
        (transformed dataframe, fitted MinMaxScaler).
    """
    scaler = scaler or MinMaxScaler()
    out = df.copy()
    out[columns] = scaler.fit_transform(out[columns])
    return out, scaler


def encode_categorical(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """One-hot encode the selected categorical columns (drops original columns)."""
    out = df.copy()
    return pd.get_dummies(out, columns=columns, drop_first=False)
