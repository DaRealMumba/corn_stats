from __future__ import annotations

import re
import unicodedata
from typing import Tuple

import pandas as pd


PLAYER_RENAME_MAP: dict[str, str] = {
    "eff_pg": "Eff_Avg",
    "eff_total": "Eff_Tot",
    "fg_FGA_pg": "FGA_Avg",
    "fg_FGM_pg": "FGM_Avg",
    "fg_FGA_total": "FGA_Tot",
    "fg_FGM_total": "FGM_Tot",
    "fg_pct": "FG%",
    "2p_A_pg": "2PA_Avg",
    "2p_M_pg": "2PM_Avg",
    "2p_A_total": "2PA_Tot",
    "2p_M_total": "2PM_Tot",
    "2p_pct": "2P%",
    "3p_A_pg": "3PA_Avg",
    "3p_M_pg": "3PM_Avg",
    "3p_A_total": "3PA_Tot",
    "3p_M_total": "3PM_Tot",
    "3p_pct": "3P%",
    "ft_A_pg": "FTA_Avg",
    "ft_M_pg": "FTM_Avg",
    "ft_A_total": "FTA_Tot",
    "ft_M_total": "FTM_Tot",
    "ft_pct": "FT%",
    "ast_pg": "AST_Avg",
    "ast_total": "AST_Tot",
    "to_pg": "TO_Avg",
    "to_total": "TO_Tot",
    "stl_pg": "STL_Avg",
    "stl_total": "STL_Tot",
    "blk_pg": "BLK_Avg",
    "blk_total": "BLK_Tot",
    "pfd_pg": "PFD_Avg",
    "pfd_total": "PFD_Tot",
    "pts_pg": "Pts_Avg",
    "pts_total": "Pts_Tot",
    "orb_pg": "ORB_Avg",
    "drb_pg": "DRB_Avg",
    "orb_total": "ORB_Tot",
    "drb_total": "DRB_Tot",
    "reb_pg": "TRB_Avg",
    "reb_total": "TRB_Tot",
    "name": "Player",
    "age": "Age",
}

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


def normalize_player_stats_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Bring player-level stats to the same naming style as team stats.
    """
    df = df.copy()
    df = df.rename(columns=PLAYER_RENAME_MAP)
    return df