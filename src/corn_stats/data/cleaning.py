from __future__ import annotations

import re
import unicodedata
from typing import Tuple

import pandas as pd


PLAYER_RENAME_MAP: dict[str, str] = {
    "eff_pg": "Eff_Avg",
    "eff_total": "Eff_Tot",
    "fg_FGA_pg": "FGA_Avg",
    "fg_FGM_pg": "FGM_Avg",
    "fg_FGA_total": "FGA_Tot",
    "fg_FGM_total": "FGM_Tot",
    "fg_pct": "FG%",
    "2p_A_pg": "2PA_Avg",
    "2p_M_pg": "2PM_Avg",
    "2p_A_total": "2PA_Tot",
    "2p_M_total": "2PM_Tot",
    "2p_pct": "2P%",
    "3p_A_pg": "3PA_Avg",
    "3p_M_pg": "3PM_Avg",
    "3p_A_total": "3PA_Tot",
    "3p_M_total": "3PM_Tot",
    "3p_pct": "3P%",
    "ft_A_pg": "FTA_Avg",
    "ft_M_pg": "FTM_Avg",
    "ft_A_total": "FTA_Tot",
    "ft_M_total": "FTM_Tot",
    "ft_pct": "FT%",
    "ast_pg": "AST_Avg",
    "ast_total": "AST_Tot",
    "to_pg": "TO_Avg",
    "to_total": "TO_Tot",
    "stl_pg": "STL_Avg",
    "stl_total": "STL_Tot",
    "blk_pg": "BLK_Avg",
    "blk_total": "BLK_Tot",
    "pfd_pg": "PFD_Avg",
    "pfd_total": "PFD_Tot",
    "pts_pg": "Pts_Avg",
    "pts_total": "Pts_Tot",
    "orb_pg": "ORB_Avg",
    "drb_pg": "DRB_Avg",
    "orb_total": "ORB_Tot",
    "drb_total": "DRB_Tot",
    "reb_pg": "TRB_Avg",
    "reb_total": "TRB_Tot",
    "games": "Games",
    "name": "Player",
    "age": "Age",
}

def normalize_string(s: str, to_lower: bool = True) -> str:
    """Normalize a string by removing diacritics and optional lowercasing."""
    if pd.isna(s):
        return ""
    normalized = unicodedata.normalize("NFD", str(s))
    without_diacritics = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    result = without_diacritics.strip()
    return result.lower() if to_lower else result


def clean_team_name(raw: str) -> Tuple[str, str | None]:
    """Clean team name and extract trailing abbreviation if present."""
    if pd.isna(raw):
        return raw, None

    s = str(raw).strip()
    s = re.sub(r"^\d+", "", s).strip()

    abbreviation = None
    if len(s) >= 3:
        tail = s[-3:]
        before = s[:-3]
        tail_normalized = normalize_string(tail, to_lower=False)
        is_abbreviation = (
            before
            and not before.endswith(" ")
            and len(tail_normalized) == 3
            and all(ch.isdigit() or (ch.isalpha() and ch.isupper()) for ch in tail_normalized)
        )
        if is_abbreviation:
            abbreviation = tail
            s = before

    s = re.sub(r"\s+", " ", s).strip()
    return s, abbreviation


