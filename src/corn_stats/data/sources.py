from __future__ import annotations

import re
from typing import Dict, Iterable, List

import pandas as pd
import requests
from bs4 import BeautifulSoup

from corn_stats.data.cleaning import clean_team_name, normalize_string, normalize_player_stats_columns, merge_duplicate_players


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


def get_team_roster_urls(team_url: str) -> List[Dict[str, str | None]]:
    html = requests.get(team_url, timeout=20).text
    soup = BeautifulSoup(html, "html.parser")

    roster = []

    player_cards = soup.select("a[href*='/players/']")

    for card in player_cards:
        lines = [line.strip() for line in card.get_text("\n", strip=True).split("\n") if line.strip()]

        birth_year = None
        name = None

        # Try find birth year
        for line in lines:
            if re.fullmatch(r"\d{4}", line):
                birth_year = line
                break

        # Name = first non-numeric, non-statistic string
        for line in lines:
            if not re.fullmatch(r"\d{4}", line) and not re.fullmatch(r"[0-9\.\-]+", line):
                # avoid PTS, REB, AST, etc.
                if line.upper() not in {"PTS", "REB", "AST", "STL", "BLK", "+/-", "3PTM", "OU:"}:
                    name = line
                    break

        if name:
            roster.append({
                "name": name,
                "birth_year": birth_year,
                "url": "https://cornliga.com" + card["href"],
            })

    return roster


