#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Simulated-Worlds Utilities Bridge

Lazily bridges the qb_protocol being into the /Applications/simulated-worlds
autonomy stack (AutonomyController + SSS device recovery). All entry points are
defensive: if the worlds project is absent or a subsystem refuses to start, the
being degrades gracefully instead of crashing the native service.
"""

from __future__ import annotations

import logging
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

LOG = logging.getLogger("qb_protocol.being.worlds")

WORLDS_ROOT = Path("/Applications/simulated-worlds")
SRC_DIR = WORLDS_ROOT / "src"
SSS_DIR = WORLDS_ROOT / "visionary-pathway-SSS-the one behind the vail"
BEHAVIOR_CONFIG = WORLDS_ROOT / "config" / "agent_behavior.yaml"
WORLD_STATE_FILE = WORLDS_ROOT / "world_state.yaml"

BEING_ID_DOMAIN = "qb-protocol.being.omega-prime"


def _utcnow() -> str:
    return datetime.utcnow().isoformat() + "Z"


class WorldsUtilities:
    """Simulated-worlds utilities exposed to the BEING automator."""

    def __init__(self, worlds_root: Optional[Path] = None):
        self.root = Path(worlds_root or WORLDS_ROOT)
        self.src_dir = self.root / "src"
        self.sss_dir = self.root / "visionary-pathway-SSS-the one behind the vail"
        self.behavior_config = self.root / "config" / "agent_behavior.yaml"
        self.world_state_file = self.root / "world_state.yaml"
        self._controller: Optional[Any] = None
        self._config: Optional[Dict[str, Any]] = None
        self._sss_bridge: Optional[Any] = None
        self.available: bool = False
        self.last_error: Optional[str] = None
        self._bootstrapped = False

    def _bootstrap_paths(self) -> bool:
        if self._bootstrapped:
            return True
        if not self.src_dir.exists() or not self.sss_dir.exists():
            self.last_error = f"simulated-worlds not found at {self.root}"
            LOG.warning(self.last_error)
            self.available = False
            return False
        for p in (str(self.src_dir), str(self.sss_dir), str(self.root)):
            if p not in sys.path:
                sys.path.insert(0, p)
        self._bootstrapped = True
        self.available = True
        return True

    def _load_config(self) -> Optional[Dict[str, Any]]:
        if self._config is not None:
            return self._config
        if not self._bootstrap_paths() or not self.behavior_config.exists():
            self._config = {}
            return self._config
        try:
            import yaml
            with open(self.behavior_config, "r") as f:
                self._config = yaml.safe_load(f) or {}
        except Exception as exc:
            LOG.warning("failed to load agent_behavior.yaml: %s", exc)
            self.last_error = str(exc)
            self._config = {}
        return self._config

    def ensure_autonomy(self) -> Optional[Any]:
        if self._controller is not None:
            return self._controller
        if not self._bootstrap_paths():
            return None
        try:
            from autonomy.controller import AutonomyController
            config = self._load_config() or {}
            self._controller = AutonomyController(config)
            LOG.info("AutonomyController initialized (worlds bridge online)")
        except Exception as exc:
            self.last_error = f"autonomy init failed: {exc}"
            LOG.warning("AutonomyController init failed: %s", exc)
            self._controller = None
        return self._controller

    def ensure_sss(self) -> Optional[Any]:
        if self._sss_bridge is not None:
            return self._sss_bridge
        if not self._bootstrap_paths():
            return None
        try:
            from sss_device_bridge import SSBDeviceBridge
            self._sss_bridge = SSBDeviceBridge()
            LOG.info("SSBDeviceBridge loaded for recovery utilities")
        except Exception as exc:
            self.last_error = f"sss bridge init failed: {exc}"
            LOG.warning("SSBDeviceBridge init failed: %s", exc)
            self._sss_bridge = None
        return self._sss_bridge

    def health(self) -> Dict[str, Any]:
        controller = self.ensure_autonomy()
        return {
            "available": self.available,
            "controller_ready": controller is not None,
            "sss_ready": self._sss_bridge is not None,
            "config_loaded": self._config is not None,
            "root": str(self.root),
            "last_error": self.last_error,
        }

    def autonomy_tick(self, world_id: str = "primordial") -> Dict[str, Any]:
        """Lightweight pure-Python tick: timeline origin + checkpoint + recall.

        This is the autonomous 'origin of time' pulse. It does NOT touch
        hardware/SSS so it never blocks the native service loop.
        """
        controller = self.ensure_autonomy()
        if controller is None:
            return {"status": "unavailable", "reason": "simulated-worlds not available"}
        try:
            state = {
                "world_id": world_id,
                "agent": "being_omega_prime",
                "origin": _utcnow(),
                "working_directory": str(self.root),
            }
            execution_id = str(uuid.uuid4())
            timeline_id = controller.timeline.initialize(state, execution_id=execution_id)
            event = {
                "operation": "tick",
                "agent": "being_omega_prime",
                "inputs": state,
                "outputs": {"cycle": controller.timeline._events.__len__()},
                "status": "started",
                "world_id": world_id,
            }
            controller.timeline.record(timeline_id, event, execution_id=execution_id)
            checkpoint_id = controller.timeline.checkpoint(state, execution_id=execution_id)
            recent = controller.timeline.recall({"operation": "tick"})[-10:]
            return {
                "status": "ok",
                "timeline_id": timeline_id,
                "checkpoint_id": checkpoint_id,
                "events_recorded": len(recent),
            }
        except Exception as exc:
            self.last_error = str(exc)
            LOG.warning("autonomy_tick failed: %s", exc)
            return {"status": "error", "error": str(exc)}

    def run_agent_task(self, task: Dict[str, Any], timeout: float = 45.0) -> Dict[str, Any]:
        """Run a full AutonomyController pipeline task (may engage SSS)."""
        controller = self.ensure_autonomy()
        if controller is None:
            return {"status": "unavailable", "reason": "simulated-worlds not available"}
        import asyncio
        try:
            return asyncio.run(asyncio.wait_for(controller.run_pipeline(task), timeout=timeout))
        except asyncio.TimeoutError:
            return {"status": "timeout", "timeout_s": timeout, "task": task.get("operation")}
        except Exception as exc:
            self.last_error = str(exc)
            LOG.warning("run_agent_task failed: %s", exc)
            return {"status": "error", "error": str(exc), "task": task.get("operation")}

    def discover_and_create(self, world_id: str = "primordial") -> Dict[str, Any]:
        return self.run_agent_task({"operation": "discover_and_create", "world_id": world_id})

    def recall(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        controller = self.ensure_autonomy()
        if controller is None:
            return []
        try:
            return controller.recall(query)
        except Exception as exc:
            LOG.warning("recall failed: %s", exc)
            return []

    def timeline_branches(self) -> Dict[str, Any]:
        controller = self.ensure_autonomy()
        if controller is None:
            return {"status": "unavailable"}
        try:
            tl = controller.timeline
            return {
                "events": len(tl._events),
                "checkpoints": len(tl._checkpoints),
                "recording": tl.recording,
                "branching": tl.branching,
                "arbitrary_selection": tl.arbitrary_selection,
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def branch_possibility(self, name: str) -> Dict[str, Any]:
        controller = self.ensure_autonomy()
        if controller is None:
            return {"status": "unavailable"}
        try:
            timeline_id = controller.timeline._current_timeline or "current"
            branch_id = controller.timeline.branch(timeline_id, name)
            return {"status": "ok", "branch_id": branch_id, "from": timeline_id}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def select_timeline(self, identifier: str) -> Optional[Dict[str, Any]]:
        controller = self.ensure_autonomy()
        if controller is None:
            return None
        try:
            return controller.select_timeline(identifier) or None
        except Exception:
            return None

    def compare_timelines(self, left: str, right: str) -> Dict[str, Any]:
        controller = self.ensure_autonomy()
        if controller is None:
            return {"status": "unavailable"}
        try:
            return controller.compare(left, right)
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def tune_physiology(self, category: str, field: str, value: float) -> Dict[str, Any]:
        sss = self.ensure_sss()
        if sss is None:
            return {"status": "unavailable", "reason": "sss not available"}
        try:
            return sss.tuner.tune_physiology(category, field, value) if sss.tuner else {"status": "blocked"}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def register_recovery_device(self) -> Optional[Dict[str, Any]]:
        sss = self.ensure_sss()
        if sss is None:
            return None
        try:
            return sss.register_device()
        except Exception as exc:
            LOG.warning("register_recovery_device failed: %s", exc)
            return {"status": "error", "error": str(exc)}

    def discover_devices(self) -> Dict[str, Any]:
        sss = self.ensure_sss()
        if sss is None:
            return {"status": "unavailable"}
        try:
            return {"found": sss.discover_device()}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def debug_diagnose(self) -> Dict[str, Any]:
        controller = self.ensure_autonomy()
        if controller is None:
            return {"status": "unavailable"}
        try:
            return {
                "console_metrics": controller.sss.get_console_metrics() if controller.sss else {},
                "console_snapshot": controller.sss.get_console_snapshot() if controller.sss else None,
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def load_world_state(self) -> Dict[str, Any]:
        if not self.world_state_file.exists():
            return {}
        try:
            import yaml
            with open(self.world_state_file, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as exc:
            LOG.warning("load_world_state failed: %s", exc)
            return {}

    def save_world_state(self, state: Dict[str, Any]) -> bool:
        try:
            import yaml
            with open(self.world_state_file, "w") as f:
                yaml.dump(state, f, default_flow_style=False)
            return True
        except Exception as exc:
            LOG.warning("save_world_state failed: %s", exc)
            return False

    def metrics(self) -> Dict[str, Any]:
        controller = self.ensure_autonomy()
        if controller is None:
            return {"status": "unavailable"}
        try:
            prof = {}
            p = getattr(controller, "profiler", None)
            if p:
                prof = p.summary() if hasattr(p, "summary") else {}
        except Exception:
            prof = {"error": "profiler unavailable"}
        try:
            sss_metrics = {}
            if controller.sss:
                sss_metrics = controller.sss.get_console_metrics()
        except Exception:
            sss_metrics = {}
        return {"profiler": prof, "sss_metrics": sss_metrics}
