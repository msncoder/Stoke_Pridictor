"""
RSS News Feed Sentiment Analyzer → MySQL `news_sentiment` table
Fetches Google News RSS, scores each article per stock, stores in MySQL.

Python 3.10+ / Windows 11. No CSV output.
"""
import sys
import re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

try:
    from goose3 import Goose
except ImportError:
    Goose = None
    print("[newsfeed] WARNING: goose3 not installed. pip install goose3")

try:
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    _STOP = set(stopwords.words("english"))
except Exception:
    _STOP = set()
    word_tokenize = str.split

try:
    import pysentiment2 as ps
    _LM = ps.LM()
except ImportError:
    try:
        import pysentiment as ps
        _LM = ps.LM()
    except ImportError:
        _LM = None
        print("[newsfeed] WARNING: pysentiment2 not installed. pip install pysentiment2")

try:
    import feedparser
except ImportError:
    feedparser = None
    print("[newsfeed] WARNING: feedparser not installed. pip install feedparser")

RSS_URL = (
    "https://news.google.com/news/rss/headlines/section/topic"
    "/BUSINESS.en_pk/Business?ned=en_pk&hl=en&gl=PK"
)

KEYWORD_MAP = {
    "PSO":    [" pso ", "pakistan state oil"],
    "HBL":    [" hbl ", "habib bank"],
    "OGDCL":  [" ogdc ", " ogdcl ", "oil & gas development"],
    "UBL":    [" ubl ", "united bank"],
    "ENGRO":  [" engro ", "engro fertilizer"],
}


def clean_text(text):
    tokens = word_tokenize(text.lower())
    tokens = [t for t in tokens if t.isalpha() and t not in _STOP]
    text = " ".join(tokens)
    return re.sub(r"\s+", " ", text).strip()


def classify_stock(text):
    """Return list of matching stock symbols."""
    matches = []
    for stock, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in f" {text} ":
                matches.append(stock)
                break
    return matches


def score_text(text):
    """Return (polarity, subjectivity, signal) using pysentiment2 LM."""
    if _LM is None:
        return 0, 0, "NEUTRAL"
    tokens = _LM.tokenize(text)
    score = _LM.get_score(tokens)
    polarity = float(score.get("Polarity", 0))
    subjectivity = float(score.get("Subjectivity", 0))
    if polarity > 0:
        signal = "BUY"
    elif polarity < 0:
        signal = "SELL"
    else:
        signal = "NEUTRAL"
    return polarity, subjectivity, signal


def save_sentiment(stock, title, polarity, subjectivity, signal):
    config.execute(
        """
        INSERT INTO news_sentiment (stock, title, polarity, subjectivity, signal, scored_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (stock, title[:999], polarity, subjectivity, signal, datetime.now()),
    )


def run():
    if feedparser is None or Goose is None or _LM is None:
        print("[newsfeed] Cannot run — missing required libraries (feedparser, goose3, pysentiment2).")
        return

    print(f"[newsfeed] Fetching RSS feed → MySQL `news_sentiment`")
    feed = feedparser.parse(RSS_URL)
    print(f"[newsfeed] {len(feed.entries)} articles found")

    saved = 0
    for entry in feed.entries:
        title = entry.get("title", "")
        link  = entry.get("link", "")
        if not link:
            continue

        try:
            g = Goose()
            article = g.extract(url=link)
            body = article.cleaned_text
        except Exception:
            body = title

        text = clean_text(f"{title} {body}")
        stocks = classify_stock(text)

        for stock in stocks:
            polarity, subjectivity, signal = score_text(text)
            save_sentiment(stock, title, polarity, subjectivity, signal)
            print(f"[newsfeed] {stock} | {signal} ({polarity:+.4f}) | {title[:50]!r}")
            saved += 1

    print(f"[newsfeed] Done. {saved} sentiment records saved to MySQL.")


if __name__ == "__main__":
    run()
