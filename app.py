"""
Flask API — Pattern Detection Service (Cup-and-Handle)

This module exposes a lightweight API endpoint for checking whether a given stock
(from the Magnificent 7) currently exhibits a cup-and-handle pattern.

It works in conjunction with:
- `fetch_data.py`: updates local CSV files every 5 minutes.
- `logic.py`: contains the detection algorithm.

Usage:
POST /check_pattern.
Payload: { "symbol": "AAPL" }.
Response: { "symbol": "AAPL", "cup_and_handle_detected": true }.

Note:
This server is intended for local execution and demonstration purposes only.
"""

# ===============================
# Imports — load required tools
# ===============================

from flask import Flask, request, jsonify 
# Flask: framework to build web API.
# request: lets us read JSON input from POST requests.
# jsonify: helps us send back clean JSON responses.

from logic import detect_cup_and_handle
# Imports the relevant function from logic.py to check the pattern.

import pandas as pd
# For loading and manipulating data (CSV files).

import os

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
    data = request.get_json()  # Read the incoming JSON data.
    symbol = data.get("symbol", "").upper()  # Extract the symbol and make it uppercase.

    # Check if the symbol is valid
    if symbol not in STOCK_SYMBOLS:
        return jsonify({"error": f"Invalid stock symbol '{symbol}'"}), 400

    # Use startswith to find files that start with the stock symbol.
    files = [f for f in os.listdir(DATA_DIR) if f.startswith(symbol) and f.endswith('.csv')]
    
    # Check if the file exists.
    if not files:
        return jsonify({"error": f"Symbol '{symbol}' not found"}), 404

    try:
        # Load the stock data from the first matching file.
        file_path = os.path.join(DATA_DIR, files[0])
        df = pd.read_csv(file_path)

        # Check for the price column (make sure it exists, it could be "Close" or "price").
        if "Close" not in df.columns:
            return jsonify({"error": "Close column not found in the data"}), 400

        # Convert the "Close" column into a list of numbers.
        prices = df["Close"].tolist()

        # Run the cup and handle pattern detection.
        result = detect_cup_and_handle(prices)

        # Return the result as a JSON response.
        return jsonify({
            "symbol": symbol,
            "cup_and_handle_detected": result
        })
    
    except Exception as e:
        # If there's any error, return a 500 error with the exception message.
        return jsonify({"error": str(e)}), 500

# ===============================
# Run the Flask app locally
# ===============================

if __name__ == "__main__":
    app.run(debug=True, port=5001)  # Run the server on port 5001 for testing.