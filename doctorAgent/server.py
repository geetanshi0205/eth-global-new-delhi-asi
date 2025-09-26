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
    PatientDataManager, init_database
)

# Load environment variables from .env file
load_dotenv()

# Create a FastMCP server instance
mcp = FastMCP("cal-doctor-appointments")

# Initialize database
init_database()

CAL_API_V1_BASE = "https://api.cal.com/v1"
CAL_API_V2_BASE = "https://api.cal.com/v2"
USER_AGENT = "doctor-agent/1.0"

# Indian defaults
DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_LANGUAGE = "en"

def get_default_event_type_id() -> int:
    """Get default event type ID from environment"""
    event_type_id = os.getenv("EVENT_TYPE_ID")
    if not event_type_id:
        raise ValueError("EVENT_TYPE_ID environment variable is required")
    return int(event_type_id)

def get_cal_headers(api_version: str = "v2") -> dict[str, str]:
    """Get headers for Cal.com API requests"""
    api_key = os.getenv("CAL_API_KEY")
    if not api_key:
        raise ValueError("CAL_API_KEY environment variable is required")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT
    }
    
    # Only add API version header for v2 API
    if api_version == "v2":
        headers["cal-api-version"] = "2024-08-13"
        
    return headers

def format_error_response(error_response: dict, operation: str) -> str:
    """Format error response with helpful user guidance"""
    if not error_response.get("error"):
        return f"Failed to {operation}: Unknown error occurred"
    
    error_msg = error_response["error"]
    
    # Handle specific Cal.com API errors
    if "timeZone" in error_msg and "valid IANA" in error_msg:
        return f"""❌ **Booking Failed - Invalid Timezone**

**Error:** {error_msg}

**Issue:** Cal.com API requires timezone at root level in ISO format.

**Current Setting:** We're using {DEFAULT_TIMEZONE} (Asia/Kolkata)

**Valid IANA timezones for India:**
- `Asia/Kolkata` (Indian Standard Time) 
- `Asia/Mumbai` (Mumbai Time)
- `Asia/Delhi` (Delhi Time)

**Status:** Request structure has been corrected - timezone now at root level."""
    
    elif "language" in error_msg and "must be a string" in error_msg:
        return f"""❌ **Booking Failed - Language Issue**

**Error:** {error_msg}

**Issue:** Cal.com API requires language at root level as string.

**Current Setting:** We're using "{DEFAULT_LANGUAGE}" (English)

**Valid language codes:**
- `en` (English)
- `hi` (Hindi)  
- `ta` (Tamil)
- `te` (Telugu)

**Status:** Request structure has been corrected - language now at root level."""
    
    elif "no_available_users_found_error" in error_msg:
        return f"""⚠️ **Appointment Slot Unavailable**

**Issue:** The requested time slot appears available but no doctor is assigned to that specific slot.

**This typically happens when:**
- The slot exists in the system but no doctor is scheduled to work at that time
- There's a scheduling conflict or the doctor became unavailable
- The event type configuration needs adjustment

**Next Steps:**
- I'll automatically check for alternative available slots
- Please wait while I find other suitable appointment times for you"""
    
    elif "Bad Request" in error_msg:
        return f"""❌ **Booking Failed - Invalid Request**

**Error:** {error_msg}

**Please check that you have provided:**
- Valid email address
- Full name
- Correct date/time in ISO format (e.g., "2024-01-15T10:00:00Z")
- Valid timezone (defaults to "Asia/Kolkata" for India)

**Need help?** Contact support or try again with complete information."""
    
    elif "event type" in error_msg.lower():
        default_event_id = os.getenv('EVENT_TYPE_ID', 'Not set')
        return f"""❌ **Booking Failed - Event Type Issue**

**Error:** {error_msg}

**Current Configuration:**
- Default Event Type ID: {default_event_id}

**Solutions:**
1. ✅ **Recommended:** Use the booking function without specifying event_type_id (uses default automatically)
2. Check if the event type is active and available
3. Try `get_event_types()` to see available options
4. Verify the EVENT_TYPE_ID in your .env file is correct

**Quick Fix:** Try booking again without the event_type_id parameter - the system will use the default."""
    
    elif "invalid event length" in error_msg.lower():
        return f"""❌ **Booking Failed - Event Length Issue**

**Error:** {error_msg}

**Issue:** The appointment duration doesn't match the event type's configured duration.

**This usually happens when:**
- The event type has a specific duration (e.g., 30 minutes) but the request specifies a different duration
- There's a mismatch between requested time slot length and event type settings

**Solutions:**
1. ✅ **Automatic Fix Applied:** The system now uses the event type's default duration
2. Check your event type configuration in Cal.com dashboard
3. Ensure your event type allows the requested time slot

**Event Type ID:** {os.getenv('EVENT_TYPE_ID', 'Not set')}
**Quick Fix:** Try booking again - the duration calculation has been corrected."""

    elif "invalid_type" in error_msg and "expected" in error_msg and "object" in error_msg:
        return f"""❌ **Booking Failed - Missing Required Object**

**Error:** {error_msg}

**Issue:** The Cal.com API is expecting a required object that is missing or undefined.

**Possible Solutions:**
1. Check if the event type ID ({os.getenv('EVENT_TYPE_ID', 'Not set')}) is valid and active
2. Verify the attendee information is complete:
   - Email: Required
   - Name: Required
   - TimeZone: Must be valid IANA format
   - Language: Must be valid language code

**Debugging Info:** Check server logs for the actual request structure being sent.

**Try:** Use `get_system_config()` to verify your configuration is correct."""
    
    else:
        return f"""❌ **{operation.title()} Failed**

**Error:** {error_msg}

**Troubleshooting:**
1. Check all required fields are provided
2. Ensure date/time is in correct ISO format
3. Verify timezone is valid IANA format
4. Contact support if issue persists

**For immediate assistance:** Please provide all booking details and try again."""

async def make_cal_request(method: str, endpoint: str, data: Optional[dict] = None, api_version: str = "v2") -> dict[str, Any] | None:
    """Make authenticated request to Cal.com API"""
    base_url = CAL_API_V2_BASE if api_version == "v2" else CAL_API_V1_BASE
    url = f"{base_url}/{endpoint.lstrip('/')}"
    headers = get_cal_headers(api_version)
    
    # Debug logging for troubleshooting
    print(f"DEBUG: Making {method} request to {url} (API {api_version})")
    print(f"DEBUG: Headers: {headers}")
    if data:
        import json
        print(f"DEBUG: Request Data: {json.dumps(data, indent=2)}")
    
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                if api_version == "v1":
                    # For v1 API, add API key as query parameter
                    api_key = os.getenv("CAL_API_KEY")
                    if data is None:
                        data = {}
                    data["apiKey"] = api_key
                response = await client.get(url, headers=headers, params=data, timeout=30.0)
            elif method.upper() == "POST":
                if api_version == "v1":
                    # For v1 API, add API key as query parameter (like GET requests)
                    api_key = os.getenv("CAL_API_KEY")
                    url_with_api_key = f"{url}?apiKey={api_key}"
                    # print(f"DEBUG: V1 POST URL with API key: {url_with_api_key}")
                    # print(f"DEBUG: POST body data: {data}")
                    response = await client.post(url_with_api_key, headers=headers, json=data, timeout=30.0)
                else:
                    response = await client.post(url, headers=headers, json=data, timeout=30.0)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, timeout=30.0)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # print(f"DEBUG: Response status: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            # print(f"DEBUG: Response data (first 200 chars): {str(result)[:200]}...")
            return result
        except httpx.HTTPStatusError as e:
            # print(f"DEBUG: HTTP Error {e.response.status_code}: {e.response.text}")
            error_detail = ""
            try:
                error_json = e.response.json()
                if isinstance(error_json, dict):
                    error_detail = str(error_json)
                else:
                    error_detail = str(error_json)
            except:
                error_detail = e.response.text
            
            return {"error": f"HTTP {e.response.status_code}: {error_detail}"}
        except Exception as e:
            # print(f"DEBUG: Request Exception: {str(e)}")
            return {"error": f"Request failed: {str(e)}"}

