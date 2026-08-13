"""
ai_models/study/model.py
Model registry for the study domain. Candidate algorithms live centrally in
ai_models.common.algorithms.
"""

from __future__ import annotations

PERFORMANCE_FEATURES = ["subject", "hours_logged", "days_to_exam", "study_consistency", "prior_score"]
PERFORMANCE_TARGET = "performance_score"

SUBJECTS = ["Maths", "Physics", "Chemistry", "Computer Science", "English", "History", "Science"]

SUBJECT_DIFFICULTY = {"Physics": -3.0, "Chemistry": -3.0, "Maths": -2.0, "English": 1.0, "History": 1.0, "Computer Science": 3.0, "Science": 1.0}
