#!/usr/bin/env python3
"""
QB Protocol - X-Velocity Benchmark
Measures dispatch/routing/registry throughput from 1000x upward until limit.
Credential-safe: no secrets, no external calls required.
"""
import os, json, time, uuid, threading, statistics, platform
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime

BENCH_PATH = Path.home() / ".qb_protocol_velocity_benchmark.json"
DOC_PATH = Path(__file__).resolve().parent.parent / "docs" / "MODEL_SPEED_BENCHMARK.md"

def _now(): return datetime.utcnow().isoformat() + "Z"

class VelocityBenchmark:
    def __init__(self, registry=None, pool=None, wallet=None, provisioner=None):
        self._registry = registry
        self._pool = pool
        self._wallet = wallet
        self._provisioner = provisioner
        self._lock = threading.RLock()
        self._last: Optional[Dict[str, Any]] = None

    def _resolve(self):
        try:
            if not self._registry:
                from qb_protocol.ai.model_registry import model_registry; self._registry = model_registry
        except Exception: pass
        try:
            if not self._pool:
                from qb_protocol.ai.mesh_pool import mesh_pool; self._pool = mesh_pool
        except Exception: pass
        try:
            if not self._wallet:
                from qb_protocol.ai.usage_wallet import usage_wallet; self._wallet = usage_wallet
        except Exception: pass
        try:
            if not self._provisioner:
                from qb_protocol.ai.argon_provisioner import argon_provisioner; self._provisioner = argon_provisioner
        except Exception: pass

    def _op_registry_list(self):
        if self._registry: self._registry.get_all_models()

    def _op_registry_status(self):
        if self._registry: self._registry.get_status()

    def _op_pool_status(self):
        if self._pool: self._pool.status()

    def _op_pricing(self):
        if self._wallet: self._wallet.pricing()

    def _op_provision_status(self):
        if self._provisioner: self._provisioner.status()

    def _op_route_sim(self):
        # Simulate MCP route decision (no model inference/external call)
        if self._registry:
            models = self._registry.get_all_models()
            _ = [m.get("provider_id") for m in models[:64]]

    def _run_scale(self, op_name, fn, scale: int, max_seconds: float = 2.0) -> Dict[str, Any]:
        # warmup
        for _ in range(min(50, max(1, scale//20))): fn()
        t0 = time.perf_counter()
        n = 0
        deadline = t0 + max_seconds
        lat = []
        batch = min(256, max(1, scale // 10))
        while n < scale and time.perf_counter() < deadline:
            b0 = time.perf_counter()
            run = min(batch, scale - n)
            for _ in range(run): fn()
            b1 = time.perf_counter()
            n += run
            lat.append((b1-b0)*1000.0/run)
        t1 = time.perf_counter()
        elapsed = max(t1-t0, 1e-9)
        ops_sec = n / elapsed
        p95 = statistics.quantiles(lat, n=20)[18] if len(lat)>=20 else (max(lat) if lat else 0)
        return {"operation": op_name, "target_scale": scale, "completed": n, "elapsed_s": round(elapsed,6),
                "ops_per_sec": round(ops_sec,2), "avg_ms_per_op": round((elapsed*1000)/max(n,1),6),
                "p95_ms_per_op_batch": round(p95,6), "hit_target": n >= scale, "time_capped": n < scale}

    def run(self, start_x: int = 1000, multiplier: int = 2, max_x: int = 1_000_000, max_seconds_per_scale: float = 1.5) -> Dict[str, Any]:
        self._resolve()
        ops = [
            ("registry_list_models", self._op_registry_list),
            ("registry_status", self._op_registry_status),
            ("mesh_pool_status", self._op_pool_status),
            ("usage_pricing", self._op_pricing),
            ("argon_provision_status", self._op_provision_status),
            ("mcp_route_sim", self._op_route_sim),
        ]
        providers = self._registry.list_providers() if self._registry else []
        scales = []
        x = max(1, int(start_x))
        limit_found = False
        while x <= max_x:
            scale_res = {"x": x, "operations": []}
            any_capped = False
            for name, fn in ops:
                r = self._run_scale(name, fn, x, max_seconds=max_seconds_per_scale)
                scale_res["operations"].append(r)
                if r["time_capped"]: any_capped = True
            avg_ops = round(statistics.mean([o["ops_per_sec"] for o in scale_res["operations"]]), 2) if scale_res["operations"] else 0
            scale_res["avg_ops_per_sec"] = avg_ops
            scales.append(scale_res)
            if any_capped:
                limit_found = True
                scale_res["limit_note"] = f"Reached throughput/time cap around {x}x on this machine (time budget {max_seconds_per_scale}s/scale/op)."
                break
            x *= max(2, int(multiplier))
        peak = max((s["avg_ops_per_sec"] for s in scales), default=0)
        result = {
            "benchmark": "x_velocity",
            "timestamp": _now(),
            "machine": {"platform": platform.platform(), "python": platform.python_version(), "processor": platform.processor() or platform.machine()},
            "config": {"start_x": start_x, "multiplier": multiplier, "max_x": max_x, "max_seconds_per_scale": max_seconds_per_scale},
            "scales": scales,
            "limit_reached": limit_found,
            "peak_avg_ops_per_sec": peak,
            "providers_assessed": [self._assess_provider(p, peak) for p in providers],
            "dataset": self._dataset_snapshot(),
            "notes": [
                "Measures local dispatch/registry/routing/pricing/provision throughput (no credentials, no external model API calls).",
                "Actual LLM token generation speed depends on backend load, model size, and whether llama.cpp/ctransformers/remote API is used.",
                "GNU 3.4 entries are discovered; files <1MB are stubs and not benchmarked for inference.",
            ],
        }
        with self._lock:
            self._last = result
            try: BENCH_PATH.write_text(json.dumps(result, indent=2, default=str))
            except Exception: pass
        self._write_docs(result)
        return result

    def _assess_provider(self, p: Dict[str, Any], peak_ops: float) -> Dict[str, Any]:
        cat = p.get("category","custom"); models = p.get("models") or []
        real = [m for m in models if (m.get("size_mb") or 0) >= 1 or (m.get("size_bytes") or 0) >= 1048576]
        # dispatch throughput applies to routing/registry; inference is provider-specific
        if cat in ("local_gguf","local_app"):
            inf = "local_cpu_bound (ctransformers/llama.cpp when loaded); dispatch near measured peak"
            est = f"dispatch ~{int(peak_ops)} ops/s; token gen measured separately via loaded backend"
        elif cat in ("vercel","custom","argon"):
            inf = "bridge/portal dispatch (network-bound when remote tunnel used)"
            est = f"local dispatch ~{int(peak_ops)} ops/s; end-to-end adds tunnel+portal latency"
        else:
            inf = "remote API (network+provider-bound); credentials required via env vars"
            est = f"local dispatch ~{int(peak_ops)} ops/s; inference latency dominated by provider/network"
        return {"provider_id": p.get("provider_id"), "name": p.get("name"), "category": cat,
                "configured": any(c.get("configured") for c in (p.get("credentials") or {}).values()) if p.get("credential_env_vars") else (cat in ("local_gguf","vercel","custom")),
                "model_entries": len(models), "real_model_files_ge_1mb": len(real),
                "inference_path": inf, "speed_assessment": est}

    def _dataset_snapshot(self) -> Dict[str, Any]:
        snap = {"measured": _now(), "locations": []}
        for label, path in [("qb_protocol/models","/Users/jjmarte/delta-stream/qb_protocol/models"),
                            ("gnu34","/Users/jjmarte/speed/Gnu-3.4-console-edition/alien ware/gnu 3.4")]:
            pp = Path(path)
            if not pp.exists(): continue
            gg = list(pp.rglob("*.gguf"))
            real = [g for g in gg if g.is_file() and g.stat().st_size >= 1048576]
            total = sum(g.stat().st_size for g in gg if g.is_file())
            snap["locations"].append({"label":label,"path":path,"gguf_total":len(gg),"gguf_ge_1mb":len(real),
                                      "total_bytes":total,"total_human":f"{total/(1024**3):.3f} GB" if total>=1024**3 else f"{total/(1024**2):.2f} MB"})
        return snap

    def _write_docs(self, result: Dict[str, Any]):
        DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"# Model Speed & X-Velocity Benchmark", "", f"Generated: {result['timestamp']}", f"Machine: {result['machine']['platform']} | Python {result['machine']['python']} | {result['machine']['processor']}",
                 "", "## Method", "- X-velocity sweep: 1000x upward (x2) until throughput/time cap.", "- Measures local dispatch/registry/routing/pricing/provision ops (credential-safe; no external API calls).",
                 "- LLM token-generation speed is backend-dependent (llama.cpp/ctransformers/remote provider) and measured separately when a model is loaded.", "",
                 f"## Result", f"- Limit reached: **{result['limit_reached']}**", f"- Peak avg ops/sec (local dispatch): **{result['peak_avg_ops_per_sec']:,.2f}**", "",
                 "## Scale Table", "| X | Avg ops/sec | Sample ops | Notes |", "|---:|---:|---|---|"]
        for s in result["scales"]:
            ops = ", ".join([f"{o['operation']}={o['ops_per_sec']:,.0f}/s" for o in s["operations"][:3]])
            lines.append(f"| {s['x']} | {s['avg_ops_per_sec']:,.2f} | {ops} | {s.get('limit_note','ok')} |")
        lines += ["", "## Per-Provider Speed Assessment", "| Provider | Category | Configured | Models | Real >=1MB | Inference path | Assessment |", "|---|---|:---:|---:|---:|---|---|"]
        for p in result["providers_assessed"]:
            lines.append(f"| {p['name']} | {p['category']} | {'yes' if p['configured'] else 'no'} | {p['model_entries']} | {p['real_model_files_ge_1mb']} | {p['inference_path']} | {p['speed_assessment']} |")
        lines += ["", "## Dataset Footprint (this machine)", "| Location | GGUF total | >=1MB | Total size |", "|---|---:|---:|---:|"]
        for loc in result["dataset"].get("locations",[]):
            lines.append(f"| `{loc['path']}` | {loc['gguf_total']} | {loc['gguf_ge_1mb']} | {loc['total_human']} |")
        reg = self._registry.get_status() if self._registry else {}
        lines += ["", f"Unified registry: **{reg.get('total_providers','?')} providers / {reg.get('total_models','?')} model entries**. Categories: `{reg.get('categories',{})}`.", "",
                  "## Notes", *[f"- {n}" for n in result["notes"]], "", "Raw JSON: `~/.qb_protocol_velocity_benchmark.json`. Run `POST /benchmark/velocity` or `GET /benchmark/velocity` to refresh.", ""]
        DOC_PATH.write_text("\n".join(lines))

    def last(self) -> Optional[Dict[str, Any]]:
        if self._last: return self._last
        if BENCH_PATH.exists():
            try: self._last = json.loads(BENCH_PATH.read_text()); return self._last
            except Exception: pass
        return None

velocity_benchmark = VelocityBenchmark()
