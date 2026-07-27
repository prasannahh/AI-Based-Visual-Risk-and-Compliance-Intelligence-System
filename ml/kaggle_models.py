"""
ml/kaggle_models.py
--------------------
Trains four DIFFERENT machine learning models on four DIFFERENT real Kaggle
datasets, replacing/augmenting the synthetic-data models in weight_predictor.py
and risk_classifier.py with models trained on real-world data.

    Dataset                                   | Algorithm              | Task
    -------------------------------------------|-------------------------|-------------------------------
    Obesity Levels (fatemehmehrparvar)         | RandomForestClassifier  | Multi-class obesity level (7 classes)
    Diabetes Prediction (iammustafatz)          | LogisticRegression      | Binary diabetes risk
    Sleep Health & Lifestyle (uom190346a)       | KNeighborsClassifier    | Sleep disorder (None/Insomnia/Apnea)
    Calories Burnt Prediction (ruchikakumbhar)  | GradientBoostingRegressor | Calories burnt during exercise

Where to put the downloaded CSV files: see data/README.md. This module reads
whatever file it finds in data/ that matches expected column names -- it
does NOT hardcode an exact Kaggle filename, so you can keep the name Kaggle
gave you. Both .csv and .xlsx are supported.
"""

import os
import glob
import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
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

    # Prefer filename hints first (faster + avoids accidental column collisions)
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


def _build_pipeline(numeric_cols, categorical_cols, estimator):
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
# 1. Obesity Level Classifier  (RandomForestClassifier, multi-class)
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


def build_obesity_pipeline():
    return _build_pipeline(
        OBESITY_NUMERIC, OBESITY_CATEGORICAL,
        RandomForestClassifier(n_estimators=250, max_depth=12, random_state=42, n_jobs=-1),
    )


def train_obesity_model():
    df, _ = load_obesity_dataset()
    X = df[OBESITY_NUMERIC + OBESITY_CATEGORICAL]
    y = df[OBESITY_TARGET]
    pipe = build_obesity_pipeline()
    pipe.fit(X, y)
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(pipe, os.path.join(MODELS_DIR, "kaggle_obesity_model.pkl"))
    return pipe


# ---------------------------------------------------------------------------
# 2. Diabetes Risk Classifier  (LogisticRegression, binary)
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


def build_diabetes_pipeline():
    return _build_pipeline(
        DIABETES_NUMERIC, DIABETES_CATEGORICAL,
        LogisticRegression(max_iter=1000),
    )


def train_diabetes_model():
    df, _ = load_diabetes_dataset()
    df = df.copy()
    df["hypertension"] = df["hypertension"].astype(str)
    df["heart_disease"] = df["heart_disease"].astype(str)
    X = df[DIABETES_NUMERIC + DIABETES_CATEGORICAL]
    y = df[DIABETES_TARGET]
    pipe = build_diabetes_pipeline()
    pipe.fit(X, y)
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(pipe, os.path.join(MODELS_DIR, "kaggle_diabetes_model.pkl"))
    return pipe


# ---------------------------------------------------------------------------
# 3. Sleep Disorder Classifier  (KNeighborsClassifier, multi-class)
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


def build_sleep_pipeline():
    return _build_pipeline(
        SLEEP_NUMERIC, SLEEP_CATEGORICAL,
        KNeighborsClassifier(n_neighbors=9),
    )


def train_sleep_model():
    df, _ = load_sleep_dataset()
    df = df.copy()
    df[SLEEP_TARGET] = df[SLEEP_TARGET].fillna("None")
    X = df[SLEEP_NUMERIC + SLEEP_CATEGORICAL]
    y = df[SLEEP_TARGET]
    pipe = build_sleep_pipeline()
    pipe.fit(X, y)
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(pipe, os.path.join(MODELS_DIR, "kaggle_sleep_model.pkl"))
    return pipe


# ---------------------------------------------------------------------------
# 4. Calories Burnt Regressor  (GradientBoostingRegressor)
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


def build_calories_pipeline():
    return _build_pipeline(
        CALORIES_NUMERIC, CALORIES_CATEGORICAL,
        GradientBoostingRegressor(n_estimators=200, max_depth=3, random_state=42),
    )


def train_calories_model():
    df, _ = load_calories_dataset()
    X = df[CALORIES_NUMERIC + CALORIES_CATEGORICAL]
    y = df[CALORIES_TARGET]
    pipe = build_calories_pipeline()
    pipe.fit(X, y)
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(pipe, os.path.join(MODELS_DIR, "kaggle_calories_model.pkl"))
    return pipe


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
