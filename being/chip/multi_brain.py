#!/usr/bin/env python3
"""
ManaCiel Multi-Brain AI Orchestrator
Integrates Kilo CLI (GPT/Claude/Gemini) with full codebase context
Cross-module intelligence with voice capability
"""

import subprocess
import json
import pickle
import base64
import os
import re
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build


# =============================================================================
# CONFIGURATION
# =============================================================================

CHIP_DIR = Path("/Users/jjmarte/delta-stream/qb_protocol/being/chip")
TOKEN_PATH = CHIP_DIR / ".gmail_token.pickle"
USER_EMAIL = "jhan.flores@icloud.com"
STATE_PATH = CHIP_DIR / ".multi_brain_state.json"
LOG_PATH = CHIP_DIR / "logs" / "multi_brain.log"

# Kilo CLI path
KILO = "kilo"

# Security constraints
BLOCKED_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\brm\s+-fr\b",
    r"\bdel\s+/[sfq]\b",
    r"\brmdir\s+/[sq]\b",
    r"\bunlink\b",
    r"\bshutil\.rmtree\b",
    r"\bos\.remove\b",
    r"\bos\.unlink\b",
    r"\btruncate\b",
    r"\bformat\b",
    r"\bmkfs\b",
    r"\bdd\s+if=.*\bof=/dev/\b",
]

# Available brains (models)
# Paid models require credits - free models work without credits
BRAINS = {
    "reasoning": "kilo/~anthropic/claude-sonnet-latest",      # Complex reasoning (paid)
    "fast": "kilo/~anthropic/claude-haiku-latest",            # Quick responses (paid)
    "deep": "kilo/~anthropic/claude-opus-latest",             # Deep analysis (paid)
    "vision": "kilo/~google/gemini-pro-latest",               # Vision/multimodal (paid)
    "coding": "kilo/~openai/gpt-latest",                      # Code generation (paid)
    "voice": "kilo/~openai/gpt-mini-latest",                  # Light tasks/fast (paid)
    "free": "kilo/kilo-auto/free",                            # Default free model
    "free_coding": "kilo/cohere/north-mini-code:free",        # Free coding model
    "free_fast": "kilo/dots-studio/dots-3-note-preview:free", # Free fast model
}

# Fallback chain - if paid model fails, try free alternatives
FALLBACK_CHAIN = {
    "reasoning": ["kilo/~anthropic/claude-sonnet-latest", "kilo/kilo-auto/free", "kilo/dots-studio/dots-3-note-preview:free"],
    "fast": ["kilo/~anthropic/claude-haiku-latest", "kilo/kilo-auto/free", "kilo/cohere/north-mini-code:free"],
    "deep": ["kilo/~anthropic/claude-opus-latest", "kilo/kilo-auto/free"],
    "vision": ["kilo/~google/gemini-pro-latest", "kilo/kilo-auto/free"],
    "coding": ["kilo/~openai/gpt-latest", "kilo/cohere/north-mini-code:free", "kilo/kilo-auto/free"],
    "voice": ["kilo/~openai/gpt-mini-latest", "kilo/kilo-auto/free"],
}


# =============================================================================
# MULTI-BRAIN ENGINE
# =============================================================================

