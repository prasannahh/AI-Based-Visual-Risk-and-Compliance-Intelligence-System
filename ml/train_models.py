"""
ml/train_models.py
-------------------
Run this once with:

    python -m ml.train_models

to pre-train and cache all ML models into ml/models/*.pkl so the Streamlit
app starts instantly. If you skip this step, the app will simply train the
models automatically the first time they're needed (a few seconds' delay).
"""

from ml import weight_predictor, risk_classifier

if __name__ == "__main__":
    print("Training weight predictor...")
    weight_predictor.train_and_save()
    print("Training risk classifiers (obesity, diabetes, hypertension)...")
    risk_classifier.train_and_save()
    print("✅ All models trained and saved to ml/models/")
