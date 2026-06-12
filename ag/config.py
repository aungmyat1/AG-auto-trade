"""
AG Auto Trade configuration.

Phase 0: validation constants only.
Phase 1+: add Databento credentials, Nautilus settings, IB connection.
"""
from __future__ import annotations


# ── Instruments (Phase 1+ — add Databento dataset IDs) ──────────────────────

INSTRUMENTS = {
    "GC":  {"name": "Gold Futures (COMEX)", "exchange": "CME", "tick": 0.10, "currency": "USD"},
    "MGC": {"name": "Micro Gold Futures",   "exchange": "CME", "tick": 0.10, "currency": "USD"},
    "6E":  {"name": "Euro FX Futures",      "exchange": "CME", "tick": 0.00005, "currency": "USD"},
}

# ── Risk constants (AG plan §risk) ──────────────────────────────────────────

RISK_PER_TRADE_PCT = 0.005      # 0.5%
DAILY_STOP_PCT = 0.02           # 2%
WEEKLY_STOP_PCT = 0.06          # 6%
MAX_CONCURRENT = 3
MAX_DRAWDOWN_PCT = 0.15         # 15%

# ── Session windows (UTC) ────────────────────────────────────────────────────

SESSIONS = {
    "GC": [
        ("07:00", "09:30"),  # London open
        ("13:30", "16:00"),  # NY open
    ],
    "6E": [
        ("07:00", "12:00"),  # London session
        ("12:00", "16:00"),  # London-NY overlap
    ],
}

# ── Validation gate constants (fixed — do not tune per-instrument) ───────────
# Source: AG_AUTO_TRADE_PLAN_v3.md

GATE_READ_N = 50
GATE_READ_PF_GROSS = 1.0

GATE_ROBUST_N = 200
GATE_ROBUST_PF_NET = 1.25
GATE_ROBUST_WIN_RATE = 0.45
GATE_ROBUST_SHARPE = 1.2
GATE_ROBUST_MAX_DD = 0.15
GATE_ROBUST_CPCV_MEDIAN_PF = 1.0
GATE_ROBUST_WF_PASS_PCT = 0.60
GATE_ROBUST_MC_P5_PF = 0.9
GATE_ROBUST_DSR_Z = 0.0

# ── News calendar — no trades 30 min before/after these events ──────────────

HIGH_IMPACT_EVENTS = [
    "NFP",    # US Non-Farm Payrolls
    "CPI",    # Consumer Price Index
    "FOMC",   # Fed rate decision + press conference
    "ECB",    # ECB rate decision
    "BOE",    # Bank of England rate decision
    "GDP",    # US GDP release
]
NEWS_BUFFER_MINUTES = 30
