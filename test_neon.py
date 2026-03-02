import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))
import config

def test_connection():
    print("Checking connection to Neon PostgreSQL...")
    try:
        cnx, cursor = config.get_db()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"Success! Database version: {version['version']}")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables in 'public' schema.")
        for t in tables:
            print(f" - {t['table_name']}")
            
        cursor.close()
        cnx.close()
        print("\nConnection verification complete.")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
