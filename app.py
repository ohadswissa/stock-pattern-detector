"""
Flask API — Pattern Detection Service (Cup-and-Handle)

This module exposes a lightweight API endpoint for checking whether a given stock
(from the Magnificent 7) currently exhibits a cup-and-handle pattern.

It works in conjunction with:
- `fetch_data.py`: fetches and stores data into a SQLite DB
- `logic.py`: contains the detection algorithm

Usage:
POST /check_pattern
Payload: { "symbol": "AAPL" }
Response: { "symbol": "AAPL", "cup_and_handle_detected": true }

Note:
This server is intended for local execution and demonstration purposes only.
"""


# ===============================
# Imports — load required tools
# ===============================

from flask import Flask, request, jsonify
import json
# Flask: framework to build web API.
# request: lets us read JSON input from POST requests.
# jsonify: helps us send back clean JSON responses.
from logic import detect_cup_and_handle
# Imports the relevant function from logic.py to check the pattern.
import pandas as pd
import sqlite3
from flask import make_response


def load_from_sqlite(symbol):
    """
    Load latest stock data for a given symbol from SQLite DB,
    ordered by timestamp ascending.
    Returns a pandas DataFrame.
    """
    conn = sqlite3.connect("stock_data.db")
    df = pd.read_sql_query(
        "SELECT * FROM stock_data WHERE symbol = ? ORDER BY timestamp ASC",
        conn,
        params=(symbol,)
    )
    conn.close()
    return df

# ===================================
# Create the Flask app (web server)
# ===================================

# Initializes my web app so it can handle HTTP requests.
app = Flask(__name__)

DATA_DIR = "data"  # Folder with CSV files.

# List of stock symbols to track (the "magnificent 7")
STOCK_SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN", "NVDA", "META", "TSLA"]

# ==============================================================
# Define the main endpoint (API route) that listens to requests
# ==============================================================

@app.route("/check_pattern", methods=["POST"])

def check_pattern():
    """
    Main API endpoint: Accepts a JSON payload with a stock symbol
    and returns whether the cup-and-handle pattern is detected.

    Expected request:
        { "symbol": "AAPL" }

    Response:
        {
            "symbol": "AAPL",
            "cup_and_handle_detected": true
        }

    Returns:
        - 200 OK on success
        - 400 Bad Request on missing/invalid input
        - 404 Not Found if no CSV exists
        - 500 Internal Server Error for unexpected issues
    """
    # Read and parse the incoming POST request body as JSON.
    data = request.get_json()
    symbol = data.get("symbol", "").upper()

    # Validate that the symbol is one of the tracked stocks.
    if symbol not in STOCK_SYMBOLS:
        return jsonify({"error": f"Invalid stock symbol '{symbol}'"}), 400
   
    # Attempt to load stock price data from the database.
    try:
        df = load_from_sqlite(symbol)
        if df.empty:
            return jsonify({"error": f"No data found in DB for symbol '{symbol}'"}), 404
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    # Verify that 'close' price data exists
    if "close" not in df.columns:
        return jsonify({"error": "close column not found in the data"}), 400
    
    # Extract the close prices into a Python list for analysis.
    prices = df["close"].tolist()
   
    # Run the pattern detection algorithm from logic.py.
    result = detect_cup_and_handle(prices)

    response_data = {
    "symbol": symbol,
    "cup_and_handle_detected": result
}

    return make_response(
        json.dumps(response_data, indent=2),
        200,
        {"Content-Type": "application/json"}
)
# ===============================
# Run the Flask app locally
# ===============================

if __name__ == "__main__":
    app.run(debug=True, port=5001)  # Run the server on port 5001 for testing.