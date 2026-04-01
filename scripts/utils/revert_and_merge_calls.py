import sqlite3
import sqlparse
import re

dump1_file = 'zoidusho_az_db (1).sql'
dump2_file = 'zoidusho_az_db (28.02.26).sql'
local_db_file = 'az_marketing.db'
cutoff_time = '2026-02-28 06:41:00'

conn = sqlite3.connect(local_db_file)
cursor = conn.cursor()

print("Borrando historial de llamadas local actual para limpieza total...")
cursor.execute("DELETE FROM calls")
conn.commit()

# --- PASO 1: Importar base primaria (Dump 1 de las 6:47 AM) ---
print(f"Importando base original intacta de calls desde {dump1_file}...")
with open(dump1_file, 'r', encoding='utf-8') as f:
    sql1 = f.read()

statements1 = sqlparse.split(sql1)
inserts1 = [s for s in statements1 if s.strip().upper().startswith("INSERT INTO `CALLS`")]

success_1 = 0
for s in inserts1:
    s_clean = s.replace('`', '"')
    s_clean = s_clean.replace("\\'", "''")
    s_clean = s_clean.replace("\\n", "\n").replace("\\r", "\r")
    s_clean = re.sub(r'\\([^rnt\'"\\])', r'\1', s_clean)
    try:
        cursor.execute(s_clean)
        success_1 += cursor.rowcount
    except Exception as e:
        pass

conn.commit()
print(f"-> Se re-establecieron las llamadas: {success_1} registros base.")

# --- PASO 2: Cargar el Dump 2 (Novedades) a Memoria ---
print(f"\nCargando novedades del dump actual {dump2_file} en memoria...")
with open(dump2_file, 'r', encoding='utf-8') as f:
    sql2 = f.read()

statements2 = sqlparse.split(sql2)
inserts2 = [s for s in statements2 if s.strip().upper().startswith("INSERT INTO `CALLS`")]

mem_conn = sqlite3.connect(':memory:')
mem_cursor = mem_conn.cursor()

# Copiar el esquema para la memoria
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='calls'")
schema_sql = cursor.fetchone()[0]
mem_cursor.execute(schema_sql)

success_2_mem = 0
for s in inserts2:
    s_clean = s.replace('`', '"')
    s_clean = s_clean.replace("\\'", "''")
    s_clean = s_clean.replace("\\n", "\n").replace("\\r", "\r")
    s_clean = re.sub(r'\\([^rnt\'"\\])', r'\1', s_clean)
    try:
        mem_cursor.execute(s_clean)
        success_2_mem += 1
    except:
        pass

print(f"-> Se cargaron {success_2_mem} lotes de llamadas en memoria.")

# --- PASO 3: Filtrar e inyectar DUMP 2 a DUMP 1 (Upsert tras 6:41 AM) ---
print(f"\nExtrayendo novedades posteriores a {cutoff_time}...")
mem_cursor.execute("PRAGMA table_info(calls)")
columns = [info[1] for info in mem_cursor.fetchall()]
col_names = ', '.join([f'"{c}"' for c in columns])
placeholders = ', '.join(['?'] * len(columns))

query = f"""
SELECT {col_names} FROM calls 
WHERE updated_at >= '{cutoff_time}' 
   OR (updated_at IS NULL AND created_at >= '{cutoff_time}')
"""
mem_cursor.execute(query)
recent_calls = mem_cursor.fetchall()

print(f"-> Encontrada(s) {len(recent_calls)} llamada(s) afectadas tras las 06:41 AM.")

if recent_calls:
    print("\nAplicando el Merge/Upsert oficial en la BD local...")
    upsert_sql = f"""
    INSERT INTO calls ({col_names})
    VALUES ({placeholders})
    ON CONFLICT(id) DO UPDATE SET
    """
    update_clauses = [f'"{col}" = excluded."{col}"' for col in columns if col != 'id']
    upsert_sql += ",\n".join(update_clauses)
    
    cursor.executemany(upsert_sql, recent_calls)
    conn.commit()
    print("-> ¡Merge de llamadas exitoso!")
else:
    print("-> No se encontraron cambios recientes para mezclar.")

mem_conn.close()
conn.close()
print("\nProceso finalizado.")
