-- ================================================================
-- Global Seismic Trends: Data-Driven Earthquake Insights
-- Author: Aravind Kumar Joshi
-- SQL Analytical Queries
-- Database: earthquake_db
-- Table: earthquakes
-- Total Queries: 26 (Q4, Q12, Q17, Q29 skipped — see notes)
-- ================================================================

USE earthquake_db;

-- ============================================================
-- Section 1: Magnitude & Depth
-- ============================================================

-- Q1: What are the top 10 strongest earthquakes recorded in the dataset?
-- Identifies the most powerful seismic events by magnitude, revealing
-- the upper extremes of earthquake intensity captured in the data.
SELECT id, time, place, mag, depth_km
FROM earthquakes
ORDER BY mag DESC
LIMIT 10;


-- Q2: What are the top 10 deepest earthquakes recorded?
-- Deep-focus earthquakes (>300 km) occur at subduction zones and behave
-- differently from shallow events. This surfaces the deepest recorded events.
SELECT id, time, place, depth_km, mag
FROM earthquakes
ORDER BY depth_km DESC
LIMIT 10;


-- Q3: Which shallow earthquakes (depth < 50 km) had a magnitude greater than 7.5?
-- Shallow, high-magnitude earthquakes are the most destructive because
-- seismic energy dissipates less before reaching the surface.
SELECT place, mag, depth_km, time
FROM earthquakes
WHERE depth_km < 50
  AND mag > 7.5
ORDER BY mag DESC;


-- Q5: What is the average magnitude per magnitude type (magType)?
-- Different magnitude scales (ml, mb, mww, etc.) are used depending on
-- the earthquake characteristics. This shows how average magnitude varies
-- across measurement methodologies.
SELECT magType,
       ROUND(AVG(mag), 2) AS avg_mag,
       COUNT(*)            AS event_count
FROM earthquakes
GROUP BY magType
ORDER BY avg_mag DESC;


-- ============================================================
-- Section 2: Time Analysis
-- ============================================================

-- Q6: Which year recorded the highest number of earthquakes?
-- Reveals temporal peaks in seismic activity (or improved detection
-- capabilities over time, since modern networks capture more small events).
SELECT Year,
       COUNT(*) AS earthquake_count
FROM earthquakes
GROUP BY Year
ORDER BY earthquake_count DESC
LIMIT 1;


-- Q7: Which month has the highest number of earthquakes overall?
-- Tests whether there is any seasonal clustering in earthquake occurrence
-- (geophysically there should not be, but detection rates may vary).
SELECT Month,
       COUNT(*) AS earthquake_count
FROM earthquakes
GROUP BY Month
ORDER BY earthquake_count DESC
LIMIT 1;


-- Q8: Which day of the week experiences the most earthquakes?
-- Earthquakes are tectonic and should be uniformly distributed across
-- weekdays. Any deviation likely reflects reporting or cataloguing patterns.
SELECT Day_of_week,
       COUNT(*) AS earthquake_count
FROM earthquakes
GROUP BY Day_of_week
ORDER BY earthquake_count DESC;


-- Q9: What is the distribution of earthquakes across each hour of the day?
-- Similar to day-of-week analysis — checks for any diurnal pattern in
-- earthquake occurrence or detection.
SELECT Hour,
       COUNT(*) AS earthquake_count
FROM earthquakes
GROUP BY Hour
ORDER BY Hour;


-- Q10: Which seismic reporting networks (net) are the most active?
-- Identifies the top contributing networks (e.g., 'us', 'ci', 'nc'),
-- reflecting geographic monitoring density and institutional contributions.
SELECT net,
       COUNT(*) AS earthquake_count
FROM earthquakes
GROUP BY net
ORDER BY earthquake_count DESC
LIMIT 10;


-- ============================================================
-- Section 3: Impact & Alerts
-- ============================================================

-- Note: USGS earthquake data does not include direct casualty or economic loss figures.
-- The 'sig' (significance) column is used as a proxy for impact assessment.
-- sig is a composite score (0-1000+) calculated by USGS based on magnitude, felt reports,
-- and estimated impact — making it the closest available measure of human/economic impact.

-- Q11: Which 5 places (countries) have the highest cumulative impact (sig)?
-- Aggregates the significance score by country to identify regions that
-- have experienced the greatest overall seismic impact.
SELECT country,
       SUM(sig)           AS total_sig,
       ROUND(AVG(mag), 2) AS avg_mag
FROM earthquakes
GROUP BY country
ORDER BY total_sig DESC
LIMIT 5;


-- Q13: What is the average impact (sig) by alert level?
-- Compares significance across PAGER alert levels to validate that higher
-- alert levels correspond to greater impact scores.
-- Note: sig is used as a proxy — see comment above.
SELECT alert,
       ROUND(AVG(sig), 2) AS avg_sig,
       COUNT(*)           AS event_count
FROM earthquakes
GROUP BY alert
ORDER BY avg_sig DESC;


