"""Train the Milestone 2 AI Core prediction models on real public datasets.

This pipeline replaces the previously saved synthetic-data models
(ai_models/saved_models/*) with models trained on downloaded, real-world
datasets, so the Streamlit app immediately uses real-data predictions.

Data flow
---------
1. ensure_data()  -> downloads + caches the source files under
                     ``data/real/`` (skip when already present).
2. Transform layer -> each dataset is mapped onto the exact feature schema
   declared in ``ai_models/<domain>/model.py`` so the existing preprocessing
   pipelines and prediction APIs keep working unchanged.
3. Training layer -> every model is (re)trained and persisted through the
   shared ``train_and_persist`` helper (best-algorithm comparison on a 20%
   hold-out, joblib dump, version-tagged registry.json entry).

Real-data coverage
------------------
+-----------------------------+------------------------------------------------+----------+
| Model                       | Dataset                                        |   Rows   |
+-----------------------------+------------------------------------------------+----------+
| health/risk_obesity         | UCI Obesity (Palechor & de la Hoz, 2019)       |   ~2000  |
| health/risk_diabetes        | CDC BRFSS 2015 diabetes health indicators      |   70692  |
| health/risk_hypertension    | ENSANUT 2021 hypertension risk (Mexico)        |   ~4300  |
| study/performance_predictor | UCI Student Performance (maths + portuguese)   |   1044   |
| ml workout calorie model    | Hugging Face "calorie-burnt" (raw_exercise)    |   15000  |
+-----------------------------+------------------------------------------------+----------+

Feature derivations (kept so the app schema is unchanged)
----------------------------------------------------------
- ``daily_calories`` is not recorded by any of these surveys; it is estimated
  from Mifflin-St Jeor x activity factor as a plausible daily intake.
- ``activity_level`` is derived per dataset: obesity -> FAF/TUE buckets,
  BRFSS -> PhysActivity binary, ENSANUT -> total MET-minutes/week buckets.
- ``exercise_frequency`` is derived per dataset (obesity -> FAF days/week,
  BRFSS -> 0/3, ENSANUT -> weekly minutes / 150, 30-min sessions).
- Diabetes height/weight are not in BRFSS (only BMI); sex-specific reference
  heights (male 175 cm, female 162 cm) recover weight = BMI x height^2,
  preserving every real BMI value.
- BRFSS ``Age`` is a 13-level CDC age bucket -> mapped to mid-point ages.
- ENSANUT ``sexo`` 1 = male / 2 = female (verified against body measurements).
- Student data has no ``days_to_exam``; it is held constant at 60 days
  (final exam ~2 months after the mid-terms used for prior_score) so the
  model learns only from observed features.
- ``hours_logged`` uses UCI ``studytime`` weekly-hour categories (1-12 h/week),
  matching the app's 0-12 h slider. ``study_consistency`` is derived from real
  absences. ``prior_score`` = mean(G1,G2) scaled to 0-100.

Models that remain synthetic (no public labelled dataset matches their
feature schema): weight_predictor, calorie_predictor, fitness_score_predictor,
goal_achievement, finance/expense_classifier.

Usage:  python ml/train_real.py
"""

from __future__ import annotations

import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_models.common import feature_engineering as fe
from ai_models.common.algorithms import candidate_classifiers, candidate_regressors
from ai_models.common.training import train_and_persist
from ai_models.health import model as hmodel
from ai_models.health import preprocess as hprep
from ai_models.study import model as smodel
from ai_models.study import preprocess as sprep

DATA_DIR = ROOT / "data" / "real"
MODELS_DIR = ROOT / "models"

# --- Public dataset sources -------------------------------------------------
OBESITY_URL = "https://raw.githubusercontent.com/pymche/Machine-Learning-Obesity-Classification/master/ObesityDataSet_raw_and_data_sinthetic.csv"
DIABETES_URL = "https://huggingface.co/datasets/Plashkar/diabetes-predict-db/resolve/main/raw/diabetes_binary_5050split_health_indicators_BRFSS2015.csv"
HYPERTENSION_URL = "https://zenodo.org/records/18092984/files/archive.zip?download=1"
STUDENT_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00320/student.zip"

