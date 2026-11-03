import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cycler import cycler

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "smog.db"

NUMERIC_COLS = ["pm2_5", "temperature", "humidity", "wind_speed", "pressure"]
WEATHER_COLS = ["temperature", "humidity", "wind_speed", "pressure"]

# Same physical limits we used in validate.py
LIMITS = {
    "pm2_5": (0, 1000),
    "temperature": (-30, 60),
    "humidity": (0, 100),
    "wind_speed": (0, 200),
    "pressure": (800, 1100),
}

# One fixed colour per city, used in every chart
CITY_COLORS = {
    "Islamabad": "#3b82f6",
    "Karachi": "#10b981",
    "Lahore": "#f43f5e",
    "Peshawar": "#8b5cf6",
}
# WHO 2021 guideline for the 24-hour mean of PM2.5 (ug/m3)
WHO_GUIDELINE = 15

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def apply_style():
    """Clean chart style used by the whole dashboard."""
    plt.rcParams.update({
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "figure.dpi": 110,
    })
    # Cities appear in alphabetical order in our tables, so this keeps colours fixed
    plt.rcParams["axes.prop_cycle"] = cycler(color=[CITY_COLORS[c] for c in sorted(CITY_COLORS)])


apply_style()


def set_city_colors(cities):
    """Keep colours fixed when only some cities are selected."""
    colors = [CITY_COLORS.get(c, "#64748b") for c in sorted(cities)]
    plt.rcParams["axes.prop_cycle"] = cycler(color=colors)


