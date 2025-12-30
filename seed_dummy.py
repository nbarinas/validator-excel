from sqlalchemy.orm import Session
from backend import models, database, auth
import random

def seed_data():
    db = database.SessionLocal()
    
    # Create Studies
    study1 = models.Study(code="TEST01", name="Estudio Consumo Masivo")
    study2 = models.Study(code="TEST02", name="Encuesta Satisfaccion")
    
    db.add(study1)
    db.add(study2)
    db.commit()
    db.refresh(study1)
    db.refresh(study2)
    
    print(f"Created Study 1: {study1.name} (ID: {study1.id})")
    print(f"Created Study 2: {study2.name} (ID: {study2.id})")
    
    # Create Calls for Study 1 (5 sras)
    names_1 = ["Maria Gonzalez", "Ana Rodriguez", "Carmen Perez", "Laura Martinez", "Sofia Lopez"]
    phones_1 = ["3001002001", "3001002002", "3001002003", "3001002004", "3001002005"]
    
    for i in range(5):
        call = models.Call(
            study_id=study1.id,
            phone_number=phones_1[i],
            person_name=names_1[i],
            person_cc=f"1000{i}",
            city="Bogota",
            initial_observation="Pendiente contactar",
            status="pending",
            product_brand="Marca A"
        )
        db.add(call)
        
    # Create Calls for Study 2 (4 sras)
    names_2 = ["Elena Sanchez", "Patricia Ramirez", "Isabel Torres", "Marta Flores"]
    phones_2 = ["3102003001", "3102003002", "3102003003", "3102003004"]
    
    for i in range(4):
        call = models.Call(
            study_id=study2.id,
            phone_number=phones_2[i],
            person_name=names_2[i],
            person_cc=f"2000{i}",
            city="Medellin",
            initial_observation="Llamar en la tarde",
            status="pending",
            product_brand="Marca B",
            appointment_time="2025-12-31T14:00:00" if i == 0 else None
        )
        db.add(call)
        
    db.commit()
    print("Dummy data inserted successfully.")
    db.close()

if __name__ == "__main__":
    seed_data()
