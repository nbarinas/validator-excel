from backend import database
from sqlalchemy import text, inspect

def migrate():
    db = database.SessionLocal()
    inspector = inspect(db.get_bind())
    log = []

    try:
        # --- USERS MIGRATION ---
        existing_user_cols = [c['name'] for c in inspector.get_columns('users')]
        new_user_cols = [
            ("neighborhood", "VARCHAR(100)"),
            ("blood_type", "VARCHAR(10)"),
            ("account_holder", "VARCHAR(100)"),
            ("account_holder_cc", "VARCHAR(20)")
        ]

        for col, dtype in new_user_cols:
            if col not in existing_user_cols:
                try:
                    db.execute(text(f"ALTER TABLE users ADD COLUMN {col} {dtype}"))
                    log.append(f"[User] Added {col}")
                except Exception as e:
                    log.append(f"[User] Error adding {col}: {e}")
            else:
                log.append(f"[User] Exists {col}")

        # --- BIZAGE STUDIES MIGRATION ---
        existing_biz_cols = [c['name'] for c in inspector.get_columns('bizage_studies')]
        new_biz_cols = [
            ("copies_price", "INTEGER"),
            ("vinipel_price", "INTEGER"),
            ("census", "VARCHAR(100)")
        ]

        for col, dtype in new_biz_cols:
            if col not in existing_biz_cols:
                try:
                    db.execute(text(f"ALTER TABLE bizage_studies ADD COLUMN {col} {dtype}"))
                    log.append(f"[Bizage] Added {col}")
                except Exception as e:
                    log.append(f"[Bizage] Error adding {col}: {e}")
            else:
                log.append(f"[Bizage] Exists {col}")

        db.commit()
        print("\n".join(log))
        print("Migration finished.")

    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
