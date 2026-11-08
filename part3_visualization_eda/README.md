# Part 3 — Visualization, EDA & Business Thinking

Profiles the trending data, tells its story in 6 Matplotlib and 2 Plotly charts, and runs distribution, outlier, correlation, funnel,
retention and cohort analyses. It ends in a content strategy briefing. Self-contained: reads only this folder's `data/`.

Every interpretation below also appears in the notebook, directly under its chart or table.

## Contents

| Path | What it is |
|---|---|
| `part3_visualization_eda.ipynb` | the analysis notebook (saved with outputs from one clean *Restart and run all*) |
| `data/` | `USvideos.csv`, `GBvideos.csv`, `INvideos.csv` (untrimmed, 46,230 rows) and `categories.csv` |
| `charts/*.png` | the Matplotlib charts, saved by the notebook (supporting artifacts only) |
| `charts/*.html` | the two Plotly charts as standalone interactive pages (open in a browser) |
| `requirements.txt` | numpy, pandas, matplotlib, plotly |

## Install and run

**Google Colab:** clone the repo, `%cd trendpulse/part3_visualization_eda`, then **Runtime → Restart and run all**. All the libraries
are preinstalled in Colab.

**Locally**
```bash
cd part3_visualization_eda
pip install -r requirements.txt jupyter
jupyter notebook part3_visualization_eda.ipynb      # Kernel → Restart & Run All
```
Plotly charts render inline. Outside Colab the notebook uses the `notebook_connected` renderer, which loads plotly.js from a CDN.

## Data profile and cleaning

Raw combined shape: **46,230 × 17** (US 16,080 · GB 15,075 · IN 15,075). Columns with missing values:

| Column | Missing | % |
|---|---|---|
| likes | 12 | 0.03% |
| comment_count | 36 | 0.08% |
| description | 1,624 | 3.51% |

Cleaning steps:
1. Parse `trending_date` (`yy.dd.mm`) and `publish_time` (ISO UTC) as datetimes.
2. Drop duplicates on (country, video_id, trending_date), leaving 46,000 rows.
3. Drop removed/errored videos, leaving 45,908.
4. Drop blank likes or comment_count, leaving **45,860**.
5. Fill blank descriptions with `""`.
6. Left-merge the category names (0 records lost).
7. Add `days_to_trend`.

Unique videos per country: 15,043. Unique video IDs overall: 14,684.

## Charts and interpretations

### Chart 1: Trending records per category (bar)

**Interpretation.** Entertainment (26.7% of records) and Music (22.4%) together make up almost half of all trending records. The next
category, People & Blogs, has only 8.3%, and the long tail (Travel & Events, Pets & Animals, Autos & Vehicles) has under 2.5% each. Three
categories in the lookup (Movies, Nonprofits & Activism, Shows) never trend at all, so in this data trending is concentrated in a few
broad entertainment formats.

*Why a horizontal bar chart:* category is a nominal variable and the count is a magnitude, so sorted bars compare lengths directly, and
horizontal bars leave room for the long category names.

### Chart 2: Views, log scale (histogram)

**Interpretation.** On a log scale, views form a single hump centred near 300K (median 318,701), from about 1K up to 360M. The
mean (1,180,632) sits far to the right of the median because a small number of huge videos pull it up. In plain numbers the distribution is
strongly right-skewed (skewness ≈ 28), which is why a log axis is needed to see its shape at all.

*Why a histogram:* views is one continuous variable and the question is about its shape, which a histogram shows. The log10 x-axis keeps
the many small records from being squashed into one bar.

### Chart 3: Views vs likes (scatter)

**Interpretation.** On log–log axes, likes rise almost in proportion to views, a tight upward band (correlation of the logs ≈ 0.79).
The band is not perfectly tight: at the same view count, likes can differ by about ×10. Music (blue) sits at the top right with the most
views and likes. The flat row of points at the bottom (likes + 1 = 1) is the ratings-disabled videos, whose likes are a true zero.

*Why a scatter plot:* it compares two continuous variables for each video and shows the strength and shape of their relationship. The log
scales spread out the skewed values, and the top 3 categories plus a grey "Other" keep the colours readable.

