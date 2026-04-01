import sqlite3
import sqlparse
import re

dump2_file = 'zoidusho_az_db (28.02.26).sql'
with open(dump2_file, 'r', encoding='utf-8') as f:
    sql2 = f.read()

statements2 = sqlparse.split(sql2)
inserts2 = [s for s in statements2 if s.strip().upper().startswith('INSERT INTO `CALLS`')]

mem_conn = sqlite3.connect(':memory:')
mem_cursor = mem_conn.cursor()

# Get schema from real db
real_conn = sqlite3.connect('az_marketing.db')
schema = real_conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='calls'").fetchone()[0]
mem_cursor.execute(schema)

for s in inserts2:
    s_clean = s.replace('`', '"')
    s_clean = s_clean.replace("\\'", "''")
    s_clean = s_clean.replace("\\n", "\n").replace("\\r", "\r")
    s_clean = re.sub(r'\\([^rnt\'"\\])', r'\1', s_clean)
    try: 
        mem_cursor.execute(s_clean)
    except Exception as e: 
        pass

print("--- PICOS MASIVOS DE ACTUALIZACION EN DUMP 2 (HOY) ---")
mem_cursor.execute("""
  SELECT updated_at, user_id, COUNT(*) 
  FROM calls 
  WHERE updated_at >= '2026-02-28 00:00:00'
  GROUP BY updated_at, user_id 
  HAVING COUNT(*) >= 5
  ORDER BY 3 DESC
""")
for r in mem_cursor.fetchall():
    print(r)
