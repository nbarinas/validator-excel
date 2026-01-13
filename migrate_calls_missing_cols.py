from sqlalchemy import create_engine, text
from backend.database import SQLALCHEMY_DATABASE_URL

def migrate():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Add 'observation'
            print("Adding 'observation' column...")
            try:
                conn.execute(text("ALTER TABLE calls ADD COLUMN observation TEXT"))
                print("Added 'observation'")
            except Exception as e:
                print(f"Skipped 'observation': {e}")
                
            # Add 'created_at'
            print("Adding 'created_at' column...")
            try:
                conn.execute(text("ALTER TABLE calls ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                print("Added 'created_at'")
            except Exception as e:
                print(f"Skipped 'created_at': {e}")
                
             # Add 'updated_at'
            print("Adding 'updated_at' column...")
            try:
                conn.execute(text("ALTER TABLE calls ADD COLUMN updated_at DATETIME"))
                print("Added 'updated_at'")
            except Exception as e:
                print(f"Skipped 'updated_at': {e}")
                
            conn.commit()
            print("Migration completed.")
            
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
