#!/usr/bin/env python3
"""
Argon API Auto-Provisioner (credential-safe)
Automatically provisions Argon-compatible API access across ALL model subsets
(local GGUF, Nemotron, Claude/Anthropic, OpenAI/GPT/Verios-class, HuggingFace, custom)
without storing secrets. Credentials remain in env vars only.
"""
import os, json, threading, urllib.request
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from datetime import datetime

PROVISION_PATH = Path.home() / ".qb_protocol_argon_provision.json"

# Broad-spectrum subset mapping (Argon API is one subset among many)
SUBSET_DEFS = {
    "argon":    {"label": "Argon / Vercel portal", "categories": ["vercel","custom"], "endpoints": ["/model/status","/mcp/route","/models/registry","/node/directive","/pool/status","/usage/pricing"]},
    "local":    {"label": "Local GGUF/ensemble",   "categories": ["local_gguf","local_app"]},
    "openai":   {"label": "OpenAI / GPT / Verios-class", "categories": ["openai"]},
    "anthropic":{"label": "Anthropic / Claude",    "categories": ["anthropic"]},
    "nemotron": {"label": "NVIDIA Nemotron",       "categories": ["nemotron"]},
    "huggingface":{"label":"HuggingFace",          "categories": ["huggingface"]},
    "all":      {"label": "Broad spectrum (all subsets)", "categories": ["*"]},
}

@dataclass
class ProvisionRecord:
    provider_id: str
    subset: str
    enabled: bool
    api_base: str
    auto_provisioned: bool
    credential_env_vars: List[str] = field(default_factory=list)
    configured: bool = False
    last_provision: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

class ArgonProvisioner:
    def __init__(self, registry):
        self._lock = threading.RLock()
        self._registry = registry
        self._records: Dict[str, ProvisionRecord] = {}
        self._load()
        self.auto_provision()

    def _load(self):
        if PROVISION_PATH.exists():
            try:
                data = json.loads(PROVISION_PATH.read_text())
                for k,v in data.get("records",{}).items():
                    self._records[k] = ProvisionRecord(**v)
            except Exception: pass

    def _save(self):
        try:
            PROVISION_PATH.write_text(json.dumps({"records":{k:asdict(v) for k,v in self._records.items()}, "updated": datetime.utcnow().isoformat()+"Z"}, indent=2))
        except Exception: pass

    def _subset_for(self, category: str) -> str:
        for s,d in SUBSET_DEFS.items():
            if s=="all": continue
            if category in d["categories"]: return s
        return "argon" if category in ("vercel","custom") else "all"

    def auto_provision(self) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()+"Z"
        backend = os.environ.get("ARGON_BACKEND_URL","http://127.0.0.1:17760").rstrip("/")
        vercel = os.environ.get("ARGON_VERCEL_URL","https://arvc-indol.vercel.app")
        providers = self._registry.list_providers() if self._registry else []
        out = []
        with self._lock:
            for p in providers:
                pid = p["provider_id"]; cat = p.get("category","custom"); subset = self._subset_for(cat)
                # Argon API base: local bridge can front all subsets; vercel portal is the public Argon surface
                api_base = backend if cat in ("local_gguf","local_app") else (p.get("endpoint") or (vercel if cat=="vercel" else backend))
                configured = any((c.get("configured") for c in (p.get("credentials") or {}).values())) if p.get("credential_env_vars") else (cat in ("local_gguf","local_app","vercel","custom"))
                rec = ProvisionRecord(provider_id=pid, subset=subset, enabled=True, api_base=api_base, auto_provisioned=True,
                                      credential_env_vars=p.get("credential_env_vars") or [], configured=configured, last_provision=now,
                                      metadata={"name":p.get("name"),"category":cat,"bridge":backend,"portal":vercel})
                self._records[pid]=rec; out.append(asdict(rec))
            self._save()
        return {"auto_provisioned": len(out), "subsets": {k:v["label"] for k,v in SUBSET_DEFS.items()}, "records": out}

    def status(self) -> Dict[str, Any]:
        by = {}
        for r in self._records.values(): by.setdefault(r.subset, []).append(asdict(r))
        return {"total": len(self._records), "enabled": sum(1 for r in self._records.values() if r.enabled),
                "configured": sum(1 for r in self._records.values() if r.configured),
                "subsets": by, "definitions": SUBSET_DEFS, "path": str(PROVISION_PATH), "credential_safe": True}

    def records(self) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self._records.values()]

# Lazy singleton: registry wired on first use or via server startup
argon_provisioner = ArgonProvisioner(registry=None)
try:
    from qb_protocol.ai.model_registry import model_registry as _reg
    argon_provisioner._registry = _reg
    argon_provisioner.auto_provision()
except Exception:
    pass
