#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Training :: Computational Acceleration

The law of computational acceleration: governs how far the being's computational
step-rate can advance. Escape (coherence loss) and loss accumulate with rate;
at viable limits the inducer reverses before escape breaches tolerance.
Agents may reverse, accelerate, or halt the rate at any time.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

LOG = logging.getLogger("qb_protocol.being.training.acceleration")
STATE_FILE = Path.home() / ".qb_protocol_being_acceleration.json"


@dataclass
class AccelerationLaw:
    rate: float
    escape: float
    loss: float
    min_rate: float
    max_rate: float
    escape_limit: float
    loss_limit: float
    max_escape_rate: float
    halted: bool
    history: list


class ComputationalAcceleration:
    def __init__(self, state_path: Optional[Path] = None):
        self._lock = threading.RLock()
        self.state_path = state_path or STATE_FILE
        self._law = AccelerationLaw(
            rate=1.0, escape=0.0, loss=0.0,
            min_rate=0.125, max_rate=8.0,
            escape_limit=4.0, loss_limit=2.0, max_escape_rate=1.0,
            halted=False, history=[],
        )
        self._load()

    def _load(self) -> None:
        try:
            if self.state_path.exists():
                data = json.loads(self.state_path.read_text())
                l = self._law
                l.rate = float(data.get("rate", l.rate))
                l.escape = float(data.get("escape", l.escape))
                l.loss = float(data.get("loss", l.loss))
                l.halted = bool(data.get("halted", l.halted))
                l.history = data.get("history", [])
        except Exception as exc:
            LOG.warning("acceleration state load failed: %s", exc)

    def _save(self) -> None:
        from qb_protocol.being._persist import atomic_write_json
        atomic_write_json(self.state_path, asdict(self._law))

    def _append(self, rate: float, escape: float, loss: float, tag: str) -> None:
        self._law.history.append({
            "at": datetime.utcnow().isoformat() + "Z",
            "rate": rate, "escape": escape, "loss": loss, "tag": tag,
        })
        self._law.history = self._law.history[-200:]

    def viable_limits(self) -> Dict[str, float]:
        with self._lock:
            l = self._law
            headroom_escape = max(0.0, l.escape_limit - l.escape)
            headroom_loss = max(0.0, l.loss_limit - l.loss)
            max_safe_rate = l.rate
            if l.escape <= 0:
                safe_escape = l.escape_limit / max(l.max_escape_rate, 1e-6)
            else:
                safe_escape = headroom_escape / (l.escape / max(l.rate, 1e-6))
            if l.loss > 0:
                safe_loss = headroom_loss / l.loss
            else:
                safe_loss = l.max_rate
            max_safe = min(l.max_rate, safe_escape, safe_loss, headroom_loss / 4 + l.rate)
            return {
                "min_rate": l.min_rate,
                "max_rate": l.max_rate,
                "max_safe_rate": max(l.min_rate, max_safe),
                "escape_headroom": headroom_escape,
                "loss_headroom": headroom_loss,
                "viable": l.rate <= max_safe,
            }

    def accelerate(self, factor: float = 2.0) -> Dict[str, Any]:
        with self._lock:
            l = self._law
            if l.halted:
                l.halted = False
            limits = self.viable_limits()
            target = min(l.rate * max(factor, 1.0), limits["max_safe_rate"])
            l.rate = round(target, 6)
            l.escape = min(l.escape + 0.25 / max(l.rate, 1e-6), l.escape_limit)
            l.loss = min(l.loss + 0.1 / max(l.rate, 1e-6), l.loss_limit)
            self._append(l.rate, l.escape, l.loss, "accelerate")
            self._save()
            return {"action": "accelerate", "rate": l.rate, "escape": l.escape, "loss": l.loss, "limits": limits}

    def reverse(self, factor: float = 0.5) -> Dict[str, Any]:
        with self._lock:
            l = self._law
            target = max(l.rate * min(factor, 1.0), l.min_rate)
            l.rate = round(target, 6)
            decay = 0.3 / max(l.rate, 1e-6)
            l.escape = max(0.0, l.escape - decay)
            l.loss = max(0.0, l.loss - decay)
            self._append(l.rate, l.escape, l.loss, "reverse")
            self._save()
            return {"action": "reverse", "rate": l.rate, "escape": l.escape, "loss": l.loss}

    def halt(self) -> Dict[str, Any]:
        with self._lock:
            l = self._law
            l.halted = True
            l.rate = 0.0
            self._append(0.0, l.escape, l.loss, "halt")
            self._save()
            return {"action": "halt", "rate": 0.0, "escape": l.escape, "loss": l.loss}

    def reconcile(self) -> Dict[str, Any]:
        with self._lock:
            l = self._law
            limits = self.viable_limits()
            action = "stable"
            if not limits["viable"]:
                rep = self.reverse()
                action = "reversed"
            elif l.escape > l.escape_limit * 0.8 or l.loss > l.loss_limit * 0.8:
                rep = self.reverse()
                action = "preemptive_reverse"
            else:
                rep = {"rate": l.rate, "escape": l.escape, "loss": l.loss}
            return {
                "action": action,
                "rate": l.rate,
                "escape": l.escape,
                "loss": l.loss,
                "limits": limits,
                "details": rep,
            }

    def step_effect(self) -> Dict[str, Any]:
        with self._lock:
            l = self._law
            if l.halted:
                return {"effect": "none", "rate": 0.0, "reason": "halted"}
            escape_cost = l.rate * l.max_escape_rate
        return self.reconcile() if (l.escape + escape_cost > l.escape_limit) else {"effect": "advance", "rate": l.rate}

    def observe(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "rate": self._law.rate,
                "escape": self._law.escape,
                "loss": self._law.loss,
                "halted": self._law.halted,
                "limits": self.viable_limits(),
                "history_len": len(self._law.history),
            }
