"""
Stock Data Fetcher — Background Collector for 5-Minute Interval Samples

This module periodically fetches stock price data (5-minute resolution) 
for the "Magnificent 7" companies over the past 3 days using Yahoo Finance.
It stores the data locally in CSV format and ensures outdated files are removed.

Key Features:
- Automatically runs in the background (using `schedule`) every 5 minutes
- Saves each stock's data to a dedicated CSV file (overwrites daily)
- Designed to support a POC system for pattern detection (e.g., cup-and-handle)
- Compatible with local-only execution — no cloud dependencies
- Can be tested with higher frequency by adjusting the schedule (e.g., every 20 sec)

Note:
In a real production system, we would avoid fetching data outside of market trading hours 
(e.g., nights or weekends). However, for this POC we assume the script runs continuously 
and simply overwrites the most recent file if no new data is available.

You can launch this script via:
    `python3 fetch_data.py &`   (on Unix/macOS) to keep it running in the background.
"""

import yfinance as yf
import os
from datetime import datetime, timedelta
import schedule
import time

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
    
    # Fetch historical data for the last 3 trading days with 5-minute intervals
    data = stock.history(period="3d", interval="5m")
    
    # Add a timestamp to the filename to manage data over time
    timestamp = datetime.now().strftime("%Y-%m-%d")
    # Overwrite the file with the same symbol
    file_path = f"{DATA_DIR}/{symbol}.csv"
    # Save the data to CSV in the 'data/' folder
    data.to_csv(file_path)
    
    print(f"Data for {symbol} saved to {file_path}")
    return data

def fetch_all_stocks():
    """
    Fetch the data for all stocks in the list and store them.
    """
    for symbol in STOCK_SYMBOLS:
        fetch_stock_data(symbol)
        
# Schedule the fetch function to run every 5 minutes to meet the criteria.
schedule.every(5).minutes.do(fetch_all_stocks)

# For testing — fetch every 20 seconds
# schedule.every(20).seconds.do(fetch_all_stocks)

# Keep the script running and periodically fetch data.
if __name__ == "__main__":
    fetch_all_stocks()  # Time 0 fetch to avoid initial delay
    while True:
        schedule.run_pending()  # Run any scheduled tasks
        time.sleep(1)  # Sleep for a second to avoid high CPU usage
