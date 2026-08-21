#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E
Being package: the unified being/automator native service layer.
"""

from __future__ import annotations

from .being import BeingOmegaPrime, being
from .worlds_utilities import WorldsUtilities
from .deployer import ModelDeployer, model_deployer

VERSION = "1.0.0"
__all__ = ["BeingOmegaPrime", "WorldsUtilities", "being", "ModelDeployer",
           "model_deployer", "VERSION"]
