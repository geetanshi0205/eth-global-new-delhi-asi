from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .db_config import get_db
from .models import Patient, Appointment, Prescription, Report

class PatientOperations:
    
    @staticmethod
    def get_or_create_patient(email: str, first_name: str, last_name: str, **kwargs) -> Patient:
        """Get existing patient or create new one"""
        db = get_db()
        try:
            patient = db.query(Patient).filter(Patient.email == email).first()
            
            if not patient:
                full_name = f"{first_name} {last_name}".strip()
                # Extract relevant fields that match the existing schema
                notes = kwargs.get('notes', '')
                if kwargs.get('medical_history'):
                    notes += f"\nMedical History: {kwargs['medical_history']}"
                if kwargs.get('allergies'):
                    notes += f"\nAllergies: {kwargs['allergies']}"
                if kwargs.get('current_medications'):
                    notes += f"\nCurrent Medications: {kwargs['current_medications']}"
                    
                patient = Patient(
                    name=full_name,
                    email=email,
                    phone=kwargs.get('phone'),
                    notes=notes.strip()
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)
            
            return patient
        finally:
            db.close()
    
    @staticmethod
    def get_patient_by_email(email: str) -> Optional[Patient]:
        """Get patient by email"""
        db = get_db()
        try:
            return db.query(Patient).filter(Patient.email == email).first()
        finally:
            db.close()
    
    @staticmethod
    def update_patient(email: str, **kwargs) -> Optional[Patient]:
        """Update patient information"""
        db = get_db()
        try:
            patient = db.query(Patient).filter(Patient.email == email).first()
            if patient:
                for key, value in kwargs.items():
                    if hasattr(patient, key):
                        setattr(patient, key, value)
                patient.updated_at = datetime.now()
                db.commit()
                db.refresh(patient)
            return patient
        finally:
            db.close()
    
    @staticmethod
    def get_patient_appointments(email: str, include_past: bool = False) -> List[Appointment]:
        """Get appointments for a patient"""
        db = get_db()
        try:
            patient = db.query(Patient).filter(Patient.email == email).first()
            if not patient:
                return []
            
            query = db.query(Appointment).filter(Appointment.patient_id == patient.id)
            
            if not include_past:
                query = query.filter(Appointment.appointment_time >= datetime.now())
            
            return query.order_by(Appointment.appointment_time).all()
        finally:
            db.close()
    
    @staticmethod
    def get_patient_prescriptions(email: str, active_only: bool = True) -> List[Prescription]:
        """Get prescriptions for a patient"""
        db = get_db()
        try:
            patient = db.query(Patient).filter(Patient.email == email).first()
            if not patient:
                return []
            
            query = db.query(Prescription).filter(Prescription.patient_id == patient.id)
            
            if active_only:
                query = query.filter(Prescription.is_active == True)
            
            return query.order_by(desc(Prescription.created_at)).all()
        finally:
            db.close()

class AppointmentOperations:
    
    @staticmethod
    def create_appointment(
        patient_email: str,
        appointment_date: datetime,
        cal_booking_id: str = None,
        **kwargs
    ) -> Appointment:
        """Create new appointment"""
        db = get_db()
        try:
            patient = PatientOperations.get_patient_by_email(patient_email)
            if not patient:
                raise ValueError(f"Patient with email {patient_email} not found")
            
            appointment = Appointment(
                patient_id=patient.id,
                appointment_time=appointment_date,
                cal_com_event_id=cal_booking_id,
                status=kwargs.get('status', 'scheduled'),
                notes=kwargs.get('notes'),
                doctor_id=kwargs.get('doctor_id', 'default_doctor')
            )
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
            return appointment
        finally:
            db.close()
    
    @staticmethod
    def update_appointment(appointment_id: int, **kwargs) -> Optional[Appointment]:
        """Update appointment information"""
        db = get_db()
        try:
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            if appointment:
                for key, value in kwargs.items():
                    if hasattr(appointment, key):
                        setattr(appointment, key, value)
                appointment.updated_at = datetime.now()
                db.commit()
                db.refresh(appointment)
            return appointment
        finally:
            db.close()
    
    @staticmethod
    def get_appointment_by_cal_id(cal_booking_id: str) -> Optional[Appointment]:
        """Get appointment by Cal.com booking ID"""
        db = get_db()
        try:
            return db.query(Appointment).filter(Appointment.cal_com_event_id == cal_booking_id).first()
        finally:
            db.close()

class PrescriptionOperations:
    
    @staticmethod
    def create_prescription(
        patient_email: str,
        medication_name: str,
        dosage: str,
        frequency: str,
        appointment_id: int = None,
        **kwargs
    ) -> Prescription:
        """Create new prescription"""
        db = get_db()
        try:
            patient = PatientOperations.get_patient_by_email(patient_email)
            if not patient:
                raise ValueError(f"Patient with email {patient_email} not found")
            
            prescription = Prescription(
                patient_id=patient.id,
                appointment_id=appointment_id,
                medication_name=medication_name,
                dosage=dosage,
                frequency=frequency,
                **kwargs
            )
            db.add(prescription)
            db.commit()
            db.refresh(prescription)
            return prescription
        finally:
            db.close()
    
    @staticmethod
    def update_prescription(prescription_id: int, **kwargs) -> Optional[Prescription]:
        """Update prescription information"""
        db = get_db()
        try:
            prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
            if prescription:
                for key, value in kwargs.items():
                    if hasattr(prescription, key):
                        setattr(prescription, key, value)
                prescription.updated_at = datetime.now()
                db.commit()
                db.refresh(prescription)
            return prescription
        finally:
            db.close()
    
    @staticmethod
    def deactivate_prescription(prescription_id: int) -> Optional[Prescription]:
        """Deactivate a prescription"""
        return PrescriptionOperations.update_prescription(prescription_id, is_active=False)

