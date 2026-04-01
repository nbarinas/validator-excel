import sqlite3

conn = sqlite3.connect('az_marketing.db')
c = conn.cursor()

print("--- REPORTE DE EFECTIVIDAD Y FECHAS DE REALIZACION ---")
c.execute("""
SELECT 
    date(realization_date), 
    COUNT(*) 
FROM calls 
WHERE status IN ('managed', 'efectiva_campo', 'caida_desempeno', 'caida_desempeno_campo', 'caida_logistica', 'caida_logistico_campo')
GROUP BY date(realization_date)
ORDER BY 1 DESC
LIMIT 10
""")
for r in c.fetchall():
    print(f"Fecha de realizacion: {r[0]} -> {r[1]} llamadas")

print("\n--- EJEMPLO DE REGISTRO DE LLAMADA DE AYER ---")
c.execute("SELECT id, realization_date, updated_at, created_at, status FROM calls WHERE date(updated_at) = '2026-02-27' OR date(realization_date) = '2026-02-27' LIMIT 5")
for r in c.fetchall():
    print(r)

print("\n--- DISTRIBUCIÓN DE STATUS AYER ---")
c.execute("SELECT status, COUNT(*) FROM calls WHERE date(updated_at) = '2026-02-27' OR date(created_at) = '2026-02-27' GROUP BY status")
for r in c.fetchall():
    print(r)
