import sqlite3
import os

db_path = 'az_marketing.db'

def inspect():
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(payroll_periods)")
        columns = cursor.fetchall()
        print("Columns in 'payroll_periods' table:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
    except Exception as e:
        print(f"Error inspecting payroll_periods: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect()
