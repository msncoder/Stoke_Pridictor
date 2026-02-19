"""
Hadoop HDFS Uploader
Reads data from MySQL and uploads to HDFS as Parquet/CSV.
Hadoop/pydoop is OPTIONAL — exits gracefully if unavailable.

Python 3.10+ / Windows 11.
"""
import sys
import io
import csv
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config


def mysql_to_csv_bytes(table, symbol=None):
    """Serialize a MySQL table to CSV bytes for HDFS upload."""
    if symbol:
        rows = config.fetchall(
            f"SELECT * FROM {table} WHERE symbol=%s ORDER BY id ASC", (symbol,)
        )
    else:
        rows = config.fetchall(f"SELECT * FROM {table} ORDER BY id ASC")

    if not rows:
        return None

    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def upload_table(hdfs, table, hdfs_dir, symbol=None):
    label = f"{table}/{symbol}" if symbol else table
    data = mysql_to_csv_bytes(table, symbol)
    if data is None:
        print(f"[tohadoop] No data for {label} — skip")
        return

    fname = f"{symbol}_{table}.csv" if symbol else f"{table}.csv"
    hdfs_path = f"{hdfs_dir}/{fname}"

    try:
        with hdfs.open(hdfs_path, "wb") as f:
            f.write(data)
        print(f"[tohadoop] Uploaded {label} ({len(data)} bytes) → {hdfs_path}")
    except Exception as e:
        print(f"[tohadoop] ERROR uploading {label}: {e}")


def main():
    hdfs = config.get_hdfs()
    if hdfs is None:
        print("[tohadoop] Hadoop (pydoop) not installed. pip install pydoop")
        print("[tohadoop] Skipping HDFS upload.")
        return

    print(f"[tohadoop] Starting HDFS upload at {datetime.now()}")

    STOCKS = ["UBL", "HBL", "OGDCL", "ENGRO", "PSO"]
    BASE   = "/user/smap_fyp"

    # Create base directories
    for d in [BASE, f"{BASE}/prices", f"{BASE}/indicators", f"{BASE}/predictions", f"{BASE}/news"]:
        try:
            hdfs.mkdir(d)
        except Exception:
            pass

    # Upload per-stock historical prices and indicators
    for symbol in STOCKS:
        upload_table(hdfs, "historical_prices", f"{BASE}/prices", symbol)
        upload_table(hdfs, "indicators",        f"{BASE}/indicators", symbol)
        upload_table(hdfs, "predictions",       f"{BASE}/predictions", symbol)

    # Upload news tables (no symbol filter)
    upload_table(hdfs, "articles",       f"{BASE}/news")
    upload_table(hdfs, "news_sentiment", f"{BASE}/news")

    print(f"[tohadoop] Done at {datetime.now()}")


if __name__ == "__main__":
    main()
