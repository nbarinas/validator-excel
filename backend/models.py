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

    calls = relationship("Call", back_populates="user")
    observations = relationship("Observation", back_populates="user")
    schedules = relationship("Schedule", back_populates="user")

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

    calls = relationship("Call", back_populates="study")

class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    phone_number = Column(String(20), index=True)
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
    corrected_phone = Column(String(20), nullable=True)
    person_cc = Column(String(20), nullable=True)
    census = Column(String(50), nullable=True) # New field requested
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    study = relationship("Study", back_populates="calls")
    user = relationship("User", back_populates="calls")
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
