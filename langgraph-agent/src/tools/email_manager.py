from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os
from privacy.privacy_manager import PrivacyManager
from pydantic import BaseModel, EmailStr

class EmailConfig(BaseModel):
    """Configuration for email settings."""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email: EmailStr
    password: str  # App-specific password for Gmail
    
class EmailManager:
    """Tool for composing and sending emails securely."""
    
    def __init__(self, config: EmailConfig, privacy_manager: PrivacyManager):
        """Initialize email manager with configuration."""
        self.config = config
        self.privacy_manager = privacy_manager
        self.server = None
        
    def _connect(self) -> None:
        """Establish connection to SMTP server."""
        if self.server is None:
            self.server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            self.server.starttls()
            self.server.login(self.config.email, self.config.password)
            
    def _disconnect(self) -> None:
        """Close SMTP connection."""
        if self.server:
            self.server.quit()
            self.server = None
            
    def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email to specified recipients.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if self.privacy_manager.is_sensitive_data("emails"):
            if not self.privacy_manager.ask_permission("send email", "email"):
                return False
                
            # Encrypt sensitive content
            body = self.privacy_manager.encrypt_data(body).decode()
            subject = self.privacy_manager.encrypt_data(subject).decode()
        
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config.email
            msg["To"] = ", ".join(to)
            msg["Subject"] = subject
            
            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)
                
            msg.attach(MIMEText(body, "plain"))
            
            recipients = to.copy()
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
                
            self._connect()
            self.server.send_message(msg)
            self._disconnect()
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
            
    def draft_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> dict:
        """
        Create a draft email without sending it.
        
        Returns:
            dict: Draft email content
        """
        return {
            "to": to,
            "cc": cc or [],
            "bcc": bcc or [],
            "subject": subject,
            "body": body
        }