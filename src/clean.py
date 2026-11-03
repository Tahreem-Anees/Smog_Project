import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

# Same database file that load.py created
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "smog.db"

# Columns that hold measurements
NUMERIC_COLS = ["pm2_5", "temperature", "humidity", "wind_speed", "pressure"]


def get_season(month):
    """Map a month number to a season name."""
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8, 9):
        return "Summer"
    return "Autumn"  # October and November


def clean_data(df):
    """Clean the raw table. Returns the clean table and a small log of what was done."""
    log = {"rows_before": len(df)}

    # 1. Convert time text to real datetime values
    df["time"] = pd.to_datetime(df["time"])

    # 2. Remove duplicate rows (same city and same hour)
    before = len(df)
    df = df.drop_duplicates(subset=["city", "time"])
    log["duplicates_removed"] = before - len(df)

    # 3. Sort so that each city's rows are in time order
    df = df.sort_values(["city", "time"]).reset_index(drop=True)

    # 4. Check for missing hours (gaps in the time series)
    span = df.groupby("city")["time"].agg(["min", "max", "count"])
    span["expected"] = ((span["max"] - span["min"]).dt.total_seconds() / 3600 + 1).astype(int)
    log["missing_hours"] = int((span["expected"] - span["count"]).sum())

    # 5. Fill small gaps (up to 3 hours) inside each city; long gaps stay empty
    log["missing_values_before"] = int(df[NUMERIC_COLS].isna().sum().sum())
    df[NUMERIC_COLS] = df.groupby("city")[NUMERIC_COLS].transform(
        lambda col: col.interpolate(limit=3)
    )

    # 6. Drop rows that still have a missing value
    before = len(df)
    df = df.dropna(subset=NUMERIC_COLS)
    log["rows_dropped_missing"] = before - len(df)

    # 7. Add new columns used later for the EDA charts
    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    df["hour"] = df["time"].dt.hour
    df["season"] = df["month"].apply(get_season)

    log["rows_after"] = len(df)
    return df, log


def save_clean(df, log):
    """Write the clean table and the cleaning log into the database."""
    df = df.copy()
    df["time"] = df["time"].dt.strftime("%Y-%m-%d %H:%M:%S")  # store time as text

    log["run_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("clean_data", conn, if_exists="replace", index=False)
    pd.DataFrame([log]).to_sql("cleaning_log", conn, if_exists="replace", index=False)
    conn.close()


if __name__ == "__main__":
    # Read the raw table from the database (no API call needed)
    conn = sqlite3.connect(DB_PATH)
    raw = pd.read_sql("SELECT * FROM raw_data", conn)
    conn.close()

    clean, log = clean_data(raw)
    save_clean(clean, log)

    print("Cleaning log:")
    for key, value in log.items():
        print(f"  {key}: {value}")

    print("\nFirst 5 clean rows:")
    print(clean.head())

    print("\nMissing values per column:")
    print(clean.isna().sum())