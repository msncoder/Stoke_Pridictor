"""
SMAP-FYP Central Configuration — MySQL-Only Architecture
Reads settings from .env and provides MySQL connection utilities.
"""
import os
from pathlib import Path

# ── Load .env ─────────────────────────────────────────────────────
ENV_PATH = Path(__file__).parent / ".env"

def _load_env():
    if not ENV_PATH.exists():
        print(f"[config] WARNING: .env not found at {ENV_PATH}")
        return
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

_load_env()

# ── Paths ─────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent

# ── MySQL (REQUIRED) ─────────────────────────────────────────────
MYSQL_HOST     = os.environ.get("MYSQL_HOST",     "localhost")
MYSQL_PORT     = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER     = os.environ.get("MYSQL_USER",     "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "smap_fyp")


def get_db():
    """
    Return (connection, cursor) or raise RuntimeError if MySQL unavailable.
    Callers are responsible for calling cnx.close() when done.
    """
    try:
        import mysql.connector
        cnx = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
        )
        cursor = cnx.cursor(dictionary=True)
        return cnx, cursor
    except ImportError:
        raise RuntimeError(
            "mysql-connector-python is not installed.\n"
            "Run: pip install mysql-connector-python"
        )
    except Exception as e:
        raise RuntimeError(
            f"Cannot connect to MySQL ({MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}).\n"
            f"Error: {e}\n"
            f"Make sure MySQL is running and credentials in .env are correct."
        )


def execute(sql, params=None, fetch=False, many=False):
    """
    Convenience wrapper — runs SQL, commits, and returns rows if fetch=True.
    Raises RuntimeError on connection failure.
    """
    cnx, cursor = get_db()
    try:
        if many:
            cursor.executemany(sql, params or [])
        else:
            cursor.execute(sql, params or ())
        
        # Fetch results BEFORE committing if needed
        result = None
        if fetch:
            result = cursor.fetchall()
        
        cnx.commit()
        return result if fetch else cursor.lastrowid
    finally:
        cursor.close()
        cnx.close()


def fetchall(sql, params=None):
    """Run a SELECT and return all rows as list of dicts."""
    return execute(sql, params, fetch=True)


def fetchone(sql, params=None):
    """Run a SELECT and return the first row as dict, or None."""
    rows = fetchall(sql, params)
    return rows[0] if rows else None


# ── Optional: Spark ───────────────────────────────────────────────
SPARK_HOME     = os.environ.get("SPARK_HOME", r"C:\spark")
PYSPARK_PYTHON = os.environ.get("PYSPARK_PYTHON", "python")

def get_spark_context():
    try:
        from pyspark import SparkContext
        from pyspark.sql import SQLContext
        sc = SparkContext.getOrCreate()
        return sc, SQLContext(sc)
    except ImportError:
        print("[config] WARNING: pyspark not installed. Spark features disabled.")
        return None, None
    except Exception as e:
        print(f"[config] WARNING: Spark unavailable: {e}")
        return None, None


# ── Optional: Hadoop ─────────────────────────────────────────────
def get_hdfs():
    try:
        import pydoop.hdfs as hdfs
        return hdfs
    except ImportError:
        print("[config] WARNING: pydoop not installed. Hadoop features disabled.")
        return None
    except Exception as e:
        print(f"[config] WARNING: Hadoop unavailable: {e}")
        return None


# ── Optional: Memcached ───────────────────────────────────────────
MEMCACHED_HOST = os.environ.get("MEMCACHED_HOST", "127.0.0.1")
MEMCACHED_PORT = int(os.environ.get("MEMCACHED_PORT", "11211"))

def get_memcache_client():
    try:
        import memcache
        return memcache.Client([f"{MEMCACHED_HOST}:{MEMCACHED_PORT}"], debug=0)
    except ImportError:
        print("[config] WARNING: python-memcached not installed.")
        return None
    except Exception as e:
        print(f"[config] WARNING: Memcached unavailable: {e}")
        return None
