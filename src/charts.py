"""Interactive (Plotly) charts and summary numbers used by the Streamlit dashboard."""
import pandas as pd
import plotly.graph_objects as go

from src.eda import CITY_COLORS, MONTH_NAMES, WHO_GUIDELINE

SMOG_MONTHS = (10, 11, 12, 1)  # smog season = October to January
UNHEALTHY_LIMIT = 55.4         # US EPA: PM2.5 above this is "Unhealthy" or worse


def _style(fig, height=430):
    """Common look for every Plotly chart."""
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis_title="PM2.5 (µg/m³)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hovermode="x unified",
    )
    return fig


# ---------- Summary numbers for the city cards ----------
def city_summary(df):
    """One row per city: average, days above WHO, share of unhealthy hours, worst month."""
    daily = df.set_index("time").groupby("city")["pm2_5"].resample("D").mean().dropna()
    monthly = df.groupby(["city", "month"])["pm2_5"].mean()
    worst = monthly.groupby(level=0).idxmax().map(lambda pair: MONTH_NAMES[pair[1] - 1])
    return pd.DataFrame({
        "avg": df.groupby("city")["pm2_5"].mean(),
        "days_above_who": (daily > WHO_GUIDELINE).groupby(level=0).mean() * 100,
        "unhealthy_pct": (df["pm2_5"] > UNHEALTHY_LIMIT).groupby(df["city"]).mean() * 100,
        "worst_month": worst,
    })


# ---------- Feature 2: daily trend with smog-season bands ----------
def daily_means(df):
    """Daily average PM2.5, one column per city."""
    daily = df.set_index("time").groupby("city")["pm2_5"].resample("D").mean().reset_index()
    return daily.pivot(index="time", columns="city", values="pm2_5")


def daily_trend_figure(df, window=7):
    """Line chart of daily PM2.5 with shaded smog seasons, WHO line and peak markers."""
    daily = daily_means(df)
    smooth = daily.rolling(window, min_periods=1).mean() if window > 1 else daily

    fig = go.Figure()
    for city in smooth.columns:
        color = CITY_COLORS.get(city, "#64748b")
        fig.add_trace(go.Scatter(
            x=smooth.index, y=smooth[city].round(1), name=city, mode="lines",
            line=dict(color=color, width=2),
        ))
        peak_day = smooth[city].idxmax()  # highest point of this city
        fig.add_trace(go.Scatter(
            x=[peak_day], y=[round(smooth[city].max(), 1)], mode="markers+text",
            text=[f"{smooth[city].max():.0f}"], textposition="top center",
            marker=dict(color=color, size=9, line=dict(color="white", width=1)),
            showlegend=False, hoverinfo="skip",
        ))

    # Grey bands for each smog season (October to January)
    first, last = daily.index.min(), daily.index.max()
    for year in range(first.year - 1, last.year + 1):
        x0 = max(pd.Timestamp(year, 10, 1), first)
        x1 = min(pd.Timestamp(year + 1, 1, 31), last)
        if x0 < x1:
            fig.add_vrect(x0=x0.strftime("%Y-%m-%d"), x1=x1.strftime("%Y-%m-%d"),
                          fillcolor="#94a3b8", opacity=0.15, layer="below", line_width=0)

    fig.add_hline(y=WHO_GUIDELINE, line_dash="dash", line_color="#475569",
                  annotation_text="WHO 24-h guideline (15)", annotation_position="bottom right")
    return _style(fig, height=470), daily.round(1)


# ---------- Feature 3: smog season tracker (year by year) ----------
def season_table(df):
    """Average PM2.5 of each complete smog season (Oct to Jan), per city."""
    d = df[df["month"].isin(SMOG_MONTHS)].copy()
    # October to December belong to the season that ends in January of the next year
    d["smog_year"] = d["year"].where(d["month"] >= 10, d["year"] - 1)
    months_present = d.groupby("smog_year")["month"].nunique()
    d = d[d["smog_year"].isin(months_present[months_present == 4].index)]
    if d.empty:
        return None
    table = d.groupby(["smog_year", "city"])["pm2_5"].mean().unstack().round(1)
    table.index = [f"{y}/{str(y + 1)[-2:]}" for y in table.index]
    return table


def season_figure(table):
    """Grouped bars: average PM2.5 of each smog season, one bar per city."""
    fig = go.Figure()
    for city in table.columns:
        fig.add_trace(go.Bar(
            x=table.index, y=table[city], name=city,
            marker_color=CITY_COLORS.get(city, "#64748b"),
            text=table[city], texttemplate="%{text:.0f}", textposition="outside",
        ))
    fig.add_hline(y=WHO_GUIDELINE, line_dash="dash", line_color="#475569",
                  annotation_text="WHO 24-h guideline (15)", annotation_position="top left")
    fig.update_layout(barmode="group", xaxis_title="Smog season (October to January)")
    return _style(fig)


# ---------- Day-of-week chart ----------
def weekday_figure(df):
    """Average PM2.5 for each day of the week, one bar per city."""
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    table = (df.assign(day=df["time"].dt.dayofweek)
               .groupby(["day", "city"])["pm2_5"].mean().unstack().reindex(range(7)))
    table.index = names
    fig = go.Figure()
    for city in table.columns:
        fig.add_trace(go.Bar(x=table.index, y=table[city].round(1), name=city,
                             marker_color=CITY_COLORS.get(city, "#64748b")))
    fig.update_layout(barmode="group")
    return _style(fig, height=380)