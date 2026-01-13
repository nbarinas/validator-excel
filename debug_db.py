import sqlite3
import pandas as pd

def check_db():
    conn = sqlite3.connect("az_marketing.db")
    cursor = conn.cursor()
    
    print("--- Table Info ---")
    cursor.execute("PRAGMA table_info(users)")
    cols = cursor.fetchall()
    for c in cols:
        print(c)
        
    print("\n--- Recent Users ---")
    df = pd.read_sql("SELECT * FROM users ORDER BY id DESC LIMIT 5", conn)
    print(df.to_string())
    
    conn.close()

if __name__ == "__main__":
    check_db()