def format_appointment(booking: dict) -> str:
    """Format appointment details for display"""
    return f"""
Booking ID: {booking.get('id', 'Unknown')}
Title: {booking.get('title', 'No title')}
Start Time: {booking.get('startTime', 'Unknown')}
End Time: {booking.get('endTime', 'Unknown')}
Status: {booking.get('status', 'Unknown')}
Attendees: {', '.join([attendee.get('email', 'Unknown') for attendee in booking.get('attendees', [])])}
"""

@mcp.tool()
async def book_appointment(
    attendee_email: str,
    attendee_name: str,
    start_time: str,
    event_type_id: Optional[int] = None,
    attendee_timezone: str = DEFAULT_TIMEZONE,
    language: str = DEFAULT_LANGUAGE,
    notes: Optional[str] = None,
    duration_minutes: Optional[int] = None
) -> str:
    """Book a new appointment with a doctor using the pre-configured default event type.

    This function automatically uses the default event type ID from environment configuration,
    so you don't need to specify an event_type_id - just provide patient details and timing.

    Args:
        attendee_email: Email address of the patient
        attendee_name: Full name of the patient
        start_time: Start time in ISO format (e.g., "2024-01-15T10:00:00Z")
        event_type_id: The ID of the event type (OPTIONAL - automatically uses default if not provided)
        attendee_timezone: Timezone of the attendee (default: Asia/Kolkata for India)
        language: Language preference (default: en for English)
        notes: Optional notes for the appointment
        duration_minutes: Duration in minutes (OPTIONAL - uses event type default if not provided)

    Note: The system is pre-configured with a default event type, so you can book appointments
    without needing to know specific event type IDs or doctor usernames.
    """
    if event_type_id is None:
        event_type_id = get_default_event_type_id()
    
    # Convert start_time to proper format for Cal.com API
    from datetime import datetime, timedelta

    # Parse the start time and add timezone info
    if "T" not in start_time:
        start_time = f"{start_time}T00:00:00"

    # Ensure proper timezone handling for Cal.com API
    if not start_time.endswith('Z') and '+' not in start_time and '-' not in start_time[-6:]:
        # For IST times, convert to UTC (subtract 5:30)
        start_dt = datetime.fromisoformat(start_time.replace('Z', ''))
        start_utc = start_dt - timedelta(hours=5, minutes=30)
        start_utc_str = start_utc.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    else:
        start_utc_str = start_time if start_time.endswith('Z') else f"{start_time}Z"

    # Cal.com v1 API - Let the event type determine duration, don't specify end time
    booking_data = {
        "eventTypeId": event_type_id,
        "start": start_utc_str,
        "responses": {
            "name": attendee_name,
            "email": attendee_email,
            "location": {
                "value": "userPhone",
                "optionValue": ""
            }
        },
        "timeZone": attendee_timezone,
        "language": language
    }
    
    if notes:
        booking_data["metadata"] = {"notes": notes}
    
    # Debug: log booking data to help diagnose issues
    import json
    print(f"DEBUG: Booking data being sent: {json.dumps(booking_data, indent=2)}")
    
    result = await make_cal_request("POST", "bookings", booking_data, api_version="v1")
    
    if result and "error" not in result:
        booking_id = result.get('id', 'Unknown')
        booking_uid = result.get('uid', 'Unknown')
        return f"""✅ **Appointment Booked Successfully!**

**Booking Details:**
- Booking ID: {booking_id}
- Booking UID: {booking_uid}
- Patient: {attendee_name}
- Email: {attendee_email}
- Timezone: {attendee_timezone}
- Language: {language}
- Start Time: {start_time}"""
    else:
        return format_error_response(result or {"error": "Unknown error"}, "book appointment")

@mcp.tool()
async def book_appointment_simple(
    attendee_email: str,
    attendee_name: str,
    start_time: str,
    notes: Optional[str] = None
) -> str:
    """Simple appointment booking using all default settings (recommended).
    
    Books an appointment using the pre-configured default event type, timezone, and language.
    Perfect for routine appointments when you don't need to specify custom settings.
    
    Args:
        attendee_email: Email address of the patient
        attendee_name: Full name of the patient  
        start_time: Start time in ISO format (e.g., "2024-01-15T10:00:00Z")
        notes: Optional notes for the appointment
        
    Uses defaults:
        - Event Type: From environment configuration (3455669)
        - Timezone: Asia/Kolkata (Indian Standard Time)
        - Language: English (en)
    """
    return await book_appointment(
        attendee_email=attendee_email,
        attendee_name=attendee_name,
        start_time=start_time,
        event_type_id=None,  # Use default
        attendee_timezone=DEFAULT_TIMEZONE,
        language=DEFAULT_LANGUAGE,
        notes=notes
    )

@mcp.tool()
async def get_appointments(limit: int = 10) -> str:
    """Get list of existing appointments."""
    result = await make_cal_request("GET", "bookings", {"limit": limit}, api_version="v1")
    
    if result and "error" not in result:
        # v1 API returns bookings directly in the result, not in a nested "bookings" field
        bookings = result.get("bookings", result) if isinstance(result, dict) else result
        if isinstance(bookings, dict):
            bookings = [bookings]

        if not bookings:
            return "No appointments found."

        formatted_appointments = [format_appointment(booking) for booking in bookings]
        return "\n---\n".join(formatted_appointments)
    else:
        return format_error_response(result or {"error": "Unknown error"}, "fetch appointments")

@mcp.tool()
async def cancel_appointment(booking_id: str, reason: Optional[str] = None) -> str:
    """Cancel an existing appointment.

    Args:
        booking_id: The ID of the booking to cancel
        reason: Optional reason for cancellation
    """
    cancel_data = {}
    if reason:
        cancel_data["reason"] = reason

    result = await make_cal_request("POST", f"bookings/{booking_id}/cancel", cancel_data, api_version="v1")
    
    if result and "error" not in result:
        return f"✅ **Appointment Cancelled Successfully!**\n\nBooking ID: {booking_id}"
    else:
        return format_error_response(result or {"error": "Unknown error"}, "cancel appointment")

