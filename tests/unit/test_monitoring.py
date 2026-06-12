"""Unit tests for ag.monitoring — Telegram alerting (stdlib-only module).

No network: urllib.request.urlopen is monkeypatched. Covers the unconfigured
path (must return False, never raise), payload construction, the non-200 and
exception paths, and the verdict-icon formatting helpers.
"""
from __future__ import annotations

import json

import pytest

from ag.monitoring import alert_system_event, alert_validation_result, send_telegram


class _FakeResponse:
    def __init__(self, status: int = 200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _Capture:
    """Stands in for urllib.request.urlopen; records the request it received."""

    def __init__(self, status: int = 200, raise_exc: Exception | None = None):
        self.status = status
        self.raise_exc = raise_exc
        self.request = None

    def __call__(self, req, timeout=None):
        self.request = req
        if self.raise_exc is not None:
            raise self.raise_exc
        return _FakeResponse(self.status)

    @property
    def payload(self) -> dict:
        assert self.request is not None, "urlopen was never called"
        return json.loads(self.request.data.decode())


@pytest.fixture
def no_env(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)


@pytest.fixture
def fake_urlopen(monkeypatch):
    cap = _Capture()
    monkeypatch.setattr("urllib.request.urlopen", cap)
    return cap


# ── unconfigured: must be a silent no-op, never an exception ──────────────────

class TestUnconfigured:
    def test_returns_false_without_credentials(self, no_env, fake_urlopen):
        assert send_telegram("hello") is False

    def test_no_network_call_without_credentials(self, no_env, fake_urlopen):
        send_telegram("hello")
        assert fake_urlopen.request is None

    def test_missing_chat_id_alone_is_enough_to_skip(self, no_env, fake_urlopen):
        assert send_telegram("hello", bot_token="tok") is False
        assert fake_urlopen.request is None


# ── configured: payload + result paths ─────────────────────────────────────────

class TestSend:
    def test_success_returns_true(self, no_env, fake_urlopen):
        assert send_telegram("hi", bot_token="tok", chat_id="42") is True

    def test_env_credentials_used(self, monkeypatch, fake_urlopen):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "envtok")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "7")
        assert send_telegram("hi") is True
        assert "botenvtok/sendMessage" in fake_urlopen.request.full_url
        assert fake_urlopen.payload["chat_id"] == "7"

    def test_explicit_args_override_env(self, monkeypatch, fake_urlopen):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "envtok")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "7")
        send_telegram("hi", bot_token="explicit", chat_id="9")
        assert "botexplicit/sendMessage" in fake_urlopen.request.full_url
        assert fake_urlopen.payload["chat_id"] == "9"

    def test_payload_text_and_parse_mode(self, no_env, fake_urlopen):
        send_telegram("<b>msg</b>", bot_token="t", chat_id="c")
        assert fake_urlopen.payload["text"] == "<b>msg</b>"
        assert fake_urlopen.payload["parse_mode"] == "HTML"

    def test_non_200_returns_false(self, no_env, monkeypatch):
        cap = _Capture(status=500)
        monkeypatch.setattr("urllib.request.urlopen", cap)
        assert send_telegram("hi", bot_token="t", chat_id="c") is False

    def test_network_error_returns_false_not_raise(self, no_env, monkeypatch):
        cap = _Capture(raise_exc=OSError("connection refused"))
        monkeypatch.setattr("urllib.request.urlopen", cap)
        assert send_telegram("hi", bot_token="t", chat_id="c") is False


# ── formatting helpers ─────────────────────────────────────────────────────────

class TestAlertFormatting:
    def test_validation_alert_unconfigured_returns_false(self, no_env, fake_urlopen):
        assert alert_validation_result("A1", "ROBUST", "details") is False
        assert fake_urlopen.request is None

    @pytest.mark.parametrize(
        "verdict,icon",
        [("ROBUST", "[GREEN]"), ("FRAGILE", "[RED]"), ("READ", "[YELLOW]")],
    )
    def test_validation_message_contains_icon_and_verdict(
        self, monkeypatch, fake_urlopen, verdict, icon
    ):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "c")
        assert alert_validation_result("A1", verdict, "n=200") is True
        text = fake_urlopen.payload["text"]
        assert icon in text
        assert verdict in text
        assert "A1" in text
        assert "n=200" in text

    def test_system_event_with_details(self, monkeypatch, fake_urlopen):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "c")
        assert alert_system_event("AG", "ERROR", "disk full", "97% used") is True
        text = fake_urlopen.payload["text"]
        assert "[AG] ERROR: disk full" in text
        assert "97% used" in text

    def test_system_event_without_details_has_single_line(
        self, monkeypatch, fake_urlopen
    ):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "c")
        alert_system_event("AG", "INFO", "started")
        assert "\n" not in fake_urlopen.payload["text"]
