from backend.database import SessionLocal, engine
from sqlalchemy import text, inspect

def migrate_last_seen():
    try:
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('users')]
        
        if 'last_seen' in columns:
            print("'last_seen' column already exists.")
        else:
            print("Adding 'last_seen' column...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN last_seen DATETIME"))
            print("Successfully added 'last_seen' column.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate_last_seen()
