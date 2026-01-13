import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from backend import models, database

print("Re-creating bizage_studies table...")
# Drop if exists (quick hack for schema update)
try:
    models.BizageStudy.__table__.drop(database.engine)
except:
    pass
models.Base.metadata.create_all(bind=database.engine)
print("Done.")
