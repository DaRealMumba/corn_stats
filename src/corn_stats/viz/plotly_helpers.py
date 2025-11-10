from __future__ import annotations

import base64
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.express as px

from corn_stats.assets.logos import get_logo_path


def _image_to_base64(image_path: Path) -> str | None:
    try:
        with image_path.open("rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")
    except Exception:
        return None


def scatter_with_logos_plotly(
    df: pd.DataFrame,
    x: str,
    y: str,
    team_col: str = "Team",
    *,
    logo_dirs: Iterable[Path] | None = None,
    logo_map: dict[str, Path] | None = None,
    logo_size_factor: float = 0.05,
    title: str | None = None,
    **px_kwargs,
):
    if "color" not in px_kwargs:
        px_kwargs["color"] = team_col
    if "hover_data" not in px_kwargs:
        px_kwargs["hover_data"] = [team_col]
    if title is not None and "title" not in px_kwargs:
        px_kwargs["title"] = title

    figure = px.scatter(df, x=x, y=y, **px_kwargs)

    effective_logo_map: dict[str, Path] = {}
    unique_teams = df[team_col].dropna().astype(str).unique().tolist()

    if logo_map:
        for team in unique_teams:
            path = logo_map.get(team)
            if path and Path(path).exists():
                effective_logo_map[team] = Path(path)

    for team in unique_teams:
        if team in effective_logo_map:
            continue
        if logo_path := get_logo_path(team, search_dirs=logo_dirs):
            effective_logo_map[team] = logo_path

    x_min, x_max = df[x].min(), df[x].max()
    y_min, y_max = df[y].min(), df[y].max()
    x_range = max(1e-9, x_max - x_min)
    y_range = max(1e-9, y_max - y_min)

    images = []

    for trace in figure.data:
        team_name = getattr(trace, "name", None) or getattr(trace, "legendgroup", None)
        if not team_name or team_name not in effective_logo_map:
            continue

        logo_path = effective_logo_map[team_name]
        image_b64 = _image_to_base64(logo_path)
        if not image_b64:
            continue

        team_data = df[df[team_col].astype(str) == team_name]
        if team_data.empty:
            continue

        x_val = team_data[x].iloc[0]
        y_val = team_data[y].iloc[0]

        images.append(
            dict(
                source=f"data:image/png;base64,{image_b64}",
                xref="x",
                yref="y",
                x=x_val,
                y=y_val,
                sizex=x_range * logo_size_factor,
                sizey=y_range * logo_size_factor,
                xanchor="center",
                yanchor="middle",
                layer="above",
            )
        )

    figure.update_traces(marker=dict(size=1, opacity=0))
    figure.update_layout(images=images)

    return figure

