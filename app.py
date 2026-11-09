"""
app.py — Streamlit Dashboard: Global Seismic Trends

Run with:
    streamlit run app.py

What it does:
    • Connects to the MySQL table `earthquake_db.earthquakes`
      (loaded by 03_load_to_mysql.py)
    • Shows KPI cards, a world map of strong earthquakes and the answers to
      26 of the 30 project questions, grouped into 5 tabs
    • Every answer shows the SQL used (expander) + result table + chart
    • Sidebar filters (year range, magnitude range) are injected into every
      query, so all answers update together

Design choices:
    • Separate file from the data pipeline so running `streamlit run app.py`
      queries the database directly without re-running API collection.
    • Queries execute directly in MySQL (`sql/04_sql_queries.sql`) rather than
      in-memory Pandas, keeping the analytics layer in SQL.
    • Built-in Streamlit charts (st.bar_chart / st.line_chart / st.map) keep
      the dashboard lightweight and responsive.
"""
import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# ─── Page Configuration ───
st.set_page_config(
    page_title="Global Seismic Trends Dashboard",
    layout="wide",
    page_icon="🌍",
)


# ─── MySQL Database Connection (credentials read from environment variables) ───
# load_dotenv() reads DB_USER / DB_PASSWORD etc. from the local '.env' file,
# so the password is never written in the code or uploaded to GitHub.
load_dotenv()

db_user = os.getenv("DB_USER", "root")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "3306")
db_name = os.getenv("DB_NAME", "earthquake_db")

if db_password is None:
    st.error("DB_PASSWORD is not set. Copy `.env.example` to `.env` and add your MySQL password, then restart the app.")
    st.stop()

connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(connection_string)


# ─── Helper Function to Run SQL Queries ───
def run_query(query, engine):
    """Execute SQL query and return result as a Pandas DataFrame."""
    df = pd.read_sql(query, con=engine)
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                df[col] = pd.to_numeric(df[col])
            except Exception:
                pass
    return df


# ─── Title ───
st.markdown("# 🌍 Global Seismic Trends: Data-Driven Earthquake Insights")
st.markdown("#### Interactive SQL Analytics Dashboard | USGS Earthquake Data (Last 5 Years)")
st.markdown("---")

# ─── Sidebar: Global Filters ───
st.sidebar.title("🎛️ Global Filters")

try:
    year_range_df = run_query("SELECT MIN(Year) as min_y, MAX(Year) as max_y FROM earthquakes", engine)
    min_year = int(year_range_df['min_y'].iloc[0])
    max_year = int(year_range_df['max_y'].iloc[0])
except Exception:
    min_year, max_year = 2019, 2024

year_filter = st.sidebar.slider("Year Range", min_year, max_year, (min_year, max_year))

try:
    mag_range_df = run_query("SELECT MIN(mag) as min_m, MAX(mag) as max_m FROM earthquakes", engine)
    min_mag = float(mag_range_df['min_m'].iloc[0])
    max_mag = float(mag_range_df['max_m'].iloc[0])
except Exception:
    min_mag, max_mag = 0.0, 10.0

mag_filter = st.sidebar.slider("Magnitude Range", min_mag, max_mag, (min_mag, max_mag), step=0.1)

# Build a WHERE clause from global filters
filter_clause = f"WHERE Year BETWEEN {year_filter[0]} AND {year_filter[1]} AND mag BETWEEN {mag_filter[0]} AND {mag_filter[1]}"

# ─── KPI Metrics ───
try:
    kpi_query = f"""
    SELECT
        COUNT(*) as total_events,
        ROUND(AVG(mag), 2) as avg_mag,
        SUM(CASE WHEN severity_flag = 'destructive' THEN 1 ELSE 0 END) as destructive_events,
        SUM(CASE WHEN tsunami = 1 THEN 1 ELSE 0 END) as tsunami_events
    FROM earthquakes
    {filter_clause}
    """
    kpi_df = run_query(kpi_query, engine)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🌐 Total Events", f"{int(kpi_df['total_events'].iloc[0]):,}")
    k2.metric("📏 Avg Magnitude", f"{kpi_df['avg_mag'].iloc[0]}")
    k3.metric("💥 Destructive Events", f"{int(kpi_df['destructive_events'].iloc[0]):,}")
    k4.metric("🌊 Tsunami Events", f"{int(kpi_df['tsunami_events'].iloc[0]):,}")
    st.markdown("---")
