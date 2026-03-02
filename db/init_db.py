import sys
from pathlib import Path

# Add backend to path
BACKEND_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

import config

def init_db():
    print("Initializing Database Schema in Neon PostgreSQL...")
    schema_path = Path(__file__).parent / "schema.sql"
    
    if not schema_path.exists():
        print(f"Error: schema.sql not found at {schema_path}")
        return

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()

        print("Executing schema.sql...")
        # config.execute handles connection management
        config.execute(sql)
        print("Success! Database schema initialized.")
        
    except Exception as e:
        print(f"Failed to initialize database: {e}")

if __name__ == "__main__":
    init_db()
