from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True) # CC or Email
    hashed_password = Column(String)
    role = Column(String, default="agent") # admin, agent
    
    observations = relationship("Observation", back_populates="user")
    schedules = relationship("Schedule", back_populates="user")

class Study(Base):
    __tablename__ = "studies"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String)
    status = Column(String, default="open") # open, closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # New Fields
    study_type = Column(String, nullable=True) # 'validacion', 'fatiga'
    stage = Column(String, nullable=True) # 'R1', 'R2', 'Rf', etc.

    calls = relationship("Call", back_populates="study")

class Call(Base):
    __tablename__ = "calls"
    
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"))
    
    phone_number = Column(String, index=True)
    corrected_phone = Column(String, nullable=True)
    person_cc = Column(String, nullable=True) # CC of the person called
    person_name = Column(String, nullable=True)
    status = Column(String, default="pending") 
    
    # New Fields
    city = Column(String, nullable=True)
    initial_observation = Column(Text, nullable=True)
    appointment_time = Column(String, nullable=True) # "Hora de llamada" from Excel
    product_brand = Column(String, nullable=True)
    extra_phone = Column(String, nullable=True) # "Otro numero"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Assigned Agent
    
    study = relationship("Study", back_populates="calls")
    observations = relationship("Observation", back_populates="call")
    schedules = relationship("Schedule", back_populates="call")
    user = relationship("User") # Relationship to Agent

class Observation(Base):
    __tablename__ = "observations"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("calls.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
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
