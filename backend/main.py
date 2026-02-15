from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends, status
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import json
import pandas as pd
import io
import os
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel
import re

def parse_messy_time(text):
    if not text or not isinstance(text, str):
        return None
    
    text = text.lower().strip()
    
    # regex patterns
    # Pattern 1: Range "9-10 am" or "10-11am" -> Take first
    match_range = re.search(r'(\d{1,2})[:\.]?(\d{2})?\s*-\s*\d{1,2}[:\.]?(\d{2})?\s*([ap][\.,]?\s*m?\.?)', text)
    if match_range:
        hour = int(match_range.group(1))
        minute = int(match_range.group(2)) if match_range.group(2) else 0
        ampm_raw = match_range.group(4).lower().replace('.', '').replace(',', '').strip()
        ampm = 'pm' if 'p' in ampm_raw else 'am'
        return convert_to_iso(hour, minute, ampm)

    # Pattern 2: "Despues de 2 pm", "A la 1 pm", "Tipo 4 pm", "2:00 pm", "2 pm"
    match_time = re.search(r'(\d{1,2})[:\.]?(\d{2})?\s*([ap][\.,]?\s*m?\.?)', text)
    if match_time:
        hour = int(match_time.group(1))
        minute = int(match_time.group(2)) if match_time.group(2) else 0
        ampm_raw = match_time.group(3).lower().replace('.', '').replace(',', '').strip()
        ampm = 'pm' if 'p' in ampm_raw else 'am'
        return convert_to_iso(hour, minute, ampm)

    return None

def convert_to_iso(hour, minute, ampm):
    if ampm == 'pm' and hour < 12:
        hour += 12
    if ampm == 'am' and hour == 12:
        hour = 0
    
    # Return today with this time
    now = datetime.now()
    try:
        dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return dt.isoformat()
    except:
        return None


from fastapi.staticfiles import StaticFiles

from . import models, database, auth

# Determine the directory of the current file to build absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Frontend is sibling to backend
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup: Create Tables & Seed Users
@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    
    # Default users to create
    default_users = [
        {"username": "admin", "password": "admin123", "role": "superuser"},
        {"username": "1032509485", "password": "1032509485", "role": "agent"},
        {"username": "agente1", "password": "agente123", "role": "agent"},
        {"username": "agente2", "password": "agente123", "role": "agent"},
        {"username": "coordinador", "password": "coordinador123", "role": "coordinator"},
    ]
    
    try:
        for user_data in default_users:
            user = db.query(models.User).filter(models.User.username == user_data["username"]).first()
            if not user:
                hashed = auth.get_password_hash(user_data["password"])
                db_user = models.User(
                    username=user_data["username"], 
                    hashed_password=hashed, 
                    role=user_data["role"]
                )
                db.add(db_user)
                print(f"Created user: {user_data['username']} ({user_data['role']})")
            else:
                # Ensure role and password are correct for admin
                if user.username == "admin":
                    hashed = auth.get_password_hash("admin123")
                    if user.hashed_password != hashed: # Note: this check might fail due to salt. Better to just update.
                         user.hashed_password = hashed
                         print("Reset admin password to default")
                
                if user.role != user_data["role"]:
                    user.role = user_data["role"]
                    print(f"Updated role for {user_data['username']} to {user_data['role']}")
        
        db.commit()
        print("User initialization complete")
    except Exception as e:
        print(f"Error during user initialization: {e}")
        db.rollback()
    finally:
        db.close()

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

class UserCreate(BaseModel):
    username: str
    password: str
    role: str # superuser, supervisor, agent
    full_name: Optional[str] = None
    bank: Optional[str] = None
    account_type: Optional[str] = None
    account_number: Optional[str] = None
    birth_date: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    blood_type: Optional[str] = None
    account_holder: Optional[str] = None
    account_holder_cc: Optional[str] = None

