import sqlite3
import sqlparse
import re

sql_file = 'zoidusho_az_db (1).sql'
db_file = 'az_marketing.db'

print("Reading dump...")
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# sqlparse splits safely around semicolons even inside strings
print("Parsing SQL statements...")
statements = sqlparse.split(sql_content)

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

insert_statements = [s for s in statements if s.strip().upper().startswith("INSERT INTO")]

tables_to_clear = set()
for s in insert_statements:
    match = re.search(r"INSERT INTO `([^`]+)`", s, re.IGNORECASE)
    if match:
        tables_to_clear.add(match.group(1))

for t in tables_to_clear:
    try:
        cursor.execute(f'DELETE FROM "{t}"')
        print(f"Cleared table {t}")
    except Exception as e:
        print(f"Could not clear {t}: {e}")

success_count = 0
for s in insert_statements:
    s_clean = s.replace('`', '"')
    
    # Process MySQL escapes carefully for SQLite
    s_clean = s_clean.replace("\\'", "''")
    s_clean = s_clean.replace("\\n", "\n")
    s_clean = s_clean.replace("\\r", "\r")
    # remove any unescaped backslashes before characters like \! \@
    s_clean = re.sub(r'\\([^rnt\'"\\])', r'\1', s_clean)
    
    try:
        cursor.execute(s_clean)
        success_count += 1
    except Exception as e:
        print(f"Error on: {s_clean[:100]}...")
        print(f"Error details: {e}")

conn.commit()
conn.close()
print(f"Import complete. Successfully ran {success_count} inserts out of {len(insert_statements)}.")
