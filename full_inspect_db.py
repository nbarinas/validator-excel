
from backend import database
from sqlalchemy import text

def inspect_all():
    db = next(database.get_db())
    try:
        # Check payroll_periods columns
        print("--- payroll_periods ---")
        result = db.execute(text("PRAGMA table_info(payroll_periods)"))
        columns = [row[1] for row in result]
        print("Columns:", columns)
        
        # Check payroll_assignments table
        print("\n--- payroll_assignments ---")
        try:
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='payroll_assignments'"))
            table_exists = result.fetchone()
            if table_exists:
                print("Table exists.")
                result = db.execute(text("PRAGMA table_info(payroll_assignments)"))
                print("Columns:", [row[1] for row in result])
            else:
                print("Table DOES NOT exist.")
        except Exception as e:
            print(f"Error checking table: {e}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_all()
