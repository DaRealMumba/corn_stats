from __future__ import annotations

import re
from typing import Dict, Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup

from corn_stats.data.cleaning import clean_team_name, normalize_string


def get_league_table(table_url: str) -> pd.DataFrame:
    """Fetch league table data and return a normalized DataFrame."""
    df = pd.read_html(table_url)[0]

    lower = {c: str(c).strip().lower() for c in df.columns}

    def find(candidates: Iterable[str]) -> str | None:
        for column, lowered in lower.items():
            if any(candidate in lowered for candidate in candidates):
                return column
        return None

    team_col = find(["ekipa"])
    points_col = find(["bodovi"])
    wins_col = find(["pobede"])
    losses_col = find(["porazi"])
    scored_col = find(["poeni +", "+"])
    allowed_col = find(["poeni -", "-"])

    missing_cols = []
    if team_col is None:
        missing_cols.append("team (ekipa)")
    if points_col is None:
        missing_cols.append("points (bodovi)")
    if wins_col is None:
        missing_cols.append("wins (pobede)")
    if losses_col is None:
        missing_cols.append("losses (porazi)")
    if scored_col is None:
        missing_cols.append("scored (poeni +)")
    if allowed_col is None:
        missing_cols.append("allowed (poeni -)")

    if missing_cols:
        raise ValueError(
            f"Could not find required columns in league table: {', '.join(missing_cols)}. "
            f"Available columns: {list(df.columns)}"
        )

    selected = df[[team_col, points_col, wins_col, losses_col, scored_col, allowed_col]].copy()
    selected.columns = ["Team", "Points", "Wins", "Losses", "Scored", "Allowed"]

    for col in ["Points", "Wins", "Losses", "Scored", "Allowed"]:
        selected[col] = (
            pd.to_numeric(
                selected[col]
                .astype(str)
                .str.replace("\u2212", "-", regex=False)
                .str.extract(r"(-?\d+)", expand=False),
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )

    selected["Games"] = selected["Wins"] + selected["Losses"]
    selected["Points_Diff"] = selected["Scored"] - selected["Allowed"]
    
    # Avoid division by zero if Games is 0
    games_mask = selected["Games"] > 0
    selected.loc[games_mask, "Pts_Scored_Avg"] = (
        selected.loc[games_mask, "Scored"] / selected.loc[games_mask, "Games"]
    ).round(1)
    selected.loc[~games_mask, "Pts_Scored_Avg"] = 0.0
    
    selected.loc[games_mask, "Pts_Allowed_Avg"] = (
        selected.loc[games_mask, "Allowed"] / selected.loc[games_mask, "Games"]
    ).round(1)
    selected.loc[~games_mask, "Pts_Allowed_Avg"] = 0.0

    team_data = selected["Team"].apply(clean_team_name)
    selected["Team"] = team_data.apply(lambda x: x[0])
    selected["Abbr"] = team_data.apply(lambda x: x[1])

    # Set position as index (1-based ranking instead of 0-11)
    selected.index = range(1, len(selected) + 1)
    selected.index.name = "Position"

    return selected


def parse_team_page_wide(team_url: str, league_table_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Parse team page data and return a DataFrame with renamed columns."""
    response = requests.get(team_url, timeout=20)
    response.raise_for_status()
    text = BeautifulSoup(response.text, "html.parser").get_text(separator=" ", strip=True)

    slug = team_url.rstrip("/").split("/")[-1]
    team_name = slug.replace("-", " ")

    abbreviation = None
    if league_table_df is not None and {"Team", "Abbr"}.issubset(league_table_df.columns):
        team_name_normalized = normalize_string(team_name)

        matches = league_table_df[
            league_table_df["Team"].astype(str).apply(normalize_string) == team_name_normalized
        ]
        if not matches.empty:
            abbreviation = matches.iloc[0]["Abbr"]
        else:
            for _, row in league_table_df.iterrows():
                league_team_normalized = normalize_string(str(row["Team"]))
                if team_name_normalized in league_team_normalized or league_team_normalized in team_name_normalized:
                    abbreviation = row["Abbr"]
                    break

    result: Dict[str, float | str | None] = {"Team": team_name, "Abbr": abbreviation}

    patterns = {
        "FG": r"FG\s+Prosečno\s+FGA\s+([\d.]+)\s+FGM\s+([\d.]+).*?Ukupno\s+FGA\s+([\d.]+)\s+FGM\s+([\d.]+)",
        "2P": r"2P\s+Prosečno\s+2PTA\s+([\d.]+)\s+2PTM\s+([\d.]+).*?Ukupno\s+2PTA\s+([\d.]+)\s+2PTM\s+([\d.]+)",
        "3P": r"3P\s+Prosečno\s+3PTA\s+([\d.]+)\s+3PTM\s+([\d.]+).*?Ukupno\s+3PTA\s+([\d.]+)\s+3PTM\s+([\d.]+)",
        "FT": r"FT\s+Prosečno\s+FTA\s+([\d.]+)\s+FTM\s+([\d.]+).*?Ukupno\s+FTA\s+([\d.]+)\s+FTM\s+([\d.]+)",
    }

    if match := re.search(patterns["FG"], text, re.DOTALL):
        result["FGA_Avg"], result["FGM_Avg"], result["FGA_Tot"], result["FGM_Tot"] = map(
            float, (match.group(1), match.group(2), match.group(3), match.group(4))
        )

    if match := re.search(patterns["2P"], text, re.DOTALL):
        a_avg, m_avg, a_tot, m_tot = map(
            float, (match.group(1), match.group(2), match.group(3), match.group(4))
        )
        result["2PA_Avg"], result["2PM_Avg"], result["2PA_Tot"], result["2PM_Tot"] = (
            a_avg,
            m_avg,
            a_tot,
            m_tot,
        )

    if match := re.search(patterns["3P"], text, re.DOTALL):
        a_avg, m_avg, a_tot, m_tot = map(
            float, (match.group(1), match.group(2), match.group(3), match.group(4))
        )
        result["3PA_Avg"], result["3PM_Avg"], result["3PA_Tot"], result["3PM_Tot"] = (
            a_avg,
            m_avg,
            a_tot,
            m_tot,
        )

    if match := re.search(patterns["FT"], text, re.DOTALL):
        a_avg, m_avg, a_tot, m_tot = map(
            float, (match.group(1), match.group(2), match.group(3), match.group(4))
        )
        result["FTA_Avg"], result["FTM_Avg"], result["FTA_Tot"], result["FTM_Tot"] = (
            a_avg,
            m_avg,
            a_tot,
            m_tot,
        )

    if match := re.search(
        r"REB O/D\s+Prosečno\s+ORB\s+([\d.]+)\s+DRB\s+([\d.]+).*?Ukupno\s+ORB\s+([\d.]+)\s+DRB\s+([\d.]+)",
        text,
        re.DOTALL,
    ):
        result["ORB_Avg"], result["DRB_Avg"], result["ORB_Tot"], result["DRB_Tot"] = map(
            float, (match.group(1), match.group(2), match.group(3), match.group(4))
        )

    # Parse metrics (excluding PTS - it's already in league table as Scored/Pts_Scored_Avg)
    for metric in ("AST", "TO", "STL", "BLK", "PFD"):
        if match := re.search(
            rf"{metric}\s+Prosečno\s+([\d.]+).*?Ukupno\s+([\d.]+)", text, re.DOTALL
        ):
            result[f"{metric}_Avg"], result[f"{metric}_Tot"] = map(float, (match.group(1), match.group(2)))

    # Validate that at least some basic stats were found
    required_stats = ["FGA_Avg", "FGM_Avg"]
    found_stats = [stat for stat in required_stats if stat in result]
    
    if not found_stats:
        raise ValueError(
            f"Could not parse any team statistics from {team_url}. "
            f"Page structure may have changed or team page is empty."
        )
    
    dataframe = pd.DataFrame([result])
    priority_cols = ["Team", "Abbr"]
    other_cols = [c for c in dataframe.columns if c not in priority_cols]
    return dataframe[priority_cols + other_cols]

