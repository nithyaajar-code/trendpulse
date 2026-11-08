# Part 4 — SQL & Spreadsheet Analysis

The cleaned trending data is loaded into a three-table **MySQL** database and queried with SQL. A shareable **Excel workbook**
(`trendpulse_workbook.xlsx`) answers the same questions with a pivot table and formulas. Self-contained: everything needed is in this folder.

## Contents

| Path | What it is |
|---|---|
| `raw_data/` | the original country files `USvideos.csv`, `GBvideos.csv`, `INvideos.csv` and `categories.csv` (input to the prep script) |
| `prepare_tables.py` | Pandas script that cleans the raw files and writes the three tables to `data/` |
| `data/categories.csv` | 17 rows: `category_id, category_name` |
| `data/videos.csv` | 14,684 rows, one per unique video: `video_id, title, channel_title, category_id, publish_time, comments_disabled, ratings_disabled` |
| `data/trending_records.csv` | 45,860 rows, one per video per day per country: `record_id, video_id, country, trending_date, views, likes, dislikes, comment_count` |
| `trendpulse.sql` | `CREATE DATABASE` / `CREATE TABLE` + `LOAD DATA` statements + row counts (recreates everything from scratch) |
| `queries.sql` | the analysis queries (Q1–Q10) |
| `trendpulse_workbook.xlsx` | the spreadsheet workbook (sheets: Summary, Pivot, Records, Categories) |
| `tools/build_workbook.py`, `tools/add_pivot_libreoffice.py` | how the workbook was generated (see "Workbook build") |
| `requirements.txt` | pandas, openpyxl |

## Tools used

* Python 3 + **pandas** (table preparation) and **openpyxl** (workbook data, formulas, formatting)
* **MySQL 8.0** (server 8.0.40), with the statements written to run in **MySQL Workbench** or the `mysql` command-line client
* **LibreOffice Calc 25.8**, used headless to insert the PivotTable and recalculate the formulas before saving the `.xlsx`.
  The file opens normally in **Microsoft Excel**.

## How the CSV tables were prepared (`prepare_tables.py`)

1. Read the three country files with `pd.read_csv()`, add a `country` column and stack them with `pd.concat()` (46,230 rows).
2. Parse `trending_date` (stored as `yy.dd.mm`, e.g. `17.14.11` = 2017-11-14) and `publish_time` (ISO UTC).
3. `drop_duplicates(subset=["country","video_id","trending_date"])`: removes 230 duplicate rows.
4. Drop the 92 rows of removed/errored videos (`video_error_or_removed`).
5. Drop the 48 rows with a blank `likes` or `comment_count` (0.1%), so every count column is a complete integer and can be `NOT NULL`.
6. **categories**: the lookup file, unchanged.
7. **videos**: `drop_duplicates(subset="video_id")` on the cleaned rows, keeping each video's descriptive columns (title, channel,
   category, publish time, flags) from its first trending day. The script asserts that every `category_id` exists in `categories`.
8. **trending_records**: the per-day metrics, plus a surrogate `record_id` (1…n). The script asserts that every `video_id` exists in `videos`.
9. Each table is written with `df.to_csv(..., index=False)`.

Run it from this folder with `python prepare_tables.py`. The committed `data/` files are its output.

## Run order

```bash
cd part4_sql_spreadsheet
python prepare_tables.py                       # optional: data/ is already committed
mysql --local-infile=1 -u root -p < trendpulse.sql
mysql -u root -p -t trendpulse < queries.sql
```

**In MySQL Workbench:**
1. Enable local loading, either with `SET GLOBAL local_infile = 1;` or by adding `OPT_LOCAL_INFILE=1` under the connection's *Advanced → Others*.
2. Open `trendpulse.sql`, replace the three `'data/....csv'` paths with absolute paths
   (for example, `'C:/trendpulse/part4_sql_spreadsheet/data/categories.csv'`), and execute the whole script (⚡).
   Alternatively, run only the `CREATE` statements and load each CSV with **Table Data Import Wizard** in this order:
   categories → videos → trending_records.
3. Open and execute `queries.sql`.

`trendpulse.sql` starts with `DROP DATABASE IF EXISTS trendpulse`, so it always rebuilds from scratch.

## Schema design

