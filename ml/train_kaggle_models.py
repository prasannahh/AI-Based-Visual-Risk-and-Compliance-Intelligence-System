"""
ml/train_kaggle_models.py
--------------------------
Kept for backward compatibility / muscle memory. Training and evaluation
are now one step (ml/evaluate_models.py evaluates every candidate algorithm
AND saves the best one), so this just calls that.

Run with:
    python -m ml.train_kaggle_models

...or run the same thing directly:
    python -m ml.evaluate_models
"""

from ml.evaluate_models import main

if __name__ == "__main__":
    main()