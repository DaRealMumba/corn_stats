from __future__ import annotations

import pandas as pd


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

    for made_col, attempted_col, output_col in metrics:
        df[output_col] = (df[made_col] / df[attempted_col] * multiplier).round(decimals)

    return df


def calculate_shot_distribution(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Pts_2P_%"] = ((2 * df["2PM_Tot"]) / df["Scored"] * 100).round(1)
    df["Pts_3P_%"] = ((3 * df["3PM_Tot"]) / df["Scored"] * 100).round(1)
    df["Pts_FT_%"] = (df["FTM_Tot"] / df["Scored"] * 100).round(1)
    return df


def total_rebounds(df: pd.DataFrame, output_col: str = "TRB_Avg") -> pd.DataFrame:
    df = df.copy()
    df[output_col] = (df["ORB_Avg"] + df["DRB_Avg"]).round(1)
    return df


def assist_to_turnover_ratio(df: pd.DataFrame, output_col: str = "ASS_TO_Ratio") -> pd.DataFrame:
    df = df.copy()
    df[output_col] = (df["AST_Avg"] / df["TO_Avg"]).round(1)
    return df


def effective_field_goal_percentage(df: pd.DataFrame, output_col: str = "eFG_%") -> pd.DataFrame:
    df = df.copy()
    df[output_col] = (((df["FGM_Avg"] + 0.5 * df["3PM_Avg"]) / df["FGA_Avg"]) * 100).round(2)
    return df


def true_shooting_percentage(df: pd.DataFrame, output_col: str = "TS_%") -> pd.DataFrame:
    df = df.copy()
    df[output_col] = (
        (df["PTS_Avg"] / (2 * (df["FGA_Avg"] + 0.44 * df["FTA_Avg"]))) * 100
    ).round(2)
    return df


def free_throw_rate(df: pd.DataFrame, output_col: str = "FT_rate") -> pd.DataFrame:
    df = df.copy()
    df[output_col] = ((df["FTA_Avg"] / df["FGA_Avg"]) * 100).round(2)
    return df


def offensive_rebound_percentage(df: pd.DataFrame, output_col: str = "ORB_%") -> pd.DataFrame:
    df = df.copy()
    league_avg_drb = df["DRB_Avg"].mean()
    df[output_col] = (df["ORB_Avg"] / (df["ORB_Avg"] + league_avg_drb) * 100).round(2)
    return df


def defensive_rebound_percentage(df: pd.DataFrame, output_col: str = "DRB_%") -> pd.DataFrame:
    df = df.copy()
    df[output_col] = (100 - df["ORB_%"]).round(2)
    return df


def calculate_possessions(df: pd.DataFrame, output_col: str = "POSS") -> pd.DataFrame:
    df = df.copy()
    df[output_col] = (df["FGA_Avg"] - df["ORB_Avg"] + df["TO_Avg"] + 0.44 * df["FTA_Avg"]).round(1)
    return df


def calculate_offensive_rating(df: pd.DataFrame, output_col: str = "Off_Rating") -> pd.DataFrame:
    df = df.copy()
    df[output_col] = (100 * df["PTS_Avg"] / df["POSS"]).round(1)
    return df


def calculate_defensive_rating(df: pd.DataFrame, output_col: str = "Def_Rating") -> pd.DataFrame:
    df = df.copy()
    df[output_col] = (100 * df["Pts_Allowed_Avg"] / df["POSS"]).round(1)
    return df


def turnover_percentage(df: pd.DataFrame, output_col: str = "TO_%") -> pd.DataFrame:
    df = df.copy()
    df[output_col] = ((df["TO_Avg"] / df["POSS"]) * 100).round(2)
    return df


def calculate_net_rating(df: pd.DataFrame, output_col: str = "Net_Rating") -> pd.DataFrame:
    df = df.copy()
    df[output_col] = (df["Off_Rating"] - df["Def_Rating"]).round(1)
    return df


def calculate_all_advanced_stats(df: pd.DataFrame) -> pd.DataFrame:
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

    df = calculate_possessions(df)
    df = calculate_offensive_rating(df)
    df = calculate_defensive_rating(df)
    df = turnover_percentage(df)
    df = calculate_net_rating(df)

    return df

