from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from requests import RequestException

from corn_stats.config import (
    TEAMS_URL,
    RAW_PLAYERS_DATA_PATH,
    PROCESSED_PLAYERS_DATA_PATH,
)
from corn_stats.data import get_team_stats_for_all_players, reorder_player_stats_columns, merge_duplicate_players

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
    raw_df = merge_duplicate_players(
        df=raw_df,
        player_names=["Ivan Fursov", "Fursov Ivan"],
        final_name="Fursov Ivan",
        age_source_name="Ivan Fursov",
    )
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


def render_usage_vs_ts_chart(df: pd.DataFrame) -> None:
    """Scatter plot: Usage Share vs True Shooting %."""
    st.markdown("#### Usage Share vs True Shooting %")
    st.caption(
        "**Usage Share** — player's share of team possessions. Possession ends when player takes a shot, free throw or turns the ball over. Possessions do not include offensive rebounds. \n\n"
        "**TS%** — shooting efficiency accounting for all shot types."
    )

    avg_usage = df["Usage_Share"].mean()
    avg_ts = df["TS%"].mean()

    fig = px.scatter(
        df,
        x="Usage_Share",
        y="TS%",
        hover_data=["Player", "Pts_Tot", "FGA_Tot"],
        labels={"Usage_Share": "Usage Share", "TS%": "True Shooting %"},
        color="TS%",
        color_continuous_scale="RdYlGn",
        size="Pts_Tot",
        text="Player",
    )
    fig.update_traces(
        textposition="top center",
        textfont_size=10,
        marker=dict(line=dict(width=1, color="DarkSlateGrey")),
    )
    fig.add_hline(
        y=avg_ts, line_dash="dash", line_color="gray",
        annotation_text=f"Avg TS%: {avg_ts:.1f}",
    )
    fig.add_vline(
        x=avg_usage, line_dash="dash", line_color="gray",
        annotation_text=f"Avg Usage: {avg_usage:.2f}",
    )
    fig.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig, width="stretch")


def render_shot_distribution_chart(df: pd.DataFrame) -> None:
    """Stacked bar chart: Shot Distribution by Player."""
    st.markdown("#### Shot Distribution")
    st.caption(
        "Points distribution by shot type: 2-pointers, 3-pointers, and free throws. "
        "Shows playing style — who attacks inside vs. from distance."
    )

    shot_cols = ["%Pts_2P", "%Pts_3P", "%Pts_FT"]
    available_cols = [col for col in shot_cols if col in df.columns]
    if not available_cols:
        st.warning("Shot distribution columns not available.")
        return

    fig = px.bar(
        df.sort_values("%Pts_2P", ascending=False),
        x="Player",
        y=available_cols,
        barmode="stack",
        labels={"value": "Percentage of Points", "variable": "Shot Type"},
        color_discrete_map={
            "%Pts_2P": "#1f77b4",
            "%Pts_3P": "#ff7f0e",
            "%Pts_FT": "#2ca02c",
        },
    )
    fig.update_layout(
        height=450,
        xaxis={"tickangle": -45},
        legend={"title": "Point Source"},
    )
    st.plotly_chart(fig, width="stretch")


def render_3pr_vs_3p_percentage_chart(df: pd.DataFrame) -> None:
    """Scatter plot: 3-Point Rate vs 3-Point Percentage."""
    st.markdown("#### 3-Point Rate vs 3-Point Percentage")
    st.caption(
        "**3Pr** — share of 3-point attempts from all field goal attempts. "
        "Dot size — Usage Share. "
        "Compares efficiency across different playing styles."
    )

    avg_3pr = df["3Pr"].mean()
    avg_3p_percentage = df["3P%"].mean()

    fig = px.scatter(
        df,
        x="3Pr",
        y="3P%",
        size="Usage_Share",
        hover_data=["Player", "3PA_Tot", "3PM_Tot", "3P%", "Usage_Share"],
        labels={"3Pr": "3-Point Rate (%)", "3P%": "3-Point Percentage"},
        color="3P%",
        color_continuous_scale="RdYlGn",
        text="Player",
    )
    fig.update_traces(
        textposition="top center",
        textfont_size=10,
        marker=dict(line=dict(width=1, color="DarkSlateGrey")),
    )
    fig.add_hline(
        y=avg_3p_percentage, line_dash="dash", line_color="gray",
        annotation_text=f"Avg 3P%: {avg_3p_percentage:.1f}",
    )
    fig.add_vline(
        x=avg_3pr, line_dash="dash", line_color="gray",
        annotation_text=f"Avg 3Pr: {avg_3pr:.1f}%",
    )
    fig.update_layout(height=500, showlegend=True)
    st.plotly_chart(fig, width="stretch")


