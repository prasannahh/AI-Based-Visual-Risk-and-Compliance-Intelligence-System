"""
ml/kaggle_models.py
--------------------
Dataset loading, preprocessing pipelines, CANDIDATE algorithm definitions,
and inference functions for the 4 real-Kaggle-dataset models.

For each dataset, SEVERAL different algorithms are defined as candidates.
The actual comparison, evaluation (80:20 split + 5-fold CV), and selection
of the best-performing candidate happens in ml/evaluate_models.py, which
saves the winning pipeline here under a fixed filename (kaggle_<name>_model.pkl)
plus a small metadata file recording which algorithm won and why -- so the
rest of the app (predictions, simulation) always uses "whichever model
tested best" without needing to know which algorithm that turned out to be.

Where to put the downloaded CSV files: see data/README.md. This module reads
whatever file it finds in data/ that matches expected column names -- it
does NOT hardcode an exact Kaggle filename. Both .csv and .xlsx are supported.
"""

import os
import glob
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
)
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
def _read_any(path):
    if path.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(path)
    return pd.read_csv(path)


def _find_dataset(required_columns, filename_hints):
    """Find a file in data/ whose columns match what we expect."""
    candidates = glob.glob(os.path.join(DATA_DIR, "*.csv")) + \
        glob.glob(os.path.join(DATA_DIR, "*.xlsx")) + \
        glob.glob(os.path.join(DATA_DIR, "*.xls"))

    candidates.sort(key=lambda p: not any(h.lower() in os.path.basename(p).lower() for h in filename_hints))

    for path in candidates:
        try:
            df = _read_any(path)
        except Exception:
            continue
        cols_lower = {c.strip().lower() for c in df.columns}
        required_lower = {c.lower() for c in required_columns}
        if required_lower.issubset(cols_lower):
            return df, path
    return None, None


class DatasetNotFoundError(FileNotFoundError):
    pass


def build_pipeline(numeric_cols, categorical_cols, estimator):
    transformer = ColumnTransformer([
        ("num", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), numeric_cols),
        ("cat", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical_cols),
    ])
    return Pipeline([("prep", transformer), ("model", estimator)])


# ---------------------------------------------------------------------------
# 1. Obesity Level  (multi-class: 7 obesity categories)
# ---------------------------------------------------------------------------
OBESITY_NUMERIC = ["Age", "Height", "Weight", "FCVC", "NCP", "CH2O", "FAF", "TUE"]
OBESITY_CATEGORICAL = ["Gender", "family_history_with_overweight", "FAVC", "CAEC",
                        "SMOKE", "SCC", "CALC", "MTRANS"]
OBESITY_TARGET = "NObeyesdad"


def load_obesity_dataset():
    required = OBESITY_NUMERIC + OBESITY_CATEGORICAL + [OBESITY_TARGET]
    df, path = _find_dataset(required, ["obesity", "obesitydataset"])
    if df is None:
        raise DatasetNotFoundError(
            "Obesity Levels dataset not found in data/. Download it from "
            "https://www.kaggle.com/datasets/fatemehmehrparvar/obesity-levels "
            "and place the CSV in the data/ folder."
        )
    return df, path


def obesity_candidates():
    """4 candidate algorithms for the 7-class obesity classification task."""
    return {
        "RandomForestClassifier": lambda: RandomForestClassifier(
            n_estimators=250, max_depth=12, random_state=42, n_jobs=-1),
        "GradientBoostingClassifier": lambda: GradientBoostingClassifier(
            n_estimators=150, max_depth=3, random_state=42),
        "LogisticRegression": lambda: LogisticRegression(max_iter=2000),
        "KNeighborsClassifier": lambda: KNeighborsClassifier(n_neighbors=9),
    }


# ---------------------------------------------------------------------------
# 2. Diabetes Risk  (binary, imbalanced)
# ---------------------------------------------------------------------------
DIABETES_NUMERIC = ["age", "bmi", "HbA1c_level", "blood_glucose_level"]
DIABETES_CATEGORICAL = ["gender", "hypertension", "heart_disease", "smoking_history"]
DIABETES_TARGET = "diabetes"