```
categories (category_id PK, category_name UNIQUE)
     1
     │
     ∞
videos (video_id PK, title, channel_title, category_id FK → categories, publish_time, comments_disabled, ratings_disabled)
     1
     │
     ∞
trending_records (record_id PK, video_id FK → videos, country, trending_date, views, likes, dislikes, comment_count,
                  UNIQUE (video_id, trending_date, country))
```

Design decisions:
* **Three tables, no repetition:** a video's title, channel and category are stored once in `videos`, not repeated on every daily
  record (normalisation). The daily numbers that change from day to day live in `trending_records`.
* **Surrogate key** `record_id` for the records table, plus a **UNIQUE (video_id, trending_date, country)** constraint that enforces the
  duplicate rule from the cleaning step inside the database.
* **Foreign keys:** `videos.category_id → categories` (`ON DELETE RESTRICT`: a category in use cannot be deleted) and
  `trending_records.video_id → videos` (`ON DELETE CASCADE`: deleting a video removes its daily records).
  Parents are loaded first so every child row finds its parent.
* **`video_id` uses a binary collation (`utf8mb4_bin`).** YouTube IDs are case-sensitive, and MySQL's default collation is not. Without
  this, two different IDs such as `abC…` and `ABc…` would collide on the primary key.
* **Types:** `BIGINT UNSIGNED` for counts (views reach 360 M, and counts cannot be negative), `DATE` / `DATETIME` for time, `CHAR(2)` for
  the country code, `BOOLEAN` for the flags.
* **Indexes** on the foreign keys and on `(country, trending_date)`, which the queries filter and join on.

## Row counts after loading

```text
+------------------+-----------+
| table_name       | row_count |
+------------------+-----------+
| categories       |        17 |
| videos           |     14684 |
| trending_records |     45860 |
+------------------+-----------+
```

These match the CSV files: 17, 14,684 and 45,860 data rows.

## Queries and their output

11 query blocks (14 statements) cover SELECT/WHERE, ORDER BY, LIMIT, DISTINCT, aliases, GROUP BY + aggregates + HAVING, and INNER, LEFT
and RIGHT JOIN. Output is from MySQL 8.0.40 (`mysql -t`).

### Q1. DISTINCT + alias: which countries are in the data?

```sql
SELECT DISTINCT country AS country_code
FROM trending_records
ORDER BY country_code;
```

Output:

```text
+--------------+
| country_code |
+--------------+
| GB           |
| IN           |
| US           |
+--------------+
```

### Q2. WHERE + ORDER BY + LIMIT + aliases: the 10 most-viewed trending records in the US

```sql
SELECT tr.record_id,
       tr.video_id,
       tr.trending_date AS day,
       tr.views         AS total_views,
       tr.likes         AS total_likes
FROM trending_records AS tr
WHERE tr.country = 'US'
ORDER BY tr.views DESC
LIMIT 10;
```

Output:

```text
+-----------+-------------+------------+-------------+-------------+
| record_id | video_id    | day        | total_views | total_likes |
+-----------+-------------+------------+-------------+-------------+
|     41469 | HPG-bd_JLxn | 2018-01-11 |   129229245 |     5964932 |
|     40474 | yd4LMLxXzWE | 2018-01-06 |   119711498 |     6795138 |
|     41271 | HPG-bd_JLxn | 2018-01-10 |   109129467 |     5037172 |
|     36685 | Nc1MUQvmyWO | 2017-12-18 |    97553795 |     3371264 |
|     40274 | yd4LMLxXzWE | 2018-01-05 |    97342335 |     5525406 |
|     41073 | HPG-bd_JLxn | 2018-01-09 |    90679797 |     4185576 |
|     36487 | Nc1MUQvmyWO | 2017-12-17 |    83611280 |     2889439 |
|     35294 | h5eHGd1GiiS | 2017-12-11 |    82623566 |     4064707 |
|     40075 | yd4LMLxXzWE | 2018-01-04 |    80368655 |     4561935 |
|     40873 | HPG-bd_JLxn | 2018-01-08 |    70261074 |     3243094 |
+-----------+-------------+------------+-------------+-------------+
```

### Q3. DISTINCT: which category ids actually appear among the videos?

```sql
SELECT DISTINCT category_id AS used_category_id
FROM videos
ORDER BY used_category_id;
```

