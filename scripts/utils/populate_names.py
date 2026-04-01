from sqlalchemy.orm import Session
from backend import models, database

def populate_names():
    db = database.SessionLocal()
    try:
        # Update specific known users
        updates = {
            "1032509485": "Agente Test (1032509485)",
            "admin": "Administrador",
            "agente1": "Agente Uno",
            "agente2": "Agente Dos"
        }
        
        for username, full_name in updates.items():
            user = db.query(models.User).filter(models.User.username == username).first()
            if user:
                user.full_name = full_name
                print(f"Updated {username} -> {full_name}")
                
        db.commit()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    populate_names()
