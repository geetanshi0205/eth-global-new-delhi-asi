from typing import Any, Optional
import httpx
import os
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import re

# Knowledge graph components removed

# Import database components
from database.operations import (
    PatientOperations, AppointmentOperations, PrescriptionOperations, 
    PatientDataManager, init_database, PatientReportOperations
)

# Import email service
from email_service import EmailService

# Load environment variables from .env file
load_dotenv()

# Create a FastMCP server instance
mcp = FastMCP("cal-doctor-appointments")

# Initialize database
init_database()

# Initialize email service
email_service = EmailService()

CAL_API_V1_BASE = "https://api.cal.com/v1"
CAL_API_V2_BASE = "https://api.cal.com/v2"
USER_AGENT = "lab-agent/1.0"

# Indian defaults
DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_LANGUAGE = "en"

# ... existing code ...

def get_default_event_type_id() -> int:
    """Get default event type ID from environment"""
    event_type_id = os.getenv("EVENT_TYPE_ID")
    if not event_type_id:
        raise ValueError("EVENT_TYPE_ID environment variable is required")
    return int(event_type_id)

# ... existing code ...

def parse_date_string(date_str: str) -> datetime:
    """Parse various date formats into datetime object"""
    date_str = date_str.strip()
    
    # Try ISO format first (fastest)
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        pass
    
    # Map month abbreviations to full names for strptime
    month_map = {
        'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Apr': 'April',
        'May': 'May', 'Jun': 'June', 'Jul': 'July', 'Aug': 'August',
        'Sep': 'September', 'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
    }
    
    # Try different formats
    formats_to_try = [
        # DD Month YYYY (e.g., "27 September 2025")
        '%d %B %Y',
        # DD Mon YYYY (e.g., "27 Sep 2025") 
        '%d %b %Y',
        # Month DD, YYYY (e.g., "September 27, 2025")
        '%B %d, %Y',
        # Month DD YYYY (e.g., "September 27 2025")
        '%B %d %Y',
        # Mon DD, YYYY (e.g., "Sep 27, 2025")
        '%b %d, %Y',
        # Mon DD YYYY (e.g., "Sep 27 2025")
        '%b %d %Y',
        # DD/MM/YYYY
        '%d/%m/%Y',
        # MM/DD/YYYY  
        '%m/%d/%Y',
        # DD-MM-YYYY
        '%d-%m-%Y',
        # MM-DD-YYYY
        '%m-%d-%Y',
        # YYYY-MM-DD
        '%Y-%m-%d',
        # YYYY/MM/DD
        '%Y/%m/%d'
    ]
    
    for fmt in formats_to_try:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try expanding abbreviated months
    for abbrev, full in month_map.items():
        if abbrev in date_str:
            expanded_date = date_str.replace(abbrev, full)
            for fmt in formats_to_try:
                try:
                    return datetime.strptime(expanded_date, fmt)
                except ValueError:
                    continue
    
    # If no format works, raise an error
    raise ValueError(f"Unable to parse date: {date_str}")

@mcp.tool()
async def add_patient_report(
    patient_email: str,
    report_type: str,
    report_content: str,
    test_date: str
) -> str:
    """Add a new patient test report for a patient by email.

    Args:
        patient_email: Patient's email address (used as identifier)
        report_type: Type of report (e.g., 'blood', 'xray', etc.)
        report_content: The content/details of the report
        test_date: Date of the test/report (e.g., '2025-09-27' or '27 September 2025')
    """
    try:
        # Parse test_date
        try:
            test_date_obj = parse_date_string(test_date)
        except ValueError:
            return "❌ Invalid date format. Please provide the date like '2025-09-27' or a natural format."
        
        # Generate MPIN
        mpin = email_service.generate_mpin()
        
        # Add report to database
        report = PatientReportOperations.add_report(
            patient_email=patient_email,
            report_type=report_type,
            report_content=report_content,
            test_date=test_date_obj,
            mpin=mpin
        )
        
        # Send email notification
        email_sent = email_service.send_report_notification(
            patient_email=patient_email,
            report_id=str(report.id),
            mpin=mpin,
            report_type=report_type
        )
        
        success_msg = f"✅ Report added for {patient_email} (type: {report_type}, date: {test_date_obj.date()})"
        if email_sent:
            success_msg += f" 📧 Email notification sent with Report ID: {report.id}"
        else:
            success_msg += f" ⚠️ Report saved but email notification failed. Report ID: {report.id}"
        
        return success_msg
    except Exception as e:
        return f"❌ Failed to add report: {str(e)}"

@mcp.tool()
async def get_patient_reports(
    patient_email: str,
    report_type: Optional[str] = None,
    test_date: Optional[str] = None
) -> str:
    """Retrieve patient reports from Supabase using email as entity identifier.

    Args:
        patient_email: Patient's email address (used as identifier)
        report_type: Optional filter by report type (e.g., 'blood', 'xray', etc.)
        test_date: Optional filter by test date (e.g., '2025-09-27' or '27 September 2025')
    """
    try:
        # Parse test_date if provided
        test_date_obj = None
        if test_date:
            try:
                test_date_obj = parse_date_string(test_date)
            except ValueError:
                return "❌ Invalid date format. Please provide the date like '2025-09-27' or a natural format."
        
        # Retrieve reports
        reports = PatientReportOperations.get_reports(
            patient_email=patient_email,
            report_type=report_type,
            test_date=test_date_obj
        )
        
        if not reports:
            filters = []
            if report_type:
                filters.append(f"type: {report_type}")
            if test_date:
                filters.append(f"date: {test_date}")
            filter_text = f" with filters ({', '.join(filters)})" if filters else ""
            return f"❌ No reports found for {patient_email}{filter_text}"
        
        # Format response
        result = f"📋 Found {len(reports)} report(s) for {patient_email}:\n\n"
        for i, report in enumerate(reports, 1):
            result += f"{i}. **{report.report_type.upper()}** ({report.test_date.date()})\n"
            result += f"   Content: {report.report_content}\n"
            result += f"   Created: {report.created_at.date()}\n\n"
        
        return result.strip()
    except Exception as e:
        return f"❌ Failed to retrieve reports: {str(e)}"

@mcp.tool()
async def verify_report_access(
    report_id: str,
    mpin: str
) -> str:
    """Verify access to a patient report using Report ID and MPIN.

    Args:
        report_id: The unique report ID
        mpin: The 6-digit MPIN associated with the report
    """
    try:
        report = PatientReportOperations.verify_report_access(report_id, mpin)
        
        if not report:
            return "❌ Invalid Report ID or MPIN. Please check your credentials."
        
        result = f"✅ Report Access Verified\n\n"
        result += f"**Report ID:** {report.id}\n"
        result += f"**Patient Email:** {report.patient_email}\n"
        result += f"**Report Type:** {report.report_type.upper()}\n"
        result += f"**Test Date:** {report.test_date.date()}\n"
        result += f"**Created:** {report.created_at.date()}\n\n"
        result += f"**Report Content:**\n{report.report_content}"
        
        return result
    except Exception as e:
        return f"❌ Failed to verify report access: {str(e)}"

# ... rest of the file remains unchanged ...