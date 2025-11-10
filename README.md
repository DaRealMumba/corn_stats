# Corn Stats

An analytics playground for the amateur Basketball League (Corn Liga) in Belgrade, specifially North Liga. The repository contains scraping helpers, data processing utilities, advanced team metrics, and a starter layout for a Streamlit dashboard.

## Features

- **Data ingestion** — `corn_stats.data` pulls the league table and team pages straight from the official website.
- **Advanced metrics** — `corn_stats.features` computes eFG%, TS%, Net Rating, and a set of other team indicators.
- **Visualizations** — `corn_stats.viz` produces interactive Plotly charts featuring team logos.
- **Exploratory notebooks** — `notebooks/draft.ipynb` documents the analysis workflow and experiments.

## Repository Layout

```
assets/              # Team logos
data/
  tables/            # League table CSV
  teams/             # Team-level stats CSV
notebooks/
  draft.ipynb        # Current exploratory notebook
src/
  corn_stats/        # Main package (config, data, features, viz)
  main.py            # Streamlit entry-point scaffold
  pages/             # Streamlit page modules (WIP)
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
  df.to_csv(TABLES_DATA_PATH / "north_liga_df.csv", index=False)
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

## Streamlit App (WIP)

When you're ready to wire up the UI:

```bash
streamlit run src/main.py
```

`src/main.py` and `src/pages/` can be populated incrementally, pulling ready-made helpers from the `corn_stats` package.

## Notebooks

Launching JupyterLab:

```bash
jupyter lab
```

The `draft.ipynb` notebook already imports `corn_stats`. For the cleanest setup, run it from within an activated virtual environment where the package was installed via `pip install -e .`.

