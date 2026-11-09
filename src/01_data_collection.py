# -*- coding: utf-8 -*-
"""
01_data_collection.py — USGS Earthquake Data Collection

Data Source:
    - USGS API: https://earthquake.usgs.gov/fdsnws/event/1/query
    - Loop through month by month and collect the data for the last 5 years.
    - Why month by month? The USGS API has a limit of 20,000 events per request.
      Collecting month by month avoids hitting that limit.
    - Why two formats (CSV and GeoJSON)?
        1. CSV has the main 22 columns (id, time, latitude, longitude, depth, mag, etc.)
        2. GeoJSON has the remaining columns required for the analysis:
           tsunami, sig, types, ids, sources, alert
    - I merge both on 'id' using pd.merge and save the result to
      data/earthquakes_intermediate.csv
"""

import pandas as pd
import datetime as dt
import requests
from requests.exceptions import HTTPError
import io
import os
import warnings

warnings.filterwarnings("ignore")

# API URL and output file path
url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
os.makedirs("data", exist_ok=True)
file_name = "data/earthquakes_intermediate.csv"

# Remove old intermediate file if it already exists so re-running does not duplicate rows
if os.path.isfile(file_name):
    os.remove(file_name)

# Get last 5 full calendar years dynamically using datetime
today = dt.date.today()
start_year = today.year - 5
end_year = today.year - 1

print(f"Collecting USGS data from {start_year} to {end_year}...")

for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"

        data_json = None
        data_csv = None

        for col in ["geojson", "csv"]:
            params = {
                "format": col,
                "starttime": start_date,
                "endtime": end_date,
                "minmagnitude": "3.0"
            }
            try:
                response = requests.get(url, params=params, timeout=60)
                response.raise_for_status()
            except HTTPError as http_err:
                print(f"HTTP Error occurred: {http_err}")
            except Exception as err:
                print(f"An error occurred: {err}")
            else:
                print(f"Request for {col} ({start_date} to {end_date}) was successful!")
                if col == "geojson":
                    data_json = response.json()
                else:
                    data_csv = response

        # Process and merge if both CSV and GeoJSON were fetched
        if data_csv is not None and data_json is not None:
            df_csv = pd.read_csv(io.BytesIO(data_csv.content))
            df_json = pd.json_normalize(data_json, record_path=["features"])

            if len(df_csv) == 0 or len(df_json) == 0:
                continue

            # Clean column names in JSON ("properties.tsunami" -> "tsunami")
            df_json.columns = df_json.columns.str.replace("properties.", "", regex=False)

            # Merge extra columns from GeoJSON into CSV using pd.merge on 'id'
            # Why pd.merge on 'id' instead of direct assignment?
            # It guarantees each earthquake's tsunami, sig, and alert values match its exact ID.
            extra_cols = df_json[["id", "tsunami", "sig", "types", "ids", "sources", "alert"]]
            df_csv = pd.merge(df_csv, extra_cols, on="id", how="left")

            # Add depth_km column from depth
            df_csv["depth_km"] = df_csv["depth"]

            file_exists = os.path.isfile(file_name)
            df_csv.to_csv(
                file_name,
                mode="a",
                header=not file_exists,
                index=False
            )

print(f"Data collection completed! Saved to {file_name}")
