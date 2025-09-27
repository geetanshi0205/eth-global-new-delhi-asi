from typing import Any, Optional
import httpx
import os
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Knowledge graph components removed

# Import database components
from database.operations import (
    PatientOperations, AppointmentOperations, PrescriptionOperations, 
    PatientDataManager, init_database, PatientReportOperations
)

# Load environment variables from .env file
load_dotenv()

# Create a FastMCP server instance
mcp = FastMCP("cal-doctor-appointments")

# Initialize database
init_database()

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
        test_date: Date of the test/report in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    """
    try:
        # Parse test_date
        try:
            test_date_obj = datetime.fromisoformat(test_date)
        except ValueError:
            return "❌ Invalid date format. Please use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS."
        report = PatientReportOperations.add_report(
            patient_email=patient_email,
            report_type=report_type,
            report_content=report_content,
            test_date=test_date_obj
        )
        return f"✅ Report added for {patient_email} (type: {report_type}, date: {test_date_obj.date()})"
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
        test_date: Optional filter by test date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    """
    try:
        # Parse test_date if provided
        test_date_obj = None
        if test_date:
            try:
                test_date_obj = datetime.fromisoformat(test_date)
            except ValueError:
                return "❌ Invalid date format. Please use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS."
        
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

# ... rest of the file remains unchanged ...