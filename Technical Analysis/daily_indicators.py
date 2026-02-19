"""
Daily Technical Indicators → MySQL `indicators` table
Reads historical_prices from MySQL, calculates MACD + daily indicators,
writes to `indicators` table.

Python 3.10+ / Windows 11. No CSV I/O.
"""
import sys
import math
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

STOCKS = ["UBL", "PSO", "HBL", "ENGRO", "OGDC"]


def load_stock(symbol):
    rows = config.fetchall(
        "SELECT trade_date, close_price, high_price, low_price "
        "FROM historical_prices WHERE symbol=%s ORDER BY trade_date ASC",
        (symbol,),
    )
    if not rows:
        print(f"[daily_indicators] No data for {symbol} in MySQL.")
    return rows


def save_indicators(rows):
    if not rows:
        return
    config.execute(
        """
        INSERT INTO indicators (symbol, trade_date, indicator_name, value, signal, period, calculated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE value=VALUES(value), signal=VALUES(signal), calculated_at=VALUES(calculated_at)
        """,
        rows,
        many=True,
    )


# ── Indicator implementations ─────────────────────────────────────

def calc_ma(close, dates, symbol, period):
    now = datetime.now()
    rows = []
    for i in range(period - 1, len(close)):
        avg = sum(close[i - period + 1: i + 1]) / period
        effect = "BUY" if close[i] > avg else "SELL" if close[i] < avg else "NEUTRAL"
        rows.append((symbol, dates[i], f"MA_{period}", round(avg, 6), effect, period, now))
    save_indicators(rows)


def calc_ema(close, dates, symbol, period):
    mult = 2.0 / (period + 1)
    ema = sum(close[:period]) / period
    now = datetime.now()
    rows = []
    for i in range(period - 1, len(close)):
        if i > period - 1:
            ema = (close[i] - ema) * mult + ema
        effect = "BUY" if close[i] > ema else "SELL" if close[i] < ema else "NEUTRAL"
        rows.append((symbol, dates[i], f"EMA_{period}", round(ema, 6), effect, period, now))
    save_indicators(rows)


def calc_rsi(close, dates, symbol, period=14):
    gains  = [max(close[i] - close[i-1], 0) for i in range(1, len(close))]
    losses = [max(close[i-1] - close[i], 0) for i in range(1, len(close))]
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    now = datetime.now()
    rows = []
    for i in range(period, len(close)):
        idx = i - 1
        if idx > period - 1:
            avg_g = (avg_g * (period - 1) + gains[idx]) / period
            avg_l = (avg_l * (period - 1) + losses[idx]) / period
        rsi_val = 100 - (100 / (1 + avg_g / avg_l)) if avg_l else 100
        effect = "BUY" if rsi_val < 30 else "SELL" if rsi_val > 70 else "NEUTRAL"
        rows.append((symbol, dates[i], "RSI", round(rsi_val, 6), effect, period, now))
    save_indicators(rows)


def calc_stochastic(close, high, low, dates, symbol, period=14):
    now = datetime.now()
    rows = []
    for i in range(period - 1, len(close)):
        highest = max(high[i - period + 1: i + 1])
        lowest  = min(low[i - period + 1: i + 1])
        k = ((close[i] - lowest) / (highest - lowest) * 100) if highest != lowest else 50
        effect = "BUY" if k < 20 else "SELL" if k > 80 else "NEUTRAL"
        rows.append((symbol, dates[i], "Stochastic_K", round(k, 6), effect, period, now))
    save_indicators(rows)


