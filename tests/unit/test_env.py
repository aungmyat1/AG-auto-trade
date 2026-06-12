"""Tests for ag/env.py — runtime environment loader."""
from __future__ import annotations

import os

import ag.env as env


class TestIbDefaults:
    """IB connection params have sensible defaults when not set in env."""

    def test_ib_host_default(self, monkeypatch):
        monkeypatch.delenv("IB_HOST", raising=False)
        # Module-level var was captured at import; check the default value matches spec
        assert env.IB_HOST in ("127.0.0.1", os.environ.get("IB_HOST", "127.0.0.1"))

    def test_ib_port_is_int(self):
        assert isinstance(env.IB_PORT, int)

    def test_ib_client_id_is_int(self):
        assert isinstance(env.IB_CLIENT_ID, int)

    def test_ib_port_in_valid_range(self):
        assert 1024 <= env.IB_PORT <= 65535

    def test_ib_client_id_positive(self):
        assert env.IB_CLIENT_ID >= 1


class TestPhaseBReadiness:
    """check_phase_b_ready() reads os.environ at call time."""

    def test_not_ready_when_key_missing(self, monkeypatch):
        monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
        ready, missing = env.check_phase_b_ready()
        assert ready is False
        assert "DATABENTO_API_KEY" in missing

    def test_ready_when_key_set(self, monkeypatch):
        monkeypatch.setenv("DATABENTO_API_KEY", "db-live-key-abc123")
        ready, missing = env.check_phase_b_ready()
        assert ready is True
        assert missing == []

    def test_missing_list_is_empty_on_success(self, monkeypatch):
        monkeypatch.setenv("DATABENTO_API_KEY", "any-key")
        _, missing = env.check_phase_b_ready()
        assert missing == []

    def test_empty_string_treated_as_missing(self, monkeypatch):
        monkeypatch.setenv("DATABENTO_API_KEY", "")
        ready, missing = env.check_phase_b_ready()
        assert ready is False
        assert "DATABENTO_API_KEY" in missing


class TestPhase3Readiness:
    """check_phase_3_ready() reads os.environ at call time."""

    def test_not_ready_when_both_telegram_keys_missing(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        ready, missing = env.check_phase_3_ready()
        assert ready is False
        assert "TELEGRAM_BOT_TOKEN" in missing
        assert "TELEGRAM_CHAT_ID" in missing

    def test_not_ready_when_only_token_missing(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123456")
        ready, missing = env.check_phase_3_ready()
        assert ready is False
        assert "TELEGRAM_BOT_TOKEN" in missing

    def test_not_ready_when_only_chat_id_missing(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot:TOKEN")
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        ready, missing = env.check_phase_3_ready()
        assert ready is False
        assert "TELEGRAM_CHAT_ID" in missing

    def test_ready_when_both_telegram_keys_set(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot:TOKEN")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123456")
        ready, missing = env.check_phase_3_ready()
        assert ready is True
        assert missing == []


class TestEnvModuleAttributes:
    """Smoke-test that ag/env exports the expected names."""

    def test_exports_databento_key(self):
        assert hasattr(env, "DATABENTO_API_KEY")

    def test_exports_telegram_token(self):
        assert hasattr(env, "TELEGRAM_BOT_TOKEN")

    def test_exports_telegram_chat_id(self):
        assert hasattr(env, "TELEGRAM_CHAT_ID")

    def test_exports_ib_host(self):
        assert hasattr(env, "IB_HOST")

    def test_exports_ib_port(self):
        assert hasattr(env, "IB_PORT")

    def test_exports_ib_client_id(self):
        assert hasattr(env, "IB_CLIENT_ID")

    def test_exports_check_phase_b_ready(self):
        assert callable(env.check_phase_b_ready)

    def test_exports_check_phase_3_ready(self):
        assert callable(env.check_phase_3_ready)
