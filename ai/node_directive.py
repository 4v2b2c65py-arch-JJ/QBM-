#!/usr/bin/env python3
"""
QB Protocol - Node Directive Registry
Allows nodes to register/connect automatically with token-based auth.
No secrets stored; node tokens are hashed for verification.
"""
import os, json, uuid, hashlib, threading
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from datetime import datetime

NODES_PATH = Path.home() / ".qb_protocol_nodes.json"

def _hash_token(token: str) -> str:
    return hashlib.sha256((token or "").encode()).hexdigest()

@dataclass
class NodeRecord:
    node_id: str
    name: str
    endpoint: str
    capabilities: List[str] = field(default_factory=list)
    status: str = "active"
    token_hash: Optional[str] = None  # never store raw token
    created: str = ""
    last_seen: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_safe_dict(self):
        d = asdict(self)
        d["has_token"] = bool(self.token_hash)
        d.pop("token_hash", None)
        return d

class NodeDirective:
    def __init__(self):
        self._lock = threading.RLock()
        self._nodes: Dict[str, NodeRecord] = {}
        self._load()

    def _load(self):
        if NODES_PATH.exists():
            try:
                data = json.loads(NODES_PATH.read_text())
                for nid, n in data.get("nodes", {}).items():
                    self._nodes[nid] = NodeRecord(**n)
            except Exception:
                pass

    def _save(self):
        try:
            NODES_PATH.write_text(json.dumps({"nodes": {k: asdict(v) for k,v in self._nodes.items()}}, indent=2))
        except Exception:
            pass

    def register(self, body: Dict[str, Any]) -> Dict[str, Any]:
        name = str(body.get("name") or "node")
        endpoint = str(body.get("endpoint") or "")
        caps = body.get("capabilities") or []
        token = body.get("token") or os.environ.get("ARGON_NODE_TOKEN") or ""
        node_id = body.get("node_id") or str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        with self._lock:
            rec = self._nodes.get(node_id) or NodeRecord(node_id=node_id, name=name, endpoint=endpoint, created=now)
            rec.name = name; rec.endpoint = endpoint; rec.capabilities = caps if isinstance(caps, list) else []
            rec.status = "active"; rec.last_seen = now
            if token: rec.token_hash = _hash_token(token)
            rec.metadata.update({k:v for k,v in (body.get("metadata") or {}).items() if k not in ("token","secret","key","password")})
            self._nodes[node_id] = rec
            self._save()
        out = rec.to_safe_dict()
        # issue a token only if caller didn't provide one (shown once)
        if not body.get("token") and not os.environ.get("ARGON_NODE_TOKEN"):
            issued = uuid.uuid4().hex + uuid.uuid4().hex
            rec.token_hash = _hash_token(issued)
            self._save()
            out["issued_token_once"] = issued
            out["warning"] = "Store this token securely; it is not retrievable later."
        return out

    def heartbeat(self, node_id: str) -> Dict[str, Any]:
        with self._lock:
            rec = self._nodes.get(node_id)
            if not rec: return {"error": "node_not_found"}
            rec.last_seen = datetime.utcnow().isoformat() + "Z"
            rec.status = "active"
            self._save()
        return rec.to_safe_dict()

    def list_nodes(self) -> List[Dict[str, Any]]:
        return [n.to_safe_dict() for n in self._nodes.values()]

    def directive(self) -> Dict[str, Any]:
        return {
            "protocol": "argon-qb-bridge",
            "version": 2,
            "connect": {
                "backend": os.environ.get("ARGON_BACKEND_URL", "http://127.0.0.1:17760"),
                "vercel_portal": os.environ.get("ARGON_VERCEL_URL", "https://arvc-indol.vercel.app"),
                "headers": {"X-Protocol-Version": "2", "Authorization": "Bearer <ARGON_API_TOKEN>"},
            },
            "steps": [
                "GET /node/directive for connection info",
                "POST /node/register {name, endpoint, capabilities, token?}",
                "POST /node/{id}/heartbeat periodically",
                "Use /model/status, /mcp/route, /models/registry, /usage/pricing, /wallet/balance",
            ],
            "pricing": "/usage/pricing",
            "registry": "/models/registry",
            "no_credentials_in_git": True,
        }

node_directive = NodeDirective()
