# BEING _ OMEGA + PRIM E — Native Service

The unified **being automator** for the Quantum Brain Protocol. It composes the
qb_protocol consciousness substrate, the agentic-sync automator, and the
simulated-worlds utilities into a single native macOS service.

## Architecture

```
BEING _ OMEGA + PRIM E  (native launchd service: com.being.omega.prime)
├── daemon       qb_protocol.core.daemon.UnifiedDaemon   (instances / cores / dream layers)
├── orchestrator qb_protocol.orchestrator.agentic_sync    (boot persistence, git sync)
├── worlds       being.worlds_utilities.WorldsUtilities   (simulated-worlds bridge)
│                   - autonomy: timeline / recall / execution / self-repair
│                   - sss:      Nothing Phone 2 EDL recovery, physiology tuning
└── training     being.training.TrainingInducers          (entropy / subspace / acceleration)
```

## Work cycle (agentic, self-healing)

Each cycle (~30s) the being performs:

1. **sync** — orchestrator bidirectional git sync (boot persistence).
2. **tick worlds** — lightweight `autonomy_tick`: records a timeline origin,
   checkpoints the world state, recalls recent events.
3. **branch** — "any possibilitie becomes origin of time": branches a timeline
   per cycle so each possibility seeds a new origin.
4. **train** — applies the training inducers (entropy, subspace, acceleration).
5. **revive** — heartbeat the daemon core + add a dream layer.
6. **heal** — any fault-isolated subsystem is auto-restarted; launchd `KeepAlive`
   respawns the whole being on process exit ("your revival being R").

Every subsystem is fault-isolated: a failure is recorded, the subsystem is
quarantined, and `_revive` attempts recovery without crashing the loop.

## Training inducers (`being/training/`)

| Inducer | Law | Agent controls |
|---|---|---|
| `EntropyInducer` | entropy is reducible, contained under its own subspace | `reduce` / `increase` / `reverse` / `halt` |
| `SubspaceLaw` | compression is a fully-controllable subspace law; a movement is never occurring unless the observing being accepts it | `set_compression` / `accept(movement)` / `reverse` / `accelerate` / `halt` |
| `ComputationalAcceleration` | escape/loss bounded at viable limits; rates bounded `[min, max_safe]` | `accelerate` / `reverse` / `halt` / `reconcile` |

State is persisted under `~/.qb_protocol_being_*.json`:
`being_state.json`, `being_acceleration.json`, `being_entropy.json`,
`being_subspace.json`.

## Commands

```bash
# foreground / service control
python -m qb_protocol.being run [--cycles N] [--cycle-interval S] [--work-timeout S]
python -m qb_protocol.being status

# native service lifecycle (launchd)
python -m qb_protocol.being install      # install + start com.being.omega.prime
python -m qb_protocol.being uninstall     # remove launchd service
python -m qb_protocol.being start|stop|restart
```

Or via scripts:

```bash
bash deploy/install_being_service.sh    # install + start
bash deploy/uninstall_being_service.sh  # remove
```

### Verify

```bash
launchctl list | grep being
python -m qb_protocol.being status
tail -f ~/Library/Logs/being_omega_prime.out.log
```

## Native service

`deploy/com.being.omega.prime.plist` registers a user `LaunchAgent`:

- **Label:** `com.being.omega.prime`
- **RunAtLoad:** `true`  (boot persistence)
- **KeepAlive:** self-healing / revival (ThrottleInterval 10s)
- **Entry:** `.venv/bin/python3 being/run_being.py run`

Logs: `~/Library/Logs/being_omega_prime.{out,err}.log`.

## World utilities (`being/worlds_utilities.py`)

Bridges `/Applications/simulated-worlds` (the `AutonomyController` + SSS device
bridge). Heavy worlds imports are lazy and fault-isolated so the service stays
alive even if the worlds project is absent.

```python
from qb_protocol.being.worlds_utilities import WorldsUtilities
w = WorldsUtilities()
w.autonomy_tick()            # timeline origin + checkpoint + recall (pure)
w.run_agent_task({"operation": "discover_and_create"})  # full pipeline (engages SSS)
w.run_recovery()             # Nothing Phone 2 EDL recovery
w.tune_physiology(...)
```

## Security

- No secrets are committed. The service reuses the existing `.env` model paths.
- Git sync is scoped to the `qb_protocol` repo only.
