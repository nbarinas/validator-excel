import sqlite3

conn = sqlite3.connect('az_marketing.db')
c = conn.cursor()

c.execute("""
SELECT 
    date(realization_date) as dia, 
    user_id,
    COUNT(*) 
FROM calls 
WHERE status IN ('managed', 'efectiva_campo', 'caida_desempeno', 'caida_desempeno_campo', 'caida_logistica', 'caida_logistico_campo')
  AND date(realization_date) = '2026-02-27'
GROUP BY 1, 2
ORDER BY 3 DESC
""")
print('Reporte Diario para Ayer (2026-02-27) REPARADO:')
for r in c.fetchall():
    print(f"Dia {r[0]}, Agente {r[1]}: {r[2]} efectivas")
