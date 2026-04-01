from sqlalchemy import create_engine, text
from backend.database import SQLALCHEMY_DATABASE_URL

def migrate_census():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        try:
            print("Adding 'census' column to 'calls' table...")
            # Using text() for raw SQL execution
            conn.execute(text("ALTER TABLE calls ADD COLUMN census VARCHAR(50)"))
            conn.commit()
            print("Successfully added 'census' column.")
        except Exception as e:
            print(f"Migration failed (Column might already exist): {e}")

if __name__ == "__main__":
    migrate_census()
