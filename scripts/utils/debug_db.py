import sys
import os
from sqlalchemy import create_engine, inspect

# Force absolute path to be sure
db_path = os.path.join(os.getcwd(), "az_marketing.db")
DATABASE_URL = f"sqlite:///{db_path}"

print(f"Connecting to: {DATABASE_URL}")
engine = create_engine(DATABASE_URL)

def check_columns():
    inspector = inspect(engine)
    cols = inspector.get_columns('calls')
    col_names = [c['name'] for c in cols]
    print(f"Columns in 'calls': {col_names}")
    
    expected = ["realization_date", "temp_armando", "temp_auxiliar", "previous_user_id"]
    for e in expected:
        if e in col_names:
             print(f"[OK] Found {e}")
        else:
             print(f"[MISSING] {e}")

if __name__ == "__main__":
    try:
        check_columns()
    except Exception as e:
        print(f"Error: {e}")
