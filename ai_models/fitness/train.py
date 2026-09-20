"""
ai_models/fitness/train.py
Training entry points for the fitness domain.
"""

from __future__ import annotations

from ai_models.common.algorithms import candidate_classifiers, candidate_regressors
from ai_models.common.training import train_and_persist
from ai_models.fitness import model as fmodel
from ai_models.fitness import preprocess as fprep
from ai_models.fitness import synthetic as fsynth


def train_fitness_score_model() -> dict:
    """Train and persist the best fitness-score regressor."""
    data = fsynth.synthetic_fitness_score_data()
    return train_and_persist(
        "fitness", "fitness_score_predictor", fmodel.FITNESS_SCORE_FEATURES, fmodel.FITNESS_SCORE_TARGET,
        data, fprep.build_fitness_score_pipeline, candidate_regressors(), display_name="Fitness Score Prediction",
    )


def train_goal_model() -> dict:
    """Train and persist the best goal-achievement classifier."""
    data = fsynth.synthetic_goal_data()
    return train_and_persist(
        "fitness", "goal_achievement", fmodel.GOAL_FEATURES, fmodel.GOAL_TARGET,
        data, fprep.build_goal_pipeline, candidate_classifiers(),
        task="classification", display_name="Goal Achievement Prediction",
    )


def train_all() -> dict:
    """Train every fitness model and return a combined summary."""
    return {
        "fitness_score_predictor": train_fitness_score_model(),
        "goal_achievement": train_goal_model(),
    }
