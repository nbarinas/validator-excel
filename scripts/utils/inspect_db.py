
from backend import database
from sqlalchemy import text

def inspect():
    db = next(database.get_db())
    try:
        result = db.execute(text("PRAGMA table_info(payroll_record_items)"))
        columns = [row[1] for row in result]
        print("Columns in payroll_record_items:", columns)
        
        if 'rate' not in columns:
            print("RATE COLUMN IS MISSING!")
        else:
            print("Rate column exists.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()
