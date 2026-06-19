import sqlite3
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(backend_dir, "../az_marketing.db")

def apply_indexes():
    print(f"Connecting to local SQLite database at: {os.path.abspath(db_path)}")
    if not os.path.exists(db_path):
        print("Error: local SQLite database file 'az_marketing.db' not found!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("Applying indexes to the 'calls' table...")
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calls_study_id ON calls (study_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calls_user_id ON calls (user_id);")
        conn.commit()
        print("Indexes created/verified successfully.")
    except Exception as e:
        print(f"Error creating indexes: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    apply_indexes()
