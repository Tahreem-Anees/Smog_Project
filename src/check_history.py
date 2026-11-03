import requests

# Air Quality API address
URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Request settings: Lahore, year 2022, hourly PM2.5
params = {
    "latitude": 31.5497,      # Lahore
    "longitude": 74.3436,
    "start_date": "2022-01-01",
    "end_date": "2022-12-31",
    "hourly": "pm2_5",
    "timezone": "Asia/Karachi",
}

# Send the request and print the HTTP status (200 = OK)
r = requests.get(URL, params=params, timeout=60)
print("Status:", r.status_code)
data = r.json()

if r.status_code != 200:
    # The API explains the error here, e.g. the earliest allowed date
    print("API response:", data)
else:
    # Find the first hour that has a real PM2.5 value (not None)
    for t, v in zip(data["hourly"]["time"], data["hourly"]["pm2_5"]):
        if v is not None:
            print("First real PM2.5 data:", t)
            break
    else:
        print("No data found in this year")