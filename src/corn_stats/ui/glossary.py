from __future__ import annotations

import streamlit as st

from corn_stats.config import TEAM_STATS_COLUMN_ORDER


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

