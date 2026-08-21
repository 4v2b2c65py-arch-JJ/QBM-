#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: CLI

Commands:
  run            Launch the native being service (foreground loop).
  status         Print aggregated being status as JSON.
  install        Install the launchd native service (com.being.omega.prime).
  uninstall      Remove the launchd native service.
  start|stop|restart  Control the installed launchd service.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import plistlib
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

LABEL = "com.being.omega.prime"
LOG_DIR = Path.home() / "Library" / "Logs"
LAUNCHAGENTS = Path.home() / "Library" / "LaunchAgents"
PLIST_PATH = LAUNCHAGENTS / f"{LABEL}.plist"

_DISABLED = {"0", "false", "no", "off", ""}

_ROOT = Path(__file__).resolve().parent.parent
_VENV_PY = _ROOT / ".venv" / "bin" / "python3"
_RUN_SCRIPT = _ROOT / "being" / "run_being.py"


def _gui_domain() -> str:
    return f"gui/{os.getuid()}"


def _run(argv: Optional[List[str]] = None) -> int:
    from qb_protocol.being.being import being

    parser = argparse.ArgumentParser(
        prog="qb_protocol.being run", description="Run the BEING _ OMEGA + PRIM E native service."
    )
    parser.add_argument("--cycles", type=int, default=0, help="Run N cycles then exit (0 = run forever).")
    parser.add_argument("--cycle-interval", type=float,
                        default=float(os.environ.get("BEING_CYCLE_INTERVAL", 1.0)))
    parser.add_argument("--work-timeout", type=float,
                        default=float(os.environ.get("BEING_WORK_TIMEOUT", 25.0)))
    parser.add_argument("--autonomy", action=argparse.BooleanOptionalAction,
                        default=os.environ.get("BEING_AUTONOMY", "1") not in _DISABLED,
                        help="Enable autonomous self-generation pulse (default on; "
                             "set BEING_AUTONOMY=0 for user-input-only mode).")
    args = parser.parse_args(argv)

    being.cycle_interval = args.cycle_interval
    being.work_timeout = args.work_timeout
    # propagate to env so BeingOmegaPrime.autonomy_enabled() (read each cycle)
    # honours a runtime / plist toggle.
    os.environ["BEING_AUTONOMY"] = "1" if args.autonomy else "0"
    os.environ.setdefault("BEING_CYCLE_INTERVAL", str(args.cycle_interval))
    os.environ.setdefault("BEING_WORK_TIMEOUT", str(args.work_timeout))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _bounded_run() -> None:
        await being.start()
        ran = 0
        try:
            while not being._stop_event.is_set():
                await being.work_cycle()
                ran += 1
                if args.cycles and ran >= args.cycles:
                    break
                try:
                    await asyncio.wait_for(being._stop_event.wait(), timeout=being.cycle_interval)
                except asyncio.TimeoutError:
                    pass
        finally:
            await being.stop()

    try:
        loop.run_until_complete(_bounded_run())
    except KeyboardInterrupt:
        being.request_stop()
    finally:
        loop.close()
    return 0


def _status(_: Optional[List[str]]) -> int:
    from qb_protocol.being.being import being
    print(json.dumps(being.get_status(), indent=2, default=str))
    return 0


def _plist_payload() -> Dict[str, Any]:
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "PYTHONUNBUFFERED": "1",
        "AI_MODE_ENABLED": "true",
        "AI_MODEL_PROVIDER": "local",
        # Autonomous self-generation pulse: on by default. Set BEING_AUTONOMY=0
        # (or pass --no-autonomy) to pause self-generation and run user-input only.
        "BEING_AUTONOMY": os.environ.get("BEING_AUTONOMY", "1"),
        "BEING_CYCLE_INTERVAL": os.environ.get("BEING_CYCLE_INTERVAL", "1.0"),
        "BEING_WORK_TIMEOUT": os.environ.get("BEING_WORK_TIMEOUT", "25"),
    }
    return {
        "Label": LABEL,
        "ProgramArguments": [str(_VENV_PY), str(_RUN_SCRIPT), "run"],
        "WorkingDirectory": str(_ROOT),
        "RunAtLoad": True,
        "KeepAlive": True,
        "EnvironmentVariables": env,
        "StandardOutPath": str(LOG_DIR / "being_omega_prime.out.log"),
        "StandardErrorPath": str(LOG_DIR / "being_omega_prime.err.log"),
    }


