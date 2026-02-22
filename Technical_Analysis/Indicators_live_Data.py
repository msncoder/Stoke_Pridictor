"""
Live Indicators & Signal Generator → MySQL
Reads historical_prices and indicators from MySQL,
calculates live signals, runs prediction algorithm,
stores results in `predictions` table.

Python 3.10+ / Windows 11. No CSV I/O.
"""
import sys
import math
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

STOCKS = ["UBL", "PSO", "HBL", "ENGRO", "OGDC"]
SIGNAL_INDICATORS = ["RSI", "Stochastic_K", "Williams_R", "CCI", "ROC", "MACD"]


def load_recent_prices(symbol, limit=200):
    return config.fetchall(
        "SELECT trade_date, close_price, high_price, low_price "
        "FROM historical_prices WHERE symbol=%s ORDER BY trade_date DESC LIMIT %s",
        (symbol, limit),
    )


def load_latest_indicators(symbol):
    """Load the most recent value for each indicator for this symbol."""
    rows = config.fetchall(
        """
        SELECT indicator_name, value, signal
        FROM indicators
        WHERE symbol=%s
          AND (symbol, indicator_name, trade_date) IN (
              SELECT symbol, indicator_name, MAX(trade_date)
              FROM indicators
              WHERE symbol=%s
              GROUP BY indicator_name
          )
        """,
        (symbol, symbol),
    )
    return {r["indicator_name"]: r for r in rows}


def count_signals(indicator_dict):
    buy = sell = 0
    for name, data in indicator_dict.items():
        if name in SIGNAL_INDICATORS:
            sig = data.get("signal", "NEUTRAL")
            if sig == "BUY":
                buy += 1
            elif sig == "SELL":
                sell += 1
    return buy, sell


def estimate_prediction(symbol, close_prices, buy_count, sell_count):
    if len(close_prices) < 5:
        return None, "NEUTRAL", 0

    current = close_prices[0]
    # Average daily movement over last 14 days
    avg_move = sum(abs(close_prices[i] - close_prices[i+1]) for i in range(min(14, len(close_prices)-1))) / min(14, len(close_prices)-1)

    total = buy_count + sell_count
    if total == 0:
        return current, "NEUTRAL", 0

    if buy_count > sell_count:
        direction = "BUY"
        confidence = buy_count / total * 100
        predicted = current + avg_move * (confidence / 100)
    elif sell_count > buy_count:
        direction = "SELL"
        confidence = sell_count / total * 100
        predicted = current - avg_move * (confidence / 100)
    else:
        direction = "NEUTRAL"
        confidence = 0
        predicted = current

    return round(predicted, 4), direction, round(confidence, 2)


def save_prediction(symbol, predicted, direction, confidence, buy_count, sell_count):
    config.execute(
        """
        INSERT INTO predictions
          (symbol, model_type, predicted_at, target_period,
           predicted_value, direction, confidence_pct, buy_signals, sell_signals)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (symbol, "SIGNAL_ALGO", datetime.now(), "next_session",
         predicted, direction, confidence, buy_count, sell_count),
    )


def process_stock(symbol):
    print(f"\n[live_indicators] ── {symbol} ──────────────────────────")

    price_rows = load_recent_prices(symbol)
    if not price_rows:
        print(f"[live_indicators] No price data in MySQL for {symbol}. Run indicators_all.py first.")
        return

    close_prices = [float(r["close_price"]) for r in price_rows]

    indicator_data = load_latest_indicators(symbol)
    if not indicator_data:
        print(f"[live_indicators] No indicators for {symbol}. Run indicators_all.py first.")
    else:
        print(f"[live_indicators] {len(indicator_data)} indicators loaded")

    buy_count, sell_count = count_signals(indicator_data)

    # MA cross-check signals
    mas = [v["value"] for k, v in indicator_data.items() if k.startswith("MA_") and v["value"]]
    if mas:
        avg_ma = sum(mas) / len(mas)
        if close_prices[0] > avg_ma:
            buy_count += 1
        elif close_prices[0] < avg_ma:
            sell_count += 1

    predicted, direction, confidence = estimate_prediction(
        symbol, close_prices, buy_count, sell_count
    )
    if predicted is None:
        return

    save_prediction(symbol, predicted, direction, confidence, buy_count, sell_count)

    print(f"[live_indicators] {symbol}: {direction} | "
          f"BUY={buy_count} SELL={sell_count} | "
          f"Current={close_prices[0]:.2f} → Predicted={predicted:.2f} "
          f"(confidence {confidence:.1f}%) → saved to MySQL")


def main():
    print(f"[live_indicators] Started at {datetime.now()}")
    for symbol in STOCKS:
        process_stock(symbol)
    print(f"\n[live_indicators] Done at {datetime.now()}. Results in MySQL `predictions`.")


if __name__ == "__main__":
    main()