except Exception as e:
    st.error(f"Error loading KPI metrics: {e}")

# ─── World Map: where do strong earthquakes happen? ───
# st.map needs columns named latitude / longitude — our table already uses
# those names. Only M6.0+ ('destructive') events are plotted: plotting all
# ~100k events makes the map a solid blob and slows the browser.
try:
    map_df = run_query(f"""SELECT latitude, longitude, mag
FROM earthquakes
{filter_clause} AND severity_flag = 'destructive'""", engine)
    st.subheader("🗺️ Destructive Earthquakes (M ≥ 6.0) — Global Distribution")
    st.caption("The points trace the tectonic plate boundaries, especially the Pacific 'Ring of Fire'.")
    if not map_df.empty:
        st.map(map_df, latitude="latitude", longitude="longitude", size=20000)
    else:
        st.info("No destructive earthquakes for the selected filters.")
    st.markdown("---")
except Exception as e:
    st.error(f"Error loading map: {e}")

# ─── Tabs ───
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Magnitude & Depth",
    "⏰ Time Analysis",
    "🚨 Impact & Alerts",
    "🔬 Seismic Patterns",
    "🌊 Depth & Location Analysis"
])

# ═══════════════════════════════════════════════════════════════════════
# TAB 1: 📊 Magnitude & Depth (Q1, Q2, Q3, Q5)
# ═══════════════════════════════════════════════════════════════════════
with tab1:
    st.header("📊 Magnitude & Depth Analysis")

    # ── Q1 ──
    q1_sql = f"""SELECT id, time, place, country, mag, depth_km
FROM earthquakes
{filter_clause}
ORDER BY mag DESC LIMIT 10"""

    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q1: Top 10 Strongest Earthquakes")
        st.markdown("*Identifies the most powerful seismic events recorded in the dataset.*")
        with st.expander("📄 View SQL Query"):
            st.code(q1_sql, language='sql')
    with col2:
        try:
            df_q1 = run_query(q1_sql, engine)
            st.dataframe(df_q1, width="stretch")
            if not df_q1.empty:
                st.bar_chart(df_q1.set_index('place')['mag'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q2 ──
    q2_sql = f"""SELECT id, time, place, country, depth_km, mag
FROM earthquakes
{filter_clause}
ORDER BY depth_km DESC LIMIT 10"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q2: Top 10 Deepest Earthquakes")
        st.markdown("*Reveals the deepest seismic events, occurring far below the Earth's surface.*")
        with st.expander("📄 View SQL Query"):
            st.code(q2_sql, language='sql')
    with col2:
        try:
            df_q2 = run_query(q2_sql, engine)
            st.dataframe(df_q2, width="stretch")
            if not df_q2.empty:
                st.bar_chart(df_q2.set_index('place')['depth_km'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q3 ──
    q3_sql = f"""SELECT place, country, mag, depth_km, time
FROM earthquakes
{filter_clause} AND depth_km < 50 AND mag > 7.5
ORDER BY mag DESC"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q3: Shallow but Powerful Earthquakes")
        st.markdown("*Shallow quakes (depth < 50 km) with magnitude > 7.5 — the most destructive combination.*")
        with st.expander("📄 View SQL Query"):
            st.code(q3_sql, language='sql')
    with col2:
        try:
            df_q3 = run_query(q3_sql, engine)
            st.dataframe(df_q3, width="stretch")
            if df_q3.empty:
                st.info("No shallow high-magnitude earthquakes found for the selected filters.")
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q5 ──
    q5_sql = f"""SELECT magType, ROUND(AVG(mag), 2) as avg_mag, COUNT(*) as event_count
FROM earthquakes
{filter_clause}
GROUP BY magType
ORDER BY avg_mag DESC"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q5: Avg Magnitude by Magnitude Type")
        st.markdown("*Compares average magnitude across different measurement scales (ml, mb, mww, etc.).*")
        with st.expander("📄 View SQL Query"):
            st.code(q5_sql, language='sql')
    with col2:
        try:
            df_q5 = run_query(q5_sql, engine)
            st.dataframe(df_q5, width="stretch")
            if not df_q5.empty:
                st.bar_chart(df_q5.set_index('magType')['avg_mag'], horizontal=True)
        except Exception as e:
            st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# TAB 2: ⏰ Time Analysis (Q6, Q7, Q8, Q9, Q10)
# ═══════════════════════════════════════════════════════════════════════
with tab2:
    st.header("⏰ Time Analysis")

    # ── Q6 ──
    q6_sql = f"""SELECT Year, COUNT(*) as event_count
FROM earthquakes
{filter_clause}
GROUP BY Year
ORDER BY event_count DESC"""

    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q6: Year with Most Earthquakes")
        st.markdown("*Identifies which year recorded the highest seismic activity.*")
        with st.expander("📄 View SQL Query"):
            st.code(q6_sql, language='sql')
    with col2:
        try:
            df_q6 = run_query(q6_sql, engine)
            st.dataframe(df_q6, width="stretch")
            if not df_q6.empty:
                chart_df = df_q6.sort_values('Year')
                st.bar_chart(chart_df.set_index('Year')['event_count'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q7 ──
    q7_sql = f"""SELECT Month, COUNT(*) as event_count
FROM earthquakes
{filter_clause}
GROUP BY Month
ORDER BY event_count DESC"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q7: Month with Highest Earthquakes")
        st.markdown("*Explores seasonal patterns in earthquake occurrence.*")
        with st.expander("📄 View SQL Query"):
            st.code(q7_sql, language='sql')
    with col2:
        try:
            df_q7 = run_query(q7_sql, engine)
            st.dataframe(df_q7, width="stretch")
            if not df_q7.empty:
                chart_df = df_q7.sort_values('Month')
                st.bar_chart(chart_df.set_index('Month')['event_count'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q8 ──
    q8_sql = f"""SELECT Day_of_week, COUNT(*) as event_count
FROM earthquakes
{filter_clause}
GROUP BY Day_of_week
ORDER BY event_count DESC"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q8: Day of Week with Most Earthquakes")
        st.markdown("*Checks if seismic activity varies by day of the week.*")
        with st.expander("📄 View SQL Query"):
            st.code(q8_sql, language='sql')
    with col2:
        try:
            df_q8 = run_query(q8_sql, engine)
            st.dataframe(df_q8, width="stretch")
            if not df_q8.empty:
                st.bar_chart(df_q8.set_index('Day_of_week')['event_count'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q9 ──
    q9_sql = f"""SELECT Hour, COUNT(*) as event_count
FROM earthquakes
{filter_clause}
GROUP BY Hour
ORDER BY Hour"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q9: Earthquakes per Hour of Day")
        st.markdown("*Analyzes the hourly distribution of seismic events (UTC time).*")
        with st.expander("📄 View SQL Query"):
            st.code(q9_sql, language='sql')
    with col2:
        try:
            df_q9 = run_query(q9_sql, engine)
            st.dataframe(df_q9, width="stretch")
            if not df_q9.empty:
                st.line_chart(df_q9.set_index('Hour')['event_count'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q10 ──
    q10_sql = f"""SELECT net, COUNT(*) as event_count
FROM earthquakes
{filter_clause}
GROUP BY net
ORDER BY event_count DESC LIMIT 10"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q10: Most Active Seismic Networks")
        st.markdown("*Shows which seismic monitoring networks report the most events.*")
        with st.expander("📄 View SQL Query"):
            st.code(q10_sql, language='sql')
    with col2:
        try:
            df_q10 = run_query(q10_sql, engine)
            st.dataframe(df_q10, width="stretch")
            if not df_q10.empty:
                st.bar_chart(df_q10.set_index('net')['event_count'])
        except Exception as e:
            st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# TAB 3: 🚨 Impact & Alerts (Q11, Q13, Q14, Q15, Q16, Q18, Q19, Q20)
# ═══════════════════════════════════════════════════════════════════════
with tab3:
    st.header("🚨 Impact & Alerts Analysis")

    # ── Q11 ──
    q11_sql = f"""SELECT country, SUM(sig) as total_significance, ROUND(AVG(mag), 2) as avg_mag, COUNT(*) as event_count
FROM earthquakes
{filter_clause}
GROUP BY country
ORDER BY total_significance DESC LIMIT 5"""

    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q11: Top 5 Places by Significance (Casualty Proxy)")
        st.markdown("*Identifies regions with highest cumulative seismic significance.*")
        st.caption("⚠️ Using `sig` (significance) as proxy — USGS doesn't provide casualty data.")
        with st.expander("📄 View SQL Query"):
            st.code(q11_sql, language='sql')
    with col2:
        try:
            df_q11 = run_query(q11_sql, engine)
            st.dataframe(df_q11, width="stretch")
            if not df_q11.empty:
                st.bar_chart(df_q11.set_index('country')['total_significance'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q13 ──
    q13_sql = f"""SELECT alert, ROUND(AVG(sig), 2) as avg_significance, COUNT(*) as event_count
FROM earthquakes
{filter_clause}
GROUP BY alert
ORDER BY avg_significance DESC"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q13: Avg Significance by Alert Level")
        st.markdown("*Compares average significance scores across alert levels (green, yellow, orange, red).*")
        with st.expander("📄 View SQL Query"):
            st.code(q13_sql, language='sql')
    with col2:
        try:
            df_q13 = run_query(q13_sql, engine)
            st.dataframe(df_q13, width="stretch")
            if not df_q13.empty:
                st.bar_chart(df_q13.set_index('alert')['avg_significance'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q14 ──
    q14_sql = f"""SELECT status, COUNT(*) as event_count
FROM earthquakes
{filter_clause}
GROUP BY status"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q14: Reviewed vs Automatic Events")
        st.markdown("*Shows the proportion of human-reviewed vs automatically processed events.*")
        with st.expander("📄 View SQL Query"):
            st.code(q14_sql, language='sql')
    with col2:
        try:
            df_q14 = run_query(q14_sql, engine)
            st.dataframe(df_q14, width="stretch")
            if not df_q14.empty:
                st.bar_chart(df_q14.set_index('status')['event_count'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q15 ──
    q15_sql = f"""SELECT type, COUNT(*) as event_count
FROM earthquakes
{filter_clause}
GROUP BY type
ORDER BY event_count DESC"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q15: Event Count by Type")
        st.markdown("*Breaks down seismic events by type (earthquake, quarry blast, explosion, etc.).*")
        with st.expander("📄 View SQL Query"):
            st.code(q15_sql, language='sql')
    with col2:
        try:
            df_q15 = run_query(q15_sql, engine)
            st.dataframe(df_q15, width="stretch")
            if not df_q15.empty:
                st.bar_chart(df_q15.set_index('type')['event_count'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q16 ──
    q16_sql = f"""SELECT types, COUNT(*) AS earthquake_count
FROM earthquakes
{filter_clause}
GROUP BY types
ORDER BY earthquake_count DESC
LIMIT 10"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q16: Earthquakes by Data Type (types)")
        st.markdown("*Counts the top 10 combinations of associated data types.*")
        with st.expander("📄 View SQL Query"):
            st.code(q16_sql, language='sql')
    with col2:
        try:
            df_q16 = run_query(q16_sql, engine)
            st.dataframe(df_q16, width="stretch")
            if not df_q16.empty:
                st.bar_chart(df_q16.set_index('types')['earthquake_count'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q18 ──
    q18_sql = f"""SELECT CASE WHEN nst > 50 THEN 'High Coverage (nst>50)' ELSE 'Low Coverage (nst<=50)' END as coverage,
    COUNT(*) as event_count, ROUND(AVG(mag), 2) as avg_mag
FROM earthquakes
{filter_clause}
GROUP BY coverage"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q18: High vs Low Station Coverage")
        st.markdown("*Compares events with high station coverage (nst > 50) vs low coverage.*")
        with st.expander("📄 View SQL Query"):
            st.code(q18_sql, language='sql')
    with col2:
        try:
            df_q18 = run_query(q18_sql, engine)
            st.dataframe(df_q18, width="stretch")
            if not df_q18.empty:
                mcols = st.columns(len(df_q18))
                for i, row in df_q18.iterrows():
                    with mcols[i]:
                        st.metric(label=row['coverage'], value=f"{int(row['event_count']):,} events")
                        st.metric(label="Avg Magnitude", value=str(row['avg_mag']))
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q19 ──
    q19_sql = f"""SELECT Year, COUNT(*) as tsunami_count
FROM earthquakes
{filter_clause} AND tsunami = 1
GROUP BY Year
ORDER BY Year"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q19: Tsunamis per Year")
        st.markdown("*Tracks the number of tsunami-associated earthquake events per year.*")
        with st.expander("📄 View SQL Query"):
            st.code(q19_sql, language='sql')
    with col2:
        try:
            df_q19 = run_query(q19_sql, engine)
            st.dataframe(df_q19, width="stretch")
            if not df_q19.empty:
                st.bar_chart(df_q19.set_index('Year')['tsunami_count'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q20 ──
    q20_sql = f"""SELECT alert, COUNT(*) as event_count, ROUND(AVG(mag), 2) as avg_mag, ROUND(AVG(sig), 2) as avg_sig
FROM earthquakes
{filter_clause}
GROUP BY alert
ORDER BY event_count DESC"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q20: Count by Alert Levels")
        st.markdown("*Summarizes event count, average magnitude, and significance by PAGER alert level.*")
        with st.expander("📄 View SQL Query"):
            st.code(q20_sql, language='sql')
    with col2:
        try:
            df_q20 = run_query(q20_sql, engine)
            st.dataframe(df_q20, width="stretch")
            if not df_q20.empty:
                st.bar_chart(df_q20.set_index('alert')['event_count'])
        except Exception as e:
            st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# TAB 4: 🔬 Seismic Patterns (Q21, Q22, Q23, Q24)
# ═══════════════════════════════════════════════════════════════════════
with tab4:
    st.header("🔬 Seismic Patterns")

    # ── Q21 ──
    q21_sql = f"""SELECT country, ROUND(AVG(mag), 2) as avg_mag, COUNT(*) as event_count
FROM earthquakes
{filter_clause}
GROUP BY country
HAVING event_count > 10
ORDER BY avg_mag DESC LIMIT 5"""

    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q21: Top 5 Countries by Avg Magnitude")
        st.markdown("*Countries with the highest average earthquake magnitude (min 10 events).*")
        with st.expander("📄 View SQL Query"):
            st.code(q21_sql, language='sql')
    with col2:
        try:
            df_q21 = run_query(q21_sql, engine)
            st.dataframe(df_q21, width="stretch")
            if not df_q21.empty:
                st.bar_chart(df_q21.set_index('country')['avg_mag'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q22 ──
    q22_sql = f"""SELECT country, Year, Month, COUNT(DISTINCT depth_flag) as depth_types,
    SUM(CASE WHEN depth_flag = 'shallow' THEN 1 ELSE 0 END) as shallow_count,
    SUM(CASE WHEN depth_flag = 'deep' THEN 1 ELSE 0 END) as deep_count
FROM earthquakes
{filter_clause}
GROUP BY country, Year, Month
HAVING depth_types = 2
ORDER BY Year, Month"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q22: Countries with Both Shallow & Deep Quakes in Same Month")
        st.markdown("*Identifies country-month combinations with both shallow and deep-focus seismicity.*")
        with st.expander("📄 View SQL Query"):
            st.code(q22_sql, language='sql')
    with col2:
        try:
            df_q22 = run_query(q22_sql, engine)
            st.dataframe(df_q22, width="stretch", height=400)
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q23 ──
    q23_sql = f"""SELECT Year, event_count, prev_year_count,
    ROUND((event_count - prev_year_count) / prev_year_count * 100, 2) AS growth_rate_pct
FROM (
    SELECT Year, COUNT(*) AS event_count,
           LAG(COUNT(*)) OVER (ORDER BY Year) AS prev_year_count
    FROM earthquakes
    {filter_clause}
    GROUP BY Year
) yearly_counts
ORDER BY Year"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q23: Year-over-Year Growth Rate")
        st.markdown("*Tracks how earthquake frequency changes from year to year.*")
        with st.expander("📄 View SQL Query"):
            st.code(q23_sql, language='sql')
    with col2:
        try:
            df_q23 = run_query(q23_sql, engine)
            st.dataframe(df_q23, width="stretch")
            if not df_q23.empty:
                chart_df = df_q23.dropna(subset=['growth_rate_pct'])
                if not chart_df.empty:
                    st.line_chart(chart_df.set_index('Year')['growth_rate_pct'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q24 ──
    q24_sql = f"""SELECT country, COUNT(*) as frequency, ROUND(AVG(mag), 2) as avg_mag,
    ROUND(COUNT(*) * AVG(mag), 2) as composite_score
FROM earthquakes
{filter_clause}
GROUP BY country
ORDER BY composite_score DESC LIMIT 3"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q24: Top 3 Most Active Regions (Composite Score)")
        st.markdown("*Ranks countries by a composite score (frequency × avg magnitude).*")
        with st.expander("📄 View SQL Query"):
            st.code(q24_sql, language='sql')
    with col2:
        try:
            df_q24 = run_query(q24_sql, engine)
            st.dataframe(df_q24, width="stretch")
            if not df_q24.empty:
                st.bar_chart(df_q24.set_index('country')['composite_score'])
        except Exception as e:
            st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# TAB 5: 🌊 Depth & Location Analysis (Q25, Q26, Q27, Q28, Q30)
# ═══════════════════════════════════════════════════════════════════════
with tab5:
    st.header("🌊 Depth & Location Analysis")

    # ── Q25 ──
    q25_sql = f"""SELECT country, ROUND(AVG(depth_km), 2) as avg_depth, COUNT(*) as event_count
FROM earthquakes
{filter_clause} AND latitude BETWEEN -5 AND 5
GROUP BY country
ORDER BY avg_depth DESC"""

    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q25: Avg Depth Near Equator by Country")
        st.markdown("*Average earthquake depth for equatorial regions (latitude ±5°).*")
        with st.expander("📄 View SQL Query"):
            st.code(q25_sql, language='sql')
    with col2:
        try:
            df_q25 = run_query(q25_sql, engine)
            st.dataframe(df_q25, width="stretch")
            if not df_q25.empty:
                st.bar_chart(df_q25.set_index('country')['avg_depth'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q26 ──
    q26_sql = f"""SELECT country,
    SUM(CASE WHEN depth_flag = 'shallow' THEN 1 ELSE 0 END) as shallow_count,
    SUM(CASE WHEN depth_flag = 'deep' THEN 1 ELSE 0 END) as deep_count,
    ROUND(SUM(CASE WHEN depth_flag = 'shallow' THEN 1 ELSE 0 END) / NULLIF(SUM(CASE WHEN depth_flag = 'deep' THEN 1 ELSE 0 END), 0), 2) as shallow_to_deep_ratio
FROM earthquakes
{filter_clause}
GROUP BY country
HAVING deep_count > 0
ORDER BY shallow_to_deep_ratio DESC LIMIT 10"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q26: Shallow-to-Deep Ratio by Country")
        st.markdown("*Ratio of shallow to deep-focus earthquakes — indicates tectonic regime.*")
        with st.expander("📄 View SQL Query"):
            st.code(q26_sql, language='sql')
    with col2:
        try:
            df_q26 = run_query(q26_sql, engine)
            st.dataframe(df_q26, width="stretch")
            if not df_q26.empty:
                st.bar_chart(df_q26.set_index('country')['shallow_to_deep_ratio'])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q27 ──
    q27_sql = f"""SELECT ROUND(AVG(CASE WHEN tsunami = 1 THEN mag END), 2) AS avg_mag_tsunami,
    ROUND(AVG(CASE WHEN tsunami = 0 THEN mag END), 2) AS avg_mag_no_tsunami,
    ROUND(AVG(CASE WHEN tsunami = 1 THEN mag END) - AVG(CASE WHEN tsunami = 0 THEN mag END), 2) AS mag_difference,
    SUM(tsunami = 1) AS tsunami_events,
    SUM(tsunami = 0) AS non_tsunami_events
FROM earthquakes
{filter_clause}"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q27: Avg Magnitude — Tsunami vs Non-Tsunami")
        st.markdown("*Average magnitude of tsunami-flagged vs other earthquakes, and the difference between them.*")
        with st.expander("📄 View SQL Query"):
            st.code(q27_sql, language='sql')
    with col2:
        try:
            df_q27 = run_query(q27_sql, engine)
            st.dataframe(df_q27, width="stretch")
            if not df_q27.empty:
                r = df_q27.iloc[0]
                m1, m2, m3 = st.columns(3)
                m1.metric("🌊 Tsunami — Avg Mag", str(r['avg_mag_tsunami']))
                m2.metric("No Tsunami — Avg Mag", str(r['avg_mag_no_tsunami']))
                m3.metric("Difference", str(r['mag_difference']))
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q28 ──
    q28_sql = f"""SELECT id, place, country, mag, gap, rms,
    ROUND((gap + rms) / 2, 2) AS avg_error_margin
FROM earthquakes
{filter_clause}
ORDER BY avg_error_margin DESC
LIMIT 10"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q28: Lowest Data Reliability Events")
        st.markdown("*Events with the highest average error margin using gap and rms.*")
        with st.expander("📄 View SQL Query"):
            st.code(q28_sql, language='sql')
    with col2:
        try:
            df_q28 = run_query(q28_sql, engine)
            st.dataframe(df_q28, width="stretch")
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ── Q30 ──
    q30_sql = f"""SELECT country, COUNT(*) as deep_focus_count, ROUND(AVG(depth_km), 2) as avg_depth
FROM earthquakes
{filter_clause} AND depth_km > 300
GROUP BY country
ORDER BY deep_focus_count DESC LIMIT 10"""

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Q30: Deep-Focus Earthquake Regions")
        st.markdown("*Countries with the most deep-focus earthquakes (depth > 300 km).*")
        with st.expander("📄 View SQL Query"):
            st.code(q30_sql, language='sql')
    with col2:
        try:
            df_q30 = run_query(q30_sql, engine)
            st.dataframe(df_q30, width="stretch")
            if not df_q30.empty:
                st.bar_chart(df_q30.set_index('country')['deep_focus_count'])
        except Exception as e:
            st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════════
# Notes Section
# ═══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📝 Notes")
st.info("""
**Queries Q4, Q12, Q17, Q29 are intentionally skipped:**
- Q4, Q17: Require 'continent' column — not part of the 26 USGS features
- Q12: Requires economic loss data — not provided by USGS API  
- Q29: Requires complex spatial distance computation between consecutive events
""")

st.markdown("---")
st.caption("Built with ❤️ using Streamlit | Data Source: USGS Earthquake API")
