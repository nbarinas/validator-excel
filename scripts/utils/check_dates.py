import sqlite3
import re

local_db_file = 'az_marketing.db'
conn = sqlite3.connect(local_db_file)
cursor = conn.cursor()

print("Calls counts by agent (Total):")
for row in cursor.execute("SELECT user_id, COUNT(*) FROM calls GROUP BY user_id ORDER BY 2 DESC LIMIT 5"):
    print(f"User {row[0]}: {row[1]}")

print("\nCalls counts for Date 2026-02-27 (Yesterday):")
for row in cursor.execute("SELECT user_id, COUNT(*) FROM calls WHERE date(created_at) = '2026-02-27' OR date(updated_at) = '2026-02-27' GROUP BY user_id ORDER BY 2 DESC LIMIT 5"):
    print(f"User {row[0]}: {row[1]}")

print("\nRecent call updates for User 9:")
for row in cursor.execute("SELECT updated_at, COUNT(*) FROM calls WHERE user_id = 9 GROUP BY updated_at ORDER BY 2 DESC LIMIT 10"):
    print(f"Updated at {row[0]}: {row[1]} calls")

# Also let check if the dump 1 has the correct data vs dump 2
print("\nScanning dumps directly for user 9 assigned calls...")
def count_user9_in_dump(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        sql = f.read()
    # Find all VALUES (...) and count those with user_id 9.
    # We can just count literal ', 9,' assuming it's an integer user_id. Overestimates slightly but fast.
    return sql.count(', 9,')

print(f"Dump 1 pattern ', 9,': {count_user9_in_dump('zoidusho_az_db (1).sql')}")
print(f"Dump 2 pattern ', 9,': {count_user9_in_dump('zoidusho_az_db (28.02.26).sql')}")
