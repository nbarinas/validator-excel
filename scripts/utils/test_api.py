import sys
import os
sys.path.append(r"c:\Users\Ciencia de DAtos\OneDrive - CONNECTA S.A.S\Escritorio\Varios\az")

from backend.database import SessionLocal
from backend.main import get_daily_effectives, get_active_cities

db = SessionLocal()

print("Testing active-cities...")
try:
    cities = get_active_cities(db=db, current_user=None)
    print("Cities:", cities)
except Exception as e:
    import traceback
    traceback.print_exc()

print("Testing daily-effectives with group_by_city...")
try:
    res = get_daily_effectives(db=db, current_user=None, group_by_city="Bogota")
    print("Effectives:", res[:2] if res else "Empty")
except Exception as e:
    import traceback
    traceback.print_exc()
