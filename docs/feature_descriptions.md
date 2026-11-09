# 📊 Earthquake Dataset — Feature Descriptions

**Author:** Aravind Kumar Joshi

## Overview
This document describes all **26 base features** collected from the USGS Earthquake API,
plus the **derived columns** created during data preprocessing.

**Data Source:** [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/fdsnws/event/1/)  
**Collection Method:** REST API calls (CSV + GeoJSON formats merged)  
**Time Range:** Last 5 years (dynamically calculated)  
**Minimum Magnitude Filter:** 3.0  

---

## 26 Base Features

### 1. `id` — Event Identifier
- **Type:** String  
- **Example:** `us7000abc1`  
- **Description:** Unique identifier assigned by USGS for each earthquake event.  
- **Usage:** Primary key for deduplication and cross-referencing events.

### 2. `time` — Event Timestamp
- **Type:** Datetime  
- **Example:** `2024-01-15 08:32:45`  
- **Description:** Exact UTC timestamp when the earthquake occurred.  
- **Usage:** Time-series analysis, trend identification, frequency counts by year/month/hour.  
- **Processing Note:** Converted from ISO 8601 string format using `pd.to_datetime()`. Not using `unit='ms'` because the CSV format provides text timestamps, not Unix milliseconds.

### 3. `updated` — Last Update Timestamp
- **Type:** Datetime  
- **Description:** Timestamp of the most recent revision to this earthquake record.  
- **Usage:** Ensures analysis uses the latest refined data. USGS continuously updates earthquake parameters as more station data arrives.

### 4. `latitude` — Epicenter Latitude
- **Type:** Float  
- **Range:** -90.0 to 90.0  
- **Description:** Latitude coordinate of the earthquake's epicenter (surface point directly above the rupture).  
- **Usage:** Geospatial mapping, equatorial analysis (Q25), proximity calculations.

### 5. `longitude` — Epicenter Longitude
- **Type:** Float  
- **Range:** -180.0 to 180.0  
- **Description:** Longitude coordinate of the earthquake's epicenter.  
- **Usage:** Combined with latitude for geospatial analysis and mapping.

### 6. `depth_km` — Focal Depth
- **Type:** Float  
- **Unit:** Kilometers  
- **Description:** Depth below the Earth's surface where the earthquake rupture initiated.  
- **Why it matters:**
  - Shallow earthquakes (0–70 km) cause the most severe surface damage
  - Deep earthquakes (300+ km) are felt over wider areas but with less intensity
  - Depth significantly affects the destructive potential of an earthquake  
- **Processing Note:** Originally named `depth` in the CSV. Renamed to `depth_km` for clarity.

### 7. `mag` — Magnitude
- **Type:** Float  
- **Range:** 3.0+ (filtered during collection)  
- **Description:** The magnitude of the earthquake — the primary measure of energy released.  
- **Scale Context:**
  - 3.0–3.9: Minor (often felt, rarely causes damage)
  - 4.0–5.9: Moderate to Strong (can cause moderate damage)
  - 6.0–6.9: Major (serious damage in populated areas)
  - 7.0+: Great/Destructive (widespread, severe damage)  
- **Usage:** Key metric for ranking, filtering, severity classification.

### 8. `magType` — Magnitude Type
- **Type:** String  
- **Common Values:** `ml` (local), `mb` (body-wave), `mww` (moment tensor), `md` (duration)  
- **Description:** The method used to calculate the magnitude.  
- **Why it matters:** Different methods are optimized for different earthquake sizes and distances. Comparing magnitudes across types requires awareness of these differences.

