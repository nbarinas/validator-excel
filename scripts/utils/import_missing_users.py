import sqlparse
import sqlite3

print("Reading zoidusho_az_db (1).sql...")
with open("zoidusho_az_db (1).sql", "r", encoding="utf-8") as f:
    sql = f.read()

statements = sqlparse.split(sql)
inserts = [s for s in statements if s.strip().upper().startswith("INSERT INTO `USERS`")]

print(f"Found {len(inserts)} inserts for users in the primary dump.")

conn = sqlite3.connect("az_marketing.db")
cursor = conn.cursor()

inserted = 0
for s in inserts:
    s_clean = s.replace("`", '"')
    
    # Manejo agresivo pero simple de los escapes de MySQL
    s_clean = s_clean.replace("\\'", "''")
    s_clean = s_clean.replace("\\n", "\n").replace("\\r", "\r")
    
    # Queremos INSERT OR IGNORE para proteger el ID 20+ y el admin
    s_clean = s_clean.replace("INSERT INTO", "INSERT OR IGNORE INTO", 1)
    
    try:
        cursor.execute(s_clean)
        inserted += cursor.rowcount
    except Exception as e:
        print(f"Error executing statement: {e}")

conn.commit()
conn.close()

print(f"Successfully inserted {inserted} users (ignoring duplicates).")
