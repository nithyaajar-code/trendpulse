# Part 1 — Python Foundations & Data Structures

Loads three countries of daily YouTube trending lists and cleans, organises and labels them in **core Python**.
Pandas is used only for `pd.read_csv()` and `df.to_dict("records")` (both inside `load_country()`).

## Contents

| Path | What it is |
|---|---|
| `part1_python_foundations.ipynb` | the notebook (saved with outputs from one clean *Restart and run all*) |
| `data/USvideos.csv`, `data/GBvideos.csv`, `data/INvideos.csv` | country trending files, untrimmed (16,080 + 15,075 + 15,075 = **46,230 rows**) |
| `data/categories.csv` | `category_id → category_name` lookup (17 rows) |
| `requirements.txt` | dependencies (`pandas` only, everything else is the standard library) |

## Install and run

**Google Colab**
1. `!git clone <this repository URL>` then `%cd trendpulse/part1_python_foundations`
   (or upload `part1_python_foundations.ipynb` together with the `data/` folder).
2. Colab already has pandas. Run **Runtime → Restart and run all**.

**Locally**
```bash
cd part1_python_foundations
pip install -r requirements.txt jupyter
jupyter notebook part1_python_foundations.ipynb     # then Kernel → Restart & Run All
```
The notebook reads only from `data/` (relative path), needs no network and does not use any other Part's folder.

## Countries and files

US, GB and IN — 46,230 raw rows, all columns kept (the files are ~4.5 MB each, so no trimming was needed).
Every file is loaded with `load_country(path, country, max_rows=None)`, which checks that the 13 required columns are present and
returns a list of dictionaries with a `country` field added. Records loaded: **US 16,080 · GB 15,075 · IN 15,075**.

## Cleaning rules

All values are read as text (`dtype=str, keep_default_na=False`) so that every conversion happens in core Python inside
`try/except`, with failures counted per field.

| Field | Conversion | Blank / bad value → | Reason |
|---|---|---|---|
| `views` | `int` | drop record | core metric; cannot be ranked or classified without it |
| `likes`, `dislikes`, `comment_count` | `int(float(x))` (likes are stored as `2155.0`) | keep record, value `None` | one missing count should not discard valid views/dates; `None` ≠ a real zero |
| `comments_disabled`, `ratings_disabled`, `video_error_or_removed` | `"True"/"False"` → `bool` | `False` (platform default), failure counted | |
| `trending_date` | `yy.dd.mm` → `datetime.date` (`17.14.11` = 14 Nov 2017) | drop record | a record cannot be placed in time without it |
| `publish_time` | `%Y-%m-%dT%H:%M:%S.%fZ` → `datetime` | keep, `None` | only needed for time-to-trend |
| `category_id` | `int`, name via `category_names` | keep, name `"Unknown"` | |

* Negative or fractional counts are treated as bad values.
* Records of **removed/errored videos** are dropped (92).
* **Duplicates** = same `(country, video_id, trending_date)` tuple; 230 dropped.
* Result on this copy: 0 parse failures in every field, 12 blank `likes`, 36 blank `comment_count`;
  **45,908 clean records** (99.3% kept).

## Classification thresholds (`classify_video`)

| Constant | Value | Meaning |
|---|---|---|
| `VIRAL_VIEWS` | 2,000,000 | ≈ top 10% of trending records |
| `STEADY_VIEWS` | 100,000 | below this a trending record is small |
| `DIVISIVE_RATIO` | 0.80 | like ratio `likes/(likes+dislikes)` below this = Divisive |
| `VIRAL_MIN_RATIO` | 0.90 | a viral hit must also be well liked |

Order of rules: no/zero views → *Low Engagement*; ratings disabled or likes/dislikes missing or zero votes → *Unrated*;
ratio < 0.80 → *Divisive*; ≥ 2M views with ratio ≥ 0.90 and comments enabled → *Viral Hit* (otherwise *Steady Performer*);
≥ 100k views → *Steady Performer*; else *Low Engagement*.
Result: Steady Performer 31,191 · Low Engagement 8,005 · Viral Hit 4,236 · Divisive 1,925 · Unrated 551.

## Design decisions

* **Strings in, Python types out.** Reading everything as text keeps Pandas from guessing types, so the cleaning step is genuinely core Python and every failure is visible.
* **Tuples where data is a fixed fact** (`(video_id, trending_date, views, likes)` and the dedup key) — immutable and hashable, so they can be set members.
* **Sets for cross-country questions** — `&` and `-` give "trended in several countries" (339 videos; 20 in all three) and "unique to one country" directly.
* **Dictionaries for counting and lookup** (channels, labels, category names) and a **nested dictionary** for country → category → count.
* **Refactor:** the repeated "increment a dict counter" block became `count_by(items, key_func)`, verified to reproduce all three earlier results.

## Data source

*Trending YouTube Video Statistics* (Mitchell J, Kaggle: <https://www.kaggle.com/datasets/datasnaek/youtube-new>), using the copy of the
files distributed on the program LMS. Not my own data. Note: the README that accompanies the LMS copy states that these files are a
**synthetic reproduction** with the same schema and quirks as the Kaggle dataset, so the numbers describe that copy, not real YouTube.
