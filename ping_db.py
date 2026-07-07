import socket
import time
import os
import pymysql

host = "162.254.201.255"
port = 3306

print("=" * 60)
print(f"Host: {host}")
print(f"Port: {port}")
db_url = os.getenv("DATABASE_URL", "NO DEFINIDA")
safe_url = db_url.split("@")[-1] if "@" in db_url else db_url
print(f"DATABASE_URL (sin credenciales): {safe_url}")
print("=" * 60)

# Ping TCP
try:
    start = time.time()
    sock = socket.create_connection((host, port), timeout=10)
    elapsed = round(time.time() - start, 2)
    print(f"TCP OK: conexion en {elapsed}s")
    sock.close()
except Exception as e:
    print(f"TCP FAIL: {e}")

# MySQL
try:
    conn = pymysql.connect(
        host=host,
        port=port,
        user="zoidusho_az_user",
        password="AzMarketing2025*",
        database="zoidusho_az_db",
        connect_timeout=10
    )
    print("MYSQL OK")
    conn.close()
except Exception as e:
    print(f"MYSQL FAIL: {e}")

print("=" * 60)
print("Test finalizado. Manteniendo el proceso activo para logs...")
print("=" * 60)

# Mantener el proceso vivo para que Render no lo reinicie
while True:
    time.sleep(60)
