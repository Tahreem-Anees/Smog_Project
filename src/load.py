import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from extract import extract_all
from validate import validate_rows

# Database file lives in the data/ folder, next to src/
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "smog.db"


def save_raw(valid_rows, invalid_rows):
    """Save validated rows in 'raw_data' and a small summary in 'validation_log'."""
    df = pd.DataFrame(valid_rows)
    df["time"] = df["time"].astype(str)  # store timestamps as text

    conn = sqlite3.connect(DB_PATH)  # creates smog.db if it does not exist

    # if_exists="replace" -> re-running the script does not duplicate rows
    df.to_sql("raw_data", conn, if_exists="replace", index=False)

    # One-row summary of this run (used later in the data-quality dashboard)
    log = pd.DataFrame([{
        "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "valid_rows": len(valid_rows),
        "invalid_rows": len(invalid_rows),
    }])
    log.to_sql("validation_log", conn, if_exists="replace", index=False)

    conn.close()


def check_database():
    """Read the database back and print a few checks."""
    conn = sqlite3.connect(DB_PATH)

    print("Rows per city:")
    print(pd.read_sql("SELECT city, COUNT(*) AS rows FROM raw_data GROUP BY city", conn))

    print("\nFirst 5 rows:")
    print(pd.read_sql("SELECT * FROM raw_data LIMIT 5", conn))

    print("\nValidation log:")
    print(pd.read_sql("SELECT * FROM validation_log", conn))

    conn.close()


if __name__ == "__main__":
    rows = extract_all()                        # Step 2: extract
    valid, invalid = validate_rows(rows)        # Step 3: validate
    save_raw(valid, invalid)                    # Step 4: store raw
    check_database()                            # confirm it was saved