#!/usr/bin/env python3
"""
QB Protocol - BEING _ OMEGA + PRIM E :: Atomic persistence helpers

Atomic JSON writes (temp file + os.replace) so concurrent readers (e.g. the
`status` command querying a running native service) never observe a
half-written state file.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def atomic_write_json(path: Path, obj: Any) -> bool:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        with open(tmp, "w") as f:
            json.dump(obj, f, indent=2, default=str)
        os.replace(tmp, path)
        return True
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        return False


def atomic_read_json(path: Path, default: Any = None) -> Any:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default
