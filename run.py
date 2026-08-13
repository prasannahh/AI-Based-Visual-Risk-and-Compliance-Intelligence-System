"""
run.py
Launcher for the linked Digital Twin AI application.

Starts the Milestone 1 Streamlit UI, which imports its AI Core Layer from the
Milestone 2 folder (see ai_bridge.py). Both milestones share the same
``digital_twin`` PostgreSQL database.

Usage:
    python run.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
APP_DIR = (
    PROJECT_ROOT
    / "Mile stone 1"
    / "AI-Driven-Digital-Twin-Solutions-main"
    / "AI-Driven-Digital-Twin-Solutions-main"
)
AI_CORE = PROJECT_ROOT / "Milestone 2" / "ai_models"


def main() -> int:
    if not APP_DIR.is_dir():
        print(f"ERROR: Milestone 1 app not found at {APP_DIR}", file=sys.stderr)
        return 1
    if not AI_CORE.is_dir():
        print(f"ERROR: Milestone 2 AI core not found at {AI_CORE}", file=sys.stderr)
        return 1

    print(f"Starting Digital Twin AI from: {APP_DIR}")
    print(f"AI Core Layer (Milestone 2):  {AI_CORE}")
    print("Database: digital_twin (configure in .streamlit/secrets.toml)")
    return subprocess.call([sys.executable, "-m", "streamlit", "run", "app.py"], cwd=str(APP_DIR))


if __name__ == "__main__":
    sys.exit(main())