def load_clean():
    """Read the clean table from the database."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM clean_data", conn)
    conn.close()
    df["time"] = pd.to_datetime(df["time"])
    return df


# ---------- Part 1: Data overview ----------
def overview(df):
    """One summary row per city."""
    summary = df.groupby("city").agg(
        rows=("pm2_5", "size"),
        start=("time", "min"),
        end=("time", "max"),
        avg_pm25=("pm2_5", "mean"),
        max_pm25=("pm2_5", "max"),
    )
    # Round only the number columns (rounding date columns triggers a warning)
    return summary.round({"avg_pm25": 1, "max_pm25": 1})


# ---------- Part 2: Data quality checks ----------
def quality_checks(df):
    """Duplicates, missing values, impossible values and time gaps in one table."""
    rows = [
        ("Duplicate rows (same city and hour)", int(df.duplicated(["city", "time"]).sum())),
        ("Missing values (all columns)", int(df.isna().sum().sum())),
    ]
    for col, (low, high) in LIMITS.items():
        bad = int(((df[col] < low) | (df[col] > high)).sum())
        rows.append((f"Impossible {col} values", bad))

    # Time gaps: expected hours between first and last row minus actual rows
    span = df.groupby("city")["time"].agg(["min", "max", "count"])
    expected = (span["max"] - span["min"]).dt.total_seconds() / 3600 + 1
    rows.append(("Missing hours (time gaps)", int((expected - span["count"]).sum())))

    return pd.DataFrame(rows, columns=["check", "result"])


def plot_rows_per_year(df):
    """Bar chart: how many rows each city has in each year."""
    counts = df.groupby(["year", "city"]).size().unstack()
    fig, ax = plt.subplots(figsize=(8, 5))
    counts.plot(kind="bar", ax=ax)
    ax.set_title("Rows per year for each city")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of hourly rows")
    fig.tight_layout()
    return fig


# ---------- Part 3: Distributions ----------
def plot_histograms(df):
    """Histogram of every measurement column."""
    fig, axes = plt.subplots(2, 3, figsize=(14, 7))
    flat = axes.flatten()
    for ax, col in zip(flat, NUMERIC_COLS):
        # Humidity is stored as whole numbers, so use one bin per number to avoid fake gaps
        bins = np.arange(-0.5, 101.5, 1) if col == "humidity" else 50
        ax.hist(df[col], bins=bins, color="steelblue")
        ax.set_title(col)
    flat[-1].axis("off")  # 6th box is unused
    fig.suptitle("Distribution of each variable")
    fig.tight_layout()
    return fig


def plot_pm25_by_city(df):
    """Box plot: PM2.5 spread for each city."""
    cities = sorted(df["city"].unique())
    data = [df.loc[df["city"] == c, "pm2_5"] for c in cities]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(data, tick_labels=cities, showfliers=False)  # hide extreme dots for clarity
    ax.set_title("PM2.5 by city")
    ax.set_ylabel("PM2.5 (ug/m3)")
    fig.tight_layout()
    return fig


# ---------- Part 4: Seasonal and hourly patterns ----------
def plot_hourly_by_city(df, season=None):
    """Line chart: average PM2.5 for each hour of the day, one line per city."""
    if season:
        df = df[df["season"] == season]  # optional filter, e.g. "Winter"
    hourly = df.groupby(["hour", "city"])["pm2_5"].mean().unstack()

    fig, ax = plt.subplots(figsize=(10, 5))
    hourly.plot(ax=ax, marker="o")
    ax.axhline(WHO_GUIDELINE, color="black", linestyle=":", linewidth=1.2,
               label="WHO 24-h guideline (15)")
    ax.set_xticks(range(0, 24, 2))
    ax.set_title("Average PM2.5 by hour of day" + (f" ({season})" if season else ""))
    ax.set_xlabel("Hour of day (local time)")
    ax.set_ylabel("PM2.5 (ug/m3)")
    ax.legend(title="City")
    fig.tight_layout()
    return fig


def plot_monthly_by_city(df):
    """Line chart: average PM2.5 for each month, one line per city."""
    monthly = df.groupby(["month", "city"])["pm2_5"].mean().unstack()

    fig, ax = plt.subplots(figsize=(10, 5))
    monthly.plot(ax=ax, marker="o")
    ax.axhline(WHO_GUIDELINE, color="black", linestyle=":", linewidth=1.2,
               label="WHO 24-h guideline (15)")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTH_NAMES)
    ax.set_title("Average PM2.5 by month")
    ax.set_xlabel("Month")
    ax.set_ylabel("PM2.5 (ug/m3)")
    ax.legend(title="City")
    fig.tight_layout()
    return fig


def plot_season_by_city(df):
    """Grouped bar chart: average PM2.5 in each season for each city."""
    order = ["Winter", "Spring", "Summer", "Autumn"]
    seasonal = df.groupby(["season", "city"])["pm2_5"].mean().unstack().reindex(order)

    fig, ax = plt.subplots(figsize=(10, 5))
    seasonal.plot(kind="bar", ax=ax)
    ax.set_xticklabels(order, rotation=0)
    ax.set_title("Average PM2.5 by season")
    ax.set_xlabel("Season")
    ax.set_ylabel("PM2.5 (ug/m3)")
    ax.legend(title="City")
    fig.tight_layout()
    return fig


# ---------- Part 5: Relationship between PM2.5 and weather ----------
def plot_correlation_heatmap(df, city=None):
    """Heatmap of correlations between all measurements (optionally for one city)."""
    if city:
        df = df[df["city"] == city]
    corr = df[NUMERIC_COLS].corr().round(2)

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.grid(False)
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(corr)))
    ax.set_yticklabels(corr.index)
    # Write the number inside every cell
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, corr.iloc[i, j], ha="center", va="center", fontsize=9)
    fig.colorbar(im, ax=ax)
    ax.set_title("Correlation" + (f" - {city}" if city else " - all cities"))
    fig.tight_layout()
    return fig


def plot_weather_correlation_by_city(df):
    """Bar chart: correlation of PM2.5 with each weather variable, one bar per city."""
    corr = df.groupby("city")[NUMERIC_COLS].corr()["pm2_5"].unstack()[WEATHER_COLS]

    fig, ax = plt.subplots(figsize=(10, 5))
    corr.T.plot(kind="bar", ax=ax)  # groups = weather variables, bars = cities
    ax.set_xticklabels(WEATHER_COLS, rotation=0)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Correlation of PM2.5 with weather, by city")
    ax.set_ylabel("Correlation (-1 to +1)")
    ax.legend(title="City")
    fig.tight_layout()
    return fig


def plot_weather_scatter(df, variable, n=5000):
    """Scatter plot of PM2.5 against one weather variable (random sample, colored by city)."""
    sample = df.sample(min(n, len(df)), random_state=1)  # 148k points would be too heavy to draw

    fig, ax = plt.subplots(figsize=(9, 5))
    for city, group in sample.groupby("city"):
        ax.scatter(group[variable], group["pm2_5"], s=6, alpha=0.4, label=city)
    ax.set_title(f"PM2.5 vs {variable}")
    ax.set_xlabel(variable)
    ax.set_ylabel("PM2.5 (ug/m3)")
    ax.legend(title="City", markerscale=3)
    fig.tight_layout()
    return fig


# ---------- Part 6: Autocorrelation and lag analysis ----------
def plot_autocorrelation(df, max_lag=72):
    """Hourly autocorrelation: how similar PM2.5 is to its own value N hours earlier."""
    lags = range(1, max_lag + 1)

    fig, ax = plt.subplots(figsize=(10, 5))
    for city, group in df.groupby("city"):
        series = group.sort_values("time")["pm2_5"]
        values = [series.autocorr(lag) for lag in lags]
        ax.plot(lags, values, label=city)
    ax.set_xticks(range(0, max_lag + 1, 6))
    ax.set_title("Hourly autocorrelation of PM2.5")
    ax.set_xlabel("Lag (hours)")
    ax.set_ylabel("Autocorrelation")
    ax.legend(title="City")
    fig.tight_layout()
    return fig


def plot_daily_autocorrelation(df, max_days=14):
    """Daily autocorrelation: how similar the daily average PM2.5 is N days earlier."""
    daily = df.set_index("time").groupby("city")["pm2_5"].resample("D").mean()
    lags = range(1, max_days + 1)

    fig, ax = plt.subplots(figsize=(10, 5))
    for city in sorted(df["city"].unique()):
        series = daily.loc[city]
        values = [series.autocorr(lag) for lag in lags]
        ax.plot(lags, values, marker="o", label=city)
    ax.set_title("Daily autocorrelation of PM2.5")
    ax.set_xlabel("Lag (days)")
    ax.set_ylabel("Autocorrelation")
    ax.legend(title="City")
    fig.tight_layout()
    return fig


def persistence_baseline(df):
    """Simple baseline: predict tomorrow's daily PM2.5 as equal to today's."""
    daily = df.set_index("time").groupby("city")["pm2_5"].resample("D").mean().reset_index()
    daily["tomorrow"] = daily.groupby("city")["pm2_5"].shift(-1)
    daily = daily.dropna()

    rows = []
    for city, group in daily.groupby("city"):
        rows.append({
            "city": city,
            "correlation_today_vs_tomorrow": round(group["pm2_5"].corr(group["tomorrow"]), 2),
            "mean_abs_error": round((group["pm2_5"] - group["tomorrow"]).abs().mean(), 1),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    plt.switch_backend("Agg")  # save charts as files instead of opening windows
    df = load_clean()

    print("PART 1: OVERVIEW")
    print(overview(df))
    print("\nPART 2: QUALITY CHECKS")
    print(quality_checks(df).to_string(index=False))

    out = BASE_DIR / "figures"
    out.mkdir(exist_ok=True)
    charts = {
        "rows_per_year": plot_rows_per_year(df),
        "histograms": plot_histograms(df),
        "pm25_by_city": plot_pm25_by_city(df),
    }
    for name, fig in charts.items():
        fig.savefig(out / f"{name}.png", dpi=120)
    print("\nCharts saved in the figures/ folder")