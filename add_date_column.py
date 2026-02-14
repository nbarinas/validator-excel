from backend.database import engine
from sqlalchemy import text

print("Adding date column to payroll_record_items...")
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE payroll_record_items ADD COLUMN date DATETIME;"))
        print("Column added successfully.")
    except Exception as e:
        print(f"Error (might already exist): {e}")
