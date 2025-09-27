from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from .db_config import get_db
from .models import PatientReport, PublishedReport

def init_database():
    """Initialize database with tables"""
    from .db_config import create_tables
    create_tables()


class PatientReportOperations:
    @staticmethod
    def add_report(patient_email: str, report_type: str, report_content: str, test_date: datetime) -> PatientReport:
        """Add a new patient report"""
        db = get_db()
        try:
            report = PatientReport(
                patient_email=patient_email,
                report_type=report_type,
                report_content=report_content,
                test_date=test_date
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            return report
        finally:
            db.close()

    @staticmethod
    def get_reports(patient_email: str, report_type: Optional[str] = None, test_date: Optional[datetime] = None) -> List[PatientReport]:
        """Retrieve patient reports by email, optionally filtered by type and date"""
        db = get_db()
        try:
            query = db.query(PatientReport).filter(PatientReport.patient_email == patient_email)
            if report_type:
                query = query.filter(PatientReport.report_type == report_type)
            if test_date:
                query = query.filter(PatientReport.test_date == test_date)
            return query.order_by(desc(PatientReport.test_date)).all()
        finally:
            db.close()

    @staticmethod
    def get_report_by_id(report_id: str) -> Optional[PatientReport]:
        """Get a patient report by its ID"""
        db = get_db()
        try:
            return db.query(PatientReport).filter(PatientReport.id == report_id).first()
        finally:
            db.close()

    @staticmethod
    def get_all_reports(limit: int = 50) -> List[PatientReport]:
        """Get all patient reports with limit"""
        db = get_db()
        try:
            return db.query(PatientReport).order_by(desc(PatientReport.created_at)).limit(limit).all()
        finally:
            db.close()

    @staticmethod
    def verify_patient_access(report_id: str, patient_email: str, mpin: str) -> bool:
        """Verify if patient has access to the report using email and MPIN"""
        db = get_db()
        try:
            report = db.query(PatientReport).filter(
                PatientReport.id == report_id,
                PatientReport.patient_email == patient_email,
                PatientReport.mpin == mpin
            ).first()
            return report is not None
        finally:
            db.close()

    @staticmethod
    def add_report_with_mpin(
        patient_email: str, 
        mpin: str, 
        report_type: str, 
        report_content: str, 
        test_date: datetime
    ) -> PatientReport:
        """Add a new patient report with MPIN for authentication"""
        db = get_db()
        try:
            report = PatientReport(
                patient_email=patient_email,
                mpin=mpin,
                report_type=report_type,
                report_content=report_content,
                test_date=test_date
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            return report
        finally:
            db.close()


class PublishedReportOperations:
    @staticmethod
    def publish_report(
        original_report_id: str, 
        anonymized_content: str, 
        title: str, 
        price_eth: str = "0.000001",
        wallet_address: str = None,
        description: str = None, 
        tags: str = None
    ) -> PublishedReport:
        """Publish an anonymized report to the marketplace"""
        db = get_db()
        try:
            # Get original report to copy metadata
            original_report = db.query(PatientReport).filter(PatientReport.id == original_report_id).first()
            if not original_report:
                raise ValueError(f"Original report with ID {original_report_id} not found")
            
            published_report = PublishedReport(
                original_report_id=original_report_id,
                anonymized_content=anonymized_content,
                report_type=original_report.report_type,
                test_date=original_report.test_date,
                title=title,
                price_eth=price_eth,
                wallet_address=wallet_address,
                description=description,
                tags=tags
            )
            db.add(published_report)
            db.commit()
            db.refresh(published_report)
            return published_report
        finally:
            db.close()

    @staticmethod
    def get_published_reports(
        report_type: Optional[str] = None, 
        tags: Optional[str] = None, 
        limit: int = 50
    ) -> List[PublishedReport]:
        """Get published reports from marketplace"""
        db = get_db()
        try:
            query = db.query(PublishedReport).filter(PublishedReport.is_active == True)
            if report_type:
                query = query.filter(PublishedReport.report_type == report_type)
            if tags:
                query = query.filter(PublishedReport.tags.contains(tags))
            return query.order_by(desc(PublishedReport.published_at)).limit(limit).all()
        finally:
            db.close()