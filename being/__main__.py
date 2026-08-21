#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Module entry point.

Usage:
    python -m qb_protocol.being                 # alias for `run` (foreground loop)
    python -m qb_protocol.being status          # print status JSON
    python -m qb_protocol.being install         # install native launchd service
    python -m qb_protocol.being install|start|stop|restart|uninstall
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_PARENT = _ROOT.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from qb_protocol.being.cli import main  # noqa: E402

if __name__ == "__main__":
    argv = sys.argv[1:] or ["run"]
    raise SystemExit(main(argv))
