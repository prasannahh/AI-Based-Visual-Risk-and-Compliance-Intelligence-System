"""Production entry point for the public Hugging Face-trained demo."""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

from ml.health_models import calculate_bmi, calorie_target, fitness_score
from ml.trainer_hf import DATASET_ID, FEATURES, train_calorie_model

ROOT = Path(__file__).parent
MODEL_PATH = ROOT / "models" / "hf_calorie_predictor.joblib"

st.set_page_config(page_title="Health Twin | AI Core", page_icon="🩺", layout="wide")
st.title("🩺 Health & Fitness Digital Twin")
st.caption("Milestone 2 — AI Core trained with Hugging Face data")


@st.cache_resource
def load_model():
    model = joblib.load(MODEL_PATH)
    model.set_params(model__n_jobs=1)  # reliable on constrained Windows machines
    return model


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
col1, col2, col3 = st.columns(3)
col1.metric("BMI", bmi.value, bmi.category)
col2.metric("Daily calorie target", f"{target.target_kcal:,} kcal")
col3.metric("Estimated BMR", f"{target.bmr_kcal:,} kcal")

st.subheader("Exercise calorie expenditure")
a, b, c, d = st.columns(4)
duration = a.number_input("Duration (minutes)", 1, 300, 30)
heart_rate = b.number_input("Average heart rate (bpm)", 50, 220, 110)
body_temp = c.number_input("Body temperature (°C)", 35.0, 43.0, 40.0, 0.1)
steps = d.number_input("Daily steps", 0, 50000, 7000, 100)
score = fitness_score(steps, duration, 7.5, 2.2)
st.progress(int(score), text=f"Fitness score: {score:.0f}/100")

if MODEL_PATH.exists():
    request = pd.DataFrame([[gender, age, height, weight, duration, heart_rate, body_temp]], columns=FEATURES)
    st.metric("Predicted workout calories burned", f"{max(0, float(load_model().predict(request)[0])):.0f} kcal")
else:
    st.warning("Train the model below before requesting an estimate.")

st.divider()
st.subheader("Train and validate")
st.write(f"Source dataset: Hugging Face `{DATASET_ID}` (15,000 exercise records with calorie labels).")
if st.button("Download dataset and train model", type="primary"):
    try:
        with st.spinner("Downloading public data and training..."):
            metrics = train_calorie_model(MODEL_PATH, ROOT / "data")
        load_model.clear()
        st.success(f"Trained on {metrics['records']:,} records. Hold-out MAE: {metrics['mae']:.2f} kcal; R²: {metrics['r2']:.3f}.")
    except Exception as error:
        st.error(f"Training failed: {error}")

st.caption("Educational estimates only — not clinical advice or a diagnostic model.")
