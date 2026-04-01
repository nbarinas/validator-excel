from backend import database, models, auth
from backend.database import SessionLocal, engine
import sys

# Ensure tables exist
models.Base.metadata.create_all(bind=engine)

def verify_direct():
    db = SessionLocal()
    print("\n--- Direct Database Verification ---")
    
    # 1. Test User Model
    print("Creating user with new fields...")
    username = "verify_direct_user"
    try:
        # Cleanup
        existing = db.query(models.User).filter(models.User.username == username).first()
        if existing:
            db.delete(existing)
            db.commit()

        new_user = models.User(
            username=username,
            hashed_password="password123", # We don't hash for this simple test or use auth.get_password_hash
            role="auxiliar",
            full_name="Verification User",
            city="Bogotá",
            neighborhood="Chapinero Direct",
            blood_type="AB+",
            account_holder="Direct Holder",
            account_holder_cc="987654321"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"[OK] User created ID: {new_user.id}")
        if new_user.neighborhood == "Chapinero Direct" and new_user.blood_type == "AB+":
            print("[OK] New User fields verified in DB")
        else:
            print(f"[FAIL] User fields mismatch: {new_user.neighborhood}, {new_user.blood_type}")

        # 2. Test Bizage Study Model
        print("\nCreating Bizage Study with new fields...")
        new_study = models.BizageStudy(
            study_type="Ascensor",
            study_name="Direct Study",
            n_value=50,
            census="Direct Census",
            copies_price=1000,
            vinipel_price=500
        )
        db.add(new_study)
        db.commit()
        db.refresh(new_study)
        
        print(f"[OK] Study created ID: {new_study.id}")
        if new_study.census == "Direct Census" and new_study.copies_price == 1000:
            print("[OK] New Study fields verified in DB")
        else:
            print(f"[FAIL] Study fields mismatch: {new_study.census}, {new_study.copies_price}")
            
    except Exception as e:
        print(f"[FAIL] Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_direct()
