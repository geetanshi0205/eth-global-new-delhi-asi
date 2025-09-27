from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .db_config import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)  # Combined name field
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, index=True, unique=True)
    phone = Column(String)
    date_of_birth = Column(Date)
    gender = Column(String)
    address = Column(Text)
    emergency_contact = Column(String)
    emergency_phone = Column(String)
    insurance_info = Column(Text)
    medical_history = Column(Text)
    allergies = Column(Text)
    current_medications = Column(Text)
    notes = Column(Text)  # Additional notes
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
    patient_email = Column(String, nullable=False, index=True)  # For quick lookup
    patient_name = Column(String, nullable=False)
    appointment_type = Column(String, nullable=False, default="consultation")  # 'doctor' or 'lab'
    appointment_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer, default=30)
    status = Column(String, default="scheduled")  # scheduled, completed, cancelled, no_show
    cal_com_booking_id = Column(String, index=True)  # Cal.com booking ID
    cal_com_booking_uid = Column(String, index=True)  # Cal.com booking UID
    event_type_id = Column(String)  # Which event type was used
    api_key_used = Column(String)  # Which API key was used (for tracking)
    doctor_id = Column(String, default="default_doctor")
    doctor_name = Column(String)
    lab_name = Column(String)  # For lab appointments
    location = Column(String)
    timezone = Column(String, default="Asia/Kolkata")
    language = Column(String, default="en")
    notes = Column(Text)  # Patient notes
    doctor_notes = Column(Text)  # Doctor's notes after appointment
    diagnosis = Column(Text)  # Diagnosis from appointment
    symptoms = Column(Text)  # Symptoms reported
    treatment_plan = Column(Text)  # Treatment plan
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime(timezone=True))
    urgency_level = Column(String, default="routine")  # emergency, urgent, moderate, routine
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