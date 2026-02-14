from backend.database import engine, Base
from backend import models

print("Creating new tables...")
# This will only create tables that don't exist
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
