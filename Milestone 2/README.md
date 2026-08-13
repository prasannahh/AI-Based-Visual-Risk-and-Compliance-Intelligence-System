# Health & Fitness Digital Twin — Milestone 2

This milestone adds the AI Core Layer to the project:

- BMI calculator with standard adult categories
- Explainable fitness score from steps, exercise, sleep, and hydration
- Daily calorie target using the Mifflin–St Jeor equation and activity factor
- Scikit-learn weight forecasting model
- Reproducible training and hold-out validation

## Run it

```powershell
cd "Milestone 2"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Train and validate

From the `Milestone 2` directory:

```powershell
python -c "from pathlib import Path; from ml.trainer import train_weight_model; print(train_weight_model(Path('models/weight_predictor.joblib')))"
pytest
```

## Real-data training

Most AI Core models are now trained on downloaded public datasets instead of
synthetic data. Run once to (re)download, transform and retrain them:

```powershell
python ml\train_real.py
```

| Model | Real dataset | Rows | Hold-out metrics |
|---|---|---|---|
| `risk_obesity` | UCI Obesity (Palechor & de la Hoz, 2019) | 2,110 | acc 0.998, F1 0.998, AUC 1.00 |
| `risk_diabetes` | CDC BRFSS 2015 diabetes indicators | 70,692 | acc 0.690, F1 0.705, AUC 0.760 |
| `risk_hypertension` | ENSANUT 2021 hypertension risk (Mexico) | 3,352 | acc 0.927, F1 0.956, AUC 0.913 |
| `performance_predictor` | UCI Student Performance (maths + portuguese) | 1,044 | MAE 4.96, R² 0.810 |
| workout calorie model | Hugging Face "calorie-burnt" | 15,000 | MAE 1.72 kcal, R² 0.998 |

The datasets are cached under `data/real/`. Where a survey does not record a
schema feature, it is derived from the real columns (e.g. `daily_calories` is
estimated with Mifflin–St Jeor × activity factor; diabetes height/weight are
recovered from BRFSS BMI using sex-specific reference heights). See the
docstring in `ml/train_real.py` for the full list of derivations.

### Still trained on synthetic data

No public labelled dataset matches these models' feature schema, so they keep
their synthetic fallback (documented in `ai_models/<domain>/synthetic.py`):

- `health/weight_predictor`, `health/calorie_predictor`
- `fitness/fitness_score_predictor`, `fitness/goal_achievement`
- `finance/expense_classifier`

These must be replaced with consented, validated data before the model is used
for real health or financial decisions. The app presents estimates, not medical
advice. Note that with real student data the performance model is dominated by
prior performance: hours logged explain only a small share of the final grade
(corr 0.16 vs 0.89 for prior score).

## Training-data schema for a future real dataset

`age, gender, height_cm, current_weight_kg, activity_level, daily_calories, next_weight_kg`

Use an independent test set and assess results across demographic groups before deployment.
