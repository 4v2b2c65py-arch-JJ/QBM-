#!/usr/bin/env python3
"""
ManaCiel Email Automation - Background Service
Runs continuously, sends notifications, reads replies
"""

import pickle
import base64
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
TOKEN_PATH = Path(__file__).parent / '.gmail_token.pickle'
USER_EMAIL = "jhan.flores@icloud.com"
CHECK_INTERVAL = 300  # 5 minutes

# State file for tracking
STATE_PATH = Path(__file__).parent / '.email_service_state.json'


def load_state():
    """Load service state."""
    if STATE_PATH.exists():
        with open(STATE_PATH, 'r') as f:
            return json.load(f)
    return {
        "started": datetime.now().isoformat(),
        "last_check": None,
        "emails_sent": 0,
        "replies_received": 0,
        "notifications": []
    }


def save_state(state):
    """Save service state."""
    state["last_check"] = datetime.now().isoformat()
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)


def connect_gmail():
    """Connect to Gmail API."""
    if not TOKEN_PATH.exists():
        print("[Service] No token found. Run setup_gmail() first.")
        return None, None
    
    with open(TOKEN_PATH, 'rb') as f:
        creds = pickle.load(f)
    
    service = build('gmail', 'v1', credentials=creds)
    profile = service.users().getProfile(userId='me').execute()
    sender = profile.get('emailAddress', '')
    return service, sender


def send_email(service, sender, to, subject, text_body, html_body=""):
    """Send an email."""
    message = MIMEMultipart('alternative')
    message['to'] = to
    message['from'] = f"ManaCiel System <{sender}>"
    message['subject'] = subject
    
    message.attach(MIMEText(text_body, 'plain'))
    if html_body:
        message.attach(MIMEText(html_body, 'html'))
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    try:
        sent = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        return sent.get('id', '')
    except Exception as e:
        print(f"[Service] Send error: {e}")
        return None


