"""
Trial registry — append-only JSONL log for honest --n-trials accounting.

Every parameter set, threshold variant, or filter combination tried for any
alpha must be logged here BEFORE the gate run that uses it. Under-reporting
trials inflates Deflated Sharpe (lowers the bar). This is the only honest
source for the n_trials argument to ValidationGate.run().

Usage:
    registry = TrialRegistry("ag/validation/trial_log.jsonl")
    trial_id = registry.log(
        alpha_id="A0_MVP",
        description="sweep+choch only, lookback=5, stop=0.5%, target=1.0%",
        params={"lookback": 5, "stop_pct": 0.005, "target_pct": 0.01},
    )
    n = registry.count("A0_MVP")
    gate.run(result, cost_model, n_trials=n)
"""
from __future__ import annotations

import json
import pathlib
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TrialEntry:
    trial_id: str
    alpha_id: str
    description: str
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp_utc: str = ""
    note: str = ""


class TrialRegistry:
    """
    Append-only JSONL trial registry.

    Each call to log() writes one line to the file.
    count() scans the file and returns the number of trials for a given alpha_id.
    The registry is append-only by design — never delete or edit entries.
    """

    def __init__(self, path: str | pathlib.Path = "ag/validation/trial_log.jsonl") -> None:
        self.path = pathlib.Path(path)

    def log(
        self,
        alpha_id: str,
        description: str,
        params: Optional[Dict[str, Any]] = None,
        timestamp_utc: str = "",
        note: str = "",
    ) -> str:
        """
        Append one trial entry. Returns the trial_id.

        Call this BEFORE running the gate with these params.
        Every distinct parameter set or filter combination counts as one trial.
        """
        entry = TrialEntry(
            trial_id=str(uuid.uuid4())[:8],
            alpha_id=alpha_id,
            description=description,
            params=params or {},
            timestamp_utc=timestamp_utc,
            note=note,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(entry)) + "\n")
        return entry.trial_id

    def count(self, alpha_id: str) -> int:
        """Return the number of logged trials for an alpha_id."""
        if not self.path.exists():
            return 0
        total = 0
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("alpha_id") == alpha_id:
                        total += 1
                except json.JSONDecodeError:
                    continue
        return total

    def all_trials(self, alpha_id: Optional[str] = None) -> List[TrialEntry]:
        """Return all entries, optionally filtered by alpha_id."""
        entries: List[TrialEntry] = []
        if not self.path.exists():
            return entries
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    if alpha_id is None or d.get("alpha_id") == alpha_id:
                        entries.append(TrialEntry(**d))
                except (json.JSONDecodeError, TypeError):
                    continue
        return entries

    def report(self, alpha_id: Optional[str] = None) -> str:
        """Human-readable summary for a given alpha (or all alphas)."""
        trials = self.all_trials(alpha_id)
        if not trials:
            label = alpha_id or "all alphas"
            return f"No trials logged for {label}."
        lines = [f"Trial registry — {alpha_id or 'all'} ({len(trials)} entries):"]
        for t in trials:
            param_str = ", ".join(f"{k}={v}" for k, v in t.params.items())
            lines.append(f"  [{t.trial_id}] {t.alpha_id}: {t.description}")
            if param_str:
                lines.append(f"    params: {param_str}")
            if t.note:
                lines.append(f"    note: {t.note}")
        return "\n".join(lines)
