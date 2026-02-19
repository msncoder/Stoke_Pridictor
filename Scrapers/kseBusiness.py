"""
KSE Business News Scraper → MySQL `articles` table
Python 3.10+ / Windows 11. No CSV output.
"""
import sys
import re
from datetime import datetime
from pathlib import Path

import requests
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
    "https://www.ksestocks.com/News",
    "https://www.ksestocks.com/MarketSummary",
]
SOURCE_NAME = "kse_business"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def clean_text(text):
    tokens = word_tokenize(text.lower())
    tokens = [t for t in tokens if t.isalpha() and t not in _STOP]
    return " ".join(tokens)


def get_article_urls():
    urls = set()
    for seed in SEED_URLS:
        try:
            r = requests.get(seed, headers=HEADERS, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = BASE_URL + href
                if "ksestocks.com" in href and href != seed:
                    urls.add(href)
        except Exception as e:
            print(f"[kse_business] ERROR {seed}: {e}")
    return list(urls)


def extract_article(url):
    if Goose is None:
        return None, None
    try:
        g = Goose()
        article = g.extract(url=url)
        return article.title, article.cleaned_text
    except Exception as e:
        print(f"[kse_business] Extraction failed: {e}")
        return None, None


def save_article(title, body, url):
    body_clean = clean_text(body) if body else ""
    try:
        config.execute(
            "INSERT IGNORE INTO articles (title, body, source, url, created_at) VALUES (%s, %s, %s, %s, %s)",
            (title[:999], body_clean or None, SOURCE_NAME, url[:1023], datetime.now()),
        )
    except Exception as e:
        print(f"[kse_business] DB insert error: {e}")


def run():
    print(f"[kse_business] Crawling KSE Business → MySQL `articles`")
    urls = get_article_urls()
    print(f"[kse_business] Found {len(urls)} links")
    saved = 0
    for url in urls:
        title, body = extract_article(url)
        if title:
            save_article(title, body, url)
            saved += 1
    print(f"[kse_business] Done. {saved}/{len(urls)} articles saved.")


if __name__ == "__main__":
    run()