"""Tests for the study AI module."""

import pandas as pd

from ai_models.study import predict as spredict


def _sample_df():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04", "2026-06-05", "2026-06-06"]),
            "subject": ["Mathematics", "Mathematics", "Physics", "Physics", "Chemistry", "English"],
            "performance_score": [45, 40, 60, 55, 70, 90],
        }
    )


def test_predict_performance_gpa_bounds():
    pred = spredict.predict_performance("Mathematics", 5, 7, 0.75, 85)
    assert 0 <= pred["predicted_gpa"] <= 4.0
    assert 0 <= pred["predicted_score"] <= 100
    assert pred["subject"] == "Mathematics"
    assert pred["band"]


def test_detect_weak_subjects_ordering():
    weak = spredict.detect_weak_subjects(_sample_df())
    assert [item["subject"] for item in weak] == ["Mathematics", "Physics", "Chemistry", "English"]
    assert weak[0]["level"] == "Medium"
    assert weak[0]["risk_score"] == 0.57
    assert weak[-1]["level"] == "Good"
    assert weak[-1]["risk_score"] == 0.10
    assert weak[0]["rank"] == 1

    # Verify all 5 risk level thresholds
    df_critical = pd.DataFrame({"subject": ["Math"], "performance_score": [10]})
    assert spredict.detect_weak_subjects(df_critical)[0]["level"] == "Critical"

    df_high = pd.DataFrame({"subject": ["Math"], "performance_score": [30]})
    assert spredict.detect_weak_subjects(df_high)[0]["level"] == "High"

    df_med = pd.DataFrame({"subject": ["Math"], "performance_score": [50]})
    assert spredict.detect_weak_subjects(df_med)[0]["level"] == "Medium"

    df_low = pd.DataFrame({"subject": ["Math"], "performance_score": [70]})
    assert spredict.detect_weak_subjects(df_low)[0]["level"] == "Low"

    df_good = pd.DataFrame({"subject": ["Math"], "performance_score": [95]})
    assert spredict.detect_weak_subjects(df_good)[0]["level"] == "Good"


def test_detect_weak_subjects_empty():
    assert spredict.detect_weak_subjects(pd.DataFrame()) == []


def test_optimize_study_time_allocation():
    hours = spredict.optimize_study_time(_sample_df(), total_hours=12)
    assert list(hours.columns) == ["subject", "avg_score", "priority_score", "recommended_hours"]
    assert abs(hours["recommended_hours"].sum() - 12) < 1.0
    assert hours.iloc[0]["subject"] == "Mathematics"


def test_generate_study_plan_structure():
    plan = spredict.generate_study_plan(_sample_df(), daily_hours=4)
    assert plan["daily_timetable"]
    first = plan["daily_timetable"][0]
    assert "time" in first and "activity" in first and "duration_min" in first
    assert plan["weekly_plan"]
    assert plan["priority_subjects"][0] == "Mathematics"
    assert plan["total_study_hours"] == 28.0
    assert plan["notes"]


def test_predict_performance_trend():
    trend = spredict.predict_performance_trend(_sample_df())
    assert list(trend.columns) == ["horizon_days", "predicted_score", "predicted_gpa"]
    assert len(trend) == 3
    assert (trend["predicted_score"] <= 100).all()
    assert (trend["predicted_gpa"] <= 4.0).all()
