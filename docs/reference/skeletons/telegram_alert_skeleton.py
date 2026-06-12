# REFERENCE SKELETON ONLY — do not use in production
# Source: telegram_alert.py upload 2026-06-12
#
# CONFLICT: uses `import requests` (third-party)
# PRODUCTION: ag/monitoring/__init__.py uses stdlib urllib.request only
# DO NOT replace or modify ag/monitoring/__init__.py with this.
#
# The production module already has:
#   send_telegram()
#   alert_validation_result()
#   alert_system_event()
#
# The class-based pattern below is the only structural difference.
# If a class wrapper is ever needed, wrap the existing stdlib functions.

import os
# import requests  # <- NOT allowed in ag/monitoring/ (stdlib only)
from datetime import datetime


class TelegramAlerter:
    """Class-based wrapper — reference only. Use ag.monitoring functions directly."""

    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    def send(self, message: str):
        if not self.token or not self.chat_id:
            print("[Telegram] Token or chat_id not set. Message:", message)
            return
        # Production equivalent (stdlib):
        # from ag.monitoring import send_telegram
        # send_telegram(message)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        print(f"[{ts}] {message}")  # stub
