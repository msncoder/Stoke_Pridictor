"""
Technical Indicators Calculator → MySQL `indicators` table
Reads historical OHLCV from `historical_prices`, calculates all indicators,
writes results to `indicators` table.

Python 3.10+ / Windows 11. No CSV I/O.
"""
import sys
import math
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

STOCKS = ["UBL", "HBL", "OGDCL", "ENGRO", "PSO"]


# ── Data loading ──────────────────────────────────────────────────

def load_stock_data(symbol):
    rows = config.fetchall(
        "SELECT trade_date, open_price, high_price, low_price, close_price "
        "FROM historical_prices WHERE symbol=%s ORDER BY trade_date ASC",
        (symbol,),
    )
    if not rows:
        print(f"[indicators_all] No data in MySQL for {symbol}. "
              f"Import historical data first using db/import_historical.py")
    return rows


# ── Batch save helper ─────────────────────────────────────────────

def save_indicators(rows_to_insert):
    """Bulk insert (symbol, trade_date, indicator_name, value, signal, period) tuples."""
    if not rows_to_insert:
        return
    config.execute(
        """
        INSERT INTO indicators (symbol, trade_date, indicator_name, value, signal, period, calculated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE value=VALUES(value), signal=VALUES(signal), calculated_at=VALUES(calculated_at)
        """,
        rows_to_insert,
        many=True,
    )


# ── Indicator maths ────────────────────────────────────────────────

def moving_average(close, dates, symbol, period=14):
    now = datetime.now()
    rows = []
    for i in range(len(close)):
        if i < period - 1:
            continue
        avg = sum(close[i - period + 1: i + 1]) / period
        effect = "BUY" if close[i] > avg else "SELL" if close[i] < avg else "NEUTRAL"
        rows.append((symbol, dates[i], f"MA_{period}", round(avg, 6), effect, period, now))
    save_indicators(rows)
    print(f"[indicators_all] {symbol} MA({period}) → {len(rows)} rows saved")


def exponential_moving_average(close, dates, symbol, period=14):
    multiplier = 2.0 / (period + 1)
    now = datetime.now()
    rows = []
    ema = sum(close[:period]) / period
    for i in range(period - 1, len(close)):
        if i > period - 1:
            ema = (close[i] - ema) * multiplier + ema
        effect = "BUY" if close[i] > ema else "SELL" if close[i] < ema else "NEUTRAL"
        rows.append((symbol, dates[i], f"EMA_{period}", round(ema, 6), effect, period, now))
    save_indicators(rows)
    print(f"[indicators_all] {symbol} EMA({period}) → {len(rows)} rows saved")


def rsi(close, dates, symbol, period=14):
    gains = [max(close[i] - close[i-1], 0) for i in range(1, len(close))]
    losses = [max(close[i-1] - close[i], 0) for i in range(1, len(close))]
    now = datetime.now()
    rows = []
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(close)):
        idx = i - 1
        if idx > period - 1:
            avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
            avg_loss = (avg_loss * (period - 1) + losses[idx]) / period
        rs = avg_gain / avg_loss if avg_loss else float("inf")
        rsi_val = 100 - (100 / (1 + rs)) if avg_loss else 100
        effect = "BUY" if rsi_val < 30 else "SELL" if rsi_val > 70 else "NEUTRAL"
        rows.append((symbol, dates[i], "RSI", round(rsi_val, 6), effect, period, now))
    save_indicators(rows)
    print(f"[indicators_all] {symbol} RSI → {len(rows)} rows saved")


def stochastic(close, high, low, dates, symbol, period=14):
    now = datetime.now()
    rows = []
    for i in range(period - 1, len(close)):
        highest = max(high[i - period + 1: i + 1])
        lowest  = min(low[i - period + 1: i + 1])
        k = ((close[i] - lowest) / (highest - lowest) * 100) if highest != lowest else 50
        effect = "BUY" if k < 20 else "SELL" if k > 80 else "NEUTRAL"
        rows.append((symbol, dates[i], "Stochastic_K", round(k, 6), effect, period, now))
    save_indicators(rows)
    print(f"[indicators_all] {symbol} Stochastic → {len(rows)} rows saved")


def williams_r(close, high, low, dates, symbol, period=14):
    now = datetime.now()
    rows = []
    for i in range(period - 1, len(close)):
        highest = max(high[i - period + 1: i + 1])
        lowest  = min(low[i - period + 1: i + 1])
        wr = ((highest - close[i]) / (highest - lowest) * -100) if highest != lowest else -50
        effect = "BUY" if wr < -80 else "SELL" if wr > -20 else "NEUTRAL"
        rows.append((symbol, dates[i], "Williams_R", round(wr, 6), effect, period, now))
    save_indicators(rows)
    print(f"[indicators_all] {symbol} Williams %R → {len(rows)} rows saved")


