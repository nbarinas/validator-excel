
import requests
import json

BASE_URL = "http://localhost:8000"
# Adjust token if needed, assuming we have a valid superuser token or can get one.
# For this test, we might need to mock or just rely on manual running if auth is complex.
# Actually, I can use the internal function testing approach by importing main and database.
# But running against the live server is better if it's running. 
# The user didn't say the server is running. I can try to run it or just check imports.
# Let's write a script that imports main.py and tests the function directly using a TestSession.

from backend import main, models, database
from backend.main import app, create_manual_record, PayrollUpdate, PayrollItemUpdate
from sqlalchemy.orm import Session


def test_manual_record_logic():
    # Setup DB session
    db = next(database.get_db())
    
    # 1. Get or Create a User
    user = db.query(models.User).filter_by(username="test_user_99").first()
    if not user:
        user = models.User(username="test_user_99", role="agent", full_name="Test User")
        db.add(user)
        db.commit()
        db.refresh(user)
        
    # 2. Get or Create a Period
    from datetime import date
    period = db.query(models.PayrollPeriod).filter_by(name="Test Period Manual").first()
    if not period:
        period = models.PayrollPeriod(
            name="Test Period Manual", 
            start_date=date(2024, 1, 1), 
            end_date=date(2024, 1, 31)
        )
        db.add(period)
        db.commit()
        db.refresh(period)
        
    # 3. Create Concepts
    c1 = db.query(models.PayrollConcept).filter_by(period_id=period.id, name="Bono").first()
    if not c1:
        c1 = models.PayrollConcept(period_id=period.id, name="Bono", rate=10000)
        db.add(c1)
    
    c2 = db.query(models.PayrollConcept).filter_by(period_id=period.id, name="Prestamo").first()
    if not c2:
        c2 = models.PayrollConcept(period_id=period.id, name="Prestamo", rate=1) # Rate 1, qty will be negative amount
        db.add(c2)
        
    db.commit()
    db.refresh(c1)
    db.refresh(c2)
    
    # 4. Invoke create_manual_record
    print(f"Testing Manual Record for User {user.id} Period {period.id}")
    
    payload = PayrollUpdate(
        total_effective=0,
        total_censuses=0,
        items=[
            PayrollItemUpdate(concept_id=c1.id, quantity=2, date="2024-01-15"), # 20000
            PayrollItemUpdate(concept_id=c2.id, quantity=-5000, date="2024-01-20") # -5000
        ]
    )
    
    # Needs a current_user (superuser) mock
    superuser = db.query(models.User).filter_by(role="superuser").first()
    if not superuser:
        superuser = models.User(username="admin", role="superuser")
        db.add(superuser)
        db.commit()

    record = create_manual_record(
        period_id=period.id,
        user_id=user.id,
        data=payload,
        db=db,
        current_user=superuser
    )
    
    print(f"Record Total: {record.total_amount}")
    assert record.total_amount == 15000, f"Expected 15000, got {record.total_amount}"
    
    # Verify Items
    items = db.query(models.PayrollRecordItem).filter_by(record_id=record.id).all()
    print(f"Items found: {len(items)}")
    assert len(items) == 2
    
    for i in items:
        print(f"Item: Concept {i.concept_id}, Qty {i.quantity}, Total {i.total}, Date {i.date}")
        if i.concept_id == c1.id:
            assert i.quantity == 2
            assert i.total == 20000
            assert str(i.date.date()) == "2024-01-15"
        elif i.concept_id == c2.id:
            assert i.quantity == -5000
            assert i.total == -5000
            assert str(i.date.date()) == "2024-01-20"

    print("Test Validated Successfully!")

if __name__ == "__main__":
    try:
        test_manual_record_logic()
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