def get_player_stats(url: str, birth_year: str | None) -> pd.DataFrame:
    """
    Parse player statistics from Cornliga player page.
    
    Page structure uses blocks:
      - EFF, FG, 2P, 3P, FT, AST, TO, STL, BLK, PFD, PTS — simple pattern:
            <HEADER>
            Prosečno → numbers
            Ukupno   → numbers
      - REB O/D — unique block where ORB/DRB are split into two vertical stacks,
        and total REB (average and total) are in a separate gradient div.
    
    extract_after() is used for "simple blocks" and extracts N numbers in a row,
    stopping when it encounters one of STOP_WORDS.
    
    Args:
        url: Player page URL
        birth_year: Birth year for age calculation (can be None if not available)
    """
    html = requests.get(url, timeout=20).text
    soup = BeautifulSoup(html, "html.parser")

    # Headers to stop extract_after
    STOP_WORDS = {
        "EFF", "FG", "2P", "3P", "FT", "REB O/D",
        "AST", "TO", "STL", "BLK", "PFD", "PTS"
    }

    def extract_after(header_node, count: int) -> List[float | None]:
        """
        Extract `count` numbers after header.
        
        Logic:
        - iterate via .find_next()
        - skip text and non-numeric elements
        - stop if next header (STOP_WORDS) is encountered
        - replace ',' with '.' and remove '%' before float conversion
        - pad list with None if fewer numbers than required
        """
        values = []
        el = header_node.find_next()

        while el and len(values) < count:
            txt = (
                el.get_text(strip=True)
                  .replace(",", ".")
                  .replace("%", "")
            )

            # If next header encountered — stop collecting
            if txt in STOP_WORDS:
                break

            # Try to convert to number
            try:
                values.append(float(txt))
            except ValueError:
                pass  # Skip text, div, span, etc.

            el = el.find_next()

        # If fewer numbers than needed — pad with None
        values += [None] * (count - len(values))
        return values

    stats: Dict[str, float | None] = {}

    # ---------- Simple blocks (all except REB O/D) ----------
    blocks = {
        "EFF": ("eff_pg", "eff_total"),
        "FG": ("fg_FGA_pg", "fg_FGM_pg", "fg_FGA_total", "fg_FGM_total", "fg_pct"),
        "2P": ("2p_A_pg", "2p_M_pg", "2p_A_total", "2p_M_total", "2p_pct"),
        "3P": ("3p_A_pg", "3p_M_pg", "3p_A_total", "3p_M_total", "3p_pct"),
        "FT": ("ft_A_pg", "ft_M_pg", "ft_A_total", "ft_M_total", "ft_pct"),
        "AST": ("ast_pg", "ast_total"),
        "TO":  ("to_pg", "to_total"),
        "STL": ("stl_pg", "stl_total"),
        "BLK": ("blk_pg", "blk_total"),
        "PFD": ("pfd_pg", "pfd_total"),
        "PTS": ("pts_pg", "pts_total"),
    }

    # Apply unified logic to all blocks
    for header, keys in blocks.items():
        h = soup.find(string=header)
        if h is not None:
            extracted = extract_after(h, len(keys))
            for k, v in zip(keys, extracted):
                stats[k] = v

    # ---------- REB block (special markup) ----------
    reb_header = soup.find(string="REB O/D")
    if reb_header is not None:
        reb_container = reb_header.find_parent("div")
        if reb_container is not None:
            # --- Prosečno block (ORB_pg, DRB_pg) ---
            proc = reb_container.find("span", string="Prosečno")
            if proc is not None:
                proc = proc.find_parent("div")
                if proc is not None:
                    spans = proc.find_all("span")
                    # spans: ["Prosečno", "ORB", "0.7", "DRB", "4.2"]
                    if len(spans) >= 5:
                        stats["orb_pg"] = float(spans[2].text)
                        stats["drb_pg"] = float(spans[4].text)

            # --- Ukupno block (ORB_total, DRB_total) ---
            ukup = reb_container.find("span", string="Ukupno")
            if ukup is not None:
                ukup = ukup.find_parent("div")
                if ukup is not None:
                    spans = ukup.find_all("span")
                    # spans: ["Ukupno", "ORB", "4", "DRB", "25"]
                    if len(spans) >= 5:
                        stats["orb_total"] = float(spans[2].text)
                        stats["drb_total"] = float(spans[4].text)

            # --- Gradient block with total REB ---
            # div class="bg-gradient" → inside two span: [REB_pg, REB_total]
            gradient = reb_container.find("div", class_="bg-gradient")
            if gradient is not None:
                reb_spans = gradient.find_all("span")
                if len(reb_spans) >= 2:
                    stats["reb_pg"] = float(reb_spans[0].text)
                    stats["reb_total"] = float(reb_spans[1].text)

    # Calculate Games from pts_total / pts_pg (if pts_pg > 0)
    # Round to nearest integer since games must be whole numbers
    # (averages are rounded, so division can give fractional results)
    if "pts_total" in stats and "pts_pg" in stats:
        if stats["pts_pg"] is not None and stats["pts_total"] is not None:
            if stats["pts_pg"] > 0:
                games_calculated = stats["pts_total"] / stats["pts_pg"]
                stats["games"] = int(round(games_calculated))
            else:
                stats["games"] = 0
        else:
            stats["games"] = None
    else:
        stats["games"] = None

    # Calculate age from birth_year if provided
    if birth_year is not None:
        try:
            stats["age"] = pd.to_datetime("now").year - int(birth_year)
        except (ValueError, TypeError):
            stats["age"] = None
    else:
        stats["age"] = None

    return pd.DataFrame([stats])


def get_team_stats_for_all_players(team_url: str) -> pd.DataFrame:
    """
    Collect statistics for all players in a CornLiga team.
    
    1) Load roster — name, birth year, player link.
    2) For each player, parse their individual statistics.
    3) Combine everything into one DataFrame.
    4) Normalize column names.
    5) Filter out players who haven't played any games (Games = 0 or None).
    
    Returns:
        DataFrame with player statistics, excluding players with no games played.
    """
    roster = get_team_roster_urls(team_url)
    all_stats = []
    
    for player in roster:
        player_url = player["url"]
        
        try:
            df = get_player_stats(player_url, birth_year=player["birth_year"])
            df["name"] = player["name"]
            all_stats.append(df)
        except Exception as e:
            # Log error but continue processing other players
            print(f"Error processing {player['name']}: {e}")
        
    if all_stats:
        players_df = pd.concat(all_stats, ignore_index=True)
        players_df = normalize_player_stats_columns(players_df)
        
        # Filter out players who haven't played any games
        # (Games = 0, None, or missing means no games played)
        if "Games" in players_df.columns:
            players_df = players_df[
                (players_df["Games"].notna()) & (players_df["Games"] > 0)
            ].copy()
        
        return players_df
    else:
        return pd.DataFrame()