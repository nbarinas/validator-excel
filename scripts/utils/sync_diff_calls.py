import sqlite3
import sqlparse
import re
from datetime import datetime

# Archivos
new_sql_file = 'zoidusho_az_db (28.02.26).sql'
local_db_file = 'az_marketing.db'
cutoff_time = '2026-02-28 09:00:00'

print(f"Reading new dump file: {new_sql_file}")
with open(new_sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

print("Parsing SQL statements (this might take a few seconds)...")
statements = sqlparse.split(sql_content)
insert_statements = [s for s in statements if s.strip().upper().startswith("INSERT INTO `CALLS`")]

print(f"Found {len(insert_statements)} INSERT statements for table `calls`.")

# 1. Crear BD temporal en memoria
temp_conn = sqlite3.connect(':memory:')
temp_cursor = temp_conn.cursor()

# Extraer el esquema de 'calls' de la DB local para recrearlo en memoria
local_conn = sqlite3.connect(local_db_file)
local_cursor = local_conn.cursor()

print("Recreating `calls` schema in memory DB...")
local_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='calls'")
schema_sql = local_cursor.fetchone()[0]
temp_cursor.execute(schema_sql)

# 2. Inyectar datos del dump nuevo a la BD en memoria
print("Injecting new data into memory DB...")
success_count = 0
for s in insert_statements:
    s_clean = s.replace('`', '"')
    s_clean = s_clean.replace("\\'", "''")
    s_clean = s_clean.replace("\\n", "\n")
    s_clean = s_clean.replace("\\r", "\r")
    s_clean = re.sub(r'\\([^rnt\'"\\])', r'\1', s_clean)
    
    try:
        temp_cursor.execute(s_clean)
        success_count += 1
    except Exception as e:
        pass # ignorar fallos menores de parseo en memoria

print(f"Loaded {success_count} batches into memory.")

# 3. Extraer solo los registros nuevos o actualizados después del Cutoff
print(f"Extracting records modified or created after {cutoff_time}...")
temp_cursor.execute("PRAGMA table_info(calls)")
columns = [info[1] for info in temp_cursor.fetchall()]
col_names = ', '.join([f'"{c}"' for c in columns])
placeholders = ', '.join(['?'] * len(columns))

query = f"""
SELECT {col_names} FROM calls 
WHERE updated_at >= '{cutoff_time}' 
   OR (updated_at IS NULL AND created_at >= '{cutoff_time}')
"""
temp_cursor.execute(query)
recent_calls = temp_cursor.fetchall()

print(f"--> Found {len(recent_calls)} calls modified today after 9:00 AM.")

# 4. Hacer el UPSERT en la base de datos local real
if recent_calls:
    print("Applying updates to local database...")
    
    upsert_sql = f"""
    INSERT INTO calls ({col_names})
    VALUES ({placeholders})
    ON CONFLICT(id) DO UPDATE SET
    """
    
    # Crear cláusulas de update excluyendo 'id'
    update_clauses = [f'"{col}" = excluded."{col}"' for col in columns if col != 'id']
    upsert_sql += ",\n".join(update_clauses)
    
    local_cursor.executemany(upsert_sql, recent_calls)
    local_conn.commit()
    print("Local database updated successfully!")
else:
    print("No recent changes found to apply.")

temp_conn.close()
local_conn.close()
print("Done.")
