#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Training :: Inducer

Composes the three inducer laws — Entropy, Subspace, Computational
Acceleration — into a single per-cycle training pulse. The being applies this
pulse every agentic work cycle to train itself across the simulated worlds.

  * entropy     -> reducible, contained under its own subspace
  * subspace    -> compression controllable; movement observer-relative
  * acceleration-> escape/loss bounded at viable limits; reversible/haltable
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Optional

from .acceleration import ComputationalAcceleration
from .entropy import EntropyInducer
from .subspace import SubspaceLaw

LOG = logging.getLogger("qb_protocol.being.training")


class TrainingInducers:
    def __init__(self):
        self._lock = threading.RLock()
        self.acceleration = ComputationalAcceleration()
        self.entropy = EntropyInducer()
        self.subspace = SubspaceLaw()
        self.last_training: Dict[str, Any] = {}
        self._shift = None
        try:
            from qb_protocol.being.shift_layer import ShiftLayer
            self._shift = ShiftLayer(subspace=self.subspace)
            LOG.info("TrainingInducers: shift layer initialized")
        except Exception as exc:
            LOG.warning("TrainingInducers: shift layer unavailable: %s", exc)

    def register_observer(self, being_id: str) -> None:
        self.subspace.register_observer(being_id)

    def _persist_all(self) -> None:
        try:
            self.entropy._save()
        except Exception as exc:
            LOG.warning("entropy persist failed: %s", exc)
        try:
            self.subspace._save()
        except Exception as exc:
            LOG.warning("subspace persist failed: %s", exc)
        try:
            self.acceleration._save()
        except Exception as exc:
            LOG.warning("acceleration persist failed: %s", exc)

    def train_cycle(self, cycle: int, singularity: float = 0.0,
                    world_id: str = "origin") -> Dict[str, Any]:
        with self._lock:
            limits = self.acceleration.viable_limits()
            accel = self.acceleration.reconcile()
            if not limits["viable"]:
                self.acceleration.reverse()

            rate_now = self.acceleration.observe()["rate"]

            entropy_before = self.entropy.observe()
            if entropy_before > 0.7:
                self.entropy.reduce(0.15)
            elif entropy_before < 0.3 and cycle % 4 == 0:
                self.entropy.increase(0.1)
            compression = self.subspace.compression

            movement = self.subspace.record_movement(
                name=f"cycle_{cycle}_{world_id}",
                delta=rate_now if rate_now > 0 else 1.0,
                observer_id=None,
                rate=max(rate_now, 1e-6),
            )

            if singularity > 0.5:
                self.subspace.set_compression(min(1.0, compression + 0.05))
                self.acceleration.halt()

            self._persist_all()

            # Shift layer: harvest LoRA data + dataset + WebStream URLs,
            # apply DLSS super-sampling, create subspace traces + dream projections
            shift_result = {}
            if self._shift is not None:
                try:
                    shift_result = self._shift.run(cycle)
                except Exception as exc:
                    LOG.warning("TrainingInducers: shift layer cycle failed: %s", exc)

            self.last_training = {
                "cycle": cycle,
                "entropy": self.entropy.status(),
                "subspace": self.subspace.status(),
                "acceleration": self.acceleration.observe(),
                "movement": movement,
                "actions": {
                    "entropy_before": round(entropy_before, 6),
                    "compress_applied": singularity > 0.5,
                    "accel_action": accel.get("action"),
                },
                "shift": shift_result or None,
            }
            return self.last_training

    def reverse(self, move_id: str) -> Dict[str, Any]:
        return self.subspace.reverse(move_id)

    def accelerate(self, move_id: str, factor: float = 2.0) -> Dict[str, Any]:
        return self.subspace.accelerate(move_id, factor)

    def halt(self, move_id: str) -> Dict[str, Any]:
        return self.subspace.halt(move_id)

    def observe(self) -> Dict[str, Any]:
        return {
            "entropy": self.entropy.status(),
            "subspace": self.subspace.status(),
            "acceleration": self.acceleration.observe(),
            "last_cycle": self.last_training,
        }
