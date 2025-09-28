from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import OperationalError, TimeoutError
from typing import List, Optional
from datetime import datetime
import time
import logging
from .db_config import get_db
from .models import PatientReport, PublishedReport

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retry_db_operation(func, max_retries=3, delay=1):
    """Retry database operation with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except (OperationalError, TimeoutError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(delay * (2 ** attempt))

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
        description: str = None, 
        tags: str = None,
        price_eth: float = 0.001,
        seller_wallet: str = None
    ) -> PublishedReport:
        """Publish an anonymized report to the marketplace"""
        db = get_db()
        try:
            # Get original report to copy metadata
            original_report = db.query(PatientReport).filter(PatientReport.id == original_report_id).first()
            if not original_report:
                raise ValueError(f"Original report with ID {original_report_id} not found")
            
            if not seller_wallet:
                raise ValueError("Seller wallet address is required")
            
            published_report = PublishedReport(
                original_report_id=original_report_id,
                anonymized_content=anonymized_content,
                report_type=original_report.report_type,
                test_date=original_report.test_date,
                title=title,
                description=description,
                tags=tags,
                price_eth=price_eth,
                seller_wallet=seller_wallet
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
        limit: int = 20
    ) -> List[PublishedReport]:
        """Get published reports from marketplace"""
        def _get_reports():
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
        
        return retry_db_operation(_get_reports)

    @staticmethod
    def get_published_report_by_id(report_id: str) -> Optional[PublishedReport]:
        """Get a specific published report by ID"""
        db = get_db()
        try:
            return db.query(PublishedReport).filter(PublishedReport.id == report_id).first()
        finally:
            db.close()