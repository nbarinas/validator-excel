import os
import sys

# Script goes in az, but az/backend contains models.
# Add the parent directory of backend (which is az) to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.database import engine
from backend.models import BotQuota, BotQuotaUpdate

def upgrade():
    print("Creating Bot Quota tables...")
    BotQuota.__table__.create(engine, checkfirst=True)
    BotQuotaUpdate.__table__.create(engine, checkfirst=True)
    print("Migration completed successfully.")

if __name__ == "__main__":
    upgrade()
