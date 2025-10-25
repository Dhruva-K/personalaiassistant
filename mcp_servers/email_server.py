#!/usr/bin/env python3
"""
MCP Server for Gmail Email Management
Handles real email sending via Gmail API
All credentials stored securely in secrets/ directory
"""
import os
import base64
import pickle
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("EmailServer")

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly'
]

# Paths to credentials (stored securely)
CREDENTIALS_PATH = os.getenv('GMAIL_CREDENTIALS_PATH', 'secrets/gmail_credentials.json')
TOKEN_PATH = os.getenv('GMAIL_TOKEN_PATH', 'secrets/gmail_token.pickle')


def get_gmail_service():
    """
    Get authenticated Gmail service.
    Credentials are stored in secrets/ directory and never exposed.
    """
    creds = None
    
    # Ensure secrets directory exists
    secrets_dir = Path('secrets')
    secrets_dir.mkdir(exist_ok=True)
    
    # Load existing token
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    
    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Gmail credentials not found at {CREDENTIALS_PATH}\n\n"
                    "Setup instructions:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Create/select a project\n"
                    "3. Enable Gmail API\n"
                    "4. Create OAuth 2.0 credentials (Desktop app)\n"
                    "5. Download as 'gmail_credentials.json' in secrets/ folder"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials securely
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)


def create_message(to: str, subject: str, body: str, cc: Optional[str] = None):
    """Create a MIME message for email."""
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    
    if cc:
        message['cc'] = cc
    
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}


@mcp.tool()
def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None
) -> str:
    """
    Send an email via Gmail.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email content (plain text)
        cc: CC recipients (comma-separated, optional)
    
    Returns:
        Confirmation message with email ID
    
    Examples:
        send_email("colleague@example.com", "Meeting Notes", "Here are the notes from our meeting...")
        send_email("team@company.com", "Update", "Project status update", "manager@company.com")
    """
    try:
        service = get_gmail_service()
        
        # Create message
        message = create_message(to, subject, body, cc)
        
        # Send message
        sent_message = service.users().messages().send(
            userId='me',
            body=message
        ).execute()
        
        result = f"✓ Email sent successfully!\n\n"
        result += f"To: {to}\n"
        if cc:
            result += f"CC: {cc}\n"
        result += f"Subject: {subject}\n"
        result += f"Message ID: {sent_message['id']}\n"
        result += f"\n✅ Email delivered via Gmail API"
        
        return result
    
    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Error sending email: {str(e)}\n\nPlease check:\n- Gmail API is enabled\n- Credentials are valid\n- Internet connection"


@mcp.tool()
def draft_email(
    to: str,
    subject: str,
    body: Optional[str] = None
) -> str:
    """
    Create an email draft in Gmail.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email content (optional)
    
    Returns:
        Draft confirmation with draft ID
    
    Examples:
        draft_email("client@company.com", "Project Proposal", "Dear Client,\n\nI wanted to...")
    """
    try:
        service = get_gmail_service()
        
        # Create draft message
        draft_body = body or "[Draft - Please add content]"
        message = create_message(to, subject, draft_body)
        
        draft = service.users().drafts().create(
            userId='me',
            body={'message': message}
        ).execute()
        
        result = f"✓ Draft created successfully!\n\n"
        result += f"To: {to}\n"
        result += f"Subject: {subject}\n"
        result += f"Draft ID: {draft['id']}\n"
        result += f"\n💡 You can edit this draft in Gmail before sending"
        
        return result
    
    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Error creating draft: {str(e)}"


@mcp.tool()
def list_recent_emails(max_results: int = 10, query: Optional[str] = None) -> str:
    """
    List recent emails from Gmail inbox.
    
    Args:
        max_results: Maximum number of emails to return (default: 10)
        query: Gmail search query (optional, e.g., "from:someone@example.com")
    
    Returns:
        List of recent emails with sender, subject, and date
    
    Examples:
        list_recent_emails(5)
        list_recent_emails(10, "from:boss@company.com")
    """
    try:
        service = get_gmail_service()
        
        # Get messages
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=query or ''
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return "No emails found matching your criteria."
        
        result = f"📧 Recent emails ({len(messages)}):\n\n"
        
        for msg in messages:
            # Get full message details
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = {h['name']: h['value'] for h in message['payload']['headers']}
            
            result += f"From: {headers.get('From', 'Unknown')}\n"
            result += f"Subject: {headers.get('Subject', '(No subject)')}\n"
            result += f"Date: {headers.get('Date', 'Unknown')}\n"
            result += "-" * 60 + "\n"
        
        return result
    
    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Error listing emails: {str(e)}"


@mcp.tool()
def search_emails(query: str, max_results: int = 10) -> str:
    """
    Search emails in Gmail.
    
    Args:
        query: Gmail search query (e.g., "subject:meeting", "from:boss@company.com", "has:attachment")
        max_results: Maximum results to return (default: 10)
    
    Returns:
        Matching emails
    
    Examples:
        search_emails("subject:invoice")
        search_emails("from:client@company.com after:2024/01/01")
    """
    return list_recent_emails(max_results, query)


if __name__ == "__main__":
    mcp.run(transport="stdio")