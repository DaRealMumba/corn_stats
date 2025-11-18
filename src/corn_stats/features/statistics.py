from __future__ import annotations

import numpy as np
import pandas as pd


def _validate_columns(df: pd.DataFrame, required: set[str], function_name: str) -> None:
    """Validate that DataFrame contains all required columns."""
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"{function_name} requires columns {sorted(missing)}, "
            f"but DataFrame only has {sorted(df.columns)}"
        )


def _safe_divide(numerator: pd.Series, denominator: pd.Series, default: float = 0.0) -> pd.Series:
    """Divide two series safely, handling zero denominators and infinity values.
    
    Replaces zero denominators with pd.NA, performs division, then replaces
    NaN and infinity values with the default value.
    """
    result = numerator.div(denominator.replace(0, pd.NA))
    return result.replace([np.inf, -np.inf], default).fillna(default)


def calculate_shooting_percentage(
    df: pd.DataFrame,
    metrics: list[tuple[str, str, str]] | None = None,
    multiplier: float = 100.0,
    decimals: int = 1,
) -> pd.DataFrame:
    df = df.copy()

    if metrics is None:
        metrics = [
            ("FGM_Tot", "FGA_Tot", "FG%"),
            ("2PM_Tot", "2PA_Tot", "2P%"),
            ("3PM_Tot", "3PA_Tot", "3P%"),
            ("FTM_Tot", "FTA_Tot", "FT%"),
        ]

    required_cols = {col for metric in metrics for col in metric[:2]}
    _validate_columns(df, required_cols, "calculate_shooting_percentage")

    for made_col, attempted_col, output_col in metrics:
        df[output_col] = (
            _safe_divide(df[made_col], df[attempted_col], default=0.0) * multiplier
        ).round(decimals)

    return df


def calculate_shot_distribution(df: pd.DataFrame, multiplier: float = 100.0, decimals: int = 1) -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"2PM_Tot", "3PM_Tot", "FTM_Tot", "Scored"}, "calculate_shot_distribution")
    df["%Pts_2P"] = (_safe_divide(2 * df["2PM_Tot"], df["Scored"], default=0.0) * multiplier).round(decimals)   
    df["%Pts_3P"] = (_safe_divide(3 * df["3PM_Tot"], df["Scored"], default=0.0) * multiplier).round(decimals)
    df["%Pts_FT"] = (_safe_divide(df["FTM_Tot"], df["Scored"], default=0.0) * multiplier).round(decimals)
    return df



def calculate_shot_rate(
    df: pd.DataFrame,
    metrics: list[tuple[str, str, str]] | None = None,
    multiplier: float = 100.0,
    decimals: int = 1,
) -> pd.DataFrame:
    df = df.copy()
    
    if metrics is None:
        metrics = [
            ("2PA_Tot", "FGA_Tot", "2Pr"),
            ("3PA_Tot", "FGA_Tot", "3Pr"),
            ("FTA_Tot", "FGA_Tot", "FTr"),
        ]

    required_cols = {col for metric in metrics for col in metric[:2]}
    _validate_columns(df, required_cols, "calculate_shot_rate")
    for made_col, attempted_col, output_col in metrics:
        df[output_col] = (
            _safe_divide(df[made_col], df[attempted_col], default=0.0) * multiplier
        ).round(decimals)
    return df


def total_rebounds(df: pd.DataFrame, output_col: str = "TRB_Tot") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"ORB_Tot", "DRB_Tot"}, "total_rebounds")
    df[output_col] = (df["ORB_Tot"] + df["DRB_Tot"]).round(1)
    return df


def total_rebounds_per_game(df: pd.DataFrame, output_col: str = "TRB_Avg") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"TRB_Tot", "Games"}, "total_rebounds_per_game")
    df[output_col] = (_safe_divide(df["TRB_Tot"], df["Games"], default=0.0)).round(1)
    return df


def assist_to_turnover_ratio(df: pd.DataFrame, output_col: str = "ASS_TO_Ratio") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"AST_Tot", "TO_Tot"}, "assist_to_turnover_ratio")
    df[output_col] = _safe_divide(df["AST_Tot"], df["TO_Tot"], default=0.0).round(1)
    return df


def effective_field_goal_percentage(df: pd.DataFrame, output_col: str = "eFG_%") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"FGM_Tot", "3PM_Tot", "FGA_Tot"}, "effective_field_goal_percentage")
    df[output_col] = (
        _safe_divide(df["FGM_Tot"] + 0.5 * df["3PM_Tot"], df["FGA_Tot"], default=0.0) * 100
    ).round(2)
    return df


