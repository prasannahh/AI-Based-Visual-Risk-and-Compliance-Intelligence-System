"""
ai_models/study/predict.py
Prediction and recommendation APIs for the study domain:

- predict_performance: expected marks + GPA for a study session.
- detect_weak_subjects: subject-wise ranking of weak topics.
- generate_study_plan: daily/weekly timetable + revision schedule.
- optimize_study_time: per-subject optimal study-hour allocation.
- predict_performance_trend: performance after 30 / 60 / 90 days.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from ai_models.common.feature_engineering import performance_to_gpa
from ai_models.common.utils import get_or_train
from ai_models.study import model as smodel
from ai_models.study import train as strain

STUDY_BLOCKS = [
    ("07:30", "Focused study", 90),
    ("09:00", "Break", 20),
    ("09:20", "Focused study", 90),
    ("10:50", "Practice problems / MCQ", 60),
    ("11:50", "Lunch", 60),
    ("12:50", "Focused study", 60),
    ("13:50", "Break", 15),
    ("14:05", "Revision of notes", 60),
    ("15:05", "Active recall quiz", 40),
    ("15:45", "Exercise / movement", 30),
    ("16:15", "Focused study", 75),
    ("17:30", "Break", 15),
    ("17:45", "Summary notes", 45),
    ("18:30", "Free time / hobbies", 60),
    ("19:30", "Dinner", 45),
    ("20:15", "Evening revision", 60),
    ("21:15", "Relax / wind down", 30),
]


def predict_performance(subject: str, hours_logged: float, days_to_exam: int, study_consistency: float, prior_score: float) -> dict:
    """Predict expected marks (score) and GPA for a study session.

    Args:
        subject: Subject name.
        hours_logged: Hours logged for the session/day.
        days_to_exam: Days remaining until the exam.
        study_consistency: Consistency in [0, 1].
        prior_score: Historical average score for the subject (0-100).

    Returns:
        {'subject', 'predicted_score', 'predicted_gpa', 'band'}.
    """
    model, _ = get_or_train("study", "performance_predictor", strain.train_performance_model)
    frame = pd.DataFrame(
        [[subject, hours_logged, days_to_exam, study_consistency, prior_score]],
        columns=smodel.PERFORMANCE_FEATURES,
    )
    score = float(np.clip(model.predict(frame)[0], 0, 100))
    gpa = performance_to_gpa(score)
    band = "Distinction" if gpa >= 3.7 else "Good" if gpa >= 3.0 else "Average" if gpa >= 2.0 else "Needs attention"
    return {"subject": subject, "predicted_score": round(score, 1), "predicted_gpa": gpa, "band": band}


def _subject_stats(study_df: pd.DataFrame) -> pd.DataFrame:
    """Per-subject averages and recency-weighted trend from the study log."""
    if study_df.empty or "subject" not in study_df.columns:
        return pd.DataFrame(columns=["subject", "avg_score", "trend"])
    df = study_df.copy()
    df["performance_score"] = pd.to_numeric(df["performance_score"], errors="coerce")
    df = df.dropna(subset=["performance_score"])
    if df.empty:
        return pd.DataFrame(columns=["subject", "avg_score", "trend"])
    df = df.sort_values("date") if "date" in df.columns else df
    stats = []
    for subject, group in df.groupby("subject"):
        avg = float(group["performance_score"].mean())
        trend = 0.0
        if len(group) >= 4:
            recent = group["performance_score"].tail(3).mean()
            earlier = group["performance_score"].head(max(len(group) - 3, 1)).mean()
            trend = ((recent - earlier) / earlier * 100) if earlier else 0.0
        stats.append({"subject": subject, "avg_score": round(avg, 1), "trend": round(trend, 1)})
    return pd.DataFrame(stats)


def detect_weak_subjects(study_df: pd.DataFrame) -> list[dict]:
    """Rank subjects by weakness (lowest average score first) and assign risk level.

    Risk score calculation:
        risk_score = (100 - avg_score) / 100.0

    Risk levels:
        risk_score >= 0.80 -> Critical
        0.60 - 0.79       -> High
        0.40 - 0.59       -> Medium
        0.20 - 0.39       -> Low
        < 0.20            -> Good

    Args:
        study_df: Study log with 'subject' and 'performance_score' columns.

    Returns:
        List of {'subject', 'avg_score', 'risk_score', 'level', 'trend', 'rank'} ordered
        weakest -> strongest.
    """
    stats = _subject_stats(study_df)
    if stats.empty:
        return []
    stats = stats.sort_values("avg_score", ascending=True).reset_index(drop=True)
    outcomes = []
    for i, row in stats.iterrows():
        avg = float(row["avg_score"])
        risk_score = round(max(0.0, min(1.0, (100.0 - avg) / 100.0)), 2)
        if risk_score >= 0.80:
            level = "Critical"
        elif risk_score >= 0.60:
            level = "High"
        elif risk_score >= 0.40:
            level = "Medium"
        elif risk_score >= 0.20:
            level = "Low"
        else:
            level = "Good"
        outcomes.append(
            {
                "subject": row["subject"],
                "avg_score": avg,
                "risk_score": risk_score,
                "level": level,
                "trend": row["trend"],
                "rank": int(i + 1),
            }
        )
    return outcomes


def optimize_study_time(study_df: pd.DataFrame, total_hours: float = 12.0, days_to_exam: dict | None = None) -> pd.DataFrame:
    """Allocate weekly study hours across subjects by priority.

    Priority combines weakness (100 - avg score) and exam proximity, so weak
    subjects that are close to the exam receive the largest allocation.

    Args:
        study_df: Study log with 'subject' and 'performance_score'.
        total_hours: Total weekly study hours to distribute.
        days_to_exam: Optional {subject: days_remaining} map.

    Returns:
        DataFrame [subject, avg_score, priority_score, recommended_hours].
    """
    stats = _subject_stats(study_df)
    if stats.empty:
        return pd.DataFrame(columns=["subject", "avg_score", "priority_score", "recommended_hours"])

    days = days_to_exam or {}
    stats["weakness"] = (100 - stats["avg_score"]).clip(5, 95)
    stats["proximity"] = stats["subject"].map(lambda s: max(0.3, 1.0 / (1 + days.get(s, 60) / 30.0)))
    stats["priority_score"] = stats["weakness"] * stats["proximity"]
    total_priority = stats["priority_score"].sum()
    stats["recommended_hours"] = (stats["priority_score"] / total_priority * total_hours).round(1)
    return stats[["subject", "avg_score", "priority_score", "recommended_hours"]].sort_values("recommended_hours", ascending=False).reset_index(drop=True)


def generate_study_plan(study_df: pd.DataFrame, exam_dates: dict | None = None, daily_hours: float = 4.0) -> dict:
    """Generate a study timetable from goals, exam dates and performance.

    Args:
        study_df: Study log with 'subject' and 'performance_score'.
        exam_dates: Optional {subject: date} of upcoming exams.
        daily_hours: Target focused study hours per day.

    Returns:
        {'daily_timetable': list[dict], 'weekly_plan': list[dict],
         'revision_schedule': list[dict], 'priority_subjects': list[str],
         'total_study_hours': float, 'notes': list[str]}.
    """
    weak = detect_weak_subjects(study_df)
    today = date.today()
    exam_dates = exam_dates or {}

    # Priority rises for weaker subjects (lower rank number = weaker) and for
    # exams that are closer (smaller days remaining -> larger proximity).
    subject_count = len(weak)
    priority_scores = {}
    for item in weak:
        subject = item["subject"]
        prox = 1.0
        if subject in exam_dates:
            days = max((exam_dates[subject] - today).days, 1)
            prox = max(0.3, 1.0 / (1 + days / 30.0))
        priority_scores[subject] = (subject_count + 1 - item["rank"]) + prox * 2.0
    priority_subjects = [s for s, _ in sorted(priority_scores.items(), key=lambda kv: kv[1], reverse=True)]
    main_focus = priority_subjects[0] if priority_subjects else "main"
    timetable = [
        {
            "time": start,
            "activity": activity.replace("Focused study", f"Focused study ({main_focus})") if "Focused study" in activity else activity,
            "duration_min": minutes,
        }
        for start, activity, minutes in STUDY_BLOCKS
        if activity != "Break"
    ]

    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekly_plan = []
    if priority_subjects:
        for i, day in enumerate(weekdays):
            focus = priority_subjects[i % len(priority_subjects)]
            weekly_plan.append({"day": day, "focus_subject": focus, "hours": round(daily_hours, 1)})

    revision_schedule = [
        {
            "subject": p,
            "reason": "Nearest exam" if p in exam_dates else "Weakest subject",
            "suggested_daily_hours": round(max(0.5, daily_hours * priority_scores[p] / max(priority_scores.values(), default=1)), 1),
        }
        for p in priority_subjects
    ]

    notes = [
        "Study in 45-60 minute blocks with 10-15 minute breaks to protect focus.",
        "Revise weak subjects early in the day when concentration peaks.",
        "Schedule lighter revision before the exam rather than cramming new topics.",
    ]
    return {
        "daily_timetable": timetable,
        "weekly_plan": weekly_plan,
        "revision_schedule": revision_schedule,
        "priority_subjects": priority_subjects,
        "total_study_hours": round(daily_hours * 7, 1),
        "notes": notes,
    }


def predict_performance_trend(study_df: pd.DataFrame, horizons: tuple[int, int, int] = (30, 60, 90)) -> pd.DataFrame:
    """Forecast performance score (+ GPA) at fixed future horizons.

    Uses the linear trend of the user's historical performance scores.

    Args:
        study_df: Study log with 'date' and 'performance_score' columns.
        horizons: Days ahead to forecast (default 30/60/90).

    Returns:
        DataFrame [horizon_days, predicted_score, predicted_gpa].
    """
    columns = ["horizon_days", "predicted_score", "predicted_gpa"]
    if study_df.empty or "date" not in study_df.columns or "performance_score" not in study_df.columns:
        return pd.DataFrame(columns=columns)
    df = study_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["performance_score"] = pd.to_numeric(df["performance_score"], errors="coerce")
    df = df.dropna(subset=["performance_score", "date"]).sort_values("date")
    if df.empty:
        return pd.DataFrame(columns=columns)

    x = (df["date"] - df["date"].min()).dt.days.to_numpy(dtype=float)
    y = df["performance_score"].to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x, y = x[valid], y[valid]

    if len(x) < 2 or (x.max() == x.min()):
        baseline = float(np.nanmean(y)) if len(y) > 0 and not np.isnan(np.nanmean(y)) else 70.0
        rows = [{"horizon_days": h, "predicted_score": round(baseline, 1), "predicted_gpa": performance_to_gpa(baseline)} for h in horizons]
        return pd.DataFrame(rows, columns=columns)

    try:
        slope, intercept = np.polyfit(x, y, 1)
        if not np.isfinite(slope) or not np.isfinite(intercept):
            raise ValueError("Non-finite fit")
    except Exception:
        baseline = float(np.nanmean(y)) if len(y) > 0 and not np.isnan(np.nanmean(y)) else 70.0
        rows = [{"horizon_days": h, "predicted_score": round(baseline, 1), "predicted_gpa": performance_to_gpa(baseline)} for h in horizons]
        return pd.DataFrame(rows, columns=columns)

    last_day = float(x.max())
    rows = []
    for h in horizons:
        predicted = float(np.clip(slope * (last_day + h) + intercept, 0, 100))
        rows.append({"horizon_days": h, "predicted_score": round(predicted, 1), "predicted_gpa": performance_to_gpa(predicted)})
    return pd.DataFrame(rows, columns=columns)
