"""
ml/train_kaggle_models.py
--------------------------
Run this AFTER placing the 4 Kaggle CSV files in the data/ folder:

    python -m ml.train_kaggle_models

Trains and caches all 4 real-data models to ml/models/kaggle_*.pkl.
Any dataset that isn't found is skipped with a clear message (the app
falls back to the built-in synthetic models for whichever ones are missing).
"""

from ml.kaggle_models import (
    train_obesity_model, train_diabetes_model, train_sleep_model, train_calories_model,
    DatasetNotFoundError,
)

TRAINERS = [
    ("Obesity Level Classifier (RandomForestClassifier)", train_obesity_model),
    ("Diabetes Risk Classifier (LogisticRegression)", train_diabetes_model),
    ("Sleep Disorder Classifier (KNeighborsClassifier)", train_sleep_model),
    ("Calories Burnt Regressor (GradientBoostingRegressor)", train_calories_model),
]

if __name__ == "__main__":
    trained, skipped = [], []
    for label, fn in TRAINERS:
        print(f"\n--- {label} ---")
        try:
            fn()
            print("✅ Trained and saved.")
            trained.append(label)
        except DatasetNotFoundError as e:
            print(f"⚠️  Skipped: {e}")
            skipped.append(label)

    print("\n================ SUMMARY ================")
    print(f"Trained: {len(trained)}/4")
    for t in trained:
        print(f"  ✅ {t}")
    for s in skipped:
        print(f"  ⚠️  {s}")
    if skipped:
        print("\nSee data/README.md for download links and where to place each file.")