-- ============================================================
-- Section 4: Event Type & Quality Metrics
-- ============================================================

-- Q14: How many earthquakes are reviewed vs automatic?
-- Shows the proportion of events that have been manually reviewed by
-- seismologists vs those still in automatic (preliminary) status.
SELECT status,
       COUNT(*) AS event_count
FROM earthquakes
GROUP BY status;


-- Q15: What is the count of events by earthquake type?
-- The 'type' column distinguishes earthquakes from explosions, quarry blasts,
-- volcanic events, etc. This reveals the composition of the catalogue.
SELECT type,
       COUNT(*) AS event_count
FROM earthquakes
GROUP BY type
ORDER BY event_count DESC;


-- Q16: Number of earthquakes by data type (types).
-- Groups by the 'types' column to count how many earthquakes have each
-- data type combination (e.g., origin, phase-data, dyfi, shakemap).
SELECT types,
       COUNT(*) AS earthquake_count
FROM earthquakes
GROUP BY types
ORDER BY earthquake_count DESC
LIMIT 10;


-- Q18: How does station coverage (nst) relate to magnitude?
-- Events recorded by more stations (nst > 50) generally have better-
-- constrained solutions. Compares average magnitude for high vs low coverage.
SELECT CASE
           WHEN nst > 50 THEN 'High Coverage (nst > 50)'
           ELSE 'Low Coverage (nst <= 50)'
       END                AS coverage_category,
       COUNT(*)           AS event_count,
       ROUND(AVG(mag), 2) AS avg_mag
FROM earthquakes
GROUP BY coverage_category;


-- Q19: How many tsunami-triggering earthquakes occurred each year?
-- Tracks the annual count of events that generated tsunami alerts,
-- useful for understanding tsunami risk trends over time.
SELECT Year,
       COUNT(*) AS tsunami_count
FROM earthquakes
WHERE tsunami = 1
GROUP BY Year
ORDER BY Year;


-- Q20: What is the breakdown of earthquakes by alert level?
-- Summarises the PAGER alert-level distribution with average magnitude
-- and significance, quantifying the severity profile at each alert tier.
SELECT alert,
       COUNT(*)           AS event_count,
       ROUND(AVG(mag), 2) AS avg_mag,
       ROUND(AVG(sig), 2) AS avg_sig
FROM earthquakes
GROUP BY alert
ORDER BY event_count DESC;


-- ============================================================
-- Section 5: Seismic Patterns & Trends
-- ============================================================

-- Q21: Which 5 countries have the highest average magnitude in the past 5 years?
-- Focuses on recent seismicity to highlight regions currently experiencing
-- the strongest earthquakes. A minimum count threshold (>10) filters out
-- countries with too few events to be statistically meaningful.
SELECT country,
       ROUND(AVG(mag), 2) AS avg_mag,
       COUNT(*)           AS event_count
FROM earthquakes
WHERE Year >= YEAR(CURDATE()) - 5
GROUP BY country
HAVING event_count > 10
ORDER BY avg_mag DESC
LIMIT 5;


-- Q22: Which countries experienced both shallow AND deep earthquakes in the same month?
-- Identifies regions with diverse depth profiles within short time windows,
-- which may indicate complex tectonic settings (e.g., subduction zones with
-- both crustal and deep slab seismicity).
SELECT country, Year, Month,
       COUNT(DISTINCT depth_flag) AS depth_types,
       COUNT(*)                   AS event_count
FROM earthquakes
GROUP BY country, Year, Month
HAVING COUNT(DISTINCT depth_flag) = 2
ORDER BY event_count DESC;


-- Q23: What is the year-over-year growth rate in total earthquakes globally?
-- Uses a window function (LAG) to compare each year's count with the
-- previous year, computing the percentage change in recorded events.
SELECT Year,
       earthquake_count,
       prev_year_count,
       CASE
           WHEN prev_year_count IS NOT NULL AND prev_year_count > 0
               THEN ROUND(((earthquake_count - prev_year_count) / prev_year_count) * 100, 2)
           ELSE NULL
       END AS growth_rate_pct
FROM (
    SELECT Year,
           COUNT(*)                          AS earthquake_count,
           LAG(COUNT(*)) OVER (ORDER BY Year) AS prev_year_count
    FROM earthquakes
    GROUP BY Year
) yearly_counts
ORDER BY Year;


-- Q24: Which 3 regions are the most seismically active (frequency × avg magnitude)?
-- Creates a composite score that rewards both frequent and high-magnitude
-- seismicity, surfacing the most tectonically significant countries.
SELECT country,
       COUNT(*)                            AS event_count,
       ROUND(AVG(mag), 2)                  AS avg_mag,
       ROUND(COUNT(*) * AVG(mag), 2)       AS composite_score
FROM earthquakes
GROUP BY country
ORDER BY composite_score DESC
LIMIT 3;


-- ============================================================
-- Section 6: Depth, Location & Distance-Based Analysis
-- ============================================================

