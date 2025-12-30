import sqlite3
import os

DB_FILE = "az_marketing.db"

def migrate_db():
    if not os.path.exists(DB_FILE):
        print("DB does not exist yet.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # List of new columns and their types
    new_columns = [
        ("city", "TEXT"),
        ("initial_observation", "TEXT"),
        ("appointment_time", "TEXT"),
        ("product_brand", "TEXT"),
        ("extra_phone", "TEXT"),
        ("person_name", "TEXT")
    ]
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(calls)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    
    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            print(f"Adding column {col_name}...")
            try:
                cursor.execute(f"ALTER TABLE calls ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column {col_name} exists.")
            
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_db()
