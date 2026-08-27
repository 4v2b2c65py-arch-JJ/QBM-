#!/usr/bin/env python3
"""
ManaCiel Service Manager
Installs, starts, stops, and monitors background services
"""

import os
import sys
import subprocess
import plistlib
from pathlib import Path
from datetime import datetime


# Configuration
CHIP_DIR = Path(__file__).parent
LOG_DIR = CHIP_DIR / "logs"
LAUNCHD_DIR = Path.home() / "Library" / "LaunchAgents"
PLIST_FILE = CHIP_DIR / "com.manaciel.email-service.plist"
LAUNCHD_PLIST = LAUNCHD_DIR / "com.manaciel.email-service.plist"


def setup():
    """Initial setup - create log directory, install launchd service."""
    print("=" * 60)
    print("MANACIEL SERVICE MANAGER")
    print("=" * 60)
    
    # Create logs directory
    LOG_DIR.mkdir(exist_ok=True)
    print(f"[✓] Logs directory: {LOG_DIR}")
    
    # Install launchd service
    install_launchd()
    
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)


def install_launchd():
    """Install launchd plist for auto-start on boot."""
    LAUNCHD_DIR.mkdir(exist_ok=True)
    
    plist_content = {
        "Label": "com.manaciel.email-service",
        "ProgramArguments": [
            str(CHIP_DIR / ".venv" / "bin" / "python3"),
            str(CHIP_DIR / "email_service.py")
        ],
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(LOG_DIR / "email_service.out"),
        "StandardErrorPath": str(LOG_DIR / "email_service.err"),
        "WorkingDirectory": str(CHIP_DIR),
        "EnvironmentVariables": {
            "PATH": "/usr/local/bin:/usr/bin:/bin"
        }
    }
    
    with open(LAUNCHD_PLIST, 'wb') as f:
        plistlib.dump(plist_content, f)
    
    print(f"[✓] Launchd plist installed: {LAUNCHD_PLIST}")
    
    # Load the service
    subprocess.run(["launchctl", "unload", str(LAUNCHD_PLIST)], capture_output=True)
    result = subprocess.run(["launchctl", "load", str(LAUNCHD_PLIST)], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("[✓] Service loaded - will start on boot")
    else:
        print(f"[!] Launchd load: {result.stderr}")


def start():
    """Start the email service."""
    print("Starting ManaCiel email service...")
    result = subprocess.run(
        ["launchctl", "start", "com.manaciel.email-service"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("[✓] Service started")
    else:
        print(f"[!] {result.stderr}")


def stop():
    """Stop the email service."""
    print("Stopping ManaCiel email service...")
    result = subprocess.run(
        ["launchctl", "stop", "com.manaciel.email-service"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("[✓] Service stopped")
    else:
        print(f"[!] {result.stderr}")


def status():
    """Check service status."""
    print("=" * 60)
    print("MANACIEL SERVICE STATUS")
    print("=" * 60)
    
    result = subprocess.run(
        ["launchctl", "list", "|", "grep", "manaciel"],
        capture_output=True, text=True, shell=True
    )
    
    if result.stdout:
        print(f"\n[✓] Service found:\n{result.stdout}")
    else:
        print("\n[✗] Service not running")
    
    # Check logs
    log_file = LOG_DIR / "email_service.out"
    if log_file.exists():
        print(f"\n[Log - {log_file.stat().st_size} bytes]")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print(f"  {line.strip()}")
    
    # Check state
    state_file = CHIP_DIR / ".email_service_state.json"
    if state_file.exists():
        import json
        with open(state_file, 'r') as f:
            state = json.load(f)
        print(f"\n[State]")
        print(f"  Started: {state.get('started', 'N/A')}")
        print(f"  Last check: {state.get('last_check', 'N/A')}")
        print(f"  Emails sent: {state.get('emails_sent', 0)}")
        print(f"  Replies received: {state.get('replies_received', 0)}")


def restart():
    """Restart the service."""
    stop()
    import time
    time.sleep(2)
    start()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'setup':
            setup()
        elif cmd == 'start':
            start()
        elif cmd == 'stop':
            stop()
        elif cmd == 'restart':
            restart()
        elif cmd == 'status':
            status()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python3 service_manager.py [setup|start|stop|restart|status]")
    else:
        setup()