def load_diabetes_dataset():
    required = DIABETES_NUMERIC + DIABETES_CATEGORICAL + [DIABETES_TARGET]
    df, path = _find_dataset(required, ["diabetes"])
    if df is None:
        raise DatasetNotFoundError(
            "Diabetes Prediction dataset not found in data/. Download it from "
            "https://www.kaggle.com/datasets/iammustafatz/diabetes-prediction-dataset "
            "and place the CSV in the data/ folder."
        )
    return df, path


def prep_diabetes(df):
    df = df.copy()
    df["hypertension"] = df["hypertension"].astype(str)
    df["heart_disease"] = df["heart_disease"].astype(str)
    return df


def diabetes_candidates():
    """4 candidate algorithms for binary diabetes-risk classification."""
    return {
        "LogisticRegression": lambda: LogisticRegression(max_iter=2000, class_weight="balanced"),
        "RandomForestClassifier": lambda: RandomForestClassifier(
            n_estimators=250, max_depth=10, class_weight="balanced", random_state=42, n_jobs=-1),
        "GradientBoostingClassifier": lambda: GradientBoostingClassifier(
            n_estimators=150, max_depth=3, random_state=42),
        "KNeighborsClassifier": lambda: KNeighborsClassifier(n_neighbors=15),
    }


# ---------------------------------------------------------------------------
# 3. Sleep Disorder  (multi-class: None / Insomnia / Sleep Apnea)
# ---------------------------------------------------------------------------
SLEEP_NUMERIC = ["Age", "Sleep Duration", "Quality of Sleep", "Physical Activity Level",
                  "Stress Level", "Heart Rate", "Daily Steps"]
SLEEP_CATEGORICAL = ["Gender", "BMI Category"]
SLEEP_TARGET = "Sleep Disorder"


def load_sleep_dataset():
    required = SLEEP_NUMERIC + SLEEP_CATEGORICAL + [SLEEP_TARGET]
    df, path = _find_dataset(required, ["sleep"])
    if df is None:
        raise DatasetNotFoundError(
            "Sleep Health and Lifestyle dataset not found in data/. Download it from "
            "https://www.kaggle.com/datasets/uom190346a/sleep-health-and-lifestyle-dataset "
            "and place the CSV in the data/ folder."
        )
    return df, path


def prep_sleep(df):
    df = df.copy()
    df[SLEEP_TARGET] = df[SLEEP_TARGET].fillna("None")
    return df


def sleep_candidates():
    """4 candidate algorithms for the 3-class sleep-disorder task."""
    return {
        "KNeighborsClassifier": lambda: KNeighborsClassifier(n_neighbors=9),
        "RandomForestClassifier": lambda: RandomForestClassifier(
            n_estimators=200, max_depth=8, random_state=42, n_jobs=-1),
        "LogisticRegression": lambda: LogisticRegression(max_iter=2000),
        "GradientBoostingClassifier": lambda: GradientBoostingClassifier(
            n_estimators=150, max_depth=3, random_state=42),
    }


# ---------------------------------------------------------------------------
# 4. Calories Burnt  (regression)
# ---------------------------------------------------------------------------
CALORIES_NUMERIC = ["Age", "Height", "Weight", "Duration", "Heart_Rate", "Body_Temp"]
CALORIES_CATEGORICAL = ["Gender"]
CALORIES_TARGET = "Calories"


def load_calories_dataset():
    required = CALORIES_NUMERIC + CALORIES_CATEGORICAL + [CALORIES_TARGET]
    df, path = _find_dataset(required, ["calorie"])
    if df is None:
        raise DatasetNotFoundError(
            "Calories Burnt Prediction dataset not found in data/. Download it from "
            "https://www.kaggle.com/datasets/ruchikakumbhar/calories-burnt-prediction "
            "and place the CSV in the data/ folder."
        )
    return df, path


