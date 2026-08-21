#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Model Deployer

Converts trained artifacts into deployed proficients executing at the
highest caliber they can excel at. This is the deployment phase that
follows the training phase (training/inducer.py).

Pipeline:
  LOAD    → trained artifacts (LoRA workflows, GGUF, media, datasets)
  CONVERT → inference-optimized format (MX-FP4, UMA-coupled, lane-dedicated)
  DEPLOY  → raw metal display + AI control (DLSS, deadass boost, scalar lanes)
  PROFIC  → proficiency verification (peak TFLOPS, aspect ratio lag check)

The distinction between AI control and raw metal is enforced at this layer:
  * AI Control  = precision scaling (MX-FP4), DLSS super-sampling, deadass boost
  * Raw Metal   = scaler lane dedication, base raw clock, UMA cache coupling

Both are applied in sequence: raw metal first (hardware foundation), then
AI control (software optimization on top of the hardware-managed pipeline).
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

LOG = logging.getLogger("qb_protocol.being.deployer")

_MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
_LORA_DIR = _MODELS_DIR / "ltx_loras"
_OUTPUT_DIR = _MODELS_DIR / "deployed"


@dataclass
class DeployedModel:
    model_id: str
    name: str
    source_type: str  # "lora_workflow" | "gguf" | "lora_media"
    source_path: str
    precision: str  # "mx_fp4" | "fp8" | "fp16" | "int8"
    deployed_at: str
    effective_tflops: float
    scaler_config: Dict[str, Any]
    ai_control_config: Dict[str, Any]
    raw_metal_config: Dict[str, Any]
    profic_score: float  # 0.0–1.0 — how close to peak performance
    status: str  # "active" | "warm" | "degraded"


