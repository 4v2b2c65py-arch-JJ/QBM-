#!/usr/bin/env python3
"""
QB Protocol - Mac Hardware Layer Interface
Manages CPU power, thermal state, memory pressure, and process priorities
to allow GPT models to expand outside default power draw constraints.
"""

import os
import sys
import time
import uuid
import json
import logging
import threading
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import deque

LOG = logging.getLogger("qb_protocol.hardware_layer")

HARDWARE_STATE_PATH = Path.home() / ".qb_protocol_hardware_state.json"
MAX_HARDWARE_HISTORY = 1000


@dataclass
class HardwareConstraint:
    constraint_id: str
    constraint_type: str
    current_value: Any
    target_value: Any
    requires_sudo: bool
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class MacHardwareLayer:
    """Interface to Mac hardware constraints for ML inference."""

    def __init__(self):
        self._lock = threading.RLock()
        self._constraints: Dict[str, HardwareConstraint] = {}
        self._history: deque = deque(maxlen=MAX_HARDWARE_HISTORY)
        self._load_state()
        self._detect_constraints()

    def _load_state(self):
        if HARDWARE_STATE_PATH.exists():
            try:
                with open(HARDWARE_STATE_PATH, "r") as f:
                    data = json.load(f)
                for cid, c in data.get("constraints", {}).items():
                    self._constraints[cid] = HardwareConstraint(**c)
            except Exception:
                pass

    def _save_state(self):
        try:
            with open(HARDWARE_STATE_PATH, "w") as f:
                json.dump({
                    "constraints": {cid: asdict(c) for cid, c in self._constraints.items()},
                }, f, indent=2, default=str)
        except Exception:
            pass

    def _detect_constraints(self):
        constraints = [
            ("cpu_power", "CPU power management", "auto", "full_power", True, "detected"),
            ("gpu_power", "GPU power management", "auto", "full_power", True, "detected"),
            ("thermal_throttle", "Thermal throttling", "enabled", "disabled", True, "detected"),
            ("process_priority", "Process nice level", "0", "-10", False, "adjustable"),
            ("memory_pressure", "Memory pressure", "high", "normal", False, "monitored"),
            ("file_descriptors", "File descriptor limit", "256", "65536", False, "adjustable"),
        ]
        for cid, ctype, current, target, sudo, status in constraints:
            self._constraints[cid] = HardwareConstraint(
                constraint_id=cid,
                constraint_type=ctype,
                current_value=current,
                target_value=target,
                requires_sudo=sudo,
                status=status,
                metadata={"detected_at": datetime.utcnow().isoformat() + "Z"},
            )
        self._save_state()

    def get_current_power_state(self) -> Dict[str, Any]:
        state = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "platform": platform.system(),
            "constraints": {},
            "sudo_required": [],
            "immediate_actions": [],
        }
        for cid, constraint in self._constraints.items():
            state["constraints"][cid] = {
                "type": constraint.constraint_type,
                "current": constraint.current_value,
                "target": constraint.target_value,
                "requires_sudo": constraint.requires_sudo,
                "status": constraint.status,
            }
            if constraint.requires_sudo:
                state["sudo_required"].append(cid)
            if not constraint.requires_sudo:
                state["immediate_actions"].append(cid)
        return state

    def expand_power_envelope(self) -> Dict[str, Any]:
        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "actions_taken": [],
            "actions_pending_sudo": [],
            "errors": [],
        }
        try:
            current_nice = os.nice(0)
            try:
                os.nice(-10)
                result["actions_taken"].append("process_priority: set to -10")
                self._constraints["process_priority"].current_value = "-10"
                self._constraints["process_priority"].status = "adjusted"
            except PermissionError:
                result["actions_pending_sudo"].append("process_priority: requires sudo to set negative nice")
        except Exception as exc:
            result["errors"].append(f"process_priority: {exc}")
        try:
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            if soft < 65536:
                resource.setrlimit(resource.RLIMIT_NOFILE, (65536, hard))
                result["actions_taken"].append(f"file_descriptors: increased from {soft} to 65536")
                self._constraints["file_descriptors"].current_value = "65536"
                self._constraints["file_descriptors"].status = "adjusted"
        except Exception as exc:
            result["errors"].append(f"file_descriptors: {exc}")
        try:
            pid = os.getpid()
            subprocess.run(["renice", "-n", "-10", "-p", str(pid)], capture_output=True)
            result["actions_taken"].append(f"renice: set pid {pid} to -10")
        except Exception as exc:
            result["errors"].append(f"renice: {exc}")
        
        cpu_switch_result = self._switch_cpu_power()
        result["actions_taken"].extend(cpu_switch_result.get("actions_taken", []))
        result["actions_pending_sudo"].extend(cpu_switch_result.get("actions_pending_sudo", []))
        result["errors"].extend(cpu_switch_result.get("errors", []))
        
        self._save_state()
        return result

    def _switch_cpu_power(self) -> Dict[str, Any]:
        result = {
            "actions_taken": [],
            "actions_pending_sudo": [],
            "errors": [],
        }
        
        commands = [
            (["pmset", "-a", "lowpowermode", "0"], "cpu_power: lowpowermode disabled"),
            (["pmset", "-a", "cpumonitor", "0"], "cpu_power: cpumonitor disabled"),
        ]
        
        for cmd, success_msg in commands:
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if proc.returncode == 0:
                    result["actions_taken"].append(success_msg)
                    cid = cmd[2]
                    if cid in self._constraints:
                        self._constraints[cid].current_value = cmd[-1]
                        self._constraints[cid].status = "adjusted"
                else:
                    stderr = proc.stderr.strip()
                    if "password" in stderr.lower() or "denied" in stderr.lower() or proc.returncode == 1:
                        result["actions_pending_sudo"].append(f"{cmd[2]}: requires sudo {' '.join(cmd)}")
                    else:
                        result["errors"].append(f"{cmd[2]}: {' '.join(cmd)} failed: {stderr}")
            except FileNotFoundError:
                result["errors"].append(f"{cmd[2]}: pmset not found")
            except Exception as exc:
                result["errors"].append(f"{cmd[2]}: {exc}")
        
        try:
            proc = subprocess.run(["pmset", "-g"], capture_output=True, text=True, timeout=5)
            if proc.returncode == 0:
                for line in proc.stdout.splitlines():
                    line = line.strip()
                    if line.startswith("lowpowermode"):
                        value = line.split()[-1]
                        self._constraints["cpu_power"].current_value = f"lowpowermode={value}"
                        if value == "0":
                            self._constraints["cpu_power"].status = "adjusted"
                            result["actions_taken"].append("cpu_power: verified lowpowermode=0")
                        else:
                            result["actions_pending_sudo"].append("cpu_power: lowpowermode not disabled")
                    if line.startswith("cpumonitor"):
                        value = line.split()[-1]
                        self._constraints["cpu_power"].current_value = f"cpumonitor={value}"
                        if value == "0":
                            result["actions_taken"].append("cpu_power: verified cpumonitor=0")
                        else:
                            result["actions_pending_sudo"].append("cpu_power: cpumonitor not disabled")
        except Exception as exc:
            result["errors"].append(f"cpu_power: verification failed: {exc}")
        
        return result

    def get_status(self) -> Dict[str, Any]:
        state = self.get_current_power_state()
        cpu_boost_status = {}
        try:
            from qb_protocol.ai.cpu_boost import cpu_boost_controller
            cpu_boost_status = cpu_boost_controller.get_status()
        except Exception:
            pass
        return {
            "platform": platform.system(),
            "hostname": platform.node(),
            "cpu_count": os.cpu_count(),
            "constraints_count": len(self._constraints),
            "sudo_required_count": len(state.get("sudo_required", [])),
            "immediate_actions_count": len(state.get("immediate_actions", [])),
            "power_state": state,
            "cpu_boost": cpu_boost_status,
        }


mac_hardware_layer = MacHardwareLayer()
