from backend import database, models
from backend.database import SessionLocal, engine
from datetime import datetime

# Ensure tables exist (already done, but safe to call)
models.Base.metadata.create_all(bind=engine)

def verify_invoice():
    db = SessionLocal()
    print("\n--- Invoice Number Verification ---")
    
    try:
        # Create a test study
        study = models.BizageStudy(
            study_type="Ascensor",
            study_name="Invoice Verification Study",
            n_value=10,
            status="number_assigned" # Ready to pay
        )
        db.add(study)
        db.commit()
        db.refresh(study)
        print(f"[OK] Created Study ID: {study.id}")
        
        # Simulate Pay with Invoice
        invoice_val = "FACT-001-TEST"
        study.invoice_number = invoice_val
        study.paid_at = datetime.now()
        study.status = "paid"
        
        db.commit()
        db.refresh(study)
        
        # Verify
        if study.invoice_number == invoice_val:
            print(f"[OK] Invoice Number '{study.invoice_number}' saved successfully.")
        else:
            print(f"[FAIL] Invoice Number verification failed. Got: {study.invoice_number}")
            
    except Exception as e:
        print(f"[FAIL] Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_invoice()
