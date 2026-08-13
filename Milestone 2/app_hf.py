"""Hugging Face data-backed Milestone 2 application."""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

from ml.health_models import calculate_bmi, calorie_target, fitness_score
from ml.trainer_hf import FEATURES, DATASET_ID, train_calorie_model

ROOT = Path(__file__).parent
MODEL_PATH = ROOT / "models" / "hf_calorie_predictor.joblib"

st.set_page_config(page_title="Health Twin | Hugging Face Model", page_icon="🩺", layout="wide")
st.title("🩺 Health & Fitness Digital Twin")
st.caption("Milestone 2 — Hugging Face-trained calorie model")


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


with st.sidebar:
    st.header("Your profile")
    age = st.number_input("Age", 18, 100, 25)
    gender = st.selectbox("Gender", ["female", "male"])
    height = st.number_input("Height (cm)", 120.0, 230.0, 170.0, 0.1)
    weight = st.number_input("Weight (kg)", 30.0, 250.0, 70.0, 0.1)
    activity = st.selectbox("Activity level", ["sedentary", "light", "moderate", "active", "very_active"], index=2)
    goal = st.selectbox("Goal", ["maintain", "lose", "gain"])

bmi = calculate_bmi(weight, height)
target = calorie_target(age, gender, weight, height, activity, goal)
a, b, c = st.columns(3)
a.metric("BMI", bmi.value, bmi.category)
b.metric("Daily calorie target", f"{target.target_kcal:,} kcal")
c.metric("Estimated BMR", f"{target.bmr_kcal:,} kcal")

st.subheader("Exercise calorie expenditure")
d, e, f, g = st.columns(4)
duration = d.number_input("Duration (minutes)", 1, 300, 30)
heart_rate = e.number_input("Average heart rate (bpm)", 50, 220, 110)
body_temp = f.number_input("Body temperature (°C)", 35.0, 43.0, 40.0, 0.1)
steps = g.number_input("Daily steps", 0, 50000, 7000, 100)
score = fitness_score(steps, duration, 7.5, 2.2)
st.progress(int(score), text=f"Fitness score: {score:.0f}/100")

if MODEL_PATH.exists():
    features = pd.DataFrame([[gender, age, height, weight, duration, heart_rate, body_temp]], columns=FEATURES)
    estimate = max(0, float(load_model().predict(features)[0]))
    st.metric("Predicted workout calories burned", f"{estimate:.0f} kcal")
else:
    st.warning("Train the model below before requesting an estimate.")

st.divider()
st.subheader("Model training and validation")
st.write(f"Training source: Hugging Face `{DATASET_ID}`. The two public CSV files are cached under `data/` after the first run.")
if st.button("Download dataset and train model", type="primary"):
    try:
        with st.spinner("Downloading public data and training model..."):
            metrics = train_calorie_model(MODEL_PATH, ROOT / "data")
        load_model.clear()
        st.success(f"Trained on {metrics['records']:,} records. Hold-out MAE: {metrics['mae']:.2f} kcal; R²: {metrics['r2']:.3f}.")
    except Exception as error:
        st.error(f"Training failed: {error}")

st.caption("For educational use only; these are estimates, not medical advice or clinical predictions.")
