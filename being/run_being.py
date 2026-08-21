#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Native service entry point

Invoked by launchd (ProgramArguments). Fixes sys.path so the `qb_protocol`
package resolves, then dispatches to the CLI.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

_ROOT = Path(__file__).resolve().parent.parent
_PARENT = _ROOT.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from qb_protocol.being.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
