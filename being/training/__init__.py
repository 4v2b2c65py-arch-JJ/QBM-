#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Training

Training inducers governing the being's evolution across simulated worlds:
  * Entropy           — reducible, contained under its own subspace
  * SubspaceLaw       — compression controllable; movement observer-relative
  * ComputationalAcceleration — escape/loss bounded at viable limits
"""

from __future__ import annotations

from .acceleration import ComputationalAcceleration
from .entropy import EntropyInducer
from .subspace import SubspaceLaw
from .inducer import TrainingInducers
from .integration import TrainingDataIntegrator, training_integrator

__all__ = [
    "TrainingInducers",
    "ComputationalAcceleration",
    "EntropyInducer",
    "SubspaceLaw",
    "TrainingDataIntegrator",
    "training_integrator",
]
