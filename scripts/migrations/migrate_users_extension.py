import sqlite3
from backend.database import SQLALCHEMY_DATABASE_URL

def migrate_users():
    # Parse the SQLite URL to get the file path
    # URL format: sqlite:///./az_marketing.db
    db_path = "az_marketing.db" 
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get existing columns
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        new_columns = {
            "full_name": "VARCHAR(100)",
            "bank": "VARCHAR(50)",
            "account_type": "VARCHAR(20)",
            "account_number": "VARCHAR(50)",
            "birth_date": "VARCHAR(20)",
            "phone_number": "VARCHAR(20)"
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                print(f"Adding '{col_name}' column to users table...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                print(f"Added {col_name}.")
            else:
                print(f"'{col_name}' column already exists.")
                
        conn.commit()
        print("Migration successful.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_users()
