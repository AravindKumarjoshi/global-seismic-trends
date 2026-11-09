# -*- coding: utf-8 -*-
"""
02_data_cleaning.py — Data Cleaning and Preprocessing

Steps followed:
    1. Load Data & Inspect (head, shape, info, describe, isnull().sum())
    2. Convert 'time' and 'updated' to datetime objects (pd.to_datetime)
    3. Clean Text Fields:
        - Extract 'country' from 'place' using Regex and .apply()
        - Normalize 'alert' to lowercase (.str.lower())
        - Clean string columns and strip extra commas
    4. Clean Numeric Fields & Null Value Treatment:
        - Check mean vs median: since mean > median (Right Skewed with outliers),
          fill missing numeric values using median
        - Fill missing 'alert' (categorical) based on domain knowledge as 'unassessed'
    5. Remove duplicates and drop extra columns ('depth', 'horizontalError')
    6. Feature Engineering / Add Derived Columns:
        - Year, Month, Day, Hour, Day_of_week from 'time'
        - depth_flag (shallow vs deep)
        - severity_flag (destructive vs standard)
"""

import pandas as pd
import numpy as np
import re
import warnings

warnings.filterwarnings("ignore")

# ==============================================================================
# 1. Load the dataset and inspect
# ==============================================================================
df = pd.read_csv("data/earthquakes_intermediate.csv")

print("Dataset Shape:", df.shape)
print("\nDataset Info:")
df.info()

print("\nMissing values before cleaning:")
print(df.isnull().sum())
print("\nMissing percentage (%):")
print(round(df.isnull().mean() * 100, 2))


# ==============================================================================
# 2. Convert "time" and "updated" fields to datetime objects
# ==============================================================================
# Why not use unit='ms'? Because the CSV format provides ISO date strings,
# not Unix millisecond timestamps.
df["time"] = pd.to_datetime(df["time"], utc=True).dt.tz_localize(None)
df["updated"] = pd.to_datetime(df["updated"], utc=True).dt.tz_localize(None)


# ==============================================================================
# 3. Clean Text Fields
# ==============================================================================

# 3a. Extract country from 'place' using a function + .apply()
# Why use a function with .apply() instead of a for-loop on df['place']?
#   Using .apply() runs the extraction function row-by-row and creates a new
#   'country' column while keeping 'place' intact as one of the 26 base features.
def get_country(place):
    place_str = str(place)
    if "," in place_str:
        return re.split(r",\s*", place_str)[-1].strip()
    else:
        return place_str.strip()


df["country"] = df["place"].apply(get_country)

# Clean up common state codes and "region" suffix using .replace()
df["country"] = df["country"].str.replace(" region", "", regex=False)
df["country"] = df["country"].replace({
    "AK": "Alaska",
    "CA": "California",
    "HI": "Hawaii",
    "NV": "Nevada",
    "NM": "New Mexico",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "TX": "Texas",
    "UT": "Utah",
    "WA": "Washington",
    "WY": "Wyoming",
    "ID": "Idaho",
    "MT": "Montana",
    "AZ": "Arizona",
    "CO": "Colorado",
    "KS": "Kansas",
    "MX": "Mexico",
    "nan": "Unknown"
})

# 3b. Normalize alert field to lowercase
df["alert"] = df["alert"].str.lower()

# 3c. Ensure all string fields are clean
string_cols = [
    "id", "magType", "place", "status", "type", "net",
    "sources", "types", "magSource", "locationSource", "ids"
]
for col in string_cols:
    df[col] = df[col].fillna("unknown").astype(str)

# Strip leading/trailing commas from types, ids, sources
for col in ["types", "ids", "sources"]:
    df[col] = df[col].str.strip(",")


# ==============================================================================
# 4. Clean Numeric Fields & Null Value Treatment
# ==============================================================================

# 4a. Convert numeric columns to numeric type
numeric_cols = [
    "mag", "depth_km", "nst", "dmin", "rms", "gap",
    "magError", "depthError", "magNst", "sig"
]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["tsunami"] = pd.to_numeric(df["tsunami"], errors="coerce").fillna(0).astype(int)