def calories_candidates():
    """4 candidate algorithms for the calories-burnt regression task."""
    return {
        "LinearRegression": lambda: LinearRegression(),
        "KNeighborsRegressor": lambda: KNeighborsRegressor(n_neighbors=9),
        "RandomForestRegressor": lambda: RandomForestRegressor(
            n_estimators=250, max_depth=10, random_state=42, n_jobs=-1),
        "GradientBoostingRegressor": lambda: GradientBoostingRegressor(
            n_estimators=200, max_depth=3, random_state=42),
    }


# ---------------------------------------------------------------------------
# Registry -- everything evaluate_models.py needs to run the comparison,
# keyed by a short dataset name used throughout (obesity/diabetes/sleep/calories).
# ---------------------------------------------------------------------------
DATASET_REGISTRY = {
    "obesity": dict(
        loader=load_obesity_dataset, prep=None,
        numeric=OBESITY_NUMERIC, categorical=OBESITY_CATEGORICAL, target=OBESITY_TARGET,
        task="classification", candidates=obesity_candidates,
        primary_metric="f1_macro",
        metric_reason=(
            "7 obesity classes are not perfectly balanced, and every class matters "
            "equally (missing 'Obesity Type II' is just as bad as missing 'Normal "
            "Weight'). Macro-F1 averages the F1 score of EACH class equally, so it "
            "won't hide poor performance on rarer classes the way plain accuracy can."
        ),
    ),
    "diabetes": dict(
        loader=load_diabetes_dataset, prep=prep_diabetes,
        numeric=DIABETES_NUMERIC, categorical=DIABETES_CATEGORICAL, target=DIABETES_TARGET,
        task="classification", candidates=diabetes_candidates,
        primary_metric="roc_auc",
        metric_reason=(
            "Diabetes is rare in this dataset (~8-9% positive), so a model that "
            "always predicts 'no diabetes' would still score ~90% accuracy while "
            "being medically useless. ROC-AUC measures how well the model RANKS "
            "at-risk people above healthy ones regardless of class imbalance or "
            "threshold choice, which is what actually matters for a screening tool."
        ),
    ),
    "sleep": dict(
        loader=load_sleep_dataset, prep=prep_sleep,
        numeric=SLEEP_NUMERIC, categorical=SLEEP_CATEGORICAL, target=SLEEP_TARGET,
        task="classification", candidates=sleep_candidates,
        primary_metric="f1_macro",
        metric_reason=(
            "3 classes (None / Insomnia / Sleep Apnea) with 'None' as the majority "
            "class. Macro-F1 again ensures the two disorder classes -- the ones we "
            "actually care about catching -- pull equal weight against the healthy "
            "majority class, instead of being drowned out by it."
        ),
    ),
    "calories": dict(
        loader=load_calories_dataset, prep=None,
        numeric=CALORIES_NUMERIC, categorical=CALORIES_CATEGORICAL, target=CALORIES_TARGET,
        task="regression", candidates=calories_candidates,
        primary_metric="rmse",
        metric_reason=(
            "Calories burnt is a continuous value, so this is regression, not "
            "classification -- accuracy/F1 don't apply. RMSE is used as the primary "
            "metric (rather than MAE) because it penalizes large errors more heavily "
            "than small ones, which fits calorie estimation: being off by 100 kcal "
            "occasionally is fine, but a model that's wildly wrong sometimes is worse "
            "than one that's consistently a little off, even at the same average error."
        ),
    ),
}


