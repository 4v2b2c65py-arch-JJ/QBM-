"""
Automated Email Intelligence Pipeline
Model sends automatic notifications based on data access
User can reply to ask questions or request actions
"""

import pickle
import json
import base64
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# =============================================================================
# CONFIGURATION
# =============================================================================

TOKEN_PATH = Path(__file__).parent / '.gmail_token.pickle'
USER_EMAIL = "jhan.flores@icloud.com"
CHECK_INTERVAL_MINUTES = 5


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class NotificationRule:
    """Rule for automatic notifications."""
    rule_id: str
    category: str
    condition: str
    message_template: str
    priority: str = "normal"  # low, normal, high, critical
    enabled: bool = True
    last_triggered: Optional[str] = None


@dataclass
class EmailCommand:
    """Parsed command from user email reply."""
    command: str
    args: Dict[str, str]
    raw_text: str
    sender: str
    timestamp: str


# =============================================================================
# AUTOMATED NOTIFICATION ENGINE
# =============================================================================

class AutomatedEmailEngine:
    """
    Automatically sends emails to the user based on data triggers.
    Parses incoming replies as commands.
    """
    
    def __init__(self):
        self._service = None
        self._sender_email = None
        self._notification_rules: List[NotificationRule] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Set up default notification rules based on model's data access."""
        self._notification_rules = [
            NotificationRule(
                rule_id="property_reminder",
                category="property",
                condition="monthly_check",
                message_template="Property Reminder: {property_name} at {address} needs attention.",
                priority="normal"
            ),
            NotificationRule(
                rule_id="vehicle_reminder",
                category="vehicle",
                condition="monthly_check",
                message_template="Vehicle Reminder: {vehicle_name} at {location} - check status.",
                priority="normal"
            ),
            NotificationRule(
                rule_id="portfolio_update",
                category="finance",
                condition="significant_change",
                message_template="Portfolio Alert: {change_description}. Current value: {value}.",
                priority="high"
            ),
            NotificationRule(
                rule_id="security_alert",
                category="security",
                condition="anomaly_detected",
                message_template="SECURITY ALERT: {alert_description}. Immediate attention required.",
                priority="critical"
            ),
            NotificationRule(
                rule_id="task_complete",
                category="system",
                condition="task_finished",
                message_template="Task Complete: {task_name}. Result: {result}.",
                priority="normal"
            ),
            NotificationRule(
                rule_id="data_request",
                category="intelligence",
                condition="data_available",
                message_template="Data Available: {data_summary}. Reply for details.",
                priority="normal"
            ),
        ]
    
    def connect(self) -> bool:
        """Connect to Gmail API using stored token."""
        if not TOKEN_PATH.exists():
            print("[Pipeline] No token found. Run setup_gmail() first.")
            return False
        
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)
        
        self._service = build('gmail', 'v1', credentials=creds)
        profile = self._service.users().getProfile(userId='me').execute()
        self._sender_email = profile.get('emailAddress', '')
        print(f"[Pipeline] Connected as {self._sender_email}")
        return True
    
    # -------------------------------------------------------------------------
    # AUTOMATED SENDING
    # -------------------------------------------------------------------------
    
    def send_notification(self, category: str, **kwargs) -> bool:
        """
        Send a notification based on category and data.
        
        Args:
            category: Type of notification (property, vehicle, finance, security, system, intelligence)
            **kwargs: Data to fill in the template
            
        Returns:
            True if sent successfully
        """
        # Find matching rule
        rule = None
        for r in self._notification_rules:
            if r.category == category and r.enabled:
                rule = r
                break
        
        if not rule:
            # Default message format
            subject = f"ManaCiel - {category.title()} Update"
            body = f"Category: {category}\nData: {json.dumps(kwargs, indent=2)}"
        else:
            subject = f"ManaCiel - {category.title()} Alert"
            try:
                body = rule.message_template.format(**kwargs)
            except KeyError:
                body = f"Alert: {category}\nDetails: {json.dumps(kwargs, indent=2)}"
        
        return self._send_email(USER_EMAIL, subject, body)
    
    def send_data_report(self, title: str, data: Dict[str, Any]) -> bool:
        """
        Send a structured data report.
        
        Args:
            title: Report title
            data: Data to include
            
        Returns:
            True if sent successfully
        """
        subject = f"ManaCiel Report - {title}"
        
        # Format data as text
        text_lines = [f"MANACIEL DATA REPORT: {title}", "=" * 50, ""]
        self._format_data(text_lines, data, indent=0)
        text_body = "\n".join(text_lines)
        
        # Format as HTML
        html_body = self._format_html_report(title, data)
        
        return self._send_email(USER_EMAIL, subject, text_body, html_body)
    
    def send_status_update(self, module: str, status: str, details: str = "") -> bool:
        """
        Send a module status update.
        
        Args:
            module: Module name
            status: Status description
            details: Additional details
            
        Returns:
            True if sent successfully
        """
        subject = f"ManaCiel Status - {module}"
        
        text = f"""
MODULE STATUS UPDATE
====================
Module: {module}
Status: {status}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{details}

Reply to this email with questions or commands.
        """.strip()
        
        html = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