### Chart 4: New videos entering the list per day (line)

**Interpretation.** Each country's list holds a steady 196–200 records a day (printed above), so the volume of trending records is
flat by design. The real day-to-day activity is **turnover**: on average about 77 new videos enter India's list each day, 62 enter the
US list and 53 enter GB's. India's list therefore churns fastest and GB's most slowly, which matches the shorter lifespans seen for India
in section 7.

*Why a line chart:* the x-axis is time (one point per day) and lines show trend and volatility over consecutive days. With one colour per
country, the three series can be compared on the same axis.

### Chart 5: Peak views by category (box plot)

**Interpretation.** Music's median peak views (≈ 992K) are almost three times the next category, Entertainment (≈ 350K), and its whole
box sits higher. The other categories cluster between ≈ 107K (Travel & Events) and ≈ 324K (Comedy) at the median. Every category has a long
upper tail of outliers, so the *typical* video and the *exceptional* video tell different stories.

*Why a box plot:* it compares the distribution (median, quartiles, spread and outliers) of a continuous variable across many groups at
once. The log y-axis is required because views span five orders of magnitude.

### Chart 6: Like ratio by category (bar)

**Interpretation.** Almost every category gets 91–97% likes among its votes, but News & Politics stands alone at about 72%. Roughly one
vote in four on a trending news video is a dislike. People & Blogs (91%) and Entertainment (93%) are the next lowest. News therefore
reaches the list through attention rather than approval, which fits its very short lifespan (section 7).

*Why a bar chart:* a ratio per nominal category is compared by bar length. The x-axis starts at 60% rather than zero so the 1–5 point
differences are visible; this is stated on the axis. News is highlighted in a contrasting colour because it is the finding.

### Plotly 1: Interactive views vs likes, title on hover

**Interpretation.** The interactive version of Chart 3 shows the same tight views–likes band. Hovering identifies individual
videos: the far top-right points are long-running Music videos (for example, *Lena Ortiz - Monsoon (Live)* with 360M peak views and 25 days
on GB's list). Clicking News & Politics in the legend isolates it: those points sit *below* the main band, with fewer likes for the same
views, consistent with its low like ratio.

*Why an interactive scatter:* with about 15,000 videos, hover-for-title and click-to-filter let a reader find specific videos and
categories that a static chart cannot label. The log axes again handle the skew.

### Plotly 2: Average views per category across countries (grouped bar)

**Interpretation.** Music has the highest average peak views in every country, and the gap is largest in GB (≈ 4.57M vs 3.40M in the
US and 2.77M in IN). Below Music the countries are close, but India's videos average higher in several categories (Comedy ≈ 753K vs 624K in
the US, Gaming ≈ 615K vs 483K). So GB is the most Music-driven market, while India's views are spread across more categories.

*Why a grouped bar chart:* it compares a numeric measure across two nominal variables (category × country). Grouping the three country bars
inside each category makes the within-category country comparison immediate. Hover gives the exact values.


## Distributions and outliers

| | views | likes |
|---|---|---|
| mean | 1,180,632 | 45,887 |
| median | 318,701 | 10,216 |
| exact mode | 16,000 (occurs 3×) | 0 (occurs 539×) |
| binned mode (log histogram) | ≈ 254,481 | ≈ 8,772 |
| skewness | 27.9 | 44.5 |

**Skewness conclusion.**
* **Views:** mean 1,180,632 > median 318,701 > binned mode ≈ 254,000. Mean > median > mode is the signature of a **right-skewed**
  distribution (skewness ≈ 28): most records sit in the hundreds of thousands, and a long tail of very large videos pulls the mean up.
  The exact mode (16,000, occurring only 3 times) is meaningless for an almost-unique count, which is why the binned mode is used.
* **Likes:** mean 45,887 > median 10,216 > binned mode ≈ 8,800, so also **right-skewed** (skewness ≈ 44). The exact mode is **0**
  (539 records): every one of them is a ratings-disabled video, a genuine zero rather than a typical value.

**IQR outliers.**
* **Views:** Q1 = 129,622, Q3 = 823,817, IQR = 694,195. The upper fence is 1,865,110 (the lower fence is negative, so there are no low
  outliers). **5,068 records (11.1%)** are outliers.
