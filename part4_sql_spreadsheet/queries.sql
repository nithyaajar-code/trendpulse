-- =====================================================================
-- TrendPulse - Part 4: analysis queries (run after trendpulse.sql)
--   mysql -u root -p -t trendpulse < queries.sql
-- =====================================================================
USE trendpulse;

-- Q1. DISTINCT + alias: which countries are in the data?
SELECT DISTINCT country AS country_code
FROM trending_records
ORDER BY country_code;

-- Q2. WHERE + ORDER BY + LIMIT + aliases: the 10 most-viewed trending records in the US
SELECT tr.record_id,
       tr.video_id,
       tr.trending_date AS day,
       tr.views         AS total_views,
       tr.likes         AS total_likes
FROM trending_records AS tr
WHERE tr.country = 'US'
ORDER BY tr.views DESC
LIMIT 10;

-- Q3. DISTINCT: which category ids actually appear among the videos?
SELECT DISTINCT category_id AS used_category_id
FROM videos
ORDER BY used_category_id;

-- Q4. GROUP BY + aggregates: records and average views per country (cross-check value #1)
SELECT country,
       COUNT(*)                 AS records,
       COUNT(DISTINCT video_id) AS unique_videos,
       ROUND(AVG(views), 2)     AS avg_views,
       SUM(views)               AS total_views
FROM trending_records
GROUP BY country
ORDER BY records DESC;

-- Q5. INNER JOIN (3 tables) + GROUP BY + HAVING:
--     categories whose average views per trending record exceed 500,000 (cross-check value #2 = Music)
SELECT c.category_name,
       COUNT(*)               AS records,
       ROUND(AVG(tr.views), 2) AS avg_views
FROM trending_records AS tr
INNER JOIN videos     AS v ON v.video_id = tr.video_id
INNER JOIN categories AS c ON c.category_id = v.category_id
GROUP BY c.category_name
HAVING AVG(tr.views) > 500000
ORDER BY avg_views DESC;

-- Q6. GROUP BY + HAVING: channels with at least 5 distinct trending videos (top 10 by video count)
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

-- Q6b. how many channels pass that HAVING filter, out of all channels?
SELECT SUM(n_videos >= 5) AS channels_with_5plus_videos,
       COUNT(*)            AS all_channels
FROM (SELECT channel_title, COUNT(*) AS n_videos FROM videos GROUP BY channel_title) AS per_channel;

-- Q7. INNER JOIN (3 tables): trending records with video title and category name - top 10 in GB
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

-- Q8. LEFT JOIN: categories that have no video in the data
SELECT c.category_id,
       c.category_name,
       COUNT(v.video_id) AS videos
FROM categories AS c
LEFT JOIN videos AS v ON v.category_id = c.category_id
GROUP BY c.category_id, c.category_name
HAVING COUNT(v.video_id) = 0
ORDER BY c.category_id;

-- Q9. RIGHT JOIN: every video, with its number of US trending days (0 if it never trended in the US).
--     Summarised: how many videos trended in the US, and how many only elsewhere?
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

-- Q10. Cross-check helpers: one country count and one category average, as single values
SELECT COUNT(*) AS us_records FROM trending_records WHERE country = 'US';

SELECT ROUND(AVG(tr.views), 2) AS music_avg_views
FROM trending_records AS tr
INNER JOIN videos AS v ON v.video_id = tr.video_id
WHERE v.category_id = 10;

SELECT ROUND(AVG(views), 2) AS overall_avg_views, COUNT(*) AS all_records FROM trending_records;
