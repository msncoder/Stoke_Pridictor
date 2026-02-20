"""
KSE National News Scraper → MySQL `articles` table
Python 3.10+ / Windows 11. Uses Selenium+Chrome to handle dynamic content.
"""
import sys
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

try:
    from goose3 import Goose
except ImportError:
    Goose = None

try:
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    _STOP = set(stopwords.words("english"))
except Exception:
    _STOP = set()
    word_tokenize = str.split

BASE_URL = "https://www.ksestocks.com"
SEED_URLS = [
    "https://www.ksestocks.com",
]
SOURCE_NAME = "kse_national"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def clean_text(text):
    """Remove stopwords, special chars."""
    tokens = word_tokenize(text.lower())
    tokens = [t for t in tokens if t.isalpha() and t not in _STOP]
    return " ".join(tokens)


def get_article_urls():
    """Extract article URLs from seed pages using Selenium."""
    urls = set()
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        for seed in SEED_URLS:
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    print(f"[kse_national] Fetching {seed} (attempt {retry_count + 1}/{max_retries})...")
                    driver.get(seed)
                    
                    # Wait for page to load
                    time.sleep(3)
                    
                    # Try to wait for dynamic content if available
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
                        )
                    except:
                        pass  # Continue anyway if wait times out
                    
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    
                    # Extract all links
                    for a in soup.find_all("a", href=True):
                        href = a["href"].strip()
                        if not href:
                            continue
                        
                        # Normalize relative URLs
                        if href.startswith("/"):
                            href = BASE_URL + href
                        
                        # Only keep ksestocks.com URLs
                        if "ksestocks.com" in href and href.startswith("https://"):
                            urls.add(href)
                    
                    print(f"[kse_national] Successfully fetched {seed}, found {len(urls)} links so far")
                    break
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2 ** retry_count
                        print(f"[kse_national] ERROR: {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"[kse_national] ERROR fetching {seed} (max retries reached): {e}")
                        break
            
            time.sleep(2)
    
    finally:
        if driver:
            driver.quit()
    
    return list(urls)


def extract_article(url, driver):
    """Extract article text using Selenium + goose3."""
    if Goose is None:
        print("[kse_national] goose3 not installed, skipping extraction")
        return None, None
    try:
        # Fetch with Selenium's rendered page
        driver.get(url)
        time.sleep(2)
        
        # Extract using goose3 from HTML content
        g = Goose()
        article = g.extract(raw_html=driver.page_source)
        return article.title, article.cleaned_text
    except Exception as e:
        print(f"[kse_national] Extraction failed for {url}: {e}")
        return None, None


def save_article(title, body, url):
    """Insert article into MySQL, skip if duplicate title."""
    body_clean = clean_text(body) if body else ""
    try:
        config.execute(
            """
            INSERT IGNORE INTO articles (title, body, source, url, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (title[:999], body_clean or None, SOURCE_NAME, url[:1023], datetime.now()),
        )
    except Exception as e:
        print(f"[kse_national] DB insert error: {e}")


def run():
    """Main scraping loop."""
    print(f"[kse_national] Crawling KSE National → MySQL `articles`")
    urls = get_article_urls()
    print(f"[kse_national] Found {len(urls)} links")

    # Configure Chrome options for extraction
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        saved = 0
        for url in urls:
            title, body = extract_article(url, driver)
            if title:
                save_article(title, body, url)
                saved += 1
                print(f"[kse_national] Saved: {title[:60]!r}")
        
        print(f"[kse_national] Done. {saved}/{len(urls)} articles saved to MySQL.")
    
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    run()