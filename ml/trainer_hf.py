"""Download, train, and validate against a public Hugging Face dataset."""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

DATASET_ID = "mnemoraorg/calorie-burnt-15k"
DATASET_URL = f"https://huggingface.co/datasets/{DATASET_ID}/resolve/main"
FEATURES = ["Gender", "Age", "Height", "Weight", "Duration", "Heart_Rate", "Body_Temp"]


def load_hugging_face_data(data_dir: Path) -> pd.DataFrame:
    """Cache public source files locally, then join calorie labels by user ID."""
    data_dir.mkdir(parents=True, exist_ok=True)
    exercise_file = data_dir / "raw_exercise.csv"
    calorie_file = data_dir / "raw_calories.csv"
    for filename, destination in (("raw_exercise.csv", exercise_file), ("raw_calories.csv", calorie_file)):
        if not destination.exists():
            pd.read_csv(f"{DATASET_URL}/{filename}").to_csv(destination, index=False)
    merged = pd.read_csv(exercise_file).merge(pd.read_csv(calorie_file), on="User_ID", validate="one_to_one")
    expected = set(FEATURES + ["Calories"])
    missing = expected - set(merged.columns)
    if missing:
        raise ValueError(f"Unexpected dataset schema; missing: {sorted(missing)}")
    return merged.dropna(subset=FEATURES + ["Calories"])


def train_calorie_model(model_path: Path, data_dir: Path) -> dict[str, float]:
    """Train an 80/20 hold-out validated calorie-expenditure estimator."""
    data = load_hugging_face_data(data_dir)
    x_train, x_test, y_train, y_test = train_test_split(data[FEATURES], data["Calories"], test_size=0.2, random_state=42)
    preprocess = ColumnTransformer([("gender", OneHotEncoder(handle_unknown="ignore"), ["Gender"])], remainder="passthrough")
    pipeline = Pipeline([("preprocess", preprocess), ("model", RandomForestRegressor(n_estimators=250, min_samples_leaf=2, random_state=42, n_jobs=-1))])
    pipeline.fit(x_train, y_train)
    predicted = pipeline.predict(x_test)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    return {"records": int(len(data)), "mae": float(mean_absolute_error(y_test, predicted)), "r2": float(r2_score(y_test, predicted))}
