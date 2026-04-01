import sqlite3

conn = sqlite3.connect('az_marketing.db')
c = conn.cursor()

c.execute("SELECT user_id, COUNT(*) as cnt FROM calls GROUP BY user_id ORDER BY cnt DESC LIMIT 10")
print("--- TOP AGENTES EN DB LOCAL ---")
for row in c.fetchall():
    print(f"User ID {row[0]}: {row[1]} calls")

# Buscar los momentos en los que se guardó el updated_at para usuario 9
query = """
SELECT strftime('%Y-%m-%d %H', updated_at) as hour, COUNT(*) as cnt 
FROM calls 
WHERE user_id = 9 
GROUP BY hour 
ORDER BY cnt DESC 
LIMIT 10
"""
c.execute(query)
print("\n--- PICOS DE ACTUALIZACION (ASIGNACION) PARA EL AGENTE 9 POR HORA ---")
for row in c.fetchall():
    print(f"Fecha/Hora: {row[0]}:00  -->  {row[1]} llamadas")

# Validar también el archivo original a nivel texto si posible (DUMP 1)
print("\n--- RASTREANDO LAS LLAMADAS DEL DUMP 1 PARA AGENTE 9 ---")
import sqlparse
with open("zoidusho_az_db (1).sql", "r", encoding="utf-8") as f:
    sql = f.read()
    print(f"La palabra (user_id=9) literal aparece:", sql.count(", 9,"))