def normalize_player_stats_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Bring player-level stats to the same naming style as team stats.
    """
    df = df.copy()
    df = df.rename(columns=PLAYER_RENAME_MAP)
    return df


def merge_duplicate_players(
    df: pd.DataFrame,
    player_names: list[str],
    final_name: str,
    age_source_name: str | None = None,
    player_col: str = "Player",
    age_col: str = "Age",
    games_col: str = "Games",
) -> pd.DataFrame:
    """
    Объединяет статистику дубликатов одного игрока в DataFrame.
    
    Функция находит записи с указанными именами игроков, объединяет их статистику:
    - Суммирует Tot колонки и Games
    - Пересчитывает Avg колонки на основе общего количества игр
    - Пересчитывает процентные колонки (FG%, 2P%, 3P%, FT%)
    - Берет Age из указанной записи (если указано)
    - Устанавливает финальное имя игрока
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame со статистикой игроков
    player_names : list[str]
        Список имен игроков для объединения (например, ["Ivan Fursov", "Fursov Ivan"])
    final_name : str
        Финальное имя игрока после объединения (например, "Fursov Ivan")
    age_source_name : str | None, optional
        Имя игрока, откуда брать Age. Если None, берется из первой записи с непустым Age
    player_col : str, default "Player"
        Название колонки с именами игроков
    age_col : str, default "Age"
        Название колонки с возрастом
    games_col : str, default "Games"
        Название колонки с количеством игр
    
    Returns
    -------
    pd.DataFrame
        DataFrame с объединенными записями игроков
        
    Examples
    --------
    >>> df = merge_duplicate_players(
    ...     ravens_players_df,
    ...     player_names=["Ivan Fursov", "Fursov Ivan"],
    ...     final_name="Fursov Ivan",
    ...     age_source_name="Ivan Fursov"
    ... )
    """
    df = df.copy()
    
    # Находим записи для объединения
    mask = df[player_col].isin(player_names)
    duplicate_rows = df[mask].copy()
    
    # Проверяем количество найденных записей
    if len(duplicate_rows) == 0:
        print(f"Внимание: не найдено ни одной записи из {player_names}.")
        return df
    
    if len(duplicate_rows) == 1:
        found_name = duplicate_rows[player_col].iloc[0]
        if found_name == final_name:
            return df  # Уже объединено
        print(f"Внимание: найдена только 1 запись из {len(player_names)} ожидаемых: {found_name}")
        return df
    
    if len(duplicate_rows) > len(player_names):
        print(f"Внимание: найдено больше записей ({len(duplicate_rows)}) чем ожидалось ({len(player_names)}).")
        return df
    
    # Определяем колонки по типам
    pct_cols = ["FG%", "2P%", "3P%", "FT%"]
    avg_cols = [col for col in df.columns if col.endswith("_Avg")]
    exclude_from_sum = [player_col, age_col, games_col] + pct_cols + avg_cols
    
    # Колонки для суммирования (все числовые кроме исключенных)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    sum_cols = [col for col in numeric_cols if col not in exclude_from_sum]
    
    # Суммируем колонки векторно (без iterrows)
    merged_data = {}
    for col in sum_cols:
        merged_data[col] = duplicate_rows[col].fillna(0).sum()
    
    # Суммируем Games напрямую
    games_total = duplicate_rows[games_col].fillna(0).sum() if games_col in df.columns else 0
    merged_data[games_col] = int(games_total)
    
    # Пересчитываем Avg колонки: Tot / Games
    if games_total > 0:
        for avg_col in avg_cols:
            tot_col = avg_col.replace("_Avg", "_Tot")
            if tot_col in merged_data:
                merged_data[avg_col] = round(merged_data[tot_col] / games_total, 1)
    
    # Пересчитываем процентные колонки
    pct_formulas = [
        ("FG%", "FGM_Tot", "FGA_Tot"),
        ("2P%", "2PM_Tot", "2PA_Tot"),
        ("3P%", "3PM_Tot", "3PA_Tot"),
        ("FT%", "FTM_Tot", "FTA_Tot"),
    ]
    for pct_col, made_col, attempted_col in pct_formulas:
        if made_col in merged_data and attempted_col in merged_data:
            if merged_data[attempted_col] > 0:
                merged_data[pct_col] = round(merged_data[made_col] / merged_data[attempted_col] * 100, 1)
    
    # Определяем Age
    if age_source_name is None:
        age_value = duplicate_rows[age_col].dropna().iloc[0] if duplicate_rows[age_col].notna().any() else None
    else:
        age_rows = duplicate_rows[duplicate_rows[player_col] == age_source_name]
        age_value = age_rows[age_col].iloc[0] if not age_rows.empty and age_rows[age_col].notna().any() else None
    merged_data[age_col] = age_value
    
    # Устанавливаем имя игрока
    merged_data[player_col] = final_name
    
    # Удаляем старые записи и добавляем объединенную
    df = df[~mask].copy()
    merged_df = pd.DataFrame([merged_data])
    
    # Восстанавливаем типы данных
    for col in merged_df.columns:
        if col in df.columns:
            try:
                merged_df[col] = merged_df[col].astype(df[col].dtype)
            except (ValueError, TypeError):
                pass  # Оставляем как есть если не удалось преобразовать
    
    return pd.concat([df, merged_df], ignore_index=True)

