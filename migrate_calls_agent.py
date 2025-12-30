from sqlalchemy import create_engine, text
from backend.database import SQLALCHEMY_DATABASE_URL

def migrate_calls_agent():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(calls)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "user_id" not in columns:
                print("Adding 'user_id' column to calls table...")
                conn.execute(text("ALTER TABLE calls ADD COLUMN user_id INTEGER REFERENCES users(id)"))
                print("Migration successful.")
            else:
                print("'user_id' column already exists.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_calls_agent()
