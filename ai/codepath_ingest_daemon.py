#!/usr/bin/env python3
"""
Codepath Ingest Daemon (credential-safe, read-only)
- Regularly scans allowlisted driver/code roots (takes its time)
- Builds packets, stores recall refs + mesh shared data
- Maintains node "state of thought" summary notes (routes, rules, additions, main code lang)
- Keeps itself alive/active via heartbeat + self-reschedule (works under KeepAlive launchd)

No credentials. Read-only allowlist (QB_DRIVER_PATHS to extend).
"""
import os, json, time, uuid, hashlib, threading, traceback, collections
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

STATE_PATH = Path.home() / ".qb_protocol_codepath_ingest_state.json"
THOUGHT_PATH = Path.home() / ".qb_protocol_node_state_of_thought.json"
LOG_PATH = Path.home() / "Library/Logs/qb_protocol_codepath_ingest.log"

TEXT_EXTS = {".py",".js",".ts",".tsx",".jsx",".json",".md",".txt",".c",".cpp",".cc",".h",".hpp",".rs",".go",".java",".kt",".swift",".sh",".zsh",".yml",".yaml",".toml",".ini",".cfg",".glsl",".hlsl",".metal",".wgsl",".sql",".proto",".ipynb",".ps1",".bat"}
LANG_BY_EXT = {".py":"python",".js":"javascript",".ts":"typescript",".tsx":"typescript",".jsx":"javascript",".c":"c",".cpp":"c++",".cc":"c++",".h":"c/c++",".hpp":"c++",".rs":"rust",".go":"go",".java":"java",".kt":"kotlin",".swift":"swift",".sh":"shell",".zsh":"shell",".ps1":"powershell",".bat":"batch",".sql":"sql",".glsl":"glsl",".hlsl":"hlsl",".metal":"metal",".wgsl":"wgsl",".md":"markdown",".json":"json",".yml":"yaml",".yaml":"yaml",".toml":"toml"}
INTERVAL_S = max(60, int(os.environ.get("QB_CODEPATH_INGEST_INTERVAL_S", "900")))        # regular basis (default 15m)
BATCH_FILES = max(1, int(os.environ.get("QB_CODEPATH_INGEST_BATCH_FILES", "12")))       # take its time
SLEEP_PER_FILE_S = float(os.environ.get("QB_CODEPATH_INGEST_SLEEP_S", "0.35"))
MAX_BYTES_PER_FILE = max(4096, int(os.environ.get("QB_CODEPATH_INGEST_MAX_BYTES", "120000")))
MAX_FILES_PER_ROOT = max(50, int(os.environ.get("QB_CODEPATH_INGEST_MAX_FILES_ROOT", "800")))

def _now(): return datetime.utcnow().isoformat()+"Z"
def _log(msg: str):
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH,"a") as f: f.write(f"{_now()} {msg}\n")
    except Exception: pass

