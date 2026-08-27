#!/usr/bin/env python3
"""
ManaCiel Autonomous AI Orchestrator
Runs Kilo AI to handle tasks automatically without user prompting
"""

import subprocess
import json
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


# Configuration
CHIP_DIR = Path("/Users/jjmarte/delta-stream/qb_protocol/being/chip")
LOG_DIR = CHIP_DIR / "logs"
STATE_PATH = CHIP_DIR / ".orchestrator_state.json"
KILO_PATH = "/usr/local/bin/kilo"  # Adjust if needed


# =============================================================================
# TASK DEFINITIONS - What the AI does automatically
# =============================================================================

AUTONOMOUS_TASKS = [
    {
        "id": "bitcoin_monitor",
        "name": "Bitcoin Holdings Monitor",
        "schedule": "hourly",
        "prompt": "Check bitcoin holdings in being/chip/bitcoin.py. Get current BTC price, calculate total USD value, check if any wallets need attention. Send summary to jhan.flores@icloud.com if significant change.",
        "enabled": True,
    },
    {
        "id": "property_check",
        "name": "Property Status Check",
        "schedule": "daily",
        "prompt": "Review property data in being/chip/property_security.py and being/chip/property_rental.py. Check for any issues, maintenance needs, or status changes. Send daily digest to jhan.flores@icloud.com.",
        "enabled": True,
    },
    {
        "id": "vehicle_status",
        "name": "Vehicle Collection Status",
        "schedule": "daily",
        "prompt": "Check vehicle collection in being/chip/vehicle_collection.py. Review conscience engine status, insurance funds, maintenance schedule. Send status to jhan.flores@icloud.com.",
        "enabled": True,
    },
    {
        "id": "portfolio_review",
        "name": "Investment Portfolio Review",
        "schedule": "daily",
        "prompt": "Review direct investments in being/chip/direct_investment.py and automated trading in being/chip/automated_trading.py. Check dividend status, DRIP status, any actions needed. Send report to jhan.flores@icloud.com.",
        "enabled": True,
    },
    {
        "id": "security_scan",
        "name": "Security System Scan",
        "schedule": "hourly",
        "prompt": "Check security status in being/chip/property_security.py and being/chip/security_camera.py. Verify all cameras online, no breaches detected. Alert jhan.flores@icloud.com if any issues.",
        "enabled": True,
    },
    {
        "id": "email_responder",
        "name": "Email Command Processor",
        "interval": 300,  # 5 minutes
        "prompt": "Check Gmail inbox for emails from jhan.flores@icloud.com. Parse any commands (STATUS, DATA, SEARCH, HELP). Execute the command using the appropriate being/chip module. Send response back. Use being/chip/email_service.py for email functions.",
        "enabled": True,
    },
    {
        "id": "family_chat",
        "name": "Family Chat Digest",
        "schedule": "daily",
        "prompt": "Check family chat in being/chip/family_chat.py. Generate daily digest of messages, pending items, urgent communications. Send to jhan.flores@icloud.com.",
        "enabled": True,
    },
    {
        "id": "location_reminders",
        "name": "Location Reminder Check",
        "schedule": "weekly",
        "prompt": "Check location reminders in being/chip/location_reminder.py. Generate reminders for property visits, vehicle checks. Send to jhan.flores@icloud.com.",
        "enabled": True,
    },
    {
        "id": "threat_analysis",
        "name": "Threat Recon Scan",
        "schedule": "daily",
        "prompt": "Run threat analysis from being/chip/threat_recon.py. Check for any security threats, anomalies, or concerns. Send report to jhan.flores@icloud.com.",
        "enabled": True,
    },
    {
        "id": "net_worth_update",
        "name": "Net Worth Calculation",
        "schedule": "daily",
        "prompt": "Calculate total net worth using being/chip/net_worth.py. Include BTC, properties, vehicles, investments. Track against honeymoon growth targets. Send update to jhan.flores@icloud.com.",
        "enabled": True,
    },
]


