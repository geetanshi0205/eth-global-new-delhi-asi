from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .db_config import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)  # Combined name field to match existing schema
    email = Column(String, index=True)
    phone = Column(String)
    notes = Column(Text)  # Using notes field from existing schema for additional info
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    appointments = relationship("Appointment", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    reports = relationship("Report", back_populates="patient")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(String, nullable=False, default="default_doctor")
    appointment_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="scheduled")
    cal_com_event_id = Column(String, index=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    prescriptions = relationship("Prescription", back_populates="appointment")
    reports = relationship("Report", back_populates="appointment")

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"))
    medication_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    duration = Column(String)
    instructions = Column(Text)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    refills_remaining = Column(Integer, default=0)
    prescribed_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    appointment = relationship("Appointment", back_populates="prescriptions")

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"))
    report_type = Column(String, nullable=False)  # e.g., "lab_test", "imaging", "consultation"
    title = Column(String, nullable=False)
    description = Column(Text)
    file_url = Column(String)  # URL to the report file if stored externally
    report_data = Column(Text)  # JSON or text data of the report
    report_date = Column(DateTime(timezone=True), nullable=False)
    doctor_name = Column(String)
    lab_name = Column(String)
    status = Column(String, default="available")  # "pending", "available", "reviewed"
    is_critical = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="reports")
    appointment = relationship("Appointment", back_populates="reports")