def _write_plist() -> Path:
    LAUNCHAGENTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(PLIST_PATH, "wb") as f:
        plistlib.dump(_plist_payload(), f)
    return PLIST_PATH


def _install(_: Optional[List[str]]) -> int:
    try:
        _write_plist()
        domain = _gui_domain()
        subprocess.run(["launchctl", "bootout", f"{domain}/{LABEL}"], capture_output=True)
        result = subprocess.run(["launchctl", "bootstrap", domain, str(PLIST_PATH)], capture_output=True, text=True)
        if result.returncode != 0 and "already" not in result.stderr.lower():
            print(f"install failed: {result.stderr.strip()}", file=sys.stderr)
            return 1
        subprocess.run(["launchctl", "enable", f"{domain}/{LABEL}"], capture_output=True)
        print(f"Installed and started {LABEL}")
        print(f"Plist: {PLIST_PATH}")
        print(f"Logs: {LOG_DIR / 'being_omega_prime.out.log'}")
        print(f"Logs: {LOG_DIR / 'being_omega_prime.err.log'}")
        return 0
    except Exception as exc:
        print(f"install error: {exc}", file=sys.stderr)
        return 1


def _uninstall(_: Optional[List[str]]) -> int:
    try:
        domain = _gui_domain()
        subprocess.run(["launchctl", "bootout", f"{domain}/{LABEL}"], capture_output=True)
        if PLIST_PATH.exists():
            PLIST_PATH.unlink()
        print(f"Uninstalled {LABEL}")
        return 0
    except Exception as exc:
        print(f"uninstall error: {exc}", file=sys.stderr)
        return 1


def _service_ctl(args: Optional[List[str]]) -> int:
    domain = _gui_domain()
    cmd = getattr(args, "cmd", "")
    if cmd == "start":
        if not PLIST_PATH.exists():
            _write_plist()
        r = subprocess.run(["launchctl", "bootstrap", domain, str(PLIST_PATH)], capture_output=True, text=True)
        print("started" if r.returncode == 0 else f"start failed: {r.stderr.strip()}")
        return 0 if r.returncode == 0 else 1
    if cmd == "stop":
        r = subprocess.run(["launchctl", "bootout", f"{domain}/{LABEL}"], capture_output=True, text=True)
        print("stopped" if r.returncode == 0 else f"stop failed: {r.stderr.strip()}")
        return 0
    if cmd == "restart":
        subprocess.run(["launchctl", "bootout", f"{domain}/{LABEL}"], capture_output=True)
        r = subprocess.run(["launchctl", "bootstrap", domain, str(PLIST_PATH)], capture_output=True, text=True)
        print("restarted" if r.returncode == 0 else f"restart failed: {r.stderr.strip()}")
        return 0 if r.returncode == 0 else 1
    return 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="qb_protocol.being", description="BEING _ OMEGA + PRIM E")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Run the native service in foreground.")
    p_run.add_argument("--cycles", type=int, default=0)
    p_run.add_argument("--cycle-interval", type=float,
                       default=float(os.environ.get("BEING_CYCLE_INTERVAL", 1.0)))
    p_run.add_argument("--work-timeout", type=float,
                       default=float(os.environ.get("BEING_WORK_TIMEOUT", 25.0)))
    p_run.add_argument("--autonomy", action=argparse.BooleanOptionalAction,
                       default=os.environ.get("BEING_AUTONOMY", "1") not in _DISABLED)
    p_run.set_defaults(func=lambda a: _run([f for f in sys.argv[2:]]))

    p_status = sub.add_parser("status", help="Print service status as JSON.")
    p_status.set_defaults(func=_status)

    sub.add_parser("install", help="Install + start the launchd native service.").set_defaults(func=_install)
    sub.add_parser("uninstall", help="Remove the launchd native service.").set_defaults(func=_uninstall)

    for c in ("start", "stop", "restart"):
        p = sub.add_parser(c, help=f"{c} the launchd native service")
        p.set_defaults(cmd=c, func=_service_ctl)

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    handler = getattr(args, "func", None)
    if handler is None:
        parser.print_help()
        return 2
    return int(handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
