
from backend import database
from sqlalchemy import text

def add_rate_column():
    print("Adding rate column to payroll_record_items...")
    db = next(database.get_db())
    try:
        # Check if exists first (double check)
        result = db.execute(text("PRAGMA table_info(payroll_record_items)"))
        columns = [row[1] for row in result]
        
        if 'rate' not in columns:
            print("Adding column...")
            db.execute(text("ALTER TABLE payroll_record_items ADD COLUMN rate INTEGER DEFAULT 0"))
            db.commit()
            print("Column 'rate' added successfully.")
        else:
            print("Column 'rate' already exists.")
            
    except Exception as e:
        print(f"Error adding column: {e}")
        db.rollback()

if __name__ == "__main__":
    add_rate_column()