class CodepathIngestDaemon:
    def __init__(self):
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.state = self._load(STATE_PATH, {"cursor":{}, "stats":{"cycles":0,"files_ingested":0,"errors":0,"volume_total_seen":0}, "node_id":"local", "started": _now(), "last_heartbeat": None, "alive": False, "velocity":{}, "branch_plan":{}, "upstream_links":0})
        self.thought = self._load(THOUGHT_PATH, {"node_id":"local","updated":None,"main_code_lang":None,"langs":{},"routes":{},"rules":[],"new_additions":[],"summary_notes":[],"batches":[],"volume_index":{},"upstream_links":[]})

    def _load(self, path: Path, default: Dict[str,Any]) -> Dict[str,Any]:
        if path.exists():
            try: d=json.loads(path.read_text()); default.update(d); return default
            except Exception: pass
        return default

    def _save(self, path: Path, data: Dict[str,Any]):
        try: path.write_text(json.dumps(data, indent=2, default=str))
        except Exception: pass

    def _resolve(self):
        rec = pool = clock = None
        try:
            from qb_protocol.ai.codepath_recall import codepath_recall as rec
        except Exception: pass
        try:
            from qb_protocol.ai.mesh_pool import mesh_pool as pool
        except Exception: pass
        try:
            from qb_protocol.ai.global_clock import global_clock as clock
        except Exception: pass
        return rec, pool, clock

    def _discover_files(self, root: Path) -> List[Path]:
        files=[]
        if not root.exists(): return files
        for p in root.rglob("*"):
            if len(files) >= MAX_FILES_PER_ROOT: break
            try:
                if p.is_file() and p.suffix.lower() in TEXT_EXTS and ".venv" not in p.parts and "node_modules" not in p.parts and ".git" not in p.parts:
                    files.append(p)
            except Exception: pass
        return sorted(files)

    def _infer_lang(self, files: List[Dict[str,Any]]) -> Tuple[Optional[str], Dict[str,int]]:
        counts=collections.Counter()
        for f in files:
            ext = Path(f.get("path","" )).suffix.lower()
            if ext in LANG_BY_EXT: counts[LANG_BY_EXT[ext]] += 1
        return (counts.most_common(1)[0][0] if counts else None), dict(counts)

    def _update_thought(self, cycle: int, ingested: List[Dict[str,Any]], roots: List[str], errors: int):
        main, langs = self._infer_lang(ingested)
        if not main: main = self.thought.get("main_code_lang") or "python"
        # merge lang counts
        mlangs = collections.Counter(self.thought.get("langs") or {})
        mlangs.update(langs)
        # routes: stable codepath routes (dirs) remembered
        routes = self.thought.get("routes") or {}
        for f in ingested:
            p=f.get("path"); 
            if not p: continue
            route = str(Path(p).parent)
            routes[route] = {"last_seen": _now(), "recall": f.get("recall_key"), "sha256": f.get("sha256"), "lang": LANG_BY_EXT.get(Path(p).suffix.lower())}
        # keep bounded
        if len(routes) > 2000:
            routes = dict(list(routes.items())[-2000:])
        # derive rules/additions (state-of-thought notes for batch/bash rulesets)
        rules = self.thought.get("rules") or []
        base_rules = [
            "read_only_allowlisted_paths",
            "no_credentials_in_packets_or_git",
            "store_recall_refs_and_mesh_shared_data",
            "take_time_sleep_per_file",
            "remember_all_routes_incrementally",
            "branching_loop_count_x_velocity_volume",
            "link_new_additions_to_entire_volume_upstream_no_error",
            f"prefer_main_code_lang:{main}",
        ]
        for r in base_rules:
            if r not in rules: rules.append(r)
        additions = self.thought.get("new_additions") or []
        for f in ingested[-20:]:
            add = {"path": f.get("path"), "sha256": f.get("sha256"), "lang": LANG_BY_EXT.get(Path(Path(f.get("path","")).suffix.lower()).suffix if False else Path(f.get("path","" )).suffix.lower()), "ts": _now()}
            if f.get("path") and not any(a.get("path")==add["path"] and a.get("sha256")==add["sha256"] for a in additions[-200:]):
                additions.append(add)
        additions = additions[-500:]
        note = {"ts": _now(), "cycle": cycle, "ingested": len(ingested), "errors": errors, "roots": roots[:5], "main_code_lang": main, "langs": dict(collections.Counter(langs))}
        notes = (self.thought.get("summary_notes") or []) + [note]
        self.thought.update({"node_id": self.state.get("node_id","local"), "updated": _now(), "main_code_lang": main,
                             "langs": dict(mlangs), "routes": routes, "rules": rules[-100:], "new_additions": additions,
                             "summary_notes": notes[-300:]})
        self._save(THOUGHT_PATH, self.thought)

    def _velocity_x_volume(self, clock, root_counts: Dict[str,int]) -> Dict[str,Any]:
        # x velocity * volume: branch loop counts safely; keep upstream (never throw)
        vel = 1.0
        try:
            if clock:
                st = clock.status() if hasattr(clock,"status") else {}
                # use tick/perf-ish signals if present, else stable default
                vel = float(st.get("tick_rate") or st.get("velocity") or st.get("perf",{}).get("velocity") or 1.0)
        except Exception: pass
        try:
            vel = float(os.environ.get("QB_CODEPATH_VELOCITY_X", vel))
        except Exception: pass
        vel = max(0.25, min(vel if vel>0 else 1.0, 8.0))  # bounded
        volume = sum(int(v) for v in root_counts.values())
        # branching factor: more roots/volume => more branches but capped
        branches = max(1, min(len(root_counts) or 1, 8))
        per_root = {}
        for r, n in root_counts.items():
            share = (n / volume) if volume else (1.0 / max(1,len(root_counts)))
            # loop count for this branch = base * velocity * volume share, capped
            count = int(max(1, min(BATCH_FILES * vel * (0.5 + share * branches), max(1, n), 64)))
            per_root[r] = {"files": int(n), "loop_count": count, "share": round(share,4)}
        plan = {"x_velocity": round(vel,4), "volume": int(volume), "branches": branches, "per_root": per_root,
                "rule": "branching_loop_count = clamp(BATCH_FILES * x_velocity * (0.5 + share*branches),1,min(root_files,64))"}
        self.state["velocity"] = {"x": plan["x_velocity"], "ts": _now()}
        self.state["branch_plan"] = plan
        return plan

    def _link_upstream(self, ingested: List[Dict[str,Any]], cycle: int):
        # link new additions to entire volume index without error; keep upstream refs
        try:
            vol = self.thought.get("volume_index") or {}
            links = self.thought.get("upstream_links") or []
            for f in ingested:
                p=f.get("path"); sha=f.get("sha256");
                if not p: continue
                node = {"path":p, "sha256":sha, "recall_key":f.get("recall_key"), "lang": LANG_BY_EXT.get(Path(p).suffix.lower()), "cycle":cycle, "ts":_now()}
                vol[p] = {"sha256":sha, "recall_key":f.get("recall_key"), "size":f.get("size"), "cycle":cycle}
                if sha:
                    links.append({"sha256":sha, "path":p, "recall_key":f.get("recall_key"), "upstream":"volume_index"})
            # bounded
            if len(vol) > 20000:
                for k in list(vol.keys())[:-20000]: vol.pop(k,None)
            self.thought["volume_index"] = vol
            self.thought["upstream_links"] = links[-5000:]
            self.state["upstream_links"] = len(self.thought["upstream_links"])
            self.state["stats"]["volume_total_seen"] = len(vol)
        except Exception as e:
            _log(f"link_upstream soft error: {e}")

    def run_cycle(self) -> Dict[str,Any]:
        rec, pool, clock = self._resolve()
        if not rec:
            return {"error":"codepath_recall_unavailable"}
        roots = rec.allowed_roots()
        # discover volume first (bounded), then branch by x velocity * volume
        root_files={}; root_counts={}
        for root_s in roots:
            try:
                fs=self._discover_files(Path(root_s)); root_files[root_s]=fs; root_counts[root_s]=len(fs)
            except Exception as e:
                _log(f"discover error {root_s}: {e}"); root_files[root_s]=[]; root_counts[root_s]=0
        plan = self._velocity_x_volume(clock, root_counts)
        ingested=[]; errors=0
        for root_s in roots:
            files = root_files.get(root_s) or []
            branch = (plan.get("per_root") or {}).get(root_s) or {}
            loop_count = int(branch.get("loop_count") or BATCH_FILES)
            cursor = int((self.state.get("cursor") or {}).get(root_s, 0))
            batch = files[cursor: cursor + loop_count]
            (self.state.setdefault("cursor", {}))[root_s] = 0 if (cursor + loop_count) >= len(files) else (cursor + loop_count)
            for fp in batch:
                try:
                    pkt = rec.build_packet([str(fp)], node_id=self.state.get("node_id","local"), max_files=1, max_bytes_per_file=MAX_BYTES_PER_FILE)
                    rec.store_recall(pkt)
                    if pool:
                        pool.put_data({"key": pkt["recall_key"], "scope":"shared", "node_id": self.state.get("node_id","local"),
                                       "value": {"packet_id": pkt["packet_id"], "summary": pkt["summary"], "paths": [f.get("path") for f in pkt.get("files",[]) if f.get("path")], "branch": {"x_velocity": plan.get("x_velocity"), "volume": plan.get("volume")}}})
                    f0 = (pkt.get("files") or [{}])[0]
                    ingested.append({"path": f0.get("path") or str(fp), "sha256": f0.get("sha256"), "size": f0.get("size"), "recall_key": pkt.get("recall_key")})
                    self.state["stats"]["files_ingested"] = int(self.state["stats"].get("files_ingested",0))+1
                except Exception as e:
                    errors += 1; self.state["stats"]["errors"] = int(self.state["stats"].get("errors",0))+1
                    _log(f"ingest error {fp}: {e}")
                time.sleep(SLEEP_PER_FILE_S)  # take its time; keeps upstream responsive
        self._link_upstream(ingested, int(self.state["stats"].get("cycles",0))+1)
        self.state["stats"]["cycles"] = int(self.state["stats"].get("cycles",0))+1
        self.state["last_heartbeat"] = _now(); self.state["alive"] = True; self.state["last_cycle"] = _now()
        self.state["last_plan"] = {"x_velocity": plan.get("x_velocity"), "volume": plan.get("volume"), "branches": plan.get("branches"), "errors": errors}
        self._save(STATE_PATH, self.state)
        try: self._update_thought(int(self.state["stats"]["cycles"]), ingested, roots, errors)
        except Exception as e: _log(f"thought update soft error: {e}")
        res = {"cycle": self.state["stats"]["cycles"], "ingested": len(ingested), "errors": errors, "roots": roots,
               "x_velocity": plan.get("x_velocity"), "volume": plan.get("volume"), "branches": plan.get("branches"),
               "per_root_loops": {k:v.get("loop_count") for k,v in (plan.get("per_root") or {}).items()},
               "thought_updated": _now(), "main_code_lang": self.thought.get("main_code_lang"), "upstream_links": self.state.get("upstream_links")}
        _log(json.dumps(res, default=str))
        return res

    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._stop.clear()
        def loop():
            _log("ingest daemon started")
            while not self._stop.is_set():
                try: self.run_cycle()
                except Exception as e: _log(f"cycle exception: {e}\n{traceback.format_exc()}")
                self._stop.wait(INTERVAL_S)
            _log("ingest daemon stopped")
        self._thread = threading.Thread(target=loop, name="qb-codepath-ingest", daemon=True)
        self._thread.start()

    def status(self) -> Dict[str,Any]:
        t = self.thought or {}
        rules = list(t.get("rules") or [])
        notes = list(t.get("summary_notes") or [])
        adds = list(t.get("new_additions") or [])
        return {"alive": bool(self._thread and self._thread.is_alive()), "interval_s": INTERVAL_S, "batch_files": BATCH_FILES,
                "sleep_per_file_s": SLEEP_PER_FILE_S, "velocity": self.state.get("velocity"), "branch_plan": self.state.get("branch_plan"),
                "upstream_links": self.state.get("upstream_links",0), "state": self.state, "thought": {"main_code_lang": t.get("main_code_lang"),
                "langs": t.get("langs") or {}, "routes_count": len(t.get("routes") or {}), "volume_index_count": len(t.get("volume_index") or {}),
                "rules": rules[-12:], "additions_count": len(adds), "summary_notes": notes[-3:], "updated": t.get("updated")}}

codepath_ingest_daemon = CodepathIngestDaemon()
