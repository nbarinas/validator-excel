import sqlite3
import os

# Database path (assuming it's in the same directory as this script)
DB_PATH = os.path.join(os.path.dirname(__file__), "az_marketing.db")

def migrate():
    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "address" not in columns:
            print("Adding 'address' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN address VARCHAR(200)")
        else:
            print("'address' column already exists.")
            
        if "city" not in columns:
            print("Adding 'city' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN city VARCHAR(100)")
        else:
            print("'city' column already exists.")
            
        conn.commit()
        print("Migration successful.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
