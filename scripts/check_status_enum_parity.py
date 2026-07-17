#!/usr/bin/env python3
"""Ensure lib/types.ts status unions match backend StrEnum values.

Run from repo root (CI gate):

    python scripts/check_status_enum_parity.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_TYPES = _REPO / "lib" / "types.ts"
_BACKEND = _REPO / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# type Name = "a" | "b" | ...
_UNION_RE = re.compile(
    r"export type (OrderStatus|TaskStatus)\s*=\s*\n((?:\s*\|[^\n]+\n)+)",
    re.MULTILINE,
)


def _parse_ts_unions(text: str) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for name, body in _UNION_RE.findall(text):
        members = re.findall(r'"([^"]+)"', body)
        out[name] = set(members)
    return out


def main() -> int:
    if not _TYPES.is_file():
        print(f"FAIL: missing {_TYPES}")
        return 1

    from app.orchestrator.states import OrderStatus, TaskStatus

    py_order = {m.value for m in OrderStatus}
    py_task = {m.value for m in TaskStatus}
    ts = _parse_ts_unions(_TYPES.read_text(encoding="utf-8"))

    if "OrderStatus" not in ts or "TaskStatus" not in ts:
        print("FAIL: could not parse OrderStatus/TaskStatus from lib/types.ts")
        return 1

    failed = False
    for label, py_set, ts_set in (
        ("OrderStatus", py_order, ts["OrderStatus"]),
        ("TaskStatus", py_task, ts["TaskStatus"]),
    ):
        only_py = sorted(py_set - ts_set)
        only_ts = sorted(ts_set - py_set)
        if only_py or only_ts:
            failed = True
            print(f"FAIL: {label} mismatch")
            if only_py:
                print(f"  backend only: {only_py}")
            if only_ts:
                print(f"  types.ts only: {only_ts}")
        else:
            print(f"OK: {label} ({len(py_set)} values)")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
