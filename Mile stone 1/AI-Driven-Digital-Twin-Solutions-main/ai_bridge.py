"""
ai_bridge.py
Links the Milestone 1 Streamlit app to the Milestone 2 AI Core Layer.

Milestone 1 (this folder) is the UI + data platform. The AI core is owned by
``project/Milestone 2/ai_models`` (single source of truth). Importing this
module puts the ``Milestone 2`` folder on ``sys.path`` so that every
``import ai_models`` in the pages resolves to the shared Milestone 2 copy —
including its ``saved_models`` registry and training code.

Both milestones share the same PostgreSQL database ``digital_twin``, which the
Milestone 1 ``database.py`` connects to (see ``.streamlit/secrets.toml``).

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
    """Put the Milestone 2 AI core on ``sys.path`` and return its directory.

    Raises:
        RuntimeError: when the ``Milestone 2`` folder or its ``ai_models``
            package cannot be found next to this project.
    """
    milestone2 = _find_milestone2()
    if milestone2 is None:
        raise RuntimeError(
            "Could not locate the 'Milestone 2' folder. The AI Core Layer lives there; "
            "keep it alongside 'Mile stone 1' inside the project folder."
        )
    if not (milestone2 / "ai_models").is_dir():
        raise RuntimeError(f"'ai_models' is missing inside {milestone2}.")
    if str(milestone2) not in sys.path:
        sys.path.insert(0, str(milestone2))
    return milestone2


LINKED_DIR = link()
