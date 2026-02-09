import sys
import os
from sqlalchemy import create_engine, text, inspect

# Add backend to path to allow imports if needed, though we will just use pure sqlalchemy here with the db url
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Database URL (Same as database.py default)
DATABASE_URL = "sqlite:///./az_marketing.db"
engine = create_engine(DATABASE_URL)

def migrate():
    print("Starting migration...")
    with engine.connect() as connection:
        # Check existing columns
        inspector = inspect(engine)
        existing_cols = [c['name'] for c in inspector.get_columns('calls')]
        print(f"Existing columns in 'calls': {existing_cols}")

        new_cols = [
            ("realization_date", "DATETIME"),
            ("temp_armando", "TEXT"),
            ("temp_auxiliar", "TEXT"),
            ("previous_user_id", "INTEGER"),
            ("dog_name", "VARCHAR(100)"),
            ("dog_user_type", "VARCHAR(50)"),
            ("stool_texture", "VARCHAR(200)"),
            ("health_status", "VARCHAR(200)"),
            ("dog_breed", "VARCHAR(100)"),
            ("dog_size", "VARCHAR(50)")
        ]

        for col, dtype in new_cols:
            if col not in existing_cols:
                print(f"Adding column: {col}")
                try:
                    connection.execute(text(f"ALTER TABLE calls ADD COLUMN {col} {dtype}"))
                    print(f"Successfully added {col}")
                except Exception as e:
                    print(f"Error adding {col}: {e}")
            else:
                print(f"Column {col} already exists.")
        
        print("Migration finished.")

        # Create Association Table if not exists
        # We use strict SQL since we don't have metadata reflection setup easily here without importing everything
        try:
            connection.execute(text("""
            CREATE TABLE IF NOT EXISTS study_assignments (
                user_id INTEGER,
                study_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(study_id) REFERENCES studies(id)
            )
            """))
            print("Ensured study_assignments table exists.")
        except Exception as e:
            print(f"Error creating table: {e}")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Fatal error: {e}")