# CDC BRFSS2015 13-level age category -> approximate mid-point age.
AGE_BUCKETS = {1: 21, 2: 27, 3: 32, 4: 37, 5: 42, 6: 47, 7: 52, 8: 57, 9: 62, 10: 67, 11: 72, 12: 77, 13: 82}

# UCI studytime weekly-hours categories (1=<2h, 2=2-5h, 3=5-10h, 4=>10h).
STUDY_HOURS = {1: 1.0, 2: 3.5, 3: 7.5, 4: 12.0}

CLASSIFIER_METRICS = ("accuracy", "precision", "recall", "f1", "roc_auc")
REGRESSOR_METRICS = ("mae", "rmse", "r2")


# --- Download / cache layer ---------------------------------------------------
def _download(url: str, destination: Path, zip_member: str | None = None) -> None:
    """Download ``url`` to ``destination`` (optionally extracting one zip member)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_DIR / f"_{destination.stem}.tmp"
    print(f"  downloading {url}")
    urllib.request.urlretrieve(url, tmp)
    if zip_member:
        with zipfile.ZipFile(tmp) as zf:
            with zf.open(zip_member) as src, open(destination, "wb") as dst:
                dst.write(src.read())
        tmp.unlink(missing_ok=True)
    else:
        tmp.replace(destination)


def _ensure(url: str, destination: Path, zip_member: str | None = None) -> Path:
    if destination.exists() and destination.stat().st_size > 0:
        return destination
    _download(url, destination, zip_member)
    return destination


def ensure_data() -> dict[str, Path]:
    """Download all source datasets into data/real (cached after first run)."""
    files = {
        "obesity": _ensure(OBESITY_URL, DATA_DIR / "obesity_uci.csv"),
        "diabetes": _ensure(DIABETES_URL, DATA_DIR / "diabetes_brfss2015.csv"),
        "hypertension": _ensure(HYPERTENSION_URL, DATA_DIR / "hypertension_ensanut.csv", zip_member="Hipertension_Arterial_Mexico.csv"),
        "student_mat": _ensure(STUDENT_URL, DATA_DIR / "student-mat.csv", zip_member="student-mat.csv"),
        "student_por": _ensure(STUDENT_URL, DATA_DIR / "student-por.csv", zip_member="student-por.csv"),
    }
    return files


# --- Shared feature derivations ------------------------------------------------
def _mifflin_maintenance(gender, age, height_cm, weight_kg, activity_level) -> pd.Series:
    """Estimated daily intake (kcal): Mifflin-St Jeor BMR x activity factor."""
    bmr = fe.mifflin_st_jeor(age, gender, weight_kg, height_cm)
    multiplier = np.array([fe.activity_multiplier(str(a)) for a in activity_level])
    return pd.Series(np.round(bmr * multiplier, 0))


def _activity_from_met_minutes(minutes: np.ndarray) -> np.ndarray:
    """Weekly MET-minutes of activity -> app activity_level bucket."""
    return np.select(
        [minutes < 75, minutes < 150, minutes < 300, minutes < 420],
        ["sedentary", "light", "moderate", "active"],
        default="very_active",
    )


def _exercise_frequency_from_met(minutes: np.ndarray) -> np.ndarray:
    """Weekly MET-minutes -> exercise days/week (assuming ~30-min sessions)."""
    return np.clip(np.round(minutes / 150.0), 0, 7)


# --- Dataset -> app-schema transforms -------------------------------------------
def real_obesity_risk() -> pd.DataFrame:
    """UCI Obesity -> risk_obesity training frame (RISK_FEATURES schema)."""
    df = pd.read_csv(DATA_DIR / "obesity_uci.csv")
    df = df[df["Age"] >= 15].reset_index(drop=True)
    faf = df["FAF"].round().astype(int).clip(0, 7)
    activity = np.where(faf >= 3, "active", np.where(faf == 2, "moderate", np.where(faf == 1, "light", "sedentary")))
    gender = df["Gender"].str.lower()
    height_cm = df["Height"] * 100
    weight_kg = df["Weight"]
    age = df["Age"].astype(int)
    frame = pd.DataFrame(
        {
            "age": age,
            "gender": gender,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "activity_level": activity,
            "daily_calories": _mifflin_maintenance(gender, age, height_cm, weight_kg, activity),
            "exercise_frequency": faf,
        }
    )
    frame["risk_obesity"] = df["NObeyesdad"].isin(["Obesity_Type_I", "Obesity_Type_II", "Obesity_Type_III"]).astype(int)
    return frame


def real_diabetes_risk() -> pd.DataFrame:
    """CDC BRFSS 2015 diabetes indicators -> risk_diabetes training frame."""
    df = pd.read_csv(DATA_DIR / "diabetes_brfss2015.csv")
    gender = np.where(df["Sex"] == 1, "male", "female")
    age = df["Age"].map(AGE_BUCKETS)
    height_cm = np.where(df["Sex"] == 1, 175.0, 162.0)
    weight_kg = df["BMI"] * (height_cm / 100.0) ** 2
    activity = np.where(df["PhysActivity"] == 1, "active", "sedentary")
    frame = pd.DataFrame(
        {
            "age": age,
            "gender": gender,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "activity_level": activity,
            "daily_calories": _mifflin_maintenance(gender, age, height_cm, weight_kg, activity),
            "exercise_frequency": np.where(df["PhysActivity"] == 1, 3, 0),
        }
    )
    frame["risk_diabetes"] = df["Diabetes_binary"].astype(int)
    return frame


def real_hypertension_risk() -> pd.DataFrame:
    """ENSANUT 2021 hypertension risk -> risk_hypertension training frame."""
    df = pd.read_csv(DATA_DIR / "hypertension_ensanut.csv")
    df = df[(df["edad"] >= 18) & (df["estatura"] > 100) & (df["peso"] > 30)].reset_index(drop=True)
    gender = np.where(df["sexo"] == 1, "male", "female")
    age = df["edad"].astype(int)
    height_cm = df["estatura"].astype(float)
    weight_kg = df["peso"].astype(float)
    minutes = df["actividad_total"].to_numpy(dtype=float)
    activity = _activity_from_met_minutes(minutes)
    frame = pd.DataFrame(
        {
            "age": age,
            "gender": gender,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "activity_level": activity,
            "daily_calories": _mifflin_maintenance(gender, age, height_cm, weight_kg, activity),
            "exercise_frequency": _exercise_frequency_from_met(minutes),
        }
    )
    frame["risk_hypertension"] = df["riesgo_hipertension"].astype(int)
    return frame


def real_student_performance() -> pd.DataFrame:
    """UCI Student Performance (math + portuguese) -> performance training frame."""
    mat = pd.read_csv(DATA_DIR / "student-mat.csv", sep=";")
    mat["subject"] = "Maths"
    por = pd.read_csv(DATA_DIR / "student-por.csv", sep=";")
    por["subject"] = "Portuguese"
    df = pd.concat([mat, por], ignore_index=True)
    df = df.reset_index(drop=True)
    for col in ("G1", "G2", "G3", "studytime", "absences"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["G1", "G2", "G3"])
    hours_logged = df["studytime"].map(STUDY_HOURS).fillna(1.0)
    prior_score = ((df["G1"] + df["G2"]) / 2.0) * 5.0
    study_consistency = (1.0 - df["absences"] / 30.0).clip(0, 1).round(3)
    return pd.DataFrame(
        {
            "subject": df["subject"].values,
            "hours_logged": hours_logged.round(2).values,
            "days_to_exam": np.full(len(df), 60, dtype=int),
            "study_consistency": study_consistency.values,
            "prior_score": prior_score.round(1).values,
            "performance_score": (df["G3"] * 5.0).round(1).values,
        }
    )


# --- Training layer -------------------------------------------------------------
def train_risk_models_real() -> dict:
    """Retrain the three health-risk classifiers on real data."""
    sources = {
        "risk_obesity": ("UCI Obesity dataset", real_obesity_risk, hmodel.RISK_LABELS["risk_obesity"]),
        "risk_diabetes": ("CDC BRFSS 2015 diabetes indicators", real_diabetes_risk, hmodel.RISK_LABELS["risk_diabetes"]),
        "risk_hypertension": ("ENSANUT 2021 hypertension risk (Mexico)", real_hypertension_risk, hmodel.RISK_LABELS["risk_hypertension"]),
    }
    summary = {}
    for name, (source, builder, display) in sources.items():
        data = builder()
        meta = train_and_persist(
            "health", name, hmodel.RISK_FEATURES, name, data,
            hprep.build_risk_pipeline, candidate_classifiers(),
            task="classification", display_name=f"{display} Risk",
        )
        summary[name] = {"source": source, "records": meta["records"], "algorithm": meta["algorithm"], "metrics": meta["metrics"]}
    return summary


def train_performance_model_real() -> dict:
    """Retrain the study performance regressor on real student records."""
    data = real_student_performance()
    meta = train_and_persist(
        "study", "performance_predictor", smodel.PERFORMANCE_FEATURES, smodel.PERFORMANCE_TARGET,
        data, sprep.build_performance_pipeline, candidate_regressors(), display_name="Academic Performance Prediction",
    )
    return {"source": "UCI Student Performance (maths + portuguese)", "records": meta["records"], "algorithm": meta["algorithm"], "metrics": meta["metrics"]}


def train_workout_calorie_model_real() -> dict:
    """Retrain the workout calorie-expenditure model on the cached HF dataset."""
    from ml.trainer_hf import train_calorie_model

    metrics = train_calorie_model(MODELS_DIR / "hf_calorie_predictor.joblib", ROOT / "data")
    return {"source": "Hugging Face calorie-burnt (mnemoraorg/calorie-burnt-15k)", "records": metrics.get("records", 0), "algorithm": "Random Forest", "metrics": metrics}


# --- Reporting -------------------------------------------------------------------
def _fmt(metrics: dict, keys) -> str:
    return ", ".join(f"{k}={metrics.get(k, 0.0):.3f}" for k in keys if k in metrics)


def main() -> None:
    print("=== Real-data training for Milestone 2 AI Core ===")
    print("Ensuring datasets (cached in data/real/):")
    ensure_data()

    print("\nTraining health risk models (real data)...")
    risks = train_risk_models_real()

    print("Training study performance model (real data)...")
    performance = train_performance_model_real()

    print("Training workout calorie model (real data)...")
    workout = train_workout_calorie_model_real()

    print("\n=== Training summary ===")
    print(f"{'Model':<24}{'Source':<40}{'Rows':>7}  {'Best algorithm':<20}  Metrics")
    print("-" * 130)
    for name, info in risks.items():
        print(f"{name:<24}{info['source']:<40}{info['records']:>7}  {info['algorithm']:<20}  {_fmt(info['metrics'], CLASSIFIER_METRICS)}")
    print(f"{'performance_predictor':<24}{performance['source']:<40}{performance['records']:>7}  {performance['algorithm']:<20}  {_fmt(performance['metrics'], REGRESSOR_METRICS)}")
    print(f"{'workout calorie (ml)':<24}{workout['source']:<40}{workout['records']:>7}  {workout['algorithm']:<20}  {_fmt(workout['metrics'], ('mae', 'r2'))}")

    print(
        "\nModels still synthetic (no public labelled dataset matches their feature "
        "schema):\n  weight_predictor, calorie_predictor, fitness_score_predictor, "
        "goal_achievement, finance/expense_classifier.\n"
    )


if __name__ == "__main__":
    main()
