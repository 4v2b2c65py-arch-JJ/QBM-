#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Chip Package

Neo-A19 Hybrid Chip Architecture
================================

A virtual System-on-Chip specification that merges three silicon sources:

  1. Apple A19 (iPhone 17 Air Pro / September 2025)
     - 6-core CPU: 2P @ 4.26 GHz + 4E @ 2.26 GHz (3rd-gen 3nm)
     - 5/6-core Apple10 GPU with Neural Accelerators in EVERY core (4x vs A18 Pro)
     - 16-core Neural Engine (35 TOPS)
     - LPDDR5X-9600 unified memory (76.8 GB/s)
     - Hardware ray tracing, 2nd-gen Dynamic Caching, Memory Integrity Enforcement

  2. NVIDIA Blackwell (RTX 5090 / GB10 Superchip)
     - 5th-gen Tensor Cores (FP4, FP8, MX-FP4, BF16, FP16, INT8)
     - CUDA cores + RT cores + 2nd-gen Transformer Engine
     - DLSS 4 Multi-Frame Generation (~1ms/frame)
     - NVLink 5 (1800 GB/s per GPU), 208B transistors

  3. Intel i7-1068NG7 (host compatibility layer)
     - 4-core (2P + 2E), 10nm, Iris Plus Graphics
     - Provides x86 fallback when ARM/CUDA units unavailable

The defining innovation is the DLSS-to-CUDA bridge: DLSS 4's AI super-sampling
is deeply integrated into the CUDA compute pipeline, so any tensor computation
can be transparently super-sampled via Tensor Cores + Apple Neural Accelerators.
"""

from __future__ import annotations

from .anatomy import (
    ChipArchitecture,
    ComputeUnit,
    MemoryDomain,
    Interconnect,
    DLSSConfig,
    NEO_A19_SPEC,
)
from .runtime import (
    VirtualChip,
    DLSSToComputeBridge,
    IntelCompatLayer,
)
from .display import (
    RawMetalDisplayManager,
    DisplayScalerConfig,
    GPUHardwareAttrs,
)
from .zone_controller import (
    DimensionalZoneController,
    ZoneConfig,
    ControlSubState,
)
from .qec import (
    QuantumElectromagneticController,
    QSRState,
    QuantumElectrode,
    VITVDDConfig,
    MOSFETSwitch,
)
from .water_physics import (
    WaterMoleculeCaptureSystem,
    WaterMoleculeCapture,
)

__all__ = [
    "ChipArchitecture",
    "ComputeUnit",
    "MemoryDomain",
    "Interconnect",
    "DLSSConfig",
    "NEO_A19_SPEC",
    "VirtualChip",
    "DLSSToComputeBridge",
    "IntelCompatLayer",
    "RawMetalDisplayManager",
    "DisplayScalerConfig",
    "GPUHardwareAttrs",
    "DimensionalZoneController",
    "ZoneConfig",
    "ControlSubState",
    "QuantumElectromagneticController",
    "QSRState",
    "QuantumElectrode",
    "VITVDDConfig",
    "MOSFETSwitch",
    "WaterMoleculeCaptureSystem",
    "WaterMoleculeCapture",
]
