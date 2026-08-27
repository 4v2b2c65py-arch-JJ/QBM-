"""
Gmail OAuth Integration
Uses Google OAuth 2.0 for browser-based login
Sends and receives emails via Gmail API
"""

import os
import json
import base64
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Email parsing
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# =============================================================================
# CONFIGURATION
# =============================================================================

GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
]

TOKEN_PATH = Path(__file__).parent / '.gmail_token.pickle'
CREDENTIALS_PATH = Path(__file__).parent / 'credentials.json'


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class GmailMessage:
    """Represents a Gmail message."""
    message_id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    body_text: str
    body_html: str
    date: str
    labels: List[str] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SendResult:
    """Result of sending an email."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# GMAIL OAUTH ENGINE
# =============================================================================

class GmailOAuthEngine:
    """
    Gmail integration using OAuth 2.0 browser flow.
    
    Features:
    - Browser-based Google login
    - Send emails via Gmail API
    - Read/receive emails
    - Automatic token refresh
    - Secure token storage
    """
    
    def __init__(self):
        self._creds: Optional[Credentials] = None
        self._service = None
        self._user_email: Optional[str] = None
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self._creds is not None and self._creds.valid
    
    @property
    def user_email(self) -> Optional[str]:
        """Get authenticated user's email."""
        return self._user_email
    
    # -------------------------------------------------------------------------
    # AUTHENTICATION
    # -------------------------------------------------------------------------
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google via OAuth browser flow.
        
        Opens browser for user to login to Google account.
        Returns True if authentication successful.
        """
        creds = None
        
        # Load existing token
        if TOKEN_PATH.exists():
            with open(TOKEN_PATH, 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    print("[Gmail] Token refreshed successfully")
                except Exception as e:
                    print(f"[Gmail] Token refresh failed: {e}")
                    creds = None
            
            if not creds:
                if not CREDENTIALS_PATH.exists():
                    print(f"[Gmail] credentials.json not found at {CREDENTIALS_PATH}")
                    print("[Gmail] Please download credentials.json from Google Cloud Console")
                    return False
                
                # Open browser for OAuth login
                print("[Gmail] Opening browser for Google login...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_PATH), GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=0)
                print("[Gmail] Browser login successful!")
            
            # Save token for future use
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)
                print(f"[Gmail] Token saved to {TOKEN_PATH}")
        
        self._creds = creds
        self._service = build('gmail', 'v1', credentials=creds)
        
        # Get user email
        self._get_user_email()
        
        return True
    
    def _get_user_email(self):
        """Get the authenticated user's email address."""
        try:
            profile = self._service.users().getProfile(userId='me').execute()
            self._user_email = profile.get('emailAddress', '')
            print(f"[Gmail] Authenticated as: {self._user_email}")
        except Exception as e:
            print(f"[Gmail] Could not get user email: {e}")
    
    def logout(self):
        """Logout and remove stored token."""
        if TOKEN_PATH.exists():
            TOKEN_PATH.unlink()
        self._creds = None
        self._service = None
        self._user_email = None
        print("[Gmail] Logged out and token removed")
    
    # -------------------------------------------------------------------------
    # SENDING EMAILS
    # -------------------------------------------------------------------------
    
    def send_email(self, to: str, subject: str,
                   body_text: str = "", body_html: str = "",
                   sender_name: str = "ManaCiel System") -> SendResult:
        """
        Send an email via Gmail API.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)
            sender_name: Display name for sender
            
        Returns:
            SendResult with success status
        """
        if not self.is_authenticated:
            return SendResult(success=False, error="Not authenticated")
        
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['from'] = f"{sender_name} <{self._user_email}>"
            message['subject'] = subject
            
            # Add text part
            if body_text:
                text_part = MIMEText(body_text, 'plain')
                message.attach(text_part)
            
            # Add HTML part
            if body_html:
                html_part = MIMEText(body_html, 'html')
                message.attach(html_part)
            
            # Encode to base64
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            # Send via Gmail API
            sent = self._service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            message_id = sent.get('id', '')
            print(f"[Gmail] Email sent to {to} (ID: {message_id})")
            
            return SendResult(success=True, message_id=message_id)
            
        except HttpError as e:
            error_msg = f"Gmail API error: {e.resp.status} - {e._get_reason()}"
            print(f"[Gmail] {error_msg}")
            return SendResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = f"Send error: {str(e)}"
            print(f"[Gmail] {error_msg}")
            return SendResult(success=False, error=error_msg)
    
    def send_reply(self, message_id: str, to: str, subject: str,
                   body_text: str = "", body_html: str = "") -> SendResult:
        """
        Reply to an existing email.
        
        Args:
            message_id: ID of message to reply to
            to: Recipient email
            subject: Reply subject
            body_text: Plain text body
            body_html: HTML body
            
        Returns:
            SendResult with success status
        """
        if not self.is_authenticated:
            return SendResult(success=False, error="Not authenticated")
        
        try:
            # Create reply message
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['subject'] = subject
            message['In-Reply-To'] = message_id
            message['References'] = message_id
            
            if body_text:
                message.attach(MIMEText(body_text, 'plain'))
            if body_html:
                message.attach(MIMEText(body_html, 'html'))
            
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            sent = self._service.users().messages().send(
                userId='me',
                body={'raw': message.as_bytes().decode('latin-1')}
            ).execute()
            
            return SendResult(success=True, message_id=sent.get('id', ''))
            
        except Exception as e:
            return SendResult(success=False, error=str(e))
    
    # -------------------------------------------------------------------------
    # RECEIVING EMAILS
    # -------------------------------------------------------------------------
    
    def get_inbox(self, max_results: int = 10,
                  label_ids: List[str] = None,
                  query: str = None) -> List[GmailMessage]:
        """
        Get emails from inbox.
        
        Args:
            max_results: Maximum number of emails to retrieve
            label_ids: Filter by labels (e.g., ['INBOX', 'UNREAD'])
            query: Gmail search query (e.g., 'from:someone@example.com')
            
        Returns:
            List of GmailMessage objects
        """
        if not self.is_authenticated:
            return []
        
        try:
            params = {
                'userId': 'me',
                'maxResults': max_results,
            }
            
            if label_ids:
                params['labelIds'] = label_ids
            if query:
                params['q'] = query
            
            results = self._service.users().messages().list(**params).execute()
            messages = results.get('messages', [])
            
            gmail_messages = []
            for msg in messages:
                full_msg = self.get_message(msg['id'])
                if full_msg:
                    gmail_messages.append(full_msg)
            
            return gmail_messages
            
        except Exception as e:
            print(f"[Gmail] Error fetching inbox: {e}")
            return []
    
    def get_message(self, message_id: str) -> Optional[GmailMessage]:
        """
        Get a specific email by ID.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            GmailMessage object or None
        """
        if not self.is_authenticated:
            return None
        
        try:
            msg = self._service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return self._parse_message(msg)
            
        except Exception as e:
            print(f"[Gmail] Error fetching message {message_id}: {e}")
            return None
    
    def _parse_message(self, msg: Dict) -> GmailMessage:
        """Parse Gmail API message into GmailMessage object."""
        headers = msg.get('payload', {}).get('headers', [])
        
        sender = ''
        recipient = ''
        subject = ''
        date = ''
        
        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')
            
            if name == 'from':
                sender = value
            elif name == 'to':
                recipient = value
            elif name == 'subject':
                subject = value
            elif name == 'date':
                date = value
        
        # Extract body
        body_text, body_html = self._extract_body(msg.get('payload', {}))
        
        return GmailMessage(
            message_id=msg.get('id', ''),
            thread_id=msg.get('threadId', ''),
            sender=sender,
            recipient=recipient,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            date=date,
            labels=msg.get('labelIds', []),
        )
    
    def _extract_body(self, payload: Dict) -> tuple:
        """Extract text and HTML body from message payload."""
        text = ''
        html = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                data = part.get('body', {}).get('data', '')
                
                if data:
                    decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    
                    if mime_type == 'text/plain':
                        text = decoded
                    elif mime_type == 'text/html':
                        html = decoded
        else:
            data = payload.get('body', {}).get('data', '')
            if data:
                text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return text, html
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read."""
        if not self.is_authenticated:
            return False
        
        try:
            self._service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            print(f"[Gmail] Error marking as read: {e}")
            return False
    
    def archive_message(self, message_id: str) -> bool:
        """Archive an email (remove from inbox)."""
        if not self.is_authenticated:
            return False
        
        try:
            self._service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            return True
        except Exception as e:
            print(f"[Gmail] Error archiving: {e}")
            return False
    
    # -------------------------------------------------------------------------
    # LABELS
    # -------------------------------------------------------------------------
    
    def get_labels(self) -> List[Dict[str, str]]:
        """Get all Gmail labels."""
        if not self.is_authenticated:
            return []
        
        try:
            results = self._service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            return [{'id': l['id'], 'name': l['name']} for l in labels]
        except Exception as e:
            print(f"[Gmail] Error fetching labels: {e}")
            return []
    
    def create_label(self, name: str) -> Optional[str]:
        """Create a new Gmail label."""
        if not self.is_authenticated:
            return None
        
        try:
            label = self._service.users().labels().create(
                userId='me',
                body={'name': name, 'labelListVisibility': 'labelShow'}
            ).execute()
            return label.get('id')
        except Exception as e:
            print(f"[Gmail] Error creating label: {e}")
            return None


# =============================================================================
# GOOGLE CLOUD SETUP INSTRUCTIONS
# =============================================================================

SETUP_INSTRUCTIONS = """
=============================================================================
GOOGLE CLOUD CONSOLE SETUP - GMAIL API
=============================================================================

