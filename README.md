# Corn Stats

An analytics dashboard for the amateur Serbian basketball league North Division. The repository contains scraping helpers, data processing utilities, advanced team metrics, and a multi-page Streamlit dashboard.

## Live Demo

The latest deployed version of the dashboard is available here:

`https://cornstats.up.railway.app`

## Features

- **Data ingestion** — `corn_stats.data` pulls the league table and team pages straight from [cornliga.com](https://cornliga.com).
- **Advanced metrics** — `corn_stats.features` computes eFG%, TS%, Net Rating, Pace, and a comprehensive set of team indicators.
- **Visualizations** — `corn_stats.viz` produces interactive Plotly charts featuring team logos.
- **UI components** — `corn_stats.ui` provides reusable Streamlit components like glossary.
- **Streamlit dashboard** — Multi-page web application with team statistics, charts, and data downloads.
- **Exploratory notebooks** — `notebooks/draft.ipynb` documents the analysis workflow and experiments.

## Repository Layout

```
assets/
  logos/             # Team logos
data/
  processed/         # Processed team statistics CSV
  raw/
    tables/          # League table CSV
    teams/           # Raw team-level stats CSV
notebooks/
  draft.ipynb        # Exploratory notebook with visualizations
src/
  corn_stats/        # Main package
    assets/          # Logo utilities
    config.py        # Configuration and constants
    data/            # Data loading and parsing
    features/        # Advanced metrics calculation
    ui/              # Streamlit UI components (glossary)
    viz/             # Visualization helpers
  main.py            # Streamlit main page
  pages/
    1_Team_Dash.py   # Team dashboard with charts
pyproject.toml       # Project metadata and dependencies
```

## Requirements

- Python `>= 3.13`
- pip 24+ or [uv](https://github.com/astral-sh/uv) for dependency management
- (optional) JupyterLab or VS Code for notebook work

## Installation

```bash
git clone https://github.com/<your-account>/corn_stats.git
cd corn_stats

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip

pip install -e .                   # install the package in editable mode
```

> Using `uv` instead?
>
> ```bash
> uv sync --all-extras
> ```

Once installed, `corn_stats` can be imported anywhere without tweaking `sys.path`.

## Working with Data

- **Download or refresh the league table:**
  ```python
  from corn_stats.config import TABLE_URL, TABLES_DATA_PATH
  from corn_stats.data import get_league_table

  df = get_league_table(TABLE_URL)
  df.to_csv(TABLES_DATA_PATH / "north_liga_df.csv", index=True)  # Position as index
  ```

- **Parse a team page into a tidy DataFrame:**
  ```python
  from corn_stats.config import TEAMS_URL
  from corn_stats.data import parse_team_page_wide

  team_df = parse_team_page_wide(f"{TEAMS_URL}/ravens-belgrade")
  ```

- **Compute advanced metrics for a dataset:**
  ```python
  from corn_stats.features import calculate_all_advanced_stats

  metrics_df = calculate_all_advanced_stats(team_df)
  ```

## Available Metrics

The package calculates a comprehensive set of basketball metrics:

**Shooting Metrics:**
- FG%, 2P%, 3P%, FT% — Basic shooting percentages
- eFG% — Effective field goal percentage
- TS% — True shooting percentage
- Shot distribution (%Pts_2P, %Pts_3P, %Pts_FT)
- Shot rates (2Pr, 3Pr, FTr)

**Possession-Based Metrics:**
- Pace — Possessions per game
- Offensive Rating — Points per 100 possessions
- Defensive Rating — Points allowed per 100 possessions
- Net Rating — Difference between offensive and defensive rating
- TO% — Turnover percentage per 100 possessions

**Rebounding:**
- ORB%, DRB% — Offensive and defensive rebound percentages
- Total rebounds (Tot and Avg variants)

**Other Advanced Metrics:**
- AST_Rate, STL_Rate, BLK_Rate, PFD_Rate — Rates per 100 possessions
- ASS_TO_Ratio — Assist-to-turnover ratio
- Win_% — Win percentage

All metrics include validation to ensure data quality and prevent errors.

## Streamlit App

Run the dashboard:

```bash
streamlit run src/main.py
```

The app includes:
- **Main page** (`src/main.py`) — League standings, team details, and advanced metrics visualization
- **Team Dashboard** (`src/pages/1_Team_Dash.py`) — Interactive charts: Pace, shooting strategies, rebounding profiles, and more

Both pages include:
- Data refresh controls
- Interactive glossary in sidebar
- CSV download functionality
- Team logos on scatter plots

All pages use shared components from `corn_stats` package for consistency.

## Notebooks

Launching JupyterLab:

```bash
jupyter lab
```

The `draft.ipynb` notebook already imports `corn_stats`. For the cleanest setup, run it from within an activated virtual environment where the package was installed via `pip install -e .`.

