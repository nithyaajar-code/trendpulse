# Part 2 — NumPy & Pandas Data Wrangling

Computes a transparent engagement score with NumPy (no loops), cleans the trending data in Pandas, and uses grouping, merging and
concatenation to answer what trends and for how long. Self-contained: reads only this folder's `data/`, with no network calls.

## Contents

| Path | What it is |
|---|---|
| `part2_numpy_pandas.ipynb` | the notebook (saved with outputs from one clean *Restart and run all*) |
| `data/USvideos.csv`, `data/GBvideos.csv`, `data/INvideos.csv` | country files, untrimmed (46,230 rows) |
| `data/categories.csv` | `category_id → category_name` lookup |
| `requirements.txt` | `numpy`, `pandas` |

## Install and run

**Google Colab:** clone the repo, `%cd trendpulse/part2_numpy_pandas`, then **Runtime → Restart and run all** (numpy/pandas are preinstalled).

**Locally**
```bash
cd part2_numpy_pandas
pip install -r requirements.txt jupyter
jupyter notebook part2_numpy_pandas.ipynb        # Kernel → Restart & Run All
```

## Engagement score

All steps use whole-array NumPy operations.

* like ratio = `likes / (likes + dislikes)` via `np.divide(..., where=votes > 0)`; there are no votes for 539 records (ratings disabled), so
  their ratio stays NaN and the score uses a neutral 0.5 for them.
* comment rate = `comments / views` with the same safe division (default 0).
* views, likes and comments are min-max normalised **on the log scale** (`np.log1p`): raw min-max puts the median record at ≈0.001,
  because one 360 M-view record sets the maximum.

`engagement = 0.25·views_n + 0.30·likes_n + 0.25·comments_n + 0.20·like_ratio`

| Weight | Reasoning |
|---|---|
| views 0.25 | Reach matters, but every record has already been selected *for* views by being on the trending list, so views should not dominate. |
| likes 0.30 | The largest weight: a like is an active positive action and grows with reach. |
| comments 0.25 | The strongest effort a viewer makes, but comments also rise with controversy, so they weigh less than likes. |
| like ratio 0.20 | A quality check that separates liked videos from ones that are only seen (for example, divisive news). |

The weights sum to 1, so the score is in [0, 1]. The top 10% (score ≥ 0.693, 4,591 records) is flagged with a boolean mask.

## Data-quality issues and how they were handled

| Issue | Size | Handling |
|---|---|---|
| Duplicate rows | 230 | `drop_duplicates(subset=["country","video_id","trending_date"])` |
| Removed / errored videos | 92 rows | dropped (stats not valid) |
| Missing `description` | 1,624 rows (3.51% of the raw rows) | `fillna("")`: free text that no calculation uses |
| Missing `likes` | 12 (0.03%) | filled from the same video's neighbouring trending day (groupby ffill/bfill → `fillna`); leftovers dropped |
| Missing `comment_count` | 36 (0.08%) | same as likes; 0 would be confused with `comments_disabled` |
| Rows with no neighbouring day to fill from | 4 | `dropna` |
| `likes`/`comment_count` stored as float | — | cast to `int64` after filling |
| `trending_date` stored as `yy.dd.mm` text | — | `pd.to_datetime(format="%y.%d.%m")`, 0 failures |
| `publish_time` as UTC text | — | parsed, timezone removed |
| `tags == "[none]"` | 3,763 rows | kept: it means "no tags" |
| Zeros when ratings/comments are disabled | — | kept as genuine zeros; ratios guard the denominators |
| Countries cover different windows (US 80 days, GB/IN 75 days) | — | the days × countries array uses the 75 shared days |

Percentages in the table are calculated on the 46,230 raw rows, before the drops. The notebook prints the exact table in section 2.1.

**Duplicate definition:** the same `video_id` on the same `trending_date` in the same `country`. A daily trending list shows a video
once, so a second row with that key is the same observation recorded twice. Found and removed: **230** (they are also exact duplicates of
the full row). Clean table: **45,904 rows**.

**Category merge:** a left merge with `validate="many_to_one"`. 45,904 rows went in and 45,904 came out, with 0 records lost and 0 left
without a name. Movies, Nonprofits & Activism and Shows exist in the lookup but have no trending records.

## Key results (see the notebook for the tables)

* Category share of records: Entertainment 26.7%, Music 22.4%, People & Blogs 8.3%.
* Median days_to_trend = 1. 63.3% of videos trend within a day of publishing, and 90.6% within a week.
* Average lifespan: 3.05 days overall, Music 5.32 days, News & Politics 1.72 days. The longest-lasting videos stay 25 days.
