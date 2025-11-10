from __future__ import annotations

import re
import unicodedata
from typing import Tuple

import pandas as pd


def normalize_string(s: str, to_lower: bool = True) -> str:
    """Normalize a string by removing diacritics and optional lowercasing."""
    if pd.isna(s):
        return ""
    normalized = unicodedata.normalize("NFD", str(s))
    without_diacritics = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    result = without_diacritics.strip()
    return result.lower() if to_lower else result


def clean_team_name(raw: str) -> Tuple[str, str | None]:
    """Clean team name and extract trailing abbreviation if present."""
    if pd.isna(raw):
        return raw, None

    s = str(raw).strip()
    s = re.sub(r"^\d+", "", s).strip()

    abbreviation = None
    if len(s) >= 3:
        tail = s[-3:]
        before = s[:-3]
        tail_normalized = normalize_string(tail, to_lower=False)
        is_abbreviation = (
            before
            and not before.endswith(" ")
            and len(tail_normalized) == 3
            and all(ch.isdigit() or (ch.isalpha() and ch.isupper()) for ch in tail_normalized)
        )
        if is_abbreviation:
            abbreviation = tail
            s = before

    s = re.sub(r"\s+", " ", s).strip()
    return s, abbreviation

