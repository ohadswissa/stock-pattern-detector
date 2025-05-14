"""
Stock Data Fetcher — Background Collector for 5-Minute Interval Samples (SQLite Version)

This module periodically fetches 5-minute interval stock price data
for the "Magnificent 7" companies over the past 3 trading days using Yahoo Finance.
It stores the data in a local SQLite database (`stock_data.db`) and ensures
that outdated samples (older than 3 days) are automatically removed.

Key Features:
- Runs in the background (via `schedule`) every 5 minutes
- Stores all stocks in a single normalized SQLite table (symbol + timestamp as primary key)
- Avoids duplicate insertions and unnecessary rewrites
- Keeps only the most recent 3 days of data per stock
- Designed to support a pattern detection API (e.g., cup-and-handle)
- Fully local and portable — no cloud services required

Note:
For simplicity, this version assumes the script runs continuously, even outside market hours.
In production, scheduling should avoid fetching during closed market times.

Usage:
    Run with: `python3 fetch_data.py &`   (on Unix/macOS)
"""

import yfinance as yf
import os
from datetime import datetime, timedelta
import schedule
import time
import sqlite3
import pytz  

# =============================
# Configuration and Constants
# =============================

# Directory to save the stock data.
DATA_DIR = "data"

# List of stock symbols to track (the "magnificent 7").
STOCK_SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN", "NVDA", "META", "TSLA"]

# Ensure that the data directory exists.
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# =============================
# Fetching Functions
# =============================

def fetch_stock_data(symbol):
    """
    Fetch 5-minute interval data for the past 3 days for a given stock symbol,
    and save it as a CSV file named {SYMBOL}.csv in the data directory.
    This will overwrite the previous file for that symbol.
    """
    stock = yf.Ticker(symbol)
    
    # Fetch historical data for the last 3 trading days with 5-minute intervals.
    data = stock.history(period="3d", interval="5m")
    save_to_sqlite(symbol, data) 
    # Save the data to CSV in the 'data/' folder
    print(f"Data for {symbol} saved to SQLite.")
    return data

def save_to_sqlite(symbol, df):
    """
    Save the latest stock data for a specific symbol into a SQLite DB.
    - Ensures only data from the last 3 days is kept (rolling window).
    - Avoids duplicate inserts by checking existing timestamps.
    """
    
    conn = sqlite3.connect("stock_data.db")
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_data (
            symbol TEXT,
            timestamp TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY (symbol, timestamp)
        )
    """)

    # Step 1: Remove old entries for this symbol (older than 3 days).
    cursor.execute("""
        DELETE FROM stock_data
        WHERE symbol = ?
        AND timestamp < datetime('now', '-3 days')
    """, (symbol,))

   
    

    # Step 2: Filter the fetched DataFrame to only include rows from the last 3 days.
    eastern = pytz.timezone("America/New_York")
    # Convert current time to NYSE timezone, then subtract 3 days to get cutoff.
    cutoff = datetime.now(eastern) - timedelta(days=3)
    df_recent = df[df.index >= cutoff]


    # Step 3: Load existing timestamps from DB to avoid duplicate inserts.
    existing = set(
        row[0] for row in cursor.execute(
            "SELECT timestamp FROM stock_data WHERE symbol = ?", (symbol,)
        )
    )

    # Step 4: Prepare only new rows (not already in DB).
    new_rows = []
    for index, row in df_recent.iterrows():
        ts = str(index)
        if ts in existing:
            continue  # Already exists — skip.
        new_rows.append((
            symbol, ts, row["Open"], row["High"], row["Low"], row["Close"], row["Volume"]
        ))

    # Step 5: Bulk insert all new, recent rows for this symbol.
    cursor.executemany("""
        INSERT INTO stock_data (symbol, timestamp, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, new_rows)

    conn.commit()
    conn.close()


def fetch_all_stocks():
    """
    Fetch the data for all stocks in the list and store them.
    """
    for symbol in STOCK_SYMBOLS:
        fetch_stock_data(symbol)
        
# Schedule the fetch function to run every 5 minutes to meet the criteria.
schedule.every(5).minutes.do(fetch_all_stocks)

# For testing — fetch every 20 seconds.
# schedule.every(20).seconds.do(fetch_all_stocks).

# Keep the script running and periodically fetch data.
if __name__ == "__main__":
    fetch_all_stocks()  # Time 0 fetch to avoid initial delay.
    while True:
        schedule.run_pending()  # Run any scheduled tasks.
        time.sleep(1)  # Sleep for a second to avoid high CPU usage.
