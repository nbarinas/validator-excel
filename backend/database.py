from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os

# Use DATABASE_URL from environment (Render) or fallback to local SQLite
# Resolve absolute path to ensure consistency regardless of CWD
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "az_marketing.db")
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

# Fix for Render: SQLAlchemy expects postgresql:// but Render provides postgres://
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fix for MySQL: Ensure pymysql driver is used if user provided mysql://
if SQLALCHEMY_DATABASE_URL.startswith("mysql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

connect_args = {}
engine_kwargs = {}

if "sqlite" in SQLALCHEMY_DATABASE_URL:
    connect_args = {"check_same_thread": False}
elif "mysql" in SQLALCHEMY_DATABASE_URL:
    # MySQL connection pooling to avoid "MySQL server has gone away"
    engine_kwargs["pool_recycle"] = 280

    engine_kwargs["pool_recycle"] = 280

print(f"DEBUG: SQLALCHEMY_DATABASE_URL = {SQLALCHEMY_DATABASE_URL}")
print(f"DEBUG: CWD = {os.getcwd()}")

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
