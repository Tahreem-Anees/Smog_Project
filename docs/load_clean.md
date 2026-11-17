# Load and Clean

Author: Fatima Khurram
Code: `src/load.py`, `src/clean.py`

This document explains how validated data is stored in a database (load) and how it is
turned into the clean table used by the EDA and the dashboards (clean).

## Where these steps sit in the pipeline

```
Extract -> Validate -> LOAD (raw_data) -> CLEAN (clean_data) -> EDA -> Dashboards
```

## Why SQLite

- **No server needed.** SQLite is a single file (`data/smog.db`). Nothing has to be installed or
  started, and Python already includes the `sqlite3` module.
- **Easy to share.** The database file is in the repository, so anyone can run the dashboards
  without calling the APIs again.
- **Real SQL.** We can check the data with queries such as
  `SELECT city, COUNT(*) FROM raw_data GROUP BY city`.
- **Big enough for our data.** About 148,000 rows is small for SQLite.
- **Raw and clean data kept apart.** Both tables live in the same file, so we can always go back
  to the raw data and re-run cleaning without calling the APIs.

## Tables in `data/smog.db`

| Table | Written by | What it holds | Rows (last run) |
|---|---|---|---|
| `raw_data` | `load.py` | Every row that passed Pydantic validation, unchanged | 148,416 |
| `validation_log` | `load.py` | One row per run: run time, valid rows, invalid rows | 1 |
| `clean_data` | `clean.py` | The cleaned table with extra columns for EDA | 148,396 |
| `cleaning_log` | `clean.py` | One row per run: what each cleaning step changed | 1 |

Both scripts use `if_exists="replace"`, so running them again rebuilds the tables instead of
adding duplicate rows.

## Load step (`src/load.py`)

1. `extract_all()` calls the two Open-Meteo APIs for the four cities.
2. `validate_rows()` checks each row with the Pydantic model and splits rows into valid and invalid.
3. `save_raw()` turns the valid rows into a pandas DataFrame, stores the timestamp as text,
   and writes it to `raw_data`. It also writes a one-row summary to `validation_log`.
4. `check_database()` reads the tables back and prints rows per city, the first 5 rows and the
   log, to confirm the save worked.

Last run: 148,416 valid rows, 0 invalid rows.

## Clean step (`src/clean.py`)

`clean.py` reads `raw_data` from the database (no API call) and applies these steps in order:

| # | Step | Why | Result (last run) |
|---|---|---|---|
| 1 | Convert `time` from text to datetime | Needed for sorting, gap checks and month/hour columns | - |
| 2 | Remove duplicates on (`city`, `time`) | Each city should have one row per hour | 0 removed |
| 3 | Sort by city, then time | Interpolation only makes sense in time order | - |
| 4 | Count missing hours per city | Expected hours = (last - first) + 1; compared with rows present | 0 missing hours |
| 5 | Fill short gaps (up to 3 hours) by linear interpolation, inside each city | PM2.5 and weather change smoothly, so a short gap can be estimated from its neighbours. Longer gaps are left empty so we do not invent data | 20 missing values before |
| 6 | Drop rows that still have a missing value | The EDA and a future model need complete rows | 20 rows dropped |
| 7 | Add `year`, `month`, `hour`, `season` | Used by the EDA charts (seasonal and hourly patterns) | - |

Interpolation is done separately for each city (`groupby("city")`), so a value in Lahore is never
filled using a value from Karachi.

### Seasons

| Season | Months |
|---|---|
| Winter | December, January, February |
| Spring | March, April, May |
| Summer | June, July, August, September |
| Autumn | October, November |

## Why 20 rows were dropped

The PM2.5 history from the Air Quality API starts at **05:00 on 2022-08-04**. The weather API has
data from 00:00 that day, so for each city the first 5 hours (00:00 to 04:00) have weather
values but **no PM2.5**.

- 4 cities x 5 hours = **20 rows**
- These gaps are at the very start of each series, so there is no earlier value to interpolate
  from. They stay empty after step 5 and are removed in step 6.
- No other rows were dropped.

Result: 148,416 raw rows -> 148,396 clean rows (37,099 per city), covering
2022-08-04 05:00 to 2026-10-27 23:00.

## How to run

```
python src/load.py     # calls the APIs, validates, writes raw_data and validation_log
python src/clean.py    # reads raw_data, writes clean_data and cleaning_log
```

`clean.py` prints the cleaning log, the first 5 clean rows and the missing values per column
(all should be 0).
