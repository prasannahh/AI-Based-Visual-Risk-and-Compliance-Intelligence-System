"""Streamlit interface for the Milestone 2 AI core."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ml.health_models import calculate_bmi, calorie_target, fitness_score
from ml.trainer import train_weight_model
from ml.weight_predictor import WeightPredictor


ROOT = Path(__file__).parent
MODEL_PATH = ROOT / "models" / "weight_predictor.joblib"

st.set_page_config(page_title="Health Twin | AI Core", page_icon="🩺", layout="wide")
st.title("🩺 Health & Fitness Digital Twin")
st.caption("Milestone 2 — AI Core Layer")


@st.cache_resource
def load_predictor() -> WeightPredictor:
    if not MODEL_PATH.exists():
        train_weight_model(model_path=MODEL_PATH)
    return WeightPredictor.load(MODEL_PATH)


with st.sidebar:
    st.header("Your profile")
    age = st.number_input("Age", 14, 100, 25)
    gender = st.selectbox("Gender", ["female", "male"])
    height_cm = st.number_input("Height (cm)", 120.0, 230.0, 170.0, 0.1)
    weight_kg = st.number_input("Current weight (kg)", 30.0, 250.0, 70.0, 0.1)
    activity = st.selectbox("Activity level", ["sedentary", "light", "moderate", "active", "very_active"], index=2)
    goal = st.selectbox("Goal", ["maintain", "lose", "gain"])

bmi = calculate_bmi(weight_kg, height_cm)
calories = calorie_target(age, gender, weight_kg, height_cm, activity, goal)

tab1, tab2, tab3 = st.tabs(["Health overview", "Weight forecast", "Model training"])

with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("BMI", f"{bmi.value:.1f}", bmi.category)
    c2.metric("Daily calorie target", f"{calories.target_kcal:,} kcal", f"BMR: {calories.bmr_kcal:,} kcal")
    c3.metric("Fitness score", f"{fitness_score(steps=7000, exercise_minutes=30, sleep_hours=7, water_litres=2.2):.0f}/100")
    st.info("Calorie targets are estimates for healthy adults. They are not medical advice; consult a qualified clinician for medical or eating-disorder concerns.")
    st.subheader("Today’s habits")
    h1, h2, h3, h4 = st.columns(4)
    steps = h1.number_input("Steps", 0, 50000, 7000, 100)
    exercise = h2.number_input("Exercise (minutes)", 0, 600, 30, 5)
    sleep = h3.number_input("Sleep (hours)", 0.0, 24.0, 7.0, 0.1)
    water = h4.number_input("Water (litres)", 0.0, 15.0, 2.2, 0.1)
    score = fitness_score(steps, exercise, sleep, water)
    st.progress(int(score), text=f"Fitness score: {score:.0f}/100")

with tab2:
    st.subheader("30-day weight forecast")
    daily_calories = st.number_input("Average daily calorie intake", 800, 7000, calories.target_kcal, 50)
    if st.button("Generate forecast", type="primary"):
        predictor = load_predictor()
        forecast = predictor.forecast(
            age=age, gender=gender, height_cm=height_cm, current_weight_kg=weight_kg,
            activity_level=activity, daily_calories=daily_calories, days=30,
        )
        st.line_chart(forecast.set_index("day")["predicted_weight_kg"])
        st.dataframe(forecast, hide_index=True, use_container_width=True)

with tab3:
    st.subheader("Train and validate the baseline model")
    st.write("The included model is trained on a reproducible synthetic dataset so the demo works immediately. Replace it with consented, representative data before any real-world use.")
    if st.button("Retrain model"):
        metrics = train_weight_model(model_path=MODEL_PATH)
        load_predictor.clear()
        st.success(f"Model trained. Validation MAE: {metrics['mae']:.2f} kg; R²: {metrics['r2']:.2f}")
    if MODEL_PATH.exists():
        st.caption(f"Saved model: {MODEL_PATH.name}")
