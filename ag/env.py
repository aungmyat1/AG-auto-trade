"""
Runtime environment loader.

Single source of truth for all env-var-backed settings.

Rule: gate thresholds and risk limits in ag/config.py are HARDCODED — they
must never be overridden by environment variables. This module only exposes
connection credentials and runtime-configurable connection params.

Usage:
    from ag.env import DATABENTO_API_KEY, check_phase_b_ready

dotenv load: python-dotenv is optional. Install with `pip install -e ".[dev]"`.
If missing, env vars must be set at the shell / systemd level (correct for prod).
"""
from __future__ import annotations

import os

try:
    from dotenv import load_dotenv as _load_dotenv

    _load_dotenv()
except ImportError:
    pass

# ── Phase B: Databento data layer ─────────────────────────────────────────────
DATABENTO_API_KEY: str = os.environ.get("DATABENTO_API_KEY", "")

# ── Telegram alerts (ag/monitoring/) ──────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")

# ── Phase 3: Interactive Brokers execution (not needed until ROBUST verdict) ──
IB_HOST: str = os.environ.get("IB_HOST", "127.0.0.1")
IB_PORT: int = int(os.environ.get("IB_PORT", "7497"))
IB_CLIENT_ID: int = int(os.environ.get("IB_CLIENT_ID", "1"))


def check_phase_b_ready() -> tuple[bool, list[str]]:
    """Return (ready, missing_keys) for Phase B data layer prerequisites.

    Reads os.environ at call time so monkeypatch works in tests.
    """
    required = {"DATABENTO_API_KEY": os.environ.get("DATABENTO_API_KEY", "")}
    missing = [k for k, v in required.items() if not v]
    return len(missing) == 0, missing


def check_phase_3_ready() -> tuple[bool, list[str]]:
    """Return (ready, missing_keys) for Phase 3 IB execution prerequisites.

    Checks Telegram keys (IB_HOST/PORT/CLIENT_ID have safe defaults).
    Reads os.environ at call time so monkeypatch works in tests.
    """
    required = {
        "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        "TELEGRAM_CHAT_ID": os.environ.get("TELEGRAM_CHAT_ID", ""),
    }
    missing = [k for k, v in required.items() if not v]
    return len(missing) == 0, missing
