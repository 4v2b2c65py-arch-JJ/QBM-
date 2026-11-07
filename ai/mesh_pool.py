#!/usr/bin/env python3
"""
QB Protocol - Mesh Pool: user base, task queue, and shared data storage across nodes.
Enables multi-interconnected meshing and datapassage under node directive.
No credentials stored.
"""
import os, json, uuid, threading, hashlib, time
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from datetime import datetime

POOL_PATH = Path.home() / ".qb_protocol_mesh_pool.json"

def _hid(s: str) -> str:
    return hashlib.sha256((s or "").encode()).hexdigest()[:16]

@dataclass
class PoolUser:
    user_id: str
    label: str
    node_id: Optional[str] = None
    created: str = ""
    last_seen: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    def safe(self): return asdict(self)

@dataclass
class PoolTask:
    task_id: str
    user_id: Optional[str]
    origin_node: Optional[str]
    type: str
    payload: Dict[str, Any]
    status: str = "queued"  # queued|claimed|done|failed
    assigned_node: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created: str = ""
    updated: str = ""
    def safe(self): return asdict(self)

class MeshPool:
    def __init__(self):
        self._lock = threading.RLock()
        self._data = {"users": {}, "tasks": {}, "data": {}, "mesh_links": []}
        self._load()

    def _load(self):
        if POOL_PATH.exists():
            try: self._data.update(json.loads(POOL_PATH.read_text()))
            except Exception: pass
        for k in ("users","tasks","data","mesh_links"):
            self._data.setdefault(k, {} if k != "mesh_links" else [])

    def _save(self):
        try:
            # keep bounded
            tasks = list(self._data.get("tasks", {}).items())[-5000:]
            self._data["tasks"] = dict(tasks)
            self._data["data"] = dict(list(self._data.get("data", {}).items())[-2000:])
            POOL_PATH.write_text(json.dumps(self._data, indent=2, default=str))
        except Exception: pass

    def upsert_user(self, body: Dict[str, Any]) -> Dict[str, Any]:
        label = str(body.get("label") or body.get("email") or body.get("name") or "anonymous")
        uid = body.get("user_id") or ("u_" + _hid(label + ":" + (body.get("node_id") or "")))
        now = datetime.utcnow().isoformat() + "Z"
        with self._lock:
            u = self._data["users"].get(uid) or {"user_id": uid, "label": label, "created": now}
            u["label"] = label; u["node_id"] = body.get("node_id") or u.get("node_id")
            u["last_seen"] = now
            meta = body.get("metadata") or {}
            u["metadata"] = {**u.get("metadata",{}), **{k:v for k,v in meta.items() if k not in ("token","secret","key","password","authorization")}}
            self._data["users"][uid] = u; self._save()
        return u

    def append_task(self, body: Dict[str, Any]) -> Dict[str, Any]:
        tid = body.get("task_id") or ("t_" + uuid.uuid4().hex[:16])
        now = datetime.utcnow().isoformat() + "Z"
        task = {"task_id": tid, "user_id": body.get("user_id"), "origin_node": body.get("origin_node") or body.get("node_id"),
                "type": str(body.get("type") or "generic"), "payload": body.get("payload") or {}, "status":"queued",
                "assigned_node": None, "result": None, "created": now, "updated": now}
        with self._lock:
            self._data["tasks"][tid] = task; self._save()
        return task

    def claim_task(self, node_id: str, task_id: Optional[str]=None, task_type: Optional[str]=None) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat() + "Z"
        with self._lock:
            if task_id:
                t = self._data["tasks"].get(task_id)
                if not t: return {"error":"task_not_found"}
                if t["status"] != "queued": return {"error":"task_not_available","status":t["status"]}
                t["status"]="claimed"; t["assigned_node"]=node_id; t["updated"]=now; self._save(); return t
            for t in reversed(list(self._data["tasks"].values())):
                if t["status"]=="queued" and (not task_type or t["type"]==task_type):
                    t["status"]="claimed"; t["assigned_node"]=node_id; t["updated"]=now; self._save(); return t
        return {"status":"empty"}

    def complete_task(self, task_id: str, result: Dict[str, Any], status: str="done") -> Dict[str, Any]:
        now = datetime.utcnow().isoformat() + "Z"
        with self._lock:
            t = self._data["tasks"].get(task_id)
            if not t: return {"error":"task_not_found"}
            t["status"]=status if status in ("done","failed") else "done"; t["result"]=result; t["updated"]=now; self._save()
        return t

    def put_data(self, body: Dict[str, Any]) -> Dict[str, Any]:
        key = body.get("key") or ("d_" + uuid.uuid4().hex[:16])
        scope = str(body.get("scope") or "shared")  # shared|node|user
        now = datetime.utcnow().isoformat() + "Z"
        rec = {"key": key, "scope": scope, "owner_node": body.get("node_id"), "owner_user": body.get("user_id"),
               "value": body.get("value"), "updated": now, "version": int(body.get("version") or 1)}
        with self._lock:
            prev = self._data["data"].get(key)
            if prev: rec["version"] = int(prev.get("version",1))+1
            self._data["data"][key]=rec; self._save()
        return rec

    def get_data(self, key: str) -> Optional[Dict[str, Any]]:
        return self._data.get("data", {}).get(key)

    def list_data(self, scope: Optional[str]=None, limit: int=100) -> List[Dict[str, Any]]:
        vals = list(self._data.get("data", {}).values())
        if scope: vals = [v for v in vals if v.get("scope")==scope]
        return vals[-max(1,min(limit,500)):]

    def link_nodes(self, a: str, b: str, meta: Dict[str, Any]=None) -> Dict[str, Any]:
        link = {"a":a,"b":b,"ts":datetime.utcnow().isoformat()+"Z","meta":meta or {}}
        with self._lock:
            if not any((l.get("a")==a and l.get("b")==b) or (l.get("a")==b and l.get("b")==a) for l in self._data["mesh_links"]):
                self._data["mesh_links"].append(link); self._data["mesh_links"]=self._data["mesh_links"][-2000:]
                self._save()
        return link

    def status(self, nodes: List[Dict[str, Any]]=None) -> Dict[str, Any]:
        users = self._data.get("users", {}); tasks = self._data.get("tasks", {})
        queued = sum(1 for t in tasks.values() if t.get("status")=="queued")
        claimed = sum(1 for t in tasks.values() if t.get("status")=="claimed")
        return {
            "capturing_user_base": len(users) > 0,
            "users": len(users),
            "tasks_total": len(tasks), "tasks_queued": queued, "tasks_claimed": claimed,
            "data_objects": len(self._data.get("data", {})),
            "mesh_links": len(self._data.get("mesh_links", [])),
            "registered_nodes": len(nodes) if nodes is not None else None,
            "meshing_active": (len(nodes or []) > 1) or (len(self._data.get("mesh_links", [])) > 0),
            "directive_applies": True,
            "pool_path": str(POOL_PATH),
        }

mesh_pool = MeshPool()