Output:

```text
+------------------+
| used_category_id |
+------------------+
|                1 |
|                2 |
|               10 |
|               15 |
|               17 |
|               19 |
|               20 |
|               22 |
|               23 |
|               24 |
|               25 |
|               26 |
|               27 |
|               28 |
+------------------+
```

### Q4. GROUP BY + aggregates: records and average views per country (cross-check value #1)

```sql
SELECT country,
       COUNT(*)                 AS records,
       COUNT(DISTINCT video_id) AS unique_videos,
       ROUND(AVG(views), 2)     AS avg_views,
       SUM(views)               AS total_views
FROM trending_records
GROUP BY country
ORDER BY records DESC;
```

Output:

```text
+---------+---------+---------------+------------+-------------+
| country | records | unique_videos | avg_views  | total_views |
+---------+---------+---------------+------------+-------------+
| US      |   15952 |          5064 | 1014684.39 | 16186245314 |
| GB      |   14954 |          4111 | 1585219.48 | 23705372062 |
| IN      |   14954 |          5868 |  953066.25 | 14252152760 |
+---------+---------+---------------+------------+-------------+
```

### Q5. INNER JOIN (3 tables) + GROUP BY + HAVING: categories whose average views per trending record exceed 500,000 (cross-check value #2 = Music)

```sql
SELECT c.category_name,
       COUNT(*)               AS records,
       ROUND(AVG(tr.views), 2) AS avg_views
FROM trending_records AS tr
INNER JOIN videos     AS v ON v.video_id = tr.video_id
INNER JOIN categories AS c ON c.category_id = v.category_id
GROUP BY c.category_name
HAVING AVG(tr.views) > 500000
ORDER BY avg_views DESC;
```

Output:

```text
+------------------+---------+------------+
| category_name    | records | avg_views  |
+------------------+---------+------------+
| Music            |   10274 | 3195081.39 |
| Entertainment    |   12236 |  901878.42 |
| Comedy           |    3247 |  602876.60 |
| Film & Animation |    2288 |  577717.31 |
| People & Blogs   |    3792 |  552318.87 |
| Gaming           |    2054 |  509044.00 |
+------------------+---------+------------+
```

**Why INNER JOIN:** the question is about records whose video *and* category are known. Each trending record needs its video (for `category_id`) and that category's name, and a record without a match could not be grouped by category anyway. The foreign keys guarantee that every record has a video and every video a category, so INNER JOIN loses nothing and is the simplest correct join. `HAVING` (not `WHERE`) filters on the aggregate `AVG(views)` after grouping.

### Q6. GROUP BY + HAVING: channels with at least 5 distinct trending videos (top 10 by video count)

```sql
SELECT v.channel_title,
       COUNT(DISTINCT v.video_id) AS trending_videos,
       COUNT(*)                   AS trending_records,
       MAX(tr.views)              AS best_record_views
FROM videos AS v
INNER JOIN trending_records AS tr ON tr.video_id = v.video_id
GROUP BY v.channel_title
HAVING COUNT(DISTINCT v.video_id) >= 5
ORDER BY trending_videos DESC, trending_records DESC
LIMIT 10;
```

Output:

```text
+-----------------------+-----------------+------------------+-------------------+
| channel_title         | trending_videos | trending_records | best_record_views |
+-----------------------+-----------------+------------------+-------------------+
| UltimateUnboxing65    |             522 |             1421 |          60717690 |
| QuietChallenge75      |             466 |             2446 |          56884049 |
| OfficialReview41      |             457 |             1575 |          37902491 |
| InsaneReaction46      |             321 |             1223 |          26603358 |
| Brand NewChallenge45  |             302 |             1167 |          30277219 |
| UltimateSpeech20      |             292 |              765 |           7552931 |
| CrazyTrailer91        |             283 |             1008 |          52818030 |
| WildHighlights7       |             245 |              681 |          10825748 |
| UltimateVlog96        |             233 |              561 |          16821972 |
| SurprisingChallenge82 |             215 |              379 |           4830443 |
+-----------------------+-----------------+------------------+-------------------+
```

**Why INNER JOIN:** only channels that actually have trending records are relevant to the question, so rows without a match on either side should be excluded. That is exactly what an inner join does.

