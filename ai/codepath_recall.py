#!/usr/bin/env python3
"""
QB Protocol - Codepath Packet & Long-Term Recall (credential-safe)
Read-only, allowlisted access to driver/code paths; builds packets for
model consumption and stores codepath references for portal/mesh recall.
NO credentials, NO arbitrary path reads outside allowlist.
"""
import os, json, uuid, hashlib, threading
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from datetime import datetime

RECALL_PATH = Path.home() / ".qb_protocol_codepath_recall.json"
# Allowlisted roots (read-only). Add via env QB_DRIVER_PATHS (os.pathsep).
DEFAULT_ALLOWED = [
    Path("/Users/jjmarte/delta-stream/QBOX---opti"),
    Path("/Users/jjmarte/delta-stream/qb_protocol"),
    Path("/Users/jjmarte/delta-stream/newbladelib"),
]
TEXT_EXTS = {".py",".js",".ts",".tsx",".json",".md",".txt",".c",".cpp",".h",".hpp",".rs",".sh",".yml",".yaml",".toml",".ini",".cfg",".glsl",".hlsl",".metal"}

def _allowed_roots() -> List[Path]:
    roots = list(DEFAULT_ALLOWED)
    for p in os.environ.get("QB_DRIVER_PATHS","").split(os.pathsep):
        p = p.strip()
        if p: roots.append(Path(p).expanduser())
    return [r.resolve() for r in roots if r.exists()]

def _is_allowed(path: Path) -> bool:
    try:
        rp = path.resolve()
        return any(str(rp).startswith(str(r)+os.sep) or rp==r for r in _allowed_roots())
    except Exception:
        return False

def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

@dataclass
class CodepathPacket:
    packet_id: str
    created: str
    source_node: str
    root: str
    files: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    recall_key: Optional[str] = None
    portal_store_hint: Dict[str, Any] = field(default_factory=dict)

class CodepathRecall:
    def __init__(self):
        self._lock = threading.RLock()
        self._refs: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if RECALL_PATH.exists():
            try: self._refs = json.loads(RECALL_PATH.read_text()).get("refs",{})
            except Exception: self._refs = {}

    def _save(self):
        try:
            RECALL_PATH.write_text(json.dumps({"refs": dict(list(self._refs.items())[-2000:]), "updated": datetime.utcnow().isoformat()+"Z"}, indent=2))
        except Exception: pass

    def allowed_roots(self) -> List[str]:
        return [str(r) for r in _allowed_roots()]

    def list_path(self, rel_or_abs: str, max_items: int = 200) -> Dict[str, Any]:
        # Resolve against allowed roots; if abs, must be allowed.
        candidates = []
        p = Path(rel_or_abs).expanduser()
        if p.is_absolute():
            candidates = [p]
        else:
            candidates = [r / p for r in _allowed_roots()]
        target = None
        for c in candidates:
            if c.exists() and _is_allowed(c): target = c; break
        if not target: return {"error":"path_not_found_or_not_allowed","allowed_roots": self.allowed_roots()}
        items = []
        if target.is_file():
            st = target.stat()
            items.append({"name":target.name,"path":str(target),"type":"file","size":st.st_size,"ext":target.suffix.lower()})
        else:
            for ch in sorted(target.iterdir(), key=lambda x:(not x.is_dir(), x.name.lower()))[:max(1,min(max_items,1000))]:
                try:
                    st = ch.stat()
                    items.append({"name":ch.name,"path":str(ch),"type":"dir" if ch.is_dir() else "file","size":st.st_size if ch.is_file() else None,"ext":ch.suffix.lower() if ch.is_file() else None})
                except Exception: pass
        return {"root": str(target), "allowed": True, "items": items}

    def read_file(self, path: str, max_bytes: int = 200_000) -> Dict[str, Any]:
        p = Path(path).expanduser()
        if not p.is_absolute():
            for r in _allowed_roots():
                c = (r / p)
                if c.exists(): p = c; break
        if not p.exists() or not p.is_file(): return {"error":"file_not_found"}
        if not _is_allowed(p): return {"error":"path_not_allowed","allowed_roots": self.allowed_roots()}
        raw = p.read_bytes()
        truncated = len(raw) > max(1024, min(max_bytes, 2_000_000))
        data = raw[:max_bytes]
        is_text = p.suffix.lower() in TEXT_EXTS
        try:
            text = data.decode("utf-8", errors="replace") if is_text else None
        except Exception:
            text = None; is_text = False
        return {"path": str(p.resolve()), "name": p.name, "ext": p.suffix.lower(), "size": len(raw),
                "sha256": _sha256_bytes(raw), "is_text": is_text, "truncated": truncated,
                "text": text, "encoding": "utf-8" if is_text else "binary"}

    def build_packet(self, paths: List[str], node_id: str = "local", max_files: int = 50, max_bytes_per_file: int = 120_000) -> Dict[str, Any]:
        files = []
        for path in (paths or [])[:max(1,min(max_files,200))]:
            r = self.read_file(path, max_bytes=max_bytes_per_file)
            if "error" in r: files.append({"path": path, "error": r["error"]})
            else: files.append({k:v for k,v in r.items()})  # includes text for text files
        pkt = CodepathPacket(
            packet_id="pkt_"+uuid.uuid4().hex[:16],
            created=datetime.utcnow().isoformat()+"Z",
            source_node=node_id,
            root=",".join(self.allowed_roots()[:3]),
            files=files,
            summary={"files": len(files), "errors": sum(1 for f in files if "error" in f),
                     "text_files": sum(1 for f in files if f.get("is_text")), "total_bytes": sum(f.get("size",0) for f in files if isinstance(f.get("size"),int))},
            recall_key=None,
            portal_store_hint={"vercel_portal": os.environ.get("ARGON_VERCEL_URL","https://arvc-indol.vercel.app"),
                               "action":"POST packet.codepath_ref to portal storage backend when configured",
                               "endpoints":["/codepath/recall/store","/pool/data"], "credential_safe": True}
        )
        pkt.recall_key = "codepath:"+pkt.packet_id
        return asdict(pkt)

    def store_recall(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        key = packet.get("recall_key") or ("codepath:"+(packet.get("packet_id") or uuid.uuid4().hex[:16]))
        # Store ref + summary (not full text blobs by default) for long-term recall; full packet can live in pool data
        ref = {"recall_key": key, "packet_id": packet.get("packet_id"), "created": packet.get("created"),
               "source_node": packet.get("source_node"), "summary": packet.get("summary"), "paths": [f.get("path") for f in packet.get("files",[]) if f.get("path")],
               "portal_store_hint": packet.get("portal_store_hint"), "updated": datetime.utcnow().isoformat()+"Z"}
        with self._lock:
            self._refs[key] = ref; self._save()
        return ref

    def get_recall(self, key: str) -> Optional[Dict[str, Any]]:
        return self._refs.get(key)

    def list_recall(self, limit: int = 100) -> List[Dict[str, Any]]:
        return list(self._refs.values())[-max(1,min(limit,500)):]

codepath_recall = CodepathRecall()