def true_shooting_percentage(df: pd.DataFrame, output_col: str = "TS_%") -> pd.DataFrame:
    """Calculate true shooting percentage.
    
    Formula: Scored / (2 * (FGA_Tot + 0.44 * FTA_Tot)) * 100
    """
    df = df.copy()
    _validate_columns(df, {"Scored", "FGA_Tot", "FTA_Tot"}, "true_shooting_percentage")
    denominator = 2 * (df["FGA_Tot"] + 0.44 * df["FTA_Tot"])
    df[output_col] = (_safe_divide(df["Scored"], denominator, default=0.0) * 100).round(2)
    return df


def offensive_rebound_percentage(df: pd.DataFrame, output_col: str = "ORB_%") -> pd.DataFrame:
    """
    Calculate offensive rebound percentage. 
    League average defensive rebound percentage is used to calculate the denominator.
    
    Formula: ORB_Tot / (ORB_Tot + DRB_League_Avg * Games) * 100
    """
    df = df.copy()
    _validate_columns(df, {"ORB_Tot", "DRB_Tot", "Games"}, "offensive_rebound_percentage")
    league_avg_drb = sum(df["DRB_Tot"]) / sum(df["Games"])
    denominator = df["ORB_Tot"] + league_avg_drb * df["Games"]
    df[output_col] = (_safe_divide(df["ORB_Tot"], denominator, default=0.0) * 100).round(2)
    return df


def defensive_rebound_percentage(df: pd.DataFrame, output_col: str = "DRB_%") -> pd.DataFrame:
    """
    Calculate defensive rebound percentage.
    Formula: DRB_Tot / (DRB_Tot + ORB_League_Avg * Games) * 100
    """
    df = df.copy()
    _validate_columns(df, {"ORB_%", "DRB_Tot", "Games"}, "defensive_rebound_percentage")
    league_avg_orb = sum(df["ORB_Tot"]) / sum(df["Games"])
    denominator = df["DRB_Tot"] + league_avg_orb * df["Games"]
    df[output_col] = (_safe_divide(df["DRB_Tot"], denominator, default=0.0) * 100).round(2)
    return df


def calculate_total_possessions(df: pd.DataFrame, output_col: str = "POSS_Tot") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"FGA_Tot", "ORB_Tot", "TO_Tot", "FTA_Tot"}, "calculate_total_possessions")
    df[output_col] = (df["FGA_Tot"] - df["ORB_Tot"] + df["TO_Tot"] + 0.44 * df["FTA_Tot"]).round(1)
    return df


def calculate_offensive_rating(df: pd.DataFrame, output_col: str = "Off_Rating") -> pd.DataFrame:
    """Calculate offensive rating (points per 100 possessions).
    
    Formula: Scored / POSS_Tot * 100
    """
    df = df.copy()
    _validate_columns(df, {"Scored", "POSS_Tot"}, "calculate_offensive_rating")
    df[output_col] = (_safe_divide(df["Scored"], df["POSS_Tot"], default=0.0) * 100).round(1)
    return df


def calculate_defensive_rating(df: pd.DataFrame, output_col: str = "Def_Rating") -> pd.DataFrame:
    """Calculate defensive rating (points allowed per 100 possessions).
    
    Formula: Allowed / POSS_Tot * 100
    """
    df = df.copy()
    _validate_columns(df, {"Allowed", "POSS_Tot"}, "calculate_defensive_rating")
    df[output_col] = (_safe_divide(df["Allowed"], df["POSS_Tot"], default=0.0) * 100).round(1)
    return df


def turnover_percentage(df: pd.DataFrame, output_col: str = "TO_%") -> pd.DataFrame:
    """Calculate turnover percentage (turnovers per 100 possessions).
    
    Formula: TO_Tot / POSS_Tot * 100
    """
    df = df.copy()
    _validate_columns(df, {"TO_Tot", "POSS_Tot"}, "turnover_percentage")
    df[output_col] = (_safe_divide(df["TO_Tot"], df["POSS_Tot"], default=0.0) * 100).round(2)
    return df


def calculate_net_rating(df: pd.DataFrame, output_col: str = "Net_Rating") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"Off_Rating", "Def_Rating"}, "calculate_net_rating")
    df[output_col] = (df["Off_Rating"] - df["Def_Rating"]).round(1)
    return df


def calculate_pace(df: pd.DataFrame, output_col: str = "Pace") -> pd.DataFrame:
    """Calculate pace (possessions per game).
    
    Formula: POSS_Tot / Games
    """
    df = df.copy()
    _validate_columns(df, {"POSS_Tot", "Games"}, "calculate_pace")
    df[output_col] = (_safe_divide(df["POSS_Tot"], df["Games"], default=0.0)).round(1)
    return df


