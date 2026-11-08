-- =====================================================================
-- TrendPulse - Part 4: schema + data load (MySQL 8.0)
-- Recreates the database from scratch. Run from INSIDE part4_sql_spreadsheet/
--   mysql --local-infile=1 -u root -p < trendpulse.sql
-- (MySQL Workbench: see README - either use the Table Data Import Wizard
--  or edit the three file paths below to absolute paths.)
-- =====================================================================

DROP DATABASE IF EXISTS trendpulse;
CREATE DATABASE trendpulse CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE trendpulse;

-- ---------------------------------------------------------------------
-- 1. categories : lookup table (parent of videos)
-- ---------------------------------------------------------------------
CREATE TABLE categories (
    category_id    SMALLINT UNSIGNED NOT NULL,
    category_name  VARCHAR(50)       NOT NULL,
    PRIMARY KEY (category_id),
    UNIQUE KEY uq_category_name (category_name)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 2. videos : one row per unique video (parent of trending_records)
--    video_id is case-sensitive on YouTube, so it uses a binary collation:
--    'abc' and 'ABC' must be two different keys.
-- ---------------------------------------------------------------------
CREATE TABLE videos (
    video_id           VARCHAR(11)  CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    title              VARCHAR(255) NOT NULL,
    channel_title      VARCHAR(100) NOT NULL,
    category_id        SMALLINT UNSIGNED NOT NULL,
    publish_time       DATETIME     NOT NULL,
    comments_disabled  BOOLEAN      NOT NULL DEFAULT FALSE,
    ratings_disabled   BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (video_id),
    KEY idx_videos_category (category_id),
    KEY idx_videos_channel (channel_title),
    CONSTRAINT fk_videos_category FOREIGN KEY (category_id)
        REFERENCES categories (category_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 3. trending_records : one row per video per day per country (child)
-- ---------------------------------------------------------------------
CREATE TABLE trending_records (
    record_id      INT UNSIGNED     NOT NULL,
    video_id       VARCHAR(11)      CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    country        CHAR(2)          NOT NULL,
    trending_date  DATE             NOT NULL,
    views          BIGINT UNSIGNED  NOT NULL,
    likes          BIGINT UNSIGNED  NOT NULL,
    dislikes       BIGINT UNSIGNED  NOT NULL,
    comment_count  BIGINT UNSIGNED  NOT NULL,
    PRIMARY KEY (record_id),
    UNIQUE KEY uq_video_day_country (video_id, trending_date, country),   -- the "no duplicates" rule
    KEY idx_records_country_date (country, trending_date),
    CONSTRAINT fk_records_video FOREIGN KEY (video_id)
        REFERENCES videos (video_id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- Load the cleaned CSVs (parents first, so every foreign key finds its parent)
-- Requires local_infile enabled on the server (SET GLOBAL local_infile = 1;)
-- ---------------------------------------------------------------------
LOAD DATA LOCAL INFILE 'data/categories.csv'
INTO TABLE categories
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(category_id, category_name);

LOAD DATA LOCAL INFILE 'data/videos.csv'
INTO TABLE videos
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(video_id, title, channel_title, category_id, publish_time, comments_disabled, ratings_disabled);

LOAD DATA LOCAL INFILE 'data/trending_records.csv'
INTO TABLE trending_records
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(record_id, video_id, country, trending_date, views, likes, dislikes, comment_count);

-- ---------------------------------------------------------------------
-- Row counts after loading
-- ---------------------------------------------------------------------
SELECT 'categories' AS table_name, COUNT(*) AS row_count FROM categories
UNION ALL
SELECT 'videos', COUNT(*) FROM videos
UNION ALL
SELECT 'trending_records', COUNT(*) FROM trending_records;
