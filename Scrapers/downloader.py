"""
Document Downloader & Parser → MySQL `documents` table
Interactively downloads PDFs/web articles, extracts text, stores in MySQL.

Python 3.10+ / Windows 11. No CSV output. FTP removed.
"""
import sys
import io
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from goose3 import Goose
    GOOSE_AVAILABLE = True
except ImportError:
    GOOSE_AVAILABLE = False


def extract_pdf_text(content_bytes):
    """Extract text from PDF bytes."""
    if not PDF_AVAILABLE:
        print("[downloader] PyPDF2 not installed: pip install PyPDF2")
        return ""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)
    except Exception as e:
        print(f"[downloader] PDF extraction error: {e}")
        return ""


def extract_web_text(url):
    """Extract article text using goose3."""
    if not GOOSE_AVAILABLE:
        print("[downloader] goose3 not installed: pip install goose3")
        return "", ""
    try:
        g = Goose()
        article = g.extract(url=url)
        return article.title or "", article.cleaned_text or ""
    except Exception as e:
        print(f"[downloader] Extraction error: {e}")
        return "", ""


def save_document(title, body, url, file_type="webpage"):
    """Store document in MySQL, skip duplicates."""
    try:
        config.execute(
            """
            INSERT IGNORE INTO documents (title, body, source_url, file_type, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (title[:499], body or None, url[:1023] if url else None, file_type, datetime.now()),
        )
        print(f"[downloader] Saved to MySQL: {title[:60]!r}")
    except Exception as e:
        print(f"[downloader] DB error: {e}")


def download_url(url):
    """Download a URL and determine if it's PDF or HTML."""
    print(f"[downloader] Fetching: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        content_type = r.headers.get("Content-Type", "")

        if "pdf" in content_type or url.lower().endswith(".pdf"):
            text = extract_pdf_text(r.content)
            title = url.split("/")[-1] or "PDF Document"
            save_document(title, text, url, file_type="pdf")
        else:
            title, text = extract_web_text(url)
            if not title:
                title = url
            save_document(title, text, url, file_type="webpage")

    except requests.RequestException as e:
        print(f"[downloader] Request error: {e}")


def search_articles(keyword):
    """Full-text search articles in MySQL."""
    print(f"\n[downloader] Searching articles for: {keyword!r}")
    try:
        rows = config.fetchall(
            """
            SELECT id, title, source, created_at
            FROM articles
            WHERE MATCH(title, body) AGAINST(%s IN BOOLEAN MODE)
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (keyword,),
        )
        if not rows:
            print("[downloader] No results found.")
        else:
            for row in rows:
                print(f"  [{row['created_at']}] [{row['source']}] {row['title'][:80]}")
        return rows
    except Exception as e:
        print(f"[downloader] Search error: {e}")
        return []


def interactive_mode():
    """Interactive CLI for downloading and searching."""
    print("=" * 60)
    print("SMAP-FYP Document Downloader → MySQL")
    print("=" * 60)
    print("Commands: download <url> | search <keyword> | quit")

    while True:
        try:
            cmd = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[downloader] Exiting.")
            break

        if not cmd:
            continue

        parts = cmd.split(None, 1)
        action = parts[0].lower()

        if action in ("quit", "exit", "q"):
            break
        elif action == "download" and len(parts) == 2:
            download_url(parts[1].strip())
        elif action == "search" and len(parts) == 2:
            search_articles(parts[1].strip())
        else:
            print("Usage: download <url> | search <keyword> | quit")


if __name__ == "__main__":
    interactive_mode()