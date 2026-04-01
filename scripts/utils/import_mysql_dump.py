import sqlite3
import re

sql_file = 'zoidusho_az_db (1).sql'
db_file = 'az_marketing.db'

print("Reading dump...")
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# We need to extract the raw INSERT INTO statements because MySQL formatting can be complex
# finditer is safer
pattern = re.compile(r"INSERT INTO `([^`]+)` \((.*?)\) VALUES\s*(.*?);", re.DOTALL)
inserts = list(pattern.finditer(sql_content))
print(f"Found {len(inserts)} INSERT blocks.")

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

tables = set(m.group(1) for m in inserts)
for t in tables:
    try:
        cursor.execute(f'DELETE FROM "{t}"')
        print(f"Cleared table {t}")
    except Exception as e:
        print(f"Warning: Could not clear {t}: {e}")

for m in inserts:
    table = m.group(1)
    cols = m.group(2).replace('`', '"')
    values_str = m.group(3)
    
    # Simple fix for MySQL escaped quotes (\') into SQLite ('')
    # and (\n, \r) chars if they exist as literals
    # This might not be perfect but covers 99% of basic dumps
    values_str = values_str.replace("\\'", "''")
    values_str = values_str.replace("\\r\\n", "\r\n")
    values_str = values_str.replace("\\n", "\n")
    
    sql = f'INSERT INTO "{table}" ({cols}) VALUES {values_str};'
    try:
        cursor.execute(sql)
    except Exception as e:
        print(f"Error inserting into {table}: {e}")

conn.commit()
conn.close()
print("Import complete.")
