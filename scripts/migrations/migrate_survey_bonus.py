from sqlalchemy import create_engine, text
import os

# Database URL from environment or default to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./az_marketing.db")

# Handle PostgreSQL URL format for render
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def migrate():
    with engine.connect() as conn:
        try:
            # Add survey_id column
            conn.execute(text("""
                ALTER TABLE calls ADD COLUMN survey_id VARCHAR(100)
            """))
            print("✓ Added survey_id column")
        except Exception as e:
            print(f"survey_id column might already exist: {e}")
        
        try:
            # Add bonus_status column
            conn.execute(text("""
                ALTER TABLE calls ADD COLUMN bonus_status VARCHAR(20)
            """))
            print("✓ Added bonus_status column")
        except Exception as e:
            print(f"bonus_status column might already exist: {e}")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    migrate()
