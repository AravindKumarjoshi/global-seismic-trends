# Project Report — Global Seismic Trends: Data-Driven Earthquake Insights

**Author:** Aravind Kumar Joshi

This document summarizes the domain context, architecture, ETL decisions, exploratory analysis, statistical hypothesis tests, and business recommendations for **Global Seismic Trends: Data-Driven Earthquake Insights**.

---

## 1. Domain Introduction
- **Geoscience & Seismology** studies how tectonic stress builds up and releases along fault lines and plate boundaries as earthquakes.
- Because earthquakes cannot be predicted deterministically, **Disaster Management** relies on historical seismic catalogs to map hazard zones, depth regimes, and recurrence rates.
- Data-driven seismic analysis helps governments, insurers, and emergency agencies allocate resources, enforce building codes, and design early-warning systems.

---

## 2. Project Introduction
- **Global Seismic Trends** is an end-to-end data analytics pipeline that I built to collect 5 full calendar years of global M3.0+ earthquake records from the **USGS FDSN API**, clean and enrich the dataset in Python, and store it in a relational **MySQL** database.
- On top of the database, **26 analytical SQL queries** and an interactive **Streamlit dashboard** surface insights across magnitude, focal depth, temporal patterns, reporting network quality, and PAGER alert severity.

---

## 3. Objective of the Project
- Build a reproducible ETL and SQL analytics system covering all **26 USGS seismic features** plus derived temporal and risk-classification columns.
- Translate raw seismic telemetry into actionable insights for disaster preparedness, risk ranking, and monitoring-network reliability assessment.

---

## 4. ETL Process & Data Migration (API → CSV → MySQL)

| Stage | What Happens | Options Checked & Why I Chose This Approach |
|---|---|---|
| **Extract (`src/01_data_collection.py`)** | Queries the USGS API month-by-month across the last 5 complete calendar years (`minmagnitude=3.0`) in **both CSV and GeoJSON** formats, merging them on `id` using `pd.merge()`. | **Why month-by-month?** USGS enforces a 20,000-row limit per request; full-year requests risk truncation.<br>**Why both CSV + GeoJSON?** CSV gives 22 tabular columns directly, while GeoJSON contains `tsunami`, `sig`, `alert`, `types`, `ids`, and `sources`.<br>**Why `pd.merge` on `id`?** Ensures every earthquake's `tsunami`, `sig`, and `alert` values match its exact event ID. |
| **Transform (`src/02_data_cleaning.py`)** | Converts timestamps using `pd.to_datetime()`, extracts `country` via a custom function and `.apply()`, normalises strings with `.str.lower()` and `.replace()`, fills missing continuous values with the **median**, fills missing `alert` with `'unassessed'` (domain-based imputation), drops duplicates, and adds derived columns. | **Why median over mean?** In a **Right Skewed distribution (`mean > median`)**, high-value outliers pull the mean up (`nst` mean `41.74` > median `32.00`); the median is not distorted by outliers.<br>**Why `'unassessed'` over mode (`'green'`) for missing `alert`?** `'green'` means PAGER evaluated the quake and found low impact, whereas `NaN` means it was not evaluated at all. |
| **Load (`src/03_load_to_mysql.py`)** | Reads database credentials from `.env`, connects to MySQL using `pymysql` cursor (`CREATE DATABASE IF NOT EXISTS earthquake_db`), and uses SQLAlchemy `create_engine()` with `df.to_sql(name='earthquakes', if_exists='replace', chunksize=10000)` to insert all 104,464 rows. | **Why `if_exists='replace'` and `chunksize=10000`?** `replace` ensures re-running the script recreates a clean table without duplicating rows, and `chunksize=10000` sends rows in batches so MySQL packet limits are not exceeded. |

---