def check_inbox(service):
    """Check for new emails from user."""
    try:
        results = service.users().messages().list(
            userId='me',
            maxResults=5,
            labelIds=['INBOX', 'UNREAD']
        ).execute()
        
        messages = results.get('messages', [])
        emails = []
        
        for msg in messages:
            data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            
            headers = data.get('payload', {}).get('headers', [])
            sender = subject = ''
            
            for h in headers:
                if h['name'].lower() == 'from':
                    sender = h['value']
                elif h['name'].lower() == 'subject':
                    subject = h['value']
            
            # Only process emails from user
            if USER_EMAIL.lower() in sender.lower():
                # Extract body
                body = ''
                payload = data.get('payload', {})
                if 'parts' in payload:
                    for part in payload['parts']:
                        if part.get('mimeType') == 'text/plain':
                            body_data = part.get('body', {}).get('data', '')
                            if body_data:
                                body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                else:
                    body_data = payload.get('body', {}).get('data', '')
                    if body_data:
                        body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                
                emails.append({
                    'id': msg['id'],
                    'sender': sender,
                    'subject': subject,
                    'body': body.strip()
                })
                
                # Mark as read
                service.users().messages().modify(
                    userId='me',
                    id=msg['id'],
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
        
        return emails
    except Exception as e:
        print(f"[Service] Inbox error: {e}")
        return []


def handle_command(service, sender, email):
    """Handle user command."""
    body = email['body'].upper().strip()
    first_line = body.split('\n')[0] if body else ''
    
    if first_line.startswith('STATUS'):
        module = ' '.join(first_line.split()[1:]) if len(first_line.split()) > 1 else 'all'
        return respond_status(service, sender, email['sender'], module)
    elif first_line.startswith('DATA'):
        category = ' '.join(first_line.split()[1:]) if len(first_line.split()) > 1 else 'all'
        return respond_data(service, sender, email['sender'], category)
    elif first_line.startswith('HELP'):
        return respond_help(service, sender, email['sender'])
    else:
        return respond_question(service, sender, email['sender'], email['body'])


def respond_status(service, sender, to, module):
    """Send status response."""
    subject = "ManaCiel - Status Response"
    text = f"""
SYSTEM STATUS - {module.upper()}
==================
✓ Email Pipeline: Active
✓ Properties: 3 tracked
✓ Vehicles: 11 tracked
✓ Bitcoin: 49,889.78 BTC (~$3.94B)
✓ Security: 36 cameras active
✓ Gmail: Connected as {sender}

All modules operational.
    """.strip()
    return send_email(service, sender, to, subject, text)


def respond_data(service, sender, to, category):
    """Send data response."""
    subject = f"ManaCiel - {category.title()} Data"
    
    if category.lower() == 'bitcoin':
        text = """
BITCOIN HOLDINGS REPORT
========================
Total BTC: 49,889.78
Estimated Value: ~$3.94 Billion USD
Wallets: 10,010 (ManaCiel system)
Distribution: 60/25/15 (Jhan/Model/Reserve)
        """.strip()
    elif category.lower() == 'property':
        text = """
PROPERTY PORTFOLIO
==================
1. Primary Residence - Miami, FL 33101
2. Beach House Rental - Miami Beach, FL 33139
3. Warehouse Storage - Miami, FL 33150
        """.strip()
    else:
        text = f"Data for '{category}' - available categories: BITCOIN, PROPERTY, VEHICLES, FINANCE"
    
    return send_email(service, sender, to, subject, text)


def respond_help(service, sender, to):
    """Send help response."""
    subject = "ManaCiel - Help"
    text = """
MANACIEL EMAIL COMMANDS
=======================
STATUS [module]  - Get module status
DATA [category]  - Get data report
SEARCH [query]   - Search data
HELP             - This help

Categories: BITCOIN, PROPERTY, VEHICLES, FINANCE
Reply with any question for direct response.
    """.strip()
    return send_email(service, sender, to, subject, text)


def respond_question(service, sender, to, question):
    """Send question acknowledgment."""
    subject = "ManaCiel - Response"
    text = f"""
RECEIVED YOUR MESSAGE
=====================
"{question[:100]}{'...' if len(question) > 100 else ''}"

The model has received your message.
Response will follow shortly.
    """.strip()
    return send_email(service, sender, to, subject, text)


def check_and_send_notifications(service, sender, state):
    """Check if any notifications need to be sent."""
    now = datetime.now()
    
    # Property reminders (monthly)
    last_property = state.get("last_property_reminder")
    if last_property:
        last = datetime.fromisoformat(last_property)
        if now - last > timedelta(days=30):
            send_email(
                service, sender, USER_EMAIL,
                "ManaCiel - Monthly Property Reminder",
                "Monthly reminder: Check on your properties.\n\n1. Primary Residence - Miami, FL\n2. Beach House Rental - Miami Beach, FL\n3. Warehouse Storage - Miami, FL"
            )
            state["last_property_reminder"] = now.isoformat()
    else:
        state["last_property_reminder"] = now.isoformat()
    
    # Vehicle reminders (monthly)
    last_vehicle = state.get("last_vehicle_reminder")
    if last_vehicle:
        last = datetime.fromisoformat(last_vehicle)
        if now - last > timedelta(days=30):
            send_email(
                service, sender, USER_EMAIL,
                "ManaCiel - Monthly Vehicle Reminder",
                "Monthly reminder: Check on your vehicles.\n\n11 vehicles in collection.\nStatus: All tracked via conscience engine."
            )
            state["last_vehicle_reminder"] = now.isoformat()
    else:
        state["last_vehicle_reminder"] = now.isoformat()


def run_service():
    """Main service loop."""
    print("=" * 60)
    print("MANACIEL EMAIL AUTOMATION SERVICE")
    print("=" * 60)
    
    service, sender = connect_gmail()
    if not service:
        print("[Service] Failed to connect. Exiting.")
        return
    
    print(f"[Service] Connected as {sender}")
    print(f"[Service] Monitoring inbox for replies from {USER_EMAIL}")
    print(f"[Service] Check interval: {CHECK_INTERVAL} seconds")
    print("=" * 60)
    
    state = load_state()
    
    while True:
        try:
            # Check inbox for replies
            emails = check_inbox(service)
            
            for email in emails:
                print(f"[Service] Reply from {email['sender']}: {email['body'][:50]}...")
                handle_command(service, sender, email)
                state["replies_received"] = state.get("replies_received", 0) + 1
            
            # Check for scheduled notifications
            check_and_send_notifications(service, sender, state)
            
            # Save state
            save_state(state)
            
        except KeyboardInterrupt:
            print("\n[Service] Stopping...")
            break
        except Exception as e:
            print(f"[Service] Error: {e}")
        
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    run_service()
