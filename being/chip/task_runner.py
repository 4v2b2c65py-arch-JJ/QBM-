#!/usr/bin/env python3
"""
ManaCiel Autonomous Task Runner
Simple version - runs tasks via Kilo and emails results
"""

import subprocess
import json
import time
from pathlib import Path
from datetime import datetime


CHIP_DIR = Path("/Users/jjmarte/delta-stream/qb_protocol/being/chip")
STATE_PATH = CHIP_DIR / ".task_runner_state.json"


# Tasks that run automatically
TASKS = [
    {
        "id": "email_processor",
        "name": "Process Email Commands",
        "interval": 300,  # 5 min
        "command": ["python3", str(CHIP_DIR / "email_service.py")],
    },
    {
        "id": "bitcoin_check",
        "name": "Bitcoin Price Check",
        "interval": 3600,  # 1 hour
        "command": [
            "kilo", "--prompt",
            "Check bitcoin price and update holdings value in being/chip/bitcoin.py. Email summary to jhan.flores@icloud.com if price changes >2%."
        ],
    },
    {
        "id": "daily_digest",
        "name": "Daily System Digest",
        "interval": 86400,  # 24 hours
        "command": [
            "kilo", "--prompt",
            "Generate daily digest of all systems: properties, vehicles, bitcoin, security, investments. Email to jhan.flores@icloud.com."
        ],
    },
]


def run_task(task):
    """Run a single task."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {task['name']}")
    try:
        result = subprocess.run(
            task["command"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(CHIP_DIR)
        )
        if result.returncode == 0:
            print(f"  ✓ Done")
            return True
        else:
            print(f"  ✗ {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"  ✗ {e}")
        return False


def main():
    """Main loop."""
    print("=" * 60)
    print("MANACIEL AUTONOMOUS TASK RUNNER")
    print("=" * 60)
    
    state = {}
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            state = json.load(f)
    
    while True:
        now = time.time()
        
        for task in TASKS:
            task_id = task["id"]
            last_run = state.get(task_id, 0)
            
            if now - last_run >= task["interval"]:
                run_task(task)
                state[task_id] = now
        
        # Save state
        with open(STATE_PATH, 'w') as f:
            json.dump(state, f)
        
        time.sleep(60)


if __name__ == '__main__':
    main()
