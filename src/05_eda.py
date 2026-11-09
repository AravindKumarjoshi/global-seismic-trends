# -*- coding: utf-8 -*-
"""
05_eda.py — Exploratory Data Analysis (EDA) & Statistical Hypothesis Testing

Overview of Analysis:
    1. Pandas Data Inspection:
        - head(), tail(), shape, info(), describe(), value_counts(), groupby().agg(), pivot_table()
    2. Distribution & Skewness Analysis:
        - Normal vs Right Skewed (mean > median) vs Left Skewed (mean < median)
        - sns.histplot(..., kde=True), sns.kdeplot(), plt.axvline()
    3. Outlier Detection & Log Transformation:
        - sns.boxplot() and np.log10() transformation on skewed columns
    4. Scatter Plot & Line Plot:
        - sns.scatterplot() and sns.lineplot(..., marker='o')
    5. Correlation Analysis:
        - df.corr() and sns.heatmap(..., cmap="coolwarm", fmt=".2f", annot=True)
    6. Statistical Hypothesis Testing:
        - ttest_ind        -> significant relation between two continuous variables
        - f_oneway (ANOVA) -> relation between continuous and categorical variable
        - chi2_contingency -> relation between two categorical variables (using pd.crosstab)
"""

import os
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import ttest_ind, f_oneway, chi2_contingency

warnings.filterwarnings("ignore")

# Create folder to save plots
os.makedirs("docs/figures", exist_ok=True)
sns.set_style("whitegrid")


# ==============================================================================
# 1. Load Data & Basic Pandas Inspection
# ==============================================================================
df = pd.read_csv("data/earthquakes_cleaned.csv")

print("First 5 rows:")
print(df.head())

print("\nDataset Shape (rows, columns):", df.shape)

print("\nSummary Statistics (describe):")
numeric_cols = [
    "mag", "depth_km", "sig", "nst", "gap", "rms", "dmin", "magError", "depthError"
]
print(df[numeric_cols].describe())

print("\nValue Counts for Categorical Columns:")
print("\nDepth Flag:\n", df["depth_flag"].value_counts())
print("\nSeverity Flag:\n", df["severity_flag"].value_counts())
print("\nAlert Level:\n", df["alert"].value_counts())
print("\nReview Status:\n", df["status"].value_counts())


# ==============================================================================
# 2. Distribution & Skewness Check
# ==============================================================================
#   - Normal Distribution: mean == median
#   - Right Skewed Distribution: mean > median (outliers on the right tail)
#   - Left Skewed Distribution: mean < median
print("\n--- Skewness Check (Mean vs Median) ---")
for col in ["mag", "depth_km", "nst", "gap", "dmin", "sig"]:
    mean_val = round(df[col].mean(), 2)
    median_val = round(df[col].median(), 2)
    skew_type = "Right Skewed (mean > median)" if mean_val > median_val else "Left/Normal (mean <= median)"
    print(f"{col:10s} -> Mean: {mean_val:8.2f} | Median: {median_val:8.2f} -> {skew_type}")

# Plot 1: Histogram of Magnitude (sns.histplot with kde=True)
plt.figure(figsize=(12, 4))
sns.histplot(data=df, x="mag", color="#F54927", kde=True, bins=40)
plt.axvline(x=df["mag"].mean(), color="b", label="Mean")
plt.axvline(x=df["mag"].median(), color="g", label="Median")
plt.title("Magnitude Histogram & Distribution")
plt.xlabel("======== Magnitude (mag) ========")
plt.ylabel("======== Counts ========")
plt.legend()
plt.tight_layout()
plt.savefig("docs/figures/01_magnitude_distribution.png")
plt.close()

# Plot 2: KDE Plot of Depth (sns.kdeplot + plt.axvline)
plt.figure(figsize=(12, 4))
sns.kdeplot(data=df, x="depth_km", color="r")
plt.axvline(x=70, color="b", label="70 km Shallow/Deep Threshold")
plt.title("Depth (depth_km) KDE Distribution")
plt.xlabel("======== Depth (km) ========")
plt.ylabel("======== Density ========")
plt.legend()
plt.tight_layout()
plt.savefig("docs/figures/02_depth_distribution.png")
plt.close()


# ==============================================================================
# 3. Outlier Detection & Log Transformation
# ==============================================================================
# I detect outliers using sns.boxplot() and reduce right-skewed outliers
# for visualization using log transformation (np.log10).
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
sns.boxplot(x=df["sig"])
plt.title("Boxplot of Significance (sig) - Before Log10")

plt.subplot(1, 2, 2)
sig_log10 = np.log10(df["sig"])
sns.boxplot(x=sig_log10)
plt.title("Boxplot of Significance (sig) - After np.log10")
plt.tight_layout()
plt.savefig("docs/figures/03_outlier_boxplot_log10.png")
plt.close()

# Boxplot of Magnitude across Alert Levels
plt.figure(figsize=(12, 4))
sns.boxplot(data=df, x="alert", y="mag")
plt.title("Magnitude Distribution Across PAGER Alert Levels")
plt.xlabel("======== Alert Level ========")
plt.ylabel("======== Magnitude ========")
plt.tight_layout()
plt.savefig("docs/figures/04_magnitude_by_alert.png")
plt.close()


