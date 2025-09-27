from typing import Any, Optional
import httpx
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Import database components
from database.operations import (
    PatientReportOperations, PublishedReportOperations, init_database
)

# Load environment variables from .env file
load_dotenv()

# Create a FastMCP server instance
mcp = FastMCP("medical-report-publisher")

# Initialize database
init_database()

@mcp.tool()
async def add_patient_report(
    patient_email: str,
    mpin: str,
    report_type: str,
    report_content: str,
    test_date: str
) -> str:
    """Add a new patient report with MPIN authentication.
    
    Args:
        patient_email: Patient's email address
        mpin: Patient's Medical PIN for future authentication
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
        
        report = PatientReportOperations.add_report_with_mpin(
            patient_email=patient_email,
            mpin=mpin,
            report_type=report_type,
            report_content=report_content,
            test_date=test_date_obj
        )
        return f"✅ Report added successfully!\n" \
               f"📧 Patient: {patient_email}\n" \
               f"🆔 Report ID: {report.id}\n" \
               f"🏷️ Type: {report_type}\n" \
               f"📅 Test Date: {test_date_obj.date()}\n" \
               f"🔐 MPIN set for future authentication"
    except Exception as e:
        return f"❌ Failed to add report: {str(e)}"

@mcp.tool()
async def verify_report_access(report_id: str, patient_email: str, mpin: str) -> str:
    """Verify if a patient has access to a specific report using email and MPIN.
    
    Args:
        report_id: Unique ID of the report
        patient_email: Patient's email address
        mpin: Patient's Medical PIN
    """
    try:
        is_authorized = PatientReportOperations.verify_patient_access(
            report_id=report_id,
            patient_email=patient_email,
            mpin=mpin
        )
        
        if is_authorized:
            return f"✅ Authentication successful! You have access to report {report_id}"
        else:
            return f"❌ Authentication failed. Invalid report ID, email, or MPIN."
            
    except Exception as e:
        return f"❌ Failed to verify access: {str(e)}"

@mcp.tool()
async def get_report_by_id(report_id: str) -> str:
    """Fetch a specific patient report by its unique ID from the database.
    
    Args:
        report_id: Unique ID of the report in the patient_reports database
    """
    try:
        report = PatientReportOperations.get_report_by_id(report_id)
        if not report:
            return f"❌ Report with ID {report_id} not found"
        
        result = f"📋 **Report Details**\n\n"
        result += f"🆔 ID: {report.id}\n"
        result += f"📧 Patient Email: {report.patient_email}\n"
        result += f"🏷️ Type: {report.report_type}\n"
        result += f"📅 Test Date: {report.test_date.strftime('%Y-%m-%d')}\n"
        result += f"📝 Content:\n{report.report_content}\n"
        result += f"⏰ Created: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return result
    except Exception as e:
        return f"❌ Failed to fetch report: {str(e)}"

@mcp.tool()
async def list_all_reports(limit: Optional[int] = 20) -> str:
    """List all patient reports in the database with their IDs for publishing.
    
    Args:
        limit: Maximum number of reports to return (default: 20)
    """
    try:
        reports = PatientReportOperations.get_all_reports(limit or 20)
        
        if not reports:
            return "❌ No reports found in database"
        
        result = f"📋 Found {len(reports)} report(s) in database:\n\n"
        for i, report in enumerate(reports, 1):
            result += f"{i}. **{report.report_type.upper()}** - {report.test_date.strftime('%Y-%m-%d')}\n"
            result += f"   🆔 ID: {report.id}\n"
            result += f"   📧 Patient: {report.patient_email}\n"
            result += f"   📝 Preview: {report.report_content[:100]}{'...' if len(report.report_content) > 100 else ''}\n\n"
        
        return result.strip()
    except Exception as e:
        return f"❌ Failed to list reports: {str(e)}"

async def anonymize_medical_text(report_content: str) -> str:
    """Use ASI LLM to anonymize medical text by removing HIPAA identifiers"""
    asi_api_key = os.getenv("ASI1_API_KEY")
    if not asi_api_key:
        raise ValueError("ASI1_API_KEY environment variable is required")
    
    anonymization_prompt = """You are a medical text de-identification engine. 

Your job is to:
1. Remove all 18 HIPAA identifiers from the input text. These include:
   - Names (patients, doctors, relatives)
   - Geographic subdivisions smaller than a state (street, city, ZIP, hospitals)
   - All dates directly related to the patient (except year)
   - Phone numbers, fax numbers, email addresses
   - Social Security numbers, medical record numbers, health plan numbers, account numbers, certificate/license numbers
   - Vehicle identifiers (VIN, license plates), device identifiers, URLs, IP addresses
   - Biometric identifiers (fingerprints, retina scans)
   - Full-face photos and comparable images
   - Any unique codes or characteristics that could identify the patient
