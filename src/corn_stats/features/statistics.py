from __future__ import annotations

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
    """Divide two series safely, handling zero denominators."""
    return numerator.div(denominator.replace(0, pd.NA)).fillna(default)


def calculate_shooting_percentage(
    df: pd.DataFrame,
    metrics: list[tuple[str, str, str]] | None = None,
    multiplier: float = 100.0,
    decimals: int = 1,
) -> pd.DataFrame:
    df = df.copy()

    if metrics is None:
        metrics = [
            ("FGM_Avg", "FGA_Avg", "FG_%"),
            ("2PM_Avg", "2PA_Avg", "2P_%"),
            ("3PM_Avg", "3PA_Avg", "3P_%"),
            ("FTM_Avg", "FTA_Avg", "FT_%"),
        ]

    required_cols = {col for metric in metrics for col in metric[:2]}
    _validate_columns(df, required_cols, "calculate_shooting_percentage")

    for made_col, attempted_col, output_col in metrics:
        df[output_col] = (
            _safe_divide(df[made_col], df[attempted_col], default=0.0) * multiplier
        ).round(decimals)

    return df


def calculate_shot_distribution(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"2PM_Tot", "3PM_Tot", "FTM_Tot", "Scored"}, "calculate_shot_distribution")
    
    df["Pts_2P_%"] = (_safe_divide(2 * df["2PM_Tot"], df["Scored"], default=0.0) * 100).round(1)
    df["Pts_3P_%"] = (_safe_divide(3 * df["3PM_Tot"], df["Scored"], default=0.0) * 100).round(1)
    df["Pts_FT_%"] = (_safe_divide(df["FTM_Tot"], df["Scored"], default=0.0) * 100).round(1)
    return df


def total_rebounds(df: pd.DataFrame, output_col: str = "TRB_Avg") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"ORB_Avg", "DRB_Avg"}, "total_rebounds")
    df[output_col] = (df["ORB_Avg"] + df["DRB_Avg"]).round(1)
    return df


def assist_to_turnover_ratio(df: pd.DataFrame, output_col: str = "ASS_TO_Ratio") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"AST_Avg", "TO_Avg"}, "assist_to_turnover_ratio")
    df[output_col] = _safe_divide(df["AST_Avg"], df["TO_Avg"], default=0.0).round(1)
    return df


def effective_field_goal_percentage(df: pd.DataFrame, output_col: str = "eFG_%") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"FGM_Avg", "3PM_Avg", "FGA_Avg"}, "effective_field_goal_percentage")
    df[output_col] = (
        _safe_divide(df["FGM_Avg"] + 0.5 * df["3PM_Avg"], df["FGA_Avg"], default=0.0) * 100
    ).round(2)
    return df


def true_shooting_percentage(df: pd.DataFrame, output_col: str = "TS_%") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"PTS_Avg", "FGA_Avg", "FTA_Avg"}, "true_shooting_percentage")
    denominator = 2 * (df["FGA_Avg"] + 0.44 * df["FTA_Avg"])
    df[output_col] = (_safe_divide(df["PTS_Avg"], denominator, default=0.0) * 100).round(2)
    return df


def free_throw_rate(df: pd.DataFrame, output_col: str = "FT_rate") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"FTA_Avg", "FGA_Avg"}, "free_throw_rate")
    df[output_col] = (_safe_divide(df["FTA_Avg"], df["FGA_Avg"], default=0.0) * 100).round(2)
    return df


def offensive_rebound_percentage(df: pd.DataFrame, output_col: str = "ORB_%") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"ORB_Avg", "DRB_Avg"}, "offensive_rebound_percentage")
    league_avg_drb = df["DRB_Avg"].mean()
    denominator = df["ORB_Avg"] + league_avg_drb
    df[output_col] = (_safe_divide(df["ORB_Avg"], denominator, default=0.0) * 100).round(2)
    return df


def defensive_rebound_percentage(df: pd.DataFrame, output_col: str = "DRB_%") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"ORB_%"}, "defensive_rebound_percentage")
    df[output_col] = (100 - df["ORB_%"]).round(2)
    return df


def calculate_average_possessions(df: pd.DataFrame, output_col: str = "POSS_Avg") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"FGA_Avg", "ORB_Avg", "TO_Avg", "FTA_Avg"}, "calculate_average_possessions")
    df[output_col] = (df["FGA_Avg"] - df["ORB_Avg"] + df["TO_Avg"] + 0.44 * df["FTA_Avg"]).round(1)
    return df


def calculate_total_possessions(df: pd.DataFrame, output_col: str = "POSS_Tot") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"FGA_Tot", "ORB_Tot", "TO_Tot", "FTA_Tot"}, "calculate_total_possessions")
    df[output_col] = (df["FGA_Tot"] - df["ORB_Tot"] + df["TO_Tot"] + 0.44 * df["FTA_Tot"]).round(1)
    return df


def calculate_offensive_rating(df: pd.DataFrame, output_col: str = "Off_Rating") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"PTS_Avg", "POSS_Avg"}, "calculate_offensive_rating")
    df[output_col] = (_safe_divide(df["PTS_Avg"], df["POSS_Avg"], default=0.0) * 100).round(1)
    return df


def calculate_defensive_rating(df: pd.DataFrame, output_col: str = "Def_Rating") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"Pts_Allowed_Avg", "POSS_Avg"}, "calculate_defensive_rating")
    df[output_col] = (_safe_divide(df["Pts_Allowed_Avg"], df["POSS_Avg"], default=0.0) * 100).round(1)
    return df


def turnover_percentage(df: pd.DataFrame, output_col: str = "TO_%") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"TO_Avg", "POSS_Avg"}, "turnover_percentage")
    df[output_col] = (_safe_divide(df["TO_Avg"], df["POSS_Avg"], default=0.0) * 100).round(2)
    return df


def calculate_net_rating(df: pd.DataFrame, output_col: str = "Net_Rating") -> pd.DataFrame:
    df = df.copy()
    _validate_columns(df, {"Off_Rating", "Def_Rating"}, "calculate_net_rating")
    df[output_col] = (df["Off_Rating"] - df["Def_Rating"]).round(1)
    return df


def calculate_all_advanced_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all advanced basketball statistics for teams.
    
    Requires basic stats columns: FGM_Avg, FGA_Avg, 2PM_Avg, 2PA_Avg, 3PM_Avg, 3PA_Avg,
    FTM_Avg, FTA_Avg, ORB_Avg, DRB_Avg, AST_Avg, TO_Avg, PTS_Avg, Scored, Pts_Allowed_Avg,
    and their Tot variants.
    
    Returns DataFrame with additional advanced metric columns.
    """
    if df.empty:
        raise ValueError("calculate_all_advanced_stats received empty DataFrame")
    
    df = df.copy()

    df = calculate_shooting_percentage(df)
    df = calculate_shot_distribution(df)
    df = total_rebounds(df)
    df = assist_to_turnover_ratio(df)
    df = effective_field_goal_percentage(df)
    df = true_shooting_percentage(df)
    df = free_throw_rate(df)
    df = offensive_rebound_percentage(df)
    df = defensive_rebound_percentage(df)

    df = calculate_average_possessions(df)
    df = calculate_total_possessions(df)
    df = calculate_offensive_rating(df)
    df = calculate_defensive_rating(df)
    df = turnover_percentage(df)
    df = calculate_net_rating(df)

    return df

