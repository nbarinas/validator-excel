import sqlite3
import sqlparse
import re

dump1_file = 'zoidusho_az_db (1).sql'
dump2_file = 'zoidusho_az_db (28.02.26).sql'
local_db_file = 'az_marketing.db'
cutoff_time = '2026-02-28 06:41:00'

conn = sqlite3.connect(local_db_file)
cursor = conn.cursor()

print("Borrando llamadas locales...")
cursor.execute("DELETE FROM calls")
conn.commit()

# --- PASO 1: Importar base primaria ---
print("Restaurando base intacta de Dump 1 (6:47 am)...")
with open(dump1_file, 'r', encoding='utf-8') as f:
    sql1 = f.read()

inserts1 = [s for s in sqlparse.split(sql1) if s.strip().upper().startswith("INSERT INTO `CALLS`")]
for s in inserts1:
    s_clean = s.replace('`', '"').replace("\\'", "''").replace("\\n", "\n").replace("\\r", "\r")
    s_clean = re.sub(r'\\([^rnt\'"\\])', r'\1', s_clean)
    try: cursor.execute(s_clean)
    except: pass
conn.commit()

# --- PASO 2: Cargar el Dump 2 (Novedades) a Memoria ---
print("Analizando Dump 2 (9:00 pm)...")
with open(dump2_file, 'r', encoding='utf-8') as f:
    sql2 = f.read()

inserts2 = [s for s in sqlparse.split(sql2) if s.strip().upper().startswith("INSERT INTO `CALLS`")]
mem_conn = sqlite3.connect(':memory:')
mem_cursor = mem_conn.cursor()
schema_sql = cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='calls'").fetchone()[0]
mem_cursor.execute(schema_sql)

for s in inserts2:
    s_clean = s.replace('`', '"').replace("\\'", "''").replace("\\n", "\n").replace("\\r", "\r")
    s_clean = re.sub(r'\\([^rnt\'"\\])', r'\1', s_clean)
    try: mem_cursor.execute(s_clean)
    except: pass

# --- PASO 3: Filtrar picos anómalos ---
print("Filtrando reasignaciones masivas accidentales...")
mem_cursor.execute("PRAGMA table_info(calls)")
columns = [info[1] for info in mem_cursor.fetchall()]
col_names = ', '.join([f'"{c}"' for c in columns])
placeholders = ', '.join(['?'] * len(columns))

query = f"""
SELECT {col_names} FROM calls 
WHERE (updated_at >= '{cutoff_time}' OR (updated_at IS NULL AND created_at >= '{cutoff_time}'))
  -- EXCLUIR EL PICO DE MILENA (08:39)
  AND NOT (user_id = 9 AND updated_at >= '2026-02-28 08:39:00' AND updated_at <= '2026-02-28 08:40:00')
  -- EXCLUIR EL PICO DE DESASIGNACIÓN (09:00-09:02)
  AND NOT (user_id IS NULL AND updated_at >= '2026-02-28 09:00:00' AND updated_at <= '2026-02-28 09:02:00')
"""
mem_cursor.execute(query)
recent_calls = mem_cursor.fetchall()

print(f"-> Novedades genuinas de agentes encontradas tras filtro: {len(recent_calls)} llamadas.")

if recent_calls:
    upsert_sql = f"""
    INSERT INTO calls ({col_names})
    VALUES ({placeholders})
    ON CONFLICT(id) DO UPDATE SET
    """
    update_clauses = [f'"{col}" = excluded."{col}"' for col in columns if col != 'id']
    upsert_sql += ",\n".join(update_clauses)
    
    cursor.executemany(upsert_sql, recent_calls)
    conn.commit()

mem_conn.close()
conn.close()
print("¡Limpieza y fusión perfecta completada!")
