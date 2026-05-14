from __future__ import annotations

from pathlib import Path
from typing import Any

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
from corn_stats.features import calculate_players_advanced_stats
from corn_stats.ui import render_glossary


TEAMS_CONFIG: dict[str, dict[str, Any]] = {
    "Ravens": {
        "slug": "ravens-belgrade",
        "raw_file": RAW_PLAYERS_DATA_PATH / "ravens_players_stats.csv",
        "adv_file": PROCESSED_PLAYERS_DATA_PATH / "ravens_players_advanced_stats.csv",
        "color": "#7c3aed",
        "merges": [
            {
                "player_names": ["Ivan Fursov", "Fursov Ivan"],
                "final_name": "Fursov Ivan",
                "age_source_name": "Ivan Fursov",
            },
            {
                "player_names": ["Fursov Mikhail"],
                "final_name": "Fursov Mikhail",
            },
        ],
    },
    "Bulls": {
        "slug": "belgrade-bulls",
        "raw_file": RAW_PLAYERS_DATA_PATH / "bulls_players_stats.csv",
        "adv_file": PROCESSED_PLAYERS_DATA_PATH / "bulls_players_advanced_stats.csv",
        "color": "#dc2626",
        "merges": [],
    },
}

TEAM_COLOR_MAP = {name: cfg["color"] for name, cfg in TEAMS_CONFIG.items()}


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@st.cache_data(show_spinner=False)
def load_team_players(team_name: str, *, force_refresh: bool = False) -> pd.DataFrame:
    """Load player statistics for a single team, tagged with a Team column."""
    cfg = TEAMS_CONFIG[team_name]
    adv_file: Path = cfg["adv_file"]
    raw_file: Path = cfg["raw_file"]

    if not force_refresh and adv_file.exists():
        df = pd.read_csv(adv_file)
        df["Team"] = team_name
        return df

    _ensure_parent(raw_file)

    raw_df = get_team_stats_for_all_players(f"{TEAMS_URL}/{cfg['slug']}/roster")
    for merge in cfg["merges"]:
        raw_df = merge_duplicate_players(df=raw_df, **merge)
    raw_df.to_csv(raw_file, index=False)

    advanced_df = calculate_players_advanced_stats(raw_df)
    _ensure_parent(adv_file)
    advanced_df.to_csv(adv_file, index=False)
    advanced_df["Team"] = team_name
    return advanced_df


def render_player_table(df: pd.DataFrame, *, show_team: bool) -> None:
    """Render player statistics table."""
    if df.empty:
        st.info("No player statistics available yet.")
        return

    column_config = {
        "Player": st.column_config.TextColumn("Player", pinned="left"),
    }
    if show_team:
        column_config["Team"] = st.column_config.TextColumn("Team", pinned="left")

    st.dataframe(
        df,
        column_config=column_config,
        width="stretch",
        hide_index=True,
    )


def _color_kwargs(df: pd.DataFrame, metric_col: str, *, color_by_team: bool) -> dict[str, Any]:
    """Build color-related px.scatter kwargs depending on display mode."""
    if color_by_team:
        return {
            "color": "Team",
            "color_discrete_map": TEAM_COLOR_MAP,
        }
    return {
        "color": metric_col,
        "color_continuous_scale": "RdYlGn",
    }


