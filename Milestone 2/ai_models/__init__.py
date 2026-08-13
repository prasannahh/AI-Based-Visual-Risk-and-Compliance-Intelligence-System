"""AI Core Layer (Milestone 2): health, fitness, study and finance models.

Every domain lives in its own sub-package with a consistent layout:

- model.py      -> model registry (features, algorithms, config)
- preprocess.py -> feature/pipeline builders
- synthetic.py  -> realistic synthetic data generators for dev & tests
- train.py      -> train + persist the best model per task
- predict.py    -> load-or-train + prediction / recommendation APIs
- evaluate.py   -> hold-out evaluation and model comparison

Trained artefacts are stored under ai_models/saved_models/<domain>/ with a
per-domain registry.json used for automatic versioning.
"""
