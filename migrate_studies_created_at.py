from sqlalchemy import create_engine, text
from backend.database import SQLALCHEMY_DATABASE_URL

def migrate_studies_created_at():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(studies)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "created_at" not in columns:
                print("Adding 'created_at' column to studies table...")
                # SQLite valid ALTER TABLE ADD COLUMN allows NULL or constant default
                conn.execute(text("ALTER TABLE studies ADD COLUMN created_at DATETIME"))
                print("Migration successful.")
            else:
                print("'created_at' column already exists.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_studies_created_at()
