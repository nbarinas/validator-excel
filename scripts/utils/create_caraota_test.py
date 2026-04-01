from backend.database import SessionLocal
from backend.models import Study, Call
import random

def create_caraota_data():
    db = SessionLocal()
    try:
        # Check if study exists
        study = db.query(Study).filter(Study.code == "CARAOTA").first()
        if not study:
            print("Creating study 'Caraota'...")
            study = Study(
                code="CARAOTA",
                name="Estudio Caraota Test",
                status="open",
                study_type="validacion",
                stage="R1"
            )
            db.add(study)
            db.commit()
            db.refresh(study)
        else:
            print("Study 'Caraota' already exists.")

        # Add 5 unassigned calls
        print(f"Adding 5 unassigned records to study {study.name}...")
        for i in range(5):
            phone = f"300{random.randint(1000000, 9999999)}"
            call = Call(
                study_id=study.id,
                phone_number=phone,
                person_name=f"Test Usuario {i+1}",
                city="Bogotá",
                status="pending",
                user_id=None  # Explicitly unassigned
            )
            db.add(call)
        
        db.commit()
        print("Successfully added 5 records.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_caraota_data()
