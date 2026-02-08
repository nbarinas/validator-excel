import pandas as pd
from sqlalchemy import create_engine, text
import os
import sys

# --- CONFIGURATION ---
# Default to local SQLite if no DATABASE_URL is set
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_URL = f"sqlite:///{os.path.join(BASE_DIR, 'az_marketing.db')}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# Fix for Render/MySQL if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

def normalize_header(h):
    return str(h).strip().lower()

def update_from_excel(file_path):
    print(f"--- Batch Update Tool ---")
    print(f"Target Database: {DATABASE_URL}")
    print(f"Reading file: {file_path}")
    
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    # Normalize columns
    df.columns = [normalize_header(c) for c in df.columns]
    cols = df.columns.tolist()
    print(f"Found columns: {cols}")

    # Mappings
    key_col_candidates = ["telefono", "celular", "phone_number", "numero", "movil"]
    
    # Target Columns to Update
    update_map = {
        "purchase_frequency": ["frecuencia compra", "frecuencia de compra", "frecuencia_compra"],
        "implantation_pollster": ["encuestador", "encuestador implante", "encuestador_implante", "nombre encuestador"],
        "supervisor": ["supervisor", "supervisora"],
        "implantation_date": ["fecha implante", "fecha de implante", "fecha_implante"]
    }

    # Identify Key Column
    key_col = None
    for c in key_col_candidates:
        if c in cols:
            key_col = c
            break
    
    if not key_col:
        print("ERROR: Could not find a phone number column (telefono, celular, etc).")
        return

    print(f"Using '{key_col}' as the unique key to match records.")
    
    # Establish Connection
    try:
        engine = create_engine(DATABASE_URL)
        conn = engine.connect()
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    updated_count = 0
    not_found_count = 0
    
    print("\nStarting Update...")
    
    for index, row in df.iterrows():
        phone = str(row[key_col]).strip()
        if not phone or phone == 'nan':
            continue

        # Build Update Dict
        updates = {}
        
        for db_field, excel_candidates in update_map.items():
            for candid in excel_candidates:
                if candid in cols:
                    val = row[candid]
                    if pd.notna(val):
                        updates[db_field] = str(val).strip()
                        break 
        
        if not updates:
            print(f"Skipping {phone}: No updateable data found in row.")
            continue

        # Construct SQL
        # We assume phone_number is unique enough per study? 
        # Ideally we should filter by study_id too, but user didn't specify.
        # We will update the LATEST call with this phone number to be safe, 
        # or ALL calls with this phone number? Usually specific study.
        # Let's try to match strict.
        
        set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
        params = updates.copy()
        params['phone'] = phone
        
        # Check if exists first
        check_sql = text("SELECT id FROM calls WHERE phone_number = :phone ORDER BY id DESC LIMIT 1")
        result = conn.execute(check_sql, {"phone": phone}).fetchone()
        
        if result:
            call_id = result[0]
            update_sql = text(f"UPDATE calls SET {set_clause} WHERE id = :id")
            params['id'] = call_id
            conn.execute(update_sql, params)
            conn.commit()
            print(f"Updated Call ID {call_id} (Phone: {phone}) -> {updates}")
            updated_count += 1
        else:
            print(f"Phone {phone} not found in DB.")
            not_found_count += 1

    conn.close()
    print(f"\nSummary: Updated {updated_count} records. {not_found_count} not found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_calls_from_excel.py <path_to_excel>")
    else:
        update_from_excel(sys.argv[1])