def assist_rate(df: pd.DataFrame, output_col: str = "AST_Rate") -> pd.DataFrame:
    """Calculate assist rate (assists per field goals made).
    
    Formula: AST / FGM * 100
    """
    df = df.copy()
    _validate_columns(df, {"AST_Tot", "FGM_Tot"}, "assist_rate")
    df[output_col] = (_safe_divide(df["AST_Tot"], df["FGM_Tot"], default=0.0) * 100).round(1)
    return df


def steal_rate(df: pd.DataFrame, output_col: str = "STL_Rate") -> pd.DataFrame:
    """Calculate steal rate (steals per 100 possessions).
    
    Formula: STL_Tot / POSS_Tot * 100
    """
    df = df.copy()
    _validate_columns(df, {"STL_Tot", "POSS_Tot"}, "steal_rate")
    df[output_col] = (_safe_divide(df["STL_Tot"], df["POSS_Tot"], default=0.0) * 100).round(2)
    return df


def block_rate(df: pd.DataFrame, output_col: str = "BLK_Rate") -> pd.DataFrame:
    """Calculate block rate (blocks per 100 possessions).
    
    Formula: BLK_Tot / POSS_Tot * 100
    """
    df = df.copy()
    _validate_columns(df, {"BLK_Tot", "POSS_Tot"}, "block_rate")
    df[output_col] = (_safe_divide(df["BLK_Tot"], df["POSS_Tot"], default=0.0) * 100).round(2)
    return df


def foul_rate(df: pd.DataFrame, output_col: str = "PFD_Rate") -> pd.DataFrame:
    """Calculate personal foul rate (fouls per 100 possessions).
    
    Formula: PFD_Tot / POSS_Tot * 100
    """
    df = df.copy()
    _validate_columns(df, {"PFD_Tot", "POSS_Tot"}, "foul_rate")
    df[output_col] = (_safe_divide(df["PFD_Tot"], df["POSS_Tot"], default=0.0) * 100).round(2)
    return df


def win_percentage(df: pd.DataFrame, output_col: str = "Win_%") -> pd.DataFrame:
    """Calculate win percentage.
    
    Formula: Wins / Games * 100
    """
    df = df.copy()
    _validate_columns(df, {"Wins", "Games"}, "win_percentage")
    df[output_col] = (_safe_divide(df["Wins"], df["Games"], default=0.0) * 100).round(1)
    return df


def points_per_game_differential(df: pd.DataFrame, output_col: str = "Pts_Diff_Avg") -> pd.DataFrame:
    """Calculate point differential per game.
    
    Formula: (Scored - Allowed) / Games
    """
    df = df.copy()
    _validate_columns(df, {"Scored", "Allowed", "Games"}, "average_points_differential")
    df[output_col] = (_safe_divide(df["Scored"] - df["Allowed"], df["Games"], default=0.0)).round(1)
    return df


def calculate_all_advanced_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all advanced basketball statistics for teams.
    
    Requires basic stats columns:
    - Tot variants: FGM_Tot, FGA_Tot, 2PM_Tot, 2PA_Tot, 3PM_Tot, 3PA_Tot,
      FTM_Tot, FTA_Tot, ORB_Tot, DRB_Tot, AST_Tot, TO_Tot, Scored,
    - League table: Scored, Allowed, Games, Wins, Losses
    """
    if df.empty:
        raise ValueError("calculate_all_advanced_stats received empty DataFrame")
    
    df = df.copy()

    df = calculate_shooting_percentage(df)
    df = calculate_shot_distribution(df)
    df = calculate_shot_rate(df)
    df = total_rebounds(df)
    df = total_rebounds_per_game(df)
    df = assist_to_turnover_ratio(df)
    df = effective_field_goal_percentage(df)
    df = true_shooting_percentage(df)
    df = offensive_rebound_percentage(df)
    df = defensive_rebound_percentage(df)

    df = calculate_total_possessions(df)
    
    # Ratings and possession-based metrics (use totals)
    df = calculate_offensive_rating(df)
    df = calculate_defensive_rating(df)
    df = turnover_percentage(df)
    df = calculate_net_rating(df)
    
    # Additional advanced metrics
    df = calculate_pace(df)
    df = assist_rate(df)
    df = steal_rate(df)
    df = block_rate(df)
    df = foul_rate(df)
    df = win_percentage(df)
    df = points_per_game_differential(df)

    return df