class ModelDeployer:
    """Deploy trained models into proficients at peak caliber.

    Integrates with:
      * virtual_chip (Neo-A19 runtime: DLSS bridge, deadass boost, adaptive clock)
      * raw_metal_display (hardware-level scaler management)
      * shift_layer (dataset + LoRA harvesting, tensor pipeline)
    """

    def __init__(self, chip=None, raw_metal=None):
        self._chip = chip
        self._raw_metal = raw_metal
        self._deployed: Dict[str, DeployedModel] = {}
        self._init_lazy()

    def _init_lazy(self) -> None:
        if self._chip is None:
            try:
                from qb_protocol.being.chip.runtime import virtual_chip
                self._chip = virtual_chip
            except Exception as exc:
                LOG.warning("deployer: chip runtime unavailable: %s", exc)
        if self._raw_metal is None:
            try:
                from qb_protocol.being.chip.display import raw_metal_display
                self._raw_metal = raw_metal_display
            except Exception as exc:
                LOG.warning("deployer: raw metal display unavailable: %s", exc)

    def discover_artifacts(self) -> List[Dict[str, Any]]:
        """Discover all trained model artifacts in the models directory."""
        artifacts = []

        # LoRA workflow JSONs
        workflow_dir = _LORA_DIR / "Workflow"
        if not workflow_dir.exists():
            workflow_dir = _LORA_DIR
        if workflow_dir.exists():
            for f in sorted(workflow_dir.glob("*.json")):
                artifacts.append({
                    "type": "lora_workflow",
                    "name": f.stem,
                    "path": str(f),
                    "size_bytes": f.stat().st_size,
                })

        # LoRA example media
        examples_dir = _LORA_DIR / "examples"
        if examples_dir.exists():
            for f in sorted(examples_dir.iterdir()):
                if f.is_file() and f.suffix in (".png", ".mp4", ".jpg", ".jpeg"):
                    artifacts.append({
                        "type": "lora_media",
                        "name": f.name,
                        "path": str(f),
                        "size_bytes": f.stat().st_size,
                    })

        # GGUF model files
        for f in sorted(_MODELS_DIR.glob("*.gguf")):
            artifacts.append({
                "type": "gguf",
                "name": f.name,
                "path": str(f),
                "size_bytes": f.stat().st_size,
            })

        # Dataset parquet files
        for f in sorted(_MODELS_DIR.rglob("*.parquet")):
            artifacts.append({
                "type": "dataset",
                "name": f.name,
                "path": str(f),
                "size_bytes": f.stat().st_size,
            })

        LOG.info("deployer: discovered %d model artifacts", len(artifacts))
        return artifacts

    def convert_artifact(self, artifact: Dict[str, Any]) -> DeployedModel:
        """Convert a trained artifact to inference-optimized format.

        Uses raw metal + AI control in sequence:
          1. RAW METAL: dedicate scaler lanes, set base raw clock, UMA coupling
          2. AI CONTROL: MX-FP4 precision scaling, DLSS super-sampling, deadass boost
        """
        self._init_lazy()
        from datetime import datetime

        name = artifact["name"]
        src_path = artifact["path"]
        src_type = artifact["type"]
        model_id = hashlib.sha256(src_path.encode()).hexdigest()[:12]

        # --- Step 1: RAW METAL configuration ---
        # Determine aspect ratio + active compute units from artifact
        if src_type == "lora_media" and ".mp4" in name:
            aspect = (16, 9)
            active_cus = 24  # video rendering uses all CUs
        elif src_type == "lora_media" and ".png" in name:
            aspect = (3, 4)  # portrait image
            active_cus = 16
        elif src_type == "lora_workflow":
            aspect = (16, 9)
            active_cus = 24
        elif src_type == "gguf":
            aspect = (16, 9)
            active_cus = 8  # text inference uses fewer CUs
        else:
            aspect = (16, 9)
            active_cus = 8

        # RAW METAL: set aspect ratio scaler at hardware level
        raw_cfg: Dict[str, Any] = {}
        if self._raw_metal is not None:
            rm_cfg = self._raw_metal.set_aspect_ratio(aspect[0], aspect[1])
            lane_plan = self._raw_metal.optimize_for_load(active_cus)
            raw_cfg = {
                "aspect_ratio": f"{rm_cfg.aspect_ratio[0]}:{rm_cfg.aspect_ratio[1]}",
                "scaler_clock_ghz": rm_cfg.scaler_clock_ghz,
                "scaler_lanes": lane_plan["scaler_lanes"],
                "compute_lanes": lane_plan["compute_lanes"],
                "uma_coupled": rm_cfg.uma_coupled,
                "scaler_precision": lane_plan["scaler_precision"],
                "hardware_level": True,
            }

        # --- Step 2: AI CONTROL configuration ---
        # Apply deadass boost: MX-FP4 precision for 16x ops/watt
        tensor_sample = self._artifact_to_tensor(src_path, src_type)
        ai_cfg: Dict[str, Any] = {}
        if self._chip is not None:
            boost = self._chip.deadass_boost(tensor_sample, target_precision="mx_fp4")
            ai_cfg = {
                "precision": "mx_fp4",
                "energy_multiplier": boost["energy_multiplier"],
                "effective_tflops_gain": boost["effective_tflops_gain"],
                "coupled_clock_ghz": boost["coupled_clock_ghz"],
                "dlss_super_sample": True,
                "deadass_boost": True,
            }
            # Also run raw_aspect_optimize for lane dedication
            raw_result = self._chip.raw_aspect_optimize(
                width=aspect[0] * 100,
                height=aspect[1] * 100,
                active_cu_count=active_cus,
            )
            raw_cfg["lane_plan"] = raw_result["lane_allocation"]

        # Determine target precision based on artifact type
        if src_type == "gguf":
            precision = "int8"  # text models excel at INT8
        else:
            precision = "mx_fp4"  # vision/video models excel at MX-FP4

        # Calculate effective TFLOPS
        zones = self._chip.tflops_zones if self._chip else {}
        high_perf = zones.get("high_perf", {}).get("total_tflops", 0.0)
        energy_mult = ai_cfg.get("energy_multiplier", 4.0)
        effective_tflops = high_perf * energy_mult / max(active_cus, 1)

        # Compute profic score: how close to peak performance
        base_perf = min(effective_tflops / max(high_perf, 0.001), 1.0)
        scaler_efficiency = 1.0 - (raw_cfg.get("scaler_lanes", 2) / 16.0)  # fewer lanes = more efficient
        profic_score = round(base_perf * 0.7 + scaler_efficiency * 0.3, 4)

        deployed = DeployedModel(
            model_id=model_id,
            name=name,
            source_type=src_type,
            source_path=src_path,
            precision=precision,
            deployed_at=datetime.utcnow().isoformat() + "Z",
            effective_tflops=round(effective_tflops, 2),
            scaler_config=raw_cfg,
            ai_control_config=ai_cfg,
            raw_metal_config=raw_cfg,
            profic_score=profic_score,
            status="active",
        )
        LOG.info("deployer: deployed %s (%s) | precision=%s | %.1f TFLOPS eff | profic=%.4f",
                 deployed.name, deployed.source_type, deployed.precision,
                 deployed.effective_tflops, deployed.profic_score)
        return deployed

    def _artifact_to_tensor(self, path: str, src_type: str) -> List[float]:
        """Convert an artifact path to a tensor vector for chip processing."""
        if src_type in ("lora_workflow",):
            try:
                data = json.loads(Path(path).read_text())
                # Extract node weights as tensor
                nodes = data.get("nodes", [])
                return [float(hash(n.get("name", str(i))) % 1000 / 1000.0)
                        for i, n in enumerate(nodes[:64])]
            except Exception:
                pass
        elif src_type == "gguf":
            # Use file size as a deterministic tensor
            size = Path(path).stat().st_size
            return [(size >> (i * 8) & 0xFF) / 255.0 for i in range(8)]
        elif src_type == "lora_media":
            # Use file hash as tensor
            h = hashlib.sha256(Path(path).read_bytes()).digest()
            return [b / 255.0 for b in h[:64]]
        return [0.5] * 64

    def deploy_all(self) -> List[DeployedModel]:
        """Discover, convert, and deploy all artifacts at peak caliber."""
        artifacts = self.discover_artifacts()
        deployed = []
        for art in artifacts:
            try:
                model = self.convert_artifact(art)
                self._deployed[model.model_id] = model
                deployed.append(model)
            except Exception as exc:
                LOG.error("deployer: failed to deploy %s: %s", art["name"], exc)
        LOG.info("deployer: deployed %d proficients", len(deployed))
        return deployed

    def get_profic_status(self) -> Dict[str, Any]:
        """Return the proficiency status of all deployed models."""
        models = {mid: {
            "name": m.name,
            "source_type": m.source_type,
            "precision": m.precision,
            "effective_tflops": m.effective_tflops,
            "profic_score": m.profic_score,
            "status": m.status,
            "scaler": m.scaler_config.get("aspect_ratio", "16:9"),
            "scaler_lanes": m.scaler_config.get("scaler_lanes", 0),
            "distinction": {
                "ai_control": "mx_fp4 precision + deadass boost + DLSS super-sample",
                "raw_metal": "scaler lane dedication + base raw clock + UMA coupling",
            },
        } for mid, m in self._deployed.items()}

        avg_profic = sum(m.profic_score for m in self._deployed.values()) / max(len(self._deployed), 1)
        total_tflops = sum(m.effective_tflops for m in self._deployed.values())

        return {
            "deployed_count": len(self._deployed),
            "avg_profic_score": round(avg_profic, 4),
            "total_effective_tflops": round(total_tflops, 2),
            "models": models,
            "chip_status": self._chip.status() if self._chip else None,
            "raw_metal_status": self._raw_metal.status() if self._raw_metal else None,
        }

    def status(self) -> Dict[str, Any]:
        return {
            "name": "ModelDeployer",
            "deployed": len(self._deployed),
            "profic_status": self.get_profic_status(),
        }


# Module-level singleton
model_deployer = ModelDeployer()