class PatientDataManager:
    """Comprehensive patient data management"""
    
    @staticmethod
    def get_comprehensive_patient_data(email: str) -> Dict[str, Any]:
        """Get all patient data including appointments and prescriptions"""
        patient = PatientOperations.get_patient_by_email(email)
        if not patient:
            return {"error": f"Patient with email {email} not found"}
        
        appointments = PatientOperations.get_patient_appointments(email, include_past=True)
        prescriptions = PatientOperations.get_patient_prescriptions(email, active_only=False)
        
        return {
            "patient": {
                "id": patient.id,
                "email": patient.email,
                "name": patient.name,
                "phone": patient.phone,
                "notes": patient.notes,
                "created_at": patient.created_at,
                "updated_at": patient.updated_at
            },
            "appointments": [
                {
                    "id": apt.id,
                    "date": apt.appointment_time,
                    "status": apt.status,
                    "notes": apt.notes,
                    "doctor_id": apt.doctor_id,
                    "cal_booking_id": apt.cal_com_event_id
                } for apt in appointments
            ],
            "prescriptions": [
                {
                    "id": rx.id,
                    "medication": rx.medication_name,
                    "dosage": rx.dosage,
                    "frequency": rx.frequency,
                    "duration": rx.duration,
                    "instructions": rx.instructions,
                    "start_date": rx.start_date,
                    "end_date": rx.end_date,
                    "is_active": rx.is_active,
                    "refills_remaining": rx.refills_remaining,
                    "prescribed_by": rx.prescribed_by,
                    "created_at": rx.created_at
                } for rx in prescriptions
            ]
        }
    
    @staticmethod
    def search_patients(query: str) -> List[Dict[str, Any]]:
        """Search patients by name or email"""
        db = get_db()
        try:
            search_term = f"%{query}%"
            patients = db.query(Patient).filter(
                or_(
                    Patient.name.ilike(search_term),
                    Patient.email.ilike(search_term)
                )
            ).limit(10).all()
            
            return [
                {
                    "id": patient.id,
                    "email": patient.email,
                    "name": patient.name,
                    "phone": patient.phone
                } for patient in patients
            ]
        finally:
            db.close()

class ReportOperations:

    @staticmethod
    def get_patient_reports(email: str, report_type: Optional[str] = None,
                           test_date: Optional[datetime] = None,
                           include_pending: bool = True) -> List[Dict[str, Any]]:
        """Get reports for a patient by email"""
        db = get_db()
        try:
            patient = db.query(Patient).filter(Patient.email == email).first()
            if not patient:
                return []

            query = db.query(Report).filter(Report.patient_id == patient.id)

            if report_type:
                query = query.filter(Report.report_type == report_type)

            if test_date:
                # Filter by test date (report_date field)
                query = query.filter(Report.report_date == test_date.date())

            if not include_pending:
                query = query.filter(Report.status != "pending")

            reports = query.order_by(desc(Report.report_date)).all()

            return [
                {
                    "id": str(report.id),
                    "title": report.title,
                    "report_type": report.report_type,
                    "description": report.description,
                    "report_date": report.report_date.isoformat() if report.report_date else None,
                    "doctor_name": report.doctor_name,
                    "lab_name": report.lab_name,
                    "status": report.status,
                    "is_critical": report.is_critical,
                    "file_url": report.file_url,
                    "report_data": report.report_data,
                    "created_at": report.created_at.isoformat() if report.created_at else None
                } for report in reports
            ]
        finally:
            db.close()

    @staticmethod
    def create_report(patient_email: str, title: str, report_type: str,
                     report_date: datetime, **kwargs) -> Optional[Dict[str, Any]]:
        """Create a new report for a patient"""
        db = get_db()
        try:
            patient = db.query(Patient).filter(Patient.email == patient_email).first()
            if not patient:
                return None

            report = Report(
                patient_id=patient.id,
                title=title,
                report_type=report_type,
                report_date=report_date,
                description=kwargs.get('description'),
                file_url=kwargs.get('file_url'),
                report_data=kwargs.get('report_data'),
                doctor_name=kwargs.get('doctor_name'),
                lab_name=kwargs.get('lab_name'),
                status=kwargs.get('status', 'available'),
                is_critical=kwargs.get('is_critical', False),
                appointment_id=kwargs.get('appointment_id')
            )

            db.add(report)
            db.commit()
            db.refresh(report)

            return {
                "id": str(report.id),
                "title": report.title,
                "report_type": report.report_type,
                "status": report.status,
                "created_at": report.created_at.isoformat()
            }
        finally:
            db.close()

    @staticmethod
    def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific report by ID"""
        db = get_db()
        try:
            report = db.query(Report).filter(Report.id == report_id).first()
            if not report:
                return None

            return {
                "id": str(report.id),
                "title": report.title,
                "report_type": report.report_type,
                "description": report.description,
                "report_date": report.report_date.isoformat() if report.report_date else None,
                "doctor_name": report.doctor_name,
                "lab_name": report.lab_name,
                "status": report.status,
                "is_critical": report.is_critical,
                "file_url": report.file_url,
                "report_data": report.report_data,
                "patient_email": report.patient.email if report.patient else None,
                "created_at": report.created_at.isoformat() if report.created_at else None
            }
        finally:
            db.close()

def init_database():
    """Initialize database with tables"""
    from .db_config import create_tables
    create_tables()