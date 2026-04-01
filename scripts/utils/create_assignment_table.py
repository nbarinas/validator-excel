from backend.database import engine, Base
from backend import models

print("Creating payroll_assignments table...")
# This will create the new table because it doesn't exist yet
Base.metadata.create_all(bind=engine)
print("Table created successfully.")
