#!/usr/bin/env python3
"""PreToolUse guard for Edit/Write/MultiEdit.

Three rails (all from GROUND_TRUTH.md / GATE_DECISION.md):
  1. GATE_DECISION.md is immutable after pre-registration — no edits, ever.
  2. LIVE_TRADING may never be set truthy by the agent. Requires ROBUST
     verdict + 30-day dry-run + explicit human action.
  3. Gate thresholds (ROBUST_* / GATE_* constants in gate.py / config.py)
     are pre-registered — "do not relax thresholds" is rule #3 of the gate.

Exit 0 = allow. Exit 2 = block (stderr shown to the agent).
"""
from __future__ import annotations

import json
import re
import sys

LOCKED_FILE = "ag/validation/lock_before_look/GATE_DECISION.md"
THRESHOLD_FILES = ("ag/validation/gate.py", "ag/config.py")

LIVE_TRADING_RE = re.compile(r"(?i)\bLIVE_TRADING\b\s*[:=]\s*(True|true|1\b|\"?on\"?)")
THRESHOLD_RE = re.compile(r"\b(ROBUST_\w+|GATE_ROBUST_\w+|GATE_READ_\w+|FLOOR_\w+)\s*[:=]")


def texts_from(payload: dict) -> tuple[str, str, str]:
    """Return (file_path, old_text, new_text) across Edit/Write/MultiEdit shapes."""
    ti = payload.get("tool_input", {}) or {}
    path = ti.get("file_path", "") or ""
    old = ti.get("old_string", "") or ""
    new = ti.get("new_string", "") or ti.get("content", "") or ""
    for e in ti.get("edits", []) or []:
        old += "\n" + (e.get("old_string", "") or "")
        new += "\n" + (e.get("new_string", "") or "")
    return path, old, new


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        path, old, new = texts_from(payload)
    except Exception:
        sys.exit(0)

    norm = path.replace("\\", "/")

    if norm.endswith(LOCKED_FILE) or "lock_before_look/GATE_DECISION" in norm:
        print(
            "BLOCKED: GATE_DECISION.md is pre-registered and immutable "
            "(lock-before-look). Rule 5: it must not be modified after any alpha "
            "has seen data. Changing goalposts requires the owner editing it "
            "manually with a written rationale.",
            file=sys.stderr,
        )
        sys.exit(2)

    if LIVE_TRADING_RE.search(new):
        print(
            "BLOCKED: LIVE_TRADING may not be enabled by the agent. "
            "Prerequisites (GATE_DECISION.md rule 4): ROBUST gate verdict on "
            "n>=200 net trades, then a 30-day dry-run, then the OWNER flips the "
            "flag manually. Run /deployment-check for the full checklist.",
            file=sys.stderr,
        )
        sys.exit(2)

    if any(norm.endswith(f) for f in THRESHOLD_FILES):
        if THRESHOLD_RE.search(old) or THRESHOLD_RE.search(new):
            print(
                "BLOCKED: gate thresholds are pre-registered in "
                "GATE_DECISION.md and mirrored here. Rule 3: if no alpha "
                "passes, that is a valid result — do NOT relax thresholds. "
                "Any change needs explicit owner sign-off outside the agent.",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
