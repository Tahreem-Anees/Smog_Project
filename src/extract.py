# Module: Open-Meteo Weather & Air Quality API Ingestion (4-Year Data Extraction )
# Developed & Maintained by: Noor Fatima (Roll No. 189)

import time
from datetime import date, timedelta

import pandas as pd
import requests

# City name -> (latitude, longitude)
CITIES = {
    "Lahore": (31.5497, 74.3436),
    "Islamabad": (33.6844, 73.0479),
    "Karachi": (24.8607, 67.0011),
    "Peshawar": (34.0151, 71.5249),
}

# PM2.5 data starts on 2022-08-04; weather archive lags a few days
START_DATE = "2022-08-04"
END_DATE = str(date.today() - timedelta(days=7))

AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_hourly(url, lat, lon, variables):
    """Call one API for the full date range and return the hourly data."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": ",".join(variables),
        "timezone": "Asia/Karachi",
    }
    response = requests.get(url, params=params, timeout=120)
    response.raise_for_status()  # stop with an error if the API failed
    return response.json()["hourly"]


def extract_city(city, lat, lon):
    """Get air + weather for one city and join them by timestamp."""
    air = fetch_hourly(AIR_URL, lat, lon, ["pm2_5"])
    time.sleep(1)  # small pause between API calls
    weather = fetch_hourly(
        WEATHER_URL, lat, lon,
        ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "surface_pressure"],
    )

    # Lookup: timestamp -> position in the weather lists
    weather_index = {t: i for i, t in enumerate(weather["time"])}

    rows = []
    for i, t in enumerate(air["time"]):
        j = weather_index.get(t)
        if j is None:
            continue  # no weather for this hour, skip it
        rows.append({
            "city": city,
            "time": t,
            "pm2_5": air["pm2_5"][i],
            "temperature": weather["temperature_2m"][j],
            "humidity": weather["relative_humidity_2m"][j],
            "wind_speed": weather["wind_speed_10m"][j],
            "pressure": weather["surface_pressure"][j],
        })
    return rows


def extract_all():
    """Run extract_city for all four cities and return one list of rows."""
    all_rows = []
    for city, (lat, lon) in CITIES.items():
        print(f"Fetching {city}...")
        rows = extract_city(city, lat, lon)
        print(f"  {len(rows)} rows")
        all_rows.extend(rows)
        time.sleep(1)
    return all_rows


if __name__ == "__main__":
    df = pd.DataFrame(extract_all())  # turn the rows into a table
    print("Total rows:", len(df))
    print(df.head())
        # How many rows does each city have?
    print(df["city"].value_counts())

    # Show 8 random rows from the whole table
    print(df.sample(8, random_state=1))
    print("Missing values per column:")
    print(df.isna().sum())