def cci(close, high, low, dates, symbol, period=14):
    tp = [(h + l + c) / 3 for h, l, c in zip(high, low, close)]
    now = datetime.now()
    rows = []
    for i in range(period - 1, len(tp)):
        window = tp[i - period + 1: i + 1]
        sma = sum(window) / len(window)
        mean_dev = sum(abs(v - sma) for v in window) / len(window)
        val = (tp[i] - sma) / (0.015 * mean_dev) if mean_dev else 0
        effect = "BUY" if val < -100 else "SELL" if val > 100 else "NEUTRAL"
        rows.append((symbol, dates[i], "CCI", round(val, 6), effect, period, now))
    save_indicators(rows)
    print(f"[indicators_all] {symbol} CCI → {len(rows)} rows saved")


def atr(close, high, low, dates, symbol, period=14):
    tr = [high[0] - low[0]]
    for i in range(1, len(close)):
        tr.append(max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1])))
    now = datetime.now()
    rows = []
    atr_val = sum(tr[:period]) / period
    for i in range(period - 1, len(close)):
        if i > period - 1:
            atr_val = (atr_val * (period - 1) + tr[i]) / period
        rows.append((symbol, dates[i], "ATR", round(atr_val, 6), "NEUTRAL", period, now))
    save_indicators(rows)
    print(f"[indicators_all] {symbol} ATR → {len(rows)} rows saved")


def roc(close, dates, symbol, period=14):
    now = datetime.now()
    rows = []
    for i in range(period, len(close)):
        val = ((close[i] - close[i - period]) / close[i - period] * 100) if close[i - period] else 0
        effect = "BUY" if val > 0 else "SELL" if val < 0 else "NEUTRAL"
        rows.append((symbol, dates[i], "ROC", round(val, 6), effect, period, now))
    save_indicators(rows)
    print(f"[indicators_all] {symbol} ROC → {len(rows)} rows saved")


def bollinger_bands(close, dates, symbol, period=20):
    now = datetime.now()
    rows = []
    for i in range(period - 1, len(close)):
        window = close[i - period + 1: i + 1]
        sma = sum(window) / period
        std = math.sqrt(sum((x - sma) ** 2 for x in window) / period)
        upper = sma + 2 * std
        lower = sma - 2 * std
        effect = "BUY" if close[i] < lower else "SELL" if close[i] > upper else "NEUTRAL"
        rows.append((symbol, dates[i], "BB_Upper",  round(upper, 6), effect, period, now))
        rows.append((symbol, dates[i], "BB_Middle", round(sma, 6),   effect, period, now))
        rows.append((symbol, dates[i], "BB_Lower",  round(lower, 6), effect, period, now))
    save_indicators(rows)
    print(f"[indicators_all] {symbol} Bollinger Bands → {len(rows)//3} rows saved")


def ultimate_oscillator(close, high, low, dates, symbol):
    bp, tr = [], []
    for i in range(len(close)):
        if i == 0:
            bp.append(close[i] - low[i])
            tr.append(high[i] - low[i])
        else:
            p = close[i - 1]
            bp.append(close[i] - min(low[i], p))
            tr.append(max(high[i], p) - min(low[i], p))
    now = datetime.now()
    rows = []
    for i in range(27, len(close)):
        a7  = sum(bp[i-6:i+1]) / sum(tr[i-6:i+1])  if sum(tr[i-6:i+1]) else 0
        a14 = sum(bp[i-13:i+1]) / sum(tr[i-13:i+1]) if sum(tr[i-13:i+1]) else 0
        a28 = sum(bp[i-27:i+1]) / sum(tr[i-27:i+1]) if sum(tr[i-27:i+1]) else 0
        uo  = ((4 * a7) + (2 * a14) + a28) / 7 * 100
        effect = "BUY" if uo < 30 else "SELL" if uo > 70 else "NEUTRAL"
        rows.append((symbol, dates[i], "UO", round(uo, 6), effect, None, now))
    save_indicators(rows)
    print(f"[indicators_all] {symbol} UO → {len(rows)} rows saved")


def process_stock(symbol):
    print(f"\n{'='*55}\n[indicators_all] Processing {symbol}\n{'='*55}")
    rows = load_stock_data(symbol)
    if not rows:
        return

    dates = [r["trade_date"] for r in rows]
    close = [float(r["close_price"]) for r in rows]
    high  = [float(r["high_price"])  for r in rows]
    low   = [float(r["low_price"])   for r in rows]

    for period in (5, 10, 14, 20, 30):
        moving_average(close, dates, symbol, period)
        exponential_moving_average(close, dates, symbol, period)

    rsi(close, dates, symbol)
    stochastic(close, high, low, dates, symbol)
    williams_r(close, high, low, dates, symbol)
    cci(close, high, low, dates, symbol)
    atr(close, high, low, dates, symbol)
    roc(close, dates, symbol)
    bollinger_bands(close, dates, symbol)
    ultimate_oscillator(close, high, low, dates, symbol)
    print(f"[indicators_all] {symbol} complete!")


def main():
    for symbol in STOCKS:
        process_stock(symbol)
    print("\n[indicators_all] All stocks processed → MySQL `indicators`")


if __name__ == "__main__":
    main()
