#!/usr/bin/env python3
"""
QB Protocol - Unified Model Registry
Credential-safe inventory of all local and remote model providers.
NO secrets are stored here — credentials live in environment variables only.
"""
import os
import json
import uuid
import logging
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

LOG = logging.getLogger("qb_protocol.model_registry")

REGISTRY_STATE_PATH = Path.home() / ".qb_protocol_model_registry.json"


@dataclass
class ModelProvider:
    provider_id: str
    name: str
    category: str  # local_gguf, local_app, openai, anthropic, nemotron, vercel, custom
    type: str      # llm, embedding, vision, audio, mcp, api
    status: str    # available, configured, unconfigured, discovered
    endpoint: Optional[str] = None
    credential_env_vars: List[str] = field(default_factory=list)  # names only, never values
    models: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_seen: str = ""

    def to_safe_dict(self) -> Dict[str, Any]:
        """Return dict with credential status but never credential values."""
        d = asdict(self)
        creds = {}
        for var in self.credential_env_vars:
            val = os.environ.get(var)
            creds[var] = {"configured": bool(val), "length": len(val) if val else 0}
        d["credentials"] = creds
        # never expose raw env refs that might contain values in metadata
        return d


class ModelRegistry:
    """Unified registry across all model categories on this device."""

    def __init__(self):
        self._lock = threading.RLock()
        self._providers: Dict[str, ModelProvider] = {}
        self._load_state()
        self._discover_builtin()

    def _load_state(self):
        if REGISTRY_STATE_PATH.exists():
            try:
                with open(REGISTRY_STATE_PATH, "r") as f:
                    data = json.load(f)
                for pid, p in data.get("providers", {}).items():
                    self._providers[pid] = ModelProvider(**p)
            except Exception as e:
                LOG.warning("Failed to load registry state: %s", e)

    def _save_state(self):
        try:
            safe = {pid: asdict(p) for pid, p in self._providers.items()}
            with open(REGISTRY_STATE_PATH, "w") as f:
                json.dump({"providers": safe, "updated": datetime.utcnow().isoformat() + "Z"}, f, indent=2)
        except Exception as e:
            LOG.warning("Failed to save registry state: %s", e)

    def _add_or_update(self, provider: ModelProvider):
        with self._lock:
            existing = self._providers.get(provider.provider_id)
            if existing:
                # preserve user metadata but update discovered fields
                existing.last_seen = provider.last_seen
                existing.status = provider.status
                if provider.models:
                    existing.models = provider.models
                if provider.endpoint and not existing.endpoint:
                    existing.endpoint = provider.endpoint
                for v in provider.credential_env_vars:
                    if v not in existing.credential_env_vars:
                        existing.credential_env_vars.append(v)
            else:
                self._providers[provider.provider_id] = provider

    def _discover_builtin(self):
        now = datetime.utcnow().isoformat() + "Z"
        # --- Local GGUF: qb_protocol/models ---
        qb_models = Path("/Users/jjmarte/delta-stream/qb_protocol/models")
        if qb_models.exists():
            models = []
            for p in qb_models.rglob("*.gguf"):
                if p.is_file() and p.stat().st_size > 1024:
                    models.append({"name": p.name, "path": str(p), "size_mb": round(p.stat().st_size/(1024*1024), 2), "format": "gguf"})
            self._add_or_update(ModelProvider(
                provider_id="local-qbprotocol",
                name="QB Protocol Local Models",
                category="local_gguf",
                type="llm",
                status="available" if models else "discovered",
                endpoint="http://127.0.0.1:17760/ai/query",
                models=models,
                metadata={"source": "qb_protocol/models"},
                last_seen=now,
            ))

        # --- Local GGUF: GNU 3.4 / AlienWare ---
        gnu_dir = Path("/Users/jjmarte/speed/Gnu-3.4-console-edition/alien ware/gnu 3.4")
        if gnu_dir.exists():
            models = []
            for p in sorted(gnu_dir.glob("*.gguf")):
                if p.is_file():
                    sz = p.stat().st_size
                    models.append({
                        "name": p.name,
                        "path": str(p),
                        "size_bytes": sz,
                        "size_mb": round(sz/(1024*1024), 4),
                        "format": "gguf",
                        "note": "stub/small" if sz < 1024*1024 else "weight_file",
                    })
            self._add_or_update(ModelProvider(
                provider_id="local-gnu34",
                name="GNU 3.4 AlienWare Models",
                category="local_gguf",
                type="llm",
                status="discovered" if models else "unconfigured",
                models=models,
                metadata={"source": str(gnu_dir), "registry_pattern": "*_registry.json"},
                last_seen=now,
            ))

        # --- OpenAI / ChatGPT (via MCP config in NOVIAN) ---
        novian_mcp = Path("/Applications/-NOVIAN-AI/config/mcp_chatgpt.json")
        openai_status = "configured" if os.environ.get("OPENAI_API_KEY") else "unconfigured"
        self._add_or_update(ModelProvider(
            provider_id="openai-chatgpt",
            name="OpenAI / ChatGPT",
            category="openai",
            type="llm",
            status=openai_status,
            endpoint="https://api.openai.com/v1",
            credential_env_vars=["OPENAI_API_KEY"],
            models=[
                {"name": "gpt-4", "type": "chat", "source": "mcp_config" if novian_mcp.exists() else "api"},
                {"name": "gpt-4o", "type": "chat", "source": "api"},
                {"name": "gpt-4o-mini", "type": "chat", "source": "api"},
            ],
            metadata={"mcp_config": str(novian_mcp) if novian_mcp.exists() else None, "app": "NOVIAN-AI / BEING OMEGA PRIM E"},
            last_seen=now,
        ))

        # --- Anthropic / Claude ---
        claude_status = "configured" if (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")) else "unconfigured"
        self._add_or_update(ModelProvider(
            provider_id="anthropic-claude",
            name="Anthropic Claude",
            category="anthropic",
            type="llm",
            status=claude_status,
            endpoint="https://api.anthropic.com/v1",
            credential_env_vars=["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
            models=[
                {"name": "claude-opus-4", "type": "chat"},
                {"name": "claude-sonnet-4", "type": "chat"},
                {"name": "claude-haiku-4", "type": "chat"},
            ],
            last_seen=now,
        ))

        # --- NVIDIA Nemotron (API/provider placeholder) ---
        nemotron_status = "configured" if os.environ.get("NVIDIA_API_KEY") else "unconfigured"
        self._add_or_update(ModelProvider(
            provider_id="nvidia-nemotron",
            name="NVIDIA Nemotron",
            category="nemotron",
            type="llm",
            status=nemotron_status,
            endpoint="https://integrate.api.nvidia.com/v1",
            credential_env_vars=["NVIDIA_API_KEY", "NGC_API_KEY"],
            models=[
                {"name": "nemotron-4-340b-instruct", "type": "chat"},
                {"name": "nemotron-mini", "type": "chat"},
            ],
            last_seen=now,
        ))

        # --- HuggingFace (token present in env per .env pattern, status from env) ---
        hf_status = "configured" if os.environ.get("HF_TOKEN") else "unconfigured"
        self._add_or_update(ModelProvider(
            provider_id="huggingface",
            name="HuggingFace Hub",
            category="huggingface",
            type="api",
            status=hf_status,
            endpoint="https://huggingface.co/api",
            credential_env_vars=["HF_TOKEN", "HF_NAMESPACE"],
            models=[],
            metadata={"namespace_env": "HF_NAMESPACE"},
            last_seen=now,
        ))

        # --- Argon-VC / Vercel Portal ---
        self._add_or_update(ModelProvider(
            provider_id="argon-vc-portal",
            name="Argon-VC Vercel Portal",
            category="vercel",
            type="api",
            status="available",
            endpoint=os.environ.get("ARGON_VERCEL_URL", "https://arvc-indol.vercel.app"),
            credential_env_vars=["ARGON_BACKEND_URL", "ARGON_VERCEL_URL", "ARGON_API_TOKEN"],
            models=[],
            metadata={"repo": "https://github.com/4v2b2c65py-arch-JJ/Argon-VC.git", "local_backend": "http://127.0.0.1:17760"},
            last_seen=now,
        ))

        self._save_state()

    def register_provider(self, data: Dict[str, Any]) -> ModelProvider:
        pid = data.get("provider_id") or str(uuid.uuid4())
        provider = ModelProvider(
            provider_id=pid,
            name=data.get("name", "Unknown"),
            category=data.get("category", "custom"),
            type=data.get("type", "llm"),
            status=data.get("status", "discovered"),
            endpoint=data.get("endpoint"),
            credential_env_vars=data.get("credential_env_vars", []),
            models=data.get("models", []),
            metadata=data.get("metadata", {}),
            last_seen=datetime.utcnow().isoformat() + "Z",
        )
        self._add_or_update(provider)
        self._save_state()
        return provider

    def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        p = self._providers.get(provider_id)
        return p.to_safe_dict() if p else None

    def list_providers(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        providers = list(self._providers.values())
        if category:
            providers = [p for p in providers if p.category == category]
        return [p.to_safe_dict() for p in providers]

    def get_all_models(self) -> List[Dict[str, Any]]:
        models = []
        for p in self._providers.values():
            for m in p.models:
                models.append({**m, "provider_id": p.provider_id, "provider_name": p.name, "category": p.category})
        return models

    def rescan(self) -> Dict[str, Any]:
        self._discover_builtin()
        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        categories = {}
        for p in self._providers.values():
            categories[p.category] = categories.get(p.category, 0) + 1
        return {
            "total_providers": len(self._providers),
            "total_models": len(self.get_all_models()),
            "categories": categories,
            "credential_safe": True,
            "state_path": str(REGISTRY_STATE_PATH),
        }


model_registry = ModelRegistry()
