import sqlite3
conn = sqlite3.connect('az_marketing.db')
cur = conn.cursor()
cur.execute("SELECT id, name, code FROM studies WHERE name LIKE '%124%' OR code LIKE '%124%'")
rows = cur.fetchall()
for row in rows:
    print(row)
conn.close()