# ==============================================================================
# 4. Groupby, Aggregation & Pivot Table
# ==============================================================================
# Country-wise total significance, average magnitude, and earthquake count
country_summary = df.groupby(["country"]).agg(
    {
        "sig": "sum",
        "mag": "mean",
        "id": "count"
    }
).reset_index()

country_summary.rename(columns={"id": "earthquake_count"}, inplace=True)
top_10_countries = country_summary.sort_values("earthquake_count", ascending=False).head(10)
print("\nTop 10 Countries by Earthquake Count (groupby + agg):")
print(top_10_countries)

# Pivot Table: Depth Flag vs Year
pivot_depth_year = pd.pivot_table(
    df,
    index=["depth_flag"],
    columns="Year",
    values="id",
    aggfunc="count"
)
print("\nPivot Table — Shallow vs Deep Earthquakes per Year:")
print(pivot_depth_year)


# ==============================================================================
# 5. Scatter Plot & Line Plot
# ==============================================================================
# Scatter Plot: Magnitude vs Significance (using a sample of 5,000 rows for clarity)
sample_df = df.head(5000)
fig, axe = plt.subplots(figsize=(12, 4))
sns.scatterplot(
    x=sample_df["mag"],
    y=sample_df["sig"],
    color="r"
)
plt.xlabel("Magnitude (mag)")
plt.ylabel("Significance (sig)")
plt.title("Magnitude vs Significance Scatter Plot")
plt.tight_layout()
plt.savefig("docs/figures/05_mag_vs_sig_scatter.png")
plt.close()

# Line Plot: Year-wise Earthquake Counts (sns.lineplot with marker='o')
yearly_counts = df.groupby(["Year"])[["id"]].count().reset_index()
fig, axe = plt.subplots(figsize=(12, 4))
sns.lineplot(
    x=yearly_counts["Year"],
    y=yearly_counts["id"],
    color="r",
    marker="o"
)
plt.xlabel("Year")
plt.ylabel("Earthquake Count")
plt.title("Year-wise Earthquake Trend")
plt.tight_layout()
plt.savefig("docs/figures/06_yearly_trend_lineplot.png")
plt.close()


# ==============================================================================
# 6. Correlation Heatmap
# ==============================================================================
# Correlation measures relationship between continuous variables (-1 to +1):
#   1. Positive correlation (0 to +1): if A increases, B also increases
#   2. Negative correlation (-1 to 0): if A increases, B decreases
#   3. No correlation (0)
corr_data = df[numeric_cols].corr()
print("\nCorrelation Matrix:")
print(round(corr_data, 2))

plt.figure(figsize=(13, 5))
sns.heatmap(corr_data, cmap="coolwarm", fmt=".2f", annot=True)
plt.title("Correlation Heatmap of Numeric Features")
plt.tight_layout()
plt.savefig("docs/figures/07_correlation_heatmap.png")
plt.close()


# ==============================================================================
# 7. Hypothesis Testing
# ==============================================================================
#   1. ttest_ind        -> significant relation between continuous variables
#   2. f_oneway (ANOVA) -> relation between continuous and categorical variable
#   3. chi2_contingency -> relation between categorical variables
#
# Rule:
#   - Null Hypothesis (H0): There is no significant difference / relationship
#   - Alternate Hypothesis (H1): There is a significant difference / relationship
#   - If p_val < 0.05 -> Reject Null Hypothesis (Accept Alternate Hypothesis)

print("\n" + "=" * 70)
print("STATISTICAL HYPOTHESIS TESTING")
print("=" * 70)

# --- Test 1: T-Test (ttest_ind) ---
# Compare Magnitude (mag) of Tsunami earthquakes vs Non-Tsunami earthquakes
tsunami_mag = df[df["tsunami"] == 1]["mag"]
no_tsunami_mag = df[df["tsunami"] == 0]["mag"]
s_ttest, p_val_ttest = ttest_ind(tsunami_mag, no_tsunami_mag)
print("\n1. T-Test (Magnitude of Tsunami vs Non-Tsunami Earthquakes):")
print("   p_val =", p_val_ttest)
print("   p_val < 0.05 ->", p_val_ttest < 0.05, "(Reject Null Hypothesis: Significant difference)")

# --- Test 2: ANOVA (f_oneway) ---
# Relation between continuous variable (mag) and categorical variable (alert level)
green = df[df["alert"] == "green"]["mag"]
yellow = df[df["alert"] == "yellow"]["mag"]
orange = df[df["alert"] == "orange"]["mag"]
red = df[df["alert"] == "red"]["mag"]
s_anova, p_val_anova = f_oneway(green, yellow, orange, red)
print("\n2. ANOVA Test (Magnitude across Alert Levels: green, yellow, orange, red):")
print("   p_val =", p_val_anova)
print("   p_val < 0.05 ->", p_val_anova < 0.05, "(Reject Null Hypothesis: Significant difference)")

# --- Test 3: Chi-Square Test (chi2_contingency) ---
# Relation between two categorical variables: alert and severity_flag
cross = pd.crosstab(df["alert"], df["severity_flag"])
print("\n3. Chi-Square Test (pd.crosstab between alert and severity_flag):")
print(cross)
chi2_stat, p_val_chi2, dof, expected = chi2_contingency(cross)
print("   p_val =", p_val_chi2)
print("   p_val < 0.05 ->", p_val_chi2 < 0.05, "(Reject Null Hypothesis: Significant relationship)")

print("\nEDA completed! All plots saved in docs/figures/")