* **Likes:** upper fence 66,982, giving **5,249 records (11.4%)** as outliers.

**Decision: keep them.** These are not errors (no impossible values, and duplicates and removed videos were already dropped). They are the
very hits this analysis is about: removing them would delete most of Music and every long-running video. The IQR rule flags so much
because it assumes a roughly symmetric distribution. On the log scale, where views are close to symmetric, only 617 records (views) and
1,039 (likes) fall outside the fences. For averages I therefore report medians next to means, and I use log scales in the charts,
instead of deleting data.

## Correlation (heatmap: `charts/07_correlation_heatmap.png`)

**The two strongest correlations** (largest absolute off-diagonal Pearson coefficients):
1. **views – likes: r = 0.92.** Videos with more views collect proportionally more likes, because likes come from viewers and grow with reach.
2. **views – comment_count: r = 0.92 (0.916).** Comments also scale with audience size. The audience count drives every engagement count,
   which is why the count columns all correlate 0.81–0.92 with each other.

By contrast, **like_ratio** is almost uncorrelated with views (r ≈ 0.05). How *well liked* a video is says nothing about how *big* it
is. **days_to_trend** is only weakly positive (≈ 0.2), because a video that has been out longer has had more time to collect views.

**Correlation is not causation:** likes and views move together because both are driven by the same thing, the size of the audience
reached (a third variable). Likes are a *result* of viewing, so this data cannot show that adding likes would cause more views.

## Funnel analysis

**Funnel result**

| Stage | Unique videos | Conversion from previous | Conversion from start |
|---|---|---|---|
| 1. Ever trended | 14,684 | — | 100% |
| 2. Peak views > median (265,290) | 7,342 | 50.0% | 50.0% |
| 3. Peak views > 90th percentile (1,646,274) | 1,469 | 20.0% | 10.0% |
| 4. ... and 1,000+ comments | 1,440 | 98.0% | 9.8% |

**Largest drop-off: stage 2 → 3.** Only 20% of above-median videos make it into the top 10%, so 5,873 videos are lost. Stage 1 → 2 is
50% by construction, since the median splits the group in half. This means that reaching the trending list is common, but breaking out
to the top 10% is the real filter: views are so skewed that the 90th percentile (1.65M) is more than six times the median. Once a video
*is* that big, 1,000+ comments is almost automatic (98%), so for the biggest videos comment volume follows reach rather than being a
separate hurdle.

## Retention (curve: `charts/09_retention_curves.png`)

Day 1 = the video's first trending day in a country. To avoid censoring, only videos whose first day falls after the first day of the
data and at least 6 days before its last day are included.

**Retention result** (13,294 videos; % still on the list):

| Group | Day 2 | Day 3 | Day 5 | Day 7 |
|---|---|---|---|---|
| **All videos** | **63.8%** | **42.7%** | **20.2%** | **10.4%** |
| Music | 81.2% | 66.0% | 44.7% | 30.6% |
| Entertainment | 71.0% | 52.5% | 28.1% | 14.4% |
| News & Politics | 41.1% | 16.2% | 3.8% | 1.0% |
| US | 65.8% | 44.7% | 21.1% | 11.5% |
| GB | 69.7% | 50.1% | 27.1% | 15.1% |
| IN | 57.8% | 35.8% | 14.6% | 6.1% |

**Interpretation.** About a third of videos (36%) disappear after a single day, and only one in ten is still trending a week later.
**Music stays:** almost a third of Music videos are still on the list on day 7, three times the overall rate. **News & Politics
vanishes:** 59% are gone after day 1 and only 1% reach day 7, the pattern of a one-day news spike. Among countries, GB keeps videos
longest (15.1% on day 7) and India shortest (6.1%), consistent with India's faster daily turnover (Chart 4).

*Why a line chart for retention:* day number is ordered and the measure is a share that can only fall, so a curve per group shows both the
level and the speed of decay, and where the groups diverge.

## Cohort view (chart: `charts/10_cohort_lifespan.png`)

