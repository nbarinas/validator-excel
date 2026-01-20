from sqlalchemy import create_engine, text
from backend.database import SQLALCHEMY_DATABASE_URL
import sys

def migrate():
    print("Starting Census Data & Study Status Migration...")
    
    # Ensure using SQLite
    if not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        print("This script is optimized for SQLite. Check database URL.")
        # Continue anyway as ALTER TABLE works for many SQL dialects
        
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    conn = engine.connect()

    def safe_add_column(table, column, type_def):
        try:
            # check if exists
            # SQLite doesn't support IF NOT EXISTS in ALTER TABLE nicely across versions, 
            # so we try and catch error
            print(f"Adding {column} to {table}...")
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}"))
            print(f" -> Added {column}")
        except Exception as e:
            if "duplicate column" in str(e) or "already exists" in str(e):
                print(f" -> {column} already exists in {table}")
            else:
                print(f" -> Error adding {column}: {e}")

    # 1. Update STUDIES table
    safe_add_column("studies", "is_active", "BOOLEAN DEFAULT 1")

    # 2. Update CALLS table
    new_columns = [
        ("nse", "VARCHAR(50)"),
        ("age", "VARCHAR(20)"),
        ("age_range", "VARCHAR(50)"),
        ("children_age", "VARCHAR(200)"),
        ("whatsapp", "VARCHAR(50)"),
        ("neighborhood", "VARCHAR(200)"),
        ("address", "VARCHAR(300)"),
        ("housing_description", "VARCHAR(300)"),
        ("respondent", "VARCHAR(100)"),
        ("supervisor", "VARCHAR(100)"),
        ("implantation_date", "VARCHAR(50)"),
        ("collection_date", "VARCHAR(50)"),
        ("collection_time", "VARCHAR(50)")
    ]

    for col_name, col_type in new_columns:
        safe_add_column("calls", col_name, col_type)
        
    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