def render_usage_vs_ts_chart(df: pd.DataFrame, *, color_by_team: bool) -> None:
    """Scatter plot: Usage Share vs True Shooting %."""
    st.markdown("#### Usage Share vs True Shooting %")
    caption = (
        "**Usage Share** — player's share of team possessions. Possession ends when player takes a shot, free throw or turns the ball over. Possessions do not include offensive rebounds. \n\n"
        "**TS%** — shooting efficiency accounting for all shot types."
    )
    if color_by_team:
        caption += "\n\n_Usage Share normalised within each team — values are not directly comparable across teams._"
    st.caption(caption)

    avg_usage = df["Usage_Share"].mean()
    avg_ts = df["TS%"].mean()

    fig = px.scatter(
        df,
        x="Usage_Share",
        y="TS%",
        hover_data=["Player", "Team", "Pts_Tot", "FGA_Tot"],
        labels={"Usage_Share": "Usage Share", "TS%": "True Shooting %"},
        size="Pts_Tot",
        text="Player",
        **_color_kwargs(df, "TS%", color_by_team=color_by_team),
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
    fig.update_layout(height=500, showlegend=color_by_team)
    st.plotly_chart(fig, width="stretch")


def render_shot_distribution_chart(df: pd.DataFrame, *, color_by_team: bool) -> None:
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

    sorted_df = df.sort_values(["Team", "%Pts_2P"] if color_by_team else "%Pts_2P", ascending=[True, False] if color_by_team else False)

    fig = px.bar(
        sorted_df,
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


def render_3pr_vs_3p_percentage_chart(df: pd.DataFrame, *, color_by_team: bool) -> None:
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
        hover_data=["Player", "Team", "3PA_Tot", "3PM_Tot", "3P%", "Usage_Share"],
        labels={"3Pr": "3-Point Rate (%)", "3P%": "3-Point Percentage"},
        text="Player",
        **_color_kwargs(df, "3P%", color_by_team=color_by_team),
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


def render_ftr_vs_ts_chart(df: pd.DataFrame, *, color_by_team: bool) -> None:
    """Scatter plot: Free Throw Rate vs Free Throw Percentage %."""
    st.markdown("#### Free Throw Rate vs Free Throw Percentage %")
    st.caption(
        "**FTr** — free throw attempts per 100 field goal attempts. "
        "Dot size — FTr. "
        "High FTr indicates aggressive play near the basket."
    )

    avg_ftr = df["FTr"].mean()
    avg_ft_percentage = df["FT%"].mean()
    fig = px.scatter(
        df,
        x="FTr",
        y="FT%",
        size="FTr",
        hover_data=["Player", "Team", "FTA_Tot", "FTM_Tot", "FT%", "Usage_Share"],
        labels={"FTr": "Free Throw Rate (%)", "FT%": "Free Throw Percentage"},
        text="Player",
        **_color_kwargs(df, "FT%", color_by_team=color_by_team),
    )
    fig.update_traces(
        textposition="top center",
        textfont_size=10,
        marker=dict(line=dict(width=1, color="DarkSlateGrey")),
    )
    fig.add_hline(
        y=avg_ft_percentage, line_dash="dash", line_color="gray",
        annotation_text=f"Avg FT%: {avg_ft_percentage:.1f}",
    )
    fig.add_vline(
        x=avg_ftr, line_dash="dash", line_color="gray",
        annotation_text=f"Avg FTr: {avg_ftr:.1f}%",
    )
    fig.update_layout(height=500, showlegend=True)
    st.plotly_chart(fig, width="stretch")


def render_usage_vs_ast_to_chart(df: pd.DataFrame, *, color_by_team: bool) -> None:
    """Scatter plot: Usage Share vs Assist-to-Turnover Ratio."""
    st.markdown("#### Usage Share vs Assist-to-Turnover Ratio")
    caption = (
        "**ASS_TO_Ratio** — assists to turnovers ratio. "
        "Higher means better ball security. Dot size — total assists."
    )
    if color_by_team:
        caption += "\n\n_Usage Share normalised within each team — values are not directly comparable across teams._"
    st.caption(caption)

    avg_usage = df["Usage_Share"].mean()
    avg_ast_to = df["ASS_TO_Ratio"].mean()

    if color_by_team:
        color_kw = {"color": "Team", "color_discrete_map": TEAM_COLOR_MAP}
    else:
        color_kw = {"color": "ASS_TO_Ratio", "color_continuous_scale": "Blues"}

    fig = px.scatter(
        df,
        x="Usage_Share",
        y="ASS_TO_Ratio",
        size="AST_Tot",
        hover_data=["Player", "Team", "AST_Tot", "AST_Avg", "TO_Tot", "TO_Avg", "Usage_Share"],
        labels={"Usage_Share": "Usage Share", "ASS_TO_Ratio": "Assist-to-Turnover Ratio"},
        text="Player",
        **color_kw,
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


def render_usage_vs_ast_share_chart(df: pd.DataFrame, *, color_by_team: bool) -> None:
    """Scatter plot: Usage Share vs Assist Share."""
    st.markdown("#### Usage Share vs Assist Share")
    caption = (
        "**AST Share** — player's share of team assists. "
        "Shows who is the primary playmaker on the team."
    )
    if color_by_team:
        caption += "\n\n_Usage Share and AST Share are both normalised within each team — values are not directly comparable across teams._"
    st.caption(caption)

    avg_usage = df["Usage_Share"].mean()
    avg_ast_share = df["AST_Share"].mean()

    if color_by_team:
        color_kw = {"color": "Team", "color_discrete_map": TEAM_COLOR_MAP}
    else:
        color_kw = {"color": "AST_Share", "color_continuous_scale": "Blues"}

    fig = px.scatter(
        df,
        x="Usage_Share",
        y="AST_Share",
        size="AST_Tot",
        hover_data=["Player", "Team", "AST_Tot", "AST_Share", "Usage_Share"],
        labels={"Usage_Share": "Usage Share", "AST_Share": "Assist Share"},
        text="Player",
        **color_kw,
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


def render_top_scorers_chart(df: pd.DataFrame, *, color_by_team: bool) -> None:
    """Horizontal bar chart: Players sorted by points per game."""
    st.markdown("#### Top Scorers (Points per Game)")
    st.caption(
        "Players sorted by points per game. "
        "Color shows shooting efficiency (eFG%) — high points + high eFG% = high impact."
    )

    sorted_df = df.sort_values("Pts_Avg", ascending=True)

    if color_by_team:
        color_kw: dict[str, Any] = {"color": "Team", "color_discrete_map": TEAM_COLOR_MAP}
    else:
        color_kw = {"color": "eFG%", "color_continuous_scale": "RdYlGn"}

    fig = px.bar(
        sorted_df,
        x="Pts_Avg",
        y="Player",
        orientation="h",
        hover_data=["Team", "Pts_Tot", "Games", "FG%", "eFG%", "TS%"],
        labels={"Pts_Avg": "Points per Game", "Player": ""},
        **color_kw,
    )
    fig.update_layout(
        height=max(400, 28 * len(sorted_df)),
        yaxis={"categoryorder": "total ascending"},
        showlegend=color_by_team,
    )
    st.plotly_chart(fig, width="stretch")


def render_efficiency_vs_usage_chart(df: pd.DataFrame, *, color_by_team: bool) -> None:
    """Scatter plot: Efficiency Rating vs Usage Share."""
    st.markdown("#### Efficiency Rating vs Usage Share")
    caption = (
        "**Eff** — composite per-game efficiency (points + rebounds + assists + "
        "steals + blocks − missed shots − turnovers). "
        "Dot size — points per game. Top-right = high-volume + high-impact players."
    )
    if color_by_team:
        caption += "\n\n_Usage Share normalised within each team — values are not directly comparable across teams._"
    st.caption(caption)

    avg_usage = df["Usage_Share"].mean()
    avg_eff = df["Eff_Avg"].mean()

    fig = px.scatter(
        df,
        x="Usage_Share",
        y="Eff_Avg",
        size="Pts_Avg",
        hover_data=["Player", "Team", "Eff_Tot", "Pts_Avg", "Pts_Tot", "Usage_Share"],
        labels={"Usage_Share": "Usage Share", "Eff_Avg": "Efficiency / Game"},
        text="Player",
        **_color_kwargs(df, "Eff_Avg", color_by_team=color_by_team),
    )
    fig.update_traces(
        textposition="top center",
        textfont_size=10,
        marker=dict(line=dict(width=1, color="DarkSlateGrey")),
    )
    fig.add_hline(
        y=avg_eff, line_dash="dash", line_color="gray",
        annotation_text=f"Avg Eff: {avg_eff:.1f}",
    )
    fig.add_vline(
        x=avg_usage, line_dash="dash", line_color="gray",
        annotation_text=f"Avg Usage: {avg_usage:.2f}",
    )
    fig.update_layout(height=500, showlegend=True)
    st.plotly_chart(fig, width="stretch")


def render_2pr_vs_2p_percentage_chart(df: pd.DataFrame, *, color_by_team: bool) -> None:
    """Scatter plot: 2-Point Rate vs 2-Point Percentage."""
    st.markdown("#### 2-Point Rate vs 2-Point Percentage")
    st.caption(
        "**2Pr** — share of 2-point attempts from all field goal attempts. "
        "Dot size — Usage Share. "
        "Compares interior efficiency across different playing styles."
    )

    avg_2pr = df["2Pr"].mean()
    avg_2p_percentage = df["2P%"].mean()

    fig = px.scatter(
        df,
        x="2Pr",
        y="2P%",
        size="Usage_Share",
        hover_data=["Player", "Team", "2PA_Tot", "2PM_Tot", "2P%", "Usage_Share"],
        labels={"2Pr": "2-Point Rate (%)", "2P%": "2-Point Percentage"},
        text="Player",
        **_color_kwargs(df, "2P%", color_by_team=color_by_team),
    )
    fig.update_traces(
        textposition="top center",
        textfont_size=10,
        marker=dict(line=dict(width=1, color="DarkSlateGrey")),
    )
    fig.add_hline(
        y=avg_2p_percentage, line_dash="dash", line_color="gray",
        annotation_text=f"Avg 2P%: {avg_2p_percentage:.1f}",
    )
    fig.add_vline(
        x=avg_2pr, line_dash="dash", line_color="gray",
        annotation_text=f"Avg 2Pr: {avg_2pr:.1f}%",
    )
    fig.update_layout(height=500, showlegend=True)
    st.plotly_chart(fig, width="stretch")


def render_rebounding_chart(df: pd.DataFrame, *, color_by_team: bool) -> None:
    """Scatter plot: Offensive vs Defensive rebounds per game."""
    st.markdown("#### Rebounding Profile: ORB vs DRB per Game")
    st.caption(
        "**ORB** — offensive rebounds per game. **DRB** — defensive rebounds per game. "
        "Dot size — total rebounds. Top-left = pure defensive rebounders (typical guards), "
        "right side = bigs who crash the offensive boards."
    )

    avg_orb = df["ORB_Avg"].mean()
    avg_drb = df["DRB_Avg"].mean()

    fig = px.scatter(
        df,
        x="ORB_Avg",
        y="DRB_Avg",
        size="TRB_Tot",
        hover_data=["Player", "Team", "ORB_Tot", "DRB_Tot", "TRB_Tot", "TRB_Avg"],
        labels={"ORB_Avg": "Offensive Rebounds / Game", "DRB_Avg": "Defensive Rebounds / Game"},
        text="Player",
        **_color_kwargs(df, "TRB_Avg", color_by_team=color_by_team),
    )
    fig.update_traces(
        textposition="top center",
        textfont_size=10,
        marker=dict(line=dict(width=1, color="DarkSlateGrey")),
    )
    fig.add_hline(
        y=avg_drb, line_dash="dash", line_color="gray",
        annotation_text=f"Avg DRB: {avg_drb:.1f}",
    )
    fig.add_vline(
        x=avg_orb, line_dash="dash", line_color="gray",
        annotation_text=f"Avg ORB: {avg_orb:.1f}",
    )
    fig.update_layout(height=500, showlegend=True)
    st.plotly_chart(fig, width="stretch")


def render_defense_chart(df: pd.DataFrame, *, color_by_team: bool) -> None:
    """Scatter plot: Steals vs Blocks per game."""
    st.markdown("#### Defensive Impact: Steals vs Blocks per Game")
    st.caption(
        "**STL** — steals per game (typical for guards/wings). "
        "**BLK** — blocks per game (typical for bigs). Dot size — games played."
    )

    avg_stl = df["STL_Avg"].mean()
    avg_blk = df["BLK_Avg"].mean()

    fig = px.scatter(
        df,
        x="STL_Avg",
        y="BLK_Avg",
        size="Games",
        hover_data=["Player", "Team", "STL_Tot", "BLK_Tot", "Games"],
        labels={"STL_Avg": "Steals / Game", "BLK_Avg": "Blocks / Game"},
        text="Player",
        **_color_kwargs(df, "STL_Avg", color_by_team=color_by_team),
    )
    fig.update_traces(
        textposition="top center",
        textfont_size=10,
        marker=dict(line=dict(width=1, color="DarkSlateGrey")),
    )
    fig.add_hline(
        y=avg_blk, line_dash="dash", line_color="gray",
        annotation_text=f"Avg BLK: {avg_blk:.2f}",
    )
    fig.add_vline(
        x=avg_stl, line_dash="dash", line_color="gray",
        annotation_text=f"Avg STL: {avg_stl:.2f}",
    )
    fig.update_layout(height=500, showlegend=True)
    st.plotly_chart(fig, width="stretch")


def main() -> None:
    st.set_page_config(page_title="Corn Liga – Player Dashboard", layout="wide")
    st.title("Player Dashboard")

    st.markdown("""
    This page contains player statistics for Ravens Belgrade and Belgrade Bulls.
    More teams will be added in next releases.

    Information about metrics is available in the glossary.

    Source: [cornliga.com](https://cornliga.com/seasons/2025-26/leagues/north-liga)
    """)

    with st.sidebar:
        st.header("Data controls")
        refresh_players = st.button("Refresh player stats")

        st.divider()

        with st.expander("📖 Glossary", expanded=False):
            render_glossary()

    if refresh_players:
        load_team_players.clear()

    col_team, col_min = st.columns([2, 1])
    with col_team:
        selection = st.radio(
            "Team",
            options=["Ravens", "Bulls", "Both"],
            horizontal=True,
            index=0,
        )
    with col_min:
        min_games = st.number_input(
            "Min games played",
            min_value=0,
            value=6,
            step=1,
            help="Hide players who played fewer games than this threshold.",
        )

    teams_to_load = list(TEAMS_CONFIG.keys()) if selection == "Both" else [selection]

    frames: list[pd.DataFrame] = []
    try:
        with st.spinner("Loading player statistics..."):
            for team_name in teams_to_load:
                frames.append(load_team_players(team_name, force_refresh=refresh_players))
    except RequestException as exc:
        st.error(f"Failed to download player statistics: {exc}")
        return
    except ValueError as exc:
        st.error(f"Unable to load player statistics: {exc}")
        return

    player_stats = pd.concat(frames, ignore_index=True)
    player_stats = reorder_player_stats_columns(player_stats)

    total_count = len(player_stats)
    if min_games > 0 and "Games" in player_stats.columns:
        player_stats = player_stats[player_stats["Games"] >= min_games].copy()
    hidden_count = total_count - len(player_stats)

    color_by_team = selection == "Both"
    scope = f"across {len(teams_to_load)} teams" if color_by_team else f"for {selection}"
    suffix = f" ({hidden_count} hidden by min games filter)" if hidden_count else ""
    st.success(f"Loaded {len(player_stats)} players {scope}{suffix}.")

    with st.expander("Download data", expanded=False):
        suffix = selection.lower() if selection != "Both" else "ravens_bulls"
        st.download_button(
            "Player stats (CSV)",
            data=player_stats.to_csv(index=False).encode("utf-8"),
            file_name=f"{suffix}_player_advanced_stats.csv",
            mime="text/csv",
        )

    st.subheader("Player Statistics")
    render_player_table(player_stats, show_team=color_by_team)

    st.divider()
    st.subheader("Charts")

    render_top_scorers_chart(player_stats, color_by_team=color_by_team)
    render_usage_vs_ts_chart(player_stats, color_by_team=color_by_team)
    render_efficiency_vs_usage_chart(player_stats, color_by_team=color_by_team)
    render_shot_distribution_chart(player_stats, color_by_team=color_by_team)
    render_2pr_vs_2p_percentage_chart(player_stats, color_by_team=color_by_team)
    render_3pr_vs_3p_percentage_chart(player_stats, color_by_team=color_by_team)
    render_ftr_vs_ts_chart(player_stats, color_by_team=color_by_team)
    render_usage_vs_ast_to_chart(player_stats, color_by_team=color_by_team)
    render_usage_vs_ast_share_chart(player_stats, color_by_team=color_by_team)
    render_rebounding_chart(player_stats, color_by_team=color_by_team)
    render_defense_chart(player_stats, color_by_team=color_by_team)


if __name__ == "__main__":
    main()