# 4b. Null Value Treatment for Continuous Variables:
#   - In a Normal distribution, mean == median.
#   - In a Right Skewed distribution, mean > median because high-value outliers pull the mean up.
#   - Because these columns contain outliers, I use the median rather than the mean so
#     extreme values do not distort the imputed values.

# 1) nst: Number of seismic stations that reported the earthquake
print("\nnst -> Mean:", round(df["nst"].mean(), 2), "| Median:", df["nst"].median())
df["nst"] = df["nst"].fillna(df["nst"].median())

# 2) gap: Azimuthal gap (in degrees) between stations (smaller gap = better coverage)
print("gap -> Mean:", round(df["gap"].mean(), 2), "| Median:", df["gap"].median())
df["gap"] = df["gap"].fillna(df["gap"].median())

# 3) dmin: Horizontal distance to the nearest station in degrees (~111 km per degree)
print("dmin -> Mean:", round(df["dmin"].mean(), 4), "| Median:", df["dmin"].median())
df["dmin"] = df["dmin"].fillna(df["dmin"].median())

# 4) rms: Root Mean Square travel-time residual (lower rms = better model fit)
print("rms -> Mean:", round(df["rms"].mean(), 4), "| Median:", df["rms"].median())
df["rms"] = df["rms"].fillna(df["rms"].median())

# 5) depthError: Uncertainty in depth calculation (km)
print("depthError -> Mean:", round(df["depthError"].mean(), 2), "| Median:", df["depthError"].median())
df["depthError"] = df["depthError"].fillna(df["depthError"].median())

# 6) magError: Uncertainty in magnitude calculation
print("magError -> Mean:", round(df["magError"].mean(), 4), "| Median:", df["magError"].median())
df["magError"] = df["magError"].fillna(df["magError"].median())

# 7) magNst: Number of stations used to calculate magnitude
print("magNst -> Mean:", round(df["magNst"].mean(), 2), "| Median:", df["magNst"].median())
df["magNst"] = df["magNst"].fillna(df["magNst"].median())

# 4c. Null Value Treatment for 'alert' (Categorical Variable):
#   - 'alert' is an Ordinal Categorical variable (green < yellow < orange < red) from PAGER.
#   - Why not fill with mode ('green')? Because 'green' means PAGER officially evaluated the
#     earthquake and found low impact, whereas NaN means it was NOT evaluated (mostly mag < 4.0).
#   - Filling based on domain knowledge with 'unassessed' preserves the true meaning.
print("\nAlert value counts before filling:")
print(df["alert"].value_counts())
df["alert"] = df["alert"].fillna("unassessed")


# ==============================================================================
# 5. Drop Duplicate Rows & Extra Columns
# ==============================================================================
# Remove duplicate earthquake IDs if any occurred at month boundaries
df.drop_duplicates(subset=["id"], inplace=True)
df.reset_index(drop=True, inplace=True)

# Drop 'depth' (since we have 'depth_km') and 'horizontalError' (not in the 26 features)
cols_to_drop = ["depth"]
if "horizontalError" in df.columns:
    cols_to_drop.append("horizontalError")
df.drop(cols_to_drop, axis=1, inplace=True)


# ==============================================================================
# 6. Add Derived Columns / Feature Engineering
# ==============================================================================

# 6a. Extract Year, Month, Day, Hour, Day_of_week from 'time' using the .dt accessor
df["Year"] = df["time"].dt.year
df["Month"] = df["time"].dt.month
df["Day"] = df["time"].dt.day
df["Hour"] = df["time"].dt.hour
df["Day_of_week"] = df["time"].dt.day_name()

# 6b. Shallow/deep earthquake flag based on depth_km (<= 70 km is shallow, > 70 km is deep)
df["depth_flag"] = np.where(df["depth_km"] <= 70, "shallow", "deep")

# 6c. Strong/destructive flag based on mag thresholds (>= 6.0 is destructive, < 6.0 is standard)
df["severity_flag"] = np.where(df["mag"] >= 6.0, "destructive", "standard")

print("\nMissing values after cleaning:")
print(df.isnull().sum())
print("\nFinal Cleaned Shape:", df.shape)

# Save cleaned dataset
df.to_csv("data/earthquakes_cleaned.csv", index=False)
print("Saved cleaned dataset to data/earthquakes_cleaned.csv")
