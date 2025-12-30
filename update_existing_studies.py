from sqlalchemy import create_engine, text
from backend.database import SQLALCHEMY_DATABASE_URL

def update_existing_studies():
    """Update existing studies with sample type and stage values"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Get all studies
            result = conn.execute(text("SELECT id, name FROM studies"))
            studies = result.fetchall()
            
            for idx, study in enumerate(studies):
                study_id = study[0]
                # Alternate between validacion and fatiga
                if idx % 2 == 0:
                    study_type = "validacion"
                    stage = "R1" if idx % 4 == 0 else "Rf"
                else:
                    study_type = "fatiga"
                    stages = ["R1", "R2", "R3", "Rf"]
                    stage = stages[idx % 4]
                
                conn.execute(
                    text("UPDATE studies SET study_type = :type, stage = :stage WHERE id = :id"),
                    {"type": study_type, "stage": stage, "id": study_id}
                )
                print(f"Updated study {study_id}: {study_type} - {stage}")
            
            conn.commit()
            print(f"\nSuccessfully updated {len(studies)} studies")
        except Exception as e:
            print(f"Update failed: {e}")

if __name__ == "__main__":
    update_existing_studies()
