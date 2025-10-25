#!/usr/bin/env python3
"""
MCP Server for Calendar Management
Handles meeting scheduling via Google Calendar
"""
import os
import pickle
from datetime import datetime, timedelta
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("CalendarServer")

SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_calendar_service():
    """Get authenticated Google Calendar service."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "Google Calendar credentials not found. "
                    "Please download credentials.json from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)


@mcp.tool()
def schedule_meeting(
    title: str,
    start_time: str,
    duration_minutes: int = 60,
    attendees: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Schedule a meeting on Google Calendar.
    
    Args:
        title: Meeting title
        start_time: Start time in ISO format (YYYY-MM-DD HH:MM)
        duration_minutes: Meeting duration in minutes (default: 60)
        attendees: Comma-separated list of attendee emails (optional)
        description: Meeting description (optional)
    
    Returns:
        Status message with meeting link
    """
    try:
        service = get_calendar_service()
        
        start_dt = datetime.fromisoformat(start_time)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        event = {
            'summary': title,
            'description': description or '',
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'UTC',
            },
        }
        
        if attendees:
            event['attendees'] = [
                {'email': email.strip()}
                for email in attendees.split(',')
            ]
        
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        return f"Meeting scheduled successfully! Link: {created_event.get('htmlLink')}"
    
    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Error scheduling meeting: {str(e)}"


@mcp.tool()
def list_upcoming_meetings(days: int = 7) -> str:
    """
    List upcoming meetings for the next N days.
    
    Args:
        days: Number of days to look ahead (default: 7)
    
    Returns:
        List of upcoming meetings
    """
    try:
        service = get_calendar_service()
        
        now = datetime.utcnow().isoformat() + 'Z'
        max_time = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=max_time,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"No upcoming meetings in the next {days} days."
        
        result = f"Upcoming meetings (next {days} days):\n\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            result += f"- {event['summary']} at {start}\n"
        
        return result
    
    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Error listing meetings: {str(e)}"


@mcp.tool()
def ask_meeting_details(purpose: str, participants: Optional[str] = None) -> str:
    """
    Ask user for meeting scheduling details.
    
    Args:
        purpose: Purpose of the meeting
        participants: Known participants (optional)
    
    Returns:
        Clarifying questions for scheduling
    """
    questions = [
        f"To schedule a meeting about '{purpose}', I need some information:",
        "1. When would you like to schedule it? (Please provide date and time, e.g., 2025-10-26 14:00)",
        "2. How long should the meeting be? (in minutes)",
    ]
    
    if not participants:
        questions.append("3. Who should attend? (Please provide email addresses)")
    
    return "\n".join(questions)


if __name__ == "__main__":
    mcp.run(transport="stdio")
