from sqlalchemy import create_engine, text
from backend.database import SQLALCHEMY_DATABASE_URL

def migrate_studies_type_stage():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(studies)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "study_type" not in columns:
                print("Adding 'study_type' column to studies table...")
                conn.execute(text("ALTER TABLE studies ADD COLUMN study_type VARCHAR"))
            else:
                print("'study_type' column already exists.")

            if "stage" not in columns:
                print("Adding 'stage' column to studies table...")
                conn.execute(text("ALTER TABLE studies ADD COLUMN stage VARCHAR"))
            else:
                print("'stage' column already exists.")
                
            print("Migration check complete.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_studies_type_stage()
