from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 1. Configuración de la URL de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "az_marketing.db")

from sqlalchemy import text

SQLALCHEMY_DATABASE_URL = None
connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True, # Verifica la conexión antes de usarla para evitar "Lost Connection"
}

if DATABASE_URL:
    # Ajustes para Render (Postgres/MySQL)
    if DATABASE_URL.startswith("postgres://"):
        target_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    elif DATABASE_URL.startswith("mysql://"):
        target_url = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
    else:
        target_url = DATABASE_URL
    
    # Ocultar credenciales en el log por seguridad
    safe_url = target_url.split("@")[-1] if "@" in target_url else "cloud-db"
    
    print(f"INFO: Intentando conectar a base de datos externa: {safe_url}")
    try:
        # Creamos un motor temporal con timeout corto para validar la conexión
        # connect_timeout funciona para MySQL (pymysql) y Postgres (psycopg2)
        temp_connect_args = {"connect_timeout": 5} if "sqlite" not in target_url else {}
        test_engine = create_engine(target_url, connect_args=temp_connect_args)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        SQLALCHEMY_DATABASE_URL = target_url
        connect_args = {} # Reset to defaults for the main engine
        engine_kwargs["pool_recycle"] = 280
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 10
        print(f"SUCCESS: Conectado a base de datos externa.")
    except Exception as e:
        print(f"WARNING: Falló la conexión externa ({type(e).__name__}). Error: {e}")
        print(f"FALLBACK: Usando base de datos SQLite Local: {db_path}")
        SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
        connect_args = {"check_same_thread": False}
else:
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    connect_args = {"check_same_thread": False}
    print(f"INFO: Usando base de datos SQLite Local: {db_path}")

# 3. Creación del motor y la sesión
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args, **engine_kwargs
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
