"""
ai_bridge.py
Links the Streamlit app to the AI Core Layer (ai_models package).

In the merged single-folder layout the ``ai_models`` package lives next to
``app.py`` so no path manipulation is needed – Python already includes the
script directory on ``sys.path``.

When the original two-folder layout is used, this module walks up looking
for the sibling ``Milestone 2`` folder and adds it to ``sys.path``.

Run the linked app with the launcher at the project root:  python run.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_APP_ROOT = Path(__file__).resolve().parent


def _find_milestone2() -> Path | None:
    """Walk up from the app root looking for the sibling ``Milestone 2`` folder."""
    for parent in (_APP_ROOT, *_APP_ROOT.parents):
        candidate = parent / "Milestone 2"
        if candidate.is_dir():
            return candidate
    return None


def link() -> Path:
    """Put the AI core on ``sys.path`` and return its directory.

    Supports both the merged single-folder layout (ai_models next to app.py)
    and the original two-folder layout (Milestone 2 as a sibling folder).
    """
    # --- Merged layout: ai_models lives right here ---
    if (_APP_ROOT / "ai_models").is_dir():
        if str(_APP_ROOT) not in sys.path:
            sys.path.insert(0, str(_APP_ROOT))
        return _APP_ROOT

    # --- Original two-folder layout ---
    milestone2 = _find_milestone2()
    if milestone2 is None:
        raise RuntimeError(
            "Could not locate the AI Core Layer. In the merged layout "
            "the 'ai_models' folder should be next to 'app.py'. "
            "In the original layout keep 'Milestone 2' alongside 'Mile stone 1'."
        )
    if not (milestone2 / "ai_models").is_dir():
        raise RuntimeError(f"'ai_models' is missing inside {milestone2}.")
    if str(milestone2) not in sys.path:
        sys.path.insert(0, str(milestone2))
    return milestone2


LINKED_DIR = link()
