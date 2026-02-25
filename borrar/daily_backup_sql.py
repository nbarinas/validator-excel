import os
import subprocess
import gzip
import shutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import sys

# =================================================================
# CONFIGURACIÓN (Completa estos datos)
# =================================================================
# 1. Credenciales de Base de Datos
# El script intentará leerlas de la variable de entorno DATABASE_URL
# Si no existe, puedes hardcodearlas aquí (solo para pruebas)
DB_HOST = "localhost" # Generalmente localhost en ClickPanda
DB_USER = "tu_usuario_db"
DB_PASS = "tu_password_db"
DB_NAME = "tu_nombre_db"

# 2. Configuración de Correo (SMTP)
SMTP_SERVER = "smtp.gmail.com" # O el de ClickPanda (ej. mail.tu-dominio.com)
SMTP_PORT = 587
SMTP_USER = "tu-correo@gmail.com"
SMTP_PASS = "tu-contraseña-de-aplicacion" # No es tu clave normal, es una clave de app
EMAIL_TO = "tu-correo@gmail.com"

# 3. Configuración de Archivos
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "respaldos")
RETENTION_DAYS = 7 # Cuántos días guardar copias locales
# =================================================================

def notify(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def get_db_config():
    """Detecta la configuración de la base de datos"""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        # Ejemplo: mysql://user:pass@host/dbname
        if db_url.startswith("mysql://") or db_url.startswith("postgresql://"):
            # Remover el prefijo
            clean_url = db_url.split("://")[1]
            auth, rest = clean_url.split("@")
            user, password = auth.split(":")
            host_port, dbname = rest.split("/")
            host = host_port.split(":")[0]
            return host, user, password, dbname
    
    return DB_HOST, DB_USER, DB_PASS, DB_NAME

def create_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    host, user, password, dbname = get_db_config()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sql_file = os.path.join(BACKUP_DIR, f"backup_{dbname}_{timestamp}.sql")
    gz_file = sql_file + ".gz"

    notify(f"Iniciando dump de la base de datos: {dbname}")
    
    try:
        # Ejecutar mysqldump
        # Nota: En ClickPanda/cPanel este comando suele estar disponible globalmente
        cmd = [
            "mysqldump",
            "-h", host,
            "-u", user,
            f"-p{password}",
            dbname
        ]
        
        with open(sql_file, "w") as f:
            subprocess.run(cmd, stdout=f, check=True)
            
        notify("Dump completado. Comprimiendo...")
        
        with open(sql_file, "rb") as f_in:
            with gzip.open(gz_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Eliminar el .sql original para ahorrar espacio
        os.remove(sql_file)
        
        notify(f"Respaldo creado: {gz_file}")
        return gz_file
    except Exception as e:
        notify(f"ERROR creando respaldo: {str(e)}")
        return None

def send_email(file_path):
    if not file_path or not os.path.exists(file_path):
        return

    notify(f"Enviando respaldo por correo a {EMAIL_TO}...")
    
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = EMAIL_TO
    msg['Subject'] = f"Respaldo Diario SQL - {datetime.now().strftime('%Y-%m-%d')}"

    # Adjuntar el archivo
    part = MIMEBase('application', 'octet-stream')
    with open(file_path, 'rb') as file:
        part.set_payload(file.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(file_path)}")
    msg.attach(part)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        notify("Correo enviado con éxito.")
    except Exception as e:
        notify(f"ERROR enviando correo: {str(e)}")

def rotate_backups():
    notify("Limpiando respaldos antiguos...")
    now = datetime.now()
    for f in os.listdir(BACKUP_DIR):
        f_path = os.path.join(BACKUP_DIR, f)
        if os.path.isfile(f_path):
            stat = os.stat(f_path)
            diff = (now - datetime.fromtimestamp(stat.st_mtime)).days
            if diff >= RETENTION_DAYS:
                os.remove(f_path)
                notify(f"Eliminado: {f}")

if __name__ == "__main__":
    # Si la base de datos es SQLite (local), este script no funcionará con mysqldump
    # Pero en el servidor ClickPanda será MySQL.
    
    backup_file = create_backup()
    if backup_file:
        send_email(backup_file)
        rotate_backups()
    
    notify("Proceso finalizado.")