# --- DEBUG ENDPOINTS ---
@app.get("/debug/reset-admin")
def debug_reset_admin(db: Session = Depends(database.get_db)):
    try:
        user = db.query(models.User).filter(models.User.username == "admin").first()
        hashed = auth.get_password_hash("admin123")
        if not user:
             user = models.User(username="admin", hashed_password=hashed, role="superuser")
             db.add(user)
             msg = "Created admin user"
        else:
             user.hashed_password = hashed
             user.role = "superuser"
             msg = "Updated admin user"
        db.commit()
        return {"status": "success", "message": f"{msg}: Password set to 'admin123'"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/migrate-db")
def debug_migrate_db(db: Session = Depends(database.get_db)):
    """
    Manually add missing columns to users table if they don't exist.
    Specific for MySQL/Postgres where auto-migration didn't run.
    """
    from sqlalchemy import text
    
    # Columns to check/add
    # (name, type)
    columns_users = [
        ("full_name", "VARCHAR(100)"),
        ("bank", "VARCHAR(50)"),
        ("account_type", "VARCHAR(20)"),
        ("account_number", "VARCHAR(50)"),
        ("birth_date", "VARCHAR(20)"),
        ("phone_number", "VARCHAR(20)"),
        ("address", "VARCHAR(200)"),
        ("city", "VARCHAR(100)"),
        ("neighborhood", "VARCHAR(100)"),
        ("blood_type", "VARCHAR(10)"),
        ("account_holder", "VARCHAR(100)"),
        ("account_holder_cc", "VARCHAR(20)")
    ]
    
    # Columns for bizage_studies
    columns_studies = [
        ("study_type", "VARCHAR(50)"),
        ("study_name", "VARCHAR(100)"),
        ("n_value", "INTEGER"),
        ("survey_no_participa", "VARCHAR(200)"),
        ("quantity", "INTEGER"),
        ("price", "INTEGER"),
        ("copies", "INTEGER"),
        ("copies_price", "INTEGER"),
        ("vinipel", "INTEGER"),
        ("vinipel_price", "INTEGER"),
        ("other_cost_description", "VARCHAR(200)"),
        ("other_cost_amount", "INTEGER"),
        ("census", "VARCHAR(100)"),
        ("bizagi_number", "VARCHAR(50)"),
        ("status", "VARCHAR(50) DEFAULT 'registered'"),
        ("registered_at", "DATETIME"),
        ("registered_by", "VARCHAR(50)"),
        ("radicated_at", "DATETIME"),
        ("radicated_by", "VARCHAR(50)"),
        ("bizagi_at", "DATETIME"),
        ("bizagi_by", "VARCHAR(50)"),
        ("paid_at", "DATETIME"),
        ("paid_by", "VARCHAR(50)"),
        ("invoice_number", "VARCHAR(50)")
    ]

    # Payroll Period Columns
    columns_payroll_periods = [
        ("study_code", "VARCHAR(50)"),
        ("is_visible", "BOOLEAN DEFAULT TRUE"),
        ("rates_snapshot", "VARCHAR(500)"),
        ("study_type", "VARCHAR(50)")
    ]

    # Payroll Record Columns
    columns_payroll_records = [
        ("details_json", "TEXT"), # MySQL TEXT
        ("total_censuses", "INTEGER DEFAULT 0"),
        ("total_effective", "INTEGER DEFAULT 0"),
        ("total_amount", "INTEGER DEFAULT 0")
    ]
    
    results = []
    
    # Migrate Users
    for col_name, col_type in columns_users:
        try:
            sql = text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            db.execute(sql)
            results.append(f"Added {col_name} to users")
        except Exception as e:
            results.append(f"Skipped {col_name} in users")

    # Migrate Bizage Studies
    for col_name, col_type in columns_studies:
        try:
            sql = text(f"ALTER TABLE bizage_studies ADD COLUMN {col_name} {col_type}")
            db.execute(sql)
            results.append(f"Added {col_name} to bizage_studies")
        except Exception as e:
            results.append(f"Skipped {col_name} in bizage_studies")

    # Migrate Payroll Periods
    for col_name, col_type in columns_payroll_periods:
        try:
            sql = text(f"ALTER TABLE payroll_periods ADD COLUMN {col_name} {col_type}")
            db.execute(sql)
            results.append(f"Added {col_name} to payroll_periods")
        except Exception as e:
             results.append(f"Skipped {col_name} in payroll_periods")
             
    # Migrate Payroll Records
    for col_name, col_type in columns_payroll_records:
        try:
            sql = text(f"ALTER TABLE payroll_records ADD COLUMN {col_name} {col_type}")
            db.execute(sql)
            results.append(f"Added {col_name} to payroll_records")
        except Exception as e:
             results.append(f"Skipped {col_name} in payroll_records")

    try:
        db.commit()
    except Exception as e:
        return {"status": "error", "message": f"Commit failed: {str(e)}", "details": results}

    return {"status": "completed", "results": results}

# --- AUTH ENDPOINTS ---

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@app.get("/users/me")
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return {
        "username": current_user.username,
        "role": current_user.role,
        "id": current_user.id,
        "full_name": current_user.full_name,
        "address": current_user.address,
        "city": current_user.city
    }

@app.post("/users/heartbeat")
async def heartbeat(current_user: models.User = Depends(auth.get_current_user)):
    """Simple endpoint to trigger auth and update last_seen"""
    return {"status": "alive", "last_seen": current_user.last_seen}

@app.get("/users/status")
def get_users_status(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Allowed for all authenticated users to see who is online
    # if current_user.role != "superuser" and current_user.role != "auxiliar":
    #      raise HTTPException(status_code=403, detail="Not authorized")
         
    users = db.query(models.User).all()
    # Return simplifed list for monitoring
    return [{
        "username": u.username,
        "full_name": u.full_name,
        "role": u.role,
        "last_seen": u.last_seen
    } for u in users]

@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    print(f"DEBUG: create_user received: {user.dict()}")
    
    # Check if user exists
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username, 
        hashed_password=hashed_password, 
        role=user.role,
        full_name=user.full_name,
        bank=user.bank,
        account_type=user.account_type,
        account_number=user.account_number,
        birth_date=user.birth_date,
        phone_number=user.phone_number,
        address=user.address,
        city=user.city,
        neighborhood=user.neighborhood,
        blood_type=user.blood_type,
        account_holder=user.account_holder,
        account_holder_cc=user.account_holder_cc
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {
        "username": db_user.username, 
        "role": db_user.role, 
        "id": db_user.id,
        "full_name": db_user.full_name,
        "address": db_user.address,
        "city": db_user.city,
        "neighborhood": db_user.neighborhood,
        "blood_type": db_user.blood_type,
        "account_holder": db_user.account_holder,
        "account_holder_cc": db_user.account_holder_cc
    }

class UserUpdate(BaseModel):
    # All fields optional for update
    password: Optional[str] = None
    role: Optional[str] = None
    full_name: Optional[str] = None
    bank: Optional[str] = None
    account_type: Optional[str] = None
    account_number: Optional[str] = None
    birth_date: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    blood_type: Optional[str] = None
    account_holder: Optional[str] = None
    account_holder_cc: Optional[str] = None

@app.put("/users/{user_id}")
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Update fields if provided
    if user_update.password:
        db_user.hashed_password = auth.get_password_hash(user_update.password)
    if user_update.role:
        db_user.role = user_update.role
    if user_update.full_name is not None:
        db_user.full_name = user_update.full_name
    if user_update.bank is not None:
        db_user.bank = user_update.bank
    if user_update.account_type is not None:
        db_user.account_type = user_update.account_type
    if user_update.account_number is not None:
        db_user.account_number = user_update.account_number
    if user_update.birth_date is not None:
        db_user.birth_date = user_update.birth_date
    if user_update.phone_number is not None:
        db_user.phone_number = user_update.phone_number
    if user_update.address is not None:
        db_user.address = user_update.address
    if user_update.city is not None:
        db_user.city = user_update.city
    if user_update.neighborhood is not None:
        db_user.neighborhood = user_update.neighborhood
    if user_update.blood_type is not None:
        db_user.blood_type = user_update.blood_type
    if user_update.account_holder is not None:
        db_user.account_holder = user_update.account_holder
    if user_update.account_holder_cc is not None:
        db_user.account_holder_cc = user_update.account_holder_cc
        
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users")
def list_users(exclude_roles: Optional[str] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser" and current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(models.User)
    
    if exclude_roles:
        # Split by comma and strip
        roles_to_exclude = [r.strip().lower() for r in exclude_roles.split(',')]
        # In SQL, we use NOT IN. But SQLAlchemy filter might need care with casing if DB is case sensitive.
        # Assuming lowercase stored or case-insensitive collation. 
        # Safer to fetch all and filter in python if list is small, OR use nice IN clause.
        # Users list is small (<1000 usually). filtering in python is fine and allows complex logic (like fuzzy match).
        # But let's try SQL method for standard logic.
        query = query.filter(models.User.role.not_in(roles_to_exclude))
        
    users = query.all()
    
    # Double check filter in python for casing safety if SQL collation is strict
    if exclude_roles:
        roles_to_exclude = [r.strip().lower() for r in exclude_roles.split(',')]
        users = [u for u in users if (u.role or '').strip().lower() not in roles_to_exclude]

    return [{
        "username": u.username, 
        "role": u.role, 
        "id": u.id,
        "full_name": u.full_name,
        "bank": u.bank,
        "account_type": u.account_type,
        "account_number": u.account_number,
        "birth_date": u.birth_date,
        "phone_number": u.phone_number,
        "address": u.address,
        "city": u.city,
        "neighborhood": u.neighborhood,
        "blood_type": u.blood_type,
        "account_holder": u.account_holder,
        "account_holder_cc": u.account_holder_cc
    } for u in users]

@app.get("/debug/user-count")
def debug_user_count(db: Session = Depends(database.get_db)):
    """Public endpoint to check if users were created"""
    count = db.query(models.User).count()
    users = db.query(models.User).all()
    return {
        "total_users": count,
        "usernames": [u.username for u in users]
    }

@app.get("/debug/reset-admin")
def debug_reset_admin(db: Session = Depends(database.get_db)):
    """Temporary endpoint to force reset admin password"""
    try:
        user = db.query(models.User).filter(models.User.username == "admin").first()
        hashed_pwd = "$2b$12$JGM4KHyZ5kQGg.4HejqX2Ov545baXJkLphOSmkPQCILbXokU0VdBG" # admin123
        
        if user:
            user.hashed_password = hashed_pwd
            user.role = "superuser"
            action = "updated"
        else:
            user = models.User(username="admin", hashed_password=hashed_pwd, role="superuser")
            db.add(user)
            action = "created"
            
        db.commit()
        return {"status": "success", "message": f"Admin user {action} successfully", "username": "admin"}
    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}

@app.get("/debug/check-admin")
def debug_check_admin(db: Session = Depends(database.get_db)):
    """Check admin user details"""
    try:
        user = db.query(models.User).filter(models.User.username == "admin").first()
        if user:
            return {
                "username": user.username,
                "role": user.role,
                "hash_length": len(user.hashed_password) if user.hashed_password else 0,
                "hash_preview": user.hashed_password[:50] if user.hashed_password else None
            }
        return {"error": "Admin not found"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/test-verify")
def debug_test_verify(db: Session = Depends(database.get_db)):
    """Test password verification"""
    try:
        user = db.query(models.User).filter(models.User.username == "admin").first()
        if not user:
            return {"error": "Admin not found"}
        
        # Test verification
        test_password = "admin123"
        try:
            result = auth.verify_password(test_password, user.hashed_password)
            return {
                "verification_result": result,
                "password_tested": test_password,
                "hash_used": user.hashed_password[:50]
            }
        except Exception as verify_error:
            return {"verification_error": str(verify_error)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/migrate-db")
def debug_migrate_db(db: Session = Depends(database.get_db)):
    """Run migrations to add missing columns to users, studies, and calls tables"""
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(db.get_bind())
        log = []

        # --- USERS MIGRATION ---
        existing_user_cols = [c['name'] for c in inspector.get_columns('users')]
        new_user_cols = [
            ("last_seen", "DATETIME"),  # ← MISSING!
            ("full_name", "VARCHAR(100)"),
            ("bank", "VARCHAR(50)"),
            ("account_type", "VARCHAR(20)"),
            ("account_number", "VARCHAR(50)"),
            ("birth_date", "VARCHAR(20)"),
            ("phone_number", "VARCHAR(20)"),
            ("address", "VARCHAR(200)"),
            ("city", "VARCHAR(100)"),
            ("neighborhood", "VARCHAR(100)"),  # ← MISSING!
            ("blood_type", "VARCHAR(10)"),  # ← MISSING!
            ("account_holder", "VARCHAR(100)"),  # ← MISSING!
            ("account_holder_cc", "VARCHAR(20)"),  # ← MISSING!
        ]
        
        for col, dtype in new_user_cols:
            if col not in existing_user_cols:
                try:
                    db.execute(text(f"ALTER TABLE users ADD COLUMN {col} {dtype}"))
                    log.append(f"Added column {col} to users")
                except Exception as e:
                    log.append(f"Failed to add {col} to users: {str(e)}")
            else:
                log.append(f"Column {col} already exists in users")

        # --- STUDIES MIGRATION ---
        existing_study_cols = [c['name'] for c in inspector.get_columns('studies')]
        new_study_cols = [
            ("study_type", "VARCHAR(50)"),
            ("stage", "VARCHAR(20)"),  # ← Changed from VARCHAR(10) to match models.py
            ("is_active", "BOOLEAN DEFAULT 1"),  # ← MISSING!
        ]

        for col, dtype in new_study_cols:
            if col not in existing_study_cols:
                try:
                    db.execute(text(f"ALTER TABLE studies ADD COLUMN {col} {dtype}"))
                    log.append(f"Added column {col} to studies")
                except Exception as e:
                    log.append(f"Failed to add {col} to studies: {str(e)}")
            else:
                log.append(f"Column {col} already exists in studies")

        # --- CALLS MIGRATION ---
        existing_call_cols = [c['name'] for c in inspector.get_columns('calls')]
        new_call_cols = [
            # Contact info
            ("person_name", "VARCHAR(100)"),
            ("city", "VARCHAR(100)"),
            ("census", "VARCHAR(50)"),
            ("observation", "VARCHAR(500)"),
            ("product_brand", "VARCHAR(100)"),
            ("initial_observation", "VARCHAR(500)"),
            ("appointment_time", "DATETIME"),
            ("extra_phone", "VARCHAR(20)"),
            ("corrected_phone", "VARCHAR(20)"),
            ("person_cc", "VARCHAR(20)"),
            ("updated_at", "DATETIME"),
            # Census / Demographic Data - THESE WERE MISSING!
            ("nse", "VARCHAR(50)"),
            ("age", "VARCHAR(20)"),
            ("age_range", "VARCHAR(50)"),
            ("children_age", "VARCHAR(200)"),
            ("whatsapp", "VARCHAR(50)"),
            ("neighborhood", "VARCHAR(200)"),
            ("address", "VARCHAR(300)"),
            ("housing_description", "VARCHAR(300)"),
            ("respondent", "VARCHAR(100)"),
            ("supervisor", "VARCHAR(100)"),
            ("implantation_date", "VARCHAR(50)"),
            ("collection_date", "VARCHAR(50)"),
            ("collection_time", "VARCHAR(50)"),
        ]

        for col, dtype in new_call_cols:
            if col not in existing_call_cols:
                try:
                    db.execute(text(f"ALTER TABLE calls ADD COLUMN {col} {dtype}"))
                    log.append(f"Added column {col} to calls")
                except Exception as e:
                    log.append(f"Failed to add {col} to calls: {str(e)}")
            else:
                log.append(f"Column {col} already exists in calls")

        # --- CALLS MIGRATION (PART 2) ---
        new_call_cols_2 = [
            ("realization_date", "DATETIME"),
            ("temp_armando", "TEXT"),
            ("temp_auxiliar", "TEXT"),
            ("previous_user_id", "INTEGER"),
            ("dog_name", "VARCHAR(100)"),
            ("dog_user_type", "VARCHAR(50)"),
            ("stool_texture", "VARCHAR(200)"),
            ("health_status", "VARCHAR(200)"),
            ("second_collection_date", "VARCHAR(50)"),
            ("second_collection_time", "VARCHAR(50)"),
            ("shampoo_quantity", "VARCHAR(50)"),
            ("shampoo_brand", "VARCHAR(100)"),
            ("shampoo_variety", "VARCHAR(100)"),
            ("conditioner_brand", "VARCHAR(100)"),
            ("conditioner_variety", "VARCHAR(100)"),
            ("treatment_brand", "VARCHAR(100)"),
            ("treatment_variety", "VARCHAR(100)"),
            ("wash_frequency", "VARCHAR(100)"),
            ("hair_type", "VARCHAR(50)"),
            ("hair_shape", "VARCHAR(50)"),
            ("hair_length", "VARCHAR(50)"),
            ("purchase_frequency", "VARCHAR(100)"),
            ("implantation_pollster", "VARCHAR(100)"),
            ("dog_breed", "VARCHAR(100)"),
            ("dog_size", "VARCHAR(50)")
        ]

        for col, dtype in new_call_cols_2:
            if col not in existing_call_cols:
                try:
                    db.execute(text(f"ALTER TABLE calls ADD COLUMN {col} {dtype}"))
                    log.append(f"Added column {col} to calls")
                except Exception as e:
                    log.append(f"Failed to add {col} to calls: {str(e)}")
            else:
                log.append(f"Column {col} already exists in calls")
                

                
        # --- PAYROLL MIGRATION ---
        # Ensure payroll_periods has the new columns for Study Liquidation
        if inspector.has_table("payroll_periods"):
            existing_rr_cols = [c['name'] for c in inspector.get_columns('payroll_periods')]
            new_rr_cols = [
                ("study_type", "VARCHAR(50)"),
                ("rates_snapshot", "TEXT"), # JSON
                ("execution_date", "DATETIME"),
                ("study_id", "INTEGER"), # If missing
                ("start_date", "DATETIME"),
                ("end_date", "DATETIME")
            ]
            for col, dtype in new_rr_cols:
                if col not in existing_rr_cols:
                    try:
                        db.execute(text(f"ALTER TABLE payroll_periods ADD COLUMN {col} {dtype}"))
                        log.append(f"Added column {col} to payroll_periods")
                    except Exception as e:
                        log.append(f"Failed to add {col} to payroll_periods: {str(e)}")
        
        db.commit()
        return {"status": "migration completed", "log": log}
    except Exception as e:
        return {"error": str(e)}



@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.delete(user)
    db.commit()
    return {"status": "ok"}

@app.delete("/studies/{study_id}")
def delete_study(study_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser" and current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    study = db.query(models.Study).filter(models.Study.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
        
    # Delete associated calls first
    db.query(models.Call).filter(models.Call.study_id == study_id).delete()
    
    # Delete study
    db.delete(study)
    db.commit()
    
    return {"message": "Study deleted successfully"}

class UserPasswordReset(BaseModel):
    new_password: str

@app.put("/users/{user_id}/password")
def reset_user_password(user_id: int, reset: UserPasswordReset, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = auth.get_password_hash(reset.new_password)
    db.commit()
    return {"status": "password updated"}

class UserSelfPasswordUpdate(BaseModel):
    old_password: str
    new_password: str

@app.put("/users/me/password")
def change_own_password(update: UserSelfPasswordUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not auth.verify_password(update.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    current_user.hashed_password = auth.get_password_hash(update.new_password)
    db.commit()
    return {"status": "password updated"}

@app.get("/users-page")
def users_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "users.html"))


# --- PAGE ROUTES ---

@app.get("/")
def read_root():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

@app.get("/login")
def login_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/validator-page")
def validator_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/call-center-page")
def call_center_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "call_center.html"))

@app.get("/bizage-page")
def bizage_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "bizage.html"))

# --- CALL CENTER API ---

class StudyCreate(BaseModel):
    code: str
    name: str

@app.post("/studies")
def create_study(study: StudyCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser" and current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Not authorized")
    db_study = models.Study(code=study.code, name=study.name)
    db.add(db_study)
    db.commit()
    db.refresh(db_study)
    return db_study

@app.get("/studies")
def get_studies(include_inactive: bool = False, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    query = db.query(models.Study)
    
    # SIMPLIFIED LOGIC requested by user:
    # If Superuser/Coordinator -> Return ALL (Active + Inactive) always.
    # If Regular User -> Return ONLY Active.
    if current_user.role.lower() in ["superuser", "coordinator"]:
        pass # No filter, return everything
    else:
        query = query.filter(models.Study.is_active == True)
    
    # AUXILIAR Filter: Only see assigned studies
    if current_user.role == "auxiliar":
        query = query.join(models.study_assignments).filter(models.study_assignments.c.user_id == current_user.id)
        
    studies = query.all()
    # Explicitly return dict to ensure is_active is available on frontend
    return [{
        "id": s.id,
        "code": s.code,
        "name": s.name,
        "is_active": s.is_active,
        "status": s.status,
        "study_type": s.study_type,
        "stage": s.stage
    } for s in studies]

class AssistantAssignment(BaseModel):
    user_ids: List[int]

@app.post("/studies/{study_id}/assistants")
def assign_study_assistants(study_id: int, assignment: AssistantAssignment, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser" and current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    study = db.query(models.Study).filter(models.Study.id == study_id).first()
    if not study:
         raise HTTPException(status_code=404, detail="Study not found")

    # Clear existing and assigned new
    # Get users
    users = db.query(models.User).filter(models.User.id.in_(assignment.user_ids)).all()
    study.assistants = users
    db.commit()
    return {"status": "updated", "count": len(users)}

@app.get("/studies/{study_id}/assistants")
def get_study_assistants(study_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser" and current_user.role != "coordinator":
         raise HTTPException(status_code=403, detail="Not authorized")
         
    study = db.query(models.Study).filter(models.Study.id == study_id).first()
    if not study:
         raise HTTPException(status_code=404, detail="Study not found")
         
    return [{"id": u.id, "username": u.username, "full_name": u.full_name, "role": u.role} for u in study.assistants]

@app.put("/studies/{study_id}/toggle")
def toggle_study_status(study_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser" and current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    study = db.query(models.Study).filter(models.Study.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
        
    # Toggle
    study.is_active = not study.is_active
    db.commit()
    
    status_str = "active" if study.is_active else "inactive"
    return {"status": "updated", "new_state": status_str, "is_active": study.is_active}

@app.post("/studies/{study_id}/duplicate-r2")
def duplicate_study_r2(study_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser" and current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    source_study = db.query(models.Study).filter(models.Study.id == study_id).first()
    if not source_study:
        raise HTTPException(status_code=404, detail="Source study not found")

    # 1. Generate New Name & Code
    # Logic: Look for "R1", replace with "R2". If no "R" pattern, append "R2"
    # Or just increment if R<N> found.
    
    new_name = source_study.name
    import re
    match = re.search(r'(R)(\d+)', new_name)
    
    new_stage = source_study.stage # Default to same if no logic
    
    if match:
        prefix = match.group(1) # R
        number = int(match.group(2))
        new_number = number + 1
        new_name = re.sub(r'R\d+', f'R{new_number}', new_name)
        new_stage = f"R{new_number}"
    else:
        new_name = f"{new_name} - R2"
        new_stage = "R2"
        
    start_code = source_study.code.split('_')[0] if '_' in source_study.code else source_study.code
    import random
    new_code = f"{start_code}_{random.randint(100,999)}"

    # 2. Create the New Study
    new_study = models.Study(
        code=new_code,
        name=new_name,
        study_type=source_study.study_type,
        stage=new_stage,
        is_active=True, 
        status="open"
    )
    db.add(new_study)
    db.commit() # Commit to get ID
    
    # 3. Filter Calls (Managed/Effective Only)
    # The user strictly said: "solo pasarian las Efectivas (antes gestionadas) pendientes, caidas y demas no pasarian"
    # We include: 'managed' (Efectiva), 'efectiva_campo' (Efectiva Presencial), 'done' (Terminado - usually implies done)
    # Exclude: pending, scheduled, caidas (all types)
    
    target_statuses = ['managed', 'efectiva_campo', 'done']
    
    source_calls = db.query(models.Call).filter(
        models.Call.study_id == study_id,
        models.Call.status.in_(target_statuses)
    ).all()
    
    count = 0
    new_calls = []
    
    # 4. Duplicate Calls
    for c in source_calls:
        # Create new call instance copying relevant data
        new_call = models.Call(
            study_id=new_study.id,
            status='pending', # Reset to Pending
            
            # Contact Info
            phone_number=c.phone_number,
            corrected_phone=c.corrected_phone,
            extra_phone=c.extra_phone,
            whatsapp=c.whatsapp,
            
            # Person Info
            person_name=c.person_name,
            person_cc=c.person_cc,
            city=c.city,
            neighborhood=c.neighborhood,
            address=c.address,
            
            # Census / Demographics (Keep these so they don't have to re-enter)
            census=c.census,
            nse=c.nse,
            age=c.age,
            age_range=c.age_range,
            children_age=c.children_age,
            housing_description=c.housing_description,
            
            # Products / Study Data (Presumably they keep the same product?)
            product_brand=c.product_brand,
            
            # Hair Data
            shampoo_quantity=c.shampoo_quantity, # Keep quantity they had?
            shampoo_brand=c.shampoo_brand,
            shampoo_variety=c.shampoo_variety,
            conditioner_brand=c.conditioner_brand,
            conditioner_variety=c.conditioner_variety,
            treatment_brand=c.treatment_brand,
            treatment_variety=c.treatment_variety,
            wash_frequency=c.wash_frequency,
            hair_type=c.hair_type,
            hair_shape=c.hair_shape,
            hair_length=c.hair_length,
            purchase_frequency=c.purchase_frequency,
            
            # Dog Data
            dog_name=c.dog_name,
            dog_user_type=c.dog_user_type,
            
            # Dog Data
            # dog_name=c.dog_name, # Already included above
            # dog_user_type=c.dog_user_type, # Already included above
            
            # Map Second Collection Date -> Collection Date/Time (Hora Original)
            # User Request: "que esas tome la fecha origianl como la de second_collection_date"
            collection_date=c.second_collection_date, # Assuming it's already a string "DD/MM/YYYY" or similar
            collection_time=c.second_collection_time, # Map time too if available
            initial_observation=f"R+ generado desde {c.study.name}. Fecha 2 Recogida anterior: {c.second_collection_date or 'N/A'}"
        )
        new_calls.append(new_call)
        count += 1
        
    if new_calls:
        db.bulk_save_objects(new_calls)
        db.commit()
        
    return {
        "status": "success", 
        "new_study_id": new_study.id, 
        "new_study_name": new_study.name,
        "count": count
    }

class CallCreate(BaseModel):
    study_id: int
    phone_number: str
    person_cc: Optional[str] = None
    corrected_phone: Optional[str] = None

@app.post("/calls")
def create_call(call: CallCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_call = models.Call(**call.dict())
    db.add(db_call)
    db.commit()
    db.refresh(db_call)
    return db_call

@app.get("/calls")
def get_calls(study_id: Optional[int] = None, study_is_active: Optional[bool] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Join with Study to get status and name
    query = db.query(models.Call).join(models.Study)
    
    if study_id:
        query = query.filter(models.Call.study_id == study_id)
        # VISIBILITY LOGIC:
        if current_user.role != "superuser" and current_user.role != "auxiliar" and current_user.role != "coordinator":
             query = query.filter(models.Call.status.in_(["pending", "scheduled"]))
             query = query.filter(models.Call.user_id == current_user.id) # Only assigned
    else:
        # GLOBAL VIEW
        
        # Determine if we want active or inactive studies
        # Default to True (Active) for backward compatibility if not specified
        target_active = True if study_is_active is None else study_is_active
        
        query = query.filter(models.Study.is_active == target_active)
        
        # Only require "open" status if we are looking for ACTIVE studies
        if target_active:
             query = query.filter(models.Study.status == "open")
        
        if current_user.role != "superuser" and current_user.role != "auxiliar" and current_user.role != "coordinator":
            query = query.filter(models.Call.status.in_(["pending", "scheduled"]))
            query = query.filter(models.Call.user_id == current_user.id) # Only assigned
        
        # Auxiliar restriction: Only calls from assigned studies (if global view)
        if current_user.role == "auxiliar":
             # We need to filter studies where user is assistant
             # Using EXISTS or JOIN
             query = query.join(models.study_assignments, models.Study.id == models.study_assignments.c.study_id)\
                          .filter(models.study_assignments.c.user_id == current_user.id)


    # Order by ID desc
    query = query.order_by(models.Call.id.desc())
    
    # We need to return study name too. 
    # Current models.Call serialization might not include study name unless we use Pydantic schemas with ORM mode
    # Let's verify what `query.all()` returns. It returns Call objects.
    # We can rely on frontend fetching study name if we return a custom dict, or just include it.
    # Quick fix: return list of dicts with study_name
    
    calls = query.all()
    result = []
    for c in calls:
        c_dict = c.__dict__.copy()
        if 'study' in c_dict: del c_dict['study'] # Remove relationship obj
        if 'user' in c_dict: del c_dict['user'] # Remove relationship obj
        if '_sa_instance_state' in c_dict: del c_dict['_sa_instance_state']
        c_dict['study_name'] = c.study.name if c.study else None
        c_dict['study_type'] = c.study.study_type if c.study else None
        c_dict['study_stage'] = c.study.stage if c.study else None
        # Prefer Full Name, fallback to username
        c_dict['agent_name'] = (c.user.full_name if c.user.full_name else c.user.username) if c.user else None
        
        # Ensure new fields are in dict (if not auto-included by __dict__)
        c_dict['realization_date'] = c.realization_date.isoformat() if c.realization_date else None
        c_dict['temp_armando'] = c.temp_armando
        c_dict['temp_auxiliar'] = c.temp_auxiliar
        c_dict['dog_name'] = c.dog_name
        c_dict['dog_name'] = c.dog_name
        c_dict['dog_breed'] = c.dog_breed
        c_dict['dog_size'] = c.dog_size
        c_dict['dog_user_type'] = c.dog_user_type
        c_dict['stool_texture'] = c.stool_texture
        c_dict['health_status'] = c.health_status
        c_dict['second_collection_date'] = c.second_collection_date
        c_dict['second_collection_time'] = c.second_collection_time
        c_dict['second_collection_time'] = c.second_collection_time
        c_dict['shampoo_quantity'] = c.shampoo_quantity

        # Hair Fields
        c_dict['shampoo_brand'] = c.shampoo_brand
        c_dict['shampoo_variety'] = c.shampoo_variety
        c_dict['conditioner_brand'] = c.conditioner_brand
        c_dict['conditioner_variety'] = c.conditioner_variety
        c_dict['treatment_brand'] = c.treatment_brand
        c_dict['treatment_variety'] = c.treatment_variety
        c_dict['wash_frequency'] = c.wash_frequency
        c_dict['hair_type'] = c.hair_type
        c_dict['hair_shape'] = c.hair_shape
        c_dict['hair_length'] = c.hair_length
        c_dict['code'] = c.code # Ensure Code is sent
        
        # Previous Agent Name
        c_dict['previous_agent_name'] = (c.previous_user.full_name if c.previous_user.full_name else c.previous_user.username) if c.previous_user else None
        
        # Get last 4 observations
        # Sort by ID descending (newest first) and take top 4
        # Note: This relies on lazy loading. For high scale, use joinedload/subqueryload.
        if c.observations:
            sorted_obs = sorted(c.observations, key=lambda x: x.id, reverse=True)[:4]
            c_dict['last_observations'] = [f"{o.text} ({o.created_at.strftime('%Y-%m-%d %H:%M') if o.created_at else ''})" for o in sorted_obs]
        else:
            c_dict['last_observations'] = []
            
        result.append(c_dict)
        
    return result

class AssignCall(BaseModel):
    user_id: int

@app.put("/calls/{call_id}/assign")
def assign_call(call_id: int, assignment: AssignCall, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser" and current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    call = db.query(models.Call).filter(models.Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # Check if call is already managed or dropped/failed
    # We restrict assignment for these statuses as requested
    restricted_statuses = [
        "managed", "done", "efectiva_campo", 
        "caida_desempeno", "caida_logistica", 
        "caida_desempeno_campo", "caida_logistico_campo", 
        "caidas", "caida" # Legacy
    ]
    
    if call.status in restricted_statuses:
         raise HTTPException(status_code=400, detail=f"No se puede reasignar una llamada con estado '{call.status}'")
    
    # Check user exists
    user = db.query(models.User).filter(models.User.id == assignment.user_id).first()
    if not user:
         raise HTTPException(status_code=404, detail="User not found")
         
    # Save Previous Agent if assignment changes
    if call.user_id and call.user_id != assignment.user_id:
        call.previous_user_id = call.user_id

    call.user_id = assignment.user_id
    db.commit()
    agent_name = user.full_name if user.full_name else user.username
    return {"status": "assigned", "agent": agent_name}

class BulkAssignCall(BaseModel):
    call_ids: List[int]
    user_id: Optional[int] = None # None allows unassignment

@app.put("/calls/assign-bulk")
def assign_call_bulk(assignment: BulkAssignCall, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser" and current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check user exists ONLY if assigning (not unassigning)
    if assignment.user_id is not None:
        user = db.query(models.User).filter(models.User.id == assignment.user_id).first()
        if not user:
             raise HTTPException(status_code=404, detail="User not found")
    
    # Update all
    # Need to do it one by one to save previous_user_id properly
    
    calls = db.query(models.Call).filter(models.Call.id.in_(assignment.call_ids)).all()
    for call in calls:
        if call.user_id: # If previously assigned
             # If we are unassigning (assignment.user_id is None) OR assigning to different user
             if assignment.user_id is None or call.user_id != assignment.user_id:
                  call.previous_user_id = call.user_id
        
        call.user_id = assignment.user_id
        
    db.commit()
    return {"status": "bulk_assigned", "count": len(assignment.call_ids)}

@app.put("/calls/{call_id}/close")
def close_call(call_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    call = db.query(models.Call).filter(models.Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Optional: check if user owns call or is superuser?
    # User said: "el pending, que pueda gestionar a closed". Implies agent can do it.
    
    call.status = "closed"
    db.commit()
    return {"status": "closed"}

class UpdateCallStatus(BaseModel):
    status: str

@app.put("/calls/{call_id}/status")
def update_call_status(call_id: int, status_update: UpdateCallStatus, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    call = db.query(models.Call).filter(models.Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # We could restrict transitions here based on current_user.role if strict security is needed.
    # For now, we trust the frontend logic as per "simple" request, but basic sanity checks are good.
    
    call.status = status_update.status
    
    # Auto-update Realization Date
    # If status is "managed" (Gestionado) or any "caida", set date to Now
    # Also if "done" or "efectiva_campo"
    trigger_statuses = [
        "managed", "done", "efectiva_campo", 
        "caida_desempeno", "caida_logistica", 
        "caida_desempeno_campo", "caida_logistico_campo", 
        "caidas", "caida", "en_campo", "en campo"
    ]
    
    if call.status in trigger_statuses:
        call.realization_date = datetime.now()
        
    db.commit()
    return {"status": call.status, "realization_date": call.realization_date}

class TempInfoUpdate(BaseModel):
    temp_armando: Optional[str] = None
    temp_auxiliar: Optional[str] = None

@app.put("/calls/{call_id}/temp-info")
def update_temp_info(call_id: int, info: TempInfoUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    call = db.query(models.Call).filter(models.Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
        
    # Permission Check
    # temp_armando: Only superuser
    if info.temp_armando is not None:
        if current_user.role != "superuser":
             raise HTTPException(status_code=403, detail="Solo Super Usuario puede editar Temporal Armando")
        call.temp_armando = info.temp_armando

    # temp_auxiliar: Superuser or Auxiliar
    if info.temp_auxiliar is not None:
        if current_user.role != "superuser" and current_user.role != "auxiliar":
             raise HTTPException(status_code=403, detail="No autorizado para editar Temporal Auxiliar")
        call.temp_auxiliar = info.temp_auxiliar
        
    db.commit()
    return {"status": "ok", "temp_armando": call.temp_armando, "temp_auxiliar": call.temp_auxiliar}

@app.post("/upload-calls")
async def upload_calls(
    file: UploadFile = File(...),
    study_name: str = Form(None),
    study_type: str = Form(None), # Added
    study_stage: str = Form(None), # Added
    study_id: int = Form(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Add Logging
    print(f"DEBUG: upload_calls start. Study: {study_name}, Type: {study_type}, Stage: {study_stage}, ID: {study_id}")
    
    try:
        if current_user.role != "superuser" and current_user.role != "coordinator":
            raise HTTPException(status_code=403, detail="Not authorized")
            
        # Ensure study
        if study_id:
            db_study = db.query(models.Study).filter(models.Study.id == study_id).first()
            if not db_study:
                 raise HTTPException(status_code=404, detail="Study not found")
        elif study_name:
            # Create new study
            if not study_type or not study_stage:
                # IMPORTANT: study_type from Form might be "null" string or actual None depending on browser?
                # Javascript FormData with null value usually becomes "null" string or empty string.
                raise HTTPException(status_code=400, detail="Study Type and Stage are required for new studies")
                
            import random
            code = study_name[:4].upper() + str(random.randint(10,99))
            db_study = models.Study(
                code=code, 
                name=study_name,
                study_type=study_type, # Save type
                stage=study_stage      # Save stage
            )
            db.add(db_study)
            db.commit()
            db.refresh(db_study)
        else:
            raise HTTPException(status_code=400, detail="Must provide study_id or study_name")

        # Read File
        print("DEBUG: Reading file...")
        try:
            content = await file.read()
            df = pd.read_excel(io.BytesIO(content))
            print(f"DEBUG: File read. Columns: {df.columns.tolist()}")
        except Exception as e:
            print(f"DEBUG: Excel Error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid Excel file: {str(e)}")

        # Map Columns
        # Expected: Telefono, Ciudad, Observaciones, Hora de llamada, Marca de producto, Otro numero, Cedula, Nombre
        # Normalize headers
        cols = {str(c).strip().lower(): c for c in df.columns}
        
        cols_mapping = {
            "phone_number": ["telefono", "teléfono", "celular", "numero", "movil"],
            "city": ["ciudad", "city"],
            "code": ["codigo", "código", "cod", "id"], # Explicit mapping for Code
            "initial_observation": ["observaciones", "observacion", "observación", "obs"],
            "appointment_time": ["hora de llamada", "hora", "cita"],
            "product_brand": ["marca de producto", "marca"],
            "extra_phone": ["otro numero", "otro telefono", "telefono 2"],
            "person_cc": ["cedula", "cédula", "cc", "id", "identificacion"],
            "person_name": ["nombre", "cliente", "usuario", "nombre y apellido", "nombre completo"],
            # New Census Fields
            "nse": ["nse", "estrato", "nivel socioeconomico"],
            "age": ["edad", "age"],
            "age_range": ["rango edad", "rango de edad", "edad rango"],
            "children_age": ["edad hijos", "hijos", "edades hijos"],
            "whatsapp": ["whatsapp", "whassapp", "wa", "celular wa"],
            "neighborhood": ["barrio", "neighborhood", "sector"],
            "address": ["direccion", "dirección", "address", "dir", "ubicacion"],
            "housing_description": ["descripcion vivienda", "descripción vivienda", "tipo vivienda", "vivienda"],
            "respondent": ["encuestado", "respondent", "persona entrevistada"],
            "supervisor": ["supervisor", "sup"],
            "implantation_date": ["fecha implantacion", "fecha implantación", "fecha imp"],
            "collection_date": ["fecha recoleccion", "fecha recolección", "fecha recogida", "fecha de recogida", "fecha rec"], # Added 'fecha de recogida'
            "collection_time": ["hora recoleccion", "hora recolección", "hora recogida", "hora de recogida", "hora rec"], # Added 'hora de recogida'
            "census": ["censo", "id", "identifier"],
            "code": ["codigo", "código", "cod", "id"], # Explicit mapping for Code
            "implantation_pollster": ["encuestador", "pollster", "nombre encuestador", "implantation_pollster"],

            # Dog Food Study
            "dog_name": ["nombre del perro", "dog name", "mascota", "nombre de la mascota"],
            # ... existing ...

            # Hair Study
            "shampoo_brand": ["marca de shampoo", "marca shampoo"],
            "shampoo_variety": ["variedad shampoo", "variedad"], 
            
            "treatment_brand": ["marca tratamiento"],
            "treatment_variety": ["variedad tratamiento"], 

            "conditioner_brand": ["marca acondicionador"],
            "conditioner_variety": ["variedad acondicionador", "variedad tratamiento.1"], # Prioritize correct name

            "wash_frequency": ["frecuencia de lavado"],
            "hair_type": ["tipo de cabello"],
            "hair_shape": ["forma de cabello"],
            "hair_length": ["largo de cabello", "plargo de cabello", "largo"], # Matches typo in Excel
            
            # Legacy/Unused removed
        }

        calls_to_add = []
        
        # Pre-fetch study_id
        sid = db_study.id
        
        for _, row in df.iterrows():
            # Helper to get value
            # Helper to get value
            def get_val(key):
                nonlocal row
                
                # Helper to find key case-insensitive in row
                def get_row_val_ci(target_key):
                    for rk in row.keys():
                        if str(rk).strip().lower() == target_key.lower():
                            val = row[rk]
                            return str(val).strip() if pd.notna(val) else None
                    return None

                # Standard Logic with CI check for aliases
                possible = cols_mapping.get(key, [])
                for k in possible:
                    # Direct check (CI)
                    res = get_row_val_ci(k)
                    if res is not None: return res
                    
                return None
                
            phone = get_val("phone_number")
            if not phone:
                continue # Skip row without phone
                
            # Safe Date Parsing
            appt_raw = get_val("appointment_time")
            appt_dt = None
            
            # 1. Try smart parser first if it looks like messy text
            if appt_raw:
                parsed_messy = parse_messy_time(appt_raw)
                if parsed_messy:
                   appt_dt = datetime.fromisoformat(parsed_messy)

            # 2. Fallback to pandas standard parser if smart parser returned nothing
            if not appt_dt and appt_raw:
                try:
                    # Use pandas to parse, convert to pydatetime, set to None if NaT
                    ts = pd.to_datetime(appt_raw, errors='coerce')
                    if pd.notna(ts):
                        appt_dt = ts.to_pydatetime()
                except:
                    appt_dt = None
            
            # If still nothing, check "initial_observation" or "collection_time" for clues if requested?
            # User suggested "Observation" might have the time.
            # Let's try to extract from initial_observation if get_val("appointment_time") was empty.
            if not appt_dt and not appt_raw:
                 obs_val = get_val("initial_observation")
                 if obs_val:
                     parsed_obs = parse_messy_time(obs_val)
                     if parsed_obs:
                         appt_dt = datetime.fromisoformat(parsed_obs)

            # Normalize City
            city_raw = get_val("city")
            city_norm = None
            if city_raw:
                import unicodedata
                city_norm = str(city_raw).strip().upper()
                city_norm = "".join(c for c in unicodedata.normalize("NFD", city_norm) if unicodedata.category(c) != "Mn")

            call_obj = models.Call(
                study_id=sid,
                phone_number=phone[:20], # Truncate to fit VARCHAR(20)
                city=city_norm[:100] if city_norm else None,
                initial_observation=get_val("initial_observation")[:500] if get_val("initial_observation") else None,
                appointment_time=appt_dt,
                product_brand=get_val("product_brand")[:100] if get_val("product_brand") else None,
                extra_phone=get_val("extra_phone")[:20] if get_val("extra_phone") else None,
                person_cc=get_val("person_cc")[:20] if get_val("person_cc") else None,
                person_name=get_val("person_name")[:100] if get_val("person_name") else None,
                
                # New Census Fields
                census=get_val("census")[:50] if get_val("census") else None,
                nse=get_val("nse")[:50] if get_val("nse") else None,
                age=get_val("age")[:20] if get_val("age") else None,
                age_range=get_val("age_range")[:50] if get_val("age_range") else None,
                children_age=get_val("children_age")[:200] if get_val("children_age") else None,
                whatsapp=get_val("whatsapp")[:50] if get_val("whatsapp") else None,
                neighborhood=get_val("neighborhood")[:200] if get_val("neighborhood") else None,
                address=get_val("address")[:300] if get_val("address") else None,
                housing_description=get_val("housing_description")[:300] if get_val("housing_description") else None,
                respondent=get_val("respondent")[:100] if get_val("respondent") else None,
                supervisor=get_val("supervisor")[:100] if get_val("supervisor") else None,
                implantation_date=get_val("implantation_date")[:50] if get_val("implantation_date") else None,
                collection_date=get_val("collection_date")[:50] if get_val("collection_date") else None,
                collection_time=get_val("collection_time")[:50] if get_val("collection_time") else None,
                
                # Dog Study Fields
                dog_name=get_val("dog_name")[:100] if get_val("dog_name") else None,
                dog_breed=get_val("dog_breed")[:100] if get_val("dog_breed") else None,
                dog_size=get_val("dog_size")[:50] if get_val("dog_size") else None,
                dog_user_type=get_val("dog_user_type")[:50] if get_val("dog_user_type") else None,
                stool_texture=get_val("stool_texture")[:200] if get_val("stool_texture") else None,
                health_status=get_val("health_status")[:200] if get_val("health_status") else None,

                # New Fields
                second_collection_date=get_val("second_collection_date")[:50] if get_val("second_collection_date") else None,
                second_collection_time=get_val("second_collection_time")[:50] if get_val("second_collection_time") else None,
                shampoo_quantity=get_val("shampoo_quantity")[:50] if get_val("shampoo_quantity") else None,
                implantation_pollster=get_val("implantation_pollster")[:100] if get_val("implantation_pollster") else None,
                
                # Hair
                shampoo_brand=get_val("shampoo_brand")[:100] if get_val("shampoo_brand") else None,
                shampoo_variety=get_val("shampoo_variety")[:100] if get_val("shampoo_variety") else None, 
                conditioner_brand=get_val("conditioner_brand")[:100] if get_val("conditioner_brand") else None,
                conditioner_variety=get_val("conditioner_variety")[:100] if get_val("conditioner_variety") else None,
                
                treatment_brand=get_val("treatment_brand")[:100] if get_val("treatment_brand") else None,
                treatment_variety=get_val("treatment_variety")[:100] if get_val("treatment_variety") else None,
                
                wash_frequency=get_val("wash_frequency")[:100] if get_val("wash_frequency") else None,
                hair_type=get_val("hair_type")[:50] if get_val("hair_type") else None,
                hair_shape=get_val("hair_shape")[:50] if get_val("hair_shape") else None,
                hair_length=get_val("hair_length")[:50] if get_val("hair_length") else None,
                
                code=get_val("code")[:50] if get_val("code") else None,

                status="pending"
            )
            calls_to_add.append(call_obj)
        
        print(f"DEBUG: Found {len(calls_to_add)} calls to add.")
        if calls_to_add:
            db.add_all(calls_to_add)
            db.commit()
            
        return {"status": "ok", "count": len(calls_to_add), "study_id": sid, "study_name": db_study.name}

    except HTTPException as he:
        # Re-raise HTTP exceptions as-is
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Return 500 JSON so frontend catch block can show message
        return JSONResponse(status_code=500, content={"detail": f"Internal Server Error: {str(e)}"})


@app.get("/calls")
def get_calls(study_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    q = db.query(models.Call)
    if study_id:
        q = q.filter(models.Call.study_id == study_id)
    return q.all()

class ObservationCreate(BaseModel):
    text: str

@app.post("/calls/{call_id}/observation")
def add_observation(call_id: int, obs: ObservationCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_obs = models.Observation(
        call_id=call_id, 
        user_id=current_user.id, 
        text=obs.text,
        created_at=datetime.now()
    )
    db.add(db_obs)
    db.commit()
    db.refresh(db_obs)
    return db_obs

@app.get("/calls/{call_id}/observations")
def get_observations(call_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    obs_list = db.query(models.Observation).filter(models.Observation.call_id == call_id).order_by(models.Observation.created_at.desc()).all()
    
    result = []
    for obs in obs_list:
        user_name = obs.user.full_name if obs.user and obs.user.full_name else (obs.user.username if obs.user else "Sistema")
        result.append({
            "id": obs.id,
            "text": obs.text,
            "created_at": obs.created_at,
            "user_name": user_name
        })
    return result

class ScheduleCreate(BaseModel):
    scheduled_time: str # ISO format

@app.post("/calls/{call_id}/schedule")
def schedule_call(call_id: int, sched: ScheduleCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    dt = pd.to_datetime(sched.scheduled_time).to_pydatetime()
    
    # Create Schedule Record (Log)
    db_sched = models.Schedule(call_id=call_id, user_id=current_user.id, scheduled_time=dt)
    db.add(db_sched)
    
    # UPDATE CALL RECORD - KEY FIX
    call = db.query(models.Call).filter(models.Call.id == call_id).first()
    if call:
        call.appointment_time = dt
        call.status = "scheduled" # Update status to reflect scheduling
    
    db.commit()
    return {"status": "ok"}

# --- BIZAGE MODULE API ---

class BizageStudyCreate(BaseModel):
    study_type: str
    study_name: str
    n_value: int
    survey_no_participa: Optional[str] = None
    census: Optional[str] = None

@app.post("/bizage/studies")
def create_bizage_study(study: BizageStudyCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db_study = models.BizageStudy(
        study_type=study.study_type,
        study_name=study.study_name,
        n_value=study.n_value,
        survey_no_participa=study.survey_no_participa,
        registered_by=current_user.username,
        census=study.census,
        registered_at=datetime.now()
    )
    db.add(db_study)
    db.commit()
    db.refresh(db_study)
    return db_study

@app.get("/bizage/studies")
def get_bizage_studies(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser":
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.BizageStudy).order_by(models.BizageStudy.id.desc()).all()

class BizageRadicate(BaseModel):
    quantity: int
    price: int
    copies: Optional[int] = 0
    copies_price: Optional[int] = 0
    vinipel: Optional[int] = 0
    vinipel_price: Optional[int] = 0
    other_cost_description: Optional[str] = None
    other_cost_amount: Optional[int] = 0

@app.put("/bizage/studies/{study_id}/radicate")
def radicate_bizage_study(study_id: int, data: BizageRadicate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    study = db.query(models.BizageStudy).filter(models.BizageStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
        
    study.quantity = data.quantity
    study.price = data.price
    study.copies = data.copies
    study.copies_price = data.copies_price
    study.vinipel = data.vinipel
    study.vinipel_price = data.vinipel_price
    study.other_cost_description = data.other_cost_description
    study.other_cost_amount = data.other_cost_amount
    
    study.status = "radicated"
    study.radicated_at = datetime.now()
    study.radicated_by = current_user.username
    
    db.commit()
    return {"status": "radicated"}

class BizageBizagi(BaseModel):
    bizagi_number: str

@app.put("/bizage/studies/{study_id}/bizagi")
def bizagi_bizage_study(study_id: int, data: BizageBizagi, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    study = db.query(models.BizageStudy).filter(models.BizageStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
        
    study.bizagi_number = data.bizagi_number
    study.status = "number_assigned"
    study.bizagi_at = datetime.now()
    study.bizagi_by = current_user.username
    
    db.commit()
    return {"status": "number_assigned"}

class BizagePay(BaseModel):
    paid_at: datetime
    invoice_number: Optional[str] = None

@app.put("/bizage/studies/{study_id}/pay")
def pay_bizage_study(study_id: int, data: BizagePay, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    study = db.query(models.BizageStudy).filter(models.BizageStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
        
    study.status = "paid"
    # Parse date
    try:
        dt = datetime.fromisoformat(data.paid_at.replace("Z", "+00:00"))
        study.paid_at = dt
    except:
        study.paid_at = data.paid_at
        
    study.paid_by = current_user.username
    if data.invoice_number:
         study.invoice_number = data.invoice_number
    study.status = "paid"
    db.commit()
    return {"status": "paid"}

class BizageUpdate(BaseModel):
    study_type: Optional[str] = None
    study_name: Optional[str] = None
    n_value: Optional[int] = None
    survey_no_participa: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[int] = None
    copies: Optional[int] = None
    vinipel: Optional[int] = None
    other_cost_description: Optional[str] = None
    other_cost_amount: Optional[int] = None
    bizagi_number: Optional[str] = None
    status: Optional[str] = None # Allow admins to manually fix status if needed

@app.put("/bizage/studies/{study_id}")
def update_bizage_study(study_id: int, data: BizageUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "superuser":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    study = db.query(models.BizageStudy).filter(models.BizageStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    # Update all provided fields
    if data.study_type is not None: study.study_type = data.study_type
    if data.study_name is not None: study.study_name = data.study_name
    if data.n_value is not None: study.n_value = data.n_value
    if data.survey_no_participa is not None: study.survey_no_participa = data.survey_no_participa
    
    if data.quantity is not None: study.quantity = data.quantity
    if data.price is not None: study.price = data.price
    if data.copies is not None: study.copies = data.copies
    if data.vinipel is not None: study.vinipel = data.vinipel
    if data.other_cost_description is not None: study.other_cost_description = data.other_cost_description
    if data.other_cost_amount is not None: study.other_cost_amount = data.other_cost_amount
    
    if data.bizagi_number is not None: study.bizagi_number = data.bizagi_number
    if data.status is not None: study.status = data.status

    db.commit()
    return {"status": "updated"}


def normalize_columns(df, manual_mapping=None):
    # If manual mapping is provided, apply it strictly
    if manual_mapping:
        rename_map = {v: k for k, v in manual_mapping.items() if v}
        missing = []
        for std, actual in manual_mapping.items():
            if actual and actual not in df.columns:
                 pass 
            elif not actual:
                 missing.append(std)
        if missing:
             return df, missing
        return df.rename(columns=rename_map), []

    # Map expected roughly to standard names if needed, or just strict check
    # User asked for: Id, Ciudad, Numero de celular, Codigo, and now Nombre (Enc_1)
    # We will try to find these columns case-insensitive
    cols = {str(c).strip().lower(): c for c in df.columns}
    
    # Required keys map to LIST of possible aliases
    required_map = {
        "Id": ["id", "censo", "identifier"],
        "Ciudad": ["ciudad", "ciu", "city"],
        "Numero de celular": ["numero de celular", "celular", "enc_3", "movil"],
        "Codigo": ["codigo", "cod", "code"],
        "Nombre": ["enc_1", "nombre", "encuestada", "name"],
        "Encuestador": ["encues_1"],
        "Nse": ["nse", "estrato", "nivel", "capa", "socioeconomico", "seg"],
        "Duration": ["duration", "duracion", "tiempo", "time"],
        "Producto": ["producto", "marca", "codigo del producto", "product", "brand", "code product"]
    }
    
    mapping = {}
    missing = []
    
    for standard_name, aliases in required_map.items():
        found = False
        for alias in aliases:
            if alias in cols:
                mapping[cols[alias]] = standard_name
                found = True
                break
        
        if not found:
            missing.append(standard_name)
    
    if missing:
        # If headers are completely different, this might fail.
        # Let's hope the user provides compliant files or we will error out with helpful message.
        return df, missing
        
    return df.rename(columns=mapping), []

@app.post("/validate")
async def validate_files(
    files: List[UploadFile] = File(...),
    mapping: str = Form(None)
):
    if len(files) != 2:
        raise HTTPException(status_code=400, detail="Exactly 2 files are required for Validation.")

    dfs = []
    filenames = []
    
    for file in files:
        content = await file.read()
        try:
            df = pd.read_excel(io.BytesIO(content))
            dfs.append(df)
            filenames.append(file.filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file {file.filename}: {str(e)}")

    # Parse mapping if provided
    manual_maps = [None, None]
    if mapping:
        try:
            parsed_map = json.loads(mapping)
            manual_maps[0] = parsed_map.get("file1")
            manual_maps[1] = parsed_map.get("file2")
        except:
            pass

    # Column Normalization
    df1, missing1 = normalize_columns(dfs[0], manual_maps[0])
    df2, missing2 = normalize_columns(dfs[1], manual_maps[1])

    if missing1 or missing2:
        return JSONResponse(
            status_code=409,
            content={
                "status": "missing_columns",
                "detail": "Could not auto-detect all required columns.",
                "file_1_name": filenames[0],
                # Return columns as simple strings to be JSON serializable
                "file_1_columns": [str(c) for c in dfs[0].columns],
                "missing_1": missing1,
                "file_2_name": filenames[1],
                "file_2_columns": [str(c) for c in dfs[1].columns],
                "missing_2": missing2,
                "required_fields": ["Id", "Ciudad", "Numero de celular", "Codigo", "Nombre", "Nse", "Duration", "Encuestador", "Producto"]
            }
        )

    # --- CATEGORIZATION LOGIC ---
    
    # helper for cleaning strings
    def clean(s):
        return str(s).strip().lower()

    # NSE Normalization Helper
    def normalize_nse(val):
        s = clean(val)
        # 2 / BA / Baja Alta
        if s in ['2', 'dos', 'ba', 'baja alta', 'bajaalta']:
            return 'Baja Alta'
        # 3 / Tres / Media Baja / NSE 3
        if s in ['3', 'tres', 'media baja', 'nse 3', 'nse3', 'mediabaja']:
            return 'Media Baja'
        # 4 / Cuatro / Media Tipica
        if s in ['4', 'cuatro', 'media tipica', 'mediatipica', 'media típica']:
            return 'Media Típica'
        return s.title() # Return capitalized original if not matched

    # 1. ELIMINAR (Duplicates)
    # We identify duplicates BEFORE dropping them for the merge
    eliminar_rows = []
    
    # Duplicates in File 1
    dup1 = df1[df1.duplicated(subset=['Id'], keep=False)]
    if not dup1.empty:
        # Add to eliminar list. We flag them as "Duplicado en R1"
        for _, row in dup1.iterrows():
            r = row.to_dict()
            r['Motivo'] = "Duplicada en R1"
            eliminar_rows.append(r)
            
    # Duplicates in File 2
    dup2 = df2[df2.duplicated(subset=['Id'], keep=False)]
    if not dup2.empty:
        for _, row in dup2.iterrows():
            r = row.to_dict()
            r['Motivo'] = "Duplicada en RF"
            eliminar_rows.append(r)

    # Now drop duplicates to allow clean merge (keeping first as requested for the comparison)
    df1_clean = df1.drop_duplicates(subset=['Id'], keep='first')
    df2_clean = df2.drop_duplicates(subset=['Id'], keep='first')

    # --- INTERVIEWER METRICS ---
    def get_interviewer_stats(df, suffix):
        tmp = df.copy()
        if 'Encuestador' not in tmp.columns:
            tmp['Encuestador'] = 'Desconocido'
            
        # Specific Normalization Map
        name_map = {
            "armando zararte": "Armando Zarate",
            "fermada ramos": "Fernanda Ramos",
            "fermamda ramos": "Fernanda Ramos",
            "fernada ramos": "Fernanda Ramos",
            "fernanada ramos": "Fernanda Ramos",
            "fernanda": "Fernanda Ramos",
            "ingrid codoba": "Ingrid Cordoba",
            "johana benitez": "Johana Benitez", # Ensure standard
            "juan moreno": "Juan Moreno",
            "laura osorio": "Laura Osorio",
            "milena zarate": "Milena Zarate",
            "yraima rey": "Yraima Rey"
        }
        
        def norm_name(n):
            s = str(n).strip().lower()
            # Direct mapping
            if s in name_map:
                return name_map[s]
            # Fallback: Title case
            return s.title()

        tmp['Encuestador_Norm'] = tmp['Encuestador'].apply(norm_name)
        
        # Duration
        col_dur = 'Duration'
        if col_dur not in tmp.columns:
            tmp[col_dur] = 0
        
        # Convert to numeric
        tmp[col_dur] = pd.to_numeric(tmp[col_dur], errors='coerce').fillna(0)
        
        # Convert Excel Serial Time to Minutes if it looks like serial time (< 1 usually, or just assuming it is)
        # User example: 0.013576 (~19.5 min). 
        # Logic: If max duration is small (< 5?), x 1440. If > 5, assume minutes already?
        # Safe bet: User specifically mentioned "toma formato general...". Assuming ALL valid durations are Excel Time.
        # But if some files are already in minutes (e.g. 20, 30), multiplying by 1440 would be huge (28800 min).
        # Heuristic: If mean < 1.0, assume Days -> Minutes.
        
        mean_val = tmp[col_dur].mean()
        if 0 < mean_val < 1.0:
            tmp[col_dur] = tmp[col_dur] * 1440
        
        # Calculate Global Mean (excluding 0s) for Alert Baseline
        global_mean = tmp[tmp[col_dur] > 0][col_dur].mean() if not tmp.empty else 0
        
        stats = tmp.groupby('Encuestador_Norm').agg(
            Count=('Id', 'count'),
            Avg_Duration=('Duration', 'mean')
        ).reset_index()
        
        # Add Alert Column
        def get_alert(row):
            if row['Count'] == 0: return ""
            avg = row['Avg_Duration']
            if global_mean > 0:
                if avg < (global_mean * 0.4): # Less than 40% of average
                    return "Muy Bajo"
                if avg > (global_mean * 1.8): # More than 180% of average (approx 2x)
                    return "Muy Alto"
            return "Normal"

        stats[f'Alerta_{suffix}'] = stats.apply(get_alert, axis=1)
        
        return stats.rename(columns={'Count': f'Cantidad_{suffix}', 'Avg_Duration': f'Tiempo_{suffix}'})

    stats_r1 = get_interviewer_stats(df1_clean, 'R1')
    stats_rf = get_interviewer_stats(df2_clean, 'RF')
    
    interviewer_stats = pd.merge(stats_r1, stats_rf, on='Encuestador_Norm', how='outer').fillna({'Cantidad_R1':0, 'Cantidad_RF':0, 'Tiempo_R1':0, 'Tiempo_RF':0, 'Alerta_R1':'-', 'Alerta_RF':'-'})
    interviewer_stats['Cantidad_R1'] = interviewer_stats['Cantidad_R1'].astype(int)
    interviewer_stats['Cantidad_RF'] = interviewer_stats['Cantidad_RF'].astype(int)
    interviewer_stats['Tiempo_R1'] = interviewer_stats['Tiempo_R1'].round(2)
    interviewer_stats['Tiempo_RF'] = interviewer_stats['Tiempo_RF'].round(2)
    
    interviewer_stats = interviewer_stats.rename(columns={
        'Encuestador_Norm': 'Encuestador',
        'Tiempo_R1': 'Tiempo Promedio R1 (Min)',
        'Tiempo_RF': 'Tiempo Promedio RF (Min)',
        'Alerta_R1': 'Alerta Tiempos R1',
        'Alerta_RF': 'Alerta Tiempos RF'
    })

    # Merge
    merged = pd.merge(df1_clean, df2_clean, on='Id', suffixes=('_1', '_2'), how='outer', indicator=True)

    # 2. CAÍDAS (Only in R1)
    caidas_df = merged[merged['_merge'] == 'left_only'].copy()
    # Rename columns back to generic (remove _1)
    rename_cols = {c: c[:-2] for c in caidas_df.columns if c.endswith('_1')}
    caidas_df = caidas_df.rename(columns=rename_cols)
    # Filter to relevant columns if possible, or keep all
    
    # 3. ELIMINAR (Only in RF) - Append to existing eliminar list
    only_rf = merged[merged['_merge'] == 'right_only'].copy()
    if not only_rf.empty:
        for _, row in only_rf.iterrows():
            # Construct row dict. Columns have _2 suffix.
            r = {}
            for col in only_rf.columns:
                if col.endswith('_2'):
                    r[col[:-2]] = row[col]
                elif col == 'Id':
                    r['Id'] = row['Id']
            r['Motivo'] = "Sobra en RF"
            eliminar_rows.append(r)
            
    eliminar_df = pd.DataFrame(eliminar_rows)
    # Reorder Eliminar: Put 'Motivo' at the end
    if not eliminar_df.empty and 'Motivo' in eliminar_df.columns:
        cols = [c for c in eliminar_df.columns if c != 'Motivo'] + ['Motivo']
        eliminar_df = eliminar_df[cols]

    # ... (rest of code) ...
    # This replace_file_content modifies the early part of validate_files.
    # I need to ensure I don't break the flow. 
    # I will target the lines from "1. ELIMINAR" down to "eliminar_df = ..."
    
    # AND I need to update the Speech generation logic which uses str.contains('RF')/('R1').
    # I can do that in a second replace or try to cover all if they are close (they are not close enough).
    # I will do two replaces. First the creation logic.


    # 4. BUENOS vs SEMI BUENOS (Common)
    common = merged[merged['_merge'] == 'both'].copy()
    
    buenos_rows = []
    semi_buenos_rows = []
    
    for _, row in common.iterrows():
        reasons = []
        
        # Check Ciudad
        if clean(row['Ciudad_1']) != clean(row['Ciudad_2']):
            reasons.append(f"Cambia de Ciudad: {row['Ciudad_1']} vs {row['Ciudad_2']}")
            
        # Check Celular
        if clean(row['Numero de celular_1']) != clean(row['Numero de celular_2']):
            reasons.append(f"Cambia de Numero: {row['Numero de celular_1']} vs {row['Numero de celular_2']}")
            
        # Check Nombre
        if clean(row['Nombre_1']) != clean(row['Nombre_2']):
            reasons.append(f"Cambia de Nombre: {row['Nombre_1']} vs {row['Nombre_2']}")
            
        # Check Codigo (Should be DIFFERENT)
        if clean(row['Codigo_1']) == clean(row['Codigo_2']):
            reasons.append(f"No es el Cod (es igual): {row['Codigo_1']}")

        # Check NSE
        val_nse1 = row.get('Nse_1', '')
        val_nse2 = row.get('Nse_2', '')
        if normalize_nse(val_nse1) != normalize_nse(val_nse2):
             reasons.append(f"Cambia de NSE: {val_nse1} vs {val_nse2}")
            
        # Base Row
        base_row = {}
        for col in df1_clean.columns:
            if col in ['Id']:
                base_row[col] = row[col]
            else:
                if f"{col}_1" in row:
                    base_row[col] = row[f"{col}_1"]
        
        # ALWAYS capture RF context for Summary (and report)
        base_row['Codigo_RF'] = row.get('Codigo_2', '')
        base_row['Ciudad_RF'] = row.get('Ciudad_2', '')
        base_row['Celular_RF'] = row.get('Numero de celular_2', '')
        base_row['Nse_RF'] = row.get('Nse_2', '')

        if reasons:
            base_row['Motivo'] = "; ".join(reasons)
            semi_buenos_rows.append(base_row)
        else:
            buenos_rows.append(base_row)
            
    buenos_df = pd.DataFrame(buenos_rows)
    semi_buenos_df = pd.DataFrame(semi_buenos_rows)
    
    # Reorder Semi Buenos: Put 'Motivo' at the end
    if not semi_buenos_df.empty and 'Motivo' in semi_buenos_df.columns:
        cols = [c for c in semi_buenos_df.columns if c != 'Motivo'] + ['Motivo']
        semi_buenos_df = semi_buenos_df[cols]
        
    # --- BUILD SUMMARY DATAFRAME ---
    # We want specific ordering: 
    # 1. Buenas (Aggregated by Ciudad, Nse ONLY)
    # 2. Por arreglar (Semi Buenos) (Aggregated by Ciudad, Nse, Codes)
    # 3. Caídas (Aggregated by Ciudad, Nse, Codes)
    # 4. Eliminar (Aggregated by Ciudad, Tipo)

    final_summary_parts = []

    # 1. BUENAS
    if not buenos_df.empty:
        # Create temp df for aggregation
        temp_buenas = pd.DataFrame()
        temp_buenas['Ciudad'] = buenos_df['Ciudad'].apply(clean)
        temp_buenas['Nse'] = buenos_df['Nse'].apply(normalize_nse) if 'Nse' in buenos_df.columns else ''
        temp_buenas['Tipo'] = 'Buenas'
        
        # Group
        grp_buenas = temp_buenas.groupby(['Ciudad', 'Nse', 'Tipo']).size().reset_index(name='Cantidad')
        # Add missing columns for schema alignment
        grp_buenas['Codigo_R1'] = '-'
        grp_buenas['Codigo_RF'] = '-'
        
        final_summary_parts.append(grp_buenas)

    # 2. POR ARREGLAR (Semi Buenos)
    if not semi_buenos_df.empty:
        temp_semi = pd.DataFrame()
        temp_semi['Ciudad'] = semi_buenos_df['Ciudad'].apply(clean)
        temp_semi['Nse'] = semi_buenos_df['Nse'].apply(normalize_nse) if 'Nse' in semi_buenos_df.columns else ''
        temp_semi['Codigo_R1'] = semi_buenos_df['Codigo'].apply(clean) if 'Codigo' in semi_buenos_df.columns else ''
        temp_semi['Codigo_RF'] = semi_buenos_df['Codigo_RF'].apply(clean) if 'Codigo_RF' in semi_buenos_df.columns else ''
        temp_semi['Tipo'] = 'Por arreglar'
        
        grp_semi = temp_semi.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        final_summary_parts.append(grp_semi)
            
    # 3. CAÍDAS
    if not caidas_df.empty:
        temp_caidas = pd.DataFrame()
        temp_caidas['Ciudad'] = caidas_df['Ciudad'].apply(clean)
        temp_caidas['Nse'] = caidas_df['Nse'].apply(normalize_nse) if 'Nse' in caidas_df.columns else ''
        temp_caidas['Codigo_R1'] = caidas_df['Codigo'].apply(clean) if 'Codigo' in caidas_df.columns else ''
        temp_caidas['Codigo_RF'] = '-'
        temp_caidas['Tipo'] = 'Caídas'
        
        grp_caidas = temp_caidas.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        final_summary_parts.append(grp_caidas)

    # 4. ELIMINAR
    if not eliminar_df.empty:
        temp_elim = pd.DataFrame()
        temp_elim['Ciudad'] = eliminar_df['Ciudad'].apply(clean)
        temp_elim['Nse'] = '-'
        temp_elim['Codigo_R1'] = '-'
        temp_elim['Codigo_RF'] = '-'
        
        # Determine subtype
        def get_elim_type(row):
            m = str(row.get('Motivo', ''))
            return 'Eliminar RF' if 'RF' in m else 'Eliminar R1'
            
        temp_elim['Tipo'] = eliminar_df.apply(get_elim_type, axis=1)
        
        grp_elim = temp_elim.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        final_summary_parts.append(grp_elim)

    # Concat all parts
    if final_summary_parts:
        summary_pivot = pd.concat(final_summary_parts, ignore_index=True)
        # Ensure column order
        summary_pivot = summary_pivot[['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo', 'Cantidad']]
    else:
        summary_pivot = pd.DataFrame(columns=['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo', 'Cantidad'])

    # --- SPEECH GENERATION ---
    study_name = "Estudio"
    if filenames:
        # Try to get a clean name from the first filename
        # Remove extension
        base = os.path.splitext(filenames[0])[0]
        study_name = base

    speech_lines = []
    speech_lines.append(f"Saludos, de estudio {study_name}")
    speech_lines.append("")

    # 1. Terminamos efectivas bien
    if not buenos_df.empty:
        good_counts = buenos_df.groupby('Ciudad').size()
        good_str = ", ".join([f"{city}: {count}" for city, count in good_counts.items()])
        speech_lines.append(f"Terminamos efectivas bien de {good_str}.")
    else:
        speech_lines.append("No hay efectivas bien.")

    # 2. Favor corregir (Semi Buenos)
    # "favor corregir xxx que de los censos ... y respectivos r con el error"
    if not semi_buenos_df.empty:
        total_fix = len(semi_buenos_df)
        speech_lines.append(f"Favor corregir {total_fix} registros.")
        # List details as requested: "valores de censos a corregir y el porque"
        speech_lines.append(f"Favor corregir {total_fix} registros:")
        for _, row in semi_buenos_df.iterrows():
             # "Censo X: Motivo"
             speech_lines.append(f"  - Censo {row['Id']}: {row['Motivo']}")

    # 3. Caídas (Por ciudad solamente)
    if not caidas_df.empty:
        drop_counts = caidas_df.groupby('Ciudad').size()
        drop_str = ", ".join([f"{city}: {count}" for city, count in drop_counts.items()])
        speech_lines.append(f"Caídas: {drop_str}.")
    
    # 4. Eliminar
    # Deduplicate IDs for speech and include reason
    if not eliminar_df.empty:
        # Filter groups
        # RF: "Sobra en RF" or "Duplicada en RF"
        elim_rf = eliminar_df[eliminar_df['Motivo'].astype(str).str.contains('RF', na=False)]
        # R1: "Duplicada en R1"
        elim_r1 = eliminar_df[eliminar_df['Motivo'].astype(str).str.contains('R1', na=False)]
        
        # Helper to format list: "ID (Reason)" unique
        def format_elim_list(df):
            # deduplicate by ID, keeping first reason found (usually same reason for duplicates)
            deduped = df.drop_duplicates(subset=['Id'])
            items = []
            for _, row in deduped.iterrows():
                items.append(f"{row['Id']} ({row['Motivo']})")
            return ", ".join(items)

        if not elim_rf.empty:
            count = len(elim_rf.drop_duplicates(subset=['Id']))
            ids_str = format_elim_list(elim_rf)
            speech_lines.append(f"Favor eliminar de las RF ({count} casos únicos): Censos {ids_str}.")
            
        if not elim_r1.empty:
            count = len(elim_r1.drop_duplicates(subset=['Id']))
            ids_str = format_elim_list(elim_r1)
            speech_lines.append(f"Favor eliminar de R1 ({count} casos únicos): Censos {ids_str}.")

    speech_text = "\n".join(speech_lines)


    # Generate Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write Summary Table
        if not summary_pivot.empty:
            summary_pivot.to_excel(writer, sheet_name='Resumen', index=False)
        else:
             pd.DataFrame({'Info': ['Sin datos']}).to_excel(writer, sheet_name='Resumen', index=False)
        
        # Write Speech below Summary
        # We need to access the workbook/sheet to write text at specific position
        # Pandas allows writing to startrow/startcol but assumes DataFrame.
        # We can write a dataframe with the speech, or hook into the sheet.
        # Simplest: Write Summary, then write Speech DF below it.
        
        start_row_speech = len(summary_pivot) + 4
        speech_df = pd.DataFrame([l for l in speech_lines], columns=["Speech Draft"])
        speech_df.to_excel(writer, sheet_name='Resumen', startrow=start_row_speech, index=False, header=False)

        # Write Interviewer Metrics
        start_row_metrics = start_row_speech + len(speech_lines) + 2
        if not interviewer_stats.empty:
            interviewer_stats.to_excel(writer, sheet_name='Resumen', startrow=start_row_metrics, index=False)


        if not buenos_df.empty:
            buenos_df.to_excel(writer, sheet_name='Buenas', index=False)
        else:
            pd.DataFrame({'Info': ['No hay registros perfectos']}).to_excel(writer, sheet_name='Buenas', index=False)
            
        if not semi_buenos_df.empty:
            semi_buenos_df.to_excel(writer, sheet_name='Por arreglar', index=False)
        else:
             pd.DataFrame({'Info': ['No hay registros por arreglar']}).to_excel(writer, sheet_name='Por arreglar', index=False)
             
        if not caidas_df.empty:
            cols_to_save = [c for c in caidas_df.columns if not c.endswith(('_2', '_merge'))]
            caidas_df[cols_to_save].to_excel(writer, sheet_name='Caidas', index=False)
        else:
            pd.DataFrame({'Info': ['No hay caídas']}).to_excel(writer, sheet_name='Caidas', index=False)
            
        if not eliminar_df.empty:
            eliminar_df.to_excel(writer, sheet_name='Eliminar', index=False)
        else:
            pd.DataFrame({'Info': ['No hay registros para eliminar']}).to_excel(writer, sheet_name='Eliminar', index=False)

    output.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="Reporte_{study_name}.xlsx"'
    }
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.post("/fatiga")
async def fatiga_check(files: List[UploadFile] = File(...), mapping: str = Form(None)):
    if not (2 <= len(files) <= 10):
         raise HTTPException(status_code=400, detail="Fatiga mode requires between 2 and 10 files.")

    dfs = []
    filenames = []
    
    for file in files:
        content = await file.read()
        try:
            df = pd.read_excel(io.BytesIO(content))
            dfs.append(df)
            filenames.append(file.filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file {file.filename}: {str(e)}")

    # Parse mapping if provided (Assuming mapping structure handles list? Logic in frontend might need verification if it sends map for >2 files. 
    # For now, simplistic manual map or auto-detect.)
    # The current frontend mapping modal supports file1 and file2. 
    # Fatigue might imply standard headers usually.
    # We'll use auto-detect. N-file mapping UI is a complexity user didn't request yet.
    
    # helper for cleaning strings
    def clean(s):
        return str(s).strip().lower()
        
    # Helper for NSE
    def normalize_nse(val):
        s = clean(val)
        if s in ['2', 'dos', 'ba', 'baja alta', 'bajaalta']: return 'Baja Alta'
        if s in ['3', 'tres', 'media baja', 'nse 3', 'nse3', 'mediabaja']: return 'Media Baja'
        if s in ['4', 'cuatro', 'media tipica', 'mediatipica', 'media típica']: return 'Media Típica'
        return s.title()
    
    # Normalize all
    norm_dfs = []
    for i, df in enumerate(dfs):
        # We don't have per-file valid mapping from existing UI for files > 2.
        # Passing None for manual map safely.
        ndf, missing = normalize_columns(df, None)
        if missing:
             return JSONResponse(
                status_code=409,
                content={
                    "status": "missing_columns",
                    "detail": f"Missing columns in {filenames[i]}: {missing}",
                    "file_1_name": filenames[0], # Reuse format so UI might catch it, though specific UI update needed for N files 409. 
                                                 # For now fallback to simple error if headers bad.
                    "file_1_columns": [str(c) for c in df.columns],
                    "missing_1": missing,
                    # Hack: To prevent crash if UI expects file_2
                    "file_2_name": filenames[1] if len(filenames) > 1 else "",
                    "file_2_columns": [],
                    "missing_2": [],
                    "required_fields": ["Id", "Ciudad", "Numero de celular", "Codigo", "Nombre", "Nse", "Duration", "Encuestador"]
                }
            )
        # Deduplicate IDs in each file (keeping first)
        ndf = ndf.drop_duplicates(subset=['Id'], keep='first')
        norm_dfs.append(ndf)

    # MERGE LOGIC
    # Base is File 1 (R1)
    # We merge everything onto a master list of IDs?
    # Or strict Left Join on R1? 
    # User: "si esta en A la r1 todas las demas deben estar en A y sino error".
    # User: "si en r1 y r2 esta pero para rf no esta caida".
    # This implies we need to track everything.
    
    from functools import reduce
    
    # Rename columns to avoid collision: suffix _0, _1, ...
    renamed_dfs = []
    for i, df in enumerate(norm_dfs):
        # Rename all except Id
        cols = {c: f"{c}_{i}" for c in df.columns if c != 'Id'}
        renamed_dfs.append(df.rename(columns=cols))
        
    # Full Outer Join to catch "Sobra" (Eliminar) vs "Caída"
    merged = reduce(lambda left, right: pd.merge(left, right, on='Id', how='outer'), renamed_dfs)
    
    buenos_rows = []
    por_arreglar_rows = []
    caidas_rows = []
    eliminar_rows = []
    
    # Iterate
    for _, row in merged.iterrows():
        # Get R1 Data
        id_val = row['Id']
        in_r1 = pd.notna(row.get('Codigo_0')) # Check existence via a required column like Codigo
        
        # Base info from R1 (or first available if missing in R1)
        base_info = {}
        # Find first existing file index for this ID to get Ciudad/NSE info
        first_idx = -1
        for i in range(len(files)):
            if pd.notna(row.get(f'Codigo_{i}')):
                first_idx = i
                break
        
        if first_idx != -1:
            base_info['Ciudad'] = row.get(f'Ciudad_{first_idx}', '')
            base_info['Nse'] = row.get(f'Nse_{first_idx}', '')
            base_info['Id'] = id_val
            base_info['Codigo_R1'] = row.get(f'Codigo_0', '') # Might be NaN if not in R1
            # RF Code (Last File)
            last_idx = len(files) - 1
            base_info['Codigo_RF'] = row.get(f'Codigo_{last_idx}', '')
        else:
            continue # Should not happen

        # Checks
        if not in_r1:
            # Not in R1 -> ELIMINAR ("Sobra")
            # Determine where it appeared
            found_in = []
            for i in range(1, len(files)):
                if pd.notna(row.get(f'Codigo_{i}')):
                    found_in.append(filenames[i])
            
            r = base_info.copy()
            r['Motivo'] = f"Sobra en {', '.join(found_in)}"
            eliminar_rows.append(r)
            continue
            
        # In R1. Check Valid Flow.
        # 1. Existence in subsequent files
        # 2. Code Consistency
        
        error_msgs = []
        is_caida = False
        
        # Check against all subsequent files
        # Code reference is R1
        ref_code = clean(row.get('Codigo_0'))
        
        for i in range(1, len(files)):
            # Check existence
            if pd.isna(row.get(f'Codigo_{i}')):
                # Missing in File i
                # If it's the LAST file, it's definitively a "Caída" (Conceptually).
                # User: "si en r1 y r2 esta pero para rf no esta caida"
                # If missing in intermediate? e.g. R1=Yes, R2=No, R3=Yes.
                # Usually that's a "Caída en R2" implies broken flow.
                error_msgs.append(f"Caída en {filenames[i]}")
                is_caida = True 
                # Should we continue checking? Usually once dropped, it's dropped.
            else:
                # Exists. Check Code.
                curr_code = clean(row.get(f'Codigo_{i}'))
                if curr_code != ref_code:
                    error_msgs.append(f"Error Codigo {filenames[i]}: {curr_code} vs R1({ref_code})")
        
        # Construct Result
        if is_caida:
             # Add to Caídas
             r = base_info.copy()
             r['Motivo'] = "; ".join([e for e in error_msgs if "Caída" in e])
             r['Tipo'] = 'Caídas'
             caidas_rows.append(r)
             # If there were ALSO code errors, maybe flag? Caída usually prioritizes.
        elif error_msgs:
            # Code Mismatches -> Por Arreglar
            r = base_info.copy()
            r['Motivo'] = "; ".join(error_msgs)
            r['Tipo'] = 'Por arreglar'
            por_arreglar_rows.append(r)
        else:
            # Perfect
            r = base_info.copy()
            r['Tipo'] = 'Buenas'
            buenos_rows.append(r)

    # Convert to DFs
    buenos_df = pd.DataFrame(buenos_rows)
    por_arreglar_df = pd.DataFrame(por_arreglar_rows)
    caidas_df = pd.DataFrame(caidas_rows)
    eliminar_df = pd.DataFrame(eliminar_rows)
    
    # --- SUMMARY ---
    summary_parts = []
    
    if not buenos_df.empty:
        g = buenos_df.copy()
        g['Ciudad'] = g['Ciudad'].apply(clean)
        g['Nse'] = g['Nse'].apply(normalize_nse)
        g['Codigo_R1'] = '-'
        g['Codigo_RF'] = '-'
        summ = g.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        summary_parts.append(summ)

    if not por_arreglar_df.empty:
        g = por_arreglar_df.copy()
        g['Ciudad'] = g['Ciudad'].apply(clean)
        g['Nse'] = g['Nse'].apply(normalize_nse)
        g['Codigo_R1'] = g['Codigo_R1'].apply(clean)
        g['Codigo_RF'] = g['Codigo_RF'].apply(clean)
        summ = g.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        summary_parts.append(summ)
        
    if not caidas_df.empty:
        g = caidas_df.copy()
        g['Ciudad'] = g['Ciudad'].apply(clean)
        g['Nse'] = g['Nse'].apply(normalize_nse)
        g['Codigo_R1'] = g['Codigo_R1'].apply(clean)
        g['Codigo_RF'] = '-' # Caída doesn't reach end usually, or inconsistent. Keep simple.
        
        # Caídas 'Motivo' contains which file. user might want split? 
        # For now aggregate all 'Caídas'.
        summ = g.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        summary_parts.append(summ)

    if not eliminar_df.empty:
        g = eliminar_df.copy()
        g['Ciudad'] = g['Ciudad'].apply(clean)
        g['Nse'] = '-'
        g['Codigo_R1'] = '-'
        g['Codigo_RF'] = '-'
        g['Tipo'] = 'Eliminar' # Simplify
        summ = g.groupby(['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo']).size().reset_index(name='Cantidad')
        summary_parts.append(summ)

    if summary_parts:
        summary_pivot = pd.concat(summary_parts, ignore_index=True)
    else:
        summary_pivot = pd.DataFrame(columns=['Ciudad', 'Nse', 'Codigo_R1', 'Codigo_RF', 'Tipo', 'Cantidad'])


    # --- SPEECH ---
    study_name = os.path.splitext(filenames[0])[0]
    speech_lines = [f"Saludos, de estudio {study_name}", "", "FATIGA CHECK REPORT", ""]
    
    # 1. Buenas
    if not buenos_df.empty:
        c = buenos_df['Ciudad'].apply(clean).value_counts()
        s = ", ".join([f"{k}: {v}" for k,v in c.items()])
        speech_lines.append(f"Terminamos efectivas bien de {s}.")
    
    # 2. Por arreglar
    if not por_arreglar_df.empty:
        speech_lines.append(f"Favor corregir {len(por_arreglar_df)} registros (Errores de Código).")
        # List IDs?
        ids = ", ".join(por_arreglar_df['Id'].astype(str).unique())
        speech_lines.append(f"  Censos: {ids}")

    # 3. Caídas
    if not caidas_df.empty:
        speech_lines.append(f"Caídas detectadas: {len(caidas_df)}.")
        # Summary by File?
        # TODO

    # 4. Eliminar
    if not eliminar_df.empty:
        speech_lines.append(f"Favor eliminar (Sobra en archivos secundarios): {len(eliminar_df)} casos.")
        ids = ", ".join(eliminar_df['Id'].astype(str).unique())
        speech_lines.append(f"  Censos: {ids}")
    
    
    # GENERATE EXCEL
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if not summary_pivot.empty:
            summary_pivot.to_excel(writer, sheet_name='Resumen', index=False)
        else: 
            pd.DataFrame({'Info': ['Sin datos']}).to_excel(writer, sheet_name='Resumen', index=False)
            
        # Write speech
        start_row = len(summary_pivot) + 4
        pd.DataFrame(speech_lines).to_excel(writer, sheet_name='Resumen', startrow=start_row, index=False, header=False)
        
        if not buenos_df.empty: buenos_df.to_excel(writer, sheet_name='Buenas', index=False)
        if not por_arreglar_df.empty: por_arreglar_df.to_excel(writer, sheet_name='Por arreglar', index=False)
        if not caidas_df.empty: caidas_df.to_excel(writer, sheet_name='Caidas', index=False)
        if not eliminar_df.empty: eliminar_df.to_excel(writer, sheet_name='Eliminar', index=False)

    output.seek(0)
    headers = {'Content-Disposition': 'attachment; filename="Reporte_Fatiga.xlsx"'}
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# --- CALLS ENDPOINTS ---

class CallStatusUpdate(BaseModel):
    status: str
    survey_id: Optional[str] = None
    bonus_status: Optional[str] = None

@app.put("/calls/{call_id}/status")
async def update_call_status(
    call_id: int,
    update: CallStatusUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    call = db.query(models.Call).filter(models.Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Update status
    call.status = update.status
    
    # Update survey fields if provided (when marking as managed)
    if update.survey_id:
        call.survey_id = update.survey_id
    if update.bonus_status:
        call.bonus_status = update.bonus_status
    
    call.updated_at = datetime.now()
    db.commit()
    db.refresh(call)
    
    return {"message": "Status updated successfully", "call_id": call.id}

class CallContactUpdate(BaseModel):
    phone_number: Optional[str] = None
    corrected_phone: Optional[str] = None
    person_cc: Optional[str] = None
    whatsapp: Optional[str] = None
    extra_phone: Optional[str] = None
    second_collection_date: Optional[str] = None
    second_collection_time: Optional[str] = None
    shampoo_quantity: Optional[str] = None

@app.put("/calls/{call_id}/contact")
async def update_call_contact(
    call_id: int,
    update: CallContactUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    call = db.query(models.Call).filter(models.Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if update.phone_number:
        call.phone_number = update.phone_number
    if update.corrected_phone is not None:
        call.corrected_phone = update.corrected_phone
    if update.person_cc is not None:
        call.person_cc = update.person_cc
    if update.whatsapp is not None:
        call.whatsapp = update.whatsapp
    if update.extra_phone is not None:
        call.extra_phone = update.extra_phone
    if update.second_collection_date is not None:
        call.second_collection_date = update.second_collection_date
    if update.second_collection_time is not None:
        call.second_collection_time = update.second_collection_time
    if update.shampoo_quantity is not None:
        call.shampoo_quantity = update.shampoo_quantity
        
    call.updated_at = datetime.now()
    db.commit()
    db.refresh(call)
    
    return {"message": "Contact data updated successfully", "call_id": call.id}



# --- PAYROLL SYSTEM ---

@app.post("/payroll/rate-sheets")
def create_rate_sheet(year: int, description: str, census: int = 0, effective: int = 0, enp: int = 0, training: int = 0, db: Session = Depends(database.get_db)):
    # Check if exists
    existing = db.query(models.RateSheet).filter(models.RateSheet.year == year).first()
    if existing:
        existing.description = description
        existing.census_rate = census
        existing.survey_effective_rate = effective
        existing.enp_rate = enp
        existing.training_rate = training
        db.commit()
        return existing
    
    new_sheet = models.RateSheet(
        year=year,
        description=description,
        census_rate=census,
        survey_effective_rate=effective,
        enp_rate=enp,
        training_rate=training
    )
    db.add(new_sheet)
    db.commit()
    db.refresh(new_sheet)
    return new_sheet

@app.get("/payroll/rate-sheets/current")
def get_current_rates(db: Session = Depends(database.get_db)):
    # Get for current year or specific
    current_year = datetime.now().year
    sheet = db.query(models.RateSheet).filter(models.RateSheet.year == current_year).first()
    return sheet or {}

@app.post("/payroll/periods")
def create_period(
    name: str = Form(...), 
    study_code: str = Form(""),
    study_type: str = Form(""), # Optional if generic
    execution_date: str = Form(None), # Might be used for single date
    start_date: str = Form(None), # "Lapsos"
    end_date: str = Form(None),   # "Lapsos"
    census_rate: int = Form(5000),
    effective_rate: int = Form(10000),
    initial_concepts: str = Form(None), # JSON String of initial concepts
    supervisor_ids: str = Form(None), # JSON String of user IDs
    db: Session = Depends(database.get_db)
):
    # Handle Dates
    e_date = None
    s_date = None
    en_date = None
    
    if execution_date:
        e_date = datetime.strptime(execution_date, "%Y-%m-%d")
        
    if start_date:
        s_date = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        en_date = datetime.strptime(end_date, "%Y-%m-%d")
        
    # Create rates snapshot
    rates = {
        "census": census_rate,
        "effective": effective_rate,
        "enp": 0 
    }
    
    # Create
    try:
        # Handle initial concepts (JSON string)
        concept_list = []
        if initial_concepts:
             try:
                 raw_concepts = json.loads(initial_concepts) # Expect [{"name": "X", "rate": 10}, ...]

                 for rc in raw_concepts:
                     # Validate
                     if rc.get('name') and rc.get('rate') is not None:
                         concept_list.append(models.PayrollConcept(name=str(rc['name']).strip(), rate=int(rc['rate'])))
             except Exception as e:
                 print(f"Error parsing initial concepts: {e}")

        period = models.PayrollPeriod(
            name=name,
            study_code=study_code,
            study_type=study_type, 
            execution_date=e_date,
            start_date=s_date,
            end_date=en_date,
            rates_snapshot=json.dumps(rates),
            status="open",
            is_visible=True
        )
        
        for c in concept_list:
            period.concepts.append(c)
            
        # Handle Supervisors
        if supervisor_ids:
            try:
                s_ids = json.loads(supervisor_ids)
                if isinstance(s_ids, list):
                     supervisors = db.query(models.User).filter(models.User.id.in_(s_ids)).all()
                     period.supervisors = supervisors
            except Exception as e:
                print(f"Error parsing supervisor IDs: {e}")

        db.add(period)
        db.commit()
        db.refresh(period)
        return period
    except Exception as e:
        db.rollback()
        print(f"Error creating period: {e}")
        raise HTTPException(500, detail=f"Error creando nómina: {str(e)}")

@app.post("/payroll/periods/{period_id}/concepts")
def add_concept(
    period_id: int, 
    name: str = Form(...), 
    rate: int = Form(...), 
    db: Session = Depends(database.get_db)
):
    period = db.query(models.PayrollPeriod).filter(models.PayrollPeriod.id == period_id).first()
    if not period: raise HTTPException(404, "Period not found")
    
    new_concept = models.PayrollConcept(period_id=period_id, name=name, rate=rate)
    db.add(new_concept)
    db.commit()
    db.refresh(new_concept)
    return new_concept

@app.get("/payroll/concepts/suggestions")
def get_concepts_suggestions(db: Session = Depends(database.get_db)):
    # Fetch all unique concept names and their latest rate
    # Subquery to find max ID for each name? Or just simple distinct.
    # We want valid suggestions.
    # Group by name?
    
    # Simple approach: Get all, map by name to overwrite with latest (likely higher ID).
    concepts = db.query(models.PayrollConcept).all()
    
    suggestions_map = {}
    for c in concepts:
        suggestions_map[c.name] = c.rate
        
    # Convert to list
    res = [{"name": k, "rate": v} for k, v in suggestions_map.items()]
    # Sort by name
    res.sort(key=lambda x: x['name'])
    return res

class ConceptUpdate(BaseModel):
    name: str
    rate: int

@app.put("/payroll/concepts/{concept_id}")
def update_concept(
    concept_id: int, 
    data: ConceptUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role not in ['superuser', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    concept = db.query(models.PayrollConcept).filter(models.PayrollConcept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
        
    concept.name = data.name
    concept.rate = data.rate
    db.commit()
    db.refresh(concept)
    return concept

@app.post("/payroll/periods/{period_id}/toggle-visibility")
def toggle_period_visibility(
    period_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != 'superuser':
        raise HTTPException(status_code=403, detail="Not authorized")
        
    p = db.query(models.PayrollPeriod).filter(models.PayrollPeriod.id == period_id).first()
    if not p: raise HTTPException(404, "Period not found")
    p.is_visible = not p.is_visible
    db.commit()
    return {"status": "ok", "is_visible": p.is_visible}

@app.delete("/payroll/periods/{period_id}")
def delete_period(
    period_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != 'superuser':
        raise HTTPException(status_code=403, detail="Not authorized")
        
    p = db.query(models.PayrollPeriod).filter(models.PayrollPeriod.id == period_id).first()
    if not p: raise HTTPException(404, "Period not found")
    
    try:
        # 1. Delete Record Items (Deepest Level - Children of Records)
        # Find all records for this period to get IDs
        records = db.query(models.PayrollRecord).filter(models.PayrollRecord.period_id == period_id).all()
        record_ids = [r.id for r in records]
        
        if record_ids:
            # Bulk delete items for these records
            db.query(models.PayrollRecordItem).filter(models.PayrollRecordItem.record_id.in_(record_ids)).delete(synchronize_session=False)

        # 2. Delete Payroll Records (Children of Period)
        db.query(models.PayrollRecord).filter(models.PayrollRecord.period_id == period_id).delete(synchronize_session=False)
        
        # 3. Delete Period (Concepts will cascade delete via ORM if defined, or we might need manual)
        # Check models.py: concepts = relationship(..., cascade="all, delete-orphan") -> This handles concepts if we delete `p` via session add/delete
        db.delete(p)
        db.commit()
        return {"status": "ok", "message": "Nómina eliminada correctamente"}
    except Exception as e:
        db.rollback()
        print(f"Error deleting period: {e}")
        raise HTTPException(500, detail=f"Error al eliminar nómina: {str(e)}")

@app.get("/payroll/periods")
@app.get("/payroll/periods")
def get_periods(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    query = db.query(models.PayrollPeriod)
    
    # RBAC: Superusers see all. Supervisors/Admins see only assigned.
    if current_user.role != 'superuser':
        # Filter where current_user is in period.supervisors
        query = query.filter(models.PayrollPeriod.supervisors.any(id=current_user.id))

    periods = query.order_by(models.PayrollPeriod.created_at.desc()).all()
    res = []
    for p in periods:
        res.append({
            "id": p.id,
            "name": p.name,
            "study_code": p.study_code,
            "study_type": p.study_type,
            "execution_date": p.execution_date,
            "start_date": p.start_date,
            "end_date": p.end_date,
            "rates": json.loads(p.rates_snapshot) if p.rates_snapshot else {},
            "status": p.status,
            "is_visible": p.is_visible if p.is_visible is not None else True,
            "concepts": [{"id": c.id, "name": c.name, "rate": c.rate} for c in p.concepts]
        })
    return res

@app.post("/payroll/generate/{period_id}")
def generate_payroll(period_id: int, db: Session = Depends(database.get_db)):
    period = db.query(models.PayrollPeriod).filter(models.PayrollPeriod.id == period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
    
    # 1. Clear existing DRAFT records
    db.query(models.PayrollRecord).filter(models.PayrollRecord.period_id == period_id, models.PayrollRecord.status == "draft").delete()
    db.commit()
    
    date_filter_start = period.start_date
    date_filter_end = period.end_date.replace(hour=23, minute=59, second=59)

    # 2. Base Query for Calls
    query = db.query(models.Call).filter(
        models.Call.updated_at >= date_filter_start,
        models.Call.updated_at <= date_filter_end,
        models.Call.user_id != None
    )
    
    if period.study_id:
        query = query.filter(models.Call.study_id == period.study_id)
        
    calls = query.all()
    
    # 3. Identify Concepts for Automatic Matching
    # We look for concepts in the period that look like "Encuesta Efectiva" or "Censo"
    # to attribute the automatic counts to them.
    # Fallback to Period Snapshot rates if concepts not found (Legacy behavior), 
    # but mainly we want to use the Concept ID.
    
    effective_concept = None
    census_concept = None
    
    for c in period.concepts:
        name_lower = c.name.lower()
        if "efectiv" in name_lower: # "Encuestas Efectivas", "Efectiva", etc.
            effective_concept = c
        elif "censo" in name_lower:
            census_concept = c
            
    # Fallback Rates from snapshot if concept not found (unlikely if created correctly)
    snapshot_rates = json.loads(period.rates_snapshot) if period.rates_snapshot else {}
    rate_eff = effective_concept.rate if effective_concept else snapshot_rates.get("effective", 0)
    rate_cen = census_concept.rate if census_concept else snapshot_rates.get("census", 0)

    # 4. Group by User
    user_activity = {}
    
    for c in calls:
        uid = c.user_id
        if uid not in user_activity:
            user_activity[uid] = { "effective": 0, "censuses": 0 }
            
        status_norm = (c.status or "").lower()
        
        # Logic 1: Effective
        if status_norm in ['done', 'terminado', 'efectiva_campo']:
            user_activity[uid]["effective"] += 1
            
        # Logic 2: Census
        if c.census and c.census.strip():
             user_activity[uid]["censuses"] += 1
             
    # 5. Create Records
    created_records = []
    for uid, data in user_activity.items():
        total_p = 0
        details = []
        record_items_data = [] # For secondary table
        
        # Calc Effective
        if data["effective"] > 0:
            qty = data["effective"]
            amt = qty * rate_eff
            total_p += amt
            
            item = {
                "concept": effective_concept.name if effective_concept else "Encuestas Efectivas (Auto)", 
                "qty": qty, 
                "rate": rate_eff, 
                "total": amt,
                "concept_id": effective_concept.id if effective_concept else None
            }
            details.append(item)
            if effective_concept:
                record_items_data.append({"concept_id": effective_concept.id, "quantity": qty, "total": amt})
            
        # Calc Census
        if data["censuses"] > 0:
            qty = data["censuses"]
            amt = qty * rate_cen
            total_p += amt
            
            item = {
                "concept": census_concept.name if census_concept else "Censos (Auto)", 
                "qty": qty, 
                "rate": rate_cen, 
                "total": amt,
                "concept_id": census_concept.id if census_concept else None
            }
            details.append(item)
            if census_concept:
                record_items_data.append({"concept_id": census_concept.id, "quantity": qty, "total": amt})
            
        # Save
        if total_p > 0:
            rec = models.PayrollRecord(
                period_id=period_id,
                user_id=uid,
                total_effective=data["effective"],
                total_censuses=data["censuses"],
                total_amount=total_p,
                details_json=json.dumps(details),
                status="draft",
                last_modified_by="Sistema",
                updated_at=datetime.now()
            )
            db.add(rec)
            db.flush() # Get ID
            
            # Create Items
            for item_data in record_items_data:
                db.add(models.PayrollRecordItem(
                    record_id=rec.id,
                    concept_id=item_data['concept_id'],
                    quantity=item_data['quantity'],
                    total=item_data['total']
                ))
            
            created_records.append(rec)
            
    db.commit()
    return {"message": "Generated", "count": len(created_records)}

class PayrollItemUpdate(BaseModel):
    concept_id: int
    quantity: int
    date: Optional[str] = None # YYYY-MM-DD

class PayrollUpdate(BaseModel):
    total_effective: int
    total_censuses: int
    total_enp: int = 0
    total_training: int = 0
    items: Optional[List[PayrollItemUpdate]] = [] # New detailed items list

@app.post("/payroll/records/manual")
def create_manual_record(
    period_id: int, 
    user_id: int, 
    data: PayrollUpdate, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    # Get Period 
    period = db.query(models.PayrollPeriod).filter(models.PayrollPeriod.id == period_id).first()
    if not period: raise HTTPException(404, "Period not found")
    
    # SECURITY: Supervisors cannot edit hidden periods
    if not period.is_visible and current_user.role != 'superuser':
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar este pago (está oculto).")

    # 1. Calculate Standard Legacy Items
    rates = {}
    if period.rates_snapshot:
        rates = json.loads(period.rates_snapshot)
    
    census_rate = rates.get("census", 0)
    effective_rate = rates.get("effective", 0)
    
    details = []
    total = 0
    
    # Legacy Calculations
    if data.total_effective > 0:
        amt = data.total_effective * effective_rate
        total += amt
        details.append({"concept": "Encuestas Efectivas", "qty": data.total_effective, "rate": effective_rate, "total": amt})
        
    if data.total_censuses > 0:
        amt = data.total_censuses * census_rate
        total += amt
        details.append({"concept": "Censos", "qty": data.total_censuses, "rate": census_rate, "total": amt})

    # 2. Calculate Dynamic Items
    # Fetch all concepts for this period to verify and get rates
    period_concepts = {str(c.id): c for c in period.concepts}
    


    # 3. Create or Get Record
    existing = db.query(models.PayrollRecord).filter(models.PayrollRecord.period_id == period_id, models.PayrollRecord.user_id == user_id).first()
    
    if not existing:
        existing = models.PayrollRecord(
            period_id=period_id,
            user_id=user_id,
            status="draft"
        )
        db.add(existing)
        db.commit() # Commit to get ID
        db.refresh(existing)
        
    # 4. Update Record Fields
    existing.total_effective = data.total_effective
    existing.total_censuses = data.total_censuses
    existing.total_enp = data.total_enp
    existing.total_training_days = data.total_training
    existing.total_amount = total
    existing.details_json = json.dumps(details)
    
    # Audit
    existing.last_modified_by = current_user.username
    # updated_at will be set automatically by SQLAlchemy onupdate if supported, or we can force it
    # updated_at will be set automatically by SQLAlchemy onupdate if supported, or we can force it
    existing.updated_at = datetime.now() # Explicit update to be safe
    
    # 5. Connect Dynamic Items (PayrollRecordItem)
    # Clear old items (Simpler to clear and re-add for manual edits)
    # We might want to be careful if we want to preserve history, but usually manual edit overwrites current state.
    db.query(models.PayrollRecordItem).filter(models.PayrollRecordItem.record_id == existing.id).delete()
    

    
    if data.items:
        for item in data.items:
            qty = item.quantity
            # Allow negative quantities for deductions!
            if qty != 0:
                concept = period_concepts.get(str(item.concept_id))
                if concept:
                    amt = qty * concept.rate
                    total += amt
                    
                    # Parse date
                    item_date = None
                    if item.date:
                        try:
                            item_date = datetime.strptime(item.date, "%Y-%m-%d")
                        except: pass
                    
                    details.append({
                        "concept": concept.name, 
                        "qty": qty, 
                        "rate": concept.rate, 
                        "total": amt,
                        "concept_id": concept.id,
                        "date": item.date
                    })
                    
                    db.add(models.PayrollRecordItem(
                        record_id=existing.id,
                        concept_id=concept.id,
                        quantity=qty,
                        rate=concept.rate,
                        total=amt,
                        date=item_date
                    ))
    
    # Update total with new items calc
    # Note: Legacy calc above added to 'total'. Dynamic calc adds to 'total'.
    existing.total_amount = total
    db.commit()
    return existing



@app.get("/payroll/records/{period_id}")
def get_payroll_records(period_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.PayrollRecord).filter(models.PayrollRecord.period_id == period_id).all()

@app.get("/payroll/records/by-user/{user_id}")
def get_user_records_admin(user_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role not in ['superuser', 'coordinator', 'supervisor']:
         raise HTTPException(403, "Not authorized")

    records = db.query(models.PayrollRecord).filter(models.PayrollRecord.user_id == user_id).all()
    
    # Enrich with Period Name and verify visibility
    res = []
    for r in records:
        # Safety check for orphaned records
        if not r.period: 
            continue
            
        # STRICT REQUIREMENT: Only show ACTIVE (visible) periods for global print/view.
        # User explicitly requested to exclude old/inactive studies even for admins in this view.
        if not r.period.is_visible:
             continue
             
        res.append({
            "period_id": r.period_id,
            "period_name": r.period.name,
            "study_code": r.period.study_code,
            "total_effective": r.total_effective,
            "total_censuses": r.total_censuses,
            "total_amount": r.total_amount,
            "details_json": r.details_json,
            "total_amount": r.total_amount,
            "details_json": r.details_json,
            "created_at": r.period.created_at,
            "last_modified_by": r.last_modified_by,
            "updated_at": r.updated_at
        })
    return res

@app.get("/payroll/active-users")
def get_active_payroll_users(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role not in ['superuser', 'coordinator', 'supervisor']:
         raise HTTPException(403, "Not authorized")

    # Distinct query: Join Record -> Period
    # Where Period.is_visible = True
    users = db.query(models.User).join(models.PayrollRecord).join(models.PayrollPeriod).filter(models.PayrollPeriod.is_visible == True).distinct().all()
    
    return [{"id": u.id, "full_name": u.full_name, "username": u.username} for u in users]

@app.get("/nomina-page")
async def nomina_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "nomina.html"))