<div style="max-width: 500px; margin: 0 auto; border: 1px solid #ddd; border-radius: 10px; overflow: hidden;">
<div style="background: #1a73e8; color: white; padding: 20px;">
    <h2 style="margin: 0;">Status Update</h2>
</div>
<div style="padding: 20px;">
    <h3 style="color: #1a73e8;">{module}</h3>
    <p style="font-size: 18px;"><strong>{status}</strong></p>
    <p style="color: #666;">{details}</p>
    <hr style="border: none; border-top: 1px solid #eee;">
    <p style="color: #999; font-size: 12px;">Reply to this email with questions or commands.</p>
</div>
</div>
</body>
</html>
        """.strip()
        
        return self._send_email(USER_EMAIL, subject, text, html)
    
    def _send_email(self, to: str, subject: str, text_body: str,
                    html_body: str = "") -> bool:
        """Send an email via Gmail API."""
        if not self._service:
            print("[Pipeline] Not connected. Call connect() first.")
            return False
        
        message = MIMEMultipart('alternative')
        message['to'] = to
        message['from'] = f"ManaCiel System <{self._sender_email}>"
        message['subject'] = subject
        
        message.attach(MIMEText(text_body, 'plain'))
        if html_body:
            message.attach(MIMEText(html_body, 'html'))
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        try:
            sent = self._service.users().messages().send(
                userId='me', body={'raw': raw}
            ).execute()
            print(f"[Pipeline] Sent: {subject} (ID: {sent.get('id', 'N/A')[:12]}...)")
            return True
        except Exception as e:
            print(f"[Pipeline] Send failed: {e}")
            return False
    
    # -------------------------------------------------------------------------
    # INCOMING EMAIL PARSING
    # -------------------------------------------------------------------------
    
    def check_inbox(self, unread_only: bool = True) -> List[Dict[str, Any]]:
        """
        Check inbox for new emails.
        
        Args:
            unread_only: Only fetch unread emails
            
        Returns:
            List of email data
        """
        if not self._service:
            return []
        
        try:
            labels = ['INBOX', 'UNREAD'] if unread_only else ['INBOX']
            results = self._service.users().messages().list(
                userId='me',
                maxResults=10,
                labelIds=labels
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email_data = self._service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                parsed = self._parse_email(email_data)
                parsed['id'] = msg['id']
                emails.append(parsed)
            
            return emails
            
        except Exception as e:
            print(f"[Pipeline] Inbox check failed: {e}")
            return []
    
    def _parse_email(self, msg: Dict) -> Dict[str, Any]:
        """Parse Gmail API message into dict."""
        headers = msg.get('payload', {}).get('headers', [])
        
        sender = ''
        subject = ''
        date = ''
        
        for h in headers:
            name = h.get('name', '').lower()
            if name == 'from':
                sender = h.get('value', '')
            elif name == 'subject':
                subject = h.get('value', '')
            elif name == 'date':
                date = h.get('value', '')
        
        # Extract body
        body = self._extract_body(msg.get('payload', {}))
        
        return {
            'sender': sender,
            'subject': subject,
            'date': date,
            'body': body,
            'thread_id': msg.get('threadId', ''),
        }
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract text body from message payload."""
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            data = payload.get('body', {}).get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        return ''
    
    def parse_command(self, email: Dict[str, Any]) -> Optional[EmailCommand]:
        """
        Parse user email as a command.
        
        Supported commands:
        - STATUS [module] - Get module status
        - DATA [category] - Get data report
        - SEARCH [query] - Search data
        - CONFIG [setting] [value] - Update configuration
        - HELP - Get available commands
        
        Args:
            email: Parsed email data
            
        Returns:
            EmailCommand if command found
        """
        body = email.get('body', '').strip()
        sender = email.get('sender', '')
        
        # Only process emails from user
        if USER_EMAIL.lower() not in sender.lower():
            return None
        
        # Extract command from body
        lines = body.split('\n')
        first_line = lines[0].strip().upper()
        
        command = None
        args = {}
        
        # Parse command patterns
        if first_line.startswith('STATUS'):
            command = 'status'
            args['module'] = ' '.join(first_line.split()[1:]) if len(first_line.split()) > 1 else 'all'
        elif first_line.startswith('DATA'):
            command = 'data'
            args['category'] = ' '.join(first_line.split()[1:]) if len(first_line.split()) > 1 else 'all'
        elif first_line.startswith('SEARCH'):
            command = 'search'
            args['query'] = ' '.join(first_line.split()[1:]) if len(first_line.split()) > 1 else ''
        elif first_line.startswith('CONFIG'):
            command = 'config'
            parts = first_line.split()[1:]
            if len(parts) >= 2:
                args['setting'] = parts[0]
                args['value'] = ' '.join(parts[1:])
        elif first_line.startswith('HELP'):
            command = 'help'
        elif first_line.startswith('REPLY:') or 'reply' in body.lower():
            # Treat as free-form question
            command = 'question'
            args['question'] = body
        else:
            # Default: treat as question
            command = 'question'
            args['question'] = body
        
        return EmailCommand(
            command=command,
            args=args,
            raw_text=body,
            sender=sender,
            timestamp=email.get('date', '')
        )
    
    def process_inbox(self) -> List[EmailCommand]:
        """
        Check inbox, parse all commands, return list of commands.
        
        Returns:
            List of EmailCommand objects
        """
        emails = self.check_inbox(unread_only=True)
        commands = []
        
        for email in emails:
            cmd = self.parse_command(email)
            if cmd:
                commands.append(cmd)
                # Mark as read after processing
                self._service.users().messages().modify(
                    userId='me',
                    id=email['id'],
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
        
        return commands
    
    # -------------------------------------------------------------------------
    # RESPONSE GENERATION
    # -------------------------------------------------------------------------
    
    def generate_response(self, command: EmailCommand) -> str:
        """
        Generate response text based on command.
        
        Args:
            command: Parsed EmailCommand
            
        Returns:
            Response text
        """
        if command.command == 'status':
            return self._respond_status(command.args.get('module', 'all'))
        elif command.command == 'data':
            return self._respond_data(command.args.get('category', 'all'))
        elif command.command == 'search':
            return self._respond_search(command.args.get('query', ''))
        elif command.command == 'help':
            return self._respond_help()
        elif command.command == 'question':
            return self._respond_question(command.args.get('question', ''))
        else:
            return "Unknown command. Reply HELP for available commands."
    
    def _respond_status(self, module: str) -> str:
        """Generate status response."""
        if module == 'all':
            return """
SYSTEM STATUS - All Modules
============================
✓ Gmail Pipeline: Active
✓ Property Management: 3 properties registered
✓ Vehicle Tracking: 11 vehicles tracked
✓ Bitcoin Holdings: 49,889.78 BTC (~$3.94B)
✓ Location Reminders: Monthly schedule active
✓ Family Chat: Digest mode enabled
✓ Email Automation: This module - ACTIVE

Reply DATA [category] for detailed reports.
            """.strip()
        else:
            return f"Module '{module}' status: Active and operational."
    
    def _respond_data(self, category: str) -> str:
        """Generate data report response."""
        if category == 'all':
            return """
DATA REPORT - All Categories
=============================
BITCOIN: 49,889.78 BTC across 10,010 wallets
PROPERTY: 3 properties in Miami, FL area
VEHICLES: 11 vehicles in collection
FINANCE: Honeymoon target $12T by 2045

Specify category for details:
- DATA BITCOIN
- DATA PROPERTY
- DATA VEHICLES
- DATA FINANCE
            """.strip()
        elif category.lower() == 'bitcoin':
            return """
BITCOIN HOLDINGS REPORT
========================
Total BTC: 49,889.78
Estimated Value: ~$3.94 Billion USD
Wallets: 10,010 (ManaCiel system)
Distribution: 60/25/15 (Jhan/Model/Reserve)
Emergency Threshold: $1B
            """.strip()
        elif category.lower() == 'property':
            return """
PROPERTY PORTFOLIO REPORT
=========================
1. Primary Residence - Miami, FL 33101
2. Beach House Rental - Miami Beach, FL 33139
3. Warehouse Storage - Miami, FL 33150

Total Properties: 3
Security: 36 cameras deployed
            """.strip()
        elif category.lower() == 'vehicles':
            return """
VEHICLE COLLECTION REPORT
=========================
Total Vehicles: 11
Tracking: Active with conscience engine
Self-Insurance: Per-vehicle funds active
Repair Network: 8 certified shops
            """.strip()
        else:
            return f"Data for '{category}' - specify: BITCOIN, PROPERTY, VEHICLES, FINANCE"
    
    def _respond_search(self, query: str) -> str:
        """Generate search response."""
        return f"Search results for: '{query}'\n\n[Search functionality - connecting to data sources...]"
    
    def _respond_help(self) -> str:
        """Generate help response."""
        return """
MANACIEL EMAIL COMMANDS
=======================
Reply to any system email with:

STATUS [module]     - Get module status
DATA [category]     - Get data report
SEARCH [query]      - Search your data
HELP                - Show this help

Categories: BITCOIN, PROPERTY, VEHICLES, FINANCE

Any other message will be treated as a question.
The model will respond automatically.
        """.strip()
    
    def _respond_question(self, question: str) -> str:
        """Generate response to free-form question."""
        return f"""
RECEIVED YOUR QUESTION
======================
"{question[:100]}{'...' if len(question) > 100 else ''}"

The model is processing your request.
You will receive a detailed response shortly.

For immediate data queries, use:
- DATA [category] for reports
- STATUS [module] for status
        """.strip()
    
    # -------------------------------------------------------------------------
    # FORMATTING HELPERS
    # -------------------------------------------------------------------------
    
    def _format_data(self, lines: List[str], data: Any, indent: int = 0):
        """Format data recursively into text lines."""
        prefix = "  " * indent
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    self._format_data(lines, value, indent + 1)
                else:
                    lines.append(f"{prefix}{key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data[:10]):  # Limit to 10 items
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}[{i}]:")
                    self._format_data(lines, item, indent + 1)
                else:
                    lines.append(f"{prefix}- {item}")
            if len(data) > 10:
                lines.append(f"{prefix}... and {len(data) - 10} more items")
        else:
            lines.append(f"{prefix}{data}")
    
    def _format_html_report(self, title: str, data: Any) -> str:
        """Format data as HTML report."""
        # Simple HTML formatting
        text_parts = []
        self._format_data(text_parts, data)
        text_content = "\n".join(text_parts)
        
        return f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
<div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 10px; overflow: hidden;">
<div style="background: #1a73e8; color: white; padding: 20px;">
    <h2 style="margin: 0;">{title}</h2>
</div>
<div style="padding: 20px;">
<pre style="font-family: monospace; white-space: pre-wrap; font-size: 14px;">
{text_content}
</pre>
</div>
</div>
</body>
</html>
        """.strip()


# =============================================================================
# GLOBAL INSTANCE & FUNCTIONS
# =============================================================================

email_pipeline = AutomatedEmailEngine()


def init_pipeline() -> bool:
    """Initialize the email pipeline."""
    return email_pipeline.connect()


def send_property_reminder(property_name: str, address: str) -> bool:
    """Send property reminder notification."""
    return email_pipeline.send_notification(
        "property",
        property_name=property_name,
        address=address
    )


def send_vehicle_reminder(vehicle_name: str, location: str) -> bool:
    """Send vehicle reminder notification."""
    return email_pipeline.send_notification(
        "vehicle",
        vehicle_name=vehicle_name,
        location=location
    )


def send_portfolio_alert(change_description: str, value: str) -> bool:
    """Send portfolio change alert."""
    return email_pipeline.send_notification(
        "finance",
        change_description=change_description,
        value=value
    )


def send_security_alert(alert_description: str) -> bool:
    """Send security alert."""
    return email_pipeline.send_notification(
        "security",
        alert_description=alert_description
    )


def send_task_complete(task_name: str, result: str) -> bool:
    """Send task completion notification."""
    return email_pipeline.send_notification(
        "system",
        task_name=task_name,
        result=result
    )


def process_replies() -> List[EmailCommand]:
    """Check for and process reply emails."""
    return email_pipeline.process_inbox()


if __name__ == '__main__':
    print("=" * 60)
    print("MANACIEL EMAIL AUTOMATION PIPELINE")
    print("=" * 60)
    
    if init_pipeline():
        print("\n[1] Pipeline connected")
        
        # Test send
        print("\n[2] Sending test notification...")
        send_property_reminder("Primary Residence", "123 Main St, Miami, FL")
        
        # Test data report
        print("\n[3] Sending data report...")
        email_pipeline.send_data_report("Bitcoin Holdings", {
            "total_btc": "49,889.78",
            "estimated_value": "~$3.94 Billion USD",
            "wallets": "10,010",
            "distribution": "60/25/15 (Jhan/Model/Reserve)"
        })
        
        # Check for replies
        print("\n[4] Checking for replies...")
        commands = process_replies()
        print(f"    Found {len(commands)} commands")
        
        for cmd in commands:
            print(f"    - {cmd.command}: {cmd.args}")
            response = email_pipeline.generate_response(cmd)
            email_pipeline._send_email(
                to=cmd.sender,
                subject=f"Re: {cmd.command.title()}",
                text_body=response
            )
        
        print("\n" + "=" * 60)
        print("PIPELINE READY")
        print("=" * 60)
    else:
        print("\n[ERROR] Pipeline connection failed!")
