import sqlite3
import os

# Path calculation logic matching database.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Search for az_marketing.db
DB_FILE = "az_marketing.db"

# Try to find the DB file in common locations relative to this script
found_db = False
possible_paths = [
    DB_FILE,
    os.path.join("backend", DB_FILE),
    os.path.join("..", DB_FILE),
    os.path.join("..", "az_marketing.db"),
    os.path.join("az", DB_FILE)
]

for p in possible_paths:
    if os.path.exists(p):
        DB_FILE = p
        found_db = True
        break

if not found_db:
    # Fallback: try absolute path from user context if known, or just CWD
    # Start looking from CWD
    cwd = os.getcwd()
    print(f"Searching in {cwd}...")
    for root, dirs, files in os.walk(cwd):
        if "az_marketing.db" in files:
            DB_FILE = os.path.join(root, "az_marketing.db")
            found_db = True
            break

if not found_db:
    print("CRITICAL: az_marketing.db not found. Please ensure you are running this in the project root or provide the path.")
    # Attempt to create it? No, that would be bad if we want to modify existing.
    exit(1)

print(f"Connecting to {DB_FILE}...")

try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check calls table
    cursor.execute("PRAGMA table_info(calls)")
    cols_info = cursor.fetchall()
    existing_cols = [c[1] for c in cols_info]
    print(f"Existing columns in calls: {existing_cols}")
    
    needed_cols = {
        "purchase_frequency": "VARCHAR(100)",
        "implantation_pollster": "VARCHAR(100)",
        "supervisor": "VARCHAR(100)", 
        "implantation_date": "VARCHAR(50)"
    }
    
    for col, dtype in needed_cols.items():
        if col not in existing_cols:
            print(f"Adding missing column: {col}")
            try:
                # Add column
                cursor.execute(f"ALTER TABLE calls ADD COLUMN {col} {dtype}")
                # For SQLite, we can only add one column at a time usually in older versions, 
                # but modern sqlite supports it. Safer to do one by one.
                print(f"  - Added {col}")
            except Exception as e:
                print(f"  ! Failed to add {col}: {e}")
        else:
            print(f"Column {col} already exists.")
            
    conn.commit()
    conn.close()
    print("Migration (Calls) Complete.")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
