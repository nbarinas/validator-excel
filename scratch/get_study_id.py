import sqlite3
conn = sqlite3.connect('az_marketing.db')
cur = conn.cursor()
cur.execute("SELECT id, name, code FROM studies WHERE code = '124' OR id = 124")
print(f"RESULT: {cur.fetchone()}")
conn.close()
