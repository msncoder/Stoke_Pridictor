#!/usr/bin/env python3
"""
Historical Data Importer
========================
Imports historical OHLCV data into PostgreSQL `historical_prices` table.

Usage:
    python db/import_historical.py                  # import from Yahoo Finance
    python db/import_historical.py --csv path.csv   # import from a local CSV file

Symbols:  UBL, PSO, HBL, ENGRO, OGDC

Dependencies:
    pip install yfinance

Yahoo Finance tickers for PSX stocks:
    UBL   → UBL.KA
    PSO   → PSO.KA
    HBL   → HBL.KA
    ENGRO → EFERT.KA
    OGDC  → OGDC.KA
"""
import sys
import argparse
import csv
from datetime import datetime
from pathlib import Path

try:
    from curl_cffi import requests as curl_requests
except ImportError:
    curl_requests = None

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

import pandas as pd

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False
    print("[import] yfinance not found. Install with: pip install yfinance")
    print("[import] Alternatively, use --csv to import from a local CSV file.")

# Map internal symbol → Yahoo Finance ticker
YAHOO_MAP = {
    "UBL":   "UBL.KA",
    "PSO":   "PSO.KA",
    "HBL":   "HBL.KA",
    "ENGRO": "EFERT.KA",
    "OGDC":  "OGDC.KA",
}

INSERT_SQL = """
    INSERT INTO historical_prices
      (symbol, trade_date, open_price, high_price, low_price, close_price, volume)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (symbol, trade_date) DO NOTHING
"""

def get_session():
    """Create a curl_cffi session, trying multiple Chrome targets for compatibility."""
    if curl_requests is None:
        return None
    # Try targets from newest to oldest; some Render builds don't support chrome110
    for target in ("chrome120", "chrome116", "chrome107", "chrome104"):
        try:
            session = curl_requests.Session(impersonate=target)
            return session
        except Exception:
            continue
    return None

def import_from_yahoo(symbol, period="2y"):
    """Download from Yahoo Finance and insert into PostgreSQL."""
    if not YF_AVAILABLE:
        print(f"[import] yfinance unavailable — skipping {symbol}")
        return 0

    ticker = YAHOO_MAP.get(symbol, f"{symbol}.KA")
    print(f"[import] Downloading {symbol} ({ticker}) from Yahoo Finance ({period})…")

    try:
        session = get_session()
        df = yf.download(ticker, period=period, auto_adjust=True, progress=False, session=session)
    except Exception as e:
        print(f"[import] Download failed for {symbol}: {e}")
        return 0

    if df.empty:
        print(f"[import] No data returned for {symbol} ({ticker}). "
              f"Check if the ticker is correct for PSX.")
        return 0

    # Flatten MultiIndex columns (yfinance ≥0.2 returns MultiIndex like ('Open','UBL.KA'))
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    rows = []
    df = df.fillna(value=0)  # Replace NaN with 0
    for date, row in df.iterrows():
        rows.append((
            symbol,
            date.date(),
            float(row["Open"])   if row["Open"]   else None,
            float(row["High"])   if row["High"]   else None,
            float(row["Low"])    if row["Low"]    else None,
            float(row["Close"])  if row["Close"]  else None,
            int(row["Volume"])   if row["Volume"] else None,
        ))

    if rows:
        config.execute(INSERT_SQL, rows, many=True)
        print(f"[import] {symbol}: {len(rows)} rows imported → PostgreSQL `historical_prices`")

    return len(rows)


def import_from_csv(csv_path, symbol):
    """
    Import from a local CSV file.
    Expected columns (case-insensitive): Date, Open, High, Low, Close, Volume
    """
    path = Path(csv_path)
    if not path.exists():
        print(f"[import] File not found: {csv_path}")
        return 0

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = [h.lower().strip() for h in reader.fieldnames]

        for line in reader:
            d = {h.lower().strip(): v for h, v in line.items()}
            try:
                trade_date = d.get("date") or d.get("trade_date")
                close      = float(d.get("close", d.get("close_price", 0)))
                open_p     = float(d.get("open",  d.get("open_price",  close)))
                high_p     = float(d.get("high",  d.get("high_price",  close)))
                low_p      = float(d.get("low",   d.get("low_price",   close)))
                volume     = int(float(d.get("volume", 0))) if d.get("volume") else None
                rows.append((symbol, trade_date, open_p, high_p, low_p, close, volume))
            except (ValueError, KeyError) as e:
                print(f"[import] Skipping row: {e}")

    if rows:
        config.execute(INSERT_SQL, rows, many=True)
        print(f"[import] {symbol}: {len(rows)} rows from {path.name} → PostgreSQL")

    return len(rows)


def run_import_all(period="2y"):
    """Programmatic entry point to import all default stocks."""
    print(f"[import] Starting bulk import for: {list(YAHOO_MAP.keys())}")
    total = 0
    for symbol in YAHOO_MAP:
        n = import_from_yahoo(symbol, period)
        total += n
    print(f"\n[import] Total: {total} rows imported across {len(YAHOO_MAP)} stocks.")
    return total


def main():
    parser = argparse.ArgumentParser(description="Import historical stock data into PostgreSQL")
    parser.add_argument("--csv",    metavar="FILE",   help="Path to a local CSV file")
    parser.add_argument("--symbol", metavar="SYMBOL", help="Stock symbol (required with --csv)")
    parser.add_argument("--period", default="2y",     help="Yahoo Finance period (default: 2y)")
    parser.add_argument("--all",  action="store_true", help="Import all default stocks from Yahoo")
    args = parser.parse_args()

    if args.csv:
        if not args.symbol:
            print("[import] --symbol is required when using --csv")
            sys.exit(1)
        import_from_csv(args.csv, args.symbol.upper())

    elif args.all or not args.csv:
        run_import_all(args.period)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
