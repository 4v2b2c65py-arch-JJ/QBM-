#!/usr/bin/env python3
"""
ManaCiel Daily Digest
Batches all notifications into ONE email per day
Prevents email spam while keeping user informed
"""

import pickle
import base64
import json
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build


TOKEN_PATH = Path("/Users/jjmarte/delta-stream/qb_protocol/being/chip/.gmail_token.pickle")
USER_EMAIL = "jhan.flores@icloud.com"
STATE_FILE = Path("/Users/jjmarte/delta-stream/qb_protocol/being/chip/.daily_digest_state.json")


def load_pending_notifications() -> list:
    """Load pending notifications from state."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f).get("pending", [])
    return []


def save_pending_notifications(notifications: list):
    """Save pending notifications."""
    with open(STATE_FILE, 'w') as f:
        json.dump({"pending": notifications}, f)


def add_notification(message: str, priority: str = "normal"):
    """Add a notification to be sent in next digest."""
    notifications = load_pending_notifications()
    notifications.append({
        "message": message,
        "priority": priority,
        "timestamp": datetime.now().isoformat(),
    })
    save_pending_notifications(notifications)


def send_digest():
    """Send batched digest email."""
    notifications = load_pending_notifications()
    
    if not notifications:
        return
    
    # Connect to Gmail
    with open(TOKEN_PATH, 'rb') as f:
        creds = pickle.load(f)
    
    service = build('gmail', 'v1', credentials=creds)
    profile = service.users().getProfile(userId='me').execute()
    sender_email = profile.get('emailAddress', '')
    
    # Build digest
    critical = [n for n in notifications if n["priority"] == "critical"]
    high = [n for n in notifications if n["priority"] == "high"]
    normal = [n for n in notifications if n["priority"] == "normal"]
    
    text = f"""
MANACIEL DAILY DIGEST
=====================
Date: {datetime.now().strftime('%B %d, %Y')}
Time: {datetime.now().strftime('%I:%M %p')}

CRITICAL ({len(critical)}):
""" + "\n".join(f"  ⚠ {n['message']}" for n in critical) + """

HIGH PRIORITY ({len(high)}):
""" + "\n".join(f"  • {n['message']}" for n in high) + """

NORMAL ({len(normal)}):
""" + "\n".join(f"  - {n['message']}" for n in normal) + f"""

---
Total: {len(notifications)} notifications
Date: {datetime.now().strftime('%B %d, %Y %I:%M %p')}
Reply STATUS for details on any item.
"""
    
    html = f"""
<html>
<body style="font-family: Arial; padding: 20px;">
<div style="max-width: 550px; margin: 0 auto;">
<h2 style="color: #1a73e8;">ManaCiel Daily Digest</h2>
<p style="color: #666;">{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
"""
    
    if critical:
        html += f"""
<div style="background: #ffebee; padding: 15px; border-radius: 8px; margin: 15px 0;">
<h3 style="color: #c62828; margin: 0;">⚠ Critical ({len(critical)})</h3>
<ul style="color: #c62828;">
""" + "\n".join(f"<li>{n['message']}</li>" for n in critical) + """
</ul>
</div>
"""
    
    if high:
        html += f"""
<div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin: 15px 0;">
<h3 style="color: #e65100; margin: 0;">• High Priority ({len(high)})</h3>
<ul style="color: #e65100;">
""" + "\n".join(f"<li>{n['message']}</li>" for n in high) + """
</ul>
</div>
"""
    
    if normal:
        html += f"""
<div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0;">
<h3 style="color: #1565c0; margin: 0;">- Normal ({len(normal)})</h3>
<ul style="color: #1565c0;">
""" + "\n".join(f"<li>{n['message']}</li>" for n in normal) + """
</ul>
</div>
"""
    
    html += f"""
<p style="color: #999; font-size: 12px; margin-top: 30px;">
Total: {len(notifications)} notifications<br>
Reply STATUS for details on any item.
</p>
</div>
</body>
</html>
"""
    
    # Send
    message = MIMEMultipart('alternative')
    message['to'] = USER_EMAIL
    message['from'] = f"ManaCiel <{sender_email}>"
    message['subject'] = f"ManaCiel Daily Digest - {len(notifications)} items"
    
    message.attach(MIMEText(text, 'plain'))
    message.attach(MIMEText(html, 'html'))
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    service.users().messages().send(userId='me', body={'raw': raw}).execute()
    
    # Clear pending
    save_pending_notifications([])
    
    print(f"✓ Digest sent: {len(notifications)} notifications")


if __name__ == '__main__':
    send_digest()