| Cohort week | Videos | Avg lifespan (days) | Median peak views |
|---|---|---|---|
| 2017-11-13 | 1,607 | 3.20 | 266,286 |
| 2017-11-20 | 1,326 | 3.19 | 269,651 |
| 2017-11-27 | 1,318 | 3.11 | 260,652 |
| 2017-12-04 | 1,323 | 3.23 | 275,461 |
| 2017-12-11 | 1,327 | 3.08 | 271,502 |
| 2017-12-18 | 1,374 | 3.15 | 269,019 |
| 2017-12-25 | 1,295 | 3.14 | 273,822 |
| 2018-01-01 | 1,349 | 3.12 | 245,696 |
| 2018-01-08 | 1,355 | 3.14 | 281,822 |
| 2018-01-15 | 1,320 | 3.01 | 266,345 |
| 2018-01-22 | 1,196 | 2.32 | 233,734 |
| 2018-01-29 | 253 | 1.69 | 173,837 |

**Cohort conclusion.** The first ten weekly cohorts are remarkably similar: an average lifespan of 3.0–3.2 days and a median
peak of ≈ 246K–282K views. Two cohorts look different, and **both differences are explained by the amount of data, not by behaviour**:
* **Week of 2018-01-22 (2.32 days)** and **week of 2018-01-29 (1.69 days, only 253 videos and 4 observed days):** these videos first
  trended near the end of the window, so the data stops before many of them leave the list. Their lifespans (and their peak views,
  174K) are cut off (**right-censored**), not genuinely shorter.
* **Week of 2017-11-13 (1,607 videos, the most):** day 1 of the data counts every video already on the list as a "new" entrant, so this
  cohort is inflated by videos that actually started trending earlier (**left-censored**).

So there is no real trend across cohorts. A fair cohort comparison should drop the first and last two weeks, or, as in section 7,
only use videos that can be observed for the full period being measured.

## Content strategy briefing

Trending is dominated by two formats: **Entertainment (26.7%) and Music (22.4%) fill almost half of all trending slots** across the US, GB
and India. Music is also the strongest performer, with a median peak of ≈ 990K views, nearly three times any other category. Videos get there
fast: **the median video trends 1 day after publishing, 41% trend the same day and 63% within a day**, so a video's first 24–48 hours
decide whether it trends. What separates videos that stay from those that vanish is format and audience approval. **About 36% of videos
drop off after one day and only 10% last a week, but 31% of Music videos are still trending on day 7, against 1% of News & Politics videos**,
which also have the lowest like ratio (≈ 72% vs 91–97% elsewhere). Countries differ clearly: **GB is the most Music-heavy market (33% of
its records) and keeps videos longest (15% still trending on day 7)**, while **India leans to Entertainment (34%) and News, and churns
fastest** (≈ 77 new entrants a day, 6% still trending on day 7). The practical takeaway is to invest in repeat-value formats (music and
entertainment) for lasting trending presence, and to treat news content as a one-day reach play. **Limitation:** this data contains only
videos that *did* trend, over a fixed ~11-week window (Nov 2017 – Jan 2018), so it cannot show what makes a video fail to trend, and
lifespans at the edges of the window are censored. (The copy of the files used here is also documented by its provider as a synthetic
reproduction of the Kaggle dataset, so the figures should be re-checked on the real files before acting on them.)

## Design decisions

* **Videos vs records:** distributions of individual records (Charts 1–2 and the outlier/correlation work) use daily records. Questions
  about *videos* (box plot, funnel, retention, cohorts) use one row per video at its peak, so a video that trends for 20 days is not
  counted 20 times.
* **Log scales everywhere views appear,** because views span five orders of magnitude.
* **One palette:** each country keeps the same colour throughout. Categorical charts show at most a few named categories plus a grey
  "Other", so the colours stay distinguishable (they were checked for colour-blind separation).
* **Censoring** is handled explicitly in the retention analysis and discussed in the cohort view.

## Data source

*Trending YouTube Video Statistics* (Mitchell J, Kaggle: <https://www.kaggle.com/datasets/datasnaek/youtube-new>), in the copy distributed
on the program LMS. The README that accompanies that copy says it is a **synthetic reproduction** with the same schema and quirks as the
Kaggle files. The findings above therefore describe that copy and should be re-checked on the real files before anyone acts on them.
