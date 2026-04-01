import sqlite3
import sqlparse
import re

with open('zoidusho_az_db (1).sql', 'r', encoding='utf-8') as f:
    sql = f.read()

# Dividir por sentencias
statements = sqlparse.split(sql)
inserts = [s for s in statements if s.strip().upper().startswith('INSERT INTO `USERS`')]

conn = sqlite3.connect('az_marketing.db')
cursor = conn.cursor()

inserted = 0
for i, s in enumerate(inserts):
    # Log the first 100 chars to see what block this is
    print(f"\n--- Processing batch {i+1} of {len(inserts)} ---")
    print(s[:100] + "...")
    
    s_clean = s.replace('`', '"')
    
    # Clean SQL escapes
    s_clean = s_clean.replace("\\'", "''")
    s_clean = s_clean.replace("\\n", "\n")
    s_clean = s_clean.replace("\\r", "\r")
    
    # Remove excessive backslashes from MySQL dump (like \", \!, \@)
    # Be careful not to replace completely formatted content
    s_clean = re.sub(r'\\([^rnt\'"\\])', r'\1', s_clean)
    
    s_clean = s_clean.replace('INSERT INTO', 'INSERT OR IGNORE INTO', 1)
    
    try:
        cursor.execute(s_clean)
        count = cursor.rowcount
        inserted += count
        print(f"Batch {i+1} success. Inserted {count} rows.")
    except Exception as e:
        print(f"Batch {i+1} FAILED with error: {e}")

conn.commit()
conn.close()
print(f"\nTotal completely new users inserted: {inserted}")
