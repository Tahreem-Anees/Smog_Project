import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src import charts, eda

st.set_page_config(page_title="Smog Forecast Dashboard", page_icon="🌫️", layout="wide")

# ---------- Look and feel ----------
st.markdown(
    """
<style>
h2, h3, h4 {color: #134e4a;}
.banner {background: linear-gradient(120deg, #0f766e 0%, #0e8aa0 50%, #5b6cdb 100%);
         color: white; padding: 28px 32px; border-radius: 18px; margin-bottom: 18px;
         box-shadow: 0 6px 18px rgba(15, 118, 110, 0.25);}
.banner .tag {font-size: 12px; letter-spacing: 1.5px; opacity: 0.85; margin-bottom: 6px;}
.banner h1 {color: white; font-size: 30px; margin: 0 0 10px 0; padding: 0;}
.banner p {margin: 0 0 14px 0; opacity: 0.95; max-width: 760px;}
.pill {display: inline-block; background: rgba(255,255,255,0.20); padding: 4px 12px;
       border-radius: 999px; font-size: 12px; margin: 0 6px 4px 0;}
.glance {background: linear-gradient(90deg, #ffffff 0%, #e6f4f1 100%);
         border-left: 5px solid #0f766e; padding: 14px 18px;
         border-radius: 10px; margin-bottom: 18px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);}
.card {background: white; border: 1px solid #d9ebe7; border-radius: 14px;
       padding: 14px 16px; box-shadow: 0 3px 10px rgba(15, 118, 110, 0.10);}
.card .city {font-weight: 700; font-size: 15px;}
.card .big {font-size: 32px; font-weight: 700; line-height: 1.2;}
.card .unit {font-size: 12px; color: #6b7280;}
.card .badge {display: inline-block; border-radius: 999px; font-weight: 600;
              padding: 2px 10px; font-size: 12px; margin: 4px 0 8px 0;}
.card .row {display: flex; justify-content: space-between; font-size: 13px;
            padding: 3px 0; border-top: 1px solid #eef5f3;}
.step {background: white; border: 1px solid #d9ebe7; border-radius: 14px;
       padding: 12px 14px; height: 100%; box-shadow: 0 3px 10px rgba(15, 118, 110, 0.08);}
.step .num {display: inline-block; background: linear-gradient(135deg, #0f766e, #5b6cdb);
            color: white; border-radius: 50%; width: 24px; height: 24px; text-align: center;
            line-height: 24px; font-size: 13px; margin-bottom: 6px;}
[data-testid="stPlotlyChart"], [data-testid="stImage"] {background: white; border-radius: 14px;
       padding: 8px; box-shadow: 0 3px 10px rgba(15, 118, 110, 0.08);}
[data-testid="stMetric"] {background: white; border: 1px solid #d9ebe7; border-radius: 14px;
       padding: 12px 16px; box-shadow: 0 3px 10px rgba(15, 118, 110, 0.08);}
[data-testid="stExpander"] {background: white; border-radius: 12px;}
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Your own observations, shown under each group of charts ----------
# Fill these in your own words after you have understood the charts.
# Empty text is simply not shown on the page.
NOTES = {
    "daily": {"see": "", "so_what": ""},
    "seasons": {"see": "", "so_what": ""},
    "time": {"see": "", "so_what": ""},
    "weather": {"see": "", "so_what": ""},
    "lag": {"see": "", "so_what": ""},
    "distributions": {"see": "", "so_what": ""},
}


def show_notes(key):
    """Show 'What I see' and 'So what' under a group of charts."""
    note = NOTES[key]
    if note["see"]:
        st.markdown(f"**What I see:** {note['see']}")
    if note["so_what"]:
        st.markdown(f"**So what:** {note['so_what']}")


# ---------- Data loading (cached so the database is read only once) ----------
@st.cache_data
def load_data():
    return eda.load_clean()


@st.cache_data
def load_logs():
    """Read the validation and cleaning summaries saved by load.py and clean.py."""
    conn = sqlite3.connect(eda.DB_PATH)
    validation = pd.read_sql("SELECT * FROM validation_log", conn)
    cleaning = pd.read_sql("SELECT * FROM cleaning_log", conn)
    conn.close()
    return validation.iloc[0], cleaning.iloc[0]


# ---------- Small helpers ----------
def explain(text):
    """Blue box that tells the reader how to read the chart."""
    st.info(text, icon="💡")


def show_matplotlib(make_figure, *args, **kwargs):
    """Draw a matplotlib chart; show a friendly message if the selection is too small."""
    try:
        fig = make_figure(*args, **kwargs)
    except Exception:
        st.info("Not enough data in this selection for this chart. "
                "Try a longer date range or more cities.")
        return
    st.pyplot(fig)
    plt.close(fig)


def show_plotly(fig):
    st.plotly_chart(fig, width="stretch")


def banner(tag, title, text, pills):
    pill_html = "".join(f"<span class='pill'>{p}</span>" for p in pills)
    st.markdown(
        f"<div class='banner'><div class='tag'>{tag}</div><h1>{title}</h1>"
        f"<p>{text}</p>{pill_html}</div>",
        unsafe_allow_html=True,
    )


def city_card(city, row):
    color = eda.CITY_COLORS.get(city, "#64748b")
    multiple = row["avg"] / eda.WHO_GUIDELINE
    return (
        f"<div class='card' style='border-top: 4px solid {color}'>"
        f"<div class='city'>{city}</div>"
        f"<div><span class='big'>{row['avg']:.1f}</span> <span class='unit'>µg/m³ average</span></div>"
        f"<div class='badge' style='background: {color}22; color: {color}'>{multiple:.1f}× the WHO guideline</div>"
        f"<div class='row'><span>Days above WHO limit</span><b>{row['days_above_who']:.0f}%</b></div>"
        f"<div class='row'><span>Hours Unhealthy or worse</span><b>{row['unhealthy_pct']:.1f}%</b></div>"
        f"<div class='row'><span>Worst month</span><b>{row['worst_month']}</b></div>"
        f"</div>"
    )


# =====================================================================
# Dashboard 1: Pipeline and Data Quality
# =====================================================================
def show_pipeline_dashboard(df):
    validation, cleaning = load_logs()

    banner(
        "PROGRAMMING FOR AI · PROJECT 1 · ETL + EDA",
        "Dashboard 1: Pipeline and Data Quality",
        "How hourly PM2.5 and weather data for Lahore, Islamabad, Karachi and Peshawar "
        "was collected, checked and cleaned before any analysis.",
        ["Open-Meteo APIs", "SQLite database", "Pydantic + pandas"],
    )

    st.subheader("How the data flows")
    steps = [
        ("1", "Extract", "Two Open-Meteo APIs (Air Quality and Historical Weather) are called for each city."),
        ("2", "Validate", "Pydantic checks every row against physical limits, e.g. humidity from 0 to 100."),
        ("3", "Store raw", "Validated rows are saved unchanged in the raw_data table (SQLite)."),
        ("4", "Clean", "Duplicates removed, small gaps filled, rows with missing values dropped, time columns added."),
        ("5", "Store clean", "The result is saved in the clean_data table, which the EDA reads."),
    ]
    for col, (num, name, text) in zip(st.columns(5), steps):
        col.markdown(
            f"<div class='step'><div class='num'>{num}</div><br><b>{name}</b><br>"
            f"<span style='font-size:13px'>{text}</span></div>",
            unsafe_allow_html=True,
        )

    st.subheader("Pipeline numbers")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows passed validation", f"{int(validation['valid_rows']):,}")
    c2.metric("Rows rejected by validation", f"{int(validation['invalid_rows']):,}")
    c3.metric("Rows dropped in cleaning", f"{int(cleaning['rows_dropped_missing']):,}")
    c4.metric("Final clean rows", f"{int(cleaning['rows_after']):,}")
    st.caption(
        "The dropped rows are the first 5 hours of each city: PM2.5 data starts at 05:00 "
        "on 2022-08-04, so those hours have no value."
    )

    st.subheader("Data overview by city")
    st.dataframe(eda.overview(df))

    st.subheader("Data quality checks")
    st.dataframe(eda.quality_checks(df), hide_index=True)
    st.caption("Every check should show 0. These checks run on the clean table.")

    st.subheader("Rows per year")
    eda.set_city_colors(df["city"].unique())
    show_matplotlib(eda.plot_rows_per_year, df)
    st.caption("2022 and 2026 are partial years: data starts in August 2022 and ends in October 2026.")

    with st.expander("Pipeline log (cleaning step)"):
        st.dataframe(cleaning.astype(str).to_frame("value"))

    with st.expander("Preview of the clean data"):
        st.dataframe(df.head(100))

    st.warning(
        "Limitation: PM2.5 and weather values are modelled estimates from Open-Meteo "
        "(not ground-sensor readings), so they can under- or over-estimate local extremes."
    )


# =====================================================================
# Dashboard 2: EDA
# =====================================================================
def show_eda_dashboard(view):
    cities = sorted(view["city"].unique())
    eda.set_city_colors(cities)  # keeps every city's colour fixed in the charts

    first_day = view["time"].min().strftime("%b %Y")
    last_day = view["time"].max().strftime("%b %Y")
    banner(
        "PROGRAMMING FOR AI · PROJECT 1 · ETL + EDA",
        "Dashboard 2: Smog (PM2.5) in Pakistan's big cities",
        "Exploratory analysis of hourly air-quality and weather data. Use the filters on the "
        "left to choose cities and dates; every chart updates.",
        [f"📅 {first_day} to {last_day}", f"🏙️ {len(cities)} cities",
         f"🕒 {len(view):,} hourly readings", "🛰️ CAMS model estimates"],
    )

    summary = charts.city_summary(view)
    if len(summary) > 1:
        worst, best = summary["avg"].idxmax(), summary["avg"].idxmin()
        text = (
            f"<b>At a glance:</b> in this selection {worst} has the most polluted air, averaging "
            f"{summary.loc[worst, 'avg']:.0f} µg/m³, about {summary.loc[worst, 'avg'] / eda.WHO_GUIDELINE:.1f} times "
            f"the WHO daily guideline of {eda.WHO_GUIDELINE}. The cleanest is {best} at "
            f"{summary.loc[best, 'avg']:.0f} µg/m³, still {summary.loc[best, 'avg'] / eda.WHO_GUIDELINE:.1f} times the guideline."
        )
    else:
        only = summary.index[0]
        text = (
            f"<b>At a glance:</b> {only} averages {summary.loc[only, 'avg']:.0f} µg/m³ in this "
            f"selection, about {summary.loc[only, 'avg'] / eda.WHO_GUIDELINE:.1f} times the WHO daily guideline."
        )
    st.markdown(f"<div class='glance'>{text}</div>", unsafe_allow_html=True)

    st.subheader("Key numbers")
    st.caption("PM2.5 means tiny particles in the air (under 2.5 micrometres) that reach deep into the lungs. "
               "It is measured in µg/m³: the lower, the better.")
    for col, city in zip(st.columns(len(summary)), summary.index):
        col.markdown(city_card(city, summary.loc[city]), unsafe_allow_html=True)

    st.subheader("Explore the data")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Daily trend", "🗓️ Smog seasons", "🕒 Time patterns",
        "🌦️ Weather", "🔁 Lag and baseline", "📊 Distributions",
    ])

    # ----- Tab 1: daily trend -----
    with tab1:
        explain("The average PM2.5 of every day, one line per city. Dots mark each city's highest "
                "point. Grey bands are the smog season (October to January) and the dashed line "
                "is the WHO daily guideline.")
        choice = st.radio("Smoothing", ["Daily", "7-day average", "30-day average"],
                          index=1, horizontal=True)
        window = {"Daily": 1, "7-day average": 7, "30-day average": 30}[choice]
        fig, daily_table = charts.daily_trend_figure(view, window)
        show_plotly(fig)
        with st.expander("View the data behind this chart"):
            st.dataframe(daily_table)
        show_notes("daily")

    # ----- Tab 2: smog seasons -----
    with tab2:
        st.markdown("#### Smog season tracker: is each winter better or worse?")
        explain("Average PM2.5 of each complete smog season (October to January). Only seasons "
                "that have all four months in your selection are shown.")
        table = charts.season_table(view)
        if table is None:
            st.info("The selected dates do not contain a complete smog season (October to January).")
        else:
            show_plotly(charts.season_figure(table))
            if len(table) > 1:
                for city in table.columns:
                    first, last = table[city].iloc[0], table[city].iloc[-1]
                    change = (last - first) / first * 100
                    st.markdown(f"- **{city}:** {table.index[0]} was {first:.0f} µg/m³, "
                                f"{table.index[-1]} was {last:.0f} µg/m³ ({change:+.0f}%).")
            with st.expander("View the data behind this chart"):
                st.dataframe(table)
        st.markdown("#### Average PM2.5 by month and by season")
        show_matplotlib(eda.plot_monthly_by_city, view)
        show_matplotlib(eda.plot_season_by_city, view)
        show_notes("seasons")

    # ----- Tab 3: hour of day and day of week -----
    with tab3:
        st.markdown("#### Hour of day")
        explain("The average PM2.5 for each hour of the day (0 is midnight, 12 is noon). "
                "Choose a season to compare.")
        season = st.radio("Season", ["All year", "Winter", "Spring", "Summer", "Autumn"],
                          horizontal=True)
        show_matplotlib(eda.plot_hourly_by_city, view, None if season == "All year" else season)
        st.markdown("#### Day of week")
        explain("The average PM2.5 for each day of the week.")
        show_plotly(charts.weekday_figure(view))
        show_notes("time")

    # ----- Tab 4: weather -----
    with tab4:
        explain("Correlation tells whether two things move together: 0 means no link, "
                "near -1 or +1 means a strong link. A link does not prove that one thing causes the other.")
        show_matplotlib(eda.plot_weather_correlation_by_city, view)
        city = st.selectbox("City for the correlation heatmap", cities)
        show_matplotlib(eda.plot_correlation_heatmap, view, city=city)
        variable = st.selectbox("Weather variable for the scatter plot", eda.WEATHER_COLS)
        show_matplotlib(eda.plot_weather_scatter, view, variable)
        st.caption("In winter, low temperature, high pressure and high humidity occur together, "
                   "so their links with PM2.5 are mixed up with the season.")
        show_notes("weather")

    # ----- Tab 5: lag and baseline -----
    with tab5:
        explain("Autocorrelation shows how similar PM2.5 is to its own value some time earlier. "
                "A high value means yesterday's PM2.5 helps to predict today's.")
        show_matplotlib(eda.plot_autocorrelation, view)
        show_matplotlib(eda.plot_daily_autocorrelation, view)
        st.markdown("#### Simple baseline: tomorrow = today")
        try:
            st.dataframe(eda.persistence_baseline(view), hide_index=True)
        except Exception:
            st.info("Not enough data in this selection for the baseline.")
        st.caption("The forecasting model in Section 2 must beat this baseline to be worth using.")
        show_notes("lag")

    # ----- Tab 6: distributions -----
    with tab6:
        explain("Histograms show how often each value occurs. The box plot shows the middle 50% "
                "of PM2.5 values of each city (the line inside is the median).")
        show_matplotlib(eda.plot_histograms, view)
        show_matplotlib(eda.plot_pm25_by_city, view)
        st.markdown("#### Data quality checks (selected data)")
        st.dataframe(eda.quality_checks(view), hide_index=True)
        show_notes("distributions")

    st.caption("PM2.5 and weather values are modelled estimates from Open-Meteo, "
               "not ground-sensor readings.")


# =====================================================================
# Main: sidebar to switch between the two dashboards
# =====================================================================
df = load_data()

st.sidebar.title("🌫️ Smog Forecast")
page = st.sidebar.radio("Choose a dashboard", ["1. Pipeline and Data Quality", "2. EDA"])

if page.startswith("1"):
    show_pipeline_dashboard(df)  # data quality always uses the full data
else:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters")
    all_cities = sorted(df["city"].unique())
    chosen = st.sidebar.multiselect("Cities", all_cities, default=all_cities)

    min_day, max_day = df["time"].min().date(), df["time"].max().date()
    picked = st.sidebar.date_input("Date range", value=(min_day, max_day),
                                   min_value=min_day, max_value=max_day)

    if not chosen:
        st.warning("Choose at least one city in the sidebar.")
        st.stop()
    if len(picked) != 2:
        st.info("Choose an end date to finish the date range.")
        st.stop()

    start, end = picked
    mask = (
        df["city"].isin(chosen)
        & (df["time"] >= pd.Timestamp(start))
        & (df["time"] < pd.Timestamp(end) + pd.Timedelta(days=1))
    )
    view = df[mask]
    st.sidebar.caption(f"{len(view):,} hourly readings selected")

    if len(view) < 24 * 30:
        st.warning("Please choose at least 30 days of data so that the charts make sense.")
        st.stop()

    show_eda_dashboard(view)