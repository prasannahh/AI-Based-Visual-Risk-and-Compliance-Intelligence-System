"""
ml/risk_classifier.py
----------------------
Trains three scikit-learn RandomForestClassifiers (obesity, diabetes,
hypertension) on a synthetic dataset built from established clinical risk
factors (BMI thresholds, age, activity level, sleep, blood pressure,
blood sugar, family/medical history flags). As with weight_predictor.py,
this is a standard "bootstrap with rule-informed synthetic data, refine
with real data later" approach for a project of this scope.

IMPORTANT: This is an educational/demo risk indicator, NOT a medical
diagnosis tool. The UI must always say so.
"""

import os
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
RISK_LEVELS = ["Low", "Medium", "High"]


def _bucket(prob):
    if prob < 0.33:
        return "Low"
    if prob < 0.66:
        return "Medium"
    return "High"


def _generate_dataset(n=8000, seed=1):
    rng = np.random.default_rng(seed)
    bmi = rng.uniform(15, 45, n)
    age = rng.integers(16, 75, n)
    steps = rng.integers(500, 18000, n)
    sleep = rng.uniform(4, 9, n)
    sys_bp = rng.integers(90, 180, n)
    dia_bp = rng.integers(60, 110, n)
    sugar = rng.uniform(70, 220, n)
    has_history = rng.integers(0, 2, n)

    X = np.column_stack([bmi, age, steps, sleep, sys_bp, dia_bp, sugar, has_history])

    def sigmoid(x):
        return 1 / (1 + np.exp(-x))

    obesity_p = sigmoid((bmi - 27) * 0.5 - (steps - 8000) / 8000 + has_history * 0.3)
    diabetes_p = sigmoid((sugar - 125) * 0.06 + (bmi - 27) * 0.08 + (age - 45) * 0.02 + has_history * 0.4)
    hyper_p = sigmoid((sys_bp - 130) * 0.06 + (dia_bp - 85) * 0.05 + (age - 45) * 0.02 + (bmi - 27) * 0.03)

    obesity_y = (rng.uniform(0, 1, n) < obesity_p).astype(int)
    diabetes_y = (rng.uniform(0, 1, n) < diabetes_p).astype(int)
    hyper_y = (rng.uniform(0, 1, n) < hyper_p).astype(int)

    return X, obesity_y, diabetes_y, hyper_y


def train_and_save():
    X, y_ob, y_db, y_hy = _generate_dataset()
    os.makedirs(MODELS_DIR, exist_ok=True)

    models = {}
    for name, y in [("obesity", y_ob), ("diabetes", y_db), ("hypertension", y_hy)]:
        clf = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42, n_jobs=-1)
        clf.fit(X, y)
        joblib.dump(clf, os.path.join(MODELS_DIR, f"risk_{name}.pkl"))
        models[name] = clf
    return models


def load_models():
    paths = {name: os.path.join(MODELS_DIR, f"risk_{name}.pkl")
              for name in ["obesity", "diabetes", "hypertension"]}
    if not all(os.path.exists(p) for p in paths.values()):
        return train_and_save()
    return {name: joblib.load(p) for name, p in paths.items()}


def predict_risks(
    bmi: float,
    age: int,
    avg_steps: float,
    avg_sleep_hours: float,
    systolic_bp: int = 120,
    diastolic_bp: int = 80,
    blood_sugar: float = 95,
    has_medical_history: bool = False,
) -> dict:
    models = load_models()
    X = np.array([[bmi, age, avg_steps, avg_sleep_hours, systolic_bp,
                    diastolic_bp, blood_sugar, int(has_medical_history)]])

    results = {}
    for name, clf in models.items():
        prob = clf.predict_proba(X)[0][1]
        results[name] = {"probability": round(float(prob), 2), "level": _bucket(prob)}
    return results
