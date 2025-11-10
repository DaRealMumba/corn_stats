from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable

from corn_stats.config import LOGO_DIR


@lru_cache(maxsize=None)
def get_logo_path(team_name: str, *, search_dirs: Iterable[Path] | None = None) -> Path | None:
    """Return the path to the team logo if it exists."""
    team_slug = team_name.lower().replace(" ", "-")
    candidate_dirs = [Path(p) for p in (search_dirs or (LOGO_DIR,))]

    for directory in candidate_dirs:
        for ext in ("png", "jpg", "jpeg", "svg"):
            candidate = directory / f"{team_slug}.{ext}"
            if candidate.exists():
                return candidate

    return None

