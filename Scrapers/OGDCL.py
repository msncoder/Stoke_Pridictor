"""
OGDCL Stock Price Scraper → MySQL
Scrapes OGDCL live price from investing.com and stores in `stock_prices` table.

Python 3.10+ / Windows 11. No CSV output.
"""
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

URL = "https://www.investing.com/equities/oil---gas-dev"
SYMBOL = "OGDCL"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
}

SCRAPE_INTERVAL = 60  # seconds


def get_price():
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        el = soup.find(attrs={"data-test": "instrument-price-last"})
        if el:
            return el.text.strip()

        el = soup.find("span", class_=lambda c: c and "instrument-price" in c)
        if el:
            return el.text.strip()

        print(f"[{SYMBOL}] WARNING: Price element not found — site structure may have changed.")
        return None
    except requests.RequestException as e:
        print(f"[{SYMBOL}] ERROR: {e}")
        return None


def save_price(price_str):
    try:
        price = float(price_str.replace(",", ""))
    except ValueError:
        print(f"[{SYMBOL}] Cannot parse price: {price_str}")
        return

    config.execute(
        "INSERT INTO stock_prices (symbol, price, scraped_at, source_url) VALUES (%s, %s, %s, %s)",
        (SYMBOL, price, datetime.now(), URL),
    )


def scrape_loop():
    print(f"[{SYMBOL}] Scraper started. Writing to MySQL `stock_prices`.")
    last_price = None

    while True:
        price = get_price()
        if price and price != last_price:
            save_price(price)
            print(f"[{SYMBOL}] {datetime.now():%Y-%m-%d %H:%M:%S} | Price: {price} → saved")
            last_price = price
        elif price:
            print(f"[{SYMBOL}] {datetime.now():%Y-%m-%d %H:%M:%S} | Price: {price} (unchanged)")
        else:
            print(f"[{SYMBOL}] {datetime.now():%Y-%m-%d %H:%M:%S} | Failed to fetch")
        time.sleep(SCRAPE_INTERVAL)


if __name__ == "__main__":
    scrape_loop()