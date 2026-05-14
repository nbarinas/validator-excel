from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 1. Configuración de la URL de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("CRITICAL: DATABASE_URL environment variable is missing. External DB is required.")

# Ajustes para Render (Postgres/MySQL)
if DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
elif DATABASE_URL.startswith("mysql://"):
    SQLALCHEMY_DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
else:
    SQLALCHEMY_DATABASE_URL = DATABASE_URL

# Ocultar credenciales en el log por seguridad
safe_url = SQLALCHEMY_DATABASE_URL.split("@")[-1] if "@" in SQLALCHEMY_DATABASE_URL else "cloud-db"
print(f"INFO: Conectando UNICAMENTE a base de datos externa: {safe_url}")

# 2. Configuración específica del motor
connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True, # Verifica la conexión antes de usarla
    "pool_recycle": 280,
    "pool_size": 5,
    "max_overflow": 10
}

# 3. Creación del motor y la sesión
# Nota: Si ClickPanda está caído, esto fallará aquí o al primer intento de uso.
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
