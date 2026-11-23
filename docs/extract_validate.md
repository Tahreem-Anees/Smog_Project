# Extract and Validate

## Overview
This step collects four years of hourly air quality and weather data
for four Pakistani cities from the Open-Meteo APIs, then checks every
row before it is used further.

- Extraction: `src/extract.py`
- Validation: `src/validate.py`
- Tests: `tests/test_validate.py`

## Extraction (`src/extract.py`)

### Cities
| City | Latitude | Longitude |
|---|---|---|
| Lahore | 31.5497 | 74.3436 |
| Islamabad | 33.6844 | 73.0479 |
| Karachi | 24.8607 | 67.0011 |
| Peshawar | 34.0151 | 71.5249 |

### Date range
- Start: 2022-08-04, because PM2.5 data starts on this date.
- End: today minus 7 days, because the weather archive is a few days late.

### Data sources
| Data | API | Variables |
|---|---|---|
| Air quality | Open-Meteo Air Quality API | pm2_5 |
| Weather | Open-Meteo Archive API | temperature_2m, relative_humidity_2m, wind_speed_10m, surface_pressure |

All requests use the timezone Asia/Karachi.

### Steps
1. `fetch_hourly` calls one API for the full date range and returns the
   hourly data. If the API fails, `raise_for_status()` stops with an error.
2. `extract_city` gets air and weather data for one city and joins them
   by timestamp. If an hour has no weather data, that hour is skipped.
3. `extract_all` runs `extract_city` for all four cities and returns one
   list of rows. There is a 1 second pause between API calls.

### Output row
Each row is a dictionary with these fields: city, time, pm2_5,
temperature, humidity, wind_speed, pressure.

## Validation (`src/validate.py`)
Each row is checked against the `AirWeatherRecord` model (built with
Pydantic). The function `validate_rows(rows)` returns two lists:

- **valid rows**: rows that follow every rule
- **invalid rows**: the original row plus the reason it failed

A bad row is kept in the invalid list with its error message. load.py saves only the number of invalid rows (in validation_log); in the last run there were 0.
### Rules for each field
| Field | Required? | Unit | Allowed range |
|---|---|---|---|
| city | Yes | text | any text |
| time | Yes | datetime | valid date and time |
| pm2_5 | No | ug/m3 | 0 to 1000 |
| temperature | No | deg C | -30 to 60 |
| humidity | No | % | 0 to 100 |
| wind_speed | No | km/h | 0 to 200 |
| pressure | No | hPa | 800 to 1100 |

"Not required" means the value can be missing (None). If it is present,
it must stay inside the allowed range.

## Tests
Tests are in `tests/test_validate.py`. They check that:

1. A normal row passes.
2. Missing optional values are allowed.
3. A negative PM2.5 value is rejected.
4. Humidity above 100 is rejected.
5. A row without a city is rejected.
6. A mix of good and bad rows is split correctly.

Run them with:

    .venv\Scripts\python -m pytest