### Q6b. how many channels pass that HAVING filter, out of all channels?

```sql
SELECT SUM(n_videos >= 5) AS channels_with_5plus_videos,
       COUNT(*)            AS all_channels
FROM (SELECT channel_title, COUNT(*) AS n_videos FROM videos GROUP BY channel_title) AS per_channel;
```

Output:

```text
+----------------------------+--------------+
| channels_with_5plus_videos | all_channels |
+----------------------------+--------------+
|                        362 |          438 |
+----------------------------+--------------+
```

### Q7. INNER JOIN (3 tables): trending records with video title and category name - top 10 in GB

```sql
SELECT tr.trending_date,
       v.title,
       c.category_name,
       tr.views
FROM trending_records AS tr
INNER JOIN videos     AS v ON v.video_id = tr.video_id
INNER JOIN categories AS c ON c.category_id = v.category_id
WHERE tr.country = 'GB'
ORDER BY tr.views DESC
LIMIT 10;
```

Output:

```text
+---------------+--------------------------------------------------+---------------+-----------+
| trending_date | title                                            | category_name | views     |
+---------------+--------------------------------------------------+---------------+-----------+
| 2018-01-05    | Lena Ortiz - Monsoon (Live)                      | Music         | 360760164 |
| 2018-01-27    | The Hollow Pines - Phones (Official Video) WATCH | Music         | 343297002 |
| 2018-01-04    | Lena Ortiz - Monsoon (Live)                      | Music         | 286714357 |
| 2018-01-26    | The Hollow Pines - Phones (Official Video) WATCH | Music         | 282812154 |
| 2017-12-24    | Rook & Vale - Phones (Official Video) WATCH      | Music         | 255362869 |
| 2018-01-03    | Lena Ortiz - Monsoon (Live)                      | Music         | 236275528 |
| 2018-01-25    | The Hollow Pines - Phones (Official Video) WATCH | Music         | 230704137 |
| 2018-01-02    | Lena Ortiz - Monsoon (Live)                      | Music         | 210747294 |
| 2017-12-23    | Rook & Vale - Phones (Official Video) WATCH      | Music         | 200444300 |
| 2018-01-24    | The Hollow Pines - Phones (Official Video) WATCH | Music         | 181785943 |
+---------------+--------------------------------------------------+---------------+-----------+
```

**Why INNER JOIN (3 tables):** each output row needs fields from all three tables (date and views from `trending_records`, title from `videos`, name from `categories`). A record is only meaningful when all three parts exist, so non-matching rows must not appear.

### Q8. LEFT JOIN: categories that have no video in the data

```sql
SELECT c.category_id,
       c.category_name,
       COUNT(v.video_id) AS videos
FROM categories AS c
LEFT JOIN videos AS v ON v.category_id = c.category_id
GROUP BY c.category_id, c.category_name
HAVING COUNT(v.video_id) = 0
ORDER BY c.category_id;
```

Output:

```text
+-------------+-----------------------+--------+
| category_id | category_name         | videos |
+-------------+-----------------------+--------+
|          29 | Nonprofits & Activism |      0 |
|          30 | Movies                |      0 |
|          43 | Shows                 |      0 |
+-------------+-----------------------+--------+
```

**Why LEFT JOIN:** the question is about categories that have *no* video, so every category must be kept even when no video matches. A LEFT JOIN from `categories` keeps all of them and fills the video columns with NULL, and `COUNT(v.video_id) = 0` picks those out. An INNER JOIN would silently drop exactly the rows we are looking for.

### Q9. RIGHT JOIN: every video, with its number of US trending days (0 if it never trended in the US). Summarised: how many videos trended in the US, and how many only elsewhere?

```sql
SELECT CASE WHEN us_days = 0 THEN 'never trended in US' ELSE 'trended in US' END AS us_status,
       COUNT(*)                                                                   AS videos
FROM (
    SELECT v.video_id,
           COUNT(us.record_id) AS us_days
    FROM trending_records AS us
    RIGHT JOIN videos AS v
           ON v.video_id = us.video_id
          AND us.country = 'US'          -- filter in ON, not WHERE, so non-US videos are kept
    GROUP BY v.video_id
) AS per_video
GROUP BY us_status
ORDER BY us_status;
```

Output:

