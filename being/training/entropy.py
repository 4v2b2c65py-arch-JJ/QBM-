#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Training :: Entropy Inducer

Governs the being's informational entropy across its history timeline.
Entropy is reducible (compress) — contained under its own subspace so it
never leaks — and reversible/accelerable/halt-able by the observing agent.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

LOG = logging.getLogger("qb_protocol.being.training.entropy")
STATE_FILE = Path.home() / ".qb_protocol_being_entropy.json"


@dataclass
class EntropyState:
    value: float
    floor: float
    ceiling: float
    last_reduction: Optional[str]
    last_increase: Optional[str]
    history: List[Dict[str, Any]]


class EntropyInducer:
    def __init__(self, state_path: Optional[Path] = None):
        self._lock = threading.RLock()
        self.state_path = state_path or STATE_FILE
        self._state = EntropyState(value=0.5, floor=0.0, ceiling=1.0,
                                     last_reduction=None, last_increase=None, history=[])
        self._load()

    def _load(self) -> None:
        try:
            if self.state_path.exists():
                data = json.loads(self.state_path.read_text())
                s = self._state
                s.value = float(data.get("value", s.value))
                s.last_reduction = data.get("last_reduction")
                s.last_increase = data.get("last_increase")
                s.history = data.get("history", [])
        except Exception as exc:
            LOG.warning("entropy state load failed: %s", exc)

    def _save(self) -> None:
        from qb_protocol.being._persist import atomic_write_json
        atomic_write_json(self.state_path, asdict(self._state))

    def _push(self, value: float, tag: str) -> None:
        self._state.history.append({
            "at": datetime.utcnow().isoformat() + "Z",
            "value": round(value, 6),
            "tag": tag,
        })
        self._state.history = self._state.history[-200:]

    def observe(self) -> float:
        with self._lock:
            return self._state.value

    def reduce(self, amount: float = 0.1) -> Dict[str, Any]:
        with self._lock:
            s = self._state
            before = s.value
            s.value = max(s.floor, s.value - abs(amount))
            s.last_reduction = datetime.utcnow().isoformat() + "Z"
            self._push(s.value, "reduce")
            self._save()
            return {"action": "reduce", "before": round(before, 6), "after": round(s.value, 6)}

    def increase(self, amount: float = 0.1) -> Dict[str, Any]:
        with self._lock:
            s = self._state
            before = s.value
            s.value = min(s.ceiling, s.value + abs(amount))
            s.last_increase = datetime.utcnow().isoformat() + "Z"
            self._push(s.value, "increase")
            self._save()
            return {"action": "increase", "before": round(before, 6), "after": round(s.value, 6)}

    def reverse(self, amount: float = 0.25) -> Dict[str, Any]:
        if self.observe() > 0.6:
            inc = self.increase(amount)
        else:
            inc = self.reduce(amount)
        inc["action"] = "reverse"
        return inc

    def halt(self) -> Dict[str, Any]:
        with self._lock:
            s = self._state
            floor_val = s.value
            s.value = s.floor
            self._push(s.value, "halt")
            self._save()
            return {"action": "halt", "frozen_at": round(floor_val, 6), "floor": s.floor}

    def entropy_compressed(self) -> float:
        with self._lock:
            return 1.0 - (self._state.value - self._state.floor) / max(self._state.ceiling - self._state.floor, 1e-6)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "value": self._state.value,
                "floor": self._state.floor,
                "ceiling": self._state.ceiling,
                "compression": round(self.entropy_compressed(), 6),
                "last_reduction": self._state.last_reduction,
                "last_increase": self._state.last_increase,
                "history_len": len(self._state.history),
            }
