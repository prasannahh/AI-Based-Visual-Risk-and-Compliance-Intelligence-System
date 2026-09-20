"""
ai_models/study/synthetic.py
Realistic synthetic data generator for the study domain.

The performance target combines the student's prior score with hours logged,
study consistency, exam proximity and per-subject difficulty.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ai_models.study import model as smodel


def synthetic_performance_data(rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Synthetic study sessions with a labelled performance score (0-100)."""
    rng = np.random.default_rng(seed)
    subjects = rng.choice(smodel.SUBJECTS, rows)
    hours_logged = rng.uniform(0, 6, rows)
    days_to_exam = rng.integers(1, 90, rows)
    study_consistency = rng.uniform(0, 1, rows)
    prior_score = rng.uniform(30, 95, rows)

    difficulty = np.array([smodel.SUBJECT_DIFFICULTY.get(s, 0.0) for s in subjects])
    hours_effect = 6.0 * np.minimum(hours_logged / 4.0, 1.0)
    consistency_effect = 5.0 * study_consistency
    proximity_effect = 6.0 * np.exp(-days_to_exam / 30.0)
    noise = rng.normal(0, 3.0, rows)

    score = 0.8 * prior_score + hours_effect + consistency_effect + proximity_effect + difficulty + noise
    score = np.clip(score, 10, 100).round(1)
    return pd.DataFrame(
        {
            "subject": subjects,
            "hours_logged": hours_logged.round(2),
            "days_to_exam": days_to_exam,
            "study_consistency": study_consistency.round(2),
            "prior_score": prior_score.round(1),
            "performance_score": score,
        }
    )