-- Q25: What is the average earthquake depth near the equator (±5° latitude)?
-- Equatorial regions span several tectonic settings (e.g., Indonesia,
-- East Africa, Ecuador). This filters to the equatorial belt and groups
-- by country to compare near-surface vs deep seismicity.
SELECT country,
       ROUND(AVG(depth_km), 2) AS avg_depth,
       COUNT(*)                AS event_count
FROM earthquakes
WHERE latitude BETWEEN -5 AND 5
GROUP BY country
ORDER BY avg_depth DESC;


-- Q26: Which countries have the highest ratio of shallow to deep earthquakes?
-- Uses conditional aggregation to count shallow vs deep events per country.
-- A high ratio indicates predominantly crustal (shallow) seismicity, while
-- a low ratio suggests active subduction with deep-focus events.
SELECT country,
       SUM(CASE WHEN depth_flag = 'shallow' THEN 1 ELSE 0 END) AS shallow_count,
       SUM(CASE WHEN depth_flag = 'deep'    THEN 1 ELSE 0 END) AS deep_count,
       ROUND(
           SUM(CASE WHEN depth_flag = 'shallow' THEN 1 ELSE 0 END) /
           NULLIF(SUM(CASE WHEN depth_flag = 'deep' THEN 1 ELSE 0 END), 0),
       2) AS shallow_to_deep_ratio
FROM earthquakes
GROUP BY country
HAVING deep_count > 0
ORDER BY shallow_to_deep_ratio DESC;


-- Q27: What is the average magnitude difference between tsunami vs non-tsunami events?
-- Conditional aggregation: AVG(CASE ... END) ignores NULLs, so each AVG only
-- sees the rows of its own group. Result is ONE row with both averages and
-- the difference — this directly answers "find the difference" instead of
-- leaving the subtraction to the reader.
SELECT ROUND(AVG(CASE WHEN tsunami = 1 THEN mag END), 2) AS avg_mag_tsunami,
       ROUND(AVG(CASE WHEN tsunami = 0 THEN mag END), 2) AS avg_mag_no_tsunami,
       ROUND(AVG(CASE WHEN tsunami = 1 THEN mag END)
           - AVG(CASE WHEN tsunami = 0 THEN mag END), 2) AS mag_difference,
       SUM(tsunami = 1)                                   AS tsunami_events,
       SUM(tsunami = 0)                                   AS non_tsunami_events
FROM earthquakes;


-- Q28: Using the gap and rms columns, identify events with the lowest data reliability
-- (highest average error margins).
-- High azimuthal gap (gap) and high root-mean-square residual (rms) indicate lower
-- station coverage and higher location error.
SELECT id,
       place,
       country,
       mag,
       gap,
       rms,
       ROUND((gap + rms) / 2, 2) AS avg_error_margin
FROM earthquakes
ORDER BY avg_error_margin DESC
LIMIT 10;


-- Q30: Which regions have the highest frequency of deep-focus earthquakes (depth > 300 km)?
-- Deep-focus earthquakes occur almost exclusively in subduction zones.
-- This identifies the top 10 countries hosting the most deep events.
SELECT country,
       COUNT(*)                  AS deep_event_count,
       ROUND(AVG(depth_km), 2)  AS avg_depth
FROM earthquakes
WHERE depth_km > 300
GROUP BY country
ORDER BY deep_event_count DESC
LIMIT 10;


-- ================================================================
-- SKIPPED QUERIES — Justification
-- ================================================================
-- Q4:  "Average depth per continent"
--   → Skipped because 'continent' is not part of the 26 features defined
--     in the project specification. The USGS API does not provide continent
--     data, and mapping countries to continents would require an external
--     lookup table that falls outside the scope of the defined schema.
--
-- Q12: "Total estimated economic loss per continent"
--   → Skipped for two reasons:
--     1. The USGS API does not provide any economic loss figures.
--     2. 'continent' is not one of the 26 project features (same as Q4).
--     Unlike Q11/Q13, a 'sig' proxy is not acceptable here because the
--     grouping column (continent) itself does not exist.
--
-- Q17: "Average RMS and gap per continent"
--   → Skipped because it groups by 'continent', which is not part of the
--     26 features. The same quality metrics (rms, gap) ARE analysed per
--     country in Q28, so the analytical intent is still covered.
--
-- Q29: "Find pairs of consecutive earthquakes (by time) that occurred
--       within 50 km of each other and within 1 hour"
--   → Skipped because it needs the Haversine great-circle distance between
--     consecutive rows (latitude/longitude → km). Options checked:
--       a) MySQL ST_Distance_Sphere() — needs POINT geometry columns,
--          which are not part of the defined schema.
--       b) Manual Haversine with LAG() — possible, but the trigonometric
--          expression is very long and hard to verify on this dataset.
--     Decided to leave it out and document the reason rather than submit
--     a query whose correctness cannot be confidently validated.
-- ================================================================
