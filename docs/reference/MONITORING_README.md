# Monitoring & Alerting

## RECONCILIATION NOTE (2026-06-12)

The uploaded `telegram_alert.py` skeleton uses `requests` (third-party library).
The production module at `ag/monitoring/__init__.py` is ALREADY implemented and
uses stdlib-only (`urllib.request`) — which is correct per the project constraint.

DO NOT replace `ag/monitoring/__init__.py` with the skeleton — the existing module
is better.

Uploaded skeleton saved at: `docs/reference/skeletons/telegram_alert_skeleton.py`

---

## Existing Production Module

Location: `ag/monitoring/__init__.py`

Functions:
- `send_telegram(message, bot_token, chat_id)` — stdlib urllib, returns bool
- `alert_validation_result(alpha, verdict, details)` — gate verdict notification
- `alert_system_event(prefix, level, event, details)` — generic system alert

Environment variables:
- `TELEGRAM_BOT_TOKEN` — bot token (never commit to git)
- `TELEGRAM_CHAT_ID` — chat/channel ID

Correct usage:
```python
from ag.monitoring import alert_validation_result, alert_system_event

alert_validation_result("A1", "ROBUST", gate_result.report())
alert_system_event("AG-TRADE", "ERROR", "Gate run failed", str(exc))
```

---

## Use For

- Validation gate decisions → `alert_validation_result()`
- Daily performance summaries → `send_telegram()`
- Emergency halts → `alert_system_event("AG-TRADE", "CRITICAL", "Kill switch", reason)`
- Error alerts → `alert_system_event("AG-TRADE", "ERROR", ...)`

Keep this module lightweight and dependency-free (stdlib only). Never add
`requests`, `httpx`, or other HTTP libraries to this file.
