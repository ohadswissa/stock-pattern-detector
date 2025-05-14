# stock-pattern-detector

**Proof-of-Concept platform for detecting cup-and-handle stock patterns using 3-day rolling SQLite storage and a lightweight Flask API.**

---

## 🔍 Project Overview

This project implements a local stock analysis engine that:
- Collects stock prices every **5 minutes** for the **Magnificent 7** stocks (AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA)
- Maintains only the **last 3 trading days** of data (rolling window)
- Detects the **cup-and-handle** pattern using a configurable, generic algorithm
- Exposes a **Flask API** for querying pattern presence per stock

The project was developed as a **POC** and can be extended to support additional pattern types, thresholds, or a broader backend.

---

## 🧠 Detection Concept (ABCDE Logic)

The pattern detection is based on identifying **five turning points** in the stock's price series:

- `a`: Local maximum (start of cup)
- `b`: Local minimum (bottom of cup)
- `c`: Local maximum (end of cup)
- `d`: Local minimum (handle dip)
- `e`: Local maximum (handle recovery)

We validate each candidate pattern using:
- **Window size**: Controls how far we look to define local extrema.
- **Distance thresholds**: Minimum spacing between turning points.
- **Price thresholds**: Minimum percentage differences between turning points.

All thresholds are adjustable, making this logic reusable for other pattern detection tasks.

---



## 🛠️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/ohadswissa/stock-pattern-detector.git
cd stock-pattern-detector
```
### 2. Create a virtual environment
```
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```
### 3. Install dependencies
```
pip install -r requirements.txt
```
## 🚀 How to Run the System

### Step 1: Start the Background Fetcher
Fetches stock data every 5 minutes and stores only the last 3 days.
```
python3 fetch_data.py &
```
(The & runs it in the background)

### Step 2: Start the Flask API
In the same VS Code terminal, run:
```
python3 app.py
```
This will start a local server at: http://127.0.0.1:5001

## 📡 Using the API
## Step 3: Query the API (in a new terminal tab)
You can use curl or Postman to test it.
Open a second terminal (outside VS Code or another tab in it), and run:

Example using curl:
```
curl -X POST http://127.0.0.1:5001/check_pattern \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'
```
Sample JSON response:
```
{
  "symbol": "AAPL",
  "cup_and_handle_detected": true
}
```
## ⏹️ Stopping the Fetcher and API
If you want to stop either process:

Use Ctrl+C once to stop the Flask API.
Then run fg and Ctrl+C again to stop the background fetcher.

## 🔧 Customization

In logic.py, you can tweak:

window_size: Default is 5, used to define local extrema.
distance_thresholds: Min distance (in samples) between turning points.
price_thresholds: Min % price change between pattern segments.
These are set in the function find_cup_and_handle_pattern(...) and can be passed dynamically or edited statically.

Note: The default parameters are tuned for ~222 samples (5-minute intervals over 3 trading days).

## 🧼 Notes

venv/, __pycache__/, and cached data are excluded via .gitignore.
The system assumes it runs during trading hours. No fetching occurs if the market is closed.
This POC runs fully locally and has no external dependencies beyond yfinance and Flask.

## 📈 Future Enhancements (Optional)

Support multiple pattern types.
Add visualizations using Plotly or Matplotlib.
Scoring for pattern confidence.
UI for dynamic threshold configuration.
Database storage or cloud integration (if needed).
