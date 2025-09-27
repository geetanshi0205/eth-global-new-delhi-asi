import smtplib
import os
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email = os.getenv("GMAIL_EMAIL")
        self.password = os.getenv("GMAIL_APP_PASSWORD")
        
        if not self.email or not self.password:
            raise ValueError("GMAIL_EMAIL and GMAIL_APP_PASSWORD environment variables are required")
    
    def generate_mpin(self, length: int = 6) -> str:
        """Generate a random MPIN"""
        digits = string.digits
        return ''.join(secrets.choice(digits) for _ in range(length))
    
    def send_report_notification(self, patient_email: str, report_id: str, mpin: str, report_type: str) -> bool:
        """Send email notification to patient with report ID and MPIN"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = patient_email
            msg['Subject'] = f"Your {report_type.title()} Report is Ready"
            
            body = f"""
Dear Patient,

Your {report_type.title()} report has been successfully submitted and is now available for review.

Report Details:
- Report ID: {report_id}
- MPIN: {mpin}
- Report Type: {report_type.title()}

Please keep your Report ID and MPIN secure. You will need both to access your report.

If you have any questions, please contact our office.

Best regards,
Medical Team
            """.strip()
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            
            text = msg.as_string()
            server.sendmail(self.email, patient_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False