from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 1. Configuración de la URL de la base de datos
# Resolve absolute path for local DB
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "az_marketing.db")

DATABASE_URL = os.getenv("DATABASE_URL")

# --- DATABASE SELECTION LOGIC ---
if DATABASE_URL:
    # SQLALCHEMY_DATABASE_URL preparation
    if DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    elif DATABASE_URL.startswith("mysql://"):
        SQLALCHEMY_DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
    else:
        SQLALCHEMY_DATABASE_URL = DATABASE_URL
    
    safe_url = SQLALCHEMY_DATABASE_URL.split("@")[-1] if "@" in SQLALCHEMY_DATABASE_URL else "cloud-db"
    print(f"INFO: Intentando conectar a base de datos externa: {safe_url}")
else:
    print("INFO: No se detectó DATABASE_URL. Usando base de datos local SQLite.")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 280
}

if "sqlite" in SQLALCHEMY_DATABASE_URL:
    connect_args = {"check_same_thread": False}
else:
    # MySQL specific connection timeout (10 seconds) to avoid hanging
    engine_kwargs["connect_args"] = {"connect_timeout": 10}

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, **engine_kwargs
    )
    # Test connection immediately to trigger fallback if needed
    with engine.connect() as conn:
        print("INFO: Conexión exitosa.")
except Exception as e:
    if DATABASE_URL and "sqlite" not in SQLALCHEMY_DATABASE_URL:
        print(f"ERROR: Falló conexión externa ({e}). USANDO RESPALDO LOCAL.")
        SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
        connect_args = {"check_same_thread": False}
        engine_kwargs = {"pool_pre_ping": True}
        engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args, **engine_kwargs)
    else:
        print(f"CRITICAL ERROR: No se puede conectar a ninguna base de datos: {e}")
        raise e
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
