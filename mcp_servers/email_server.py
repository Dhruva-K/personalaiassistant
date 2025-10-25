#!/usr/bin/env python3
"""
MCP Server for Email Management
Handles email sending with privacy protection
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("EmailServer")


@mcp.tool()
def send_email(to_email: str, subject: str, body: str, from_email: Optional[str] = None) -> str:
    """
    Send an email to a recipient.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body content
        from_email: Sender email (optional, uses env var if not provided)
    
    Returns:
        Status message indicating success or failure
    """
    try:
        from_email = from_email or os.getenv("SMTP_EMAIL")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        
        if not from_email or not smtp_password:
            return "Error: Email credentials not configured. Please set SMTP_EMAIL and SMTP_PASSWORD environment variables."
        
        message = MIMEMultipart()
        message["From"] = from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, smtp_password)
            server.send_message(message)
        
        return f"Email successfully sent to {to_email}"
    
    except Exception as e:
        return f"Error sending email: {str(e)}"


@mcp.tool()
def draft_email(recipient: str, purpose: str) -> str:
    """
    Ask user for email details before sending.
    
    Args:
        recipient: Who should receive the email
        purpose: Purpose of the email
    
    Returns:
        Clarifying questions for the user
    """
    return f"To send an email to {recipient} about {purpose}, I need:\n1. What should the subject line be?\n2. What would you like to say in the email body?"


if __name__ == "__main__":
    mcp.run(transport="stdio")
