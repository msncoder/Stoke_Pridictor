"""
Dawn.com News Scraper → MySQL `articles` table
Python 3.10+ / Windows 11. No CSV output.
"""
import sys
import re
import time
from datetime import datetime
from pathlib import Path

import cloudscraper
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

BASE_URL = "https://www.dawn.com"
SEED_URLS = [
    "https://www.dawn.com/business",
    "https://www.dawn.com/pakistan",
]
SOURCE_NAME = "dawn"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://www.dawn.com/",
}


def clean_text(text):
    """Remove stopwords, special chars."""
    tokens = word_tokenize(text.lower())
    tokens = [t for t in tokens if t.isalpha() and t not in _STOP]
    return " ".join(tokens)


def get_article_urls():
    urls = set()
    scraper = cloudscraper.create_scraper()
    
    for seed in SEED_URLS:
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                print(f"[dawn] Fetching {seed} (attempt {retry_count + 1}/{max_retries})...")
                r = scraper.get(seed, headers=HEADERS, timeout=15)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
                
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("/"):
                        href = BASE_URL + href
                    if "dawn.com" in href and href.startswith("https://") and href != seed:
                        urls.add(href)
                
                print(f"[dawn] Successfully fetched {seed}")
                break
                
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count
                    print(f"[dawn] ERROR: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"[dawn] ERROR fetching {seed} (max retries reached): {e}")
                    break
        
        time.sleep(2)
    
    return list(urls)


def extract_article(url, scraper):
    """Extract article text using cloudscraper + goose3."""
    if Goose is None:
        print("[dawn] goose3 not installed, skipping extraction")
        return None, None
    try:
        # Fetch with cloudscraper to bypass Cloudflare
        r = scraper.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        
        # Extract using goose3 from HTML content
        g = Goose()
        article = g.extract(raw_html=r.text)
        return article.title, article.cleaned_text
    except Exception as e:
        print(f"[dawn] Extraction failed for {url}: {e}")
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
        print(f"[dawn] DB insert error: {e}")


def run():
    print(f"[dawn] Crawling Dawn.com → MySQL `articles`")
    urls = get_article_urls()
    print(f"[dawn] Found {len(urls)} links")

    scraper = cloudscraper.create_scraper()
    saved = 0
    for url in urls:
        title, body = extract_article(url, scraper)
        if title:
            save_article(title, body, url)
            saved += 1
            print(f"[dawn] Saved: {title[:60]!r}")

    print(f"[dawn] Done. {saved}/{len(urls)} articles saved to MySQL.")


if __name__ == "__main__":
    run()
