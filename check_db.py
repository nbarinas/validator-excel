import sqlite3

def check_schema():
    conn = sqlite3.connect('az_marketing.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(calls)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print("Columns in 'calls' table:")
        for col in columns:
            print(f"- {col}")
            
        required = ['shampoo_quantity', 'second_collection_date', 'purchase_frequency']
        missing = [col for col in required if col not in columns]
        
        if missing:
            print(f"\nCRITICAL: Missing columns: {missing}")
        else:
            print("\nSUCCESS: All required columns are present.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_schema()
