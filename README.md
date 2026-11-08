# TrendPulse — What's Actually Trending Right Now

A mini project that follows one theme, *what trends on YouTube and why*, through the whole analysis loop: core Python, NumPy/Pandas
wrangling, visual exploration, and SQL plus spreadsheet reporting. It ends in a content strategy briefing for a media-analytics team.

Each Part is **self-contained**: it has its own data copy, `requirements.txt` and `README.md` (install/run steps, design decisions and
written interpretation), and never reads from another Part's folder.

| Part | Folder | What it covers |
|---|---|---|
| 1 — Python Foundations & Data Structures | [`part1_python_foundations/`](part1_python_foundations/) | loading function, core-Python type cleaning with try/except, list/tuple/set/dict/nested dict, scope, loops over titles, rule-based `classify_video`, refactor |
| 2 — NumPy & Pandas Data Wrangling | [`part2_numpy_pandas/`](part2_numpy_pandas/) | loop-free NumPy engagement score, broadcasting, data-quality fixes, filtering, merge/groupby/concat, time-to-trend and lifespan |
| 3 — Visualization, EDA & Business Thinking | [`part3_visualization_eda/`](part3_visualization_eda/) | 6 Matplotlib + 2 Plotly charts with interpretations, skew and IQR outliers, correlation, funnel, retention, cohorts, content briefing |
| 4 — SQL & Spreadsheet Analysis | [`part4_sql_spreadsheet/`](part4_sql_spreadsheet/) | 3-table MySQL schema with PK/FK, LOAD DATA, 10+ queries with output, Excel workbook (pivot, VLOOKUP, COUNTIF/SUM/AVERAGE, filter/sort, conditional formatting, named ranges), SQL ↔ spreadsheet cross-check |

## Dataset

**Trending YouTube Video Statistics** by Mitchell J, published on Kaggle:
<https://www.kaggle.com/datasets/datasnaek/youtube-new>. This is not my own dataset.

This project uses the files **as distributed on the program LMS**: `USvideos.csv`, `GBvideos.csv`, `INvideos.csv` (46,230 rows in total)
and `categories.csv`. The README shipped with that LMS copy states that the files are a *synthetic reproduction* with the same schema
and the same kinds of mess as the Kaggle files (duplicates, removed videos, blank counts, `yy.dd.mm` dates, `[none]` tags). All findings
therefore describe that copy. The notebooks run unchanged on the real Kaggle CSVs, but the numbers quoted in the write-ups would change.

No personal or private data is included. No API keys, network services or paid tools are needed.

## Quick start

Each notebook is a Google Colab notebook. Clone the repository, `%cd` into a Part's folder and use **Runtime → Restart and run all**.
Locally, run `pip install -r requirements.txt jupyter` inside the folder and open the notebook. Part 4 runs with MySQL 8 (Workbench or
the CLI) and Excel; see its README for the run order.
