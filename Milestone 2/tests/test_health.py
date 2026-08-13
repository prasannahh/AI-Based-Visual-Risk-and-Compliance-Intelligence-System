"""Tests for the health AI module."""

from ai_models.health import evaluate as heval
from ai_models.health import predict as hpredict
from ai_models.health import synthetic as hsynth


def test_synthetic_weight_data_shape():
    data = hsynth.synthetic_weight_data(rows=200)
    assert len(data) == 200
    assert "next_weight_kg" in data.columns


def test_synthetic_risk_data_has_labels():
    data = hsynth.synthetic_risk_data(rows=200)
    for label in ["risk_obesity", "risk_diabetes", "risk_hypertension"]:
        assert label in data.columns
        assert set(data[label].unique()) <= {0, 1}


def test_assess_bmi_categories():
    underweight = hpredict.assess_bmi(25, "male", 180, 55)
    assert underweight["category"] == "Underweight"
    healthy = hpredict.assess_bmi(25, "male", 180, 75)
    assert healthy["category"] == "Healthy range"
    assert healthy["bmi"] == round(75 / 1.8 ** 2, 1)


def test_predict_calorie_requirement():
    result = hpredict.predict_calorie_requirement(30, "male", 175, 70, "moderate")
    assert result["ml_kcal"] > 0
    assert result["mifflin_bmr_kcal"] > 0
    assert result["maintenance_kcal"] >= result["mifflin_bmr_kcal"]


def test_predict_weight_forecast():
    forecast = hpredict.predict_weight_forecast(30, "male", 175, 70, "moderate", 2400, days=14)
    assert len(forecast) == 14
    assert list(forecast.columns) == ["day", "predicted_weight_kg"]
    assert (forecast["predicted_weight_kg"] > 0).all()


def test_predict_health_risks():
    risks = hpredict.predict_health_risks(55, "male", 170, 90, "sedentary", 2500, 1)
    assert len(risks) == 3
    for risk in risks:
        assert 0 <= risk["probability_pct"] <= 100
        assert risk["risk_level"] in {"Low", "Moderate", "High"}
        assert risk["recommendations"]


def test_evaluate_weight_model_table():
    table = heval.evaluate_weight_model()
    assert "model" in table.columns and "best" in table.columns
    assert table["best"].sum() == 1


def test_saved_model_metrics_after_train():
    metrics = heval.saved_model_metrics()
    assert "weight_predictor" in metrics
