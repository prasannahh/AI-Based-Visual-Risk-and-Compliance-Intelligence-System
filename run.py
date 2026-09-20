"""
run.py
Launcher for the Digital Twin AI application.

Starts the Streamlit UI (app.py) which imports its AI Core Layer (ai_models/)
directly from the same folder.  The UI + data platform lives alongside the AI
models, database layer, and ML training code in a single flat project layout.

Usage:
    python run.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
APP_FILE = PROJECT_ROOT / "app.py"


def main() -> int:
    if not APP_FILE.is_file():
        print(f"ERROR: app.py not found at {APP_FILE}", file=sys.stderr)
        return 1

    print(f"Starting Digital Twin AI from: {PROJECT_ROOT}")
    print("Database: digital_twin (configure in .streamlit/secrets.toml)")
    return subprocess.call(
        [sys.executable, "-m", "streamlit", "run", "app.py"],
        cwd=str(PROJECT_ROOT),
    )


if __name__ == "__main__":
    sys.exit(main())