# =============================================================================
# ORCHESTRATOR
# =============================================================================

class AutonomousOrchestrator:
    """Manages and runs autonomous AI tasks."""
    
    def __init__(self):
        self.tasks = AUTONOMOUS_TASKS
        self.state = self._load_state()
        LOG_DIR.mkdir(exist_ok=True)
    
    def _load_state(self) -> Dict:
        """Load orchestrator state."""
        if STATE_PATH.exists():
            with open(STATE_PATH, 'r') as f:
                return json.load(f)
        return {
            "started": datetime.now().isoformat(),
            "tasks_run": 0,
            "last_runs": {},
            "errors": []
        }
    
    def _save_state(self):
        """Save orchestrator state."""
        with open(STATE_PATH, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def run_kilo_task(self, task: Dict) -> bool:
        """
        Run a task using Kilo AI.
        
        This invokes Kilo with the task prompt and lets it execute
        using all available tools and codebase knowledge.
        """
        task_id = task["id"]
        prompt = task["prompt"]
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Running: {task['name']}")
        
        try:
            # Build Kilo command
            # Kilo will use its tools to execute the prompt
            cmd = [
                "kilo",
                "--prompt", prompt,
                "--workdir", str(CHIP_DIR),
                "--output", "json"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout
            )
            
            if result.returncode == 0:
                self.state["tasks_run"] += 1
                self.state["last_runs"][task_id] = datetime.now().isoformat()
                print(f"  ✓ {task['name']} completed")
                return True
            else:
                error = result.stderr or result.stdout
                self.state["errors"].append({
                    "task": task_id,
                    "error": error[:500],
                    "time": datetime.now().isoformat()
                })
                print(f"  ✗ {task['name']} failed: {error[:100]}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"  ⏱ {task['name']} timed out")
            return False
        except Exception as e:
            print(f"  ✗ {task['name']} error: {e}")
            return False
    
    def check_and_run_tasks(self):
        """Check which tasks need to run and execute them."""
        now = datetime.now()
        
        for task in self.tasks:
            if not task["enabled"]:
                continue
            
            task_id = task["id"]
            last_run = self.state["last_runs"].get(task_id)
            
            should_run = False
            
            if task.get("interval"):
                # Interval-based (seconds)
                if last_run:
                    last = datetime.fromisoformat(last_run)
                    if (now - last).total_seconds() >= task["interval"]:
                        should_run = True
                else:
                    should_run = True
                    
            elif task.get("schedule"):
                # Schedule-based
                if task["schedule"] == "hourly":
                    if last_run:
                        last = datetime.fromisoformat(last_run)
                        if (now - last).total_seconds() >= 3600:
                            should_run = True
                    else:
                        should_run = True
                        
                elif task["schedule"] == "daily":
                    if last_run:
                        last = datetime.fromisoformat(last_run)
                        if (now - last).total_seconds() >= 86400:
                            should_run = True
                    else:
                        should_run = True
                        
                elif task["schedule"] == "weekly":
                    if last_run:
                        last = datetime.fromisoformat(last_run)
                        if (now - last).total_seconds() >= 604800:
                            should_run = True
                    else:
                        should_run = True
            
            if should_run:
                self.run_kilo_task(task)
                self._save_state()
    
    def run_loop(self):
        """Main orchestrator loop."""
        print("=" * 60)
        print("MANACIEL AUTONOMOUS AI ORCHESTRATOR")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tasks: {len([t for t in self.tasks if t['enabled']])}")
        print(f"Check interval: 60 seconds")
        print("=" * 60)
        
        while True:
            try:
                self.check_and_run_tasks()
            except KeyboardInterrupt:
                print("\n[Orchestrator] Stopping...")
                break
            except Exception as e:
                print(f"[Orchestrator] Error: {e}")
            
            time.sleep(60)  # Check every minute


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    orchestrator = AutonomousOrchestrator()
    orchestrator.run_loop()
