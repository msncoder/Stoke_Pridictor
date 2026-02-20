"""
Gold Price Scraper → MySQL commodity_prices table
Python 3.10+ / Windows 11. Uses Selenium for reliable scraping.
"""
import sys
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

URL = "https://www.investing.com/commodities/gold"
COMMODITY = "GOLD"

SCRAPE_INTERVAL = 60


def create_driver():
    """Create a Selenium WebDriver instance."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def get_price(driver=None):
    """Fetch commodity price using Selenium."""
    close_driver = False
    if driver is None:
        driver = create_driver()
        close_driver = True
    
    try:
        print(f"[{COMMODITY}] Fetching {URL}...")
        driver.get(URL)
        
        wait = WebDriverWait(driver, 10)
        try:
            el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='instrument-price-last']")))
            price = el.text.strip()
            print(f"[{COMMODITY}] Price found: {price}")
            return price
        except:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            el = soup.find("span", class_=lambda c: c and "instrument-price" in c)
            if el:
                return el.text.strip()
        
        print(f"[{COMMODITY}] WARNING: Price element not found.")
        return None
        
    except Exception as e:
        print(f"[{COMMODITY}] ERROR: {e}")
        return None
    finally:
        if close_driver:
            driver.quit()


def save_price(price_str):
    """Insert price into MySQL."""
    try:
        price = float(price_str.replace(",", ""))
    except ValueError:
        return
    config.execute(
        "INSERT INTO commodity_prices (commodity, price, scraped_at) VALUES (%s, %s, %s)",
        (COMMODITY, price, datetime.now()),
    )


def scrape_loop():
    print(f"[{COMMODITY}] Scraper started. Writing to MySQL `commodity_prices`.")
    driver = create_driver()
    
    try:
        while True:
            price = get_price(driver)
            if price:
                save_price(price)
                print(f"[{COMMODITY}] {datetime.now():%Y-%m-%d %H:%M:%S} | {price} → saved")
            time.sleep(SCRAPE_INTERVAL)
    except KeyboardInterrupt:
        print(f"\n[{COMMODITY}] Scraper stopped.")
    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_loop()