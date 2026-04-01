from backend.database import SessionLocal
from backend import models, auth

def reset_admin():
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == "admin").first()
        hashed_pw = auth.get_password_hash("admin123")
        
        if user:
            print("Found admin user. Updating password...")
            user.hashed_password = hashed_pw
            user.role = "superuser" # Ensure correct role
        else:
            print("Admin user not found. Creating...")
            user = models.User(
                username="admin", 
                hashed_password=hashed_pw, 
                role="superuser",
                full_name="Administrator"
            )
            db.add(user)
        
        db.commit()
        print("Successfully reset admin password to 'admin123'")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin()
