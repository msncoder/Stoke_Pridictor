#!/usr/bin/env python3
"""
Historical Data Importer
========================
Imports historical OHLCV data into MySQL `historical_prices` table.

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

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

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
    INSERT IGNORE INTO historical_prices
      (symbol, trade_date, open_price, high_price, low_price, close_price, volume)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""


def import_from_yahoo(symbol, period="2y"):
    """Download from Yahoo Finance and insert into MySQL."""
    if not YF_AVAILABLE:
        print(f"[import] yfinance unavailable — skipping {symbol}")
        return 0

    ticker = YAHOO_MAP.get(symbol, f"{symbol}.KA")
    print(f"[import] Downloading {symbol} ({ticker}) from Yahoo Finance ({period})…")

    try:
        df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    except Exception as e:
        print(f"[import] Download failed for {symbol}: {e}")
        return 0

    if df.empty:
        print(f"[import] No data returned for {symbol} ({ticker}). "
              f"Check if the ticker is correct for PSX.")
        return 0

    rows = []
    for date, row in df.iterrows():
        rows.append((
            symbol,
            date.date(),
            float(row["Open"])   if not hasattr(row["Open"], "isna") else None,
            float(row["High"])   if not hasattr(row["High"], "isna") else None,
            float(row["Low"])    if not hasattr(row["Low"],  "isna") else None,
            float(row["Close"]),
            int(row["Volume"])   if row["Volume"] else None,
        ))

    if rows:
        config.execute(INSERT_SQL, rows, many=True)
        print(f"[import] {symbol}: {len(rows)} rows imported → MySQL `historical_prices`")

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
        print(f"[import] {symbol}: {len(rows)} rows from {path.name} → MySQL")

    return len(rows)


def main():
    parser = argparse.ArgumentParser(description="Import historical stock data into MySQL")
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
        total = 0
        for symbol in YAHOO_MAP:
            n = import_from_yahoo(symbol, args.period)
            total += n
        print(f"\n[import] Total: {total} rows imported across {len(YAHOO_MAP)} stocks.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
