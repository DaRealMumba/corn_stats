from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st
from requests import RequestException

from corn_stats.config import (
    LOGO_DIR,
    TABLES_DATA_PATH,
    TABLE_URL,
    TEAMS,
    TEAMS_DATA_PATH,
    TEAMS_URL,
)
from corn_stats.data import get_league_table, parse_team_page_wide
from corn_stats.features import calculate_all_advanced_stats
from corn_stats.viz import scatter_with_logos_plotly

LEAGUE_TABLE_FILE = TABLES_DATA_PATH / "north_liga_df.csv"
RAW_TEAM_STATS_FILE = TEAMS_DATA_PATH / "raw_teams_stats.csv"
ADV_TEAM_STATS_FILE = TEAMS_DATA_PATH / "all_teams_stats.csv"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@st.cache_data(show_spinner=False)
def load_league_table(force_refresh: bool = False) -> pd.DataFrame:
    if force_refresh or not LEAGUE_TABLE_FILE.exists():
        _ensure_parent(LEAGUE_TABLE_FILE)
        df = get_league_table(TABLE_URL)
        df.to_csv(LEAGUE_TABLE_FILE, index=False)
        return df

    return pd.read_csv(LEAGUE_TABLE_FILE)


@st.cache_data(show_spinner=False)
def load_team_stats(
    league_df: pd.DataFrame, *, force_refresh: bool = False
) -> pd.DataFrame:
    if not force_refresh and ADV_TEAM_STATS_FILE.exists():
        return pd.read_csv(ADV_TEAM_STATS_FILE)

    _ensure_parent(RAW_TEAM_STATS_FILE)

    frames: list[pd.DataFrame] = []
    for slug in TEAMS:
        team_url = f"{TEAMS_URL}/{slug}"
        team_df = parse_team_page_wide(team_url, league_df)
        frames.append(team_df)

    raw_df = pd.concat(frames, ignore_index=True)
    raw_df.to_csv(RAW_TEAM_STATS_FILE, index=False)

    advanced_df = calculate_all_advanced_stats(
        league_df.merge(
            raw_df.drop(columns=["Team"]),
            on="Abbr",
            how="inner",
        )
    )
    advanced_df.to_csv(ADV_TEAM_STATS_FILE, index=False)
    return advanced_df


def render_team_summary(df: pd.DataFrame, *, team_names: Iterable[str]) -> None:
    if df.empty:
        st.info("No team statistics available yet.")
        return

    team_name = st.selectbox("Select team", sorted(team_names))
    team_row = df[df["Team"] == team_name]
    if team_row.empty:
        st.warning("Team data not found. Try refreshing the dataset.")
        return

    st.subheader(team_row.iloc[0]["Team"])
    st.dataframe(
        team_row.drop(columns=["Abbr"]).set_index("Team").T,
        width="content",
    )


def render_ratings_chart(df: pd.DataFrame) -> None:
    required = {"Off_Rating", "Def_Rating", "Team"}
    if not required.issubset(df.columns):
        st.info("Ratings scatter plot becomes available after advanced stats are computed.")
        return

    fig = scatter_with_logos_plotly(
        df,
        x="Off_Rating",
        y="Def_Rating",
        logo_size_factor=0.15,
        # team_col="Team",
        title="Offensive vs Defensive Rating",
        # logo_dirs=[LOGO_DIR],
        hover_data=["Net_Rating"],
    )
    st.plotly_chart(fig, width="stretch")


def main() -> None:
    st.set_page_config(page_title="Corn Liga – North", layout="wide")
    st.title("Corn Liga North – Team Dashboard")

    with st.sidebar:
        st.header("Data controls")
        refresh_league = st.button("Refresh league table")
        refresh_teams = st.button("Refresh team stats")

    try:
        league_df = load_league_table(force_refresh=refresh_league)
        st.success(f"League table loaded ({len(league_df)} teams).")
    except RequestException as exc:
        st.error(f"Failed to download league table: {exc}")
        return

    st.subheader("League standings")
    st.dataframe(league_df, width="stretch")

    try:
        team_stats = load_team_stats(
            league_df,
            force_refresh=refresh_teams or refresh_league,
        )
    except RequestException as exc:
        st.error(f"Failed to download team statistics: {exc}")
        return
    except ValueError as exc:
        st.error(f"Unable to compute team statistics: {exc}")
        return

    with st.expander("Download data", expanded=False):
        st.download_button(
            "League table (CSV)",
            data=league_df.to_csv(index=False).encode("utf-8"),
            file_name="north_liga_table.csv",
            mime="text/csv",
        )
        st.download_button(
            "Team stats (CSV)",
            data=team_stats.to_csv(index=False).encode("utf-8"),
            file_name="north_liga_team_stats.csv",
            mime="text/csv",
        )

    st.subheader("Team details")
    render_team_summary(team_stats, team_names=team_stats["Team"].unique())

    st.subheader("Advanced metrics")
    render_ratings_chart(team_stats)


if __name__ == "__main__":
    main()