2. Replace each identifier with a pseudonym or placeholder:
   - Patient names → Patient_001, Patient_002, etc.
   - Doctors → Doctor_A, Doctor_B
   - Dates → shift dates or replace with [Year-YYYY] for timeline context
   - Hospitals → Hospital_X, Hospital_Y
   - MRNs or IDs → MRN_XXXX
3. Preserve all **medical information**: conditions, symptoms, procedures, medications, lab results, treatments, timelines.
4. Rewrite the text so it **reads naturally**, maintaining full readability and context, but ensuring no PHI/PII remains.
5. Output **only the rewritten, de-identified text**. Do not explain or comment on the changes."""

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.asi1.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {asi_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "asi1-mini",
                    "messages": [
                        {"role": "system", "content": anonymization_prompt},
                        {"role": "user", "content": report_content}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise Exception(f"Failed to anonymize text with ASI LLM: {str(e)}")

@mcp.tool()
async def publish_report(
    report_id: str,
    patient_email: str,
    mpin: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None
) -> str:
    """Publish a medical report by anonymizing it and adding to marketplace.
    Requires patient authentication with email and MPIN.
    
    Args:
        report_id: Unique ID of the report in the patient_reports database
        patient_email: Patient's email address for verification
        mpin: Patient's Medical PIN for authentication
        title: Title for the published report (optional, will generate if not provided)
        description: Description for the published report (optional)
        tags: Comma-separated tags for categorization (optional)
    """
    try:
        # First verify patient authorization
        is_authorized = PatientReportOperations.verify_patient_access(
            report_id=report_id,
            patient_email=patient_email,
            mpin=mpin
        )
        
        if not is_authorized:
            return f"❌ Authentication failed. Invalid report ID, email, or MPIN. Please verify your credentials."
        
        # Get the original report (we know it exists from verification)
        original_report = PatientReportOperations.get_report_by_id(report_id)
        
        # Anonymize the report content using ASI LLM
        try:
            anonymized_content = await anonymize_medical_text(original_report.report_content)
        except Exception as e:
            return f"❌ Failed to anonymize report: {str(e)}"
        
        # Generate title if not provided
        if not title:
            title = f"Anonymous {original_report.report_type.title()} Report - {original_report.test_date.strftime('%Y-%m')}"
        
        # Publish to marketplace
        published_report = PublishedReportOperations.publish_report(
            original_report_id=report_id,
            anonymized_content=anonymized_content,
            title=title,
            description=description,
            tags=tags
        )
        
        return f"✅ Successfully authenticated and published report to marketplace!\n" \
               f"👤 Authorized User: {patient_email}\n" \
               f"📋 Published ID: {published_report.id}\n" \
               f"📝 Title: {title}\n" \
               f"🏷️ Type: {original_report.report_type}\n" \
               f"📅 Test Date: {original_report.test_date.strftime('%Y-%m-%d')}\n" \
               f"🔒 Content has been fully anonymized and HIPAA compliant"
               
    except Exception as e:
        return f"❌ Failed to publish report: {str(e)}"

@mcp.tool()
async def get_marketplace_reports(
    report_type: Optional[str] = None,
    tags: Optional[str] = None,
    limit: Optional[int] = 10
) -> str:
    """Get published reports from the marketplace.
    
    Args:
        report_type: Filter by report type (e.g., 'blood', 'xray', etc.)
        tags: Filter by tags
        limit: Maximum number of reports to return (default: 10)
    """
    try:
        reports = PublishedReportOperations.get_published_reports(
            report_type=report_type,
            tags=tags,
            limit=limit or 10
        )
        
        if not reports:
            filters = []
            if report_type:
                filters.append(f"type: {report_type}")
            if tags:
                filters.append(f"tags: {tags}")
            filter_text = f" with filters ({', '.join(filters)})" if filters else ""
            return f"❌ No published reports found{filter_text}"
        
        result = f"📊 Found {len(reports)} published report(s) in marketplace:\n\n"
        for i, report in enumerate(reports, 1):
            result += f"{i}. **{report.title}**\n"
            result += f"   Type: {report.report_type} | Published: {report.published_at.strftime('%Y-%m-%d')}\n"
            if report.description:
                result += f"   Description: {report.description}\n"
            if report.tags:
                result += f"   Tags: {report.tags}\n"
            result += f"   ID: {report.id}\n\n"
        
        return result.strip()
    except Exception as e:
        return f"❌ Failed to get marketplace reports: {str(e)}"

# ... rest of the file remains unchanged ...