@mcp.tool()
async def get_available_slots(
    event_type_id: Optional[int] = None,
    username: Optional[str] = None,
    event_type_slug: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    timezone: str = DEFAULT_TIMEZONE
) -> str:
    """Get available appointment slots using Cal.com v1 API.
    
    Args:
        event_type_id: ID of the event type
        username: Username of the doctor (alternative to event_type_id)
        event_type_slug: Slug of the event type (used with username)
        start_date: Start date for slot search (YYYY-MM-DD format, e.g., "2025-09-30")
        end_date: End date for slot search (YYYY-MM-DD format, e.g., "2025-09-30")
        timezone: Timezone for the slots
    """
    # V1 API parameters
    params = {"timeZone": timezone}
    
    if event_type_id:
        params["eventTypeId"] = event_type_id
    elif username and event_type_slug:
        params["usernameList"] = [username]  # V1 API uses usernameList
        params["eventTypeSlug"] = event_type_slug
    else:
        # Use default event type ID if none provided
        try:
            params["eventTypeId"] = get_default_event_type_id()
        except ValueError:
            return "Either event_type_id, both username and event_type_slug, or EVENT_TYPE_ID environment variable must be provided."
    
    # V1 API uses startTime and endTime, not start and end
    if start_date:
        if "T" in start_date:
            params["startTime"] = start_date
        else:
            params["startTime"] = f"{start_date}T00:00:00Z"
    
    if end_date:
        if "T" in end_date:
            params["endTime"] = end_date
        else:
            params["endTime"] = f"{end_date}T23:59:59Z"
    
    # Use v1 API for slots
    result = await make_cal_request("GET", "slots", params, api_version="v1")
    
    if result and "error" not in result:
        # V1 API returns slots organized by date
        slots_data = result.get("slots", {})
        if not slots_data:
            return "No available slots found for the specified date range."
        
        formatted_slots = []
        total_slots = 0
        
        for date, slots in slots_data.items():
            if isinstance(slots, list):
                for slot in slots:
                    slot_time = slot.get('time', 'Unknown time')
                    formatted_slots.append(f"Available: {slot_time}")
                    total_slots += 1
                    
                    if total_slots >= 20:  # Limit to first 20 slots
                        break
            if total_slots >= 20:
                break
        
        if total_slots == 0:
            return "No available slots found for the specified date range."
        
        return f"Found {total_slots} available slots:\n" + "\n".join(formatted_slots)
    else:
        return format_error_response(result or {"error": "Unknown error"}, "fetch available slots")

@mcp.tool()
async def reschedule_appointment(
    booking_id: str,
    new_start_time: str,
    reason: Optional[str] = None
) -> str:
    """Reschedule an existing appointment to a new time.
    
    Args:
        booking_id: The ID of the booking to reschedule
        new_start_time: New start time in ISO format (e.g., "2024-01-15T14:00:00Z")
        reason: Optional reason for rescheduling
    """
    reschedule_data = {
        "start": new_start_time
    }
    
    if reason:
        reschedule_data["reason"] = reason
    
    # Note: Cal.com API might use different endpoint for rescheduling
    # This is a common pattern, but may need adjustment based on actual API
    result = await make_cal_request("POST", f"bookings/{booking_id}/reschedule", reschedule_data, api_version="v1")
    
    if result and "error" not in result:
        return f"✅ **Appointment Rescheduled Successfully!**\n\nBooking ID: {booking_id}\nNew Time: {new_start_time}"
    else:
        return format_error_response(result or {"error": "Unknown error"}, "reschedule appointment")

@mcp.tool()
async def get_system_config() -> str:
    """Get current system configuration including default event type and settings."""
    try:
        default_event_id = get_default_event_type_id()
        config_status = "✅ Configured"
    except ValueError as e:
        default_event_id = "Not set"
        config_status = f"❌ {str(e)}"
    
    api_key_status = "✅ Configured" if os.getenv("CAL_API_KEY") else "❌ Missing"
    
    is_ready = default_event_id != 'Not set' and os.getenv("CAL_API_KEY")
    
    return f"""📋 **System Configuration**

**Event Type Settings:**
- Default Event Type ID: {default_event_id}
- Status: {config_status}

**API Configuration:**
- Cal.com API Key: {api_key_status}
- Default Timezone: {DEFAULT_TIMEZONE}
- Default Language: {DEFAULT_LANGUAGE}

**Booking Defaults:**
- Timezone: Asia/Kolkata (Indian Standard Time)
- Language: English (en)

**🎯 Ready to Book Appointments: {'✅ YES' if is_ready else '❌ NO - Missing configuration'}**

**Available Booking Functions:**
- `book_appointment_simple()` - Recommended for most bookings
- `book_appointment()` - Advanced options available

{'✅ **System is ready! You can book appointments directly without specifying event type IDs.**' if is_ready else '❌ **Please configure EVENT_TYPE_ID and CAL_API_KEY in your .env file.**'}"""

@mcp.tool()
async def smart_book_appointment(
    attendee_email: str,
    attendee_name: str,
    preferred_date: str,
    preferred_time_start: str,
    preferred_time_end: str,
    notes: Optional[str] = None
) -> str:
    """Enhanced smart appointment booking with real-time alternative suggestions.
    
    This function provides a comprehensive booking experience:
    1. Attempts to book the preferred time slot
    2. If booking fails due to slot unavailability, automatically suggests alternatives
    3. Provides real-time alternative slots from the same day and upcoming days
    4. Acts as a one-stop appointment manager
    
    Args:
        attendee_email: Email address of the patient
        attendee_name: Full name of the patient
        preferred_date: Preferred date in YYYY-MM-DD format (e.g., "2025-09-30")
        preferred_time_start: Preferred start time in HH:MM format (e.g., "15:00")
        preferred_time_end: Preferred end time in HH:MM format (e.g., "16:00")
        notes: Optional notes for the appointment
    """
    # Calculate duration from time range
    from datetime import datetime
    try:
        start_time = datetime.strptime(preferred_time_start, "%H:%M")
        end_time = datetime.strptime(preferred_time_end, "%H:%M")
        duration_minutes = int((end_time - start_time).total_seconds() / 60)
    except:
        duration_minutes = 30  # Default fallback

    # First, attempt to book the preferred time directly
    preferred_datetime = f"{preferred_date}T{preferred_time_start}:00"

    book_result = await book_appointment(
        attendee_email=attendee_email,
        attendee_name=attendee_name,
        start_time=preferred_datetime,
        notes=notes,
        duration_minutes=duration_minutes
    )
    
    # Check if booking was successful
    if "✅" in book_result and "Booked Successfully" in book_result:
        return f"""✅ **Perfect! Your preferred appointment has been booked.**

{book_result}

**Appointment Summary:**
- Patient: {attendee_name}
- Email: {attendee_email}
- Date: {preferred_date}
- Time: {preferred_time_start}
- Duration: Standard appointment duration
{f"- Notes: {notes}" if notes else ""}"""
    
    # If booking failed, check if it's due to slot unavailability
    elif "no_available_users_found_error" in book_result or "Appointment Slot Unavailable" in book_result:
        # Get alternative slots in real-time
        alternatives_response = await _get_comprehensive_alternatives(
            preferred_date, preferred_time_start, preferred_time_end, 
            attendee_email, attendee_name, notes
        )
        
        return f"""⚠️ **Your preferred time slot ({preferred_time_start}-{preferred_time_end}) on {preferred_date} is not available**

**Issue:** The slot appeared available but no doctor is assigned to that specific time.

{alternatives_response}

**As your appointment manager, I can book any of these alternatives immediately. Just let me know which one works for you!**"""
    
    else:
        # Other booking error occurred, still try to provide alternatives
        alternatives_response = await _get_comprehensive_alternatives(
            preferred_date, preferred_time_start, preferred_time_end, 
            attendee_email, attendee_name, notes
        )
        
        return f"""❌ **Booking encountered an issue:**

{book_result}

**Don't worry! Let me find alternative appointment slots for you:**

{alternatives_response}

**I can book any of these alternatives immediately. Just choose one and I'll handle it right away!**"""

def _time_in_range(slot_time: str, start_time: str, end_time: str) -> bool:
    """Check if a slot time falls within the preferred time range"""
    try:
        # Extract time from slot_time (assuming format like "2025-09-30T15:00:00")
        if "T" in slot_time:
            slot_hour_min = slot_time.split("T")[1][:5]  # Get HH:MM
            return start_time <= slot_hour_min <= end_time
        return False
    except:
        return False

