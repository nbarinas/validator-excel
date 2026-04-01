from backend import database
from sqlalchemy import text, inspect

def migrate():
    db = database.SessionLocal()
    inspector = inspect(db.get_bind())
    
    try:
        # --- BIZAGE STUDIES MIGRATION ---
        existing_cols = [c['name'] for c in inspector.get_columns('bizage_studies')]
        col = "invoice_number"
        dtype = "VARCHAR(50)"

        if col not in existing_cols:
            try:
                db.execute(text(f"ALTER TABLE bizage_studies ADD COLUMN {col} {dtype}"))
                print(f"[Bizage] Added {col}")
            except Exception as e:
                print(f"[Bizage] Error adding {col}: {e}")
        else:
             print(f"[Bizage] Exists {col}")

        db.commit()
        print("Migration finished.")

    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
