"""
Cup-and-Handle Pattern Detection Logic

This module analyzes stock price sequences to detect a technical analysis pattern
known as the "cup and handle." It defines a sequence of five turning points:
  - a: Local maximum (start of cup)
  - b: Local minimum (bottom of cup)
  - c: Local maximum (end of cup)
  - d: Local minimum (handle dip)
  - e: Local maximum (handle recovery)

Key Configurations:
- `window_size`: Controls how local maxima/minima are detected (default: 5)
- `price_thresholds`: Dict of min required % changes between turning points
- `distance_thresholds`: Dict of min required index spacing between points

The algorithm:
- Detects local minima and maxima within a sliding window
- Validates spacing and price change constraints (configurable)
- Designed for 5-minute interval data across 3 days (~234 samples)
- Includes testing blocks for both real data and random simulations

The `detect_cup_and_handle(prices)` function is the main interface for other components (e.g., Flask API).
"""

import numpy as np
import pandas as pd

# ===============================================================
# Local extrema detection — identify highs and lows in price data
# ===============================================================

def is_local_minima(i, prices, window_size=5):
    """
    Returns True if prices[i] is lower than its neighboring values within a window.
    """
    left_window = prices[max(0, i - window_size):i]
    right_window = prices[i + 1:min(i + window_size + 1, len(prices))]
    
    if prices[i] < min(left_window) and prices[i] < min(right_window):
        return True
    return False

def is_local_maxima(i, prices, window_size=5):
    """
    Returns True if prices[i] is higher than its neighboring values within a window.
    """
    left_window = prices[max(0, i - window_size):i]
    right_window = prices[i + 1:min(i + window_size + 1, len(prices))]
    
    if prices[i] > max(left_window) and prices[i] > max(right_window):
        return True
    return False

# ================================================================
# Validation helpers — check spacing and price change requirements
# ================================================================

def distance_is_valid(a, b, distance_thresholds, pair_name):
    """
    Check if the distance between two points is valid, given a distance threshold.
    pair_name specifies which pair is being checked: 'a_b', 'b_c', 'c_d', 'd_e'.
    """
    distance = abs(a - b)  # Distance between indices.
    if pair_name in distance_thresholds:
        return distance >= distance_thresholds[pair_name]  # Compare against the threshold.
    return False

def price_difference_is_valid(a, b, c, d, e, prices, price_thresholds):
    """    
    Applies constraints to validate shape of the cup and handle based on price deltas.
    """
    valid = True

    # Check price difference between a and b (b should be at least price_thresholds['a_b'] % lower than a).
    if a is not None and b is not None and prices[a] - prices[b] <= price_thresholds['a_b'] * prices[a]:
        valid = False

    # Check price difference between b and c (c should be at least price_thresholds['b_c'] % higher than b).
    if b is not None and c is not None and prices[c] - prices[b] <= price_thresholds['b_c'] * prices[b]:
        valid = False

    # Check price difference between a and c (c should be at most price_thresholds['a_c'] % higher/lower than a).
    if a is not None and c is not None and abs(prices[c] - prices[a]) >= price_thresholds['a_c'] * prices[a]:
        valid = False


    # Check price difference between c and d (d should be at least price_thresholds['c_d'] % lower than c).
    if c is not None and d is not None and prices[c] - prices[d] <= price_thresholds['c_d'] * prices[c]:
        valid = False

    # Check price difference between b and d (d should be at least price_thresholds['b_d'] % lower than b).
    if b is not None and d is not None and prices[d] - prices[b] <= price_thresholds['b_d'] * prices[b]:
        valid = False

    # Check price difference between d and e (e should be at least price_thresholds['d_e'] % higher than d).
    if d is not None and e is not None and prices[e] - prices[d] <= price_thresholds['d_e'] * prices[d]:
        valid = False

    return valid

# ==============================================================
# Helper for extracting extrema across price series
# ==============================================================

def get_min_max_indices(prices, window_size=5):
    """
    Returns indices of local minima and maxima in the price array.
    The `window_size` determines how many neighbors on each side must be
    lower (for maxima) or higher (for minima) for a point to qualify.
    A higher value filters out short-term noise, detecting stronger reversals.
    """
    maxima = []
    minima = []

    for i in range(window_size, len(prices) - window_size):  # Ensure we have enough data for the window.
        if is_local_maxima(i, prices, window_size):
            maxima.append(i)
        if is_local_minima(i, prices, window_size):
            minima.append(i)

    return maxima, minima

# ==============================================================
# Main pattern detection logic
# ==============================================================