def render_ftr_vs_ts_chart(df: pd.DataFrame) -> None:
    """Scatter plot: Free Throw Rate vs True Shooting %."""
    st.markdown("#### Free Throw Rate vs True Shooting %")
    st.caption(
        "**FTr** — free throw attempts per 100 field goal attempts. "
        "Dot size — offensive rebounds. "
        "High FTr indicates aggressive play near the basket."
    )

    avg_ftr = df["FTr"].mean()
    avg_ts = df["TS%"].mean()

    fig = px.scatter(
        df,
        x="FTr",
        y="TS%",
        size="ORB_Tot",
        hover_data=["Player", "FTA_Tot", "FTM_Tot", "FT%", "ORB_Tot", "Usage_Share"],
        labels={"FTr": "Free Throw Rate (%)", "TS%": "True Shooting %"},
        color="TS%",
        color_continuous_scale="RdYlGn",
        text="Player",
    )
    fig.update_traces(
        textposition="top center",
        textfont_size=10,
        marker=dict(line=dict(width=1, color="DarkSlateGrey")),
    )
    fig.add_hline(
        y=avg_ts, line_dash="dash", line_color="gray",
        annotation_text=f"Avg TS%: {avg_ts:.1f}",
    )
    fig.add_vline(
        x=avg_ftr, line_dash="dash", line_color="gray",
        annotation_text=f"Avg FTr: {avg_ftr:.1f}%",
    )
    fig.update_layout(height=500, showlegend=True)
    st.plotly_chart(fig, width="stretch")


def render_usage_vs_ast_to_chart(df: pd.DataFrame) -> None:
    """Scatter plot: Usage Share vs Assist-to-Turnover Ratio."""
    st.markdown("#### Usage Share vs Assist-to-Turnover Ratio")
    st.caption(
        "**ASS_TO_Ratio** — assists to turnovers ratio. "
        "Higher means better ball security. Dot size — total assists."
    )

    avg_usage = df["Usage_Share"].mean()
    avg_ast_to = df["ASS_TO_Ratio"].mean()

    fig = px.scatter(
        df,
        x="Usage_Share",
        y="ASS_TO_Ratio",
        size="AST_Tot",
        hover_data=["Player", "AST_Tot", "AST_Avg", "TO_Tot", "TO_Avg", "Usage_Share"],
        labels={"Usage_Share": "Usage Share", "ASS_TO_Ratio": "Assist-to-Turnover Ratio"},
        color="ASS_TO_Ratio",
        color_continuous_scale="Blues",
        text="Player",
    )
    fig.update_traces(
        textposition="top center",
        textfont_size=10,
        marker=dict(line=dict(width=1, color="DarkSlateGrey")),
    )
    fig.add_hline(
        y=avg_ast_to, line_dash="dash", line_color="gray",
        annotation_text=f"Avg ASS_TO_Ratio: {avg_ast_to:.2f}",
    )
    fig.add_vline(
        x=avg_usage, line_dash="dash", line_color="gray",
        annotation_text=f"Avg Usage: {avg_usage:.2f}",
    )
    fig.update_layout(height=500, showlegend=True)
    st.plotly_chart(fig, width="stretch")


def render_usage_vs_ast_share_chart(df: pd.DataFrame) -> None:
    """Scatter plot: Usage Share vs Assist Share."""
    st.markdown("#### Usage Share vs Assist Share")
    st.caption(
        "**AST Share** — player's share of team assists. "
        "Shows who is the primary playmaker on the team."
    )

    avg_usage = df["Usage_Share"].mean()
    avg_ast_share = df["AST_Share"].mean()

    fig = px.scatter(
        df,
        x="Usage_Share",
        y="AST_Share",
        size="AST_Tot",
        hover_data=["Player", "AST_Tot", "AST_Share", "Usage_Share"],
        labels={"Usage_Share": "Usage Share", "AST_Share": "Assist Share"},
        color="AST_Share",
        color_continuous_scale="Blues",
        text="Player",
    )
    fig.update_traces(
        textposition="top center",
        textfont_size=10,
        marker=dict(line=dict(width=1, color="DarkSlateGrey")),
    )
    fig.add_hline(
        y=avg_ast_share, line_dash="dash", line_color="gray",
        annotation_text=f"Avg AST Share: {avg_ast_share:.2f}",
    )
    fig.add_vline(
        x=avg_usage, line_dash="dash", line_color="gray",
        annotation_text=f"Avg Usage: {avg_usage:.2f}",
    )
    fig.update_layout(height=500, showlegend=True)
    st.plotly_chart(fig, width="stretch")


def main() -> None:
    st.set_page_config(page_title="Corn Liga – Player Dashboard", layout="wide")
    st.title("Player Dashboard")
    
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

    # Charts section
    st.divider()
    st.subheader("Charts")
    
    render_usage_vs_ts_chart(player_stats)
    render_shot_distribution_chart(player_stats)
    render_3pr_vs_3p_percentage_chart(player_stats)
    render_ftr_vs_ts_chart(player_stats)
    render_usage_vs_ast_to_chart(player_stats)
    render_usage_vs_ast_share_chart(player_stats)


if __name__ == "__main__":
    main()