1. Go to https://console.cloud.google.com/

2. Create a new project (or select existing):
   - Click project dropdown at top
   - Click "New Project"
   - Name: "ManaCiel System"

3. Enable Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search "Gmail API"
   - Click "Enable"

4. Create OAuth credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure OAuth consent screen:
     * User Type: External
     * App name: "ManaCiel System"
     * User support email: your-email@gmail.com
     * Developer contact: your-email@gmail.com
     * Scopes: Add gmail.send, gmail.readonly, gmail.modify
     * Test users: Add your-email@gmail.com
   - Application type: "Desktop app"
   - Name: "ManaCiel Desktop Client"

5. Download credentials:
   - Click the download icon for your new OAuth client
   - Save as "credentials.json" in the same folder as this script

6. Run authentication:
   - The system will open your browser
   - Login to your Google account
   - Grant permissions
   - Token will be saved for future use

=============================================================================
"""


# =============================================================================
# MAIN INTERFACE
# =============================================================================

# Global instance
gmail_engine = GmailOAuthEngine()


def setup_gmail() -> bool:
    """
    Run the Gmail setup process.
    Opens browser for OAuth login.
    """
    print(SETUP_INSTRUCTIONS)
    
    if not CREDENTIALS_PATH.exists():
        print(f"\n[ERROR] credentials.json not found!")
        print(f"Please download it from Google Cloud Console and save to:")
        print(f"  {CREDENTIALS_PATH}")
        return False
    
    return gmail_engine.authenticate()


def send_email(to: str, subject: str, body_text: str = "",
               body_html: str = "") -> SendResult:
    """Send an email via Gmail."""
    return gmail_engine.send_email(to, subject, body_text, body_html)


def get_inbox(max_results: int = 10) -> List[GmailMessage]:
    """Get emails from inbox."""
    return gmail_engine.get_inbox(max_results)


if __name__ == '__main__':
    print("Gmail OAuth Integration")
    print("=" * 60)
    
    if setup_gmail():
        print("\n[Gmail] Setup complete!")
        print(f"[Gmail] Authenticated as: {gmail_engine.user_email}")
        
        # Test send
        result = send_email(
            to=gmail_engine.user_email,
            subject="Gmail Integration Test",
            body_text="Gmail OAuth is now working!",
            body_html="<h1>Gmail Integration Active</h1><p>OAuth login successful.</p>"
        )
        
        if result.success:
            print("[Gmail] Test email sent!")
        else:
            print(f"[Gmail] Test failed: {result.error}")
    else:
        print("\n[Gmail] Setup failed!")
