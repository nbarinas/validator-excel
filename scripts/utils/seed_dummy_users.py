from backend.database import SessionLocal
from backend.models import User
from datetime import datetime, timedelta
import random

def seed():
    db = SessionLocal()
    print("Seeding 25 dummy users...")
    
    roles = ["agent", "auxiliar", "supervisor", "admin"]
    
    for i in range(1, 26):
        # Determine status color by manipulating time
        # 0-9m: Green
        # 10-14m: Yellow
        # 15-19m: Red
        minutes_ago = random.randint(0, 19) 
        last_seen = datetime.utcnow() - timedelta(minutes=minutes_ago)
        
        username = f"zz_test_user_{i}"
        
        # Check if exists to avoid error on re-run
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            existing.last_seen = last_seen
        else:
            u = User(
                username=username,
                full_name=f"Usuario Prueba {i}",
                hashed_password="dummy_hash_value",
                role=random.choice(roles),
                last_seen=last_seen
            )
            db.add(u)
            
    db.commit()
    print("Done. Refresh the page to see the scrollbar.")

if __name__ == "__main__":
    seed()
