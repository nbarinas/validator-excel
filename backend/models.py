from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True) # specified length for MySQL
    hashed_password = Column(String(255)) # specified length
    role = Column(String(20), default="agent") # specified length
    last_seen = Column(DateTime(timezone=True), nullable=True)
    
    # New Fields
    full_name = Column(String(100), nullable=True)
    bank = Column(String(50), nullable=True) # Banco Caja Social, Bancolombia, etc.
    account_type = Column(String(20), nullable=True) # Ahorros, Corriente
    account_number = Column(String(50), nullable=True)
    birth_date = Column(String(20), nullable=True) # Storing as string for simplicity or Date
    phone_number = Column(String(20), nullable=True)
    address = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    neighborhood = Column(String(100), nullable=True) # Barrio
    blood_type = Column(String(10), nullable=True) # Tipo de sangre
    account_holder = Column(String(100), nullable=True) # Titular
    account_holder_cc = Column(String(20), nullable=True) # CC Titular

    calls = relationship("Call", foreign_keys="Call.user_id", back_populates="user")
    observations = relationship("Observation", back_populates="user")
    schedules = relationship("Schedule", back_populates="user")
    assigned_studies = relationship("Study", secondary="study_assignments", back_populates="assistants")

from sqlalchemy import Table

# Association Table for Auxiliar <-> Study
study_assignments = Table('study_assignments', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('study_id', Integer, ForeignKey('studies.id'))
)

class Study(Base):
    __tablename__ = "studies"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True)
    name = Column(String(100))
    status = Column(String(20), default="open") # open, closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # New Fields
    study_type = Column(String(50), nullable=True) # 'validacion', 'fatiga'
    stage = Column(String(20), nullable=True) # 'R1', 'R2', 'Rf', etc.
    is_active = Column(Boolean, default=True) # Soft delete / Hide functionality

    calls = relationship("Call", back_populates="study")
    assistants = relationship("User", secondary=study_assignments, back_populates="assigned_studies")

class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    phone_number = Column(String(20), index=True)
    code = Column(String(50), nullable=True) # Codigo del registro (Excel)
    person_name = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    status = Column(String(20), default="pending") # pending, managed, closed
    
    # New Fields
    observation = Column(String(500), nullable=True) # Legacy simple obs
    product_brand = Column(String(100), nullable=True)
    initial_observation = Column(String(500), nullable=True)
    appointment_time = Column(DateTime, nullable=True) # For scheduling
    extra_phone = Column(String(20), nullable=True)
    
    # Contact info updates
    corrected_phone = Column(String(20), nullable=True)
    person_cc = Column(String(20), nullable=True)
    census = Column(String(50), nullable=True) # New field requested

    # Census / Demographic Data
    nse = Column(String(50), nullable=True)
    age = Column(String(20), nullable=True)
    age_range = Column(String(50), nullable=True)
    children_age = Column(String(200), nullable=True)
    whatsapp = Column(String(50), nullable=True)
    neighborhood = Column(String(200), nullable=True)
    address = Column(String(300), nullable=True)
    housing_description = Column(String(300), nullable=True)
    respondent = Column(String(100), nullable=True)
    supervisor = Column(String(100), nullable=True)
    implantation_date = Column(String(50), nullable=True) # Keeping as string for flexibility unless strictly DateTime
    collection_date = Column(String(50), nullable=True)
    collection_time = Column(String(50), nullable=True)
    
    # Survey and Bonus tracking (when managed)
    survey_id = Column(String(100), nullable=True) # Alphanumeric survey identifier
    bonus_status = Column(String(20), nullable=True) # 'enviado' or 'no enviado'
    
    # Second Pickup & Product Info
    second_collection_date = Column(String(50), nullable=True) # Fecha 2 recogida
    second_collection_time = Column(String(50), nullable=True) # Hora 2 recogida
    shampoo_quantity = Column(String(50), nullable=True) # Cantidad Shampoo
    
    # Hair Study Specifics
    shampoo_brand = Column(String(100), nullable=True) # Marca Shampoo
    shampoo_variety = Column(String(100), nullable=True) # Variedad Shampoo
    conditioner_brand = Column(String(100), nullable=True) # Marca Acondicionador
    conditioner_variety = Column(String(100), nullable=True) # Variedad Acondicionador
    treatment_brand = Column(String(100), nullable=True) # Marca Tratamiento
    treatment_variety = Column(String(100), nullable=True) # Variedad Tratamiento
    wash_frequency = Column(String(100), nullable=True) # Frecuencia Lavado
    hair_type = Column(String(50), nullable=True) # Tipo Cabello
    hair_shape = Column(String(50), nullable=True) # Forma Cabello
    hair_length = Column(String(50), nullable=True) # Largo Cabello
    
    # New Requested Fields
    realization_date = Column(DateTime(timezone=True), nullable=True) # Fecha de Realización (Auto on action)
    temp_armando = Column(Text, nullable=True) # Temporal Armando (Superuser only)
    temp_auxiliar = Column(Text, nullable=True) # Temporal Auxiliar (Superuser & Auxiliar)
    
    previous_user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Tracks previous agent

    # Dog Food Study Fields
    dog_name = Column(String(100), nullable=True)
    dog_user_type = Column(String(50), nullable=True) # Mezclador, etc.
    dog_breed = Column(String(100), nullable=True) # Raza
    dog_size = Column(String(50), nullable=True) # Tamaño
    stool_texture = Column(String(200), nullable=True)
    health_status = Column(String(200), nullable=True)

    # New Requested Columns
    purchase_frequency = Column(String(100), nullable=True) # Frecuencia de Compra
    implantation_pollster = Column(String(100), nullable=True) # Encuestador Implante

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    study = relationship("Study", back_populates="calls")
    user = relationship("User", foreign_keys=[user_id], back_populates="calls")
    previous_user = relationship("User", foreign_keys=[previous_user_id]) # Relationship for access
    observations = relationship("Observation", back_populates="call")
    schedules = relationship("Schedule", back_populates="call")

