"""Minimal Telegram alert for validation status and system events.

Stdlib-only. No retries, no singleton, no external dependencies.
Call send_telegram() directly; set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in env.
"""
from __future__ import annotations

import json
import os
import urllib.request


def send_telegram(
    message: str,
    bot_token: str | None = None,
    chat_id: str | None = None,
) -> bool:
    """Send a plain-text alert. Returns True on HTTP 200, False otherwise."""
    token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    cid = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not cid:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": cid, "text": message, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


def alert_validation_result(alpha: str, verdict: str, details: str) -> bool:
    """Send a gate verdict notification."""
    icon = "GREEN" if verdict == "ROBUST" else "RED" if verdict == "FRAGILE" else "YELLOW"
    msg = (
        f"[{icon}] <b>[AG-TRADE] Validation: {alpha}</b>\n"
        f"Verdict: <b>{verdict}</b>\n"
        f"{details}"
    )
    return send_telegram(msg)


def alert_system_event(prefix: str, level: str, event: str, details: str = "") -> bool:
    """Generic system alert (level = INFO | WARN | ERROR | CRITICAL)."""
    msg = f"<b>[{prefix}] {level}: {event}</b>"
    if details:
        msg += f"\n{details}"
    return send_telegram(msg)