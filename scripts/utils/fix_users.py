import sqlite3
import sqlparse
import re

sql_file = 'zoidusho_az_db (1).sql'
db_file = 'az_marketing.db'

print("Reading dump...")
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

statements = sqlparse.split(sql_content)
insert_statements = [s for s in statements if s.strip().upper().startswith("INSERT INTO `USERS`")]

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

success_count = 0
errors = []

for s in insert_statements:
    # Usar INSERT OR IGNORE para no duplicar los que (como el admin o del 20 en adelante) ya existen
    s_clean = s.replace('INSERT INTO', 'INSERT OR IGNORE INTO', 1)
    s_clean = s_clean.replace('`', '"')
    
    s_clean = s_clean.replace("\\'", "''")
    s_clean = s_clean.replace("\\n", "\n")
    s_clean = s_clean.replace("\\r", "\r")
    
    # Remover backlashes de escape de mysql (salvo los que ya procesamos)
    s_clean = re.sub(r'\\([^rnt\'"\\])', r'\1', s_clean)

    try:
        cursor.execute(s_clean)
        success_count += cursor.rowcount
    except Exception as e:
        errors.append(e)

conn.commit()
conn.close()

print(f"Users inserted this time: {success_count}")
if errors:
    print(f"Found {len(errors)} errors:")
    for err in errors[:3]:
        print(f"  - {err}")