def find_cup_and_handle_pattern(prices, window_size=5, price_thresholds=None, distance_thresholds=None):
    
    valid_patterns = []

    # Default distance thresholds if not provided.
    if distance_thresholds is None:
        distance_thresholds = {
            'a_b': 10,  # Threshold for distance between 'a' and 'b'.
            'b_c': 10,  # Threshold for distance between 'b' and 'c'.
            'c_d': 10,  # Threshold for distance between 'c' and 'd'.
            'd_e': 10   # Threshold for distance between 'd' and 'e'.
        }

    
    # Default price thresholds (tuned for ~3 trading days of 5-minute samples ≈ 234 points)
    # These values are intentionally lenient to allow pattern detection in short, noisy sequences.
    # For longer datasets or real-world applications, adjust these thresholds upward
    # to better reflect meaningful movements and reduce false positives.

    if price_thresholds is None:
        price_thresholds = {
            'a_b': 0.005,  # drop from a to b.
            'b_c': 0.005,  # rise from b to c.
            'a_c': 0.005,   # diff from a to c.
            'c_d': 0.005,  # drop from c to d.
            'b_d': 0.005,   # rise from b to d.
            'd_e': 0.005   # rise from d to e.
        }

    # Get the list of maxima and minima.
    maxima, minima = get_min_max_indices(prices, window_size)

    # Iterate over the maxima and minima lists.
    for i in range(len(maxima) - 4):  # We need at least 5 points: a, b, c, d, e.
        a = maxima[i]
        
         # Check for the corresponding 'b' (minima after 'a').
        for b in minima:
            if b > a and distance_is_valid(a, b, distance_thresholds, 'a_b'):
                # Check the price difference condition immediately.
                if not price_difference_is_valid(a, b, None, None, None, prices, price_thresholds):
                    continue  # Skip if price difference is invalid.

                # Now find the next 'c' (maxima after 'b').
                for c in maxima:
                    if c > b and distance_is_valid(b, c, distance_thresholds, 'b_c'):
                        # Check the price difference condition immediately.
                        if not price_difference_is_valid(a, b, c, None, None, prices, price_thresholds):
                            continue  # Skip if price difference is invalid.

                        # Now find the next 'd' (minima after 'c').
                        for d in minima:
                            if d > c and distance_is_valid(c, d, distance_thresholds, 'c_d'):
                                # Check the price difference condition immediately.
                                if not price_difference_is_valid(a, b, c, d, None, prices, price_thresholds):
                                    continue  # Skip if price difference is invalid.

                                # Finally, check for 'e' (maxima after 'd').
                                for e in maxima:
                                    if e > d and distance_is_valid(d, e, distance_thresholds, 'd_e'):
                                        # Now check if all price difference conditions are met.
                                        if price_difference_is_valid(a, b, c, d, e, prices, price_thresholds):
                                            valid_patterns.append((a, b, c, d, e))
    
    return valid_patterns

# ==============================================================
# Public API — used by Flask app
# ==============================================================

def detect_cup_and_handle(prices):
    """
    Returns True if at least one valid cup-and-handle pattern is found.
    """
    valid_patterns = find_cup_and_handle_pattern(prices)
    return len(valid_patterns) > 0

# ==============================================================
# Debugging / Visualization Helpers (Optional)
# ==============================================================

def display_patterns(prices, valid_patterns):
    """
    Prints detailed output for detected patterns — useful for debugging.
    """
    for pattern in valid_patterns:
        a, b, c, d, e = pattern
        print(f"Pattern found at indices: a={a}, b={b}, c={c}, d={d}, e={e}")
        print(f"Prices: a={prices[a]}, b={prices[b]}, c={prices[c]}, d={prices[d]}, e={prices[e]}")
        print("--------")

# =====================================================================
# Uncomment for real-time data testing (with real stock data)
# Read data from your CSV file (Real-time data)
# df = pd.read_csv('path_to_your_file.csv')  # Replace 'path_to_your_file.csv' with the path to your CSV file
# prices = df['Close'].values  # Assuming 'Price' is the column with stock prices

# Find cup and handle patterns in the stock price data
# valid_patterns = find_cup_and_handle_pattern(prices)

# Display the results for real-time data
# display_patterns(prices, valid_patterns)
# =====================================================================






# =====================================================================
# Uncomment for random data testing (for testing purposes)
# Generating random data for testing (e.g., 234 data points)
# np.random.seed(42)  # Set seed for reproducibility
# random_prices = np.random.randn(234) * 10 + 100  # Generate random prices with some volatility

# This mimics the DataFrame you'd have from reading a CSV
# df = pd.DataFrame({'Close': random_prices})

# Find cup and handle patterns in the randomly generated stock price data
# valid_patterns = find_cup_and_handle_pattern(df['Close'].values)

# Display the results for random data
# display_patterns(df['Close'].values, valid_patterns)
# =====================================================================






# ==============================================================
# Structure for Future Extensions (Optional)
# ==============================================================

# The following structure and modularization are intentionally designed
# for extensibility. Future enhancements might include:
# - Visualization using matplotlib or Plotly
# - Pattern scoring and ranking logic
# - Multiple pattern types (not just cup-and-handle)
# - Batch analysis for all stocks in a folder
# - Integration with alerting systems or dashboards
# - Adjustable thresholds via config or UI
# - Logging to files for monitoring

# You can add new functions below or extend the main API call
# (in app.py) to return richer output (e.g., index ranges or confidence score).