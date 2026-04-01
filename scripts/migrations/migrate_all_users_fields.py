import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "az_marketing.db")

def migrate():
    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        # Define new columns and their types
        new_columns = {
            "full_name": "VARCHAR(100)",
            "bank": "VARCHAR(50)",
            "account_type": "VARCHAR(20)",
            "account_number": "VARCHAR(50)",
            "birth_date": "VARCHAR(20)",
            "phone_number": "VARCHAR(20)",
            "address": "VARCHAR(200)",
            "city": "VARCHAR(100)"
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                print(f"Adding '{col_name}' column to users table...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            else:
                print(f"'{col_name}' column already exists.")
            
        conn.commit()
        print("Migration successful.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
