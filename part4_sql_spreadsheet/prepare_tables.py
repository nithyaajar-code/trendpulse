"""Prepare the three cleaned CSV tables for Part 4 from the raw country files in raw_data/.

Run from inside part4_sql_spreadsheet/:   python prepare_tables.py
Writes data/categories.csv, data/videos.csv, data/trending_records.csv
"""
import os
import pandas as pd

RAW, OUT = "raw_data", "data"
COUNTRIES = ["US", "GB", "IN"]
os.makedirs(OUT, exist_ok=True)

# 1. load and stack the country files
frames = []
for c in COUNTRIES:
    d = pd.read_csv(f"{RAW}/{c}videos.csv")
    d["country"] = c
    frames.append(d)
raw = pd.concat(frames, ignore_index=True)
print("raw rows:", len(raw))

# 2. clean
df = raw.copy()
df["trending_date"] = pd.to_datetime(df["trending_date"], format="%y.%d.%m")            # yy.dd.mm text -> date
df["publish_time"] = pd.to_datetime(df["publish_time"], utc=True).dt.tz_convert(None)    # ISO UTC -> naive UTC
df = df.drop_duplicates(subset=["country", "video_id", "trending_date"])                 # duplicate = same video/day/country
df = df[~df["video_error_or_removed"]]                                                   # removed/errored videos
df = df.dropna(subset=["likes", "comment_count"])                                        # 48 rows with blank counts
df[["likes", "comment_count"]] = df[["likes", "comment_count"]].astype("int64")
df = df.sort_values(["country", "trending_date", "views"], ascending=[True, True, False]).reset_index(drop=True)
print("clean trending records:", len(df))

# 3. categories table: straight from the lookup
categories = pd.read_csv(f"{RAW}/categories.csv")
categories["category_name"] = categories["category_name"].str.strip()
assert categories["category_id"].is_unique

# 4. videos table: one row per unique video_id (descriptive attributes only)
videos = (df.sort_values("trending_date")
            .drop_duplicates(subset="video_id", keep="first")
            [["video_id", "title", "channel_title", "category_id", "publish_time",
              "comments_disabled", "ratings_disabled"]]
            .sort_values("video_id").reset_index(drop=True))
videos["publish_time"] = videos["publish_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
videos["comments_disabled"] = videos["comments_disabled"].astype(int)
videos["ratings_disabled"] = videos["ratings_disabled"].astype(int)
assert videos["category_id"].isin(categories["category_id"]).all()   # every FK has a parent

# 5. trending_records table: one row per video per day per country, with a surrogate key
records = df[["video_id", "country", "trending_date", "views", "likes", "dislikes", "comment_count"]].copy()
records.insert(0, "record_id", range(1, len(records) + 1))
records["trending_date"] = records["trending_date"].dt.strftime("%Y-%m-%d")
assert records["video_id"].isin(videos["video_id"]).all()

categories.to_csv(f"{OUT}/categories.csv", index=False)
videos.to_csv(f"{OUT}/videos.csv", index=False)
records.to_csv(f"{OUT}/trending_records.csv", index=False)
print(f"categories: {len(categories)} | videos: {len(videos)} | trending_records: {len(records)}")
