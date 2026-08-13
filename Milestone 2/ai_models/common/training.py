"""
ai_models/common/training.py
Shared "compare algorithms -> pick best -> fit -> persist" helpers used by
every domain's train.py, so the training flow is identical across models.
"""

from __future__ import annotations

from sklearn.model_selection import train_test_split

from ai_models.common.metrics import best_model, compare_classifiers, compare_regressors
from ai_models.common.utils import ensure_seed, log_model_training, save_model


def best_fit_regressor(features: list[str], target: str, data, build_pipeline, algorithms: dict) -> tuple[str, object, dict]:
    """Compare regressors (wrapped in their preprocessing pipeline), reuse the
    winning fitted pipeline and return (best_name, fitted_pipeline, metrics)."""
    x_train, x_test, y_train, y_test = train_test_split(data[features], data[target], test_size=0.2, random_state=42)
    estimators = {name: build_pipeline(est) for name, est in algorithms.items()}
    results = compare_regressors(estimators, x_train, y_train, x_test, y_test)
    best_name = best_model(results)
    metrics = results.set_index("model").loc[best_name].to_dict()
    return best_name, estimators[best_name], metrics


def best_fit_classifier(features: list[str], target: str, data, build_pipeline, algorithms: dict) -> tuple[str, object, dict]:
    """Compare classifiers (wrapped in their preprocessing pipeline), reuse the
    winning fitted pipeline and return (best_name, fitted_pipeline, metrics)."""
    x_train, x_test, y_train, y_test = train_test_split(data[features], data[target], test_size=0.2, random_state=42)
    estimators = {name: build_pipeline(est) for name, est in algorithms.items()}
    results = compare_classifiers(estimators, x_train, y_train, x_test, y_test)
    best_name = best_model(results)
    metrics = results.set_index("model").loc[best_name].to_dict()
    return best_name, estimators[best_name], metrics


def train_and_persist(
    domain: str,
    name: str,
    features: list[str],
    target: str,
    data,
    build_pipeline,
    algorithms: dict,
    task: str = "regression",
    display_name: str = "",
) -> dict:
    """Run best-fit selection, persist the winning model and log training.

    Args:
        domain: 'health' | 'fitness' | 'study' | 'finance'.
        name: Model name used for persistence.
        features: Feature columns.
        target: Target column.
        data: Full training dataframe.
        build_pipeline: Callable(algorithm) -> sklearn Pipeline.
        algorithms: Mapping of {algorithm_name: unfitted estimator}.
        task: 'regression' or 'classification' (drives model comparison).
        display_name: Optional human-readable model label stored in metadata.

    Returns:
        Training metadata dict (version, algorithm, metrics, records...).
    """
    ensure_seed()
    if task == "classification":
        best_name, pipeline, metrics = best_fit_classifier(features, target, data, build_pipeline, algorithms)
    else:
        best_name, pipeline, metrics = best_fit_regressor(features, target, data, build_pipeline, algorithms)
    meta = save_model(domain, name, pipeline, metrics, records=len(data))
    meta["algorithm"] = best_name
    meta["display_name"] = display_name or name
    log_model_training(meta)
    return meta