```text
+---------------------+--------+
| us_status           | videos |
+---------------------+--------+
| never trended in US |   9620 |
| trended in US       |   5064 |
+---------------------+--------+
```

**Why RIGHT JOIN:** we want *every video* (the right-hand table), including the ones with no US record, which get a NULL that `COUNT` turns into 0. `trending_records` is written on the left, so a RIGHT JOIN is what keeps all rows of `videos`. The US filter sits in the `ON` clause: putting `country = 'US'` in `WHERE` would throw away the NULL rows and turn the query back into an inner join. (This is the mirror image of `videos LEFT JOIN trending_records`; the RIGHT form is used here to show the join type.)

### Q10. Cross-check helpers: one country count and one category average, as single values

```sql
SELECT COUNT(*) AS us_records FROM trending_records WHERE country = 'US';

SELECT ROUND(AVG(tr.views), 2) AS music_avg_views
FROM trending_records AS tr
INNER JOIN videos AS v ON v.video_id = tr.video_id
WHERE v.category_id = 10;

SELECT ROUND(AVG(views), 2) AS overall_avg_views, COUNT(*) AS all_records FROM trending_records;
```

Output:

```text
+------------+
| us_records |
+------------+
|      15952 |
+------------+

+-----------------+
| music_avg_views |
+-----------------+
|      3195081.39 |
+-----------------+

+-------------------+-------------+
| overall_avg_views | all_records |
+-------------------+-------------+
|        1180631.71 |       45860 |
+-------------------+-------------+
```


## Spreadsheet workbook (`trendpulse_workbook.xlsx`)

| Sheet | Contents |
|---|---|
| **Summary** | headline numbers built with COUNTIF / COUNTA / SUM / AVERAGE / AVERAGEIF / PERCENTILE on named ranges |
| **Pivot** | PivotTable: average views by category and country |
| **Records** | all 45,860 trending records (12 columns) with a VLOOKUP category-name column, filter, sort and conditional formatting |
| **Categories** | the lookup table (17 rows) plus a small "try a lookup" cell |

The Records sheet is built by joining `trending_records.csv` with `videos.csv` (title, channel, category_id) in pandas. The
**category_name column is not copied from the data**: it is computed in the sheet with VLOOKUP.

### (a) Pivot table (sheet *Pivot*, named `AvgViewsPivot`)
* Source range: `Records!A1:L45861` (all records, with headers)
* **Rows:** `category_name` (14 categories) · **Columns:** `country` (GB, IN, US) · **Values:** `views`, summarised by **Average**
* Row and column grand totals are on ("Total Result").
* Example values: Music GB 3,733,341 · Music US 2,872,035 · Music overall 3,195,081 · grand total 1,180,632.
* To recreate it by hand in Excel: select `Records!A1:L45861` → *Insert → PivotTable → New worksheet* → drag `category_name` to Rows,
  `country` to Columns and `views` to Values → *Value Field Settings → Average*.

### (b) Lookup sheet and VLOOKUP
* Sheet **Categories**, `A1:B18`: `category_id` | `category_name`.
* Named range **`cat_table`** = `Categories!$A$2:$B$18`.
* In **Records**, column H (`category_name`), row 2 (filled down to row 45,861):
  `=VLOOKUP(G2, cat_table, 2, FALSE)`. This takes the `category_id` in G2, finds it in the first column of `cat_table`, and returns
  column 2 (the name). `FALSE` forces an exact match.
* The same formula is in `Categories!F2` (`=VLOOKUP(E2,cat_table,2,FALSE)`), so a reader can type an id in E2 and see its name.
  (In Excel 365 the equivalent is `=XLOOKUP(G2, Categories!$A$2:$A$18, Categories!$B$2:$B$18)`.)

### (c) COUNTIF, SUM and AVERAGE headline numbers (sheet *Summary*, column B; the formula text is also in column C)

