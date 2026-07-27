"""
ml/evaluate_models.py
-----------------------
Evaluates all 4 real-data ML models using:
  (a) an 80:20 train/test split, and
  (b) 5-fold cross-validation on the full dataset,

then prints a report to the console AND saves it to
ml/evaluation_report.txt.

Run with:
    python -m ml.evaluate_models

Requires the Kaggle datasets to already be in data/ (see data/README.md).
Datasets that are missing are skipped with a clear message.
"""

import io
import contextlib

import numpy as np
from sklearn.model_selection import train_test_split, cross_validate, StratifiedKFold, KFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score,
)

from ml.kaggle_models import (
    load_obesity_dataset, build_obesity_pipeline, OBESITY_NUMERIC, OBESITY_CATEGORICAL, OBESITY_TARGET,
    load_diabetes_dataset, build_diabetes_pipeline, DIABETES_NUMERIC, DIABETES_CATEGORICAL, DIABETES_TARGET,
    load_sleep_dataset, build_sleep_pipeline, SLEEP_NUMERIC, SLEEP_CATEGORICAL, SLEEP_TARGET,
    load_calories_dataset, build_calories_pipeline, CALORIES_NUMERIC, CALORIES_CATEGORICAL, CALORIES_TARGET,
    DatasetNotFoundError,
)


def _evaluate_classifier(name, load_fn, build_fn, numeric_cols, categorical_cols, target_col, extra_prep=None):
    out = [f"\n{'='*70}\n{name}\n{'='*70}"]
    df, path = load_fn()
    if extra_prep:
        df = extra_prep(df)
    out.append(f"Dataset file: {path}")
    out.append(f"Rows: {len(df)}   Columns used: {len(numeric_cols) + len(categorical_cols)}")

    X = df[numeric_cols + categorical_cols]
    y = df[target_col]

    # --- 80:20 split ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if y.nunique() < 20 else None
    )
    model = build_fn()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    avg = "binary" if y.nunique() == 2 else "weighted"
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average=avg, zero_division=0, pos_label=y.unique()[0] if avg == "binary" else None) \
        if avg == "binary" else precision_score(y_test, y_pred, average=avg, zero_division=0)
    rec = recall_score(y_test, y_pred, average=avg, zero_division=0) if avg != "binary" else \
        recall_score(y_test, y_pred, average=avg, zero_division=0, pos_label=y.unique()[0])
    f1 = f1_score(y_test, y_pred, average=avg, zero_division=0) if avg != "binary" else \
        f1_score(y_test, y_pred, average=avg, zero_division=0, pos_label=y.unique()[0])

    out.append("\n[80:20 Train/Test Split]")
    out.append(f"  Train size: {len(X_train)}   Test size: {len(X_test)}")
    out.append(f"  Accuracy : {acc:.4f}")
    out.append(f"  Precision: {prec:.4f}  (average='{avg}')")
    out.append(f"  Recall   : {rec:.4f}")
    out.append(f"  F1-score : {f1:.4f}")

    # --- 5-fold CV on the FULL dataset ---
    cv_model = build_fn()
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_validate(
        cv_model, X, y, cv=skf,
        scoring=["accuracy", "f1_weighted", "precision_weighted", "recall_weighted"],
    )
    out.append("\n[5-Fold Cross-Validation, full dataset]")
    out.append(f"  Accuracy : {scores['test_accuracy'].mean():.4f} (+/- {scores['test_accuracy'].std():.4f})")
    out.append(f"  F1       : {scores['test_f1_weighted'].mean():.4f} (+/- {scores['test_f1_weighted'].std():.4f})")
    out.append(f"  Precision: {scores['test_precision_weighted'].mean():.4f}")
    out.append(f"  Recall   : {scores['test_recall_weighted'].mean():.4f}")
    out.append(f"  Per-fold accuracy: {np.round(scores['test_accuracy'], 4).tolist()}")

    return "\n".join(out)


