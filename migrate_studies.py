from sqlalchemy import create_engine, text
from backend.database import SQLALCHEMY_DATABASE_URL

def migrate_studies():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(studies)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "status" not in columns:
                print("Adding 'status' column to studies table...")
                conn.execute(text("ALTER TABLE studies ADD COLUMN status VARCHAR DEFAULT 'open'"))
                print("Migration successful.")
            else:
                print("'status' column already exists.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_studies()
