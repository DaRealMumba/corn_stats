from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable
import unicodedata

from corn_stats.config import LOGO_DIR


@lru_cache(maxsize=None)
def get_logo_path(team_name: str, *, search_dirs: Iterable[Path] | None = None) -> Path | None:
    """Return the path to the team logo if it exists."""
    candidate_dirs = [Path(p) for p in (search_dirs or (LOGO_DIR,))]

    slugs = _slug_candidates(team_name)

    for directory in candidate_dirs:
        for slug in slugs:
            for ext in ("png", "jpg", "jpeg", "svg"):
                candidate = directory / f"{slug}.{ext}"
                if candidate.exists():
                    return candidate

    return None


def _slug_candidates(team_name: str) -> list[str]:
    base = team_name.strip().lower().replace(" ", "-")
    candidates = [base]

    normalized = unicodedata.normalize("NFD", base)
    ascii_slug = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    if ascii_slug not in candidates:
        candidates.append(ascii_slug)

    return candidates