def _evaluate_regressor(name, load_fn, build_fn, numeric_cols, categorical_cols, target_col):
    out = [f"\n{'='*70}\n{name}\n{'='*70}"]
    df, path = load_fn()
    out.append(f"Dataset file: {path}")
    out.append(f"Rows: {len(df)}   Columns used: {len(numeric_cols) + len(categorical_cols)}")

    X = df[numeric_cols + categorical_cols]
    y = df[target_col]

    # --- 80:20 split ---
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = build_fn()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    out.append("\n[80:20 Train/Test Split]")
    out.append(f"  Train size: {len(X_train)}   Test size: {len(X_test)}")
    out.append(f"  MAE  : {mae:.3f}")
    out.append(f"  RMSE : {rmse:.3f}")
    out.append(f"  R^2  : {r2:.4f}")

    # --- 5-fold CV ---
    cv_model = build_fn()
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_validate(
        cv_model, X, y, cv=kf,
        scoring=["neg_mean_absolute_error", "neg_root_mean_squared_error", "r2"],
    )
    out.append("\n[5-Fold Cross-Validation, full dataset]")
    out.append(f"  MAE  : {-scores['test_neg_mean_absolute_error'].mean():.3f}")
    out.append(f"  RMSE : {-scores['test_neg_root_mean_squared_error'].mean():.3f}")
    out.append(f"  R^2  : {scores['test_r2'].mean():.4f} (+/- {scores['test_r2'].std():.4f})")
    out.append(f"  Per-fold R^2: {np.round(scores['test_r2'], 4).tolist()}")

    return "\n".join(out)


def _prep_diabetes(df):
    df = df.copy()
    df["hypertension"] = df["hypertension"].astype(str)
    df["heart_disease"] = df["heart_disease"].astype(str)
    return df


def _prep_sleep(df):
    df = df.copy()
    df[SLEEP_TARGET] = df[SLEEP_TARGET].fillna("None")
    return df


def main():
    report_sections = []
    report_sections.append(
        "HEALTH & FITNESS DIGITAL TWIN -- ML MODEL EVALUATION REPORT\n"
        "Evaluation method: 80:20 train/test split AND 5-fold cross-validation\n"
    )

    jobs = [
        ("1. Obesity Level Classifier -- RandomForestClassifier\n"
         "   Dataset: Obesity Levels (Kaggle: fatemehmehrparvar/obesity-levels)",
         load_obesity_dataset, build_obesity_pipeline, OBESITY_NUMERIC, OBESITY_CATEGORICAL, OBESITY_TARGET, None),
        ("2. Diabetes Risk Classifier -- LogisticRegression\n"
         "   Dataset: Diabetes Prediction (Kaggle: iammustafatz/diabetes-prediction-dataset)",
         load_diabetes_dataset, build_diabetes_pipeline, DIABETES_NUMERIC, DIABETES_CATEGORICAL, DIABETES_TARGET, _prep_diabetes),
        ("3. Sleep Disorder Classifier -- KNeighborsClassifier\n"
         "   Dataset: Sleep Health & Lifestyle (Kaggle: uom190346a/sleep-health-and-lifestyle-dataset)",
         load_sleep_dataset, build_sleep_pipeline, SLEEP_NUMERIC, SLEEP_CATEGORICAL, SLEEP_TARGET, _prep_sleep),
    ]

    for name, load_fn, build_fn, num_cols, cat_cols, target, prep in jobs:
        try:
            print(f"Evaluating: {name.splitlines()[0]}...")
            result = _evaluate_classifier(name, load_fn, build_fn, num_cols, cat_cols, target, prep)
            report_sections.append(result)
        except DatasetNotFoundError as e:
            report_sections.append(f"\n{'='*70}\n{name}\n{'='*70}\n⚠️  SKIPPED: {e}")

    try:
        print("Evaluating: 4. Calories Burnt Regressor...")
        result = _evaluate_regressor(
            "4. Calories Burnt Regressor -- GradientBoostingRegressor\n"
            "   Dataset: Calories Burnt Prediction (Kaggle: ruchikakumbhar/calories-burnt-prediction)",
            load_calories_dataset, build_calories_pipeline, CALORIES_NUMERIC, CALORIES_CATEGORICAL, CALORIES_TARGET,
        )
        report_sections.append(result)
    except DatasetNotFoundError as e:
        report_sections.append(f"\n{'='*70}\n4. Calories Burnt Regressor\n{'='*70}\n⚠️  SKIPPED: {e}")

    full_report = "\n".join(report_sections)
    print(full_report)

    with open("ml/evaluation_report.txt", "w") as f:
        f.write(full_report)
    print("\n\n✅ Full report saved to ml/evaluation_report.txt")


if __name__ == "__main__":
    main()
