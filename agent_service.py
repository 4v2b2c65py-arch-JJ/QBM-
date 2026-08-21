#!/usr/bin/env python3
"""
QB Protocol - Persistent Agent Entry Point
macOS launchd service entry point for boot-persistent agentic sync.
"""

from __future__ import annotations

import asyncio
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestrator.agentic_sync import orchestrator
from orchestrator.incognito_missions import incognito_mission_runner

_AGENT_DISABLED = {"0", "false", "no", "off", ""}


def agent_autonomy_enabled() -> bool:
    """Pause the autonomous agent while the user is active (so it stops
    generating its own inputs); resume in the background when idle."""
    raw = os.environ.get("AGENT_AUTONOMY")
    if raw is not None and raw != "":
        return raw.lower() not in _AGENT_DISABLED
    try:
        out = subprocess.run(["ioreg", "-c", "IOHIDSystem"],
                             capture_output=True, text=True, timeout=3).stdout
        m = re.search(r'"HIDIdleTime"\s*=\s*(\d+)', out)
        if m:
            idle_s = int(m.group(1)) / 1_000_000_000
            threshold = float(os.environ.get("AGENT_IDLE_THRESHOLD_SECONDS", "300"))
            return idle_s >= threshold
    except Exception:
        pass
    return True


class Agent:
    def __init__(self) -> None:
        self.stop_event = asyncio.Event()

    def request_stop(self, *_args) -> None:
        self.stop_event.set()

    async def initialize(self) -> None:
        print("agent: initializing orchestrator")
        status = orchestrator.get_status()
        print(f"agent: device_id={status.get('device_id')}")
        print(f"agent: version={status.get('version')}")
        print(f"agent: boot_count={status.get('boot_count')}")

        if agent_autonomy_enabled():
            print("agent: starting incognito solo mission runner")
            incognito_mission_runner.start()
            print("agent: incognito solo mission runner started")
        else:
            print("agent: autonomy paused (user active or AGENT_AUTONOMY=0) "
                  "- incognito missions deferred")

    async def heartbeat(self) -> None:
        print("agent: heartbeat")
        if not agent_autonomy_enabled():
            print("agent: autonomous sync paused (user active)")
            return
        try:
            result = orchestrator.sync(direction="bidirectional")
            print(f"agent: sync status={result.get('status')} changes={result.get('changes_count')}")
        except Exception as e:
            print(f"agent: heartbeat error: {e}")

    async def work_cycle(self) -> None:
        await self.heartbeat()

    async def shutdown(self) -> None:
        print("agent: shutting down cleanly")
        try:
            incognito_mission_runner.stop()
        except Exception:
            pass
        print("agent: incognito solo mission runner stopped")

    async def run(self) -> None:
        loop = asyncio.get_running_loop()

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, self.request_stop)
            except NotImplementedError:
                pass

        await self.initialize()

        try:
            while not self.stop_event.is_set():
                try:
                    await asyncio.wait_for(self.work_cycle(), timeout=30)
                except asyncio.TimeoutError:
                    print("agent: work cycle timed out")
                except Exception as exc:
                    print(f"agent: recoverable error: {exc}")

                try:
                    await asyncio.wait_for(self.stop_event.wait(), timeout=60)
                except asyncio.TimeoutError:
                    pass

        finally:
            await self.shutdown()


def main() -> None:
    asyncio.run(Agent().run())


if __name__ == "__main__":
    main()
