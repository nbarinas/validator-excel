import socket
import time
import os
import pymysql
from http.server import HTTPServer, BaseHTTPRequestHandler

host = "162.254.201.255"
port = 3306

print("=" * 60)
print(f"Host: {host}")
print(f"Port: {port}")
db_url = os.getenv("DATABASE_URL", "NO DEFINIDA")
safe_url = db_url.split("@")[-1] if "@" in db_url else db_url
print(f"DATABASE_URL (sin credenciales): {safe_url}")
print("=" * 60)

results = []

# Ping TCP
try:
    start = time.time()
    sock = socket.create_connection((host, port), timeout=10)
    elapsed = round(time.time() - start, 2)
    msg = f"TCP OK: conexion en {elapsed}s"
    print(msg)
    results.append(msg)
    sock.close()
except Exception as e:
    msg = f"TCP FAIL: {e}"
    print(msg)
    results.append(msg)

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
    msg = "MYSQL OK"
    print(msg)
    results.append(msg)
    conn.close()
except Exception as e:
    msg = f"MYSQL FAIL: {e}"
    print(msg)
    results.append(msg)

print("=" * 60)
print("Test finalizado. Levantando servidor HTTP para Render...")
print("=" * 60)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        body = "Diagnostico Render -> ClickPanda MySQL\n\n"
        body += f"DATABASE_URL (sin credenciales): {safe_url}\n\n"
        for r in results:
            body += r + "\n"
        self.wfile.write(body.encode())

    def log_message(self, format, *args):
        # Silenciar logs de requests HTTP para no saturar
        pass


server_port = int(os.getenv("PORT", "10000"))
server = HTTPServer(("0.0.0.0", server_port), Handler)
print(f"Servidor HTTP escuchando en puerto {server_port}")
server.serve_forever()