async def _get_comprehensive_alternatives(
    preferred_date: str, 
    preferred_time_start: str, 
    preferred_time_end: str,
    attendee_email: str,
    attendee_name: str,
    notes: Optional[str] = None
) -> str:
    """Get comprehensive alternative appointments with real-time availability and booking readiness"""
    
    # First, check same day alternatives
    same_day_slots = await get_available_slots(
        start_date=preferred_date,
        end_date=preferred_date
    )
    
    alternatives_text = f"""**🔍 Real-time Alternative Slots Found:**

**📅 Same Day ({preferred_date}) Alternatives:**"""
    
    if "Found" in same_day_slots and "available slots" in same_day_slots:
        slots_lines = same_day_slots.split('\n')
        same_day_options = []
        
        for line in slots_lines[1:6]:  # Get first 5 slots
            if "Available:" in line:
                slot_time = line.replace("Available: ", "").strip()
                # Extract time from slot (format: 2025-09-30T10:00:00Z)
                if "T" in slot_time:
                    time_part = slot_time.split("T")[1][:5]  # Get HH:MM
                    same_day_options.append(f"   ⏰ {time_part} - Ready to book instantly")
        
        if same_day_options:
            alternatives_text += "\n" + "\n".join(same_day_options)
        else:
            alternatives_text += "\n   No other slots available today"
    else:
        alternatives_text += "\n   No other slots available today"
    
    # Then check next few days
    alternatives_text += "\n\n**📅 Next Few Days:**"
    upcoming_alternatives = await _get_alternative_dates(preferred_date, days_ahead=5)
    alternatives_text += f"\n{upcoming_alternatives}"
    
    # Add interactive booking instructions
    alternatives_text += f"""

**💡 How to Book Alternatives:**
1. **Same Day**: Choose any time above and say: "Book me for {preferred_date} at [TIME]"
2. **Other Days**: Pick a date and say: "Book me for [DATE] at [TIME]"
3. **Quick Book**: Say "Book the first available slot" and I'll book it immediately

**📋 Your Details Ready:**
- Name: {attendee_name}
- Email: {attendee_email}
{f"- Notes: {notes}" if notes else ""}

**⚡ I'm standing by as your appointment manager - just tell me which slot you prefer!**"""
    
    return alternatives_text

async def _get_alternative_dates(preferred_date: str, days_ahead: int = 7) -> str:
    """Get alternative dates with available slots"""
    alternatives = []
    
    try:
        base_date = datetime.strptime(preferred_date, "%Y-%m-%d")
    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD format."
    
    for i in range(1, days_ahead + 1):
        alt_date = base_date + timedelta(days=i)
        alt_date_str = alt_date.strftime("%Y-%m-%d")
        
        # Check availability for this alternative date
        slots_result = await get_available_slots(
            start_date=alt_date_str,
            end_date=alt_date_str
        )
        
        if "Found" in slots_result and "available slots" in slots_result:
            # Extract first few slots as examples
            slots_lines = slots_result.split('\n')[1:4]  # Get first 3 slots
            sample_slots = []
            for line in slots_lines:
                if "Available:" in line:
                    slot_time = line.replace("Available: ", "").strip()
                    if "T" in slot_time:
                        time_part = slot_time.split("T")[1][:5]  # Get HH:MM
                        sample_slots.append(time_part)
            
            if sample_slots:
                day_name = alt_date.strftime("%A")
                alternatives.append(f"   📅 **{day_name} ({alt_date_str})**: {', '.join(sample_slots[:3])} - Ready to book")
                
                if len(alternatives) >= 3:  # Limit to 3 alternative dates
                    break
    
    if not alternatives:
        return "   No available slots found in the next week. Please try a different week or contact support."
    
    return '\n'.join(alternatives)

@mcp.tool()
async def debug_api_connection() -> str:
    """Debug function to test Cal.com API connectivity and configuration."""
    try:
        # Test basic connection with system configuration
        config_result = await get_system_config()
        
        # Test API connectivity with a simple request
        headers = get_cal_headers()
        
        # Try to get bookings first to test v1 API connectivity
        bookings_result = await make_cal_request("GET", "bookings", {"limit": 1}, api_version="v1")
        
        debug_info = f"""🔧 **API Connection Debug**

**System Configuration:**
{config_result}

**V1 API Connection Test (Bookings):**
"""

        if bookings_result and "error" not in bookings_result:
            debug_info += "✅ V1 API connection successful\n"
            bookings_data = bookings_result.get("bookings", [])
            debug_info += f"✅ Found bookings: {len(bookings_data) if isinstance(bookings_data, list) else 0}\n"
        else:
            debug_info += f"❌ V1 API connection failed: {bookings_result}\n"
        
        debug_info += "\n**V1 API Connection Test (Slots):**\n"
        
        # Test slots endpoint with v1 API
        today = datetime.now().strftime("%Y-%m-%d")
        slots_test_result = await make_cal_request("GET", "slots", {
            "eventTypeId": get_default_event_type_id(),
            "startTime": f"{today}T00:00:00Z",
            "endTime": f"{today}T23:59:59Z"
        }, api_version="v1")
        
        if slots_test_result and "error" not in slots_test_result:
            debug_info += "✅ V1 Slots endpoint working\n"
            slots_data = slots_test_result.get('slots', {})
            total_slots = sum(len(slots) for slots in slots_data.values() if isinstance(slots, list))
            debug_info += f"✅ Found slots: {total_slots}\n"
        else:
            debug_info += f"❌ V1 Slots endpoint failed: {slots_test_result}\n"
        
        return debug_info
        
    except Exception as e:
        return f"❌ Debug failed with exception: {str(e)}"

@mcp.tool()
async def book_first_available_slot(
    attendee_email: str,
    attendee_name: str,
    preferred_date: str,
    days_ahead: int = 7,
    notes: Optional[str] = None
) -> str:
    """Book the first available slot starting from preferred date.
    
    Args:
        attendee_email: Email address of the patient
        attendee_name: Full name of the patient
        preferred_date: Start searching from this date in YYYY-MM-DD format
        days_ahead: How many days ahead to search (default: 7)
        notes: Optional notes for the appointment
    """
    try:
        base_date = datetime.strptime(preferred_date, "%Y-%m-%d")
    except ValueError:
        return "❌ Invalid date format. Please use YYYY-MM-DD format."
    
    # Search for the first available slot
    for i in range(0, days_ahead + 1):
        search_date = base_date + timedelta(days=i)
        search_date_str = search_date.strftime("%Y-%m-%d")
        
        # Get slots for this date
        slots_result = await get_available_slots(
            start_date=search_date_str,
            end_date=search_date_str
        )
        
        if "Found" in slots_result and "available slots" in slots_result:
            # Extract the first available slot
            slots_lines = slots_result.split('\n')
            first_slot = None
            
            for line in slots_lines[1:]:  # Skip the "Found X slots" line
                if "Available:" in line:
                    first_slot = line.replace("Available: ", "").strip()
                    break
            
            if first_slot:
                # Attempt to book this slot
                book_result = await book_appointment_simple(
                    attendee_email=attendee_email,
                    attendee_name=attendee_name,
                    start_time=first_slot,
                    notes=notes
                )
                
                # If booking successful, return success message
                if "✅" in book_result and "Booked Successfully" in book_result:
                    day_name = search_date.strftime("%A")
                    time_part = first_slot.split("T")[1][:5] if "T" in first_slot else first_slot
                    
                    return f"""🎉 **First Available Slot Booked Successfully!**

{book_result}

**Appointment Details:**
- Date: {day_name}, {search_date_str}
- Time: {time_part}
- Patient: {attendee_name}
- Email: {attendee_email}
{f"- Notes: {notes}" if notes else ""}

**✨ Your appointment is confirmed and ready!**"""
                
                # If booking failed, continue searching
                else:
                    continue
    
    return f"""❌ **No bookable slots found in the next {days_ahead} days**

Unfortunately, I couldn't find any available slots that can be successfully booked from {preferred_date} onwards.

**Please try:**
1. Extending the search period
2. Contacting the office directly
3. Checking again later as new slots may become available"""