class MultiBrainEngine:
    """
    Orchestrates multiple AI models through Kilo CLI.
    Each brain is selected based on task type.
    """
    
    def __init__(self):
        self._state = self._load_state()
        self._gmail_service = None
        self._sender_email = None
    
    def _load_state(self) -> dict:
        """Load orchestrator state."""
        if STATE_PATH.exists():
            with open(STATE_PATH) as f:
                return json.load(f)
        return {
            "started": datetime.now().isoformat(),
            "queries_processed": 0,
            "brains_used": {},
            "last_query": None,
        }
    
    def _save_state(self):
        """Save orchestrator state."""
        with open(STATE_PATH, 'w') as f:
            json.dump(self._state, f, indent=2)
    
    def _log(self, message: str):
        """Log message."""
        LOG_PATH.parent.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"[MultiBrain] {message}")
    
    # -------------------------------------------------------------------------
    # SECURITY
    # -------------------------------------------------------------------------
    
    def _check_safety(self, prompt: str) -> tuple:
        """
        Check if prompt contains dangerous commands.
        
        Returns:
            (is_safe, reason)
        """
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                return False, f"Blocked pattern: {pattern}"
        return True, "Safe"
    
    def _sanitize_output(self, output: str) -> str:
        """Sanitize AI output to prevent dangerous operations."""
        # Remove any file deletion commands from output
        lines = output.split('\n')
        safe_lines = []
        for line in lines:
            is_safe, _ = self._check_safety(line)
            if is_safe:
                safe_lines.append(line)
            else:
                safe_lines.append(f"# BLOCKED: {line}")
        return '\n'.join(safe_lines)
    
    # -------------------------------------------------------------------------
    # BRAIN SELECTION
    # -------------------------------------------------------------------------
    
    def _select_brain(self, task_type: str, use_free: bool = False) -> str:
        """
        Select the best brain for the task.
        
        Args:
            task_type: Type of task (reasoning, fast, deep, vision, coding, voice)
            use_free: Force use of free model
            
        Returns:
            Model identifier
        """
        if use_free:
            return BRAINS.get("free", "kilo/kilo-auto/free")
        
        # Check if user has credits for paid models
        auth_path = Path.home() / ".local" / "share" / "kilo" / "auth.json"
        if not auth_path.exists():
            return BRAINS.get("free", "kilo/kilo-auto/free")
        
        # Try paid model first, will fall back to free on error
        return BRAINS.get(task_type, BRAINS["reasoning"])
    
    # -------------------------------------------------------------------------
    # KILO CLI INTEGRATION
    # -------------------------------------------------------------------------
    
    def query_brain(self, prompt: str, brain: str = "reasoning",
                    context_files: list = None, max_output: int = 2000) -> str:
        """
        Query a specific brain via Kilo CLI.
        
        Args:
            prompt: Question or instruction
            brain: Brain type to use
            context_files: Files to include as context
            max_output: Max output length
            
        Returns:
            AI response
        """
        # Safety check
        is_safe, reason = self._check_safety(prompt)
        if not is_safe:
            self._log(f"BLOCKED: {reason}")
            return f"Request blocked for security: {reason}"
        
        model = self._select_brain(brain)
        
        # Build Kilo command
        cmd = [
            KILO, "run",
            "--model", model,
            "--format", "default",
            "--dir", str(CHIP_DIR),
        ]
        
        # Add context files
        if context_files:
            for f in context_files:
                cmd.extend(["--file", str(f)])
        
        # Add the prompt
        cmd.append(prompt)
        
        self._log(f"Querying {brain} ({model})...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(CHIP_DIR)
            )
            
            output = result.stdout.strip()
            
            # Update state
            self._state["queries_processed"] += 1
            self._state["brains_used"][brain] = self._state["brains_used"].get(brain, 0) + 1
            self._state["last_query"] = datetime.now().isoformat()
            self._save_state()
            
            # Sanitize output
            output = self._sanitize_output(output)
            
            if len(output) > max_output:
                output = output[:max_output] + "\n... [truncated]"
            
            return output
            
        except subprocess.TimeoutExpired:
            self._log(f"Timeout querying {brain}")
            return "AI response timed out. Try a simpler query."
        except Exception as e:
            self._log(f"Error querying {brain}: {e}")
            return f"AI Error: {e}"
    
    def query_multi_brain(self, prompt: str, brains: list = None) -> dict:
        """
        Query multiple brains and combine responses.
        
        Args:
            prompt: Question or instruction
            brains: List of brain types to query
            
        Returns:
            Dict of brain -> response
        """
        if brains is None:
            brains = ["reasoning", "fast"]
        
        responses = {}
        for brain in brains:
            response = self.query_brain(prompt, brain=brain)
            responses[brain] = response
        
        return responses
    
    # -------------------------------------------------------------------------
    # CODEBASE CONTEXT
    # -------------------------------------------------------------------------
    
    def get_codebase_context(self) -> str:
        """Get summary of entire codebase for context."""
        context = []
        
        # Scan chip modules
        for py_file in sorted(CHIP_DIR.glob("*.py")):
            if py_file.name.startswith('_'):
                continue
            with open(py_file, 'r') as f:
                lines = f.readlines()
                # Get first few lines for context
                preview = ''.join(lines[:20])
                context.append(f"\n=== {py_file.name} ===\n{preview}")
        
        return '\n'.join(context[:10])  # Limit context size
    
    def build_context_prompt(self, user_query: str) -> str:
        """
        Build a full context prompt with codebase knowledge.
        
        Args:
            user_query: User's question
            
        Returns:
            Full prompt with context
        """
        context = f"""You are ManaCiel AI, an intelligent system managing Jhan's entire portfolio and operations.

=== JHAN'S PROFILE ===
Name: JHAN JHONNIEL FLORES MARTE
Email: jhan.flores@icloud.com
Bitcoin: 49,889.78 BTC (~$3.94B USD)
Properties: 3 in Miami, FL
Vehicles: 11 in collection
Growth Target: $12 Trillion by 2045

=== AVAILABLE MODULES ===
- bitcoin.py: BTC holdings, identity protection, anti-theft, KYC
- property_security.py: 36 cameras, 3 properties, emergency detection
- vehicle_collection.py: 11 vehicles, conscience engine
- automated_trading.py: Multi-broker trading, DRS/DSPP
- direct_investment.py: Direct stock purchases, dividend tracking
- property_rental.py: Rental management, cleaning/market APIs
- family_chat.py: Model-to-Jhan communication
- location_reminder.py: Asset tracking, GPS integration
- security_camera.py: Camera placement optimization
- advanced_finance.py: Tax optimization, captive insurance
- threat_recon.py: Threat analysis and reconciliation
- net_worth.py: Net worth calculation and governance
- email_pipeline.py: Automated email responses
- gmail_oauth.py: Gmail API integration

=== SECURITY CONSTRAINTS ===
- CANNOT delete any files
- CANNOT run destructive commands
- CANNOT access systems outside being/chip/
- All actions are logged and auditable

=== USER QUERY ===
{user_query}

=== INSTRUCTIONS ===
1. Use the appropriate module(s) to answer
2. If data is needed, reference the correct module
3. Provide specific numbers and actionable insights
4. Keep response concise but complete
5. If you need to run code, specify which module and function
"""
        return context
    
    # -------------------------------------------------------------------------
    # EMAIL INTEGRATION
    # -------------------------------------------------------------------------
    
    def connect_gmail(self):
        """Connect to Gmail API."""
        if not TOKEN_PATH.exists():
            self._log("No Gmail token found")
            return False
        
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)
        
        self._gmail_service = build('gmail', 'v1', credentials=creds)
        profile = self._gmail_service.users().getProfile(userId='me').execute()
        self._sender_email = profile.get('emailAddress', '')
        self._log(f"Gmail connected: {self._sender_email}")
        return True
    
    def send_email(self, to: str, subject: str, text_body: str,
                   html_body: str = "") -> bool:
        """Send email via Gmail API."""
        if not self._gmail_service:
            return False
        
        message = MIMEMultipart('alternative')
        message['to'] = to
        message['from'] = f"ManaCiel AI <{self._sender_email}>"
        message['subject'] = subject
        
        message.attach(MIMEText(text_body, 'plain'))
        if html_body:
            message.attach(MIMEText(html_body, 'html'))
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        try:
            sent = self._gmail_service.users().messages().send(
                userId='me', body={'raw': raw}
            ).execute()
            self._log(f"Email sent: {subject[:40]}")
            return True
        except Exception as e:
            self._log(f"Send error: {e}")
            return False
    
    def check_inbox(self) -> list:
        """Check for new emails from user."""
        if not self._gmail_service:
            return []
        
        results = self._gmail_service.users().messages().list(
            userId='me', maxResults=10, labelIds=['INBOX']
        ).execute()
        
        emails = []
        for msg in results.get('messages', []):
            data = self._gmail_service.users().messages().get(
                userId='me', id=msg['id'], format='full'
            ).execute()
            
            headers = data.get('payload', {}).get('headers', [])
            sender = subject = ''
            
            for h in headers:
                if h['name'].lower() == 'from':
                    sender = h['value']
                elif h['name'].lower() == 'subject':
                    subject = h['value']
            
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
        
        return emails
    
    # -------------------------------------------------------------------------
    # AUTONOMOUS PROCESSING
    # -------------------------------------------------------------------------
    
    def process_email(self, email: dict) -> str:
        """
        Process an email using the appropriate brain.
        
        Args:
            email: Email data dict
            
        Returns:
            Response text
        """
        body = email.get('body', '')
        subject = email.get('subject', '')
        
        # Determine which brain to use
        brain = "reasoning"  # default
        
        body_upper = body.upper()
        if "STATUS" in body_upper:
            brain = "fast"
        elif "ANALYZE" in body_upper or "DEEP" in brain:
            brain = "deep"
        elif "CODE" in body_upper or "FIX" in body_upper:
            brain = "coding"
        elif "IMAGE" in body_upper or "PHOTO" in body_upper:
            brain = "vision"
        elif len(body) < 50:
            brain = "fast"
        
        # Build context-aware prompt
        prompt = self.build_context_prompt(body)
        
        # Query the brain
        response = self.query_brain(prompt, brain=brain)
        
        return response
    
    def run_autonomous_loop(self):
        """
        Main autonomous loop - checks email and responds.
        """
        self._log("Starting autonomous loop...")
        
        if not self.connect_gmail():
            self._log("Cannot connect to Gmail")
            return
        
        self._log(f"Monitoring inbox for {USER_EMAIL}")
        
        while True:
            try:
                emails = self.check_inbox()
                
                for email in emails:
                    self._log(f"Processing: {email['subject'][:40]}")
                    
                    # Process with AI
                    response = self.process_email(email)
                    
                    # Send response
                    self.send_email(
                        to=email['sender'],
                        subject=f"Re: {email['subject']}",
                        text_body=response
                    )
                
            except KeyboardInterrupt:
                self._log("Stopping autonomous loop...")
                break
            except Exception as e:
                self._log(f"Loop error: {e}")
            
            import time
            time.sleep(300)  # 5 minutes


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    engine = MultiBrainEngine()
    engine.run_autonomous_loop()
