from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st
from requests import RequestException

from corn_stats.config import (
    TABLES_DATA_PATH,
    TABLE_URL,
    TEAMS,
    TEAMS_DATA_PATH,
    TEAMS_URL,
    TEAM_STATS_COLUMN_ORDER,
)
from corn_stats.data import get_league_table, parse_team_page_wide
from corn_stats.features import calculate_all_advanced_stats
from corn_stats.viz import scatter_with_logos_plotly

LEAGUE_TABLE_FILE = TABLES_DATA_PATH / "north_liga_df.csv"
RAW_TEAM_STATS_FILE = TEAMS_DATA_PATH / "raw_teams_stats.csv"
ADV_TEAM_STATS_FILE = TEAMS_DATA_PATH / "all_teams_stats.csv"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def reorder_team_stats_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Reorder columns in team stats DataFrame according to TEAM_STATS_COLUMN_ORDER.
    
    Columns not in the order list will be appended at the end.
    """
    df = df.copy()
    
    # Get columns that exist in DataFrame
    ordered_cols = [col for col in TEAM_STATS_COLUMN_ORDER if col in df.columns]
    
    # Get remaining columns (not in order list)
    remaining_cols = [col for col in df.columns if col not in TEAM_STATS_COLUMN_ORDER]
    
    # Reorder: ordered columns first, then remaining
    return df[ordered_cols + remaining_cols]


@st.cache_data(show_spinner=False)
def load_league_table(force_refresh: bool = False) -> pd.DataFrame:
    if force_refresh or not LEAGUE_TABLE_FILE.exists():
        _ensure_parent(LEAGUE_TABLE_FILE)
        df = get_league_table(TABLE_URL)
        df.to_csv(LEAGUE_TABLE_FILE, index=True)
        return df

    df = pd.read_csv(LEAGUE_TABLE_FILE, index_col=0)
    df.index.name = "Position"
    return df


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
        title="Offensive vs Defensive Rating",
        hover_data=["Net_Rating"],
    )
    st.plotly_chart(fig, width="stretch")


def render_glossary() -> None:
    """Render glossary of metrics and columns in the same order as TEAM_STATS_COLUMN_ORDER."""
    st.markdown("### Glossary")
    
    # All metric descriptions
    glossary_all = {
        # Basic info
        "Team": "Team name",
        "Abbr": "Team abbreviation",
        # League standings
        "Position": "Team's position in the league standings (1-12)",
        "Points": "Total points in the league",
        "Wins": "Number of wins",
        "Losses": "Number of losses",
        "Games": "Total games played",
        "Win_%": "Win percentage",
        "Scored": "Total points scored",
        "Allowed": "Total points allowed",
        "Points_Diff": "Point differential (Scored - Allowed)",
        "Pts_Scored_Avg": "Average points scored per game",
        "Pts_Allowed_Avg": "Average points allowed per game",
        "Pts_Diff_Avg": "Average points differential per game",
        # Shooting percentages
        "FG%": "Field goal percentage",
        "2P%": "2-point field goal percentage",
        "3P%": "3-point field goal percentage",
        "FT%": "Free throw percentage",
        "eFG_%": "Effective field goal percentage - accounts for 3-pointers being worth more",
        "TS_%": "True shooting percentage - accounts for 2-pointers, 3-pointers, and free throws",
        # Shot distribution
        "%Pts_2P": "Percentage of points scored from 2-pointers",
        "%Pts_3P": "Percentage of points scored from 3-pointers",
        "%Pts_FT": "Percentage of points scored from free throws",
        "2Pr": "2-point shot rate",
        "3Pr": "3-point shot rate",
        "FTr": "Free throw shot rate",
        # Totals (shooting)
        "FGM_Tot": "Total field goals made",
        "FGA_Tot": "Total field goals attempted",
        "2PM_Tot": "Total 2-point field goals made",
        "2PA_Tot": "Total 2-point field goals attempted",
        "3PM_Tot": "Total 3-point field goals made",
        "3PA_Tot": "Total 3-point field goals attempted",
        "FTM_Tot": "Total free throws made",
        "FTA_Tot": "Total free throws attempted",
        # Averages (shooting)
        "FGM_Avg": "Average field goals made per game",
        "FGA_Avg": "Average field goals attempted per game",
        "2PM_Avg": "Average 2-point field goals made per game",
        "2PA_Avg": "Average 2-point field goals attempted per game",
        "3PM_Avg": "Average 3-point field goals made per game",
        "3PA_Avg": "Average 3-point field goals attempted per game",
        "FTM_Avg": "Average free throws made per game",
        "FTA_Avg": "Average free throws attempted per game",
        # Rebounds
        "ORB_Tot": "Total offensive rebounds",
        "DRB_Tot": "Total defensive rebounds",
        "TRB_Tot": "Total rebounds",
        "ORB_Avg": "Average offensive rebounds per game",
        "DRB_Avg": "Average defensive rebounds per game",
        "TRB_Avg": "Average total rebounds per game",
        "ORB_%": "Offensive rebound percentage",
        "DRB_%": "Defensive rebound percentage",
        # Other stats
        "AST_Tot": "Total assists",
        "AST_Avg": "Average assists per game",
        "TO_Tot": "Total turnovers",
        "TO_Avg": "Average turnovers per game",
        "STL_Tot": "Total steals",
        "STL_Avg": "Average steals per game",
        "BLK_Tot": "Total blocks",
        "BLK_Avg": "Average blocks per game",
        "PFD_Tot": "Total personal fouls",
        "PFD_Avg": "Average personal fouls per game",
        # Advanced metrics
        "POSS_Tot": "Total possessions: FGA_Tot - ORB_Tot + TO_Tot + 0.44 * FTA_Tot",
        "Pace": "Possessions per game",
        "Off_Rating": "Offensive rating - points scored per 100 possessions: Scored / POSS_Tot * 100",
        "Def_Rating": "Defensive rating - points allowed per 100 possessions: Allowed / POSS_Tot * 100",
        "Net_Rating": "Net rating - difference between offensive and defensive rating",
        "TO_%": "Turnover percentage - turnovers per 100 possessions",
        "AST_Rate": "Assist rate - assists per field goals made per 100 possessions",
        "STL_Rate": "Steal rate - steals per 100 possessions",
        "BLK_Rate": "Block rate - blocks per 100 possessions",
        "PFD_Rate": "Personal foul rate - fouls per 100 possessions",
        "ASS_TO_Ratio": "Assist-to-turnover ratio",
    }
    
    # Render metrics in the same order as TEAM_STATS_COLUMN_ORDER
    for metric in TEAM_STATS_COLUMN_ORDER:
        if metric in glossary_all:
            st.markdown(f"**{metric}**: {glossary_all[metric]}")
    
    # Show any remaining metrics not in TEAM_STATS_COLUMN_ORDER (if any)
    remaining = {k: v for k, v in glossary_all.items() if k not in TEAM_STATS_COLUMN_ORDER}
    if remaining:
        st.markdown("#### Other Metrics")
        for metric, description in remaining.items():
            st.markdown(f"**{metric}**: {description}")


def main() -> None:
    st.set_page_config(page_title="Corn Liga – North", layout="wide")
    st.title("Corn Liga North – Team Dashboard")
    
    # Description
    st.markdown("""
    This is an analytics dashboard for the amateur Serbian basketball league North Division. 
    Data is sourced from [cornliga.com](https://cornliga.com).
    """)
    
    with st.sidebar:
        st.header("Data controls")
        refresh_league = st.button("Refresh league table")
        refresh_teams = st.button("Refresh team stats")
        
        st.divider()
        
        with st.expander("📖 Glossary", expanded=False):
            render_glossary()

    if refresh_league:
        load_league_table.clear()
        load_team_stats.clear()
    elif refresh_teams:
        load_team_stats.clear()

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
        # Reorder columns for better readability
        team_stats = reorder_team_stats_columns(team_stats)
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