## 5. Exploratory Data Analysis (EDA) Findings (`src/05_eda.py`)
- **Distribution & Skewness:** I compared `mean` vs `median` and plotted `sns.histplot(..., kde=True)` and `sns.kdeplot()`. Continuous columns like `depth_km` (mean `72.05` > median `21.10`) and `nst` (mean `41.74` > median `32.00`) are **Right Skewed (`mean > median`)** due to outliers, which I visualised using `sns.boxplot()` and `np.log10()`.
- **Groupby, Pivot Table & Correlation:** I used `df.groupby(["country"]).agg(...)` and `pd.pivot_table()` to summarise yearly shallow vs deep earthquakes, and `df.corr()` with `sns.heatmap(..., cmap="coolwarm", fmt=".2f", annot=True)` to confirm a strong positive correlation (`0.89`) between `mag` and `sig`.

---

## 6. Feature Engineering (`src/02_data_cleaning.py`)
- **Location Extraction (`country`):** Extracted **493 unique countries/regions** from `place` using `df["place"].apply(get_country)` and `.replace()` to standardise state and country abbreviations.
- **Temporal Features (`Year`, `Month`, `Day`, `Hour`, `Day_of_week`):** Extracted from `time` using `.dt.year`, `.dt.month`, `.dt.day`, `.dt.hour`, and `.dt.day_name()`.
- **Domain Binary Flags (`depth_flag`, `severity_flag`):**
  - `depth_flag`: `'shallow'` (≤ 70 km, `78,018` events) vs `'deep'` (> 70 km, `26,446` events).
  - `severity_flag`: `'destructive'` (mag ≥ 6.0, `675` events) vs `'standard'` (< 6.0, `103,789` events).

---

## 7. Statistical Hypothesis Testing (`src/05_eda.py` — Section 7)
I applied three statistical hypothesis tests using `scipy.stats` (`ttest_ind`, `f_oneway`, `chi2_contingency`, with significance threshold `p_val < 0.05` → Reject Null Hypothesis):
1. **T-Test (`ttest_ind` — continuous vs continuous):** Tested `mag` of tsunami (`5.42`) vs non-tsunami (`4.25`) earthquakes → `p_val < 0.05` (Reject Null Hypothesis: significant difference).
2. **ANOVA (`f_oneway` — continuous vs categorical):** Tested `mag` across PAGER `alert` categories (`green`, `yellow`, `orange`, `red`) → `p_val < 0.05` (Reject Null Hypothesis: magnitude differs significantly by alert level).
3. **Chi-Square Test (`chi2_contingency` with `pd.crosstab` — categorical vs categorical):** Tested relationship between `alert` and `severity_flag` → `p_val < 0.05` (Reject Null Hypothesis: significant relationship).

---

## 8. Handling Missing Schema Fields (Skipped Queries & Proxy Choice)
- **Proxy Used for Q11 & Q13 (`sig` for Casualties / Economic Loss):** The USGS API does not provide casualty counts or dollar loss columns in its 26 features. I used `sig` (USGS composite significance score driven by magnitude, PAGER impact, and felt reports) as a domain proxy.
- **Skipped Queries (`Q4`, `Q12`, `Q17`, `Q29`):**
  - **Q4, Q12, Q17** require grouping by `continent` (and Q12 also requires `economic_loss`), neither of which exists in the 26 USGS features.
  - **Q29** requires pairwise 50 km spherical distance across consecutive events, which requires spatial geometry indexes or a self-join Haversine formula outside standard tabular SQL.

---

## 9. Conclusion (Key Findings Summary)
- Over two-thirds of global M3.0+ earthquakes (`74.68%`) are **shallow (≤ 70 km)**, and destructive earthquakes (**M ≥ 6.0**) concentrate along subduction boundaries—most notably the Pacific Ring of Fire.
- Temporal analysis across years, months, weekdays, and hours shows that tectonic activity is time-invariant, while tsunami-linked events have a statistically higher average magnitude than non-tsunami events.

---

## 10. Business Suggestions / Solutions
- **Disaster & Urban Planning:** Governments and insurers should weight seismic risk models by **both magnitude and shallow focal depth (< 50–70 km)** rather than magnitude alone, prioritising retrofitting in high-frequency shallow-quake regions identified in Q3, Q24, and Q26.
- **Seismic Network Investment:** International monitoring agencies should add ocean-bottom or island seismometers in regions flagged by **Q28** (high azimuthal `gap` and high `rms`), reducing location uncertainty for remote tsunami-generating trenches.
