import sqlite3
import os

# Path calculation logic matching database.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Assuming this script is run from backend/ or root? 
# database.py is in backend. If we run this from project root, we need to adjust.
# Let's find az_marketing.db
# User path: c:\Users\Ciencia de DAtos\OneDrive - CONNECTA S.A.S\Escritorio\Varios\az\az_marketing.db
# It used to be there. Let's look for it.

DB_FILE = "az_marketing.db"
# Search in current dir or subdirs
if not os.path.exists(DB_FILE):
    if os.path.exists(os.path.join("backend", DB_FILE)): # unlikely
         DB_FILE = os.path.join("backend", DB_FILE)
    elif os.path.exists(os.path.join("..", DB_FILE)):
         DB_FILE = os.path.join("..", DB_FILE)
    elif os.path.exists(os.path.join("az", DB_FILE)):
         DB_FILE = os.path.join("az", DB_FILE)
    else:
        # User URI: c:\Users\Ciencia de DAtos\OneDrive - CONNECTA S.A.S\Escritorio\Varios\az\
        # So it should be in CWD if CWD is 'az'
        pass

print(f"Connecting to {DB_FILE}...")

try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Check payroll_periods columns
    cursor.execute("PRAGMA table_info(payroll_periods)")
    cols_info = cursor.fetchall()
    existing_cols = [c[1] for c in cols_info]
    print(f"Existing columns in payroll_periods: {existing_cols}")
    
    needed_cols = {
        "study_id": "INTEGER",
        "study_type": "VARCHAR(50)",
        "rates_snapshot": "TEXT",
        "execution_date": "DATETIME",
        "start_date": "DATETIME",
        "end_date": "DATETIME",
        "study_code": "VARCHAR(50)", 
        "is_visible": "BOOLEAN DEFAULT 1"
    }
    
    for col, dtype in needed_cols.items():
        if col not in existing_cols:
            print(f"Adding missing column: {col}")
            try:
                cursor.execute(f"ALTER TABLE payroll_periods ADD COLUMN {col} {dtype}")
                print(f"  - Added {col}")
            except Exception as e:
                print(f"  ! Failed to add {col}: {e}")
        else:
            print(f"Column {col} already exists.")
            
    conn.commit()
    conn.close()
    print("Migration Check Complete.")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
