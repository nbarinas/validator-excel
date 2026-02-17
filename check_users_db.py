
import requests
import json

BASE_URL = "http://127.0.0.1:8000" # Assuming default or check database.py
# I need a token. I'll try to get it from the database or just check the DB directly.
# Since I'm an agent, I can check the DB directly.

from backend import database, models
from sqlalchemy.orm import Session

def check_users():
    db = next(database.get_db())
    users = db.query(models.User).all()
    print(f"Total users in DB: {len(users)}")
    roles = {}
    for u in users:
        roles[u.role] = roles.get(u.role, 0) + 1
        if "Prueba" in (u.full_name or "") or "zz_test" in u.username:
            print(f"User: {u.username}, Full Name: {u.full_name}, Role: {u.role}")
    
    print("\nRole distribution:")
    for role, count in roles.items():
        print(f"Role: {role}, Count: {count}")

if __name__ == "__main__":
    check_users()
