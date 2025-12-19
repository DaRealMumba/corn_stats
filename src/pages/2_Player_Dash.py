from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from requests import RequestException

from corn_stats.config import (
    TEAMS_URL,
    RAW_PLAYERS_DATA_PATH,
    PROCESSED_PLAYERS_DATA_PATH,
)
from corn_stats.data import get_team_stats_for_all_players, reorder_player_stats_columns

RAVENS_URL = f"{TEAMS_URL}/ravens-belgrade/roster"
from corn_stats.features import calculate_players_advanced_stats
from corn_stats.ui import render_glossary

RAW_PLAYERS_FILE = RAW_PLAYERS_DATA_PATH / "ravens_players_stats.csv"
ADV_PLAYERS_FILE = PROCESSED_PLAYERS_DATA_PATH / "ravens_players_advanced_stats.csv"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@st.cache_data(show_spinner=False)
def load_player_stats(*, force_refresh: bool = False) -> pd.DataFrame:
    """Load player statistics from Ravens Belgrade."""
    if not force_refresh and ADV_PLAYERS_FILE.exists():
        return pd.read_csv(ADV_PLAYERS_FILE)

    _ensure_parent(RAW_PLAYERS_FILE)

    raw_df = get_team_stats_for_all_players(RAVENS_URL)
    raw_df.to_csv(RAW_PLAYERS_FILE, index=False)

    advanced_df = calculate_players_advanced_stats(raw_df)
    _ensure_parent(ADV_PLAYERS_FILE)
    advanced_df.to_csv(ADV_PLAYERS_FILE, index=False)
    return advanced_df


def render_player_table(df: pd.DataFrame) -> None:
    """Render player statistics table."""
    if df.empty:
        st.info("No player statistics available yet.")
        return

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
    )


def main() -> None:
    st.set_page_config(page_title="Corn Liga – Player Dashboard", layout="wide")
    st.title("Player Dashboard – Ravens Belgrade")
    
    # Description
    st.markdown("""
    This page contains statistics for the Ravens Belgrade players. In next releases will be added players statistics for other teams.
    
    Information about metrics is available in the glossary.
    
    Source: [cornliga.com](https://cornliga.com/seasons/2025-26/leagues/north-liga/teams/ravens-belgrade/roster)
    """)

    with st.sidebar:
        st.header("Data controls")
        refresh_players = st.button("Refresh player stats")

        st.divider()

        with st.expander("📖 Glossary", expanded=False):
            render_glossary()

    if refresh_players:
        load_player_stats.clear()

    try:
        with st.spinner("Loading player statistics..."):
            player_stats = load_player_stats(force_refresh=refresh_players)
        player_stats = reorder_player_stats_columns(player_stats)
        st.success(f"Loaded statistics for {len(player_stats)} players.")
    except RequestException as exc:
        st.error(f"Failed to download player statistics: {exc}")
        return
    except ValueError as exc:
        st.error(f"Unable to load player statistics: {exc}")
        return

    # Download button
    with st.expander("Download data", expanded=False):
        st.download_button(
            "Player stats (CSV)",
            data=player_stats.to_csv(index=False).encode("utf-8"),
            file_name="ravens_player_advanced_stats.csv",
            mime="text/csv",
        )

    # Player statistics table
    st.subheader("Player Statistics")
    render_player_table(player_stats)

    # Placeholder for future charts
    st.divider()
    st.subheader("Charts")
    st.info("📊 Charts coming soon...")


if __name__ == "__main__":
    main()

