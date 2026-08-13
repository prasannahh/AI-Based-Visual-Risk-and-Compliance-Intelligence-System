# 🧠 AI Core Layer (Milestone 2)

The AI layer turns the logged data from Milestone 1 into predictions, recommendations
and insights across four life domains — health, fitness, study and finance. Every model
is trained locally, persisted to disk with a version tag, and every prediction is logged
back to PostgreSQL so results stay traceable to the user's stored data.

```
ai_models/
├── common/          # Shared helpers used by every domain
│   ├── algorithms.py      # Candidate ML algorithms (XGBoost optional)
│   ├── data_cleaning.py   # Missing values, outliers, scaling, encoding
│   ├── feature_engineering.py  # BMI, calorie formulas, date features...
│   ├── metrics.py         # Regression/classification metrics + model comparison
│   ├── streamlit_ui.py    # Chart & DB helpers for the Streamlit AI tabs
│   ├── training.py        # Compare → pick best → fit → persist flow
│   └── utils.py           # joblib persistence, registry, model logs
├── health/          # BMI, weight, calorie & disease-risk models
├── fitness/         # Fitness score, workout plans, goal achievement
├── study/           # Performance prediction, weak subjects, study plans
├── finance/         # Expense classification, budgets, savings forecasts
├── saved_models/    # Trained artifacts + registry.json per domain (gitignored)
└── README.md
```

## Models

| Domain | Model | Type | Purpose |
|---|---|---|---|
| health | `weight_predictor` | regression | Next-period weight from profile + intake |
| health | `calorie_predictor` | regression | Daily calorie requirement (Mifflin-St Jeor check) |
| health | `risk_obesity` / `risk_diabetes` / `risk_hypertension` | classification | Chronic-disease risk level |
| fitness | `fitness_score_predictor` | regression | 0–100 overall fitness score |
| fitness | `goal_achievement` | classification | Probability of reaching a goal |
| study | `performance_predictor` | regression | Expected score + GPA for a subject |
| finance | `expense_classifier` | classification | Free-text expense → category |

Each domain also exposes rule-based "AI" recommendations (workout plans, study
timetables, budget splits, BMI advice) in `ai_models/<domain>/predict.py`.

## Training & evaluation

Models auto-train on first prediction (`get_or_train` in `common/utils.py`). To
retrain manually:

```bash
python -c "from ai_models.health.train import train_all; print(train_all())"
python -c "from ai_models.fitness.train import train_all; print(train_all())"
python -c "from ai_models.study.train import train_all; print(train_all())"
python -c "from ai_models.finance.train import train_all; print(train_all())"
```

Hold-out comparison tables (used by the "Model training" panels):

```bash
python -c "from ai_models.health.evaluate import evaluate_weight_model, evaluate_calorie_model, evaluate_risk_models; print(evaluate_weight_model())"
```

The training flow (`common/training.py`) wraps every candidate algorithm in the
domain's preprocessing pipeline, trains it on a hold-out split, cross-validates,
selects the best model, persists it via joblib and records a `model_logs` row.

## Replacing synthetic data

`ai_models/<domain>/synthetic.py` generates datasets matching each model's
feature columns. The three health-risk classifiers (`risk_obesity`,
`risk_diabetes`, `risk_hypertension`) and the study `performance_predictor` are
already trained on real public datasets via `ml/train_real.py` (UCI Obesity,
CDC BRFSS 2015 diabetes indicators, ENSANUT 2021 hypertension, UCI Student
Performance), which downloads, transforms and retrains them into
`saved_models/` so the app uses them immediately.

The models below still use synthetic fallbacks because no public labelled
dataset matches their feature schema; **production data** should replace them:

1. Point each `train_*` function (in `ai_models/<domain>/train.py`) at the real
   tables instead of the synthetic generator — the existing `database.py` CRUD
   functions (`get_health_records`, `get_fitness_records`, `get_financial_records`,
   `get_study_activities`) already return DataFrames with compatible columns.
2. Keep `build_*_pipeline` in `preprocess.py` unchanged — pipelines are designed
   to accept any feature count from the same schema.
3. Retrain (`train_all`) and delete old artifacts in `ai_models/saved_models/`.

## Prediction traceability

- Generic log: `database.log_prediction(user_id, domain, model_name, version, confidence, input, output)`.
- Per-domain tables (`health_predictions`, `fitness_predictions`,
  `finance_predictions`, `study_predictions`) store structured results for charts.
- All DB writes are best-effort: if PostgreSQL is unreachable the UI still works
  (`safe_log` in `common/streamlit_ui.py`).

## Tests

```bash
python -m pytest tests -q
```

## Database migration

The new tables (`Health_Records`, `Fitness_Records`, `model_logs`, `predictions`,
`health_predictions`, `fitness_predictions`, `finance_predictions`,
`study_predictions`) are created automatically by `database.init_db()`. For
standalone migrations: `psql -U postgres -d digital_twin -f sql/migration.sql`.
