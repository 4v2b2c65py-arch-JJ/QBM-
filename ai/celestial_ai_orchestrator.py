#!/usr/bin/env python3
"""
QB Protocol - Celestial AI Orchestrator
Unified orchestrator merging hardware layer, model ensemble,
and celestial routing into a single anomalous-event-curve dispatch.
"""

import os
import sys
import time
import uuid
import json
import logging
import threading
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import deque

LOG = logging.getLogger("qb_protocol.celestial_ai_orchestrator")

ORCHESTRATOR_STATE_PATH = Path.home() / ".qb_protocol_celestial_ai_orchestrator.json"
MAX_ORCHESTRATOR_HISTORY = 1000


@dataclass
class DimensionalDispatch:
    dispatch_id: str
    dimension_id: str
    model_id: str
    hardware_profile: str
    prompt_hash: str
    event_curve: List[float]
    latency_ns: float
    status: str
    timestamp: str


class CelestialAIOrchestrator:
    """Unified orchestrator for AI, hardware, and celestial routing."""

    def __init__(self):
        self._lock = threading.RLock()
        self._dispatches: Dict[str, DimensionalDispatch] = {}
        self._dispatch_history: deque = deque(maxlen=MAX_ORCHESTRATOR_HISTORY)
        self._load_state()

    def _load_state(self):
        if ORCHESTRATOR_STATE_PATH.exists():
            try:
                with open(ORCHESTRATOR_STATE_PATH, "r") as f:
                    data = json.load(f)
                for did, d in data.get("dispatches", {}).items():
                    self._dispatches[did] = DimensionalDispatch(**d)
            except Exception:
                pass

    def _save_state(self):
        try:
            with open(ORCHESTRATOR_STATE_PATH, "w") as f:
                json.dump({
                    "dispatches": {did: asdict(d) for did, d in self._dispatches.items()},
                }, f, indent=2, default=str)
        except Exception:
            pass

    def _get_event_curve(self, prompt: str, dimension_id: str) -> List[float]:
        seed = f"{prompt}:{dimension_id}:{time.time()}"
        curve = []
        current = 0.0
        for i in range(8):
            value = (hash(seed + str(i)) % 1000) / 1000.0
            current = (current + value) / 2.0
            curve.append(round(current, 6))
        return curve

    def _expand_hardware_for_dimension(self, dimension_id: str) -> Dict[str, Any]:
        hardware_result = {}
        try:
            from qb_protocol.ai.hardware_layer import mac_hardware_layer
            hardware_result = mac_hardware_layer.expand_power_envelope()
            hardware_result["dimension_id"] = dimension_id
        except Exception as exc:
            hardware_result = {"dimension_id": dimension_id, "error": str(exc), "actions_taken": [], "actions_pending_sudo": []}
        
        try:
            from qb_protocol.ai.cpu_boost import cpu_boost_controller
            boost_result = cpu_boost_controller.trigger_boost()
            hardware_result["cpu_boost"] = boost_result
        except Exception as exc:
            hardware_result["cpu_boost_error"] = str(exc)
        
        return hardware_result

    def _get_ensemble_models(self) -> List[Dict[str, Any]]:
        try:
            from qb_protocol.ai.model_ensemble import model_ensemble
            return model_ensemble.get_status().get("models", [])
        except Exception:
            return []

    def _select_model_for_dimension(self, dimension_id: str, prompt: str) -> Optional[Dict[str, Any]]:
        models = self._get_ensemble_models()
        if not models:
            return None
        prompt_hash = hash(prompt) % len(models)
        return models[prompt_hash]

    def dispatch_query(self, prompt: str, max_tokens: int = 512, temperature: float = 0.8) -> Dict[str, Any]:
        start = time.time()
        try:
            from qb_protocol.communication.celestial_router import celestial_router
            dimensions = celestial_router.get_dimensions()
            if not dimensions:
                dimension_id = str(uuid.uuid4())
                celestial_router.register_dimension(
                    name="default_ai_dimension",
                    coordinates={"x": 0.0, "y": 0.0, "z": 0.0},
                    universe="earth",
                    stability=1.0,
                )
                dimensions = celestial_router.get_dimensions()
            dimension = dimensions[0]
            dimension_id = dimension.get("dimension_id")
        except Exception:
            dimension_id = str(uuid.uuid4())
        
        hardware_result = self._expand_hardware_for_dimension(dimension_id)
        selected_model = self._select_model_for_dimension(dimension_id, prompt)
        event_curve = self._get_event_curve(prompt, dimension_id)
        dispatch = DimensionalDispatch(
            dispatch_id=str(uuid.uuid4()),
            dimension_id=dimension_id,
            model_id=selected_model.get("model_id") if selected_model else None,
            hardware_profile="expanded",
            prompt_hash=str(hash(prompt)),
            event_curve=event_curve,
            latency_ns=0.0,
            status="dispatched",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
        with self._lock:
            self._dispatches[dispatch.dispatch_id] = dispatch
            self._dispatch_history.append(dispatch)
        self._save_state()
        
        if selected_model and selected_model.get("loaded"):
            try:
                from qb_protocol.ai.model_ensemble import model_ensemble
                inference = model_ensemble.ensemble_infer(prompt, max_tokens=max_tokens, temperature=temperature)
                dispatch.status = "completed"
                end = time.time()
                dispatch.latency_ns = (end - start) * 1_000_000_000
                self._save_state()
                return {
                    "dispatch_id": dispatch.dispatch_id,
                    "dimension_id": dimension_id,
                    "model_id": dispatch.model_id,
                    "response": inference.get("combined_response", ""),
                    "event_curve": event_curve,
                    "hardware_expansion": hardware_result,
                    "latency_ns": dispatch.latency_ns,
                    "status": "completed",
                }
            except Exception as exc:
                dispatch.status = "error"
                self._save_state()
                return {
                    "dispatch_id": dispatch.dispatch_id,
                    "dimension_id": dimension_id,
                    "error": str(exc),
                    "event_curve": event_curve,
                    "hardware_expansion": hardware_result,
                    "status": "error",
                }
        else:
            try:
                from qb_protocol.ai.gpt_layer import gpt_layer
                result = gpt_layer.query(prompt, max_tokens=max_tokens, temperature=temperature)
                dispatch.status = "completed"
                end = time.time()
                dispatch.latency_ns = (end - start) * 1_000_000_000
                self._save_state()
                return {
                    "dispatch_id": dispatch.dispatch_id,
                    "dimension_id": dimension_id,
                    "model_id": dispatch.model_id,
                    "response": result.get("response", ""),
                    "event_curve": event_curve,
                    "hardware_expansion": hardware_result,
                    "latency_ns": dispatch.latency_ns,
                    "status": "completed",
                }
            except Exception as exc:
                dispatch.status = "error"
                self._save_state()
                return {
                    "dispatch_id": dispatch.dispatch_id,
                    "dimension_id": dimension_id,
                    "error": str(exc),
                    "event_curve": event_curve,
                    "hardware_expansion": hardware_result,
                    "status": "error",
                }

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            recent = list(self._dispatch_history)[-10:]
            return {
                "total_dispatches": len(self._dispatches),
                "recent_dispatches": len(recent),
                "orchestrator_state_path": str(ORCHESTRATOR_STATE_PATH),
                "recent_status": [asdict(d) for d in recent],
            }


celestial_ai_orchestrator = CelestialAIOrchestrator()