| Cell | Metric | Formula | Value |
|---|---|---|---|
| B4 | Records - US | `=COUNTIF(country_col,"US")` | 15,952 |
| B5 | Records - GB | `=COUNTIF(country_col,"GB")` | 14,954 |
| B6 | Records - IN | `=COUNTIF(country_col,"IN")` | 14,954 |
| B7 | Records - total | `=COUNTA(country_col)` | 45,860 |
| B8 | Total views | `=SUM(views_col)` | 54,143,770,136 |
| B9 | Overall average views | `=AVERAGE(views_col)` | 1,180,631.71 |
| B10 | Average views - US | `=AVERAGEIF(country_col,"US",views_col)` | 1,014,684.39 |
| B11 | Average views - Music | `=AVERAGEIF(category_col,"Music",views_col)` | 3,195,081.39 |
| B12 | Records in Music | `=COUNTIF(category_col,"Music")` | 10,274 |
| B13 | 90th-percentile views | `=PERCENTILE(views_col,0.9)` | 2,026,787.30 |
| B14 | Records in the top 10% | `=COUNTIF(views_col,">="&B13)` | 4,586 |

### (d) Filters and sorting
* **AutoFilter** on the Records header row, range `A1:L45861`, so every column has a filter drop-down (for example, filter `country` = IN
  and `category_name` = News & Politics).
* **Sorting:** the records are sorted by `views`, **largest to smallest** (row 2 is the most-viewed record: *Lena Ortiz - Monsoon
  (Live)*, GB, 360,760,164 views). The sort condition is stored on the filter for column I (`views`, descending).
* The header row is frozen (`Freeze Panes` at A2), so it stays visible while scrolling.

### (e) Conditional formatting: top 10% of views
* Range: `Records!I2:I45861` (the views column).
* Rule: **Top/Bottom Rules → Top 10%**, i.e. rank 10, *percent* ticked. Format: light-amber fill (`#FFE699`) with bold dark-orange text.
* This highlights every record with views ≥ the 90th percentile (2,026,787.3). Summary!B14 confirms that 4,586 records (10.0%) are highlighted.

### (f) Named ranges (Formulas → Name Manager)

| Name | Refers to | Used in |
|---|---|---|
| `cat_table` | `Categories!$A$2:$B$18` | every VLOOKUP in `Records!H:H` and `Categories!F2` |
| `views_col` | `Records!$I$2:$I$45861` | SUM, AVERAGE, AVERAGEIF, PERCENTILE, COUNTIF in Summary |
| `country_col` | `Records!$C$2:$C$45861` | COUNTIF / COUNTA / AVERAGEIF in Summary |
| `category_col` | `Records!$H$2:$H$45861` | `AVERAGEIF(category_col,"Music",views_col)`, `COUNTIF(category_col,"Music")` |

### Workbook build
`tools/build_workbook.py` (openpyxl) writes the sheets, formulas, named ranges, filter/sort and conditional formatting.
`tools/add_pivot_libreoffice.py` then opens the file in LibreOffice Calc, inserts the PivotTable, recalculates every formula (so the file
also shows values in viewers that do not recalculate) and saves `trendpulse_workbook.xlsx`. Only the final workbook is committed.

## Cross-check: SQL vs spreadsheet

| Value | SQL (query) | Spreadsheet (cell) | Match |
|---|---|---|---|
| Number of US trending records | **15,952** (Q4 / Q10 `COUNT(*) ... WHERE country = 'US'`) | **15,952** (`Summary!B4` `=COUNTIF(country_col,"US")`; Pivot) | ✅ |
| Average views per record, Music | **3,195,081.39** (Q5 / Q10 `AVG(tr.views)` joined to Music) | **3,195,081.39** (`Summary!B11` `=AVERAGEIF(category_col,"Music",views_col)`; Pivot "Music / Total Result") | ✅ |
| Overall average views | **1,180,631.71** (Q10) | **1,180,631.71** (`Summary!B9` `=AVERAGE(views_col)`) | ✅ |
| Average views, US | **1,014,684.39** (Q4) | **1,014,684.39** (`Summary!B10`; Pivot "Total Result / US") | ✅ |

The values agree exactly because both tools read the same cleaned tables, with the same 45,860 rows. The SQL side joins
`trending_records → videos → categories` on keys, and the spreadsheet side reaches the same category through VLOOKUP on `category_id`.

## Data source

*Trending YouTube Video Statistics* (Mitchell J, Kaggle: <https://www.kaggle.com/datasets/datasnaek/youtube-new>), in the copy distributed
on the program LMS. The README that accompanies that copy describes it as a synthetic reproduction with the same schema and quirks as the
Kaggle files.
