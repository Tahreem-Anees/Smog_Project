# Smog(PM2.5) Forecast: ETL and EDA Pipeline (Section 1)

Programming for AI, Project 1.
Team: 4 members
1.Tahreem Anees
2.Sehrish Imran
3.Fatima khurram
4.Noor Fatima

## Problem
Smog is a serious health issue in Pakistani cities, especially in winter, but ground-sensor
coverage is limited. This project builds the data pipeline and the exploratory analysis
for a next-day PM2.5 forecasting model (Sections 2 and 3).

## Data
- Cities: Lahore, Islamabad, Karachi, Peshawar
- Source: two free Open-Meteo APIs (Air Quality for PM2.5, Historical Weather for
  temperature, humidity, wind speed and pressure)
- Period: 2022-08-04 to 2026-10-24 (PM2.5 history starts on 2022-08-04)
- Size: 148,108 clean hourly rows

## Pipeline
1. **Extract** (`src/extract.py`): call both APIs for each city and join them by time.
2. **Validate** (`src/validate.py`): Pydantic checks every row against physical limits.
3. **Load raw** (`src/load.py`): store validated rows in SQLite (`raw_data` table).
4. **Clean** (`src/clean.py`): remove duplicates, fill short gaps, drop rows with
   missing values, add year, month, hour and season (`clean_data` table).
5. **EDA** (`src/eda.py`, `src/charts.py`, `notebooks/eda.ipynb`).

## Dashboard
Streamlit app with two dashboards: (1) Pipeline and Data Quality, (2) EDA.
Live link: https://smogproject-7cv9tpdwdtclu8uh4yl4de.streamlit.app/

## How to run
```
pip install -r requirements.txt
python src/load.py
python src/clean.py
streamlit run app.py
```
`data/smog.db` is included, so the dashboard also runs without the first two steps.

## Limitations
- PM2.5 and weather values are modelled estimates from Open-Meteo, not ground-sensor readings.
- Correlation between weather and PM2.5 does not show cause and effect.