class Observation(Base):
    __tablename__ = "observations"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("calls.id"))
    user_id = Column(Integer, ForeignKey("users.id")) # Kept this as it was in the original, not removed as in the example.
    
    text = Column(String(1000))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    call = relationship("Call", back_populates="observations")
    user = relationship("User", back_populates="observations")

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("calls.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    scheduled_time = Column(DateTime)
    alert_shown = Column(Boolean, default=False)
    
    call = relationship("Call", back_populates="schedules")
    user = relationship("User", back_populates="schedules")

class BizageStudy(Base):
    __tablename__ = "bizage_studies"

    id = Column(Integer, primary_key=True, index=True)
    study_type = Column(String(50)) # ascensor, in home, test de compra, seguimiento de marca, nuevo
    study_name = Column(String(100))
    n_value = Column(Integer)
    survey_no_participa = Column(String(200), nullable=True) # Notes/Status
    
    # Financials
    quantity = Column(Integer, nullable=True) 
    price = Column(Integer, nullable=True)
    copies = Column(Integer, nullable=True)
    copies_price = Column(Integer, nullable=True) # Added price
    vinipel = Column(Integer, nullable=True) # Now represents "Contac" / Vinipel
    vinipel_price = Column(Integer, nullable=True) # Added price
    other_cost_description = Column(String(100), nullable=True) # "Otro que se pueda digitar"
    other_cost_amount = Column(Integer, nullable=True)
    census = Column(String(100), nullable=True) # For Ascensor study
    
    # Bizagi
    bizagi_number = Column(String(50), nullable=True)
    
    # Status
    status = Column(String(50), default="registered") # registered, radicated, number_assigned, paid
    
    # Timestamps & Audits
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    registered_by = Column(String(50), nullable=True) # Username
    
    radicated_at = Column(DateTime(timezone=True), nullable=True)
    radicated_by = Column(String(50), nullable=True)
    
    bizagi_at = Column(DateTime(timezone=True), nullable=True)
    bizagi_by = Column(String(50), nullable=True)
    
    paid_at = Column(DateTime(timezone=True), nullable=True)
    paid_by = Column(String(50), nullable=True)
    invoice_number = Column(String(50), nullable=True) # Numero de factura

class RateSheet(Base):
    __tablename__ = "rate_sheets"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, unique=True, index=True) # 2025, 2026
    description = Column(String(100))
    is_active = Column(Boolean, default=True)
    
    # Storing rates as separate columns for clarity, or JSON. 
    # Validacion / Normal Rates
    census_rate = Column(Integer, default=0)
    survey_effective_rate = Column(Integer, default=0)
    enp_rate = Column(Integer, default=0) # Encuesta No Participa / Rechazo
    training_rate = Column(Integer, default=0) # Dia de entrenamiento
    
    # Bizage / In Home specific base rates if needed
    # But usually per-study rates might differ. 
    # For now, let's assume these are global base rates or defaults.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PayrollPeriod(Base):
    __tablename__ = "payroll_periods"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100)) # e.g. "Primera Quincena Enero 2026"
    study_id = Column(Integer, ForeignKey("studies.id"), nullable=True) # Optional link
    study_type = Column(String(50), nullable=True) # ascensor, in_home, tdc
    study_code = Column(String(50), nullable=True) # New Code
    execution_date = Column(DateTime, nullable=True)
    rates_snapshot = Column(String(500), nullable=True) # JSON
    
    start_date = Column(DateTime, nullable=True) 
    end_date = Column(DateTime, nullable=True)
    is_visible = Column(Boolean, default=True) # Visibility toggle
    status = Column(String(20), default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    records = relationship("PayrollRecord", back_populates="period")
    study = relationship("Study") # Relationship

class PayrollRecord(Base):
    __tablename__ = "payroll_records"
    
    id = Column(Integer, primary_key=True, index=True)
    period_id = Column(Integer, ForeignKey("payroll_periods.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Counts
    days_worked = Column(Integer, default=0)
    total_censuses = Column(Integer, default=0)
    total_effective = Column(Integer, default=0)
    total_enp = Column(Integer, default=0)
    total_training_days = Column(Integer, default=0)
    
    # Money
    total_amount = Column(Integer, default=0) # Sum of all calculated
    adjustments = Column(Integer, default=0) # Manual +/-
    
    # JSON breakdown for the detailed table in PDF
    # Structure: [ { "study_name": "Studio 1", "dates": "...", "concept": "Encuesta", "qty": 10, "rate": 1000, "total": 10000 }, ... ]
    details_json = Column(Text, nullable=True) 
    
    status = Column(String(20), default="draft") # draft, approved
    
    period = relationship("PayrollPeriod", back_populates="records")
    user = relationship("User", back_populates="payroll_records")

# Backref alias for User
User.payroll_records = relationship("PayrollRecord", back_populates="user")
