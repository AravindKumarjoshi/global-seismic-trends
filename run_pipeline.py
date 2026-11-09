# -*- coding: utf-8 -*-
"""
run_pipeline.py — Master ETL & Analytics Pipeline Orchestrator

=== Purpose ===
    Runs the complete batch data pipeline in sequence with a single command:
        Step 1: src/01_data_collection.py  (USGS API -> data/earthquakes_intermediate.csv)
        Step 2: src/02_data_cleaning.py    (Clean & derive -> data/earthquakes_cleaned.csv)
        Step 3: src/03_load_to_mysql.py    (Load into MySQL earthquake_db.earthquakes)
        Step 4: src/05_eda.py              (Run EDA, ttest_ind / f_oneway / chi2_contingency, save 7 charts)

=== Usage ===
    # Full pipeline (scrapes USGS API + cleans + loads MySQL + runs EDA):
    python run_pipeline.py

    # Skip API scraping if data/earthquakes_intermediate.csv already exists:
    python run_pipeline.py --skip-scrape

    # Then launch the interactive web dashboard:
    streamlit run app.py
"""

import argparse
import os
import subprocess
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("Step 1: Collect USGS Data", os.path.join(PROJECT_ROOT, "src", "01_data_collection.py")),
    ("Step 2: Clean & Preprocess Data", os.path.join(PROJECT_ROOT, "src", "02_data_cleaning.py")),
    ("Step 3: Load Cleaned Data to MySQL", os.path.join(PROJECT_ROOT, "src", "03_load_to_mysql.py")),
    ("Step 4: Run EDA & Statistical Tests", os.path.join(PROJECT_ROOT, "src", "05_eda.py")),
]


def main():
    parser = argparse.ArgumentParser(description="Run the Global Seismic Trends pipeline.")
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip Step 1 (API scraping) if data/earthquakes_intermediate.csv already exists.",
    )
    args = parser.parse_args()

    intermediate_csv = os.path.join(PROJECT_ROOT, "data", "earthquakes_intermediate.csv")

    print("=" * 70)
    print("🌍 GLOBAL SEISMIC TRENDS — MASTER PIPELINE RUNNER")
    print("=" * 70)

    pipeline_start = time.time()

    for title, script_path in STEPS:
        if args.skip_scrape and script_path.endswith("01_data_collection.py"):
            if os.path.isfile(intermediate_csv):
                print(f"\n⏭ Skipping {title} (using existing {intermediate_csv})")
                continue
            else:
                print(f"\n⚠ --skip-scrape was set, but {intermediate_csv} was not found. Running Step 1...")

        print(f"\n▶ Starting {title} ({os.path.relpath(script_path, PROJECT_ROOT)})...")
        step_start = time.time()

        result = subprocess.run([sys.executable, script_path], cwd=PROJECT_ROOT)
        elapsed = time.time() - step_start

        if result.returncode != 0:
            print(f"\n✗ {title} failed with exit code {result.returncode}. Stopping pipeline.")
            sys.exit(result.returncode)

        print(f"✓ Completed {title} in {elapsed:.1f}s")

    total_elapsed = time.time() - pipeline_start
    print("\n" + "=" * 70)
    print(f"🎉 ALL PIPELINE STEPS COMPLETED SUCCESSFULLY in {total_elapsed:.1f}s!")
    print("Next step — launch the interactive dashboard:")
    print("    streamlit run app.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
