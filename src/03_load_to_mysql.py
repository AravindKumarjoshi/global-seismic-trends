# -*- coding: utf-8 -*-
"""
03_load_to_mysql.py — Store Cleaned Earthquake Data in MySQL

Approach:
    1. Connect to MySQL using pymysql cursor to create the database
       'earthquake_db' if it does not exist.
    2. Create the SQLAlchemy engine using the connection string format:
       mysql+pymysql://username:password@host:port/database_name
    3. Push the cleaned DataFrame into the 'earthquakes' table using df.to_sql()
       with chunksize=10000.
    4. Verify the inserted records using a SQL COUNT(*) check.
"""

import os
import pandas as pd
import pymysql
from sqlalchemy import create_engine
from dotenv import load_dotenv
import warnings

warnings.filterwarnings("ignore")

# 1. Read MySQL connection details from environment variables
# Why environment variables?
#   The password must not be written inside the code, because the code is pushed
#   to GitHub. load_dotenv() reads the values from the local '.env' file
#   (which is listed in .gitignore, so it is never uploaded).
load_dotenv()

db_user = os.getenv("DB_USER", "root")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST", "localhost")
db_port = int(os.getenv("DB_PORT", "3306"))
db_name = os.getenv("DB_NAME", "earthquake_db")

if db_password is None:
    raise SystemExit("DB_PASSWORD is not set. Copy .env.example to .env and add your MySQL password.")

# 2. Connect with MySQL to create the database if it does not exist
connect = pymysql.connect(
    host=db_host,
    port=db_port,
    user=db_user,
    password=db_password
)

cur = connect.cursor()
cur.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
connect.commit()
cur.close()
connect.close()
print(f"Database '{db_name}' is ready!")

# 3. Load the cleaned CSV dataset
df = pd.read_csv("data/earthquakes_cleaned.csv")
df["time"] = pd.to_datetime(df["time"])
df["updated"] = pd.to_datetime(df["updated"])
print("Loaded cleaned dataset with shape:", df.shape)

# 4. Create the SQLAlchemy engine
# Format: mysql+pymysql://username:password@host:port/database_name
connection_string = (
    f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
)
engine = create_engine(connection_string)

# 5. Push the cleaned DataFrame to MySQL table 'earthquakes'
# Why if_exists='replace'?
#   If I run this script again, 'replace' recreates the table cleanly instead
#   of appending duplicate rows.
# Why chunksize=10000?
#   Inserts the 104,464 rows in batches of 10,000 so MySQL packet limits are not exceeded.
df.to_sql(
    name="earthquakes",
    con=engine,
    if_exists="replace",
    index=False,
    chunksize=10000
)

print("Successfully loaded cleaned data into MySQL table 'earthquakes'!")

# 6. Verify row count using cursor & fetchall
connect = pymysql.connect(
    host=db_host,
    port=db_port,
    user=db_user,
    password=db_password,
    database=db_name
)
cur = connect.cursor()
cur.execute("SELECT COUNT(*) AS total_rows FROM earthquakes")
data = cur.fetchall()
print("Total rows in MySQL table 'earthquakes':", data[0][0])
cur.close()
connect.close()
