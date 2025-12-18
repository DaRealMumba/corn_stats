from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"

RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

TABLES_DATA_PATH = RAW_DATA_DIR / "tables"
RAW_TEAMS_DATA_PATH = RAW_DATA_DIR / "teams"
PROCESSED_TEAMS_DATA_PATH = PROCESSED_DATA_DIR / "teams"
RAW_PLAYERS_DATA_PATH = RAW_DATA_DIR / "players"
PROCESSED_PLAYERS_DATA_PATH = PROCESSED_DATA_DIR / "players"
LOGO_DIR = ASSETS_DIR / "logos"

TABLE_URL = "https://cornliga.com/seasons/2025-26/leagues/north-liga"
TEAMS_URL = "https://cornliga.com/seasons/2025-26/leagues/north-liga/teams"

TEAMS = [
    "ravens-belgrade",
    "belgrade-bulls",
    "kk-sljakeri",
    "kk-savski",
    "pistacci",
    "dva-telefona",
    "fireflies",
    "kk-tap-011",
    "kk-tufe",
    "phantom-troupe",
    "koza-nostra",
    "kk-bricklayers",
]

# Column order for team stats DataFrame
TEAM_STATS_COLUMN_ORDER = [
    # Basic info
    "Team",
    "Abbr",
    # League standings
    "Position",
    "Points",
    "Wins",
    "Losses",
    "Games",
    "Win%",
    "Scored",
    "Allowed",
    "Points_Diff",
    "Pts_Scored_Avg",
    "Pts_Allowed_Avg",
    "Pts_Diff_Avg",
    # Shooting percentages
    "FG%",
    "2P%",
    "3P%",
    "FT%",
    "eFG%",
    "TS%",
    # Shot distribution
    "%Pts_2P",
    "%Pts_3P",
    "%Pts_FT",
    "2Pr",
    "3Pr",
    "FTr",
    # Totals (shooting)
    "FGM_Tot",
    "FGA_Tot",
    "2PM_Tot",
    "2PA_Tot",
    "3PM_Tot",
    "3PA_Tot",
    "FTM_Tot",
    "FTA_Tot",
    # Averages (shooting)
    "FGM_Avg",
    "FGA_Avg",
    "2PM_Avg",
    "2PA_Avg",
    "3PM_Avg",
    "3PA_Avg",
    "FTM_Avg",
    "FTA_Avg",
    # Rebounds
    "ORB_Tot",
    "DRB_Tot",
    "TRB_Tot",
    "ORB_Avg",
    "DRB_Avg",
    "TRB_Avg",
    "ORB%",
    "DRB%",
    # Other stats
    "AST_Tot",
    "AST_Avg",
    "TO_Tot",
    "TO_Avg",
    "STL_Tot",
    "STL_Avg",
    "BLK_Tot",
    "BLK_Avg",
    "PFD_Tot",
    "PFD_Avg",
    # Advanced metrics
    "POSS_Tot",
    "Pace",
    "Off_Rating",
    "Def_Rating",
    "Net_Rating",
    "TO%",
    "AST_Rate",
    "STL_Rate",
    "BLK_Rate",
    "PFD_Rate",
    "ASS_TO_Ratio",
]

# Column order for player stats DataFrame
PLAYER_STATS_COLUMN_ORDER = [
    # Basic info
    "Player",
    "Age",
    "Games",
    # Points & Efficiency
    "Pts_Avg",
    "Pts_Tot",
    "Eff_Avg",
    "Eff_Tot",
    # Field Goals
    "FGM_Avg",
    "FGA_Avg",
    "FG%",
    "FGM_Tot",
    "FGA_Tot",
    # 2-Pointers
    "2PM_Avg",
    "2PA_Avg",
    "2P%",
    "2PM_Tot",
    "2PA_Tot",
    # 3-Pointers
    "3PM_Avg",
    "3PA_Avg",
    "3P%",
    "3PM_Tot",
    "3PA_Tot",
    # Free Throws
    "FTM_Avg",
    "FTA_Avg",
    "FT%",
    "FTM_Tot",
    "FTA_Tot",
    # Rebounds
    "TRB_Avg",
    "TRB_Tot",
    "ORB_Avg",
    "ORB_Tot",
    "DRB_Avg",
    "DRB_Tot",
    # Playmaking
    "AST_Avg",
    "AST_Tot",
    "TO_Avg",
    "TO_Tot",
    # Defense
    "STL_Avg",
    "STL_Tot",
    "BLK_Avg",
    "BLK_Tot",
    # Fouls Drawn
    "PFD_Avg",
    "PFD_Tot",
    # Advanced metrics
    "TS%",
    "eFG%",
    "Shot_Usage",
    # "Usage_Share",
    "%Pts_2P",
    "%Pts_3P",
    "%Pts_FT",
    "2Pr",
    "3Pr",
    "FTr",
    "ASS_TO_Ratio",
    "AST_Share",
    "ORBr",
    "PFDr",
]