# ---------------------------------------------------------------------------
# Saving / loading the WINNING model + its metadata (written by evaluate_models.py)
# ---------------------------------------------------------------------------
def save_best_model(dataset_key: str, pipeline, algo_name: str, metric_name: str, metric_value: float,
                     all_results: list):
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(pipeline, os.path.join(MODELS_DIR, f"kaggle_{dataset_key}_model.pkl"))
    meta = {
        "dataset": dataset_key,
        "best_algorithm": algo_name,
        "primary_metric": metric_name,
        "primary_metric_value": round(float(metric_value), 4),
        "all_candidates": all_results,
    }
    with open(os.path.join(MODELS_DIR, f"kaggle_{dataset_key}_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)


def load_best_model_meta(dataset_key: str):
    path = os.path.join(MODELS_DIR, f"kaggle_{dataset_key}_meta.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Loading trained models for inference (used by app.py)
# ---------------------------------------------------------------------------
def _load_cached(name):
    path = os.path.join(MODELS_DIR, f"kaggle_{name}_model.pkl")
    if os.path.exists(path):
        return joblib.load(path)
    return None


def predict_obesity_level(profile: dict):
    model = _load_cached("obesity")
    if model is None:
        return None
    row = pd.DataFrame([{
        "Age": profile["age"], "Height": profile["height_m"], "Weight": profile["weight_kg"],
        "FCVC": profile.get("fcvc", 2), "NCP": profile.get("ncp", 3),
        "CH2O": profile.get("ch2o", 2), "FAF": profile.get("faf", 1), "TUE": profile.get("tue", 1),
        "Gender": profile["gender"], "family_history_with_overweight": profile.get("family_history", "no"),
        "FAVC": profile.get("favc", "no"), "CAEC": profile.get("caec", "Sometimes"),
        "SMOKE": profile.get("smoke", "no"), "SCC": profile.get("scc", "no"),
        "CALC": profile.get("calc", "no"), "MTRANS": profile.get("mtrans", "Walking"),
    }])
    pred = model.predict(row)[0]
    proba = model.predict_proba(row)[0].max()
    return {"level": pred, "confidence": round(float(proba), 2)}


def predict_diabetes_risk(profile: dict):
    model = _load_cached("diabetes")
    if model is None:
        return None
    row = pd.DataFrame([{
        "age": profile["age"], "bmi": profile["bmi"],
        "HbA1c_level": profile.get("hba1c", 5.4),
        "blood_glucose_level": profile.get("blood_glucose", 100),
        "gender": profile["gender"], "hypertension": str(profile.get("hypertension", 0)),
        "heart_disease": str(profile.get("heart_disease", 0)),
        "smoking_history": profile.get("smoking_history", "never"),
    }])
    proba = model.predict_proba(row)[0]
    classes = list(model.classes_)
    idx_positive = classes.index(1) if 1 in classes else classes.index("1") if "1" in classes else -1
    p = float(proba[idx_positive]) if idx_positive != -1 else float(proba.max())
    level = "Low" if p < 0.33 else "Medium" if p < 0.66 else "High"
    return {"probability": round(p, 2), "level": level}


def predict_sleep_disorder(profile: dict):
    model = _load_cached("sleep")
    if model is None:
        return None
    row = pd.DataFrame([{
        "Age": profile["age"], "Sleep Duration": profile["sleep_hours"],
        "Quality of Sleep": profile.get("sleep_quality_score", 6),
        "Physical Activity Level": profile.get("exercise_minutes", 30),
        "Stress Level": profile.get("stress_level", 5),
        "Heart Rate": profile.get("heart_rate", 72), "Daily Steps": profile.get("steps", 6000),
        "Gender": profile["gender"], "BMI Category": profile.get("bmi_category", "Normal"),
    }])
    pred = model.predict(row)[0]
    proba = model.predict_proba(row)[0].max()
    return {"disorder": pred, "confidence": round(float(proba), 2)}


def predict_calories_burnt(profile: dict):
    model = _load_cached("calories")
    if model is None:
        return None
    row = pd.DataFrame([{
        "Age": profile["age"], "Height": profile["height_cm"], "Weight": profile["weight_kg"],
        "Duration": profile["duration_minutes"], "Heart_Rate": profile.get("heart_rate", 100),
        "Body_Temp": profile.get("body_temp", 38.5), "Gender": profile["gender"].lower(),
    }])
    return round(float(model.predict(row)[0]), 1)


def all_kaggle_models_available():
    return all(_load_cached(n) is not None for n in ["obesity", "diabetes", "sleep", "calories"])


def which_kaggle_models_available():
    return {n: _load_cached(n) is not None for n in ["obesity", "diabetes", "sleep", "calories"]}