### 9. `place` — Location Description
- **Type:** String  
- **Example:** `"10 km SSW of Shizunai, Japan"`  
- **Description:** Human-readable description of the earthquake location.  
- **Usage:** The `country` derived column is extracted from this field using regex (splitting on comma).  
- **Processing Note:** Original `place` column is preserved as-is (it's one of the 26 features). A separate `country` column is derived for grouping.

### 10. `status` — Review Status
- **Type:** String  
- **Values:** `reviewed`, `automatic`  
- **Description:** Whether the earthquake record has been manually reviewed by a seismologist or is still an automatic computer determination.  
- **Usage:** Filter for high-confidence data (reviewed) vs preliminary data (automatic).

### 11. `tsunami` — Tsunami Indicator
- **Type:** Integer (0 or 1)  
- **Source:** GeoJSON format (not available in CSV)  
- **Description:** Flag indicating whether a tsunami was generated or a tsunami advisory was issued.  
- **Usage:** Analyzing secondary effects, tsunami frequency trends (Q19, Q27).

### 12. `sig` — Significance Score
- **Type:** Integer  
- **Range:** 0 to 1000+  
- **Source:** GeoJSON format  
- **Description:** A composite significance score calculated by USGS based on magnitude, felt reports, PAGER alert level, and estimated impact.  
- **Why it matters:** This is the closest proxy for human/economic impact available in USGS data. Higher significance = more impactful event.  
- **Usage:** Used as a proxy for impact assessment in Q11 and Q13 (since USGS does not provide direct casualty or economic loss figures).

### 13. `net` — Reporting Network
- **Type:** String  
- **Examples:** `us` (USGS), `ci` (California), `pr` (Puerto Rico)  
- **Description:** The network or agency code that reported this earthquake.  
- **Usage:** Network-specific analysis, identifying the primary data source (Q10).

### 14. `nst` — Number of Reporting Stations
- **Type:** Float (can have NaN)  
- **Description:** Total number of seismic stations that recorded and reported this earthquake.  
- **Why it matters:** More stations = more data points = higher confidence in the calculated location and magnitude.  
- **Missing Value Strategy:** Filled with **median** (not mean) because station counts have extreme outliers (1 vs 500+ stations). Median is robust to these outliers.

### 15. `dmin` — Distance to Nearest Station
- **Type:** Float  
- **Unit:** Degrees (1° ≈ 111 km)  
- **Description:** Horizontal distance from the epicenter to the closest seismic station.  
- **Why it matters:**
  - Small dmin (~0.1°): Station was nearby → very precise location/depth
  - Large dmin (~10°+): Nearest station was far away → less precise (common for mid-ocean earthquakes)  
- **Missing Value Strategy:** Filled with **median**.

### 16. `rms` — Travel-Time Residual
- **Type:** Float  
- **Unit:** Seconds  
- **Description:** Root Mean Square of the travel-time residuals. Measures how well the observed seismic wave arrival times match the theoretical model.  
- **Interpretation:** Lower RMS = better fit = more reliable location determination.  
- **Missing Value Strategy:** Filled with **median**.

### 17. `gap` — Azimuthal Gap
- **Type:** Float  
- **Unit:** Degrees (0–360)  
- **Description:** The largest azimuthal angle between adjacent seismic stations as seen from the epicenter.  
- **Interpretation:**
  - Small gap (<90°): Good station coverage surrounding the earthquake
  - Large gap (>180°): Poor coverage, location may be less reliable  
- **Missing Value Strategy:** Filled with **median**.

### 18. `magError` — Magnitude Uncertainty
- **Type:** Float  
- **Description:** The estimated standard error of the magnitude calculation.  
- **Usage:** Filtering for high-confidence magnitude values; data quality assessment (Q28).  
- **Missing Value Strategy:** Filled with **median**.

### 19. `depthError` — Depth Uncertainty
- **Type:** Float  
- **Unit:** Kilometers  
- **Description:** The estimated uncertainty in the calculated depth.  
- **Interpretation:** Lower error = more reliable depth. High errors occur when station geometry is poor.  
- **Missing Value Strategy:** Filled with **median**.

### 20. `magNst` — Magnitude Station Count
- **Type:** Float  
- **Description:** Number of seismic stations specifically used for the magnitude calculation (separate from `nst` which is for location).  
- **Usage:** Reliability metric — more stations contributing to magnitude = more robust measurement.  
- **Missing Value Strategy:** Filled with **median**.

### 21. `locationSource` — Location Agency
- **Type:** String  
- **Description:** The network/agency code that determined the earthquake's location (epicenter).  
- **Usage:** Tracking which agency's data was used for spatial calculations.

### 22. `magSource` — Magnitude Agency
- **Type:** String  
- **Description:** The network/agency code that calculated the earthquake's magnitude.  
- **Usage:** Verifying consistency across different agencies' magnitude measurements.

### 23. `types` — Associated Data Types
- **Type:** String (comma-separated)  
- **Examples:** `origin,phase-data,dyfi,shakemap`  
- **Description:** Types of supplementary data products associated with this event.  
- **Processing Note:** Leading/trailing commas stripped during cleaning.

### 24. `ids` — Associated Event IDs
- **Type:** String (comma-separated)  
- **Description:** All IDs associated with this event across different networks/agencies.  
- **Usage:** Cross-referencing the same earthquake across different reporting systems.  
- **Processing Note:** Leading/trailing commas stripped during cleaning.

### 25. `sources` — Reporting Sources
- **Type:** String (comma-separated)  
- **Description:** All agencies/networks that reported this event.  
- **Usage:** Reliability assessment — more sources reporting = higher confidence.  
- **Processing Note:** Leading/trailing commas stripped during cleaning.

### 26. `type` — Event Type
- **Type:** String  
- **Common Values:** `earthquake`, `explosion`, `quarry blast`  
- **Description:** The type of seismic event recorded.  
- **Usage:** Filtering to analyze only actual earthquakes vs man-made events (Q15).

---

## Derived Columns (Created During Preprocessing)

### `country` — Extracted Country/Region
- **Source:** Extracted from `place` using regex  
- **Method:** Split on comma, take the last segment (which is typically the country or region name)  
- **Example:** `"10 km SSW of Shizunai, Japan"` → `"Japan"`  
- **Why `.apply()` over a for-loop:** A for-loop that assigns `df['place'] = value` overwrites the entire column on each iteration. `.apply()` processes row-by-row correctly.  
- **Why keep `place` too:** `place` is one of the 26 required features; `country` is a cleaner derived field for GROUP BY operations.

### `Year` — Event Year
- **Source:** `df['time'].dt.year`  
- **Usage:** Annual trend analysis (Q6, Q23)

### `Month` — Event Month
- **Source:** `df['time'].dt.month`  
- **Usage:** Seasonal pattern analysis (Q7, Q22)

### `Day` — Event Day of Month
- **Source:** `df['time'].dt.day`

### `Hour` — Event Hour (0–23)
- **Source:** `df['time'].dt.hour`  
- **Usage:** Hourly distribution analysis (Q9)

### `Day_of_week` — Day Name
- **Source:** `df['time'].dt.day_name()`  
- **Values:** Monday, Tuesday, ... Sunday  
- **Usage:** Weekly pattern analysis (Q8)

### `depth_flag` — Depth Classification
- **Values:** `shallow` (≤ 70 km), `deep` (> 70 km)  
- **Why binary (not 3-level)?** The project specification says *"Shallow/deep earthquake **flag**"* — the word "flag" implies a binary indicator. In seismology, three levels exist (shallow/intermediate/deep), but a **flag** is a true/false classification.  
- **Threshold:** 70 km is the standard seismological boundary between shallow and intermediate earthquakes (USGS/NEIC classification).

### `severity_flag` — Magnitude Severity Classification
- **Values:** `standard` (< 6.0), `destructive` (≥ 6.0)  
- **Why binary?** The project specification says *"Strong/destructive **flag**"* — flag implies binary.  
- **Threshold:** 6.0 is the widely-accepted threshold for potentially destructive earthquakes (USGS Earthquake Hazards Program).  
- **Why "standard" instead of "strong"?** Earthquakes in the 3.0–3.9 range are technically "minor/light", not "strong". Using "standard" is more accurate for the non-destructive category.

### `alert` — PAGER Alert Level
- **Source:** GeoJSON format (merged during collection)  
- **Values:** `green`, `yellow`, `orange`, `red`, `unassessed`  
- **Description:** The PAGER (Prompt Assessment of Global Earthquakes for Response) alert level estimating economic loss and fatalities.  
- **Why `unassessed` for missing values?**
  - `NaN` means the earthquake was **not evaluated** by the PAGER system
  - `green` means it **was evaluated** and found to be low-impact
  - These are semantically different: "not checked" ≠ "checked and safe"
  - Alternatives considered: `none`, `not_rated`, `unknown`
  - `unassessed` was chosen as the most descriptively accurate term

---

## Missing Value Strategy Summary

| Column | Strategy | Justification |
|--------|----------|---------------|
| `nst` | Median | Outlier-resistant; station counts range from 1 to 500+ |
| `gap` | Median | Outlier-resistant; gap ranges from 0° to 360° |
| `dmin` | Median | Outlier-resistant; distance varies greatly by location |
| `rms` | Median | Outlier-resistant; consistent with other numeric fills |
| `depthError` | Median | Outlier-resistant; error values can be extreme |
| `magError` | Median | Outlier-resistant; consistent with other numeric fills |
| `magNst` | Median | Outlier-resistant; mirrors nst logic |
| `alert` | `'unassessed'` | Semantic correctness (see above) |

> **Why median over mean?** The median is the middle value in a sorted dataset. Unlike the mean, it is not influenced by extreme outliers. For seismic data — where a field like `nst` might have values of 3 (remote ocean earthquake with few nearby stations) and 800 (major event near a dense station network) — the mean gets pulled toward the extremes, while the median represents the typical observation.
