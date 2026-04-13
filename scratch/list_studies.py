import sqlite3
conn = sqlite3.connect('az_marketing.db')
cur = conn.cursor()
cur.execute("SELECT id, name, code FROM studies")
rows = cur.fetchall()
for row in rows:
    print(row)
conn.close()