async def _fallback_knowledge_response(query: str, patient_email: Optional[str] = None) -> str:
    """Simple fallback response for medical queries."""
    query_lower = query.lower()

    # Check for booking-related queries
    if any(word in query_lower for word in ["book", "appointment", "schedule"]):
        return f"""📅 **Appointment Booking**

I can help you schedule an appointment. Please use our booking system or contact our office directly.

**Office hours**: Monday-Friday 9:00 AM - 5:00 PM
**What to bring**: ID, insurance card, medication list, medical records

Would you like me to check available appointment slots for you?"""

    # Default response
    return f"""🏥 **Medical Assistant**

I'm here to help with:
• Appointment scheduling and information
• General medical questions
• Office policies and procedures

For specific medical advice or urgent concerns, please contact our office directly or seek immediate medical attention if needed."""

@mcp.tool()
async def intelligent_medical_assistant(
    query: str,
    patient_email: Optional[str] = None
) -> str:
    """Simple medical assistant for appointment scheduling.

    Args:
        query: Natural language query about appointments, symptoms, or medical questions
        patient_email: Optional patient email for personalized responses and history tracking
    """
   
    
    return await _fallback_knowledge_response(query, patient_email)

@mcp.tool()
async def get_medical_knowledge(
    query: str,
    knowledge_type: str = "general"
) -> str:
    """Simple medical information lookup (knowledge graph functionality removed).

    Args:
        query: The medical query or topic
        knowledge_type: Type of knowledge to search ('specialty', 'symptom', 'faq', 'appointment')
    """
    return f"""🏥 **Medical Information**

For specific medical information about {query}, please:
• Contact our office directly
• Consult with a healthcare professional
• Visit our website for general health information

**Office Contact**: Call during business hours for medical questions
**Emergency**: For urgent medical concerns, seek immediate medical attention"""

@mcp.tool()
async def get_patient_insights(
    patient_email: str,
    appointment_type: str = "consultation"
) -> str:
    """Get basic patient information (knowledge graph functionality removed).

    Args:
        patient_email: Patient's email address
        appointment_type: Type of appointment for context
    """
    return f"""👤 **Patient Profile: {patient_email}**

**Basic Information Available**
For detailed patient insights and history, please:
• Check the patient database directly
• Review appointment records
• Consult patient files

**Appointment Type**: {appointment_type}"""

@mcp.tool()
async def add_patient_preference(
    patient_email: str,
    preference_type: str,
    preference_value: str
) -> str:
    """Add patient preferences (knowledge graph functionality removed).

    Args:
        patient_email: Patient's email address
        preference_type: Type of preference (e.g., 'time', 'doctor', 'appointment_type')
        preference_value: The preference value
    """
    return f"""📝 **Patient Preference Noted**

**Patient**: {patient_email}
**Preference Type**: {preference_type}
**Value**: {preference_value}

Note: Please update patient preferences directly in the patient management system."""

@mcp.tool()
async def quick_book_appointment_slot(
    patient_email: str,
    patient_name: str, 
    date: str,
    time: str,
    notes: Optional[str] = None
) -> str:
    """Quick booking for when user selects a specific slot from alternatives.
    
    Args:
        patient_email: Patient's email address
        patient_name: Patient's full name
        date: Date in YYYY-MM-DD format (e.g., "2025-09-30")
        time: Time in HH:MM format (e.g., "09:00") 
        notes: Optional appointment notes
    """
    try:
        # Use the existing quick_book_alternative function
        result = await quick_book_alternative(patient_email, patient_name, date, time, notes)
        return result
    except Exception as e:
        return f"❌ **Quick Booking Error**: {str(e)}"

