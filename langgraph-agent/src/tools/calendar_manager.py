from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pathlib import Path
import pickle
import os
from ..privacy.privacy_manager import PrivacyManager

class CalendarManager:
    """Tool for scheduling and managing meetings using Google Calendar."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, privacy_manager: PrivacyManager, credentials_file: str = 'credentials.json'):
        """Initialize calendar manager."""
        self.privacy_manager = privacy_manager
        self.credentials_file = credentials_file
        self.credentials = self._get_credentials()
        self.service = build('calendar', 'v3', credentials=self.credentials)
        
    def _get_credentials(self) -> Credentials:
        """Get or refresh Google Calendar credentials."""
        creds = None
        token_file = 'token.pickle'
        
        # Load existing credentials if available
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
                
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Save credentials
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
                
        return creds
        
    def schedule_meeting(
        self,
        summary: str,
        start_time: datetime,
        duration_minutes: int,
        attendees: List[str],
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule a new meeting.
        
        Args:
            summary: Meeting title
            start_time: Meeting start time
            duration_minutes: Duration in minutes
            attendees: List of attendee email addresses
            description: Optional meeting description
            location: Optional meeting location
            
        Returns:
            dict: Created event details
        """
        if self.privacy_manager.is_sensitive_data("calendar"):
            if not self.privacy_manager.ask_permission("schedule", "meeting"):
                return {}
                
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Chicago',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Chicago',
            },
            'attendees': [{'email': email} for email in attendees],
            'reminders': {
                'useDefault': True,
            },
        }
        
        try:
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            return event
        except Exception as e:
            print(f"Error scheduling meeting: {e}")
            return {}
            
    def get_available_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        working_hours: Dict[str, tuple] = None
    ) -> List[datetime]:
        """
        Find available time slots for a meeting.
        
        Args:
            start_date: Start date to look for slots
            end_date: End date to look for slots
            duration_minutes: Required duration in minutes
            working_hours: Optional dict of day-of-week to (start_hour, end_hour)
            
        Returns:
            list: List of available datetime slots
        """
        if working_hours is None:
            working_hours = {
                'monday': (9, 17),
                'tuesday': (9, 17),
                'wednesday': (9, 17),
                'thursday': (9, 17),
                'friday': (9, 17)
            }
            
        # Get existing events
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=start_date.isoformat() + 'Z',
            timeMax=end_date.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Find available slots
        available_slots = []
        current = start_date
        
        while current < end_date:
            day = current.strftime('%A').lower()
            if day in working_hours:
                start_hour, end_hour = working_hours[day]
                day_start = current.replace(hour=start_hour, minute=0)
                day_end = current.replace(hour=end_hour, minute=0)
                
                # Check each potential slot
                slot = day_start
                while slot + timedelta(minutes=duration_minutes) <= day_end:
                    is_available = True
                    
                    # Check if slot conflicts with any event
                    for event in events:
                        event_start = datetime.fromisoformat(event['start']['dateTime'])
                        event_end = datetime.fromisoformat(event['end']['dateTime'])
                        
                        if (slot < event_end and 
                            slot + timedelta(minutes=duration_minutes) > event_start):
                            is_available = False
                            break
                            
                    if is_available:
                        available_slots.append(slot)
                        
                    slot += timedelta(minutes=30)  # Check every 30 minutes
                    
            current += timedelta(days=1)
            current = current.replace(hour=0, minute=0)
            
        return available_slots
        
    def cancel_meeting(self, event_id: str) -> bool:
        """
        Cancel a scheduled meeting.
        
        Args:
            event_id: ID of the event to cancel
            
        Returns:
            bool: True if cancelled successfully, False otherwise
        """
        if self.privacy_manager.is_sensitive_data("calendar"):
            if not self.privacy_manager.ask_permission("cancel", "meeting"):
                return False
                
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return True
        except Exception as e:
            print(f"Error cancelling meeting: {e}")
            return False