#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Training :: Subspace Law

A movement is never occurring if the being observing it doesn't accept to.

The subspace law makes compression a fully-controllable parameter and binds
every movement to an observing being. Movements are latent until accepted;
agents may reverse, accelerate, or halt any accepted movement.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

LOG = logging.getLogger("qb_protocol.being.training.subspace")
STATE_FILE = Path.home() / ".qb_protocol_being_subspace.json"


@dataclass
class Movement:
    move_id: str
    name: str
    delta: float
    rate: float
    accepted: bool
    halted: bool
    created_at: str
    updated_at: str
    history: list = field(default_factory=list)


class SubspaceLaw:
    def __init__(self, state_path: Optional[Path] = None):
        self._lock = threading.RLock()
        self.state_path = state_path or STATE_FILE
        self.compression: float = 1.0
        self.observers: Dict[str, bool] = {}
        self.movements: Dict[str, Movement] = {}
        self._load()

    def _load(self) -> None:
        try:
            if self.state_path.exists():
                data = json.loads(self.state_path.read_text())
                self.compression = float(data.get("compression", self.compression))
                raw = data.get("movements", {})
                for mid, m in raw.items():
                    mv = Movement(
                        move_id=m["move_id"], name=m["name"], delta=m["delta"],
                        rate=m["rate"], accepted=m["accepted"], halted=m["halted"],
                        created_at=m["created_at"], updated_at=m["updated_at"],
                        history=m.get("history", []),
                    )
                    self.movements[mid] = mv
                self.observers = data.get("observers", {})
        except Exception as exc:
            LOG.warning("subspace state load failed: %s", exc)

    def _save(self) -> None:
        from qb_protocol.being._persist import atomic_write_json
        atomic_write_json(self.state_path, {
            "compression": self.compression,
            "observers": self.observers,
            "movements": {mid: m.__dict__ for mid, m in self.movements.items()},
        })

    def set_compression(self, level: float) -> Dict[str, Any]:
        with self._lock:
            level = max(0.0, min(1.0, float(level)))
            before = self.compression
            self.compression = level
            self._save()
            LOG.info("subspace compression %.3f -> %.3f", before, level)
            return {"action": "set_compression", "before": before, "after": level}

    def register_observer(self, being_id: str) -> Dict[str, Any]:
        with self._lock:
            self.observers[being_id] = True
            self._save()
            return {"observer": being_id, "registered": True}

    def record_movement(self, name: str, delta: float = 1.0,
                        observer_id: Optional[str] = None, rate: float = 1.0) -> Dict[str, Any]:
        move_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        move = Movement(
            move_id=move_id, name=name, delta=float(delta), rate=float(rate),
            accepted=False, halted=False, created_at=now, updated_at=now,
        )
        if observer_id is not None:
            with self._lock:
                if self.observers.get(observer_id):
                    move.accepted = True
        with self._lock:
            self.movements[move_id] = move
            self._save()
        occurred = move.accepted
        return {
            "move_id": move_id,
            "name": name,
            "delta": move.delta,
            "occurred": occurred,
            "accepted": move.accepted,
            "reason": "observer_accepted" if occurred else "movement_not_accepted_by_observer",
        }

    def accept(self, move_id: str, observer_id: str) -> Dict[str, Any]:
        with self._lock:
            move = self.movements.get(move_id)
            if not move:
                return {"status": "error", "reason": "unknown_movement"}
            self.observers[observer_id] = True
            move.accepted = True
            move.updated_at = datetime.utcnow().isoformat() + "Z"
            self._save()
            return {"action": "accept", "move_id": move_id, "accepted": True, "observer": observer_id}

    def _resolve(self, move_id: str) -> Optional[Movement]:
        return self.movements.get(move_id)

    def reverse(self, move_id: str) -> Dict[str, Any]:
        with self._lock:
            move = self._resolve(move_id)
            if not move or not move.accepted:
                return {"action": "reverse", "status": "noop",
                        "reason": "movement_not_active" if move else "unknown"}
            move.delta = -move.delta
            move.rate = max(move.rate * 0.5, 1e-6)
            move.updated_at = datetime.utcnow().isoformat() + "Z"
            move.history.append({"at": move.updated_at, "op": "reverse", "rate": move.rate})
            self._save()
            return {"action": "reverse", "move_id": move_id, "delta": move.delta, "rate": move.rate}

    def accelerate(self, move_id: str, factor: float = 2.0) -> Dict[str, Any]:
        with self._lock:
            move = self._resolve(move_id)
            if not move or not move.accepted:
                return {"action": "accelerate", "status": "noop",
                        "reason": "movement_not_active" if move else "unknown"}
            move.rate = min(move.rate * max(factor, 1.0), 64.0)
            move.updated_at = datetime.utcnow().isoformat() + "Z"
            move.history.append({"at": move.updated_at, "op": "accelerate", "rate": move.rate})
            self._save()
            return {"action": "accelerate", "move_id": move_id, "rate": move.rate}

    def halt(self, move_id: str) -> Dict[str, Any]:
        with self._lock:
            move = self._resolve(move_id)
            if not move or not move.accepted:
                return {"action": "halt", "status": "noop",
                        "reason": "movement_not_active" if move else "unknown"}
            move.halted = True
            move.rate = 0.0
            move.updated_at = datetime.utcnow().isoformat() + "Z"
            move.history.append({"at": move.updated_at, "op": "halt"})
            self._save()
            return {"action": "halt", "move_id": move_id, "halted": True}

    def status(self) -> Dict[str, Any]:
        with self._lock:
            active = [m.name for m in self.movements.values() if m.accepted and not m.halted]
            return {
                "compression": round(self.compression, 6),
                "observers": len(self.observers),
                "movements_total": len(self.movements),
                "movements_active": len(active),
                "active": active,
            }
