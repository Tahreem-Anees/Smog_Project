# Data Dictionary: `clean_data`

Author: Fatima Khurram

Table `clean_data` in `data/smog.db`, built by `src/clean.py`.
One row = one city at one hour.

- Rows: 148,396 (37,099 per city)
- Period: 2022-08-04 05:00 to 2026-10-27 23:00, hourly
- Time zone: Asia/Karachi (PKT)
- Missing values: none

## Columns

| Column | Type | Meaning | Unit | Range in data | Source |
|---|---|---|---|---|---|
| `city` | text | City name | - | Lahore, Islamabad, Karachi, Peshawar | Set in `extract.py` |
| `time` | text (`YYYY-MM-DD HH:MM:SS`) | Start of the hour, local time | - | 2022-08-04 05:00:00 to 2026-10-27 23:00:00 | Both APIs |
| `pm2_5` | float | Fine particulate matter (particles smaller than 2.5 micrometres) near the ground | µg/m³ | 0.4 to 448.9 (mean 43.9) | Open-Meteo Air Quality API, `pm2_5` |
| `temperature` | float | Air temperature at 2 m above ground | °C | -1.4 to 46.5 (mean 23.7) | Open-Meteo Historical Weather API, `temperature_2m` |
| `humidity` | float | Relative humidity at 2 m above ground | % | 4 to 100 (mean 62.9) | Historical Weather API, `relative_humidity_2m` |
| `wind_speed` | float | Wind speed at 10 m above ground | km/h | 0 to 46.6 (mean 8.2) | Historical Weather API, `wind_speed_10m` |
| `pressure` | float | Air pressure at the ground surface (not sea level, so it is lower in higher cities like Islamabad and Peshawar) | hPa | 934.4 to 1024.4 (mean 977.8) | Historical Weather API, `surface_pressure` |
| `year` | integer | Year taken from `time` | - | 2022 to 2026 | Added in `clean.py` |
| `month` | integer | Month taken from `time` | 1 = January ... 12 = December | 1 to 12 | Added in `clean.py` |
| `hour` | integer | Hour of the day taken from `time` | 0 = midnight ... 23 = 11 pm | 0 to 23 | Added in `clean.py` |
| `season` | text | Season from `month` (see below) | - | Winter, Spring, Summer, Autumn | Added in `clean.py` |

## Season mapping

| Season | Months | Rows |
|---|---|---|
| Summer | 6, 7, 8, 9 | 52,396 |
| Spring | 3, 4, 5 | 35,328 |
| Winter | 12, 1, 2 | 34,656 |
| Autumn | 10, 11 | 26,016 |

## Validation limits

Every row passed these limits in `src/validate.py` before it was saved:

| Column | Allowed range |
|---|---|
| `pm2_5` | 0 to 1000 µg/m³ |
| `temperature` | -30 to 60 °C |
| `humidity` | 0 to 100 % |
| `wind_speed` | 0 to 200 km/h |
| `pressure` | 800 to 1100 hPa |

## Reference values

- WHO 24-hour guideline for PM2.5: 15 µg/m³
- US EPA "Unhealthy" level: above 55.4 µg/m³

## Notes

- PM2.5 and weather values are modelled estimates from Open-Meteo, not ground-sensor readings.
- Some values may be interpolated: gaps of up to 3 hours were filled linearly in `clean.py`.
  In the last run no gaps needed filling; only the first 5 hours of each city were missing
  and those rows were dropped.
