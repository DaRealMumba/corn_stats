from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"

RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

TABLES_DATA_PATH = RAW_DATA_DIR / "tables"
TEAMS_DATA_PATH = RAW_DATA_DIR / "teams"
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

