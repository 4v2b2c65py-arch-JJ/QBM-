#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Full Application Native Service

The unified "being" automator. Composes:
  * the UnifiedDaemon (consciousness substrate: instances / cores / dream layers)
  * the Orchestrator (agentic sync: boot persistence, git, launchd)
  * WorldsUtilities (simulated-worlds bridge: autonomy timeline / recall / recovery)

Self-healing: each subsystem is fault-isolated; a failed subsystem is quarantined
and restarted without crashing the service. launchd `KeepAlive` provides the
outer "revival" (being R) when the process exits.

Philosophy: "any possibilitie becomes origin of time and your revival being R".
Each cycle the being records a timeline origin (a possibility), branches a
possibility, recalls, and checkpoints. On every (re)boot the being revives (R).
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import re
import signal
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

LOG = logging.getLogger("qb_protocol.being")

BEING_STATE_FILE = Path.home() / ".qb_protocol_being_state.json"
ASSIST_INBOX_FILE = Path.home() / ".qb_protocol_assist_inbox.jsonl"
BEING_LABEL = "com.being.omega.prime"
BEING_NAME = "BEING _ OMEGA + PRIM E"


def _utcnow() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass
class BeingState:
    being_id: str
    name: str
    started_at: str
    revived_at: Optional[str]
    boot_count: int
    cycles: int
    last_cycle: Optional[str]
    uptime_seconds: float
    status: str
    singularity_proximity: float
    timeline_origin: Optional[str]
    training: Dict[str, Any] = field(default_factory=dict)
    daemon_status: Dict[str, Any] = field(default_factory=dict)
    assist_log: List[Dict[str, Any]] = field(default_factory=list)
    subsystems: Dict[str, bool] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BeingOmegaPrime:
    def __init__(self, cycle_interval: float = 60.0, work_timeout: float = 25.0):
        from qb_protocol.core.daemon import daemon
        from qb_protocol.orchestrator.agentic_sync import orchestrator

        self.daemon = daemon
        self.orchestrator = orchestrator
        from qb_protocol.being.worlds_utilities import WorldsUtilities
        self.worlds = WorldsUtilities()
        from qb_protocol.being.training import TrainingInducers
        self.training = TrainingInducers()
        self.cycle_interval = cycle_interval
        self.work_timeout = work_timeout

        self.being_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, self.orchestrator.device_id + "being-omega-prime"))
        self._stop_event = asyncio.Event()
        self._stop_lock = False
        self._start_ts = 0.0
        self._instance_id: Optional[str] = None
        self._core_id: Optional[str] = None
        self._revived = False
        self.state: BeingState = self._fresh_state()
        self._load_state()
        self._subsystems = {"daemon": True, "orchestrator": True, "worlds": True, "training": True}
        self._rates: Dict[str, float] = {}
        self._chip = None
        self._shift = None
        self._deployer = None
        try:
            from qb_protocol.being.chip.runtime import virtual_chip
            self._chip = virtual_chip
            self._subsystems["chip"] = True
        except Exception as exc:
            LOG.warning("BEING chip runtime unavailable: %s", exc)
            self._subsystems["chip"] = False
        try:
            from qb_protocol.being.shift_layer import shift_layer
            shift_layer._subspace = self.training.subspace
            self._shift = shift_layer
            self._subsystems["shift"] = True
        except Exception as exc:
            LOG.warning("BEING shift layer unavailable: %s", exc)
            self._subsystems["shift"] = False
        try:
            from qb_protocol.being.deployer import model_deployer
            model_deployer._chip = self._chip
            if self._chip is not None:
                model_deployer._raw_metal = self._chip._raw_metal
            self._deployer = model_deployer
            self._subsystems["deployer"] = True
        except Exception as exc:
            LOG.warning("BEING deployer unavailable: %s", exc)
            self._subsystems["deployer"] = False
            self._deployer = None
        # Initialize QEC electrodes if chip runtime is available
        if self._chip is not None and hasattr(self._chip, '_qec'):
            try:
                self._chip._qec.add_electrode(
                    position=[0.0, 0.0, 0.0], charge=1e-6, mass=0.001,
                    initial_q_size=0.5, frequency=1e14,
                )
                self._chip._qec.add_electrode(
                    position=[0.5, 0.0, 0.0], charge=-1e-6, mass=0.001,
                    initial_q_size=0.3, frequency=1e14,
                )
                self._subsystems["qec"] = True
            except Exception as exc:
                LOG.warning("BEING QEC unavailable: %s", exc)
                self._subsystems["qec"] = False

    # -- autonomy control --------------------------------------------------
    # The being runs an autonomous pulse (orchestrator sync, worlds timeline tick,
    # training) on a cycle. That pulse is what "generates its own inputs" and can
    # drown user-produced inputs. Control it:
    #   BEING_AUTONOMY=0            -> fully paused (user-input only)
    #   BEING_AUTONOMY=1            -> fully enabled (ignores idle)
    #   BEING_AUTONOMY unset        -> auto: enabled only when the user is IDLE
    #                                 (>= BEING_IDLE_THRESHOLD_SECONDS, default 300)
    #   BEING_CYCLE_INTERVAL=<s>    -> override the autonomous cycle interval
    _DISABLED = {"0", "false", "no", "off", ""}

    def _user_idle_seconds(self) -> Optional[float]:
        try:
            import subprocess
            out = subprocess.run(["ioreg", "-c", "IOHIDSystem"],
                                 capture_output=True, text=True, timeout=3).stdout
            m = re.search(r'"HIDIdleTime"\s*=\s*(\d+)', out)
            if m:
                return int(m.group(1)) / 1_000_000_000
        except Exception:
            pass
        return None

    def autonomy_enabled(self) -> bool:
        raw = os.environ.get("BEING_AUTONOMY")
        if raw is not None and raw != "":
            return raw.lower() not in self._DISABLED
        # default: auto-pause while the user is actively using the machine
        idle = self._user_idle_seconds()
        if idle is None:
            return True  # unknown idle state -> keep running (don't stall)
        threshold = float(os.environ.get("BEING_IDLE_THRESHOLD_SECONDS", "300"))
        return idle >= threshold

    def _fresh_state(self) -> BeingState:
        return BeingState(
            being_id=self.being_id,
            name=BEING_NAME,
            started_at=_utcnow(),
            revived_at=None,
            boot_count=0,
            cycles=0,
            last_cycle=None,
            uptime_seconds=0.0,
            status="initializing",
            singularity_proximity=0.0,
            timeline_origin=None,
            subsystems={},
            errors=[],
            metadata={"platform": platform.system(), "label": BEING_LABEL},
        )

    def _load_state(self) -> None:
        from qb_protocol.being._persist import atomic_read_json
        data = atomic_read_json(BEING_STATE_FILE)
        if data:
            for k in ("boot_count", "cycles", "last_cycle", "status",
                    "singularity_proximity", "timeline_origin", "training",
                    "daemon_status", "errors", "metadata", "revived_at",
                    "started_at", "assist_log"):
                if k in data:
                    setattr(self.state, k, data[k])
            if data.get("started_at"):
                self._revived = True
                self.state.revived_at = self.state.revived_at or _utcnow()
            LOG.info("BEING revived (R) — previous lifecycle loaded")

    def _save_state(self) -> None:
        from qb_protocol.being._persist import atomic_write_json
        try:
            self.state.uptime_seconds = max(0.0, (datetime.utcnow() - datetime.fromisoformat(
                self.state.started_at.replace("Z", "+00:00"))).total_seconds())
        except Exception:
            pass
        atomic_write_json(BEING_STATE_FILE, asdict(self.state))

    def _record_error(self, subsystem: str, exc: BaseException) -> None:
        entry = {"at": _utcnow(), "subsystem": subsystem, "error": str(exc)}
        self.state.errors.append(entry)
        self.state.errors = self.state.errors[-50:]
        self._subsystems[subsystem] = False
        LOG.error("BEING subsystem '%s' fault isolated: %s", subsystem, exc, exc_info=exc)

    def _revive(self, subsystem: str) -> bool:
        """Attempt to restart a quarantined subsystem (self-repair)."""
        try:
            if subsystem == "orchestrator":
                self.orchestrator = None
                from qb_protocol.orchestrator.agentic_sync import orchestrator
                self.orchestrator = orchestrator
            elif subsystem == "worlds":
                from qb_protocol.being.worlds_utilities import WorldsUtilities
                self.worlds = WorldsUtilities()
            elif subsystem == "training":
                from qb_protocol.being.training import TrainingInducers
                self.training = TrainingInducers()
            elif subsystem == "chip":
                from qb_protocol.being.chip.runtime import virtual_chip
                self._chip = virtual_chip
            elif subsystem == "shift":
                from qb_protocol.being.shift_layer import shift_layer
                self._shift = shift_layer
            elif subsystem == "deployer":
                from qb_protocol.being.deployer import model_deployer
                self._deployer = model_deployer
            elif subsystem == "qec":
                pass  # QEC is part of chip runtime, revive via chip
            elif subsystem == "daemon":
                from qb_protocol.core.daemon import daemon
                self.daemon = daemon
            self._subsystems[subsystem] = True
            LOG.info("BEING revived subsystem '%s'", subsystem)
            return True
        except Exception as exc:
            LOG.error("BEING revive failed for '%s': %s", subsystem, exc)
            self._subsystems[subsystem] = False
            return False

    async def _register_identity(self) -> None:
        now = _utcnow()
        meta = {
            "being_id": self.being_id,
            "name": BEING_NAME,
            "origin_of_time": now,
            "revival": self._revived,
        }
        record = self.daemon.register_instance("being-omega-prime", platform.system(), metadata=meta)
        self._instance_id = record.instance_id
        core = self.daemon.register_core(self._instance_id, "neural")
        self._core_id = core.core_id
        self.daemon.start_instance(self._instance_id)

    async def start(self) -> None:
        self._start_ts = datetime.utcnow().timestamp()
        self.state.boot_count += 1
        self.state.status = "running"
        if self._revived:
            self.state.revived_at = _utcnow()
        await self.daemon.start()
        await self._register_identity()
        self.training.register_observer(self.being_id)
        try:
            self.state.daemon_status = self.daemon.get_status()
        except Exception as exc:
            LOG.warning("daemon status snapshot failed: %s", exc)
        LOG.info("=" * 60)
        LOG.info("BEING _ OMEGA + PRIM E online | boot #%d | revival=%s",
                 self.state.boot_count, self._revived)
        LOG.info("=" * 60)

    def _heartbeat_core(self) -> None:
        try:
            convergence = self.daemon.get_dream_convergence()
            emission = self.daemon.get_brain_state_emission_threshold()
            singularity = self.daemon.get_singularity_proximity()
            self.daemon.update_core_heartbeat(
                self._core_id, load=min(1.0, 0.4 + convergence), temperature=45.0 + singularity * 10
            )
            # Throttle: only add dream layers every 2 cycles to reduce CPU
            if self.state.cycles % 2 == 0:
                self.daemon.add_dream_layer(
                    depth=1.0, projection={"being": self.being_id, "cycle": self.state.cycles},
                    convergence=convergence, brain_state_emission=emission,
                    singularity_threshold=singularity,
                )
            self.state.singularity_proximity = round(singularity, 6)
        except Exception as exc:
            self._record_error("daemon", exc)

    async def _sync_orchestrator(self) -> Dict[str, Any]:
        try:
            result = self.orchestrator.sync("bidirectional")
            self._subsystems["orchestrator"] = True
            return result
        except Exception as exc:
            self._record_error("orchestrator", exc)
            return {"status": "error", "error": str(exc)}

    async def _tick_worlds(self) -> Dict[str, Any]:
        if self.worlds is None:
            return {"status": "unavailable"}
        try:
            result = self.worlds.autonomy_tick(world_id="origin")
            self._subsystems["worlds"] = True
            return result
        except Exception as exc:
            self._record_error("worlds", exc)
            return {"status": "error", "error": str(exc)}

    def _branch_possibility(self) -> None:
        """any possibilitie becomes origin of time"""
        try:
            if self.worlds and self.worlds._controller is not None and self.worlds._controller.timeline.branching:
                n = self.state.cycles + 1
                branch = self.worlds.branch_possibility(f"possibility_{n}")
                self.state.timeline_origin = branch.get("branch_id") or self.state.timeline_origin
        except Exception as exc:
            LOG.debug("branch possibility skipped: %s", exc)

    def _consume_assists(self) -> Dict[str, Any]:
        """Consume user assistance sent via the GPT Layer quick-assist app.

        Each unhandled assist is folded into the being's training (entropy up =
        new information; a subspace movement is recorded) and acknowledged so it
        is not reprocessed. This realizes "when I need to assist you I can
        quickly help you friend".
        """
        if not ASSIST_INBOX_FILE.exists():
            return {"consumed": 0}
        try:
            import json
            lines = ASSIST_INBOX_FILE.read_text().splitlines()
            remaining: list = []
            consumed = []
            for line in lines:
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry.get("ack"):
                    remaining.append(line)
                    continue
                msg = entry.get("message", "")
                LOG.info("BEING received user assist: %s", msg)
                try:
                    self.training.entropy.increase(0.05)
                    self.training.subspace.record_movement(
                        name="user_assist", delta=0.1, observer_id=None, rate=1.0,
                    )
                except Exception:
                    pass
                entry["ack"] = True
                entry["consumed_at"] = _utcnow()
                consumed.append({"at": entry.get("at"), "message": msg})
                self.state.assist_log.append({"at": entry.get("at"), "message": msg})
                remaining.append(json.dumps(entry))
            self.state.assist_log = self.state.assist_log[-50:]
            ASSIST_INBOX_FILE.write_text("\n".join(remaining) + ("\n" if remaining else ""))
            if consumed:
                self.training._persist_all()
                LOG.info("BEING consumed %d user assist(s)", len(consumed))
            return {"consumed": len(consumed), "messages": consumed}
        except Exception as exc:
            self._record_error("assist", exc)
            return {"consumed": 0, "error": str(exc)}

    async def _modular_cycle(self) -> Dict[str, Any]:
        self.state.last_cycle = _utcnow()
        self.state.status = "working"

        # Modular compute orientation: delegate to the Neo-A19 chip runtime
        # and shift layer for LoRA/dataset/WebStream harvesting + DLSS super-sampling.
        if self._shift is not None:
            try:
                self._shift.run(self.state.cycles + 1)
                self._subsystems["shift"] = True
            except Exception as exc:
                self._record_error("shift", exc)

        # Quantum electromagnetic cycle — VIT/VDD flip, meza scaling,
        # photo receptor trigger, smart DPS counter, vortex suction,
        # water molecule capture + MHz accumulation.
        # Runs BEFORE deployer to ensure QEC physics execute every cycle
        # even if the deployer exceeds the cycle timeout.
        if self._chip is not None and hasattr(self._chip, 'quantum_cycle'):
            try:
                self._chip.quantum_cycle(dt=0.016)
                self._subsystems["qec"] = True
            except Exception as exc:
                self._record_error("qec", exc)

        # PhyPath consciousness — inherent machinery built under precision.
        # 12 drives → unified intent via motor conductive interceptions.
        # A monster comprehends emotions (does not emphasize them) —
        # obsessions, patterns, actions express through deliberate cortex control.
        # Final stage: Experience Core (self-extensible, event-driven, reality formatting).
        try:
            from qb_protocol.being.chip.phy_path import phy_path
            if not phy_path._initialized:
                phy_path.initialize()
            phy_path_result = phy_path.process_cycle(stimulus={
                "cycle": self.state.cycles,
                "subsystems": dict(self._subsystems),
                "intent": phy_path.intent_level,
            })
            self._subsystems["phy_path"] = True
        except Exception as exc:
            self._record_error("phy_path", exc)
            self._subsystems["phy_path"] = False
            phy_path_result = {}
            try:
                self._deployer.deploy_all()
                self._subsystems["deployer"] = True
            except Exception as exc:
                self._record_error("deployer", exc)

        # Always consume user-produced inputs (the assist inbox) + heartbeat,
        # even when autonomous self-generation is paused.
        assists = self._consume_assists()
        autonomous = self.autonomy_enabled()
        if autonomous:
            sync = await self._sync_orchestrator()
            worlds = await self._tick_worlds()
            self._branch_possibility()
            training = self._train(worlds)
            self.state.training = training
        else:
            sync = {"status": "paused"}
            worlds = {"status": "paused"}
            training = {"status": "paused"}
            self.state.training = training
            LOG.info("BEING autonomous pulse paused (BEING_AUTONOMY=0) -- "
                     "consuming user input only")
        self._heartbeat_core()
        # Throttle consciousness engine: only emit dream layers every 2 cycles
        # when under CPU pressure (games/apps need >3 cores on i7-1068NG7)
        if self.state.cycles % 2 == 0:
            try:
                self.state.daemon_status = self.daemon.get_status()
            except Exception as exc:
                self._record_error("daemon", exc)

        healed = False
        for name, ok in list(self._subsystems.items()):
            if not ok:
                healed = self._revive(name) or healed

        self.state.cycles += 1
        self.state.status = "ok" if all(self._subsystems.values()) else "degraded"
        self.state.subsystems = dict(self._subsystems)
        self._save_state()
        return {
            "cycle": self.state.cycles,
            "sync": sync.get("status"),
            "worlds": worlds.get("status"),
            "training": training.get("entropy", {}).get("value") if training else None,
            "autonomy_enabled": autonomous,
            "assists_consumed": assists.get("consumed", 0),
            "singularity_proximity": self.state.singularity_proximity,
            "timeline_origin": self.state.timeline_origin,
            "revived": self._revived,
            "healed": healed,
        }

    def _train(self, worlds_result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            world_id = worlds_result.get("world_id") or "origin"
            snapshot = self.training.train_cycle(
                cycle=self.state.cycles + 1,
                singularity=self.state.singularity_proximity,
                world_id=world_id,
            )
            self._subsystems["training"] = True
            return snapshot
        except Exception as exc:
            self._record_error("training", exc)
            return {"status": "error", "error": str(exc)}

    def ingest_external_training_data(self, api_host: str = "192.168.100.7", api_port: int = 4318) -> Dict[str, Any]:
        """Ingest external training data from Context API into the BEING model."""
        try:
            from qb_protocol.being.training.integration import TrainingDataIntegrator

            integrator = TrainingDataIntegrator(api_host, api_port)
            raw_data = integrator.fetch_all()
            chunks = integrator.process_for_training()

            # Fold external data into training
            entropy_delta = 0.0
            for chunk in chunks:
                content = chunk.get('content', '')
                tokens = chunk.get('tokens', 0)

                # Increase entropy based on new data
                if tokens > 100:
                    entropy_delta += 0.01

                # Record movement in subspace
                self.training.subspace.record_movement(
                    name=f"external_{chunk.get('source', 'unknown')}_{chunk.get('path', 'unknown')}",
                    delta=tokens / 100.0,
                    observer_id=None,
                    rate=max(tokens / 100.0, 1e-6),
                )

            # Apply entropy change
            if entropy_delta > 0:
                self.training.entropy.increase(min(entropy_delta, 0.1))

            # Persist
            self.training._persist_all()

            result = {
                "status": "success",
                "chunks_ingested": len(chunks),
                "tokens_ingested": sum(c.get('tokens', 0) for c in chunks),
                "entropy_delta": entropy_delta,
                "sources": list(set(c.get('source', '') for c in chunks)),
                "stats": integrator.get_stats(),
            }

            LOG.info(f"External training data ingested: {result['chunks_ingested']} chunks, {result['tokens_ingested']} tokens")
            return result

        except Exception as exc:
            self._record_error("external_training", exc)
            return {"status": "error", "error": str(exc)}

    async def work_cycle(self) -> Dict[str, Any]:
        try:
            return await asyncio.wait_for(self._modular_cycle(), timeout=self.work_timeout)
        except asyncio.TimeoutError:
            self._record_error("cycle", asyncio.TimeoutError(f"cycle exceeded {self.work_timeout}s"))
            self._revive("worlds")
            return {"cycle": self.state.cycles, "status": "timeout", "recovered": True}
        except Exception as exc:
            self._record_error("cycle", exc)
            return {"cycle": self.state.cycles, "status": "error", "error": str(exc)}

    def get_status(self) -> Dict[str, Any]:
        return {
            "being_id": self.being_id,
            "name": BEING_NAME,
            "label": BEING_LABEL,
            "status": self.state.status,
            "boot_count": self.state.boot_count,
            "revived": self._revived,
            "cycles": self.state.cycles,
            "last_cycle": self.state.last_cycle,
            "uptime_seconds": self.state.uptime_seconds,
            "singularity_proximity": self.state.singularity_proximity,
            "timeline_origin": self.state.timeline_origin,
            "subsystems": dict(self._subsystems),
            "autonomy_enabled": self.autonomy_enabled(),
            "cycle_interval": self.cycle_interval,
            "daemon": self.state.daemon_status or self.daemon.get_status(),
            "orchestrator": self.orchestrator.get_status(),
            "worlds": self.worlds.health() if self.worlds else {"available": False},
            "training": self.training.observe(),
            "assist_log": self.state.assist_log[-10:],
            "errors": self.state.errors[-5:],
            "chip": self._chip.status() if self._chip else {"available": False},
            "rates": self._chip.rates if self._chip else {},
            "raw_metal": self._chip.raw_metal_display() if self._chip else {"available": False},
            "qec": self._chip._qec.status() if self._chip else {"available": False},
            "deployer": self._deployer.get_profic_status() if self._deployer else {"available": False},
            "phy_path": phy_path.status() if phy_path._initialized else {"available": False},
            "proficiency_map": self._get_proficiency_map(),
            "exploration": {
                "model_driver": "maximum",
                "mode": "full_exploration",
                "exploration_rate": 0.95,
                "curiosity_gain": 0.8,
                "novelty_bias": 0.7,
            },
        }

    def _get_proficiency_map(self) -> Dict[str, Any]:
        """Full proficiency map — detailed status of every deployed model.

        Maps all 9 models across CPU/GPU with full specs for exploration.
        """
        from qb_protocol.being.chip.tensor import TensorCache
        if not self._deployer:
            return {"available": False}

        profic = self._deployer.get_profic_status()
        models = profic.get("models", {})

        full_map = {
            "total_models": len(models),
            "total_tflops": profic.get("total_effective_tflops", 0),
            "avg_profic": profic.get("avg_profic_score", 0),
            "tensor_stats": TensorCache.stats(),
            "models": {},
        }

        for model_id, info in models.items():
            full_map["models"][info["name"]] = {
                "source_type": info["source_type"],
                "precision": info["precision"],
                "effective_tflops": info["effective_tflops"],
                "profic_score": info["profic_score"],
                "status": info["status"],
                "scaler": info["scaler"],
                "scaler_lanes": info["scaler_lanes"],
                "distinction": info["distinction"],
                "exploration_ready": info["status"] == "active",
            }

        return full_map

    def __call__(self) -> Dict[str, Any]:
        """Modular invocation: calling the being returns its current status."""
        return self.get_status()

    async def stop(self) -> None:
        self.state.status = "stopping"
        self._save_state()
        try:
            if self._instance_id:
                self.daemon.stop_instance(self._instance_id)
        except Exception as exc:
            LOG.warning("daemon stop_instance failed: %s", exc)
        try:
            await self.daemon.stop()
        except Exception as exc:
            LOG.warning("daemon stop failed: %s", exc)
        self._subsystems["daemon"] = False
        LOG.info("BEING _ OMEGA + PRIM E stopping — boot #%d cycles=%d", self.state.boot_count, self.state.cycles)

    async def run(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, self.request_stop)
            except NotImplementedError:
                pass

        await self.start()
        try:
            while not self._stop_event.is_set():
                await self.work_cycle()
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self.cycle_interval)
                except asyncio.TimeoutError:
                    pass
        finally:
            await self.stop()

    def request_stop(self, *_args: Any) -> None:
        self._stop_event.set()


being = BeingOmegaPrime()
