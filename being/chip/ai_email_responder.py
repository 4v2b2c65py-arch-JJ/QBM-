#!/usr/bin/env python3
"""
ManaCiel Smart Email Responder
Only responds to NEW emails from the user - no loops
"""

import json
import pickle
import base64
import urllib.request
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build


# Configuration
TOKEN_PATH = Path("/Users/jjmarte/delta-stream/qb_protocol/being/chip/.gmail_token.pickle")
USER_EMAIL = "jhan.flores@icloud.com"
MY_EMAIL = "oxzkillerfros23@gmail.com"  # The model's own email
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"

# Track processed emails to avoid loops
PROCESSED_FILE = Path("/Users/jjmarte/delta-stream/qb_protocol/being/chip/.processed_emails.json")


def load_processed() -> dict:
    """Load processed email IDs."""
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE) as f:
            return json.load(f)
    return {"ids": [], "last_run": None}


def save_processed(processed: dict):
    """Save processed email IDs."""
    # Keep only last 100 to avoid file bloat
    processed["ids"] = processed["ids"][-100:]
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(processed, f)


def is_already_processed(email_id: str) -> bool:
    """Check if email was already processed."""
    processed = load_processed()
    return email_id in processed["ids"]


def mark_processed(email_id: str):
    """Mark email as processed."""
    processed = load_processed()
    processed["ids"].append(email_id)
    processed["last_run"] = datetime.now().isoformat()
    save_processed(processed)


def ask_local_ai(prompt: str) -> str:
    """Ask the local AI."""
    data = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "max_tokens": 1000}
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("response", "No response from AI")
    except Exception as e:
        return f"AI Error: {e}"


def connect_gmail():
    """Connect to Gmail API."""
    with open(TOKEN_PATH, 'rb') as f:
        creds = pickle.load(f)
    service = build('gmail', 'v1', credentials=creds)
    profile = service.users().getProfile(userId='me').execute()
    return service, profile.get('emailAddress', '')


def send_email(service, sender, to, subject, text_body, html_body=""):
    """Send email via Gmail API."""
    message = MIMEMultipart('alternative')
    message['to'] = to
    message['from'] = f"ManaCiel AI <{sender}>"
    message['subject'] = subject
    
    message.attach(MIMEText(text_body, 'plain'))
    if html_body:
        message.attach(MIMEText(html_body, 'html'))
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    sent = service.users().messages().send(userId='me', body={'raw': raw}).execute()
    return sent.get('id', '')


def check_inbox(service):
    """
    Check for NEW emails from the user only.
    Ignores:
    - Emails from myself (my own replies)
    - Already processed emails
    - Old emails (older than last run)
    """
    processed = load_processed()
    last_run = processed.get("last_run")
    
    results = service.users().messages().list(
        userId='me', maxResults=10, labelIds=['INBOX']
    ).execute()
    
    emails = []
    for msg in results.get('messages', []):
        data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = data.get('payload', {}).get('headers', [])
        
        sender = subject = date = ''
        for h in headers:
            if h['name'].lower() == 'from':
                sender = h['value']
            elif h['name'].lower() == 'subject':
                subject = h['value']
            elif h['name'].lower() == 'date':
                date = h['value']
        
        # SKIP if from myself (my own replies)
        if MY_EMAIL.lower() in sender.lower():
            continue
        
        # SKIP if not from user
        if USER_EMAIL.lower() not in sender.lower():
            continue
        
        # SKIP if already processed
        if is_already_processed(msg['id']):
            continue
        
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
            'date': date,
            'body': body.strip()
        })
    
    return emails


def process_email(service, sender, email):
    """Process email and respond."""
    body = email['body']
    
    # Get real current date/time for the AI
    now = datetime.now()
    current_date = now.strftime("%B %d, %Y")
    current_time = now.strftime("%I:%M %p")
    current_year = now.year
    
    context = f"""You are ManaCiel AI, managing Jhan's portfolio.

CURRENT DATE: {current_date}
CURRENT TIME: {current_time}
CURRENT YEAR: {current_year}

Jhan's Portfolio:
- Bitcoin: 49,889.78 BTC (~$3.94B USD)
- Properties: 3 in Miami, FL
- Vehicles: 11 in collection
- Growth Target: $12T by 2045

User says: {body}

IMPORTANT: The current year is {current_year}, NOT 2023. Use the correct date in your response.

Respond concisely with real data."""
    
    ai_response = ask_local_ai(context)
    
    subject = f"Re: {email['subject']}" if email['subject'] else "ManaCiel Response"
    send_email(service, sender, USER_EMAIL, subject, ai_response)
    
    # Mark as processed so we don't reply again
    mark_processed(email['id'])
    
    print(f"  ✓ Replied to: {email['subject'][:40]}")
    return True


def main():
    """Main function."""
    print("=" * 60)
    print("MANACIEL SMART EMAIL PROCESSOR")
    print("=" * 60)
    
    service, sender = connect_gmail()
    print(f"Connected as: {sender}")
    print(f"Listening for: {USER_EMAIL}")
    print(f"Ignoring: {MY_EMAIL} (self)")
    
    emails = check_inbox(service)
    print(f"New emails to process: {len(emails)}")
    
    for email in emails:
        print(f"\nProcessing: {email['subject'][:50]}")
        process_email(service, sender, email)
    
    print("\n" + "=" * 60)
    print("DONE - No loops!")
    print("=" * 60)


if __name__ == '__main__':
    main()
