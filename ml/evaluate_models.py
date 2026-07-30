"""
ml/evaluate_models.py
-----------------------
For EACH of the 4 Kaggle datasets, this script:

  1. Trains and evaluates SEVERAL different ML algorithms (not just one),
     chosen to represent genuinely different modeling approaches (linear,
     instance-based, bagged-ensemble, boosted-ensemble).
  2. Evaluates every candidate two ways:
       (a) an 80:20 train/test split
       (b) 5-fold cross-validation across the FULL dataset
  3. Uses a metric appropriate to that dataset's problem (explained below
     and printed in the report -- not the same metric for every dataset,
     because "accuracy" is actively misleading for some of these).
  4. Prints ONE summary table per dataset (4 tables total) comparing every
     candidate on that metric.
  5. Retrains the single best-performing candidate on the FULL dataset and
     saves it as the "production" model (ml/models/kaggle_<name>_model.pkl)
     -- this is the exact model app.py loads for live predictions and for
     the Digital Twin Simulation page. A metadata file records which
     algorithm won and why, so the app can show it in the UI.

Run with:
    python -m ml.evaluate_models

Requires the Kaggle datasets to already be in data/ (see data/README.md).
Datasets that are missing are skipped with a clear message.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_validate, StratifiedKFold, KFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_absolute_error, mean_squared_error, r2_score,
)

from ml.kaggle_models import (
    DATASET_REGISTRY, build_pipeline, save_best_model, DatasetNotFoundError,
)

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 20)

# ---------------------------------------------------------------------------
# Why each algorithm is included as a candidate -- printed once per dataset
# so the report explains itself instead of just dumping numbers.
# ---------------------------------------------------------------------------
ALGO_RATIONALE = {
    "LogisticRegression": "Linear baseline. Fast, interpretable, and a useful "
        "sanity check -- if a complex model can't beat this, the complexity isn't paying off.",
    "LinearRegression": "Linear baseline for regression -- same role as LogisticRegression: "
        "fast and interpretable, sets the bar the other models need to clear.",
    "KNeighborsClassifier": "Instance-based / non-parametric. Makes no assumption about the "
        "shape of the relationship between features and outcome -- good at capturing local patterns.",
    "KNeighborsRegressor": "Instance-based / non-parametric regression -- predicts from the "
        "average of similar past examples rather than fitting a global formula.",
    "RandomForestClassifier": "Bagged ensemble of decision trees. Captures non-linear "
        "interactions between features and is naturally robust to outliers and irrelevant features.",
    "RandomForestRegressor": "Bagged ensemble of regression trees -- same robustness benefits "
        "as the classifier version, applied to a continuous target.",
    "GradientBoostingClassifier": "Boosted ensemble -- trees are built sequentially, each one "
        "correcting the previous ones' mistakes. Often the strongest tabular-data performer of the group.",
    "GradientBoostingRegressor": "Boosted ensemble for regression -- same sequential "
        "error-correction idea, frequently the most accurate option for structured/tabular data.",
}

ASCENDING_METRICS = {"mae", "rmse"}  # lower is better for these; higher is better for everything else


def _is_binary(y) -> bool:
    return pd.Series(y).nunique() == 2


def _classification_scoring(is_binary: bool):
    base = ["accuracy", "f1_macro", "precision_macro", "recall_macro"]
    base.append("roc_auc" if is_binary else "roc_auc_ovr_weighted")
    return base


def _evaluate_classification_candidate(name, factory, X, y, numeric, categorical, is_binary):
    # --- 80:20 split ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    pipe = build_pipeline(numeric, categorical, factory())
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    split_metrics = {
        "split_accuracy": accuracy_score(y_test, y_pred),
        "split_f1_macro": f1_score(y_test, y_pred, average="macro", zero_division=0),
        "split_precision_macro": precision_score(y_test, y_pred, average="macro", zero_division=0),
        "split_recall_macro": recall_score(y_test, y_pred, average="macro", zero_division=0),
    }
    if is_binary:
        proba = pipe.predict_proba(X_test)
        classes = list(pipe.classes_)
        pos_idx = classes.index(1) if 1 in classes else 0
        split_metrics["split_roc_auc"] = roc_auc_score((y_test == classes[pos_idx]).astype(int), proba[:, pos_idx])
    else:
        proba = pipe.predict_proba(X_test)
        split_metrics["split_roc_auc"] = roc_auc_score(
            y_test, proba, multi_class="ovr", average="weighted", labels=pipe.classes_
        )

    # --- 5-fold CV on the full dataset ---
    cv_pipe = build_pipeline(numeric, categorical, factory())
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv = cross_validate(cv_pipe, X, y, cv=skf, scoring=_classification_scoring(is_binary))

    cv_metrics = {
        "cv_accuracy": cv["test_accuracy"].mean(),
        "cv_f1_macro": cv["test_f1_macro"].mean(),
        "cv_precision_macro": cv["test_precision_macro"].mean(),
        "cv_recall_macro": cv["test_recall_macro"].mean(),
        "cv_roc_auc": cv["test_roc_auc" if is_binary else "test_roc_auc_ovr_weighted"].mean(),
        "cv_f1_macro_std": cv["test_f1_macro"].std(),
    }

    return {"algorithm": name, **split_metrics, **cv_metrics}


def _evaluate_regression_candidate(name, factory, X, y, numeric, categorical):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    pipe = build_pipeline(numeric, categorical, factory())
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    split_metrics = {
        "split_mae": mean_absolute_error(y_test, y_pred),
        "split_rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
        "split_r2": r2_score(y_test, y_pred),
    }

    cv_pipe = build_pipeline(numeric, categorical, factory())
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv = cross_validate(
        cv_pipe, X, y, cv=kf,
        scoring=["neg_mean_absolute_error", "neg_root_mean_squared_error", "r2"],
    )
    cv_metrics = {
        "cv_mae": -cv["test_neg_mean_absolute_error"].mean(),
        "cv_rmse": -cv["test_neg_root_mean_squared_error"].mean(),
        "cv_r2": cv["test_r2"].mean(),
        "cv_rmse_std": (-cv["test_neg_root_mean_squared_error"]).std(),
    }
    return {"algorithm": name, **split_metrics, **cv_metrics}


def _metric_column_for(primary_metric: str) -> str:
    """Map a primary_metric key to the actual CV column name to rank by."""
    return {
        "f1_macro": "cv_f1_macro",
        "roc_auc": "cv_roc_auc",
        "rmse": "cv_rmse",
    }[primary_metric]


def evaluate_dataset(dataset_key: str) -> pd.DataFrame:
    cfg = DATASET_REGISTRY[dataset_key]
    df, path = cfg["loader"]()
    if cfg["prep"]:
        df = cfg["prep"](df)

    numeric, categorical, target = cfg["numeric"], cfg["categorical"], cfg["target"]
    X = df[numeric + categorical]
    y = df[target]
    is_classification = cfg["task"] == "classification"
    is_binary = is_classification and _is_binary(y)

    print(f"\n{'='*78}\nDATASET: {dataset_key.upper()}   ({path})\n{'='*78}")
    print(f"Rows: {len(df)}  |  Task: {cfg['task']}  |  Target: '{target}'")
    print(f"Primary metric: {cfg['primary_metric']}")
    print(f"Why this metric: {cfg['metric_reason']}")

    candidates = cfg["candidates"]()
    rows = []
    for name, factory in candidates.items():
        print(f"\n  -> Evaluating {name}")
        print(f"     Why this algorithm is a candidate: {ALGO_RATIONALE.get(name, '')}")
        if is_classification:
            row = _evaluate_classification_candidate(name, factory, X, y, numeric, categorical, is_binary)
        else:
            row = _evaluate_regression_candidate(name, factory, X, y, numeric, categorical)
        rows.append(row)

    results_df = pd.DataFrame(rows)
    metric_col = _metric_column_for(cfg["primary_metric"])
    ascending = cfg["primary_metric"] in ASCENDING_METRICS
    results_df = results_df.sort_values(metric_col, ascending=ascending).reset_index(drop=True)

    # --- Print the summary table for this dataset ---
    if is_classification:
        display_cols = ["algorithm", "cv_accuracy", "cv_f1_macro", "cv_precision_macro",
                          "cv_recall_macro", "cv_roc_auc", "split_accuracy", "split_f1_macro"]
    else:
        display_cols = ["algorithm", "cv_mae", "cv_rmse", "cv_r2", "split_mae", "split_rmse", "split_r2"]

    print(f"\n--- SUMMARY TABLE: {dataset_key.upper()} "
          f"(sorted by {cfg['primary_metric']}, {'lower' if ascending else 'higher'} = better) ---")
    print(results_df[display_cols].round(4).to_string(index=False))

    best_name = results_df.iloc[0]["algorithm"]
    best_value = results_df.iloc[0][metric_col]
    print(f"\n🏆 Best model for '{dataset_key}': {best_name}  "
          f"({cfg['primary_metric']} = {best_value:.4f})")

    # --- Retrain the winner on the FULL dataset and save it as production ---
    winning_pipeline = build_pipeline(numeric, categorical, candidates[best_name]())
    winning_pipeline.fit(X, y)
    save_best_model(
        dataset_key, winning_pipeline, best_name, cfg["primary_metric"], best_value,
        all_results=results_df[["algorithm", metric_col]].round(4).to_dict(orient="records"),
    )
    print(f"   Saved to ml/models/kaggle_{dataset_key}_model.pkl "
          f"(+ kaggle_{dataset_key}_meta.json)")

    results_df.insert(0, "dataset", dataset_key)
    return results_df


def main():
    all_tables = []
    skipped = []

    for dataset_key in DATASET_REGISTRY:
        try:
            table = evaluate_dataset(dataset_key)
            all_tables.append(table)
        except DatasetNotFoundError as e:
            print(f"\n{'='*78}\nDATASET: {dataset_key.upper()}\n{'='*78}")
            print(f"⚠️  SKIPPED: {e}")
            skipped.append(dataset_key)

    if not all_tables:
        print("\nNo datasets found in data/ -- nothing to evaluate. See data/README.md.")
        return

    combined = pd.concat(all_tables, ignore_index=True)
    combined.to_csv("ml/evaluation_report.csv", index=False)

    # --- Final recap: which algorithm won for each dataset ---
    print(f"\n\n{'='*78}\nFINAL RECAP -- best model per dataset ({len(all_tables)}/4 datasets evaluated)\n{'='*78}")
    recap_rows = []
    for dataset_key in DATASET_REGISTRY:
        if dataset_key in skipped:
            continue
        cfg = DATASET_REGISTRY[dataset_key]
        sub = combined[combined["dataset"] == dataset_key]
        metric_col = _metric_column_for(cfg["primary_metric"])
        best_row = sub.iloc[0]
        recap_rows.append({
            "dataset": dataset_key,
            "best_algorithm": best_row["algorithm"],
            "primary_metric": cfg["primary_metric"],
            "score": round(best_row[metric_col], 4),
        })
    recap_df = pd.DataFrame(recap_rows)
    print(recap_df.to_string(index=False))

    if skipped:
        print(f"\nSkipped (dataset not found): {', '.join(skipped)}. See data/README.md.")

    print("\n✅ Full per-model results saved to ml/evaluation_report.csv")
    print("✅ Winning model + metadata saved per dataset to ml/models/")


if __name__ == "__main__":
    main()