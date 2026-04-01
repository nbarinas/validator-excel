import sqlite3
import os

# DB Path logic from database.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "az_marketing.db")

print(f"Checking database at: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print("Database not found!")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def add_column_if_missing(table, column, type_def):
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [info[1] for info in cursor.fetchall()]
        
        if column not in columns:
            print(f"Adding column {column} to {table}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}")
            print(f"  - Added {column}")
        else:
            print(f"Column {column} already exists in {table}.")
            
    except Exception as e:
        print(f"Error adding {column}: {e}")

# USERS TABLE
add_column_if_missing("users", "cedula_ciudadania", "VARCHAR(20)")
add_column_if_missing("users", "photo_base64", "TEXT")
add_column_if_missing("users", "account_holder_cc", "VARCHAR(20)")
add_column_if_missing("users", "last_seen", "DATETIME")
add_column_if_missing("users", "neighborhood", "VARCHAR(100)")

# CALLS TABLE (Just in case, from previous migrations)
add_column_if_missing("calls", "person_cc", "VARCHAR(20)")

conn.commit()
conn.close()
print("Migration check complete.")