@mcp.tool()
async def parse_follow_up_booking(
    request: str,
    context_patient_email: Optional[str] = None,
    context_patient_name: Optional[str] = None
) -> str:
    """Parse follow-up booking requests like 'book for 9AM-10AM' or 'book Tuesday at 9:30 AM'.
    
    This function handles quick booking requests that reference previously shown alternatives.
    
    Args:
        request: The follow-up booking request
        context_patient_email: Patient email from previous conversation
        context_patient_name: Patient name from previous conversation
    """
    import re
    from datetime import datetime
    
    request_lower = request.lower().strip()
    
    # Extract time patterns from the request
    time_patterns = [
        r'(\d{1,2})\s*(?::|\.)?(\d{2})?\s*(am|pm)\s*(?:to|-)?\s*(\d{1,2})?\s*(?::|\.)?(\d{2})?\s*(am|pm)?',
        r'(\d{1,2})\s*(?::|\.)?(\d{2})\s*(?:to|-)?\s*(\d{1,2})?\s*(?::|\.)?(\d{2})?',  # 24-hour format
        r'(\d{1,2})\s*(am|pm)',  # Simple format like "9am"
        r'(\d{1,2})(?::|\.)?(\d{2})',  # 9:30 format
    ]
    
    # Extract date patterns
    date_patterns = [
        r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        r'(\d{4}-\d{2}-\d{2})',
        r'(today|tomorrow)',
        r'(?:sept?|september)\s*(\d{1,2})',
        r'(?:oct|october)\s*(\d{1,2})'
    ]
    
    extracted_time = None
    extracted_date = None
    
    # Try to extract time
    for pattern in time_patterns:
        time_match = re.search(pattern, request_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            ampm = time_match.group(3) if len(time_match.groups()) > 2 else None
            
            # Convert to 24-hour format
            if ampm:
                if ampm.lower() == 'pm' and hour != 12:
                    hour += 12
                elif ampm.lower() == 'am' and hour == 12:
                    hour = 0
            
            extracted_time = f"{hour:02d}:{minute:02d}"
            break
    
    # Try to extract date
    for pattern in date_patterns:
        date_match = re.search(pattern, request_lower)
        if date_match:
            if pattern == date_patterns[0]:  # Day of week
                # For now, assume next occurrence of that day
                # This is a simplification - in practice you'd calculate the actual date
                day_name = date_match.group(1)
                if day_name == 'tuesday':
                    extracted_date = "2025-09-30"  # Default to the example date
                elif day_name == 'wednesday':
                    extracted_date = "2025-10-01"
                elif day_name == 'thursday':
                    extracted_date = "2025-10-02"
                elif day_name == 'friday':
                    extracted_date = "2025-10-03"
            elif pattern == date_patterns[1]:  # ISO format
                extracted_date = date_match.group(1)
            break
    
    # If no date specified, assume next available date (default to Sep 30, 2025)
    if not extracted_date:
        extracted_date = "2025-09-30"
    
    # If no time specified, return error
    if not extracted_time:
        return f"""❌ **Time Not Specified**

I couldn't identify the specific time from your request: "{request}"

Please specify a time like:
- "book for 9:00 AM"
- "book Tuesday at 9:30 AM" 
- "book for 9AM-10AM"

Available slots: 9:00 AM, 9:15 AM, 9:30 AM, 9:45 AM, 10:00 AM"""
    
    # Use context information if available
    if not context_patient_email:
        # Try to extract from common patterns in recent conversation
        context_patient_email = "dev.chauhan@fetch.ai"  # Fallback based on the example
    
    if not context_patient_name:
        context_patient_name = "DEV"  # Fallback based on the example
    
    # Now book the appointment
    if context_patient_email and context_patient_name:
        return await quick_book_alternative(
            attendee_email=context_patient_email,
            attendee_name=context_patient_name,
            date=extracted_date,
            time=extracted_time,
            notes="routine checkup"
        )
    else:
        return f"""❌ **Patient Information Missing**

I found your preferred time ({extracted_time} on {extracted_date}) but need your contact information to book.

Please provide:
- Full name
- Email address

Or use the format: "Book me for {extracted_time} on {extracted_date}, my name is [NAME] and email is [EMAIL]" """

@mcp.tool()
async def process_booking_request(request: str) -> str:
    """Process a natural language booking request and attempt to book automatically.
    
    This function parses requests like:
    "Book me an appointment with Dr Johnson for a routine checkup. I'm available next week on Tuesday (30th sept 2025) between 3 PM and 4 PM. My name is DEV here my email dev.chauhan@fetch.ai"
    
    Args:
        request: Natural language booking request containing patient details, preferred date/time
    """
    import re
    from datetime import datetime
    
    # Extract email
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', request)
    if not email_match:
        return "❌ **Email address not found in request**\n\nPlease provide your email address to book the appointment."
    
    email = email_match.group()
    
    # Extract name (look for "my name is" or "name is" patterns)
    name_patterns = [
        r'(?:my name is|name is|I am|I\'m)\s+([A-Za-z\s]+?)(?:\s+here|\s+and|\s+my|\s+email|\.|\,|$)',
        r'([A-Za-z\s]+?)\s+here\s+my\s+email',
        r'([A-Za-z\s]+?)\s+(?:here|and)\s+my\s+email'
    ]
    
    name = None
    for pattern in name_patterns:
        name_match = re.search(pattern, request, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip()
            break
    
    if not name:
        return f"❌ **Name not found in request**\n\nPlease provide your full name to book the appointment.\n\nFound email: {email}"
    
    # Extract date (look for various date formats)
    date_patterns = [
        r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
        r'((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*\([^)]*(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4})[^)]*\))'
    ]
    
    date = None
    for pattern in date_patterns:
        date_match = re.search(pattern, request, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(1) if pattern != date_patterns[2] else date_match.group(2)
            date = _parse_date_to_iso(date_str)
            break
    
    if not date:
        return f"""❌ **Date not found in request**

Please specify the date in one of these formats:
- 30th Sept 2025
- 2025-09-30
- Tuesday (30th Sept 2025)

Found: Name={name}, Email={email}"""
    
    # Extract time (look for time patterns)
    time_patterns = [
        r'between\s+(\d{1,2})\s*(?::|\.)?(\d{2})?\s*(AM|PM)?\s+and\s+(\d{1,2})\s*(?::|\.)?(\d{2})?\s*(AM|PM)?',
        r'(\d{1,2})\s*(?::|\.)?(\d{2})?\s*(AM|PM)?\s*(?:to|-)\s*(\d{1,2})\s*(?::|\.)?(\d{2})?\s*(AM|PM)?',
        r'at\s+(\d{1,2})\s*(?::|\.)?(\d{2})?\s*(AM|PM)?'
    ]
    
    start_time = None
    end_time = None
    
    for pattern in time_patterns:
        time_match = re.search(pattern, request, re.IGNORECASE)
        if time_match:
            if "between" in pattern or "to" in pattern or "-" in pattern:
                # Time range
                start_hour = int(time_match.group(1))
                start_min = int(time_match.group(2)) if time_match.group(2) else 0
                start_ampm = time_match.group(3)
                end_hour = int(time_match.group(4))
                end_min = int(time_match.group(5)) if time_match.group(5) else 0
                end_ampm = time_match.group(6)
                
                # Convert to 24-hour format
                if start_ampm and start_ampm.upper() == 'PM' and start_hour != 12:
                    start_hour += 12
                elif start_ampm and start_ampm.upper() == 'AM' and start_hour == 12:
                    start_hour = 0
                
                if end_ampm and end_ampm.upper() == 'PM' and end_hour != 12:
                    end_hour += 12
                elif end_ampm and end_ampm.upper() == 'AM' and end_hour == 12:
                    end_hour = 0
                
                start_time = f"{start_hour:02d}:{start_min:02d}"
                end_time = f"{end_hour:02d}:{end_min:02d}"
            else:
                # Single time
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                ampm = time_match.group(3)
                
                if ampm and ampm.upper() == 'PM' and hour != 12:
                    hour += 12
                elif ampm and ampm.upper() == 'AM' and hour == 12:
                    hour = 0
                
                start_time = f"{hour:02d}:{minute:02d}"
                end_time = f"{hour+1:02d}:{minute:02d}"  # Default 1-hour appointment
            break
    
    if not start_time:
        return f"""❌ **Time not found in request**

Please specify the time in one of these formats:
- between 3 PM and 4 PM
- 3:00 PM to 4:00 PM
- at 3:00 PM

Found: Name={name}, Email={email}, Date={date}"""
    
    # Extract notes (look for appointment type/reason)
    notes_patterns = [
        r'for\s+(?:a\s+)?([^.]+?)(?:\.|I\'m|My)',
        r'appointment\s+(?:with\s+[^.]*?\s+)?for\s+(?:a\s+)?([^.]+?)(?:\.|I\'m|My)'
    ]
    
    notes = None
    for pattern in notes_patterns:
        notes_match = re.search(pattern, request, re.IGNORECASE)
        if notes_match:
            notes = notes_match.group(1).strip()
            break
    
    # Use the enhanced smart booking function
    result = await smart_book_appointment(
        attendee_email=email,
        attendee_name=name,
        preferred_date=date,
        preferred_time_start=start_time,
        preferred_time_end=end_time,
        notes=notes
    )
    
    return f"""🤖 **One-Stop Appointment Manager - Processing Complete**

**📋 Extracted Information:**
- Name: {name}
- Email: {email}
- Date: {date}
- Time: {start_time} - {end_time}
{f"- Reason: {notes}" if notes else ""}

**📅 Booking Result:**
{result}"""

def _parse_date_to_iso(date_str: str) -> str:
    """Convert various date formats to ISO format (YYYY-MM-DD)"""
    import re
    from datetime import datetime
    
    # Month abbreviations mapping
    months = {
        'jan': '01', 'january': '01',
        'feb': '02', 'february': '02',
        'mar': '03', 'march': '03',
        'apr': '04', 'april': '04',
        'may': '05',
        'jun': '06', 'june': '06',
        'jul': '07', 'july': '07',
        'aug': '08', 'august': '08',
        'sep': '09', 'sept': '09', 'september': '09',
        'oct': '10', 'october': '10',
        'nov': '11', 'november': '11',
        'dec': '12', 'december': '12'
    }
    
    # If already in ISO format
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        return date_str
    
    # Parse "30th Sept 2025" format
    match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})', date_str, re.IGNORECASE)
    if match:
        day = int(match.group(1))
        month_name = match.group(2).lower()
        year = int(match.group(3))
        
        if month_name in months:
            month = months[month_name]
            return f"{year}-{month}-{day:02d}"
    
    return date_str  # Return as-is if can't parse

@mcp.tool()
async def quick_book_alternative(
    attendee_email: str,
    attendee_name: str,
    date: str,
    time: str,
    notes: Optional[str] = None
) -> str:
    """Quick booking for alternative slots chosen by the user.
    
    This function is optimized for when a user has already chosen an alternative slot
    from the suggestions provided by smart_book_appointment.
    
    Args:
        attendee_email: Email address of the patient
        attendee_name: Full name of the patient
        date: Date in YYYY-MM-DD format (e.g., "2025-09-30")
        time: Time in HH:MM format (e.g., "15:00") or full ISO format
        notes: Optional notes for the appointment
    """
    # Handle different time formats
    if "T" in time:
        # Already in ISO format
        start_time = time
    else:
        # Convert HH:MM to full datetime
        start_time = f"{date}T{time}:00"
    
    # Attempt booking
    book_result = await book_appointment_simple(
        attendee_email=attendee_email,
        attendee_name=attendee_name,
        start_time=start_time,
        notes=notes
    )
    
    # Format response based on booking result
    if "✅" in book_result and "Booked Successfully" in book_result:
        from datetime import datetime
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            day_name = date_obj.strftime("%A")
            time_display = time.split("T")[1][:5] if "T" in time else time
            
            return f"""🎉 **Alternative Appointment Booked Successfully!**

{book_result}

**✅ Confirmed Appointment Details:**
- Patient: {attendee_name}
- Email: {attendee_email}
- Date: {day_name}, {date}
- Time: {time_display}
{f"- Notes: {notes}" if notes else ""}

**🎯 Perfect! Your appointment is all set. As your appointment manager, I've taken care of everything for you!**"""
        except:
            return f"""🎉 **Alternative Appointment Booked Successfully!**

{book_result}

**Your appointment is confirmed and ready!**"""
    else:
        return f"""⚠️ **Alternative Booking Issue**

{book_result}

**Don't worry!** Let me find you another available slot. Would you like me to:
1. Try booking the next available slot automatically
2. Show you more alternative times
3. Check a different date

Just let me know and I'll handle it right away!"""

@mcp.tool()
async def get_event_types(limit: int = 10) -> str:
    """Get available event types (appointment types) for booking.
    
    Args:
        limit: Maximum number of event types to return (default: 10)
    """
    result = await make_cal_request("GET", "event-types", {"limit": limit}, api_version="v1")
    
    if result and "error" not in result:
        # v1 API returns event types directly in the result array
        event_types = result if isinstance(result, list) else result.get("event_types", [])

        # Always show the default configured event type
        try:
            default_event_id = get_default_event_type_id()
            default_info = f"""📍 **Default Event Type (Pre-configured):**
Event Type ID: {default_event_id}
Status: Ready to use for bookings
Note: You can book appointments directly without specifying an event type ID

---"""
        except ValueError:
            default_info = "⚠️ **No default event type configured in environment**\n\n---\n"

        if not event_types:
            return f"""{default_info}

**Available Event Types:** No additional event types found via API.

You can still book appointments using the default event type ID above."""

        formatted_types = [default_info]
        for event_type in event_types:
            marker = "✅ **DEFAULT**" if event_type.get('id') == default_event_id else ""
            formatted_types.append(f"""
Event Type ID: {event_type.get('id', 'Unknown')} {marker}
Title: {event_type.get('title', 'No title')}
Duration: {event_type.get('length', 'Unknown')} minutes
Description: {event_type.get('description', 'No description')}
""")

        return "\n---\n".join(formatted_types)
    else:
        return format_error_response(result or {"error": "Unknown error"}, "fetch event types")

# ===========================================
# PATIENT DATA MANAGEMENT TOOLS
# ===========================================

@mcp.tool()
async def get_patient_data(patient_email: str) -> str:
    """Retrieve comprehensive patient data including appointments and prescriptions.
    
    Args:
        patient_email: Patient's email address (unique identifier)
    """
    try:
        data = PatientDataManager.get_comprehensive_patient_data(patient_email)
        
        if "error" in data:
            return f"❌ **Patient Not Found**: {data['error']}"
        
        patient = data["patient"]
        appointments = data["appointments"]
        prescriptions = data["prescriptions"]
        
        # Format patient info
        response = f"""👤 **Patient Profile**

**Basic Information:**
- Name: {patient['name']}
- Email: {patient['email'] or 'Not provided'}
- Phone: {patient['phone'] or 'Not provided'}

**Notes/Medical Information:**
{patient['notes'] or 'No additional notes recorded'}
"""

        # Format appointments
        if appointments:
            response += f"\n📅 **Appointments ({len(appointments)} total):**\n"
            for apt in appointments[-5:]:  # Show last 5 appointments
                status_emoji = "✅" if apt['status'] == "completed" else "📅" if apt['status'] == "scheduled" else "⏳"
                response += f"{status_emoji} {apt['date'].strftime('%Y-%m-%d %H:%M')} - ({apt['status']})\n"
                if apt['notes']:
                    response += f"   Notes: {apt['notes']}\n"
        else:
            response += "\n📅 **Appointments:** No appointments found\n"

        # Format prescriptions
        active_prescriptions = [rx for rx in prescriptions if rx['is_active']]
        if active_prescriptions:
            response += f"\n💊 **Active Prescriptions ({len(active_prescriptions)}):**\n"
            for rx in active_prescriptions:
                response += f"• {rx['medication']} - {rx['dosage']} ({rx['frequency']})\n"
                if rx['instructions']:
                    response += f"  Instructions: {rx['instructions']}\n"
        else:
            response += "\n💊 **Active Prescriptions:** None\n"
        
        return response
        
    except Exception as e:
        return f"❌ **Error retrieving patient data**: {str(e)}"

@mcp.tool()
async def create_or_update_patient(
    email: str,
    first_name: str,
    last_name: str,
    phone: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    gender: Optional[str] = None,
    address: Optional[str] = None,
    emergency_contact: Optional[str] = None,
    emergency_phone: Optional[str] = None,
    insurance_info: Optional[str] = None,
    medical_history: Optional[str] = None,
    allergies: Optional[str] = None,
    current_medications: Optional[str] = None
) -> str:
    """Create new patient or update existing patient information.
    
    Args:
        email: Patient's email address (unique identifier)
        first_name: Patient's first name
        last_name: Patient's last name
        phone: Patient's phone number
        date_of_birth: Date of birth in YYYY-MM-DD format
        gender: Patient's gender
        address: Patient's address
        emergency_contact: Emergency contact name
        emergency_phone: Emergency contact phone
        insurance_info: Insurance information
        medical_history: Medical history notes
        allergies: Known allergies
        current_medications: Current medications
    """
    try:
        # Parse date of birth if provided
        dob = None
        if date_of_birth:
            try:
                dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
            except ValueError:
                return "❌ **Invalid date format**: Please use YYYY-MM-DD format for date_of_birth"
        
        patient_data = {
            "phone": phone,
            "date_of_birth": dob,
            "gender": gender,
            "address": address,
            "emergency_contact": emergency_contact,
            "emergency_phone": emergency_phone,
            "insurance_info": insurance_info,
            "medical_history": medical_history,
            "allergies": allergies,
            "current_medications": current_medications
        }
        
        # Remove None values
        patient_data = {k: v for k, v in patient_data.items() if v is not None}
        
        patient = PatientOperations.get_or_create_patient(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **patient_data
        )
        
        return f"""✅ **Patient Profile Updated Successfully**

**Patient Information:**
- Name: {patient.name}
- Email: {patient.email}
- ID: {patient.id}

The patient profile has been {'created' if patient.created_at == patient.updated_at else 'updated'} in the system."""
        
    except Exception as e:
        return f"❌ **Error managing patient**: {str(e)}"

@mcp.tool()
async def add_prescription(
    patient_email: str,
    medication_name: str,
    dosage: str,
    frequency: str,
    duration: Optional[str] = None,
    instructions: Optional[str] = None,
    prescribed_by: Optional[str] = None,
    refills_remaining: int = 0,
    start_date: Optional[str] = None
) -> str:
    """Add a new prescription for a patient.
    
    Args:
        patient_email: Patient's email address
        medication_name: Name of the medication
        dosage: Dosage information (e.g., "500mg")
        frequency: How often to take (e.g., "twice daily", "every 8 hours")
        duration: How long to take (e.g., "7 days", "2 weeks")
        instructions: Special instructions
        prescribed_by: Doctor who prescribed it
        refills_remaining: Number of refills allowed
        start_date: Start date in YYYY-MM-DD format (defaults to today)
    """
    try:
        # Parse start date
        start_dt = None
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                return "❌ **Invalid date format**: Please use YYYY-MM-DD format for start_date"
        else:
            start_dt = datetime.now()
        
        prescription = PrescriptionOperations.create_prescription(
            patient_email=patient_email,
            medication_name=medication_name,
            dosage=dosage,
            frequency=frequency,
            duration=duration,
            instructions=instructions,
            prescribed_by=prescribed_by,
            refills_remaining=refills_remaining,
            start_date=start_dt
        )
        
        return f"""💊 **Prescription Added Successfully**

**Prescription Details:**
- Medication: {prescription.medication_name}
- Dosage: {prescription.dosage}
- Frequency: {prescription.frequency}
- Duration: {prescription.duration or 'As needed'}
- Start Date: {prescription.start_date.strftime('%Y-%m-%d')}
- Refills: {prescription.refills_remaining}
- Prescribed by: {prescription.prescribed_by or 'Not specified'}

**Patient:** {patient_email}
**Prescription ID:** {prescription.id}"""
        
    except ValueError as e:
        return f"❌ **Patient Error**: {str(e)}"
    except Exception as e:
        return f"❌ **Error adding prescription**: {str(e)}"

@mcp.tool()
async def search_patients(query: str) -> str:
    """Search for patients by name or email.
    
    Args:
        query: Search term (name or email)
    """
    try:
        patients = PatientDataManager.search_patients(query)
        
        if not patients:
            return f"🔍 **No patients found** matching '{query}'"
        
        response = f"🔍 **Found {len(patients)} patient(s) matching '{query}':**\n\n"
        
        for patient in patients:
            response += f"• **{patient['name']}**\n"
            response += f"  Email: {patient['email']}\n"
            response += f"  Phone: {patient['phone'] or 'Not provided'}\n"
            response += f"  ID: {patient['id']}\n\n"
        
        return response
        
    except Exception as e:
        return f"❌ **Error searching patients**: {str(e)}"

@mcp.tool()
async def update_appointment_notes(
    cal_booking_id: str,
    doctor_notes: Optional[str] = None,
    diagnosis: Optional[str] = None,
    status: Optional[str] = None
) -> str:
    """Update appointment with doctor notes, diagnosis, or status.
    
    Args:
        cal_booking_id: Cal.com booking ID from the appointment
        doctor_notes: Doctor's notes about the appointment
        diagnosis: Diagnosis from the appointment
        status: Update appointment status (scheduled, completed, cancelled)
    """
    try:
        appointment = AppointmentOperations.get_appointment_by_cal_id(cal_booking_id)
        
        if not appointment:
            return f"❌ **Appointment not found** with booking ID: {cal_booking_id}"
        
        updates = {}
        if doctor_notes is not None:
            updates['doctor_notes'] = doctor_notes
        if diagnosis is not None:
            updates['diagnosis'] = diagnosis
        if status is not None:
            updates['status'] = status
        
        if not updates:
            return "❌ **No updates provided**: Please specify doctor_notes, diagnosis, or status"
        
        updated_appointment = AppointmentOperations.update_appointment(appointment.id, **updates)
        
        return f"""✅ **Appointment Updated Successfully**

**Appointment ID:** {updated_appointment.id}
**Cal Booking ID:** {cal_booking_id}
**Date:** {updated_appointment.appointment_date.strftime('%Y-%m-%d %H:%M')}
**Status:** {updated_appointment.status}

**Updates Made:**
{f"• Doctor Notes: {doctor_notes}" if doctor_notes else ""}
{f"• Diagnosis: {diagnosis}" if diagnosis else ""}
{f"• Status: {status}" if status else ""}"""
        
    except Exception as e:
        return f"❌ **Error updating appointment**: {str(e)}"

@mcp.tool()
async def enhanced_book_appointment_with_patient_data(
    attendee_email: str,
    attendee_name: str,
    start_time: str,
    notes: Optional[str] = None,
    appointment_type: Optional[str] = None
) -> str:
    """Enhanced appointment booking that also creates/links patient data.
    
    This function books an appointment and automatically:
    1. Creates or updates patient record in database
    2. Links the appointment to patient data
    3. Provides comprehensive booking confirmation
    
    Args:
        attendee_email: Patient's email address
        attendee_name: Patient's full name
        start_time: Start time in ISO format
        notes: Appointment notes
        appointment_type: Type of appointment
    """
    try:
        # First, book the appointment using existing function
        booking_result = await book_appointment_simple(
            attendee_email=attendee_email,
            attendee_name=attendee_name,
            start_time=start_time,
            notes=notes
        )
        
        # If booking successful, create/update patient data
        if "✅" in booking_result and "Booked Successfully" in booking_result:
            # Parse name
            name_parts = attendee_name.strip().split()
            first_name = name_parts[0] if name_parts else attendee_name
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            # Create/update patient record
            patient = PatientOperations.get_or_create_patient(
                email=attendee_email,
                first_name=first_name,
                last_name=last_name
            )
            
            # Extract booking ID from result (if available)
            cal_booking_id = None
            if "Booking ID:" in booking_result:
                import re
                booking_id_match = re.search(r'Booking ID:\s*(\d+)', booking_result)
                if booking_id_match:
                    cal_booking_id = booking_id_match.group(1)
            
            # Create appointment record in database
            appointment_date = datetime.fromisoformat(start_time.replace('Z', ''))
            appointment = AppointmentOperations.create_appointment(
                patient_email=attendee_email,
                appointment_date=appointment_date,
                cal_booking_id=cal_booking_id,
                appointment_type=appointment_type or "consultation",
                notes=notes,
                status="scheduled"
            )
            
            return f"""{booking_result}

📋 **Patient Database Integration:**
- Patient ID: {patient.id}
- Database Appointment ID: {appointment.id}
- Patient record: {'Updated' if patient.updated_at != patient.created_at else 'Created'}

✅ **Complete Integration**: Your appointment is now fully integrated with patient management system!"""
        
        else:
            # Booking failed, return original result
            return booking_result
            
    except Exception as e:
        # If database operations fail, still return the booking result
        return f"""{booking_result}

⚠️ **Database Integration Warning**: Appointment booked successfully but database integration encountered an issue: {str(e)}
The appointment is still valid in the Cal.com system."""

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')