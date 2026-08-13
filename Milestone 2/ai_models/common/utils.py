"""
ai_models/common/utils.py
Model-management helpers used across every AI domain:

- Deterministic random seeds for reproducible synthetic data / training.
- Joblib persistence with explicit versioning (registry.json per domain).
- Auto load-or-train orchestration ("if the model exists, load it;
  otherwise train automatically").
- Optional model-training logging to the `model_logs` table (lazy DB import
  so the AI package never requires a live PostgreSQL connection to import).
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Callable

import joblib

MODEL_DIR = Path(__file__).resolve().parents[1] / "saved_models"

DEFAULT_SEED = 42


def ensure_seed(seed: int = DEFAULT_SEED) -> None:
    """Pin the NumPy/sklearn random state for reproducible runs."""
    import random

    import numpy as np

    random.seed(seed)
    np.random.seed(seed)


def domain_dir(domain: str) -> Path:
    """Directory where models for a domain are persisted."""
    path = MODEL_DIR / domain
    path.mkdir(parents=True, exist_ok=True)
    return path


def _registry_path(domain: str) -> Path:
    return domain_dir(domain) / "registry.json"


def version_tag() -> str:
    """Human-readable version string, unique per training run."""
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _load_registry(domain: str) -> dict:
    path = _registry_path(domain)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_registry(domain: str, registry: dict) -> None:
    _registry_path(domain).write_text(json.dumps(registry, indent=2), encoding="utf-8")


def save_model(domain: str, name: str, pipeline, metrics: dict, records: int = 0) -> dict:
    """Persist a trained pipeline with a new version and update the registry.

    Args:
        domain: AI domain ('health', 'fitness', 'study', 'finance').
        name: Model name (e.g. 'weight_predictor').
        pipeline: Trained sklearn estimator/pipeline to dump.
        metrics: Evaluation metrics dict recorded at training time.
        records: Number of training records used.

    Returns:
        Metadata dict {domain, name, version, path, metrics, records}.
    """
    version = version_tag()
    filename = f"{name}__{version}.joblib"
    path = domain_dir(domain) / filename
    joblib.dump(pipeline, path)

    registry = _load_registry(domain)
    registry[name] = {
        "version": version,
        "file": filename,
        "metrics": {k: float(v) for k, v in metrics.items()},
        "records": int(records),
        "trained_at": _dt.datetime.now().isoformat(timespec="seconds"),
    }
    _save_registry(domain, registry)
    return {"domain": domain, "name": name, "version": version, "path": str(path), "metrics": metrics, "records": records}


def load_model(domain: str, name: str) -> tuple[object, dict]:
    """Load the latest version of a model.

    Returns:
        (pipeline, metadata dict) or (None, {}) if it does not exist yet.
    """
    registry = _load_registry(domain)
    meta = registry.get(name)
    if not meta:
        return None, {}
    path = domain_dir(domain) / meta["file"]
    if not path.exists():
        return None, {}
    try:
        return joblib.load(path), meta
    except Exception:
        # A model pickled by a different library version may no longer
        # deserialize cleanly (e.g. sklearn upgrades). Treat it as missing so
        # get_or_train() retrains it with the current environment instead of
        # crashing the app.
        return None, {}


def model_available(domain: str, name: str) -> bool:
    """Whether a persisted model exists for the given domain/name."""
    return load_model(domain, name)[0] is not None


def get_or_train(domain: str, name: str, train_fn: Callable[..., dict], **train_kwargs) -> tuple[object, dict]:
    """Load an existing model; otherwise train it (and persist it) on the fly.

    Args:
        domain: AI domain.
        name: Model name.
        train_fn: Callable that trains + persists the model and returns
            metadata dict {version, metrics, records, ...}.
        train_kwargs: Keyword arguments forwarded to `train_fn`.

    Returns:
        (pipeline, metadata dict) with metadata added when freshly trained.
    """
    pipeline, meta = load_model(domain, name)
    if pipeline is not None:
        return pipeline, meta
    trained_meta = train_fn(**train_kwargs)
    pipeline, meta = load_model(domain, name)
    if pipeline is None:
        raise RuntimeError(f"Training '{domain}/{name}' did not produce a loadable model.")
    return pipeline, {**meta, **trained_meta}


def log_model_training(meta: dict) -> None:
    """Best-effort write of a training record into `model_logs` (no-op offline).

    Args:
        meta: Metadata dict produced by save_model / train functions.
    """
    try:
        import database as db

        db.log_model_log(
            model_name=meta.get("name", ""),
            model_version=meta.get("version", ""),
            domain=meta.get("domain", ""),
            algorithm=meta.get("algorithm", ""),
            metrics=meta.get("metrics", {}),
            records=meta.get("records", 0),
        )
    except Exception:
        # The AI core must keep working even when PostgreSQL is unavailable.
        pass


def list_models(domain: str) -> list[dict]:
    """All registered models for a domain (newest registry first)."""
    registry = _load_registry(domain)
    return [{"name": k, **v} for k, v in registry.items()]


def format_float(value: float, digits: int = 3) -> str:
    """Compact float formatting used in metric tables."""
    return f"{float(value):.{digits}f}"
