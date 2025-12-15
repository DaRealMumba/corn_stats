from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from requests import RequestException

from corn_stats.config import (
    TABLES_DATA_PATH,
    TABLE_URL,
    TEAMS,
    RAW_TEAMS_DATA_PATH,
    PROCESSED_TEAMS_DATA_PATH,
    TEAMS_URL,
    TEAM_STATS_COLUMN_ORDER,
)
from corn_stats.data import get_league_table, parse_team_page_wide
from corn_stats.features import calculate_all_advanced_stats
from corn_stats.ui import render_glossary
from corn_stats.viz import scatter_with_logos_plotly

LEAGUE_TABLE_FILE = TABLES_DATA_PATH / "north_liga_df.csv"
RAW_TEAM_STATS_FILE = RAW_TEAMS_DATA_PATH / "raw_teams_stats.csv"
ADV_TEAM_STATS_FILE = PROCESSED_TEAMS_DATA_PATH / "all_teams_stats.csv"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def reorder_team_stats_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Reorder columns in team stats DataFrame according to TEAM_STATS_COLUMN_ORDER."""
    df = df.copy()
    ordered_cols = [col for col in TEAM_STATS_COLUMN_ORDER if col in df.columns]
    remaining_cols = [col for col in df.columns if col not in TEAM_STATS_COLUMN_ORDER]
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


def main() -> None:
    st.set_page_config(page_title="Corn Liga – Team Dashboard", layout="wide")
    st.title("Team Dashboard")

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
    except RequestException as exc:
        st.error(f"Failed to download league table: {exc}")
        return

    try:
        team_stats = load_team_stats(
            league_df,
            force_refresh=refresh_teams or refresh_league,
        )
        team_stats = reorder_team_stats_columns(team_stats)
    except RequestException as exc:
        st.error(f"Failed to download team statistics: {exc}")
        return
    except ValueError as exc:
        st.error(f"Unable to compute team statistics: {exc}")
        return

    # 1. Pace of teams
    st.subheader("1. Pace of Teams")
    pace_sorted = team_stats.sort_values("Pace", ascending=True)
    fig_pace = px.bar(
        pace_sorted,
        x="Pace",
        y="Team",
        orientation="h",
        color="Pace",
        title="Pace (Possessions per Game)",
        color_continuous_scale="Blues",
        hover_data=["Net_Rating", "Off_Rating", "Def_Rating"],
    )
    fig_pace.update_layout(height=500, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_pace, width="stretch") 

    # 2. Points vs FG%
    st.subheader("2. Points vs Field Goal %")
    # Use Pts_Scored_Avg for points per game, or Scored for total
    points_col = "Pts_Scored_Avg" if "Pts_Scored_Avg" in team_stats.columns else "Scored"
    fig_points_fg = scatter_with_logos_plotly(
        team_stats,
        x=points_col,
        y="FG%",
        logo_size_factor=0.15,
        title="Points vs Field Goal Percentage",
        hover_data=["Team", "FGM_Tot", "FGA_Tot", "eFG%", "TS%"],
    )
    st.plotly_chart(fig_points_fg, width="stretch")

    # 3. Shooting Strategy: 2-Point vs 3-Point Attempts
    st.subheader("3. Shooting Strategy: 2-Point vs 3-Point Attempts")
    fig_shooting_strategy = scatter_with_logos_plotly(
        team_stats,
        x="2PA_Avg",
        y="3PA_Avg",
        logo_size_factor=0.15,
        title="Shooting Strategy: 2-Point vs 3-Point Attempts per Game",
        hover_data=["Team", "2P%", "3P%", "%Pts_2P", "%Pts_3P"],
    )
    st.plotly_chart(fig_shooting_strategy, width="stretch")

    # 4. Free Throw Frequency vs Efficiency
    st.subheader("4. Free Throw Frequency vs Efficiency")
    # Calculate FTA per game for frequency
    if "FTA_Avg" in team_stats.columns:
        fig_ft = scatter_with_logos_plotly(
            team_stats,
            x="FTA_Avg",
            y="FT%",
            logo_size_factor=0.15,
            title="Free Throw Frequency vs Efficiency",
            hover_data=["Team", "FTM_Avg", "FTr", "%Pts_FT"],
        )
        st.plotly_chart(fig_ft, width="stretch")

    # 5. Shot Distribution by Team
    st.subheader("5. Shot Distribution by Team")
    shot_dist_cols = ["%Pts_2P", "%Pts_3P", "%Pts_FT"]
    available_shot_cols = [col for col in shot_dist_cols if col in team_stats.columns]
    
    if available_shot_cols:
        shot_dist_sorted = team_stats.sort_values("%Pts_2P", ascending=False)
        fig_shot_dist = px.bar(
            shot_dist_sorted,
            x="Team",
            y=available_shot_cols,
            title="Shot Distribution by Team (% of Total Points)",
            barmode="stack",
            labels={"value": "Percentage of Points", "variable": "Shot Type"},
            color_discrete_map={
                "%Pts_2P": "#1f77b4",
                "%Pts_3P": "#ff7f0e",
                "%Pts_FT": "#2ca02c",
            },
        )
        fig_shot_dist.update_layout(
            height=500,
            xaxis={"tickangle": -45},
            legend={"title": "Point Source"},
        )
        st.plotly_chart(fig_shot_dist, width="stretch")

    # 6. Rebounding Profile: Offensive vs Defensive Rebound %
    st.subheader("6. Rebounding Profile: Offensive vs Defensive Rebound %")
    fig_rebounds = scatter_with_logos_plotly(
        team_stats,
        x="ORB%",
        y="DRB%",
        logo_size_factor=0.15,
        title="Rebounding Profile: Offensive vs Defensive Rebound %",
        hover_data=["Team", "ORB_Tot", "DRB_Tot", "TRB_Tot", "TRB_Avg"],
    )
    st.plotly_chart(fig_rebounds, width="stretch")

    # 7. Teams by Net Rating
    st.subheader("7. Teams by Net Rating")
    net_rating_sorted = team_stats.sort_values("Net_Rating", ascending=True)
    fig_net_rating = px.bar(
        net_rating_sorted,
        x="Net_Rating",
        y="Team",
        orientation="h",
        color="Net_Rating",
        title="Teams by Net Rating",
        color_continuous_scale="RdYlGn",
        hover_data=["Off_Rating", "Def_Rating", "Win%"],
    )
    fig_net_rating.update_layout(height=500, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_net_rating, width="stretch")


if __name__ == "__main__":
    main()

