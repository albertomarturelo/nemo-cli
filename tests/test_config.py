"""Tests for nemo_cli.config."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from nemo_cli.config import API_BASE_URL, Credentials, load_credentials


class TestApiBaseUrl:
    def test_points_to_production_root(self) -> None:
        assert API_BASE_URL == "https://portalclientes.vectorcapital.cl/api"


class TestLoadCredentials:
    def test_returns_credentials_when_both_vars_set(
        self, credentials_env: None
    ) -> None:
        creds = load_credentials()
        assert isinstance(creds, Credentials)
        assert creds.user_name == "test@example.com"
        assert creds.password == "test-password"

    def test_strips_username_whitespace(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NEMO_USERNAME", "  spaced@example.com  ")
        monkeypatch.setenv("NEMO_PASSWORD", "pw")
        creds = load_credentials()
        assert creds.user_name == "spaced@example.com"

    def test_does_not_strip_password(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Passwords with intentional surrounding whitespace must be preserved.
        monkeypatch.setenv("NEMO_USERNAME", "u@example.com")
        monkeypatch.setenv("NEMO_PASSWORD", "  pw-with-spaces  ")
        creds = load_credentials()
        assert creds.password == "  pw-with-spaces  "

    def test_raises_when_username_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("NEMO_USERNAME", raising=False)
        monkeypatch.setenv("NEMO_PASSWORD", "pw")
        with pytest.raises(RuntimeError, match="Missing credentials"):
            load_credentials()

    def test_raises_when_password_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NEMO_USERNAME", "u@example.com")
        monkeypatch.delenv("NEMO_PASSWORD", raising=False)
        with pytest.raises(RuntimeError, match="Missing credentials"):
            load_credentials()

    def test_raises_when_both_missing(
        self, no_credentials_env: None
    ) -> None:
        with pytest.raises(RuntimeError, match="Missing credentials"):
            load_credentials()

    def test_raises_when_username_is_only_whitespace(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NEMO_USERNAME", "   ")
        monkeypatch.setenv("NEMO_PASSWORD", "pw")
        with pytest.raises(RuntimeError, match="Missing credentials"):
            load_credentials()


class TestCredentials:
    def test_is_frozen_dataclass(self) -> None:
        creds = Credentials(user_name="u@e.com", password="pw")
        with pytest.raises(FrozenInstanceError):
            creds.user_name = "other"  # type: ignore[misc]

    def test_equality_by_value(self) -> None:
        a = Credentials(user_name="u@e.com", password="pw")
        b = Credentials(user_name="u@e.com", password="pw")
        c = Credentials(user_name="u@e.com", password="other")
        assert a == b
        assert a != c