def calc_macd(close, dates, symbol, fast=12, slow=26, signal_period=9):
    """Calculate MACD line, signal line, and histogram."""
    def ema_series(data, p):
        mult = 2.0 / (p + 1)
        first = sum(data[:p]) / p
        result = [None] * (p - 1) + [first]
        e = first
        for i in range(p, len(data)):
            e = (data[i] - e) * mult + e
            result.append(e)
        return result

    ema_fast = ema_series(close, fast)
    ema_slow = ema_series(close, slow)

    macd_line = []
    for f, s in zip(ema_fast, ema_slow):
        macd_line.append(f - s if (f is not None and s is not None) else None)

    valid_macd = [(i, v) for i, v in enumerate(macd_line) if v is not None]
    now = datetime.now()
    rows = []

    # MACD line
    for i, v in valid_macd:
        effect = "BUY" if v > 0 else "SELL" if v < 0 else "NEUTRAL"
        rows.append((symbol, dates[i], "MACD", round(v, 6), effect, None, now))

    # Signal line (EMA of MACD values)
    macd_vals = [v for _, v in valid_macd]
    macd_dates_idx = [i for i, _ in valid_macd]
    if len(macd_vals) >= signal_period:
        mult = 2.0 / (signal_period + 1)
        sig_ema = sum(macd_vals[:signal_period]) / signal_period
        for j in range(signal_period - 1, len(macd_vals)):
            if j > signal_period - 1:
                sig_ema = (macd_vals[j] - sig_ema) * mult + sig_ema
            i = macd_dates_idx[j]
            hist = macd_vals[j] - sig_ema
            effect = "BUY" if hist > 0 else "SELL" if hist < 0 else "NEUTRAL"
            rows.append((symbol, dates[i], "MACD_Signal",    round(sig_ema, 6), effect, signal_period, now))
            rows.append((symbol, dates[i], "MACD_Histogram", round(hist, 6),    effect, signal_period, now))

    save_indicators(rows)


def calc_williams(close, high, low, dates, symbol, period=14):
    now = datetime.now()
    rows = []
    for i in range(period - 1, len(close)):
        highest = max(high[i - period + 1: i + 1])
        lowest  = min(low[i - period + 1: i + 1])
        wr = ((highest - close[i]) / (highest - lowest) * -100) if highest != lowest else -50
        effect = "BUY" if wr < -80 else "SELL" if wr > -20 else "NEUTRAL"
        rows.append((symbol, dates[i], "Williams_R", round(wr, 6), effect, period, now))
    save_indicators(rows)


def calc_cci(close, high, low, dates, symbol, period=14):
    tp = [(h + l + c) / 3 for h, l, c in zip(high, low, close)]
    now = datetime.now()
    rows = []
    for i in range(period - 1, len(tp)):
        w = tp[i - period + 1: i + 1]
        sma = sum(w) / period
        md  = sum(abs(v - sma) for v in w) / period
        val = (tp[i] - sma) / (0.015 * md) if md else 0
        effect = "BUY" if val < -100 else "SELL" if val > 100 else "NEUTRAL"
        rows.append((symbol, dates[i], "CCI", round(val, 6), effect, period, now))
    save_indicators(rows)


def calc_roc(close, dates, symbol, period=14):
    now = datetime.now()
    rows = []
    for i in range(period, len(close)):
        val = ((close[i] - close[i - period]) / close[i - period] * 100) if close[i - period] else 0
        effect = "BUY" if val > 0 else "SELL" if val < 0 else "NEUTRAL"
        rows.append((symbol, dates[i], "ROC", round(val, 6), effect, period, now))
    save_indicators(rows)


def process_stock(symbol):
    print(f"\n{'='*55}")
    print(f"[daily_indicators] {symbol}")
    print(f"{'='*55}")

    rows = load_stock(symbol)
    if not rows:
        return

    dates = [r["trade_date"] for r in rows]
    close = [float(r["close_price"]) for r in rows]
    high  = [float(r["high_price"])  for r in rows]
    low   = [float(r["low_price"])   for r in rows]

    for p in (5, 10, 14, 20, 30):
        calc_ma(close, dates, symbol, p)
        calc_ema(close, dates, symbol, p)

    calc_rsi(close, dates, symbol)
    calc_stochastic(close, high, low, dates, symbol)
    calc_macd(close, dates, symbol)
    calc_williams(close, high, low, dates, symbol)
    calc_cci(close, high, low, dates, symbol)
    calc_roc(close, dates, symbol)
    print(f"[daily_indicators] {symbol} complete!")


def main():
    for symbol in STOCKS:
        process_stock(symbol)
    print("\n[daily_indicators] All stocks → MySQL `indicators`")


if __name__ == "__main__":
    main()
