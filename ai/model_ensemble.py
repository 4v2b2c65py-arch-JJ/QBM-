#!/usr/bin/env python3
"""
QB Protocol - Unified Model Ensemble
Combines all available model files and configurations into a unified
inference layer that expands beyond single-model constraints.
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

LOG = logging.getLogger("qb_protocol.model_ensemble")

ENSEMBLE_STATE_PATH = Path.home() / ".qb_protocol_model_ensemble.json"
MAX_ENSEMBLE_HISTORY = 1000


@dataclass
class ModelEntry:
    model_id: str
    model_path: str
    model_type: str
    format: str
    size_mb: float
    config: Dict[str, Any]
    loaded: bool
    backend: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnsembleInference:
    inference_id: str
    model_ids: List[str]
    prompt: str
    responses: List[Dict[str, Any]]
    combined_response: str
    certainty_score: float
    latency_ms: float
    timestamp: str


class ModelEnsemble:
    """Unified model ensemble combining all available models."""

    def __init__(self):
        self._lock = threading.RLock()
        self._models: Dict[str, ModelEntry] = {}
        self._inferences: deque = deque(maxlen=MAX_ENSEMBLE_HISTORY)
        self._load_state()
        self._discover_models()

    def _load_state(self):
        if ENSEMBLE_STATE_PATH.exists():
            try:
                with open(ENSEMBLE_STATE_PATH, "r") as f:
                    data = json.load(f)
                seen_paths = set()
                for mid, m in data.get("models", {}).items():
                    path = m.get("model_path")
                    if path and path not in seen_paths:
                        seen_paths.add(path)
                        self._models[mid] = ModelEntry(**m)
            except Exception:
                pass

    def _save_state(self):
        try:
            with open(ENSEMBLE_STATE_PATH, "w") as f:
                json.dump({
                    "models": {mid: asdict(m) for mid, m in self._models.items()},
                }, f, indent=2, default=str)
        except Exception:
            pass

    def _discover_models(self):
        search_paths = [
            Path("/Users/jjmarte/delta-stream/qb_protocol/models"),
            Path("/Users/jjmarte/speed/Gnu-3.4-console-edition/alien ware/gnu 3.4"),
            Path("/Users/jjmarte/Downloads"),
            Path.home() / "Models",
            Path.home() / ".models",
        ]
        extra = os.environ.get("QB_MODEL_SEARCH_PATHS", "")
        for p in extra.split(os.pathsep):
            p = p.strip()
            if p:
                search_paths.append(Path(p))
        discovered = []
        for base in search_paths:
            if not base.exists():
                continue
            for ext in ["*.gguf", "*.safetensors", "*.bin", "*.pt", "*.pth", "*.onnx"]:
                for path in base.rglob(ext):
                    if path.is_file() and path.stat().st_size > 1024 * 1024:
                        discovered.append(path)
        for path in discovered:
            if any(m.model_path == str(path) for m in self._models.values()):
                continue
            model_id = str(uuid.uuid4())
            fmt = path.suffix.lower()
            name_lower = path.name.lower()
            if fmt == ".gguf" or ("tinyllama" in name_lower and "chat" in name_lower):
                model_type = "llm"
            elif fmt == ".pt" and ("stdit" in name_lower or "diffusion" in name_lower or "video" in name_lower):
                model_type = "video_diffusion"
            elif fmt in [".safetensors", ".bin"] and "gguf" not in name_lower:
                model_type = "other"
            else:
                model_type = "unknown"
            entry = ModelEntry(
                model_id=model_id,
                model_path=str(path),
                model_type=model_type,
                format=fmt,
                size_mb=round(path.stat().st_size / (1024 * 1024), 2),
                config={},
                loaded=False,
                backend="discovered",
                metadata={"discovered_at": datetime.utcnow().isoformat() + "Z"},
            )
            with self._lock:
                self._models[model_id] = entry
        if self._models:
            self._save_state()
            LOG.info("Discovered %d model files", len(self._models))

    def load_model(self, model_id: str) -> bool:
        entry = self._models.get(model_id)
        if not entry:
            return False
        try:
            if entry.format == ".gguf":
                from llama_cpp import Llama
                entry.config = {
                    "n_ctx": 8192,
                    "n_threads": 8,
                    "n_batch": 512,
                    "use_mmap": True,
                }
                model = Llama(
                    model_path=entry.model_path,
                    n_ctx=entry.config["n_ctx"],
                    n_threads=entry.config["n_threads"],
                    n_batch=entry.config["n_batch"],
                    use_mmap=entry.config["use_mmap"],
                )
                entry.loaded = True
                entry.backend = "llama-cpp"
            else:
                LOG.warning("Unsupported model format: %s", entry.format)
                return False
            self._save_state()
            LOG.info("Loaded model: %s", entry.model_path)
            return True
        except Exception as exc:
            LOG.warning("Failed to load model %s: %s", entry.model_path, exc)
            return False

    def ensemble_infer(self, prompt: str, max_tokens: int = 512, temperature: float = 0.8) -> Dict[str, Any]:
        inference_id = str(uuid.uuid4())
        responses = []
        total_latency = 0.0
        with self._lock:
            for entry in self._models.values():
                if not entry.loaded or entry.model_type != "llm":
                    continue
                start = time.time()
                try:
                    from llama_cpp import Llama
                    model = Llama(
                        model_path=entry.model_path,
                        n_ctx=entry.config.get("n_ctx", 4096),
                        n_threads=entry.config.get("n_threads", 4),
                        n_batch=entry.config.get("n_batch", 256),
                        use_mmap=entry.config.get("use_mmap", True),
                    )
                    formatted = f"<|user|>\n{prompt}</s>\n<|assistant|>\n"
                    result = model(formatted, max_tokens=max_tokens, temperature=temperature, stop=["</s>"])
                    text = result["choices"][0]["text"].strip()
                    latency = (time.time() - start) * 1000
                    responses.append({
                        "model_id": entry.model_id,
                        "model_path": entry.model_path,
                        "text": text,
                        "latency_ms": round(latency, 2),
                        "tokens": result.get("usage", {}).get("total_tokens", len(text.split())),
                    })
                    total_latency += latency
                except Exception as exc:
                    LOG.warning("Ensemble inference failed for %s: %s", entry.model_id, exc)
        combined = self._combine_responses(responses)
        certainty = self._calculate_certainty(responses)
        inference = EnsembleInference(
            inference_id=inference_id,
            model_ids=[r["model_id"] for r in responses],
            prompt=prompt,
            responses=responses,
            combined_response=combined,
            certainty_score=certainty,
            latency_ms=round(total_latency, 2),
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
        with self._lock:
            self._inferences.append(inference)
        self._save_state()
        return asdict(inference)

    def _combine_responses(self, responses: List[Dict[str, Any]]) -> str:
        if not responses:
            return ""
        seen = set()
        parts = []
        for r in responses:
            text = r.get("text", "").strip()
            if text and text not in seen:
                seen.add(text)
                parts.append(text)
        return "\n---\n".join(parts)

    def _calculate_certainty(self, responses: List[Dict[str, Any]]) -> float:
        if not responses:
            return 0.0
        texts = [r.get("text", "").strip() for r in responses if r.get("text")]
        if not texts:
            return 0.0
        lengths = [len(t) for t in texts]
        avg_len = sum(lengths) / len(lengths)
        variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
        consistency = max(0.0, 1.0 - (variance / max(avg_len, 1)))
        return round(min(1.0, consistency), 4)

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_models": len(self._models),
                "loaded_models": len([m for m in self._models.values() if m.loaded]),
                "llm_models": len([m for m in self._models.values() if m.model_type == "llm"]),
                "total_inferences": len(self._inferences),
                "models": [asdict(m) for m in self._models.values()],
            }


model_ensemble = ModelEnsemble()
